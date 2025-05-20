import os
from dotenv import load_dotenv
from src.utils import setup_logger
from src.core import (
    get_llm,
    get_embeddings,
    load_ethics_frameworks_to_db,
    create_ethics_workflow
)

def main():
    """워크플로우 시각화 스크립트"""
    # 환경 변수 로드
    load_dotenv()
    
    # 로거 설정
    setup_logger()
    
    # 모델 초기화
    llm = get_llm(model_name=os.getenv("LLM_MODEL", "gpt-4o"))
    embeddings = get_embeddings(model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    
    # 윤리 프레임워크 벡터 DB 로드
    ethics_db = load_ethics_frameworks_to_db(embeddings, vector_db_path=os.getenv("VECTOR_DB_PATH"))
    
    # 워크플로우 생성
    workflow = create_ethics_workflow(llm, ethics_db)
    
    # 다이어그램 생성
    try:
        # 저장 디렉토리 생성
        os.makedirs("outputs", exist_ok=True)
        
        # 다이어그램 생성 및 저장
        workflow.write_html("outputs/ethics_workflow_diagram.html")
        print(f"워크플로우 다이어그램이 생성되었습니다: {os.path.abspath('outputs/ethics_workflow_diagram.html')}")
        
        return 0
    except Exception as e:
        print(f"다이어그램 생성 중 오류 발생: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 