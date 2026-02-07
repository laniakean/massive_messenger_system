# WeChat Clone - 빠른 시작 가이드

## 로컬 개발 환경 설정

### 1. 인프라 실행
```bash
docker-compose up -d postgres redis rabbitmq minio
```

### 2. Auth Service 실행
```bash
cd services/auth-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 3. Chat Service 실행
```bash
cd services/chat-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### 4. API 테스트
```bash
# 로그인
curl -X POST http://localhost:8001/login \
  -d "username=test&password=test123"

# WebSocket 연결
# JavaScript에서:
const ws = new WebSocket('ws://localhost:8002/ws/YOUR_TOKEN');
ws.send(JSON.stringify({
  type: "message",
  receiver_id: 2,
  content: "Hello!"
}));
```

## Docker Compose로 전체 실행
```bash
docker-compose up --build
```

## Kubernetes 배포
```bash
kubectl apply -f k8s/deployment.yaml
```
