from loguru import logger
from langchain_core.messages import AIMessage
from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict
from langgraph.prebuilt import ToolNode
import asyncio

from ..prompts import criteria_search_prompt
from ..tools.ethics_retriever import create_ethics_retriever_tool
from ..tools.web_search import create_web_search_tool

class CriteriaSearchAgentState(TypedDict):
    """기준 검색 에이전트의 상태를 정의하는 타입"""
    ai_service: str
    criteria: str
    service_info: Optional[AIMessage]
    ethical_risk_keywords: Optional[List[str]]
    criteria_info: Optional[AIMessage]
    query_attempt: Optional[int]
    last_query: Optional[str]

def create_criteria_search_agent(llm, vector_db):
    """기준 검색 에이전트를 생성합니다."""
    logger.info("기준 검색 에이전트 생성 중...")
    
    # 윤리 기준 검색 도구 생성 - 동일한 임베딩 모델 사용 확인
    ethics_retriever_tool = create_ethics_retriever_tool(vector_db, llm)
    
    # 웹 검색 도구 생성
    web_search_tool = create_web_search_tool()
    
    # ToolNode 생성
    ethics_retriever_node = ToolNode(
        tools=[ethics_retriever_tool]
    )
    
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
    
    def criteria_search_node(state):
        """기준 검색을 처리하는 노드"""
        try:
            print("기준 검색 노드 실행 중...")
            # 서비스 정보 확인
            if not hasattr(state, "service_info") or state.service_info is None:
                logger.warning("서비스 정보가 없습니다. 기준 검색을 건너뜁니다.")
                return {"criteria_info": AIMessage(content="서비스 정보가 없어 기준 검색을 수행할 수 없습니다.")}
            
            # 윤리적 리스크 키워드 확인
            has_keywords = hasattr(state, "ethical_risk_keywords") and state.ethical_risk_keywords
            if has_keywords:
                logger.info(f"윤리적 리스크 키워드 사용: {state.ethical_risk_keywords}")
            else:
                logger.warning("윤리적 리스크 키워드가 없습니다. 서비스 정보만 사용합니다.")
            
            # 쿼리 시도 횟수 초기화
            query_attempt = getattr(state, "query_attempt", 0)
            
            # 초기 쿼리 또는 재시도 쿼리
            if query_attempt == 0:
                # 키워드 기반 검색 쿼리 준비
                if has_keywords:
                    # 영어 검색 쿼리 생성
                    translate_keywords_prompt = f"""
                    다음 윤리적 리스크 키워드를 영어로 번역해주세요:
                    {', '.join(state.ethical_risk_keywords[:10])}
                    
                    번역된 영어 키워드만 쉼표로 구분하여 응답해주세요.
                    """
                    translate_response = llm.invoke(translate_keywords_prompt)
                    english_keywords = [kw.strip() for kw in translate_response.content.split(',')]
                    
                    # 영어 키워드 중에서 가장 관련성 높은 키워드 선택
                    keywords_selection_prompt = f"""
                    다음은 AI 서비스 '{state.ai_service}'의 윤리적 리스크와 관련된 키워드입니다:
                    {', '.join(english_keywords)}
                    
                    '{state.criteria}' 관련 규제 문서를 검색하기에 가장 적합한 키워드 5개를 선택하고, 
                    효과적인 검색 쿼리로 조합해주세요. 검색 쿼리만 응답해주세요.
                    """
                    query_response = llm.invoke(keywords_selection_prompt)
                    last_query = query_response.content.strip()
                else:
                    # 서비스 정보만 사용하여 쿼리 생성
                    translate_prompt = f"""
                    AI 규제 문서에서 효과적으로 검색하기 위한 구체적인 영어 쿼리를 작성해주세요.
                    AI 규제 문서는 법조문 형태입니다.

                    AI 서비스: {state.ai_service}
                    윤리 기준: {state.criteria}
                    서비스 정보:
                    {state.service_info.content}

                    다음 규제 내용을 고려하여 쿼리를 작성하세요:
                    - 해당 AI 서비스가 EU AI Act 기준으로 어떤 위험 카테고리에 속하는지 (금지된 사용 사례, 고위험, 제한된 위험, 최소 위험 등)
                    - 서비스의 주요 기능과 관련된 구체적인 규제 조항
                    - 데이터 처리, 투명성, 인간 감독, 정확성 등의 요구사항

                    예시 형식:
                    "[AI 서비스 유형] [주요 기능] [위험 카테고리] requirements under EU AI Act Article [관련 조항]"

                    영어로 된 검색 쿼리만 작성해주세요. 추가 설명 없이 쿼리만 응답하세요.
                    """
                    
                    english_query_response = llm.invoke(translate_prompt)
                    last_query = english_query_response.content.strip()
                
                logger.info(f"영어 검색 쿼리 생성: {last_query}")
            else:
                # 쿼리 리라이팅을 위한 프롬프트 (영어로)
                rewrite_prompt = f"""
                The previous query '{getattr(state, "last_query", "")}' did not return adequate results.
                Please rewrite a more effective query in English to search for ethical issues related to 
                '{state.ai_service}' in the context of '{state.criteria}'.
                
                Consider these ethical risk keywords if available:
                {', '.join(state.ethical_risk_keywords[:10]) if has_keywords else 'No keywords available'}
                
                Respond with only the new query in English, no additional explanation.
                """
                # 쿼리 리라이팅
                rewrite_response = llm.invoke(rewrite_prompt)
                last_query = rewrite_response.content.strip()
                logger.info(f"영어 쿼리 리라이팅: {last_query}")
                
            # 윤리 기준 검색 (메타데이터 지정)
            logger.info(f"윤리 기준 검색 중: {last_query} (프레임워크: {state.criteria})")
            
            # 메타데이터에 맞게 프레임워크 이름 변환
            framework_mapping = {
                "EU AI Act": "EU_AI_Act", 
                "UNESCO AI Ethics": "UNESCO_AI_Ethics",
                "OECD AI Principles": "OECD_AI_Principles"
            }
            framework = framework_mapping.get(state.criteria, state.criteria)
            
            # 윤리 기준 검색 수행 (비동기 함수 동기적으로 실행)
            search_results = []
            
            try:
                # 1. 먼저 키워드를 조합한 주 검색 쿼리 실행
                ethics_result = run_async(ethics_retriever_tool(last_query, framework))
                
                # 검색 결과가 빈약하면 각 키워드로 개별 검색
                if "could not find relevant" in ethics_result.content.lower() or len(ethics_result.content.strip()) < 100:
                    if has_keywords:
                        # 키워드별 개별 검색 시도
                        for idx, keyword in enumerate(state.ethical_risk_keywords[:5]):  # 상위 5개 키워드만 사용
                            translated_keyword_prompt = f"Translate this term to English for searching in regulatory documents: {keyword}"
                            translated_response = llm.invoke(translated_keyword_prompt)
                            eng_keyword = translated_response.content.strip()
                            
                            search_query = f"{eng_keyword} {state.ai_service} {framework} requirements"
                            logger.info(f"키워드 개별 검색: {search_query}")
                            
                            keyword_result = run_async(ethics_retriever_tool(search_query, framework))
                            if not "could not find relevant" in keyword_result.content.lower() and len(keyword_result.content.strip()) > 50:
                                search_results.append(keyword_result.content)
                                logger.info(f"키워드 '{keyword}' 검색 성공")
                    
                    # 추가 대체 쿼리 시도
                    alternative_queries = [
                        f"{state.ai_service} {framework} requirements",
                        f"{state.ai_service} type classification in {framework}",
                        f"obligations for {state.ai_service} under {framework}",
                        f"{state.ai_service} risk assessment {framework}"
                    ]
                    
                    # 대체 쿼리 시도
                    for alt_query in alternative_queries:
                        if not search_results:  # 이미 결과가 있으면 건너뛰기
                            logger.info(f"대체 쿼리로 검색 시도: {alt_query}")
                            alt_result = run_async(ethics_retriever_tool(alt_query, framework))
                            if not "could not find relevant" in alt_result.content.lower() and len(alt_result.content.strip()) > 100:
                                ethics_result = alt_result
                                last_query = alt_query
                                logger.info(f"대체 쿼리 성공: {alt_query}")
                                break
                else:
                    # 주 검색이 성공한 경우
                    search_results.append(ethics_result.content)
            except Exception as e:
                logger.error(f"윤리 기준 검색 오류: {e}")
                ethics_result = AIMessage(content=f"윤리 기준 검색 중 오류가 발생했습니다: {e}")
            
            # 검색 결과 확인
            if not search_results or len(search_results) < 100:
                logger.warning(f"윤리 기준 검색 결과 부족")
                
                # 웹 검색 수행
                web_search_keywords = []
                if has_keywords:
                    # 키워드 기반 웹 검색 쿼리 생성
                    translate_prompt = f"""
                    Create an effective English web search query about ethical regulations for this AI service:
                    Service: {state.ai_service}
                    Ethical Framework: {state.criteria}
                    Ethical risk keywords: {', '.join(state.ethical_risk_keywords[:7])}
                    
                    Respond with only the search query.
                    """
                    web_query_response = llm.invoke(translate_prompt)
                    web_search_keywords.append(web_query_response.content.strip())
                else:
                    # 기본 웹 검색 쿼리
                    web_search_keywords.append(f"{state.criteria} {state.ai_service} ethical requirements")
                
                web_results = []
                for web_query in web_search_keywords:
                    logger.info(f"웹 검색 수행: {web_query}")
                    web_result = run_async(web_search_tool(web_query))
                    if len(web_result.content.strip()) > 100:
                        web_results.append(web_result.content)
                
                # 웹 검색 결과도 부족한 경우
                if not web_results or len(web_results) < 100:
                    if query_attempt < 2:  # 최대 2번까지 재시도
                        logger.info(f"웹 검색 결과도 부족, 쿼리 리라이팅 후 재시도 ({query_attempt + 1}/2)")
                        return {
                            "criteria_info": AIMessage(content="관련 정보 없음"),
                            "query_attempt": query_attempt + 1,
                            "last_query": last_query
                        }
                    else:
                        logger.warning("최대 재시도 횟수 초과, 검색 실패")
                        return {"criteria_info": AIMessage(content="충분한 관련 윤리 기준 정보를 찾을 수 없습니다.")}
                
                # 웹 검색 결과가 있는 경우, 이를 기반으로 응답 생성 (영어 -> 한국어 번역)
                web_analysis_prompt = f"""
                다음은 '{state.ai_service}'에 대한 '{state.criteria}' 관련 영어로 된 웹 검색 결과입니다:
                
                {web_results}
                
                이 정보를 바탕으로 AI 서비스에 적용 가능한 윤리 기준을 분석하여 한국어로 정리해주세요.
                다음 형식에 맞추어 응답해 주세요:
                
                ### AI 서비스 분류
                [EU AI Act 기준으로 해당 서비스의 위험 분류 및 근거]
                
                ### 적용 조항 및 부록
                [서비스에 직접 적용되는 EU AI Act의 조항과 부록 번호]
                출처: [정보 출처]
                
                ### 주요 의무사항
                [서비스가 준수해야 할 구체적인 요구사항]
                출처: [정보 출처]
                
                ### 기술적 요구사항
                [구현 시 고려해야 할 기술적 요구사항]
                출처: [정보 출처]
                
                ### 문서화 및 투명성 요구사항
                [필요한 문서화 및 투명성 관련 요구사항]
                출처: [정보 출처]
                
                ### 평가 및 감독 체계
                [서비스 평가 및 감독 관련 요구사항]
                출처: [정보 출처]
                
                모든 정보에 [출처: 웹 검색]을 표시해주세요.
                """
                criteria_response = llm.invoke(web_analysis_prompt)
                return {"criteria_info": criteria_response, "query_attempt": 0, "last_query": last_query}
            
            # 벡터DB 검색 결과가 있는 경우, 이를 기반으로 응답 생성 (영어 -> 한국어 번역)
            criteria_analysis_prompt = f"""
            다음은 '{state.ai_service}'에 대한 '{state.criteria}' 관련 영어로 된 윤리 기준 검색 결과입니다:
            
            {search_results}
            
            이 정보를 바탕으로 AI 서비스에 적용 가능한 윤리 기준을 분석하여 한국어로 정리해주세요.
            다음 형식에 맞추어 응답해 주세요:
            
            ### AI 서비스 분류
            [EU AI Act 기준으로 해당 서비스의 위험 분류 및 근거]
            
            ### 적용 조항 및 부록
            [서비스에 직접 적용되는 EU AI Act의 조항과 부록 번호]
            출처: [정보 출처]
            
            ### 주요 의무사항
            [서비스가 준수해야 할 구체적인 요구사항]
            출처: [정보 출처]
            
            ### 기술적 요구사항
            [구현 시 고려해야 할 기술적 요구사항]
            출처: [정보 출처]
            
            ### 문서화 및 투명성 요구사항
            [필요한 문서화 및 투명성 관련 요구사항]
            출처: [정보 출처]
            
            ### 평가 및 감독 체계
            [서비스 평가 및 감독 관련 요구사항]
            출처: [정보 출처]
            
            모든 정보의 출처를 명확히 표시해주세요. 예: "출처: EU AI Act 제6조", "출처: EU AI Act 부록 III"
            """
            criteria_response = llm.invoke(criteria_analysis_prompt)
            return {"criteria_info": criteria_response, "query_attempt": 0, "last_query": last_query}
            
        except Exception as e:
            logger.error(f"기준 검색 처리 중 오류 발생: {e}")
            return {"criteria_info": AIMessage(content=f"윤리 기준 검색 중 오류가 발생했습니다: {e}")}
    
    return criteria_search_node 