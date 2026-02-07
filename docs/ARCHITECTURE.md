# WeChat Clone - 시스템 아키텍처

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         클라이언트                                │
│              (Web, iOS, Android, Desktop)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (Nginx)                         │
│  - 라우팅  - Rate Limiting  - SSL/TLS  - Load Balancing        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Auth Service  │  │  Chat Service   │  │  Media Service  │
│   Port: 8001   │  │   Port: 8002    │  │   Port: 8004    │
│   (FastAPI)    │  │  (WebSocket)    │  │   (FastAPI)     │
└────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
        │           ┌─────────▼─────────┐          │
        │           │  WebRTC Service   │          │
        │           │   Port: 8005      │          │
        │           │  (WebSocket)      │          │
        │           └───────────────────┘          │
        │                     │                     │
┌───────▼────────────────────▼─────────────────────▼────────┐
│              Shared Infrastructure Layer                   │
│  ┌──────────┐  ┌──────┐  ┌──────────┐  ┌──────────┐     │
│  │PostgreSQL│  │Redis │  │ RabbitMQ │  │  MinIO   │     │
│  │  :5432   │  │:6379 │  │   :5672  │  │  :9000   │     │
│  └──────────┘  └──────┘  └──────────┘  └──────────┘     │
└────────────────────────────────────────────────────────────┘
```

## 마이크로서비스 상세

### 1. Auth Service (인증/인가)
**책임:**
- 사용자 회원가입/로그인
- JWT 토큰 발급 및 검증
- 토큰 갱신
- 사용자 세션 관리

**기술 스택:**
- FastAPI
- SQLAlchemy (PostgreSQL)
- Redis (세션 캐싱)
- JWT + bcrypt

**주요 API:**
- POST /register - 회원가입
- POST /login - 로그인
- POST /refresh - 토큰 갱신
- GET /me - 현재 사용자 정보

### 2. Chat Service (실시간 메시징)
**책임:**
- 1:1 실시간 채팅
- 그룹 채팅
- 타이핑 인디케이터
- 읽음 확인
- 온라인/오프라인 상태 관리

**기술 스택:**
- FastAPI + WebSocket
- Redis Pub/Sub
- RabbitMQ (메시지 큐)
- PostgreSQL (메시지 저장)

**WebSocket 메시지 타입:**
- message - 1:1 메시지
- group_message - 그룹 메시지
- typing - 타이핑 중
- read_receipt - 읽음 확인
- presence - 온라인 상태

### 3. Media Service (파일 관리)
**책임:**
- 이미지/파일 업로드
- 썸네일 생성
- 파일 다운로드
- 스토리지 관리

**기술 스택:**
- FastAPI
- MinIO/S3
- Pillow (이미지 처리)

**주요 API:**
- POST /upload/image - 이미지 업로드
- POST /upload/file - 파일 업로드
- GET /media/{file_id} - 파일 다운로드

### 4. WebRTC Service (음성/영상 통화)
**책임:**
- WebRTC 시그널링
- STUN/TURN 서버 관리
- 통화 세션 관리

**기술 스택:**
- FastAPI + WebSocket
- WebRTC
- Redis (세션 관리)

**시그널링 메시지:**
- call_request - 통화 요청
- offer/answer - SDP 교환
- ice_candidate - ICE 후보 교환

## 데이터 플로우

### 메시지 전송 플로우
```
1. 사용자 A → Chat Service (WebSocket)
2. Chat Service → Redis Pub/Sub
3. Redis → Chat Service (사용자 B 연결)
4. Chat Service → 사용자 B (WebSocket)
5. Chat Service → PostgreSQL (메시지 저장)
6. Chat Service → RabbitMQ → Notification Service → 푸시 알림
```

### 파일 전송 플로우
```
1. 사용자 → Media Service (파일 업로드)
2. Media Service → MinIO (파일 저장)
3. Media Service → PostgreSQL (메타데이터 저장)
4. Media Service → 사용자 (파일 URL 반환)
5. 사용자 → Chat Service (메시지 + 파일 URL)
```

## 확장성 전략

### 수평적 확장
- **Chat Service**: WebSocket 연결 수에 따라 자동 스케일링
  - Kubernetes HPA 사용
  - Redis Pub/Sub로 인스턴스 간 메시지 라우팅
  
- **Auth Service**: API 요청 부하에 따라 스케일링
  
- **Media Service**: 업로드 트래픽에 따라 스케일링

### 데이터베이스 확장
- **Read Replicas**: 읽기 작업 분산
- **Sharding**: 사용자 ID 기반 샤딩
- **Connection Pooling**: 연결 풀 최적화

### 캐싱 전략
```
L1: In-Memory Cache (각 서비스)
 └─> L2: Redis (공유 캐시)
      └─> L3: Database
```

## 보안

### 인증/인가
- JWT 기반 토큰 인증
- Access Token (30분) + Refresh Token (7일)
- Token Blacklist (Redis)

### 통신 보안
- TLS/SSL (HTTPS, WSS)
- API Gateway에서 인증서 관리

### 데이터 보안
- 비밀번호 bcrypt 해싱
- 메시지 암호화 (E2EE 옵션)
- Rate Limiting

## 모니터링 및 로깅

### 메트릭 (Prometheus)
- 요청/응답 시간
- 에러율
- WebSocket 연결 수
- 메시지 처리량

### 로깅 (ELK Stack)
- 구조화된 JSON 로그
- 중앙 집중식 로그 수집
- 로그 레벨: DEBUG, INFO, WARNING, ERROR

### 알람
- 서비스 다운
- 높은 에러율
- 응답 시간 초과

## 성능 목표

| 메트릭 | 목표 |
|--------|------|
| 동시 접속자 | 100,000+ |
| 메시지 지연 | < 100ms (P95) |
| API 응답 시간 | < 200ms (P95) |
| 메시지 처리량 | 10,000 msg/sec |
| 가용성 | 99.9% |

## 장애 복구

### 고가용성
- 다중 인스턴스 배포
- Health Check 및 자동 재시작
- Circuit Breaker 패턴

### 백업 전략
- PostgreSQL: 일일 백업 + WAL 아카이빙
- Redis: RDB + AOF
- MinIO: 다중 노드 복제

### Disaster Recovery
- 다중 리전 배포
- 데이터 복제
- 자동 failover
