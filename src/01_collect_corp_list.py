"""1단계: 분석 대상 상장사 후보 목록 만들기.

실행:  python src/01_collect_corp_list.py
결과:  data/processed/corp_candidates.csv

순서
 1. corpCode.xml로 전체 기업의 고유번호(corp_code)와 종목코드를 받는다.
 2. 종목코드가 있는 회사(상장 이력 있음)만 남긴다.
 3. 각 회사의 company.json(기업개황)을 받아 업종코드·상장구분·결산월을 붙인다.
 4. 업종코드가 대상 산업에 해당하고 유가증권·코스닥 상장인 회사만 남긴다.

상장사는 약 2,700곳이라 3번에서 company.json을 2,700번 정도 부른다(하루 한도 2만 건 안).
처음 한 번만 10분 남짓 걸리고, 이후에는 저장된 파일을 읽어서 바로 끝난다.
"""
import xml.etree.ElementTree as ET

import pandas as pd

from config import HOLDING_KEYWORDS, PROCESSED_DIR, RAW_DIR, TARGET_INDUSTRIES, TARGET_MARKETS
from dart_client import download_corp_code_xml, get_json


def load_corp_codes(xml_path) -> pd.DataFrame:
    root = ET.parse(xml_path).getroot()
    rows = [
        {
            "corp_code": el.findtext("corp_code", "").strip(),
            "corp_name": el.findtext("corp_name", "").strip(),
            "stock_code": el.findtext("stock_code", "").strip(),
            "modify_date": el.findtext("modify_date", "").strip(),
        }
        for el in root.iter("list")
    ]
    return pd.DataFrame(rows)


def classify_industry(induty_code: str) -> str | None:
    """업종코드를 대상 산업 이름으로 바꾼다. 해당 없으면 None.

    긴 접두어부터 비교해 '20423'(화장품)이 다른 규칙보다 먼저 잡히게 한다.
    """
    code = str(induty_code or "").strip()
    rules = sorted(
        ((p, name) for name, prefixes in TARGET_INDUSTRIES.items() for p in prefixes),
        key=lambda x: -len(x[0]),
    )
    for prefix, name in rules:
        if code.startswith(prefix):
            return name
    return None


def fetch_company_info(corp_code: str) -> dict:
    return get_json(
        "company.json",
        {"corp_code": corp_code},
        RAW_DIR / "company" / f"{corp_code}.json",
    )


def main():
    xml_path = download_corp_code_xml()
    corps = load_corp_codes(xml_path)
    listed = corps[corps["stock_code"] != ""].reset_index(drop=True)
    print(f"전체 {len(corps):,}곳 중 종목코드가 있는 회사 {len(listed):,}곳")

    records = []
    for i, row in listed.iterrows():
        info = fetch_company_info(row["corp_code"])
        records.append(
            {
                "corp_code": row["corp_code"],
                "corp_name": row["corp_name"],
                "stock_code": row["stock_code"],
                "corp_cls": info.get("corp_cls", ""),
                "induty_code": info.get("induty_code", ""),
                "acc_mt": info.get("acc_mt", ""),
                "est_dt": info.get("est_dt", ""),
            }
        )
        if (i + 1) % 200 == 0:
            print(f"  기업개황 {i + 1:,}/{len(listed):,}")

    df = pd.DataFrame(records)
    df["industry"] = df["induty_code"].map(classify_industry)
    df = df[df["industry"].notna() & df["corp_cls"].isin(TARGET_MARKETS)].copy()

    df["market"] = df["corp_cls"].map(TARGET_MARKETS)
    df["is_holding"] = df["corp_name"].str.contains("|".join(HOLDING_KEYWORDS))
    df["dec_fiscal_year"] = df["acc_mt"] == "12"  # 12월 결산이 아니면 연도 비교에 주의

    df = df.sort_values(["industry", "market", "corp_name"])
    cols = ["industry", "corp_name", "stock_code", "corp_code", "market",
            "induty_code", "acc_mt", "dec_fiscal_year", "is_holding", "est_dt"]
    out = PROCESSED_DIR / "corp_candidates.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(out, index=False, encoding="utf-8-sig")  # 엑셀에서 한글이 깨지지 않게

    print(f"\n후보 {len(df)}곳 → {out}")
    print(df.groupby(["industry", "market"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
