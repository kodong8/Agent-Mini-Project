from loguru import logger
import sys
import os

# 로그 설정
def setup_logger():
    """로그 설정을 초기화합니다."""
    
    # 로그 디렉토리 생성
    os.makedirs("ai_agent/logs", exist_ok=True)
    
    # 콘솔에 로그 출력 설정
    logger.remove()  # 기본 핸들러 제거
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # 파일에 로그 출력 설정
    logger.add("ai_agent/logs/ai_ethics.log", rotation="10 MB", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
    
    logger.info("로거 설정 완료")
    return logger 