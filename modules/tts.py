import asyncio
import io
from utils.logger import get_logger
from utils.audio import convert_to_format
from config import get_settings

logger = get_logger(__name__)


async def synthesize_with_edge(text: str, voice: str = None, rate: str = None, volume: str = None) -> bytes:
    import edge_tts
    
    settings = get_settings()
    voice = voice or settings.tts_voice
    rate = rate or settings.tts_rate
    volume = volume or settings.tts_volume
    
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    
    return b"".join(chunks)


async def synthesize_with_gtts(text: str) -> bytes:
    from gtts import gTTS
    
    loop = asyncio.get_event_loop()
    
    def synthesize():
        tts = gTTS(text=text, lang="en")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()

    audio_bytes = await asyncio.to_thread(synthesize)


async def synthesize(text: str, output_format: str = "mp3") -> bytes:
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    audio = None
    
    # Try Edge TTS first
    try:
        audio = await synthesize_with_edge(text)
        logger.info(f"Edge TTS: {len(audio)} bytes")
    except Exception as e:
        logger.warning(f"Edge TTS failed: {e}, trying gTTS...")
    
    # Fallback to gTTS
    if audio is None:
        audio = await synthesize_with_gtts(text)
        logger.info(f"gTTS: {len(audio)} bytes")
    
    # Convert format if needed
    if output_format != "mp3":
        audio = await convert_to_format(audio, output_format)
    
    return audio


async def list_voices():
    """List available Edge TTS voices."""
    import edge_tts
    return await edge_tts.list_voices()
