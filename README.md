# 소비재 상장사 마케팅비 효율 분석

국내 식음료·화장품·패션 상장사의 광고선전비와 판매촉진비가 매출과 이익으로 얼마나 돌아오는지
OpenDART 공시 데이터로 분석하는 프로젝트입니다.

## 폴더 구조

```
├── data/
│   ├── raw/          # API에서 받은 원본 (GitHub에 올리지 않음, 다시 받을 수 있음)
│   └── processed/    # 정리된 CSV (GitHub에 올림)
├── src/
│   ├── config.py                 # 경로, 인증키, 대상 업종 설정
│   ├── dart_client.py            # OpenDART 호출 + 로컬 저장
│   └── 01_collect_corp_list.py   # 대상 상장사 후보 목록 만들기
├── notebooks/        # 탐색·시각화용 주피터 노트북
├── docs/             # 계정명 매핑표, 검증 기록, 보고서
├── requirements.txt
└── .env.example      # 인증키 예시 (.env로 복사해서 사용)
```

## 시작하기

```bash
pip install -r requirements.txt
cp .env.example .env          # .env 안에 OpenDART 인증키를 넣는다
python src/01_collect_corp_list.py
```

결과는 `data/processed/corp_candidates.csv`에 저장됩니다. 처음 실행할 때는 상장사 약 2,700곳의
기업개황을 받느라 10분 남짓 걸리고, 그다음부터는 저장된 파일을 읽어서 바로 끝납니다.
중간에 멈춰도 다시 실행하면 이어서 받습니다.

## 대상 산업

| 산업 | KSIC 코드 |
|---|---|
| 식료품 | C10 |
| 음료 | C11 |
| 화장품 | C20423 |
| 의류·패션 | C14 |

DART의 업종코드는 영문자 없이 숫자만 쓰고 자릿수도 회사마다 달라서(`10`, `108`, `10712` 등),
코드 앞자리로 비교합니다. 대상 업종은 `src/config.py`의 `TARGET_INDUSTRIES`만 바꾸면 늘리거나 바꿀 수 있습니다.

## 후보 목록의 열

| 열 | 뜻 |
|---|---|
| `industry` | 대상 산업 분류 |
| `market` | 유가증권 / 코스닥 |
| `induty_code` | DART 업종코드 원본 |
| `acc_mt`, `dec_fiscal_year` | 결산월, 12월 결산 여부 (다른 달이면 연도 비교에 주의) |
| `is_holding` | 이름에 '홀딩스'나 '지주'가 들어간 회사 (제외하지 않고 표시만 함) |

## 알아둘 한계

- 지주회사는 보통 업종코드가 지주회사(715)로 잡혀 있어 처음부터 목록에 잘 들어오지 않습니다.
  그래도 이름으로 한 번 더 표시합니다.
- `company.json`은 지금 기준의 상장 구분을 알려주므로 이미 상장폐지된 회사는 빠집니다.
  분석 기간 중에 사라진 회사가 빠지는 생존 편향이 있다는 점을 보고서에 적어 둡니다.
