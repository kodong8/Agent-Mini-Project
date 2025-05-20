import os
import json
import markdown
from weasyprint import HTML, CSS
from datetime import datetime
from loguru import logger

def save_json(data, filename, directory="outputs/states"):
    """JSON 데이터를 파일로 저장합니다."""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON 파일 저장 완료: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"JSON 파일 저장 실패: {e}")
        raise

def load_json(filepath):
    """JSON 파일을 로드합니다."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"JSON 파일 로드 완료: {filepath}")
        return data
    except Exception as e:
        logger.error(f"JSON 파일 로드 실패: {e}")
        raise

def save_report(content, service_name, criteria, directory="outputs/reports"):
    """보고서를 TXT 파일과 PDF 파일로 저장합니다."""
    try:
        # 디렉토리 생성
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{service_name}_{criteria}_{timestamp}"
        
        # TXT 파일 저장 경로
        txt_filename = f"{base_filename}.txt"
        txt_filepath = os.path.join(directory, txt_filename)
        
        # PDF 파일 저장 경로
        pdf_filename = f"{base_filename}.pdf"
        pdf_filepath = os.path.join(directory, pdf_filename)
        
        # TXT 파일 저장
        with open(txt_filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"TXT 보고서 저장 완료: {txt_filepath}")
        
        # 마크다운을 HTML로 변환
        try:
            html_content = markdown.markdown(content)
            
            # 기본 스타일 추가
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{service_name} - {criteria} 윤리 평가 보고서</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 2cm; }}
                    h1 {{ color: #333366; }}
                    h2 {{ color: #336699; margin-top: 1.5em; }}
                    h3 {{ color: #339999; margin-top: 1.2em; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .footer {{ text-align: center; font-size: 0.8em; margin-top: 2em; color: #666; }}
                </style>
            </head>
            <body>
                {html_content}
                <div class="footer">생성 시간: {timestamp}</div>
            </body>
            </html>
            """
            
            # HTML을 PDF로 변환
            HTML(string=styled_html).write_pdf(pdf_filepath)
            logger.info(f"PDF 보고서 저장 완료: {pdf_filepath}")
        except Exception as pdf_error:
            logger.error(f"PDF 변환 중 오류: {pdf_error}")
            pdf_filepath = None
        
        # 파일 경로 반환
        return {
            "txt_path": txt_filepath,
            "pdf_path": pdf_filepath
        }
    except Exception as e:
        logger.error(f"보고서 저장 실패: {e}")
        raise 