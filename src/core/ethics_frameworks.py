from loguru import logger
import os
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.document_loaders import PyMuPDFLoader

file_path = "data/eu_ai_act.pdf"

def create_documents(file_path):
    """PDF 파일을 문서로 변환하고 청크로 나눕니다."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    
    loader = PyMuPDFLoader(file_path)
    docs = loader.load()
        
    # 문서를 청크로 나누기
    split_documents = text_splitter.split_documents(docs)
    
    # 각 문서에 framework 메타데이터 추가
    for doc in split_documents:
        if 'metadata' not in doc:
            doc.metadata = {}
        doc.metadata['framework'] = 'EU_AI_Act'
    
    logger.info(f"분할된 청크의 수: {len(split_documents)}")
    return split_documents

def load_ethics_frameworks_to_db(embeddings, faiss_path="data/vectorstore"):
    """윤리 프레임워크를 벡터 데이터베이스에 로드합니다."""
    try:
        logger.info(f"윤리 프레임워크 벡터 DB에 로드 중...")
        docs = create_documents(file_path)
        return create_or_load_faiss(docs, embeddings, faiss_path)
    except Exception as e:
        logger.error(f"윤리 프레임워크 벡터 DB 로드 실패: {e}")
        raise

def create_or_load_faiss(documents, embeddings, persist_directory):
    """FAISS 벡터 데이터베이스를 생성하거나 로드합니다."""
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(persist_directory, exist_ok=True)
        
        # FAISS 인덱스 파일이 있는지 확인
        index_file = os.path.join(persist_directory, "index.faiss")
        if os.path.exists(index_file):
            logger.info(f"기존 FAISS 데이터베이스 로드: {persist_directory}")
            return FAISS.load_local(persist_directory, embeddings, allow_dangerous_deserialization=True)
        else:
            logger.info(f"새로운 FAISS 데이터베이스 생성: {persist_directory}")
            vector_db = FAISS.from_documents(documents, embeddings)
            # 저장
            vector_db.save_local(persist_directory)
            logger.info(f"FAISS 데이터베이스 저장 완료: {persist_directory}")
            return vector_db
    except Exception as e:
        logger.error(f"FAISS 데이터베이스 초기화 실패: {e}")
        raise


