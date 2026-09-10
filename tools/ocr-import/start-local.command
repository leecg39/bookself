#!/bin/zsh
set -eu
cd "${0:A:h}/../.."
export PATH="/opt/homebrew/opt/node@25/bin:$HOME/.local/bin:$PATH"
if ! docker compose -f local/docker-compose.ocr.yml up -d --wait; then
  print '로컬 DB를 시작하지 못했습니다. Docker VM 상태와 디스크 여유 공간을 확인하세요.'
  exit 1
fi
if [[ ! -f server/dist/main.js ]]; then
  pnpm run build:server
fi
if curl -fsS http://127.0.0.1:3147/api/v1/health >/dev/null 2>&1; then
  print 'API가 이미 실행 중입니다.'
else
  (cd server && node --env-file=.env dist/main.js) > local/server-launch.log 2>&1 &
  BOOKORBIT_API_PID=$!
fi
if curl -fsS http://127.0.0.1:5179/ >/dev/null 2>&1; then
  open http://127.0.0.1:5179/library/1
else
  BOOKORBIT_API_URL=http://127.0.0.1:3147 pnpm --filter client dev --host 127.0.0.1 --port 5179 > local/client-launch.log 2>&1 &
  BOOKORBIT_CLIENT_PID=$!
  print '책장 주소: http://127.0.0.1:5179/library/1'
fi
function stop_local_children() {
  [[ -z "${BOOKORBIT_API_PID:-}" ]] || kill "$BOOKORBIT_API_PID" 2>/dev/null || true
  [[ -z "${BOOKORBIT_CLIENT_PID:-}" ]] || kill "$BOOKORBIT_CLIENT_PID" 2>/dev/null || true
}
trap stop_local_children EXIT INT TERM
wait
