import io
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from modules import orchestrator, tts
from utils.logger import setup_logging, get_logger
from utils.audio import get_audio_duration

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting VoiceBot...")
    logger.info("Preloading Whisper model..")
    from modules.stt import _load_whisper
    await _load_whisper()
    logger.info("Ready!")
    yield
    logger.info("Shutting down...")
    await orchestrator.cleanup()


app = FastAPI(title="VoiceBot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response schemas
class TextRequest(BaseModel):
    text: str
    output_format: str = "mp3"


class TextResponse(BaseModel):
    success: bool
    transcribed_text: Optional[str] = None
    response_text: Optional[str] = None
    error: Optional[str] = None


# Endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/voice/process")
async def process_voice(
    audio: UploadFile = File(...),
    output_format: str = Form(default="mp3")
):
    if output_format not in ["mp3", "ogg", "wav"]:
        raise HTTPException(400, "Format must be: mp3, ogg, wav")
    
    audio_data = await audio.read()
    if not audio_data:
        raise HTTPException(400, "Empty audio file")
    
    # Check duration
    duration = await get_audio_duration(audio_data)
    if duration > settings.max_audio_duration_seconds:
        raise HTTPException(400, f"Audio too long (max {settings.max_audio_duration_seconds}s)")
    
    # Get format hint from filename
    format_hint = None
    if audio.filename:
        ext = audio.filename.rsplit(".", 1)[-1].lower()
        if ext in ["wav", "mp3", "ogg", "m4a", "webm", "flac"]:
            format_hint = ext
    
    logger.info(f"Processing: {audio.filename}")
    
    result = await orchestrator.process_audio(audio_data, format_hint, output_format)
    
    if not result["success"] or not result["audio_output"]:
        raise HTTPException(500, result.get("error", "Processing failed"))
    
    content_types = {"mp3": "audio/mpeg", "ogg": "audio/ogg", "wav": "audio/wav"}
    
    return StreamingResponse(
        io.BytesIO(result["audio_output"]),
        media_type=content_types[output_format]
    )


@app.post("/api/voice/process-with-text", response_model=TextResponse)
async def process_voice_text(audio: UploadFile = File(...), output_format: str = Form(default="mp3")):
    audio_data = await audio.read()
    if not audio_data:
        raise HTTPException(400, "Empty audio file")
    
    format_hint = audio.filename.rsplit(".", 1)[-1].lower() if audio.filename else None
    result = await orchestrator.process_audio(audio_data, format_hint, output_format)
    
    return TextResponse(
        success=result["success"],
        transcribed_text=result.get("transcribed_text"),
        response_text=result.get("response_text"),
        error=result.get("error")
    )


@app.post("/api/text/chat")
async def text_chat(request: TextRequest):
    if not request.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    
    result = await orchestrator.process_text(request.text, request.output_format)
    
    if not result["success"]:
        raise HTTPException(500, result.get("error", "Failed"))
    
    content_types = {"mp3": "audio/mpeg", "ogg": "audio/ogg", "wav": "audio/wav"}
    
    return StreamingResponse(
        io.BytesIO(result["audio_output"]),
        media_type=content_types[request.output_format]
    )


@app.post("/api/text/chat-text", response_model=TextResponse)
async def text_chat_only(request: TextRequest):
    from modules import llm
    
    try:
        response = await llm.generate(request.text)
        return TextResponse(success=True, transcribed_text=request.text, response_text=response)
    except Exception as e:
        return TextResponse(success=False, error=str(e))


@app.post("/api/conversation/clear")
async def clear_conversation():
    orchestrator.clear_conversation()
    return {"status": "cleared"}


@app.get("/api/tts/voices")
async def get_voices():
    """List available TTS voices."""
    voices = await tts.list_voices()
    return {"voices": [v for v in voices if v["Locale"].startswith("en-")]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
