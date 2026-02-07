# 프로젝트 구조

```
wechat-clone/
├── services/
│   ├── auth-service/         # 인증 서비스
│   ├── chat-service/         # 채팅 서비스 (WebSocket)
│   ├── media-service/        # 파일 업로드 서비스
│   └── webrtc-service/       # 음성/영상 통화
├── shared/                    # 공유 코드
│   ├── models/               # 데이터베이스 모델
│   └── config/               # 설정
├── api-gateway/              # Nginx 게이트웨이
├── k8s/                      # Kubernetes 설정
├── docs/                     # 문서
└── examples/                 # 클라이언트 예제

주요 파일:
- docker-compose.yml          # Docker 실행
- README.md                   # 프로젝트 설명
- QUICKSTART.md              # 빠른 시작
- .env.example               # 환경 변수

서비스 포트:
- Auth: 8001
- Chat: 8002
- Media: 8004
- WebRTC: 8005
```
