"""OpenDART API 호출 도우미.

한 번 받은 응답은 data/raw 아래에 저장해 두고, 다시 실행하면 저장된 파일을 읽는다.
키 하나당 하루 약 2만 건 한도가 있으므로 같은 요청을 두 번 보내지 않는 것이 핵심이다.
"""
import io
import json
import time
import zipfile
from pathlib import Path

import requests

from config import DART_API_KEY, RAW_DIR

BASE_URL = "https://opendart.fss.or.kr/api"
SLEEP_SEC = 0.15  # 호출 사이 간격 (분당 1,000건 이하로 유지)

# OpenDART status 코드 중 의미 있는 것들
STATUS_OK = "000"
STATUS_NO_DATA = "013"
STATUS_LIMIT = "020"


class DartError(RuntimeError):
    pass


def _require_key():
    if not DART_API_KEY:
        raise DartError(".env 파일에 DART_API_KEY가 없습니다. .env.example을 참고하세요.")


def get_json(endpoint: str, params: dict, cache_path: Path) -> dict:
    """JSON 엔드포인트를 호출하고 결과를 cache_path에 저장한다.

    정상(000)과 데이터 없음(013)만 저장한다. 오류는 저장하지 않아 다음에 다시 시도된다.
    """
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    _require_key()
    resp = requests.get(
        f"{BASE_URL}/{endpoint}",
        params={"crtfc_key": DART_API_KEY, **params},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    status = data.get("status")

    if status == STATUS_LIMIT:
        raise DartError("오늘 호출 한도를 넘었습니다. 내일 다시 실행하면 이어서 받습니다.")
    if status not in (STATUS_OK, STATUS_NO_DATA):
        raise DartError(f"{endpoint} 오류 {status}: {data.get('message')}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    time.sleep(SLEEP_SEC)
    return data


def download_corp_code_xml(force: bool = False) -> Path:
    """전체 기업 고유번호 파일(CORPCODE.xml)을 받아 data/raw에 저장한다."""
    out = RAW_DIR / "CORPCODE.xml"
    if out.exists() and not force:
        return out

    _require_key()
    resp = requests.get(f"{BASE_URL}/corpCode.xml", params={"crtfc_key": DART_API_KEY}, timeout=60)
    resp.raise_for_status()
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            name = zf.namelist()[0]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(zf.read(name))
    except zipfile.BadZipFile:
        # 키가 틀리면 zip 대신 오류 메시지(XML/JSON)가 온다
        raise DartError(f"corpCode.xml 응답이 zip이 아닙니다: {resp.text[:200]}")
    return out
