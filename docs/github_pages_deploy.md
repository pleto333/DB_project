# GitHub Pages 배포 가이드

이 프로젝트는 팀원에게 프론트엔드 화면을 공유하기 위해 GitHub Pages 배포를 사용할 수 있습니다. GitHub Pages는 정적 파일만 호스팅하므로 FastAPI, MySQL, LS증권 API, LLM API는 Pages에서 직접 실행되지 않습니다.

## 이번 설정으로 되는 것

- `frontend/` Vue 화면을 자동 빌드
- 빌드 결과물인 `frontend/dist`를 GitHub Pages에 배포
- 백엔드 API가 없는 Pages 환경에서는 프론트에 들어 있는 `static-demo` 데이터로 화면 표시
- 팀원은 설치 없이 브라우저 링크로 화면 확인

## 이번 설정으로 안 되는 것

- MySQL DB 조회
- FastAPI 서버 실행
- 실제 LS증권 API 호출
- 실제 LLM API 호출
- DB에 새 추천 결과 저장

즉, Pages 링크는 실제 서비스 서버가 아니라 프론트 UI 공유용 데모입니다.

## 배포 방식

`.github/workflows/deploy-pages.yml` 워크플로가 `codex/stock-news-dashboard-presentation` 브랜치에 push될 때 실행됩니다.

워크플로 흐름은 다음과 같습니다.

```text
1. GitHub Actions에서 코드 checkout
2. frontend 의존성 설치
3. npm run build 실행
4. frontend/dist를 GitHub Pages artifact로 업로드
5. GitHub Pages에 배포
```

## 사용자가 GitHub에서 확인해야 할 것

아래 설정은 GitHub 웹사이트에서 repository 권한이 있는 사람이 확인해야 합니다.

1. GitHub 저장소 접속
2. `Settings` 클릭
3. 왼쪽 메뉴에서 `Pages` 클릭
4. `Build and deployment`의 `Source`를 `GitHub Actions`로 설정
5. `Actions` 탭에서 `Deploy frontend to GitHub Pages` 실행 결과 확인

배포가 성공하면 Actions 로그 또는 Settings > Pages 화면에서 Pages URL을 확인할 수 있습니다.

이 설정이 되어 있지 않으면 Actions의 `Configure Pages` 단계에서 다음과 비슷한 오류가 납니다.

```text
Get Pages site failed. Please verify that the repository has Pages enabled and configured to build using GitHub Actions.
```

이 오류는 코드 문제가 아니라 저장소 Pages 기능이 아직 켜져 있지 않아서 발생합니다. 저장소 관리자 권한이 있는 사람이 위 설정을 한 뒤 실패한 workflow를 다시 실행하면 됩니다.

## 예상 URL

저장소 이름이 `DB_project`이므로 보통 아래 주소가 됩니다.

```text
https://pleto333.github.io/DB_project/
```

GitHub 계정명이나 저장소명이 바뀌면 URL도 달라집니다.

## 팀원에게 공유할 때 설명

```text
이 링크는 프론트 화면 확인용 GitHub Pages 배포본입니다.
GitHub Pages에서는 FastAPI/MySQL/LS증권 API/LLM API가 실행되지 않기 때문에
현재 화면 데이터는 static-demo 샘플 데이터입니다.
실제 DB 연동은 로컬 백엔드 또는 별도 서버 배포 환경에서 확인해야 합니다.
```
