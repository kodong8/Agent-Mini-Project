import os
from dotenv import load_dotenv
from loguru import logger

def load_config():
    """환경 변수를 로드합니다."""
    # .env 파일 로드
    load_dotenv()
    
    # 필수 환경 변수 확인
    required_vars = [
        "OPENAI_API_KEY",
        "SERPER_API_KEY",
        "EMBEDDING_MODEL",
        "LLM_MODEL",
        "CHROMA_DB_PATH"
    ]
    
    config = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        config[var.lower()] = value
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("환경 변수를 .env 파일에 설정해주세요.")
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    logger.info("환경 설정 로드 완료")
    return config 