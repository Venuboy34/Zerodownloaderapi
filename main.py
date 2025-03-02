from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to Zero Downloader API"}

# Function to download YouTube videos and Shorts
@app.get("/youtube")
def download_youtube(url: str):
    try:
        command = ["yt-dlp", "-f", "best", "-o", "downloads/%(title)s.%(ext)s", url]
        subprocess.run(command, check=True)
        return {"status": "success", "message": "Download started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Function to download TikTok videos and MP3
@app.get("/tiktok")
def download_tiktok(url: str, format: str = "video"):
    try:
        if format == "mp3":
            command = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", "downloads/%(title)s.%(ext)s", url]
        else:
            command = ["yt-dlp", "-f", "best", "-o", "downloads/%(title)s.%(ext)s", url]
        subprocess.run(command, check=True)
        return {"status": "success", "message": "Download started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Function to download Instagram reels and stories
@app.get("/instagram")
def download_instagram(url: str):
    try:
        command = ["instaloader", "--dirname-pattern", "downloads", url]
        subprocess.run(command, check=True)
        return {"status": "success", "message": "Download started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
