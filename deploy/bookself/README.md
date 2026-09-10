# Bookself Hostinger 배포

- 서비스: `https://bookself.soverin.cloud`
- VPS: `srv1655088.hstgr.cloud` (`72.61.116.250`)
- 서버 배포 경로: `/docker/bookself`
- 소스 경로: `/docker/bookself/source`
- 컨테이너: `bookself-app`, `bookself-db`
- 데이터: `/docker/bookself/data/app`, `/docker/bookself/data/postgres`
- 도서: `/docker/bookself/books`

기존 `books.soverin.cloud`의 BookOrbit와 별도 데이터베이스·볼륨·라우터를 사용합니다.
Traefik은 이 서버에서 host 네트워크로 실행되며 Docker provider로 라우터를 발견합니다.
DB는 호스트 포트를 공개하지 않습니다. 앱의 `127.0.0.1:3148` 포트는 서버 내부 관리용입니다.

## DNS

Cloudflare의 `soverin.cloud` 영역에 A 레코드 `bookself → 72.61.116.250`을 추가합니다.
최초 인증서 발급은 DNS 전용으로 연결하고, HTTPS 정상 동작을 확인합니다.
Traefik의 기존 `letsencrypt` HTTP challenge resolver가 인증서를 발급합니다.

## 환경 파일

서버의 `/docker/bookself/.env`는 소유자만 읽도록 `0600` 권한으로 보관합니다.
필수 키: `APP_IMAGE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`,
`JWT_SECRET`, `SETUP_BOOTSTRAP_TOKEN`, `APP_URL`.
현재 이미지 태그는 `bookself:1caac4e`이며 해당 소스 커밋으로 빌드합니다.
비밀값과 관리자 인증정보는 Git에 저장하지 않습니다.

## 업데이트

서버에서 새 커밋을 확인하고 이미지 태그를 변경한 다음 실행합니다.

```sh
cd /docker/bookself/source
git fetch origin
git checkout <검증한-커밋>
docker build --build-arg APP_VERSION=<짧은-커밋> -t bookself:<짧은-커밋> .
# /docker/bookself/.env의 APP_IMAGE를 새 태그로 변경
cd /docker/bookself
docker compose -f compose.yml config --quiet
docker compose -f compose.yml up -d
docker compose -f compose.yml ps
curl --fail http://127.0.0.1:3148/api/v1/health
```

초기 관리자는 bootstrap 토큰을 사용하는 `/api/v1/auth/setup`으로 생성합니다.
초기화 완료 후 `setup-status`의 `needsSetup`과 `allowRegistration`이 모두 `false`인지 확인합니다.
원격 도서 전송은 소유자가 승인한 파일에만 수행합니다.

## 복구와 보관

업데이트 전에 DB를 `pg_dump`하고 앱 데이터 및 도서 폴더를 별도 보관합니다.
스키마 마이그레이션을 포함한 업데이트의 롤백은 기존 이미지뿐 아니라 해당 DB 백업도 필요할 수 있습니다.
`docker compose down -v`, 데이터 폴더 삭제, 기존 BookOrbit 프로젝트 변경은 정상 배포 절차에 포함하지 않습니다.
