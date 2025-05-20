from loguru import logger
from langchain_core.messages import AIMessage
from typing import Optional, List
from typing_extensions import TypedDict

from ..prompts import ethics_evaluation_prompt

class EthicsEvaluationAgentState(TypedDict):
    """윤리 평가 에이전트의 상태를 정의하는 타입"""
    ai_service: str
    criteria: str
    service_info: Optional[AIMessage]
    ethical_risk_keywords: Optional[List[str]]  # 윤리적 리스크 키워드 추가
    criteria_info: Optional[AIMessage]
    risk_message: Optional[AIMessage]

def create_ethics_evaluation_agent(llm):
    """윤리 평가 에이전트를 생성합니다."""
    logger.info("윤리 평가 에이전트 생성 중...")
    
    def ethics_evaluation_node(state):
        """윤리 평가를 처리하는 노드"""
        try:
            print("윤리 평가 노드 실행 중...")
            # 필요한 정보 확인
            if not hasattr(state, "service_info") or state.service_info is None:
                logger.warning("서비스 정보가 없습니다. 윤리 평가를 건너뜁니다.")
                return {"risk_message": AIMessage(content="서비스 정보가 없어 윤리 평가를 수행할 수 없습니다.")}
            
            if not hasattr(state, "criteria_info") or state.criteria_info is None:
                logger.warning("윤리 기준 정보가 없습니다. 윤리 평가를 건너뜁니다.")
                return {"risk_message": AIMessage(content="윤리 기준 정보가 없어 윤리 평가를 수행할 수 없습니다.")}
            
            # 윤리적 리스크 키워드 확인
            has_keywords = hasattr(state, "ethical_risk_keywords") and state.ethical_risk_keywords
            keywords_text = ", ".join(state.ethical_risk_keywords) if has_keywords else "윤리적 리스크 키워드 없음"
            logger.info(f"윤리적 리스크 키워드: {keywords_text}")
            
            # 프롬프트 준비 (키워드 포함)
            formatted_prompt = ethics_evaluation_prompt.format(
                ai_service=state.ai_service,
                criteria=state.criteria,
                service_info=state.service_info.content,
                ethical_risk_keywords=keywords_text,
                criteria_info=state.criteria_info.content
            )
            
            # LLM에 질의
            logger.info(f"윤리 평가 수행 중: {state.ai_service}")
            response = llm.invoke(formatted_prompt)
            logger.info("윤리 평가 완료")
            
            # 리스크 평가가 적절히 수행되었는지 검증
            verification_prompt = f"""
            당신의 윤리 평가 결과를 검토하여 다음 사항을 확인해주세요:
            
            1. 다음 윤리적 리스크 키워드가 모두 적절히 다루어졌는지: {keywords_text}
            2. 모든 주장에 윤리 기준의 출처와 조항이 명확히 연결되었는지
            3. 서비스 특성에 맞는 구체적인 평가가 제공되었는지
            
            누락된 부분이 있다면 보완하여 완전한 평가를 제공해주세요.
            결과만 응답하고, 검증 과정에 대한 설명은 포함하지 마세요.
            """
            
            verified_response = llm.invoke(response.content + "\n\n" + verification_prompt)
            logger.info("윤리 평가 검증 완료")
            
            return {"risk_message": verified_response}
        except Exception as e:
            logger.error(f"윤리 평가 처리 중 오류 발생: {e}")
            return {"risk_message": AIMessage(content=f"윤리 평가 중 오류가 발생했습니다: {e}")}
    
    return ethics_evaluation_node 