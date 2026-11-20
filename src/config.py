"""프로젝트 공통 설정: 경로, 인증키, 분석 대상 업종."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

load_dotenv(ROOT / ".env")
DART_API_KEY = os.getenv("DART_API_KEY", "")

# 분석 대상 산업: 표준산업분류(KSIC) 코드의 앞자리로 판별한다.
# DART의 induty_code는 '10', '108', '10712'처럼 길이가 제각각이라 접두어로 비교한다.
TARGET_INDUSTRIES = {
    "식료품": ["10"],
    "음료": ["11"],
    "화장품": ["20423"],
    "의류·패션": ["14"],
}

# 상장 구분: Y=유가증권, K=코스닥 (N=코넥스, E=기타는 제외)
TARGET_MARKETS = {"Y": "유가증권", "K": "코스닥"}

# 지주회사로 의심되는 이름 (제외하지 않고 표시만 해서 강건성 검증에 쓴다)
HOLDING_KEYWORDS = ["홀딩스", "지주", "Holdings"]
