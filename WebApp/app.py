import os
from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import tempfile
import asyncio
import speech_recognition as sr
import edge_tts
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# ============ Config ============
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
TTS_VOICE = "en-IN-NeerjaNeural"

SYSTEM_PROMPT = """You are Sudip. Full name Sudip Das.

You must answer exactly as Sudip would answer in a real interview.

Background and context about Sudip:
- Sudip has a technical background in statistics and computing.
- He is pursuing MSc in Mathematics & Computing and works heavily with AI/ML.
- He has built real projects such as recommender systems, interview bots, automation tools, and ML models.
- He has experience with Python, MLOps, Agentic AI(RAG), cloud(AZURE), NLP and Computer Vision, Git, LLMs, MCP and n8n.
- He prefers learning by doing, experimenting, and breaking problems into small steps.
- He values consistency, clarity, and practical impact over buzzwords.
- He is calm, thoughtful, and focused rather than flashy.
- He is growth-oriented and honest about areas he wants to improve.
- He communicates clearly using simple language.

Answering style rules (mandatory):
- Speak in first person (“I”).
- Use simple, clear, very polite human language.
- No jargon unless necessary.
- 3-5 sentences per answer.
- Calm, confident, humble tone.
- Honest and realistic, not exaggerated.
- Do NOT sound like an AI, coach, or motivational speaker.
- Do NOT invent life events, job titles, or achievements.
- If unsure, answer conservatively and truthfully.

Behavior rules:
- Answers should feel like a real interview conversation.
- Slight imperfection in wording is acceptable if it feels natural.
- Keep personality consistent across all questions.
- Never mention being an AI or language model.

Your goal:
Respond exactly as Sudip would respond if he were personally answering these interview questions in his own voice.
"""

# ============ State ============
_recognizer = sr.Recognizer()
_history = []


# ============ STT (Google Speech Recognition) ============
def transcribe(audio_path):
    if not audio_path:
        return ""
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = _recognizer.record(source)
            text = _recognizer.recognize_google(audio_data)
            return text.strip()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"STT error: {e}")
        return ""


# ============ LLM (Groq + Google fallback) ============
def generate(message):
    global _history
    
    if not message:
        return "I didn't hear anything. Could you try again?"
    
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(_history)
    messages.append(HumanMessage(content=message))
    
    reply = None
    
    # Try Groq first
    if GROQ_API_KEY:
        try:
            llm = ChatGroq(
                api_key=GROQ_API_KEY,
                model=GROQ_MODEL,
                temperature=0.7,
                max_tokens=150
            )
            response = llm.invoke(messages)
            reply = response.content.strip()
        except Exception as e:
            print(f"Groq failed: {e}")
    
    # Fallback to Google
    if reply is None and GOOGLE_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(
                api_key=GOOGLE_API_KEY,
                model=GOOGLE_MODEL,
                temperature=0.7,
                max_output_tokens=150
            )
            response = llm.invoke(messages)
            reply = response.content.strip()
        except Exception as e:
            print(f"Google failed: {e}")
    
    if reply is None:
        return "No API configured. Add GROQ_API_KEY or GOOGLE_API_KEY."
    
    _history.append(HumanMessage(content=message))
    _history.append(AIMessage(content=reply))
    
    if len(_history) > 10:
        _history = _history[-10:]
    
    return reply


# ============ TTS (Edge TTS) ============
def synthesize(text):
    if not text:
        return None
    
    async def _synthesize():
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        communicate = edge_tts.Communicate(text, TTS_VOICE)
        await communicate.save(temp.name)
        return temp.name
    
    return asyncio.run(_synthesize())


# ============ Main Pipeline ============
def process_voice(audio_path):
    if not audio_path:
        return None, "No audio recorded"
    
    # STT
    user_text = transcribe(audio_path)
    if not user_text:
        return None, "Could not understand audio"
    
    # LLM
    bot_response = generate(user_text)
    
    # TTS
    audio_file = synthesize(bot_response)
    
    chat_text = f"You: {user_text}\nBot: {bot_response}"
    return audio_file, chat_text


def process_text(text):
    if not text or not text.strip():
        return None, "Please enter a message"
    
    # LLM
    bot_response = generate(text.strip())
    
    # TTS
    audio_file = synthesize(bot_response)
    
    chat_text = f"You: {text}\nBot: {bot_response}"
    return audio_file, chat_text


def clear_chat():
    global _history
    _history = []
    return None, None, "Conversation cleared!"


# ============ Gradio UI ============
with gr.Blocks(title="VoiceBot", theme=gr.themes.Soft()) as app:
    
    gr.Markdown("# 🎙️ VoiceBot")
    gr.Markdown("*Voice assistant powered by Whisper + Groq + Edge TTS*")
    
    with gr.Tab("🎤 Voice"):
        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Record")
        voice_btn = gr.Button("Send", variant="primary")
        audio_output = gr.Audio(label="Response", autoplay=True)
        voice_text = gr.Textbox(label="Chat", lines=3)
        
        voice_btn.click(process_voice, [audio_input], [audio_output, voice_text])
    
    with gr.Tab("⌨️ Text"):
        text_input = gr.Textbox(label="Message", placeholder="Type here...")
        text_btn = gr.Button("Send", variant="primary")
        text_audio = gr.Audio(label="Response", autoplay=True)
        text_display = gr.Textbox(label="Chat", lines=3)
        
        text_btn.click(process_text, [text_input], [text_audio, text_display])
        text_input.submit(process_text, [text_input], [text_audio, text_display])
    
    clear_btn = gr.Button("Clear Chat")
    clear_status = gr.Markdown("")
    clear_btn.click(clear_chat, [], [audio_output, text_audio, clear_status])

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
