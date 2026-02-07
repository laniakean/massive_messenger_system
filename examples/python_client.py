"""
WeChat Clone - Python 클라이언트 예제
"""
import asyncio
import websockets
import requests
import json


class WeChatClient:
    def __init__(self):
        self.access_token = None
        self.ws = None
    
    def login(self, username: str, password: str):
        response = requests.post(
            "http://localhost:8001/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            print("✅ 로그인 성공!")
            return True
        return False
    
    async def connect_chat(self):
        ws_url = f"ws://localhost:8002/ws/{self.access_token}"
        self.ws = await websockets.connect(ws_url)
        print("✅ 채팅 서버 연결")
        asyncio.create_task(self.receive_messages())
    
    async def receive_messages(self):
        async for message in self.ws:
            data = json.loads(message)
            if data.get("type") == "message":
                print(f"\n📩 {data['content']}")
    
    async def send_message(self, receiver_id: int, content: str):
        await self.ws.send(json.dumps({
            "type": "message",
            "receiver_id": receiver_id,
            "content": content
        }))


# 사용 예제
async def main():
    client = WeChatClient()
    
    # 로그인
    if client.login("testuser", "password123"):
        # 채팅 연결
        await client.connect_chat()
        
        # 메시지 전송
        await client.send_message(2, "안녕하세요!")
        
        # 메시지 수신 대기
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
