from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger
import os

def get_llm(model_name="gpt-4o", temperature=0.0):
    """LLM 모델을 초기화합니다."""
    try:
        logger.info(f"LLM 모델 초기화: {model_name}")
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        return llm
    except Exception as e:
        logger.error(f"LLM 모델 초기화 실패: {e}")
        raise

def get_embeddings(model_name="BAAI/bge-m3"):
    """임베딩 모델을 초기화합니다."""
    try:
        logger.info(f"임베딩 모델 초기화: {model_name}")
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        return embeddings
    except Exception as e:
        logger.error(f"임베딩 모델 초기화 실패: {e}")
        raise 