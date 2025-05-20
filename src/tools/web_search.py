from loguru import logger
import os
from langchain_core.tools import Tool
from langchain_core.messages import AIMessage
import json

# 웹 검색 도구 설명
WEB_SEARCH_DESCRIPTION = """
다음과 같은 경우에 이 도구를 사용하세요:
1. AI 서비스에 대한 추가 정보가 필요할 때
2. 서비스의 기능, 기술적 세부사항, 사용 사례 등에 대한 정보를 수집해야 할 때
3. 서비스의 최신 기능이나 업데이트에 대한 정보가 필요할 때

검색어를 구체적으로 작성할수록 더 관련성 높은 정보를 얻을 수 있습니다.
"""

class WebSearchTool(Tool):
    """Serper를 사용하여 웹 검색을 수행하는 도구"""
    
    # 도구 메타데이터
    name: str = "web_search"
    description: str = WEB_SEARCH_DESCRIPTION
    
    def __init__(self):
        super().__init__()
        # SerpAPI 키 확인
        self.serper_key = os.getenv("SERPER_API_KEY")
        if not self.serper_key:
            logger.error("SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    async def _arun(self, query: str) -> str:
        """비동기적으로 웹 검색을 수행합니다."""
        from langchain_community.utilities import GoogleSerperAPIWrapper
        
        try:
            logger.info(f"웹 검색 수행: {query}")
            # Serper 래퍼 초기화
            search = GoogleSerperAPIWrapper(serper_api_key=self.serper_key)
            
            # 검색 수행
            results = search.run(query)
            
            logger.info(f"웹 검색 완료: {len(results)} 자 결과")
            return results
        except Exception as e:
            logger.error(f"웹 검색 실패: {e}")
            return f"웹 검색 중 오류가 발생했습니다: {e}"

def create_web_search_tool():
    """웹 검색 도구를 생성합니다."""
    
    async def web_search_function(query: str):
        """웹 검색 함수"""
        try:
            # SerpAPI 키 확인
            serper_key = os.getenv("SERPER_API_KEY")
            if not serper_key:
                logger.error("SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
                return AIMessage(content="SERPER_API_KEY 환경 변수가 설정되지 않았습니다.")
            
            # SerpAPI 래퍼 초기화
            from langchain_community.utilities import GoogleSerperAPIWrapper
            search = GoogleSerperAPIWrapper(serper_api_key=serper_key)
            
            # 검색 수행
            logger.info(f"웹 검색 수행: {query}")
            results = search.run(query)
            
            logger.info(f"웹 검색 완료: {len(results)} 자 결과")
            return AIMessage(content=results)
        except Exception as e:
            logger.error(f"웹 검색 실패: {e}")
            return AIMessage(content=f"웹 검색 중 오류가 발생했습니다: {e}")
    
    return web_search_function 