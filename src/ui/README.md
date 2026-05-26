# StockAI API 엔드포인트 명세

> **Base URL:** `http://localhost:5000`  
> **Content-Type:** `application/json`

---

## 1. 인증 (Auth)

### 회원가입
- **Method:** `POST`
- **URL:** `/register`
- **Request Body:**
```json
{
  "id": "hong123",
  "password": "pass1234",
  "email": "hong@email.com",
  "nickname": "홍길동"
}
```
- **Response (성공 200):**
```json
{
  "message": "success"
}
```
- **Response (실패 400):**
```json
{
  "message": "이미 존재하는 아이디입니다"
}
```

---

### 로그인
- **Method:** `POST`
- **URL:** `/login`
- **Request Body:**
```json
{
  "id": "hong123",
  "password": "pass1234"
}
```
- **Response (성공 200):**
```json
{
  "message": "success",
  "user_id": "hong123",
  "nickname": "홍길동"
}
```
- **Response (실패 401):**
```json
{
  "message": "아이디 또는 비밀번호가 올바르지 않습니다"
}
```

---

## 2. 주식 검색 (Stocks)

### 종목 검색
- **Method:** `GET`
- **URL:** `/stocks/search`
- **Query Parameter:**

| 파라미터 | 타입 | 예시 | 설명 |
|----------|------|------|------|
| `query` | string | `삼성전자` | 종목명 또는 종목코드 |

- **요청 예시:** `GET /stocks/search?query=삼성전자`
- **Response (성공 200):**
```json
[
  {
    "name": "삼성전자",
    "code": "005930",
    "price": "71500",
    "change": 2.3
  },
  {
    "name": "삼성바이오로직스",
    "code": "207940",
    "price": "850000",
    "change": -0.8
  }
]
```

---

## 3. 포트폴리오 (Portfolio)

### 즐겨찾기 추가
- **Method:** `POST`
- **URL:** `/portfolio`
- **Request Body:**
```json
{
  "user_id": "hong123",
  "stock_code": "005930",
  "stock_name": "삼성전자"
}
```
- **Response (성공 200):**
```json
{
  "message": "success"
}
```
- **Response (실패 409):**
```json
{
  "message": "이미 추가된 종목입니다"
}
```

---

### 즐겨찾기 제거
- **Method:** `DELETE`
- **URL:** `/portfolio`
- **Request Body:**
```json
{
  "user_id": "hong123",
  "stock_code": "005930"
}
```
- **Response (성공 200):**
```json
{
  "message": "success"
}
```
- **Response (실패 404):**
```json
{
  "message": "존재하지 않는 종목입니다"
}
```

---

## 4. 전체 요약

| 기능 | Method | URL | 비고 |
|------|--------|-----|------|
| 회원가입 | `POST` | `/register` | id, password, email, nickname |
| 로그인 | `POST` | `/login` | id, password |
| 종목 검색 | `GET` | `/stocks/search` | query 파라미터 |
| 즐겨찾기 추가 | `POST` | `/portfolio` | user_id, stock_code, stock_name |
| 즐겨찾기 제거 | `DELETE` | `/portfolio` | user_id, stock_code |

---

## 5. 공통 에러 응답

| 상태코드 | 의미 |
|----------|------|
| `200` | 성공 |
| `400` | 잘못된 요청 (필드 누락 등) |
| `401` | 인증 실패 |
| `404` | 리소스 없음 |
| `409` | 중복 충돌 |
| `500` | 서버 내부 오류 |

> 실패 시 항상 `{ "message": "에러 내용" }` 형태로 응답해주세요.

---

## 6. 종목 상세 분석 (LLM)

### 종목 AI 분석 조회
- **Method:** `GET`
- **URL:** `/stocks/<code>/analysis`
- **URL Parameter:**

| 파라미터 | 타입 | 예시 | 설명 |
|----------|------|------|------|
| `code` | string | `005930` | 종목 코드 |

- **요청 예시:** `GET /stocks/005930/analysis`
- **Response (성공 200):**
```json
{
  "name": "삼성전자",
  "code": "005930",
  "price": "71500",
  "change": 2.3,
  "recommend": true,
  "confidence": 82,
  "summary": "반도체 수출 증가와 HBM 수요 급증으로 단기 상승 모멘텀이 강하게 형성되어 있습니다.",
  "positives": [
    "2분기 반도체 수출액 전년 대비 34% 증가",
    "HBM3E 엔비디아 공급 계약 체결 보도"
  ],
  "negatives": [
    "중국 반도체 자급률 상승으로 장기 수요 불확실"
  ],
  "detail_analysis": "최근 5일간 뉴스 128건을 분석한 결과...",
  "related_news": [
    {
      "id": 1,
      "sentiment": "positive",
      "time": "5분 전",
      "title": "삼성전자, HBM3E 엔비디아 공급 계약 체결",
      "desc": "삼성전자가 엔비디아와 HBM3E 메모리 공급 계약을 체결했다."
    }
  ]
}
```
> `sentiment` 값: `"positive"` | `"negative"` | `"neutral"`

- **Response (실패 404):**
```json
{
  "message": "존재하지 않는 종목 코드입니다"
}
```

---

## 전체 요약 (업데이트)

| 기능 | Method | URL | 비고 |
|------|--------|-----|------|
| 회원가입 | `POST` | `/register` | id, password, email, nickname |
| 로그인 | `POST` | `/login` | id, password |
| 종목 검색 | `GET` | `/stocks/search` | query 파라미터 |
| 종목 AI 분석 조회 | `GET` | `/stocks/<code>/analysis` | code = 종목코드 |
| 즐겨찾기 추가 | `POST` | `/portfolio` | user_id, stock_code, stock_name |
| 즐겨찾기 제거 | `DELETE` | `/portfolio` | user_id, stock_code |
