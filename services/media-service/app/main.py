"""
Media Service - 파일/이미지 업로드 및 관리
MinIO/S3 기반 스토리지
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import io
from PIL import Image

app = FastAPI(title="Media Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 설정
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# Pydantic Models
class MediaUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    file_size: int
    url: str
    thumbnail_url: Optional[str] = None
    uploaded_at: datetime


class ImageProcessingOptions(BaseModel):
    resize: Optional[tuple] = None
    quality: int = 85
    format: str = "JPEG"


# Mock Storage (실제로는 MinIO/S3 클라이언트 사용)
storage = {}


def generate_file_id() -> str:
    """고유 파일 ID 생성"""
    return str(uuid.uuid4())


def validate_file_size(file_size: int, max_size: int):
    """파일 크기 검증"""
    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_size / (1024*1024)}MB"
        )


def validate_file_type(content_type: str, allowed_types: set):
    """파일 타입 검증"""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {content_type}"
        )


async def create_thumbnail(image_data: bytes, size: tuple = (200, 200)) -> bytes:
    """썸네일 생성"""
    try:
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail(size)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        print(f"Thumbnail creation failed: {e}")
        return None


@app.post("/upload/image", response_model=MediaUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    이미지 업로드
    - 자동 썸네일 생성
    - 이미지 최적화
    """
    # 파일 크기 및 타입 검증
    content = await file.read()
    file_size = len(content)
    
    validate_file_size(file_size, MAX_IMAGE_SIZE)
    validate_file_type(file.content_type, ALLOWED_IMAGE_TYPES)
    
    # 파일 ID 생성
    file_id = generate_file_id()
    
    # 썸네일 생성
    thumbnail_data = await create_thumbnail(content)
    thumbnail_id = f"{file_id}_thumb" if thumbnail_data else None
    
    # 실제로는 MinIO/S3에 업로드
    # s3_client.put_object(bucket, file_id, content)
    # if thumbnail_data:
    #     s3_client.put_object(bucket, thumbnail_id, thumbnail_data)
    
    # Mock storage에 저장
    storage[file_id] = content
    if thumbnail_data:
        storage[thumbnail_id] = thumbnail_data
    
    return MediaUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type=file.content_type,
        file_size=file_size,
        url=f"/media/{file_id}",
        thumbnail_url=f"/media/{thumbnail_id}" if thumbnail_id else None,
        uploaded_at=datetime.utcnow()
    )


@app.post("/upload/file", response_model=MediaUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    일반 파일 업로드
    - 문서, PDF 등
    """
    # 파일 읽기
    content = await file.read()
    file_size = len(content)
    
    # 검증
    validate_file_size(file_size, MAX_FILE_SIZE)
    validate_file_type(file.content_type, ALLOWED_FILE_TYPES)
    
    # 파일 ID 생성
    file_id = generate_file_id()
    
    # 저장
    storage[file_id] = content
    
    return MediaUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type=file.content_type,
        file_size=file_size,
        url=f"/media/{file_id}",
        uploaded_at=datetime.utcnow()
    )


@app.post("/upload/batch", response_model=List[MediaUploadResponse])
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    다중 파일 업로드
    - 최대 10개까지
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
    
    results = []
    for file in files:
        content = await file.read()
        file_size = len(content)
        file_id = generate_file_id()
        
        # 간단한 검증
        if file_size > MAX_FILE_SIZE:
            continue
        
        storage[file_id] = content
        
        results.append(MediaUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            url=f"/media/{file_id}",
            uploaded_at=datetime.utcnow()
        ))
    
    return results


@app.get("/media/{file_id}")
async def get_file(file_id: str):
    """
    파일 다운로드
    """
    if file_id not in storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 실제로는 S3에서 가져옴
    # file_data = s3_client.get_object(bucket, file_id)
    
    file_data = storage[file_id]
    
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type="application/octet-stream"
    )


@app.delete("/media/{file_id}")
async def delete_file(file_id: str):
    """
    파일 삭제
    """
    if file_id not in storage:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 실제로는 S3에서 삭제
    # s3_client.delete_object(bucket, file_id)
    
    del storage[file_id]
    
    return {"message": "File deleted successfully"}


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "media-service",
        "stored_files": len(storage)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
