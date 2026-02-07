"""
WebRTC Service - 음성/영상 통화 시그널링 서버
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from datetime import datetime

app = FastAPI(title="WebRTC Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STUN/TURN 서버
ICE_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"},
]


class WebRTCManager:
    """WebRTC 시그널링 매니저"""
    
    def __init__(self):
        self.connections: Dict[int, WebSocket] = {}
        self.active_calls: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.connections:
            del self.connections[user_id]
    
    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.connections:
            await self.connections[user_id].send_json(message)
    
    def create_call(self, room_id: str, caller_id: int, callee_id: int, call_type: str):
        self.active_calls[room_id] = {
            "caller_id": caller_id,
            "callee_id": callee_id,
            "call_type": call_type,
            "status": "calling",
            "started_at": datetime.utcnow()
        }


manager = WebRTCManager()


@app.websocket("/ws/signaling/{user_id}")
async def signaling_endpoint(websocket: WebSocket, user_id: int):
    """WebRTC 시그널링 엔드포인트"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "call_request":
                callee_id = data.get("callee_id")
                room_id = data.get("room_id")
                call_type = data.get("call_type", "audio")
                
                manager.create_call(room_id, user_id, callee_id, call_type)
                
                await manager.send_to_user(callee_id, {
                    "type": "incoming_call",
                    "caller_id": user_id,
                    "room_id": room_id,
                    "call_type": call_type,
                    "ice_servers": ICE_SERVERS
                })
            
            elif message_type == "call_response":
                accepted = data.get("accepted")
                room_id = data.get("room_id")
                caller_id = data.get("caller_id")
                
                await manager.send_to_user(caller_id, {
                    "type": "call_response",
                    "accepted": accepted,
                    "room_id": room_id,
                    "ice_servers": ICE_SERVERS if accepted else None
                })
            
            elif message_type == "offer":
                target_id = data.get("target_id")
                await manager.send_to_user(target_id, {
                    "type": "offer",
                    "sdp": data.get("sdp"),
                    "sender_id": user_id
                })
            
            elif message_type == "answer":
                target_id = data.get("target_id")
                await manager.send_to_user(target_id, {
                    "type": "answer",
                    "sdp": data.get("sdp"),
                    "sender_id": user_id
                })
            
            elif message_type == "ice_candidate":
                target_id = data.get("target_id")
                await manager.send_to_user(target_id, {
                    "type": "ice_candidate",
                    "candidate": data.get("candidate"),
                    "sender_id": user_id
                })
            
            elif message_type == "end_call":
                room_id = data.get("room_id")
                if room_id in manager.active_calls:
                    call_info = manager.active_calls[room_id]
                    other_user = (call_info["callee_id"] 
                                 if user_id == call_info["caller_id"] 
                                 else call_info["caller_id"])
                    
                    await manager.send_to_user(other_user, {
                        "type": "call_ended",
                        "room_id": room_id
                    })
                    del manager.active_calls[room_id]
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "webrtc-service",
        "active_calls": len(manager.active_calls)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
