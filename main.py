import os
import argparse
from loguru import logger

from src.utils import setup_logger, load_config
from src.core import (
    get_llm,
    get_embeddings,
    load_ethics_frameworks_to_db,
    EthicsState,
    create_ethics_workflow
)
from langchain.embeddings import HuggingFaceEmbeddings


def main():
    """AI 윤리성 리스크 진단 시스템 메인 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description="AI 윤리성 리스크 진단 시스템")
    parser.add_argument("--service", "-s", type=str, required=True, help="분석할 AI 서비스 이름")
    parser.add_argument("--criteria", "-c", type=str, default="EU AI Act", choices=["EU AI Act", "UNESCO AI Ethics", "OECD AI Principles"], help="적용할 윤리 기준")
    args = parser.parse_args()
    
    # 로거 설정
    setup_logger()
    logger.info("AI 윤리성 리스크 진단 시스템 시작")
    
    try:
        # 환경 설정 로드
        config = load_config()
        print("환경 설정 로드 완료")
        
        # 모델 초기화
        llm = get_llm(model_name=os.getenv("LLM_MODEL", "gpt-4o"))
        print("LLM 모델 초기화 완료")
        
        # 임베딩 모델 초기화 - 테스트와 같은 모델 사용
        embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        print(f"임베딩 모델 초기화 완료: {embedding_model}")
        
        # 윤리 프레임워크 벡터 DB 로드 - FAISS 사용
        faiss_path = os.getenv("FAISS_DB_PATH", "./data/vectorstore")
        ethics_db = load_ethics_frameworks_to_db(embeddings, faiss_path=faiss_path)
        print(f"윤리 프레임워크 벡터 DB 로드 완료: {faiss_path}")
        
        # 상태 초기화
        state = EthicsState(
            ai_service=args.service,
            criteria=args.criteria,
            workflow_status="processing"
        )
        print(f"상태 초기화 완료: {state.ai_service}, {state.criteria}")
        
        # 워크플로우 생성 및 실행
        workflow = create_ethics_workflow(llm, ethics_db)
        print("워크플로우 생성 완료, 실행 시작...")
        
        # 상태 저장
        state_path = state.save_state()
        logger.info(f"초기 상태 저장 완료: {state_path}")
        
        # 워크플로우 실행
        current_state = state  # 초기 상태로 설정
        for step in workflow.stream(state):
            # 현재 단계 로깅
            node = step.get("node")
            if node:
                print(f"실행 중인 노드: {node}")
            
            # 노드 실행 결과 명시적으로 확인 및 로깅
            if step.get("output"):
                output = step.get("output")
                print(f"노드 출력 키: {list(output.keys())}")
                logger.info(f"노드 '{node}' 출력 키: {list(output.keys())}")
                
                # 출력 결과를 현재 상태에 반영
                for key, value in output.items():
                    if hasattr(current_state, key):
                        setattr(current_state, key, value)
                        logger.info(f"상태 업데이트: {key}")
                
                # 중간 상태 저장
                try:
                    temp_dir = os.path.join("ai_agent/outputs/states", "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_state_path = current_state.save_state(
                        directory=temp_dir
                    )
                    logger.info(f"중간 상태 저장 완료: {temp_state_path}")
                except Exception as e:
                    logger.error(f"중간 상태 저장 실패: {e}")
            
            # 상태 업데이트 (step의 "state" 키가 있는 경우에만)
            if step.get("state") is not None:
                current_state = step.get("state")
                logger.info("워크플로우 상태 갱신됨")
            
            # 완료된 경우
            if current_state.workflow_status == "completed" or node == "end":
                logger.info("워크플로우 완료 감지됨")
                break
        
        # 워크플로우 상태 완료로 설정
        current_state.workflow_status = "completed"
        logger.info("워크플로우 상태 완료로 설정됨")
        
        # 워크플로우 완료 후 처리
        if hasattr(current_state, "report_path") and current_state.report_path:
            # TXT 파일 경로에서 PDF 파일 경로 추출
            pdf_path = current_state.report_path.replace('.txt', '.pdf')
            
            if os.path.exists(current_state.report_path):
                logger.info(f"보고서 생성 확인됨: {current_state.report_path} (TXT)")
                print(f"\n보고서가 생성되었습니다:")
                print(f"- TXT: {current_state.report_path}")
                
                if os.path.exists(pdf_path):
                    logger.info(f"PDF 보고서 확인됨: {pdf_path}")
                    print(f"- PDF: {pdf_path}")
                else:
                    logger.warning(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            else:
                logger.warning(f"TXT 파일을 찾을 수 없습니다: {current_state.report_path}")
                print("\n보고서 파일을 찾을 수 없습니다.")
        else:
            logger.warning("보고서 경로가 설정되지 않았습니다.")
            print("\n보고서 생성에 실패했습니다.")
        
        # 최종 상태 저장
        final_state_path = current_state.save_state()
        logger.info(f"최종 상태 저장 완료: {final_state_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"시스템 실행 중 오류 발생: {e}")
        print(f"오류 발생: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 