# PostgreSQL 초기화

`create_tables.sh`는 환경변수 `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`을 사용합니다.
대상 DB를 미리 만든 뒤 실행하면 해당 DB에 스키마와 테이블을 생성합니다.
DB 이름을 `coins`로 강제 변경하지 않으며, SQL 오류 시 즉시 종료합니다.

```bash
bash src/sql/create_tables.sh
```

`database_coins.sql`은 이름이 `coins`인 DB를 처음 만들 때만 수동으로 실행하는 예시입니다.
`CREATE TABLE IF NOT EXISTS`는 기존 테이블의 컬럼을 변경하지 않습니다.
