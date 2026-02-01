import os
import asyncio
from utils.logger import get_logger
from utils.audio import save_to_temp_wav, cleanup_temp_file

logger = get_logger(__name__)

_whisper_model = None

# Cache directory for Whisper model
WHISPER_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache", "whisper")


async def _load_whisper(model_name: str = "base"):
    global _whisper_model
    if _whisper_model is None:
        os.makedirs(WHISPER_CACHE_DIR, exist_ok=True)
        
        logger.info(f"Loading Whisper model: {model_name} (cache: {WHISPER_CACHE_DIR})")
        
        import whisper
        _whisper_model = await asyncio.to_thread(
            whisper.load_model,
            model_name,
            download_root=WHISPER_CACHE_DIR
        )
        logger.info("Whisper loaded")
    return _whisper_model


async def transcribe_with_whisper(audio_path: str, model_name: str = "base") -> str:

    model = await _load_whisper(model_name)
    
    result = await asyncio.to_thread(
        model.transcribe,
        audio_path,
        fp16=False,
        language="en"
    )
    return result.get("text", "").strip()


async def transcribe_with_google(audio_path: str) -> str:
    import speech_recognition as sr
    
    recognizer = sr.Recognizer()

    def recognize():
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)

    text = await asyncio.to_thread(recognize)
    return text.strip()


async def transcribe(audio_data: bytes, format_hint: str = None) -> str:
    temp_path = None
    
    try:
        temp_path = await save_to_temp_wav(audio_data, format_hint)
        
        # Try Whisper first
        try:
            text = await transcribe_with_whisper(temp_path)
            logger.info(f"Whisper: '{text[:50]}...'")
            return text
        except Exception as e:
            logger.warning(f"Whisper failed: {e}, trying fallback...")
        
        # Fallback to Google
        text = await transcribe_with_google(temp_path)
        logger.info(f"Google STT: '{text[:50]}...'")
        return text
        
    finally:
        cleanup_temp_file(temp_path)
