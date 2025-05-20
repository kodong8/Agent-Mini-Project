# AI 윤리성 리스크 진단 시스템

## 프로젝트 개요
이 프로젝트는 AI 서비스의 윤리적 리스크를 자동으로 진단하고 평가하는 시스템입니다. 주요 AI 윤리 프레임워크(EU AI Act, UNESCO AI Ethics, OECD AI Principles)를 기반으로 서비스를 분석하고, 잠재적인 윤리적 문제점을 식별하며, 개선 방안을 제시합니다.

## 주요 기능
- AI 서비스 윤리적 리스크 분석
- 주요 윤리 프레임워크 기반 평가
- 자동화된 리스크 평가 및 보고서 생성
- 상세한 분석 보고서 자동 생성
- 개선을 위한 구체적인 권고사항 제시

## 기술 스택
| 구분 | 기술 |
|------|------|
| 프레임워크 | LangChain, Python |
| LLM | GPT-4o |
| 벡터DB | FAISS, ChromaDB |
| 저장소 | JSON, Markdown |

## 에이전트 구성
1. 서비스 입력 에이전트: 사용자로부터 입력받은 AI 서비스를 ToolNode를 활용해 웹 검색 툴콜링 수행. Serpapi Web search tool 사용해 정보 수집
2. 기준 검색 에이전트: 선택된 윤리 기준과 AI 서비스, 서비스 입력 에이전트 리턴 메시지를 입력받아 ChromaDB에서 관련 윤리 기준 검색
3. 윤리 평가 에이전트: 서비스 입력 에이전트와 기준 검색 에이전트 정보를 바탕으로 GPT-4o 사용해 윤리 리스크 분석
4. 보고서 생성 에이전트: 수집된 정보를 바탕으로 보고서 형식에 따라 txt 파일 작성

## State
**AI_service**: 보고서의 대상이 될 AI 서비스 이름. 이용자가 입력한 String 형태
**service_info**: 서비스 입력 에이전트가 생성한 AI_service의 설명. message 형태
**criteria**: 선택한 윤리 기준 (예: EU AI Act). 이용자가 입력한 string 형태
**criteria_info**: 기준 검색 에이전트가 생성한 관련 윤리 기준에 대한 내용 message 형태
**risk_message**: 윤리 평가 에이전트의 Output 값. service_info와 ciriteria_info 정보를 활용해서 AI_service에서 발생할 수 있는 윤리적 리스크에 대한 내용과 생성된 권고 사항. message 형태
**state_score**: 워크플로우 상태 추적을 할 수 있는 state임. 각 state의 대한 정보에 질을 평가한 점수이며 list 형태로 표시. 만약, 답변의 퀄리티가 낮아 점수가 낮다면 해당 노드로 돌아가서 작업을 다시 수행함. 

## 설치 방법

1. 레포지토리 클론
```bash
git clone <repository_url>
cd ai_agent
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
```
`.env` 파일을 편집하여 필요한 API 키와 설정 입력

## 사용 방법

### 1. 시스템 실행

```bash
python main.py --service "분석할 AI 서비스명" --criteria "EU AI Act"
```

옵션:
- `--service` 또는 `-s`: 분석할 AI 서비스 이름 (필수)
- `--criteria` 또는 `-c`: 적용할 윤리 기준 (기본값: "EU AI Act")
  - 가능한 선택지: "EU AI Act", "UNESCO AI Ethics", "OECD AI Principles"

### 2. 결과 확인

분석이 완료되면 보고서가 `ai_agent/outputs/reports/` 디렉토리에 생성됩니다.
상태 정보는 `ai_agent/outputs/states/` 디렉토리에 JSON 형식으로 저장됩니다.

### 3. 워크플로우 시각화

```bash
python visualize_workflow.py
```

위 명령어를 실행하면 `ai_agent/outputs/ethics_workflow_diagram.html` 파일이 생성됩니다.
이 파일은 웹 브라우저에서 열어서 전체 워크플로우의 시각적 다이어그램을 확인할 수 있습니다.

## 프로젝트 구조
```
ai_agent/
├── src/
│   ├── agents/           # 에이전트 구현
│   ├── core/             # 핵심 기능 (workflow, state 등)
│   ├── prompts/          # 프롬프트 템플릿
│   ├── tools/            # 에이전트 도구(websearch, retriever)
│   └── utils/            # 유틸리티 함수
├── outputs/
│   ├── reports/          # 생성된 보고서
│   └── states/           # 시스템 상태
├── tests/                # 테스트 코드
├── main.py               # 메인 실행 스크립트
├── visualize_workflow.py # 워크플로우 시각화 스크립트
└── requirements.txt      # 의존성 패키지
```

## 기여자
- 고동현: Prompt Engineering, Agent Design

# Python 관련
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# 가상 환경
venv/
env/
ENV/
.env

# IDE 관련
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# 로그 및 출력 파일
ai_agent/logs/
ai_agent/outputs/
logs/
*.log
*.txt
*.pdf

# 벡터 데이터베이스 (필요시 주석 해제)
# ./data/vectorstore/

# 모델 관련 파일
*.bin
*.pt
*.pth
*.h5
*.onnx
*.tflite

# API 키 및 민감한 정보
.env
secrets.json
credentials.json

# 임시 파일
.ipynb_checkpoints/
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/
.hypothesis/
.coverage.*
coverage.xml
*.cover
.cache/
nosetests.xml
coverage.xml

# 시스템 파일
.DS_Store
Thumbs.db