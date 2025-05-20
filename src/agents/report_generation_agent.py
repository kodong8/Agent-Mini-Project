from loguru import logger
from langchain_core.messages import AIMessage
from typing import Optional, List
from typing_extensions import TypedDict
import datetime
from ..prompts import report_generation_prompt
from ..utils import save_report

class ReportGenerationAgentState(TypedDict):
    """보고서 생성 에이전트의 상태를 정의하는 타입"""
    ai_service: str
    criteria: str
    service_info: Optional[AIMessage]
    ethical_risk_keywords: Optional[List[str]]  # 윤리적 리스크 키워드 추가
    criteria_info: Optional[AIMessage]
    risk_message: Optional[AIMessage]
    report_path: Optional[str]

def create_report_generation_agent(llm):
    """보고서 생성 에이전트를 생성합니다."""
    logger.info("보고서 생성 에이전트 생성 중...")
    
    # 보고서 생성 처리 노드 생성
    def report_generation_node(state):
        """보고서 생성을 처리하는 노드"""
        try:
            print("보고서 생성 노드 실행 중...")
            # 입력 정보 확인
            if (not hasattr(state, "service_info") or state.service_info is None or
                not hasattr(state, "criteria_info") or state.criteria_info is None or
                not hasattr(state, "risk_message") or state.risk_message is None):
                logger.warning("필요한 정보가 없습니다. 보고서 생성을 건너뜁니다.")
                return {"report_path": None}
            
            # 윤리적 리스크 키워드 확인
            has_keywords = hasattr(state, "ethical_risk_keywords") and state.ethical_risk_keywords
            keywords_text = ", ".join(state.ethical_risk_keywords) if has_keywords else "윤리적 리스크 키워드 없음"
            logger.info(f"보고서 생성에 사용할 윤리적 리스크 키워드: {keywords_text}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 프롬프트 준비 (키워드 포함)
            formatted_prompt = report_generation_prompt.format(
                ai_service=state.ai_service,
                criteria=state.criteria,
                ethical_risk_keywords=keywords_text,
                service_info=state.service_info.content,
                criteria_info=state.criteria_info.content,
                risk_message=state.risk_message.content,
                timestamp=timestamp
            )
            
            # LLM에 질의
            logger.info(f"보고서 생성 중: {state.ai_service}")
            response = llm.invoke(formatted_prompt)
            logger.info("보고서 생성 완료")
            
            # 보고서 초안 품질 검증
            if "# AI 윤리성 리스크 진단 보고서" not in response.content:
                logger.warning("생성된 보고서가 올바른 형식이 아닙니다. 다시 시도합니다.")
                retry_prompt = f"""
                이전 응답이 올바른 보고서 형식이 아닙니다. 다음 내용을 바탕으로 AI 윤리성 리스크 진단 보고서를 처음부터 
                다시 작성해주세요. 반드시 '# AI 윤리성 리스크 진단 보고서:'로 시작하는 마크다운 형식의 보고서를 작성하세요.
                
                AI 서비스: {state.ai_service}
                적용된 윤리 기준: {state.criteria}
                윤리적 리스크 키워드: {keywords_text}
                서비스 정보: {state.service_info.content}
                적용 가능한 윤리 기준: {state.criteria_info.content}
                윤리 평가 결과: {state.risk_message.content}
                """
                response = llm.invoke(retry_prompt)
                logger.info("보고서 재생성 완료")
            
            # 보고서 검증 준비 (키워드 기반 검증)
            verification_prompt = f"""
            당신은 AI 윤리성 리스크 진단 보고서의 검증자입니다. 다음 보고서를 검토하고, 보고서를 개선해야 합니다.
            
            검토 기준:
            1. 모든 윤리적 리스크 키워드({keywords_text})가 보고서에서 적절히 다루어져야 합니다.
            2. 모든 주장에 윤리 기준의 출처와 조항이 명확히 연결되어야 합니다.
            3. 서비스 특성에 맞는 맞춤형 보고서여야 합니다.
            4. 모든 섹션이 적절히 작성되어야 합니다.
            
            검토 후, 보고서 전체를 개선된 형태로 다시 작성해주세요. 검토 의견이나 설명 없이 
            개선된 보고서 전체만 작성해주세요. 보고서는 반드시 '# AI 윤리성 리스크 진단 보고서:'로 시작해야 합니다.
            
            검토할 보고서:
            {response.content}
            """
            
            # 검증 및 개선된 보고서 생성
            logger.info("보고서 검증 및 개선 중...")
            verified_response = llm.invoke(verification_prompt)
            
            # 검증 결과 확인
            if "# AI 윤리성 리스크 진단 보고서" not in verified_response.content:
                logger.warning("검증 결과가 올바른 보고서 형식이 아닙니다. 원본 보고서를 사용합니다.")
                final_content = response.content
            else:
                logger.info("보고서 검증 및 개선 완료")
                final_content = verified_response.content
            
            # 로그에 일부 내용만 출력하여 로그 가독성 향상
            content_preview = final_content[:300] + "..." if len(final_content) > 300 else final_content
            logger.info(f"최종 보고서 내용(일부): {content_preview}")
            
            # 보고서 저장
            try:
                # 저장 경로 명시
                save_directory = "outputs/reports"
                report_files = save_report(
                    content=final_content,
                    service_name=state.ai_service.replace(" ", "_"),
                    criteria=state.criteria.replace(" ", "_"),
                    directory=save_directory
                )
                
                logger.info(f"보고서 저장 성공: {report_files['txt_path']}")
                
                # 상태 업데이트 - txt_path를 report_path로 사용
                return {"report_path": report_files["txt_path"]}
            except Exception as save_error:
                logger.error(f"보고서 저장 실패: {save_error}")
                return {"report_path": None}
        except Exception as e:
            logger.error(f"보고서 생성 처리 중 오류 발생: {e}")
            return {"report_path": None}
    
    return report_generation_node 