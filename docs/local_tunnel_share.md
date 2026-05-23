# 로컬 서버 터널 공유 가이드

GitHub Pages나 Netlify Drop은 정적 프론트만 공유하므로 FastAPI/MySQL API 연결은 동작하지 않습니다. 실제 로컬 DB와 API가 연결된 화면을 팀원에게 보여주려면 로컬 서버를 켜고 Cloudflare Tunnel 같은 임시 터널을 사용하면 됩니다.

## 공유 구조

```text
팀원 브라우저
→ Cloudflare Tunnel 공개 URL
→ 내 컴퓨터의 Vue 개발 서버 5173
→ Vue /api 요청
→ 내 컴퓨터의 FastAPI 서버 8000
→ 내 컴퓨터의 MySQL 3307
```

## 실행 순서

### 1. MySQL 실행 확인

MySQL 서버가 `3307` 포트로 실행 중이어야 합니다.

### 2. FastAPI 실행

```powershell
cd C:\Users\tmdql\Desktop\DB_project

$env:DB_HOST="localhost"
$env:DB_PORT="3307"
$env:DB_USER="root"
$env:DB_PASSWORD="1234"
$env:DB_NAME="stock_prediction_db"

python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### 3. Vue 실행

```powershell
cd C:\Users\tmdql\Desktop\DB_project\frontend
npm.cmd run dev
```

### 4. Cloudflare Tunnel 실행

`cloudflared.exe`가 있는 위치에서 다음 명령을 실행합니다.

```powershell
cloudflared.exe tunnel --url http://127.0.0.1:5173
```

터미널에 표시되는 `https://...trycloudflare.com` 주소를 팀원에게 공유하면 됩니다.

## 주의할 점

- 내 컴퓨터가 켜져 있어야 합니다.
- MySQL, FastAPI, Vue, Cloudflare Tunnel이 모두 실행 중이어야 합니다.
- 터널 창을 닫으면 공유 링크도 끊깁니다.
- 무료 quick tunnel 링크는 다시 실행할 때마다 바뀔 수 있습니다.
- 이 방식은 발표/테스트용 임시 공유에 적합합니다.

## Vite 설정

Cloudflare Tunnel 주소로 접속하면 Vite 개발 서버가 외부 Host를 차단할 수 있습니다. 그래서 `frontend/vite.config.js`에 아래 설정을 추가했습니다.

```js
server: {
  allowedHosts: [".trycloudflare.com"],
}
```

