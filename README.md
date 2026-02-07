# WeChat Clone - 대규모 메신저 시스템

Python 기반 마이크로서비스 아키텍처로 구현된 엔터프라이즈급 메신저 플랫폼

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                           │
│                    (Kong / Nginx)                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Auth Service  │  │  Chat Service   │  │  Media Service  │
│   (JWT/OAuth)  │  │   (WebSocket)   │  │  (File Upload)  │
└────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  User Service  │  │ Message Queue   │  │  WebRTC Service │
│  (Profile DB)  │  │  (RabbitMQ)     │  │  (Audio/Video)  │
└────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
┌───────▼────────────────────▼─────────────────────▼────────┐
│              Shared Infrastructure Layer                   │
│  PostgreSQL │ Redis │ MinIO/S3 │ Elasticsearch │ Metrics  │
└────────────────────────────────────────────────────────────┘
```

## 📦 마이크로서비스 목록

1. **Auth Service** - 인증/인가 (JWT, OAuth2)
2. **User Service** - 사용자 관리 및 프로필
3. **Chat Service** - 실시간 메시징 (WebSocket)
4. **Group Service** - 그룹 채팅 관리
5. **Media Service** - 파일/이미지 업로드 및 관리
6. **WebRTC Service** - 음성/영상 통화 시그널링
7. **Notification Service** - 푸시 알림 (FCM/APNS)
8. **Presence Service** - 온라인/오프라인 상태 관리

## 🚀 기능

- ✅ 1:1 실시간 채팅
- ✅ 그룹 채팅 (최대 500명)
- ✅ 파일/이미지 전송
- ✅ 음성/영상 통화 (WebRTC)
- ✅ 읽음 확인 및 입력 중 표시
- ✅ 메시지 검색
- ✅ 푸시 알림
- ✅ 엔드투엔드 암호화 옵션

## 🛠️ 기술 스택

### Backend
- **Python 3.11+**
- **FastAPI** - REST API
- **WebSocket** - 실시간 통신
- **SQLAlchemy** - ORM
- **Alembic** - DB 마이그레이션
- **Celery** - 비동기 작업

### Database & Cache
- **PostgreSQL** - 주 데이터베이스
- **Redis** - 캐싱, Pub/Sub, 세션
- **MongoDB** (선택) - 메시지 아카이브

### Message Queue
- **RabbitMQ** - 서비스 간 통신

### Storage
- **MinIO / AWS S3** - 파일 저장소

### Monitoring
- **Prometheus** - 메트릭
- **Grafana** - 대시보드
- **ELK Stack** - 로그 관리

### Deployment
- **Docker** - 컨테이너화
- **Kubernetes** - 오케스트레이션
- **Helm** - 패키지 관리

## 📁 프로젝트 구조

```
wechat-clone/
├── services/
│   ├── auth-service/
│   ├── user-service/
│   ├── chat-service/
│   ├── group-service/
│   ├── media-service/
│   ├── webrtc-service/
│   ├── notification-service/
│   └── presence-service/
├── shared/
│   ├── models/
│   ├── utils/
│   └── config/
├── api-gateway/
├── docker/
├── k8s/
└── tests/
```

## 🏃 빠른 시작

### 로컬 개발 환경

```bash
# 1. 저장소 클론
git clone <repository-url>
cd wechat-clone

# 2. 환경 변수 설정
cp .env.example .env

# 3. Docker Compose로 인프라 실행
docker-compose up -d postgres redis rabbitmq minio

# 4. 각 서비스 실행 (예: Auth Service)
cd services/auth-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# 5. Chat Service (WebSocket)
cd services/chat-service
uvicorn app.main:app --reload --port 8002
```

### Docker Compose로 전체 실행

```bash
docker-compose up --build
```

### Kubernetes 배포

```bash
# Helm으로 배포
helm install wechat-clone ./k8s/helm-chart

# 또는 kubectl로 직접 배포
kubectl apply -f k8s/
```

## 📊 확장성 전략

### 수평적 확장
- **Chat Service**: WebSocket 연결 수에 따라 자동 스케일링
- **Media Service**: 업로드 트래픽에 따라 스케일링
- **Database**: Read Replicas + Sharding

### 캐싱 전략
- **L1 Cache**: 인메모리 (각 서비스)
- **L2 Cache**: Redis (공유)
- **CDN**: 정적 파일 및 미디어

### 메시지 처리
- **분산 메시지 큐**: RabbitMQ 클러스터
- **이벤트 소싱**: 메시지 영속성
- **CQRS 패턴**: 읽기/쓰기 분리

## 🔐 보안

- JWT 기반 인증
- Rate Limiting
- CORS 설정
- SQL Injection 방지
- XSS 방지
- 메시지 암호화 (E2EE 옵션)
- SSL/TLS 통신

## 📈 성능 목표

- **동시 접속자**: 100,000+ 
- **메시지 처리**: 10,000 msg/sec
- **메시지 지연**: < 100ms (P95)
- **API 응답 시간**: < 200ms (P95)
- **가용성**: 99.9%

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 부하 테스트
locust -f tests/load/locustfile.py
```

## 📝 API 문서

각 서비스 실행 후 Swagger UI 접속:
- Auth Service: http://localhost:8001/docs
- Chat Service: http://localhost:8002/docs
- User Service: http://localhost:8003/docs
- Media Service: http://localhost:8004/docs

## 🤝 기여

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 라이선스

MIT License

## 👥 Authors

- Your Name - Initial work

## 🙏 감사의 말

- WeChat for inspiration
- FastAPI community
- Open source contributors