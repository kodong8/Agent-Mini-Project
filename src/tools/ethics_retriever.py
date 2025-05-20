from loguru import logger
import os
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# 윤리 기준 검색 도구 설명
ETHICS_RETRIEVER_DESCRIPTION = """
다음과 같은 경우에 이 도구를 사용하세요:
1. 특정 윤리 기준(EU AI Act, UNESCO AI Ethics, OECD AI Principles)에 대한 정보가 필요할 때
2. AI 서비스와 관련된 윤리적 요구사항을 검색해야 할 때
3. 윤리 기준에서 특정 주제나 개념에 대한 내용을 찾아야 할 때

검색어를 구체적으로 작성할수록 더 관련성 높은 정보를 얻을 수 있습니다.
"""

def create_ethics_retriever_tool(vector_db, llm):
    """윤리 기준 검색 도구를 생성합니다."""
    
    async def ethics_retriever_function(query: str, framework: str = "all"):
        """윤리 기준 검색 함수"""
        try:
            logger.info(f"윤리 기준 검색: {query} (프레임워크: {framework})")
            
            # 기본 검색기 설정 - 프레임워크 필터 제거
            retriever = vector_db.as_retriever(
                search_kwargs={"k": 5}
            )
            
            # 컨텍스트 압축 검색기 설정 (더 관련성 높은 결과 추출)
            compressor = LLMChainExtractor.from_llm(llm)
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=retriever
            )
            
            # 검색 수행
            docs = compression_retriever.invoke(query)
            
            # 결과 정리
            if not docs:
                logger.warning(f"윤리 기준 검색 결과 없음: {query}")
                return AIMessage(content=f"'{query}'에 대한 관련 윤리 기준을 찾을 수 없습니다.")
            
            results = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("framework", "Unknown")
                page = doc.metadata.get("page", "Unknown")
                results.append(f"### 결과 {i} ({source} - 페이지 {page})\n{doc.page_content}\n")
            
            content = "\n".join(results)
            logger.info(f"윤리 기준 검색 완료: {len(docs)}개 결과")
            
            return AIMessage(content=content)
        except Exception as e:
            logger.error(f"윤리 기준 검색 실패: {e}")
            return AIMessage(content=f"윤리 기준 검색 중 오류가 발생했습니다: {e}")
    
    return ethics_retriever_function 