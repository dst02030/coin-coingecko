# CoinGecko collection

설정된 수집 모드를 독립 실행해 PostgreSQL에 저장합니다.

```bash
python -m pip install -r requirements.txt
# First checkout only: copy examples to local settings and edit credentials.
for name in credentials data.yml logging.yml webhook.yml; do
    [ -f "conf/$name" ] || cp "conf/$name.example" "conf/$name"
done
bash run.sh coins_markets
bash run.sh coins_list
```

지원 모드는 `python main.py --help`에서 확인할 수 있습니다.
`coins_markets`는 한 번 수집한 전체 데이터로 순위를 계산하고 DB 저장 후 Discord에 상위 행을 보냅니다.
알림 행 수·분할 크기는 `conf/webhook.yml`, 수집 설정은 `conf/data.yml`에서 변경합니다.

비밀정보는 Git에서 제외한 `conf/credentials`의 셸 환경변수로 보관합니다.
필수 DB 변수는 `DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`이며,
시장 알림에는 `webhook_url`이 필요합니다. 선택 API 키는 `COINGECKO_API_KEY`입니다.
Pro 키를 사용할 경우 `COINGECKO_BASE_URL`도 해당 API 주소로 지정합니다.
`run.sh`가 이 파일을 읽어 환경변수로 전달합니다. 키나 출력 로그는 커밋하지 않습니다.
기본 Conda 환경은 `jupyter`이며 `CONDA_VOLUME`, `CONDA_ENV`로 변경할 수 있습니다.

테이블 생성은 매 수집 때 실행하지 않습니다. 새 DB에서만 아래와 같이 기존 SQL을 실행합니다.
대상 데이터베이스는 미리 생성되어 있어야 합니다. SQL 오류가 발생하면 즉시 종료합니다.

```bash
set -a
source conf/credentials
set +a
bash src/sql/create_tables.sh
```

기존 테이블의 구조를 변경하는 마이그레이션은 포함하지 않습니다.
설정 로딩의 과거 함수명 `get_jinja_yaml_conf`는 노트북 호환용으로 남겨두었으며 Jinja2는 사용하지 않습니다.

```bash
python -m unittest discover -s tests -v
```
