from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from modules import stt, tts, llm
from utils.logger import get_logger

logger = get_logger(__name__)


# State schema using TypedDict
class PipelineState(TypedDict):
    audio_input: bytes
    audio_format: Optional[str]
    transcribed_text: Optional[str]
    llm_response: Optional[str]
    audio_output: Optional[bytes]
    output_format: str
    error: Optional[str]


# Pipeline node functions
async def stt_node(state: PipelineState) -> dict:
    try:
        text = await stt.transcribe(state["audio_input"], state.get("audio_format"))
        if not text:
            return {"error": "Could not transcribe audio"}
        return {"transcribed_text": text}
    except Exception as e:
        logger.error(f"STT error: {e}")
        return {"error": f"Speech recognition failed: {e}"}


async def llm_node(state: PipelineState) -> dict:
    try:
        response = await llm.generate(state["transcribed_text"])
        if not response:
            return {"error": "LLM returned empty response"}
        return {"llm_response": response}
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {"error": f"Failed to generate response: {e}"}


async def tts_node(state: PipelineState) -> dict:
    try:
        audio = await tts.synthesize(state["llm_response"], state.get("output_format", "mp3"))
        return {"audio_output": audio}
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return {"error": f"Speech synthesis failed: {e}"}


async def error_node(state: PipelineState) -> dict:
    error_msg = "Sorry, I had trouble processing that. Please try again."
    try:
        audio = await tts.synthesize(error_msg, state.get("output_format", "mp3"))
        return {"llm_response": error_msg, "audio_output": audio}
    except:
        return {}


def check_error(state: PipelineState) -> str:
    return "error" if state.get("error") else "ok"


def build_pipeline():
    graph = StateGraph(PipelineState)
    
    # Add nodes
    graph.add_node("stt", stt_node)
    graph.add_node("llm", llm_node)
    graph.add_node("tts", tts_node)
    graph.add_node("error", error_node)
    
    graph.set_entry_point("stt")
    
    # Add edges with error handling
    graph.add_conditional_edges("stt", check_error, {"ok": "llm", "error": "error"})
    graph.add_conditional_edges("llm", check_error, {"ok": "tts", "error": "error"})
    graph.add_conditional_edges("tts", check_error, {"ok": END, "error": "error"})
    graph.add_edge("error", END)
    
    logger.info("Pipeline built")
    return graph.compile()


_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


async def process_audio(audio_data: bytes, audio_format: str = None, output_format: str = "mp3") -> dict:
    logger.info("Processing audio...")
    
    initial_state: PipelineState = {
        "audio_input": audio_data,
        "audio_format": audio_format,
        "transcribed_text": None,
        "llm_response": None,
        "audio_output": None,
        "output_format": output_format,
        "error": None,
    }
    
    pipeline = get_pipeline()
    final = await pipeline.ainvoke(initial_state)
    
    return {
        "success": final.get("error") is None,
        "transcribed_text": final.get("transcribed_text"),
        "response_text": final.get("llm_response"),
        "audio_output": final.get("audio_output"),
        "error": final.get("error")
    }


async def process_text(text: str, output_format: str = "mp3") -> dict:
    try:
        response = await llm.generate(text)
        audio = await tts.synthesize(response, output_format)
        return {
            "success": True,
            "transcribed_text": text,
            "response_text": response,
            "audio_output": audio,
            "error": None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def clear_conversation():
    llm.clear_history()

