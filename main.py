from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, HttpUrl
import yt_dlp
import os
import tempfile
import time
from urllib.parse import urlparse
from typing import Optional, Dict, Any

app = FastAPI(title="Social Media Downloader API")

# Create temp directory for downloads
TEMP_DIR = os.path.join(tempfile.gettempdir(), "social_media_downloads")
os.makedirs(TEMP_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    url: HttpUrl
    format: Optional[str] = "best"

class DownloadResponse(BaseModel):
    success: bool
    message: str
    download_url: Optional[str] = None
    platform: Optional[str] = None
    media_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

def identify_platform(url: str) -> Dict[str, str]:
    """Identify the platform and potential media type from URL."""
    domain = urlparse(url).netloc.lower()

    platform_mapping = {
        "instagram.com": {"platform": "instagram", "media_type": "unknown"},
        "pinterest.com": {"platform": "pinterest", "media_type": "unknown"},
        "tiktok.com": {"platform": "tiktok", "media_type": "video"},
        "twitter.com": {"platform": "twitter", "media_type": "unknown"},
        "x.com": {"platform": "twitter", "media_type": "unknown"},
        "vk.com": {"platform": "vk", "media_type": "unknown"},
        "reddit.com": {"platform": "reddit", "media_type": "unknown"},
        "twitch.tv": {"platform": "twitch", "media_type": "video"},
        "vimeo.com": {"platform": "vimeo", "media_type": "video"},
        "ok.ru": {"platform": "ok", "media_type": "video"},
        "tumblr.com": {"platform": "tumblr", "media_type": "unknown"},
        "dailymotion.com": {"platform": "dailymotion", "media_type": "video"},
        "likee.com": {"platform": "likee", "media_type": "video"},
        "soundcloud.com": {"platform": "soundcloud", "media_type": "audio"},
        "music.apple.com": {"platform": "apple_music", "media_type": "audio"},
        "spotify.com": {"platform": "spotify", "media_type": "audio"},
        "youtube.com": {"platform": "youtube", "media_type": "video"},
        "youtu.be": {"platform": "youtube", "media_type": "video"},
    }

    for domain_key, info in platform_mapping.items():
        if domain_key in domain:
            return info

    return {"platform": "unknown", "media_type": "unknown"}

async def download_media(url: str, format_option: str = "best") -> Dict:
    """Download media using yt-dlp."""
    platform_info = identify_platform(url)
    platform = platform_info["platform"]
    media_type = platform_info["media_type"]

    response = {
        "success": False,
        "message": "",
        "download_url": None,
        "platform": platform,
        "media_type": media_type,
        "metadata": {}
    }

    if platform == "unknown":
        response["message"] = "Unsupported platform or URL"
        return response

    try:
        # Set download options
        options = {
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s-%(id)s.%(ext)s'),
            'format': format_option,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

            if not os.path.exists(downloaded_file):
                response["message"] = "Download completed but file not found"
                return response

            file_path = os.path.relpath(downloaded_file, TEMP_DIR)
            response["success"] = True
            response["message"] = "Download successful"
            response["download_url"] = f"/download/{file_path}"
            response["metadata"] = {
                "title": info.get("title", ""),
                "uploader": info.get("uploader", ""),
                "duration": info.get("duration", 0),
                "file_size": os.path.getsize(downloaded_file),
                "file_name": os.path.basename(downloaded_file)
            }

            return response

    except Exception as e:
        response["message"] = f"Download failed: {str(e)}"
        return response

@app.get("/")
async def root():
    return {"message": "Social Media Downloader API is running!"}

@app.post("/download")
async def download(download_request: DownloadRequest):
    """Download media from the provided URL."""
    result = await download_media(str(download_request.url), download_request.format)
    
    if not result["success"]:
        return JSONResponse(result, status_code=400)
    
    return JSONResponse(result)

@app.get("/download/{file_path:path}")
async def serve_download(file_path: str):
    """Serve the downloaded file."""
    full_path = os.path.join(TEMP_DIR, file_path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=full_path, filename=os.path.basename(full_path), media_type="application/octet-stream")

@app.get("/cleanup")
async def cleanup_temp_files(hours: int = Query(24, ge=1, le=168)):
    """Clean up temporary files older than the specified hours."""
    cleaned = 0
    total_size = 0

    current_time = time.time()
    max_age = hours * 3600  # Convert hours to seconds

    for root, _, files in os.walk(TEMP_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            file_age = current_time - os.path.getmtime(file_path)

            if file_age > max_age:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                os.remove(file_path)
                cleaned += 1

    return {
        "message": f"Cleaned {cleaned} files, freed {total_size/1024/1024:.2f} MB of space",
        "cleaned_files": cleaned,
        "freed_space_mb": total_size/1024/1024
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
