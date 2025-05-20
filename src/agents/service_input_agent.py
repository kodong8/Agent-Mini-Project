from loguru import logger
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from typing import Optional, List
from typing_extensions import TypedDict
import asyncio
import re

from ..prompts import service_input_prompt
from ..tools.web_search import create_web_search_tool

class ServiceInputAgentState(TypedDict):
    """서비스 입력 에이전트의 상태를 정의하는 타입"""
    ai_service: str
    service_info: Optional[AIMessage]
    ethical_risk_keywords: Optional[List[str]]

def create_service_input_agent(llm):
    """서비스 입력 에이전트를 생성합니다."""
    logger.info("서비스 입력 에이전트 생성 중...")
    
    # 웹 검색 도구 생성
    web_search_tool = create_web_search_tool()
    
    # ToolNode 생성
    web_search_node = ToolNode(
        tools=[web_search_tool]
    )
    
    # 비동기 함수를 동기적으로 실행하는 헬퍼 함수
    def run_async(coro):
        try:
            return asyncio.run(coro)
        except RuntimeError:  # 이미 실행 중인 이벤트 루프가 있는 경우
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)
    
    # 키워드 추출 함수
    def extract_keywords(content):
        """LLM 응답에서 윤리적 리스크 키워드를 추출합니다."""
        # 윤리적 리스크 키워드 섹션 찾기
        keyword_section_match = re.search(r"(?:###\s*윤리적\s*리스크\s*키워드[\s\n]*)(.+?)(?=###|$)", content, re.DOTALL)
        
        if not keyword_section_match:
            # 키워드 섹션을 찾을 수 없는 경우, 전체 내용에서 잠재적 키워드 추출 시도
            logger.warning("윤리적 리스크 키워드 섹션을 찾을 수 없습니다. 내용 분석을 통해 키워드를 추출합니다.")
            
            # 키워드 추출 프롬프트
            extract_prompt = f"""
            다음 AI 서비스 설명에서 윤리적 리스크와 관련된 핵심 키워드를 10-15개 추출해주세요.
            쉼표로 구분된 단어나 짧은 구문으로만 응답해주세요.
            
            {content}
            """
            
            # 키워드 추출을 위한 LLM 호출
            extract_response = llm.invoke(extract_prompt)
            keywords_raw = extract_response.content.strip()
        else:
            # 키워드 섹션이 발견된 경우
            keywords_raw = keyword_section_match.group(1).strip()
        
        # 키워드 정리 (줄바꿈, 불릿 포인트 등 제거)
        keywords_raw = re.sub(r'[-*•]', '', keywords_raw)
        
        # 쉼표로 구분된 키워드 리스트 생성
        keywords = [kw.strip() for kw in re.split(r'[,\n]', keywords_raw) if kw.strip()]
        
        # 중복 제거 및 빈 키워드 제거
        keywords = list(set(keywords))
        keywords = [kw for kw in keywords if kw and len(kw) > 1]
        
        return keywords
    
    # 서비스 입력 처리 노드 생성
    def service_input_node(state):
        """서비스 입력을 처리하는 노드"""
        try:
            print("서비스 입력 노드 실행 중...")
            logger.info(f"서비스 정보 수집 중: {state.ai_service}")
            
            # 프롬프트 준비
            formatted_prompt = service_input_prompt.format(
                ai_service=state.ai_service
            )
            
            # LLM에 질의
            response = llm.invoke(formatted_prompt)
            
            # 서비스 정보가 부족한 경우 웹 검색 수행
            if "분석할 수 없는 서비스" in response.content:
                logger.info("웹 검색 필요: 서비스 정보 부족")
                
                # 웹 검색 수행
                web_search_result = run_async(web_search_tool(state.ai_service))
                
                if len(web_search_result.content.strip()) < 100:
                    logger.warning("웹 검색 결과가 부정확하거나 부족합니다.")
                    return {
                        "service_info": AIMessage(content="분석할 수 없는 서비스 입니다."),
                        "ethical_risk_keywords": ["unknown", "insufficient_data", "analysis_failure"]
                    }
                else:
                    # 웹 검색 결과를 프롬프트에 통합
                    combined_prompt = f"""
                    {formatted_prompt}
                    
                    추가로 검색한 정보:
                    {web_search_result.content}
                    
                    위 정보를 바탕으로 AI 서비스에 대한 종합적인 정보를 제공해주세요.
                    """
                    
                    # LLM에 통합된 프롬프트로 질의
                    combined_response = llm.invoke(combined_prompt)
                    logger.info("웹 검색 결과 기반으로 서비스 정보 업데이트")
                    
                    # 웹 검색 결과에서 키워드 추출
                    keywords = extract_keywords(combined_response.content)
                    logger.info(f"윤리적 리스크 키워드 추출 완료: {len(keywords)}개")
                    
                    return {
                        "service_info": combined_response,
                        "ethical_risk_keywords": keywords
                    }
            else:
                logger.info("웹 검색 없이 서비스 정보 업데이트")
                keywords = extract_keywords(response.content)
                return {
                    "service_info": response,
                    "ethical_risk_keywords": keywords
                }
                
        except Exception as e:
            logger.error(f"서비스 입력 처리 중 오류 발생: {e}")
            return {
                "service_info": AIMessage(content=f"서비스 정보 수집 중 오류가 발생했습니다: {e}"),
                "ethical_risk_keywords": ["error", "processing_failure"]
            }
    
    return service_input_node 