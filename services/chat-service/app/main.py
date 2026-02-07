"""
Chat Service - 실시간 메시징 서비스
WebSocket 기반 1:1 채팅 및 그룹 채팅
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Set
from datetime import datetime
from pydantic import BaseModel
import json
import asyncio
from collections import defaultdict
import jwt

app = FastAPI(title="Chat Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT 설정 (Auth Service와 동일해야 함)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


# Pydantic Models
class Message(BaseModel):
    id: str
    sender_id: int
    receiver_id: int
    content: str
    message_type: str = "text"  # text, image, file, audio, video
    timestamp: datetime
    is_read: bool = False
    reply_to: str = None


class GroupMessage(BaseModel):
    id: str
    group_id: str
    sender_id: int
    content: str
    message_type: str = "text"
    timestamp: datetime
    read_by: List[int] = []


class TypingIndicator(BaseModel):
    user_id: int
    chat_id: str
    is_typing: bool


class ReadReceipt(BaseModel):
    message_id: str
    user_id: int
    read_at: datetime


# Connection Manager
class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # user_id -> WebSocket 매핑
        self.active_connections: Dict[int, WebSocket] = {}
        # group_id -> Set[user_id] 매핑
        self.group_members: Dict[str, Set[int]] = defaultdict(set)
        # user_id -> presence status
        self.user_presence: Dict[int, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_presence[user_id] = "online"
        
        # 온라인 상태 브로드캐스트
        await self.broadcast_presence(user_id, "online")
    
    def disconnect(self, user_id: int):
        """연결 종료"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        self.user_presence[user_id] = "offline"
    
    async def send_personal_message(self, message: dict, receiver_id: int):
        """1:1 메시지 전송"""
        if receiver_id in self.active_connections:
            await self.active_connections[receiver_id].send_json(message)
    
    async def send_group_message(self, message: dict, group_id: str, exclude_sender: int = None):
        """그룹 메시지 전송"""
        if group_id in self.group_members:
            for user_id in self.group_members[group_id]:
                if user_id != exclude_sender and user_id in self.active_connections:
                    await self.active_connections[user_id].send_json(message)
    
    async def broadcast_presence(self, user_id: int, status: str):
        """사용자 상태 브로드캐스트"""
        presence_message = {
            "type": "presence",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 모든 연결된 사용자에게 전송
        for connection in self.active_connections.values():
            try:
                await connection.send_json(presence_message)
            except:
                pass
    
    def join_group(self, user_id: int, group_id: str):
        """그룹 참여"""
        self.group_members[group_id].add(user_id)
    
    def leave_group(self, user_id: int, group_id: str):
        """그룹 나가기"""
        if group_id in self.group_members:
            self.group_members[group_id].discard(user_id)


manager = ConnectionManager()


def verify_token(token: str) -> dict:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket 연결 엔드포인트
    - token: JWT 액세스 토큰
    """
    try:
        # 토큰 검증
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008)
            return
        
        # 연결 수락
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "message":
                    # 1:1 메시지
                    await handle_direct_message(data, user_id)
                
                elif message_type == "group_message":
                    # 그룹 메시지
                    await handle_group_message(data, user_id)
                
                elif message_type == "typing":
                    # 타이핑 인디케이터
                    await handle_typing_indicator(data, user_id)
                
                elif message_type == "read_receipt":
                    # 읽음 확인
                    await handle_read_receipt(data, user_id)
                
                elif message_type == "join_group":
                    # 그룹 참여
                    group_id = data.get("group_id")
                    manager.join_group(user_id, group_id)
                    await websocket.send_json({
                        "type": "group_joined",
                        "group_id": group_id
                    })
                
                elif message_type == "leave_group":
                    # 그룹 나가기
                    group_id = data.get("group_id")
                    manager.leave_group(user_id, group_id)
                
        except WebSocketDisconnect:
            manager.disconnect(user_id)
            await manager.broadcast_presence(user_id, "offline")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1011)


async def handle_direct_message(data: dict, sender_id: int):
    """1:1 메시지 처리"""
    receiver_id = data.get("receiver_id")
    content = data.get("content")
    message_type = data.get("message_type", "text")
    
    # 메시지 ID 생성 (실제로는 UUID 또는 DB 생성)
    message_id = f"msg_{datetime.utcnow().timestamp()}"
    
    message = {
        "type": "message",
        "id": message_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": content,
        "message_type": message_type,
        "timestamp": datetime.utcnow().isoformat(),
        "is_read": False
    }
    
    # 수신자에게 전송
    await manager.send_personal_message(message, receiver_id)
    
    # 발신자에게 확인 전송
    await manager.send_personal_message({
        **message,
        "type": "message_sent"
    }, sender_id)
    
    # 실제로는 DB에 저장
    # await save_message_to_db(message)
    
    # 수신자가 오프라인이면 푸시 알림 전송
    if receiver_id not in manager.active_connections:
        # await send_push_notification(receiver_id, message)
        pass


async def handle_group_message(data: dict, sender_id: int):
    """그룹 메시지 처리"""
    group_id = data.get("group_id")
    content = data.get("content")
    message_type = data.get("message_type", "text")
    
    message_id = f"grpmsg_{datetime.utcnow().timestamp()}"
    
    message = {
        "type": "group_message",
        "id": message_id,
        "group_id": group_id,
        "sender_id": sender_id,
        "content": content,
        "message_type": message_type,
        "timestamp": datetime.utcnow().isoformat(),
        "read_by": [sender_id]
    }
    
    # 그룹 멤버들에게 전송 (발신자 제외)
    await manager.send_group_message(message, group_id, exclude_sender=sender_id)
    
    # 발신자에게 확인
    await manager.send_personal_message({
        **message,
        "type": "group_message_sent"
    }, sender_id)
    
    # DB에 저장
    # await save_group_message_to_db(message)


async def handle_typing_indicator(data: dict, user_id: int):
    """타이핑 인디케이터 처리"""
    chat_id = data.get("chat_id")
    is_typing = data.get("is_typing", True)
    is_group = data.get("is_group", False)
    
    typing_message = {
        "type": "typing",
        "user_id": user_id,
        "chat_id": chat_id,
        "is_typing": is_typing
    }
    
    if is_group:
        await manager.send_group_message(typing_message, chat_id, exclude_sender=user_id)
    else:
        # 1:1 채팅의 경우 상대방에게만 전송
        receiver_id = int(chat_id.split("_")[-1])  # 간단한 예시
        await manager.send_personal_message(typing_message, receiver_id)


async def handle_read_receipt(data: dict, user_id: int):
    """읽음 확인 처리"""
    message_id = data.get("message_id")
    sender_id = data.get("sender_id")
    
    receipt = {
        "type": "read_receipt",
        "message_id": message_id,
        "user_id": user_id,
        "read_at": datetime.utcnow().isoformat()
    }
    
    # 메시지 발신자에게 읽음 확인 전송
    await manager.send_personal_message(receipt, sender_id)
    
    # DB 업데이트
    # await update_message_read_status(message_id, user_id)


# REST API Endpoints
@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "chat-service",
        "active_connections": len(manager.active_connections)
    }


@app.get("/stats")
async def get_stats():
    """서비스 통계"""
    return {
        "active_connections": len(manager.active_connections),
        "total_groups": len(manager.group_members),
        "online_users": [uid for uid, status in manager.user_presence.items() if status == "online"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
