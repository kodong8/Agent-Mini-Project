from loguru import logger
from langgraph.graph import StateGraph, END
from typing import Dict, Any, Tuple, List, Literal
from .state import EthicsState
from langchain_core.messages import AIMessage
from ..agents import (
    create_service_input_agent,
    create_criteria_search_agent,
    create_ethics_evaluation_agent,
    create_report_generation_agent
)

def router(state: EthicsState) -> Literal["service_input", "criteria_search", "ethics_evaluation", "report_generation", "end"]:
    """각 상태에서 다음 단계를 결정하는 라우터"""
    print(f"라우터 실행 중, 상태: {state.workflow_status}")
    
    # 현재 상태 로깅
    state.log_current_state()
    
    # 워크플로우 상태 확인
    if state.workflow_status == "completed":
        return "end"
    
    # 서비스 입력 단계
    if not state.service_info or not state.ethical_risk_keywords:
        logger.info("다음 단계: 서비스 입력")
        return "service_input"
    
    # 기준 검색 단계
    if not state.criteria_info:
        logger.info("다음 단계: 기준 검색")
        return "criteria_search"
    
    # 윤리 평가 단계
    if not state.risk_message:
        logger.info("다음 단계: 윤리 평가")
        return "ethics_evaluation"
    
    # 보고서 생성 단계
    if not state.report_path:
        logger.info("다음 단계: 보고서 생성")
        return "report_generation"
    
    # 모든 단계 완료
    logger.info("워크플로우 완료")
    return "end"

def create_ethics_workflow(llm, vector_db):
    """AI 윤리성 리스크 진단 워크플로우를 생성합니다."""
    logger.info("AI 윤리성 리스크 진단 워크플로우 생성 중...")
    
    # 에이전트 생성
    service_input_node = create_service_input_agent(llm)
    criteria_search_node = create_criteria_search_agent(llm, vector_db)
    ethics_evaluation_node = create_ethics_evaluation_agent(llm)
    report_generation_node = create_report_generation_agent(llm)
    
    # 상태 변경 후 로깅 처리하는 래퍼 함수 생성
    def log_after_service_input(state_dict):
        try:
            result = service_input_node(state_dict)
            # 결과 검증
            if result and "service_info" in result:
                logger.info(f"서비스 입력 에이전트 실행 완료: 서비스 정보 생성됨")
            else:
                logger.warning(f"서비스 입력 에이전트 실행 결과 불완전: {result.keys() if result else None}")
            return result
        except Exception as e:
            logger.error(f"서비스 입력 에이전트 오류: {e}")
            return {"service_info": AIMessage(content=f"에러: {e}"), "ethical_risk_keywords": ["error"]}
    
    def log_after_criteria_search(state_dict):
        try:
            result = criteria_search_node(state_dict)
            # 결과 검증
            if result and "criteria_info" in result:
                logger.info(f"기준 검색 에이전트 실행 완료: 기준 정보 생성됨")
            else:
                logger.warning(f"기준 검색 에이전트 실행 결과 불완전: {result.keys() if result else None}")
            return result
        except Exception as e:
            logger.error(f"기준 검색 에이전트 오류: {e}")
            return {"criteria_info": AIMessage(content=f"에러: {e}")}
    
    def log_after_ethics_evaluation(state_dict):
        try:
            result = ethics_evaluation_node(state_dict)
            # 결과 검증
            if result and "risk_message" in result:
                logger.info(f"윤리 평가 에이전트 실행 완료: 리스크 메시지 생성됨")
            else:
                logger.warning(f"윤리 평가 에이전트 실행 결과 불완전: {result.keys() if result else None}")
            return result
        except Exception as e:
            logger.error(f"윤리 평가 에이전트 오류: {e}")
            return {"risk_message": AIMessage(content=f"에러: {e}")}
    
    def log_after_report_generation(state_dict):
        try:
            result = report_generation_node(state_dict)
            # 결과 검증
            if result and "report_path" in result and result["report_path"]:
                logger.info(f"보고서 생성 에이전트 실행 완료: 보고서 경로 생성됨 ({result['report_path']})")
            else:
                logger.warning(f"보고서 생성 에이전트 실행 결과 불완전: {result}")
            return result
        except Exception as e:
            logger.error(f"보고서 생성 에이전트 오류: {e}")
            return {"report_path": None}
    
    # 워크플로우 상태 그래프 생성
    workflow = StateGraph(EthicsState)
    
    # 노드 추가 (로깅 기능 포함)
    workflow.add_node("service_input", log_after_service_input)
    workflow.add_node("criteria_search", log_after_criteria_search)
    workflow.add_node("ethics_evaluation", log_after_ethics_evaluation)
    workflow.add_node("report_generation", log_after_report_generation)
    workflow.add_node("end", lambda x: {"workflow_status": "completed"})

    
    # 엣지 설정을 이렇게 수정
    workflow.add_edge("service_input", "criteria_search")
    workflow.add_edge("criteria_search", "ethics_evaluation")
    workflow.add_edge("ethics_evaluation", "report_generation")
    workflow.add_edge("report_generation", "end")
    
    # 조건부 엣지를 사용하려면 이렇게 설정
    # workflow.add_conditional_edges("service_input", router)
    # workflow.add_conditional_edges("criteria_search", router)
    # workflow.add_conditional_edges("ethics_evaluation", router)
    # workflow.add_conditional_edges("report_generation", router)
    
    # 엔트리 포인트 설정
    workflow.set_entry_point("service_input")
    
    # 그래프 컴파일
    ethics_workflow = workflow.compile()
    
    logger.info("AI 윤리성 리스크 진단 워크플로우 생성 완료")
    return ethics_workflow 