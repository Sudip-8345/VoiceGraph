"""Voice processing modules."""

from modules.stt import transcribe, transcribe_with_whisper, transcribe_with_google
from modules.tts import synthesize, synthesize_with_edge, synthesize_with_gtts, list_voices
from modules.llm import generate, clear_history, get_history
from modules.orchestrator import process_audio, process_text, clear_conversation, cleanup

__all__ = [
    # STT
    "transcribe",
    "transcribe_with_whisper",
    "transcribe_with_google",
    # TTS
    "synthesize",
    "synthesize_with_edge",
    "synthesize_with_gtts",
    "list_voices",
    # LLM
    "generate",
    "clear_history",
    "get_history",
    # Orchestrator
    "process_audio",
    "process_text",
    "clear_conversation",
    "cleanup",
]
