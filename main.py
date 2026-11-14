import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import httpx
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI(title="Voie Speak Realtime", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="."), name="static")

XAI_API_KEY = os.getenv("XAI_API_KEY") or os.getenv("LLM_API_KEY")

@app.get("/")
def root():
    return {"message": "Voie Speak Realtime API", "docs": "/docs", "app": "/app"}

@app.get("/app")
def serve_app():
    html_path = "voie-speak-realtime.html"
    if os.path.exists(html_path):
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="HTML file not found")

@app.post("/api/realtime/token")
async def get_ephemeral_token():
    """Mint a short-lived token so the browser never sees the real API key."""
    if not XAI_API_KEY:
        raise HTTPException(status_code=500, detail="XAI_API_KEY (or LLM_API_KEY) not set in .env")

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            "https://api.x.ai/v1/realtime/client_secrets",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"expires_after": {"seconds": 600}},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()
        return {"token": data.get("value"), "expires_at": data.get("expires_at")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
