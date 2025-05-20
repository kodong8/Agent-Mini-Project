from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from loguru import logger
from langchain_core.messages import AIMessage, HumanMessage
import json
import os
import uuid
from datetime import datetime

# 메시지 유형 정의
MessageType = Union[AIMessage, HumanMessage]

class EthicsState(BaseModel):
    """AI 윤리성 리스크 진단 시스템의 상태를 관리하는 클래스"""
    
    # 기본 상태 정보
    ai_service: str = Field(default="", description="분석 대상 AI 서비스 이름")
    criteria: str = Field(default="", description="선택된 윤리 기준 (예: EU AI Act)")
    
    # 에이전트 관련 상태
    service_info: Optional[MessageType] = Field(default=None, description="서비스 입력 에이전트가 생성한 서비스 설명")
    ethical_risk_keywords: Optional[List[str]] = Field(default=None, description="서비스 입력 에이전트가 식별한 윤리적 리스크 키워드 목록")
    criteria_info: Optional[MessageType] = Field(default=None, description="기준 검색 에이전트가 생성한 관련 윤리 기준")
    risk_message: Optional[MessageType] = Field(default=None, description="윤리 평가 에이전트가 생성한 리스크 분석")
    
    # 검색 관련 상태
    query_attempt: int = Field(default=0, description="쿼리 시도 횟수")
    last_query: Optional[str] = Field(default=None, description="마지막 실행된 검색 쿼리")
    
    # 상태 점수 (품질 평가)
    state_score: List[int] = Field(default=[0, 0, 0], description="각 상태의 품질 점수 [service_info, criteria_info, risk_message]")
    
    # 작업 상태 관리
    workflow_status: str = Field(default="initialized", description="워크플로우 상태 (initialized, processing, completed, failed)")
    
    # 보고서 정보
    report_path: Optional[str] = Field(default=None, description="생성된 보고서 파일 경로")
    
    # 워크플로우 추적
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="워크플로우 ID")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="워크플로우 생성 시간")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="워크플로우 업데이트 시간")
    
    def update_state(self, **kwargs):
        """상태를 업데이트합니다."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
                # 메시지 내용 로그 출력
                if key in ["service_info", "criteria_info", "risk_message"] and value is not None:
                    logger.info(f"======= {key.upper()} 생성 결과 =======")
                    logger.info(f"{value.content[:500]}...")
                    logger.info(f"================================")
                    print(f"\n======= {key.upper()} 생성 결과 =======")
                    print(f"{value.content[:500]}...")
                    print(f"================================\n")
                elif key == "ethical_risk_keywords" and value is not None:
                    logger.info(f"======= 윤리적 리스크 키워드 =======")
                    logger.info(f"{value}")
                    logger.info(f"================================")
                    print(f"\n======= 윤리적 리스크 키워드 =======")
                    print(f"{value}")
                    print(f"================================\n")
        
        # 업데이트 시간 갱신
        self.updated_at = datetime.now().isoformat()
        logger.info(f"상태 업데이트 완료: {list(kwargs.keys())}")
    
    def update_score(self, index: int, score: int):
        """특정 인덱스의 상태 점수를 업데이트합니다."""
        if 0 <= index < len(self.state_score):
            self.state_score[index] = score
            logger.info(f"상태 점수 업데이트: state_score[{index}] = {score}")
        else:
            logger.error(f"유효하지 않은 상태 점수 인덱스: {index}")
    
    def log_current_state(self):
        """현재 상태를 로그로 출력합니다."""
        try:
            logger.info(f"====== 현재 워크플로우 상태 ======")
            logger.info(f"서비스: {self.ai_service}")
            logger.info(f"윤리 기준: {self.criteria}")
            logger.info(f"워크플로우 상태: {self.workflow_status}")
            
            if self.service_info:
                logger.info(f"서비스 정보: 생성됨 ({len(self.service_info.content)} 자)")
            
            if self.ethical_risk_keywords:
                # 너무 길면 로그가 깨질 수 있으므로 키워드 수만 표시
                if len(self.ethical_risk_keywords) > 5:
                    logger.info(f"윤리적 리스크 키워드: {len(self.ethical_risk_keywords)}개 (첫 5개: {self.ethical_risk_keywords[:5]})")
                else:
                    logger.info(f"윤리적 리스크 키워드: {self.ethical_risk_keywords}")
            
            if self.criteria_info:
                logger.info(f"윤리 기준 정보: 생성됨 ({len(self.criteria_info.content)} 자)")
            
            if self.risk_message:
                logger.info(f"리스크 분석: 생성됨 ({len(self.risk_message.content)} 자)")
            
            if self.report_path:
                logger.info(f"보고서 경로: {self.report_path}")
            
            logger.info(f"쿼리 시도 횟수: {self.query_attempt}")
            
            if self.last_query:
                # 쿼리가 너무 길면 로그가 깨질 수 있으므로 길이 제한
                if len(self.last_query) > 50:
                    logger.info(f"마지막 쿼리: {self.last_query[:50]}...")
                else:
                    logger.info(f"마지막 쿼리: {self.last_query}")
            
            logger.info(f"================================")
        except Exception as e:
            logger.error(f"상태 로깅 중 오류 발생: {e}")
    
    def save_state(self, directory="ai_agent/outputs/states"):
        """현재 상태를 JSON 파일로 저장합니다."""
        os.makedirs(directory, exist_ok=True)
        filename = f"state_{self.workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(directory, filename)
        
        # 직렬화 가능한 데이터로 변환
        serializable_data = self.dict(exclude={"service_info", "criteria_info", "risk_message"})
        
        # 메시지 직렬화
        if self.service_info:
            serializable_data["service_info"] = {
                "type": self.service_info.__class__.__name__,
                "content": self.service_info.content
            }
        
        if self.criteria_info:
            serializable_data["criteria_info"] = {
                "type": self.criteria_info.__class__.__name__,
                "content": self.criteria_info.content
            }
        
        if self.risk_message:
            serializable_data["risk_message"] = {
                "type": self.risk_message.__class__.__name__,
                "content": self.risk_message.content
            }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            logger.info(f"상태 저장 완료: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"상태 저장 실패: {e}")
            raise
    
    @classmethod
    def load_state(cls, filepath):
        """저장된 상태를 JSON 파일에서 로드합니다."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 메시지 객체 복원
            if "service_info" in data and data["service_info"]:
                msg_type = data["service_info"]["type"]
                msg_content = data["service_info"]["content"]
                if msg_type == "AIMessage":
                    data["service_info"] = AIMessage(content=msg_content)
                elif msg_type == "HumanMessage":
                    data["service_info"] = HumanMessage(content=msg_content)
            
            if "criteria_info" in data and data["criteria_info"]:
                msg_type = data["criteria_info"]["type"]
                msg_content = data["criteria_info"]["content"]
                if msg_type == "AIMessage":
                    data["criteria_info"] = AIMessage(content=msg_content)
                elif msg_type == "HumanMessage":
                    data["criteria_info"] = HumanMessage(content=msg_content)
            
            if "risk_message" in data and data["risk_message"]:
                msg_type = data["risk_message"]["type"]
                msg_content = data["risk_message"]["content"]
                if msg_type == "AIMessage":
                    data["risk_message"] = AIMessage(content=msg_content)
                elif msg_type == "HumanMessage":
                    data["risk_message"] = HumanMessage(content=msg_content)
            
            state = cls(**data)
            logger.info(f"상태 로드 완료: {filepath}")
            return state
        except Exception as e:
            logger.error(f"상태 로드 실패: {e}")
            raise 