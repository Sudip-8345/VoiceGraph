import os
import gradio as gr
import requests
import tempfile

API_URL = os.getenv("API_URL", "http://localhost:8000")


# ============ API Functions ============

def check_api():
    try:
        return requests.get(f"{API_URL}/health", timeout=3).ok
    except:
        return False


def send_audio_to_api(audio_path, output_format="mp3"):
    if not audio_path:
        return None, "No audio recorded"
    
    try:
        # First get the text response
        with open(audio_path, "rb") as f:
            text_resp = requests.post(
                f"{API_URL}/api/voice/process-with-text",
                files={"audio": ("audio.wav", f, "audio/wav")},
                data={"output_format": output_format},
                timeout=120
            )
        
        if text_resp.status_code != 200:
            error = text_resp.json().get("detail", "Unknown error")
            return None, f"Error: {error}"
        
        text_data = text_resp.json()
        user_text = text_data.get("transcribed_text", "")
        bot_text = text_data.get("response_text", "")
        
        # Now get the audio response
        with open(audio_path, "rb") as f:
            audio_resp = requests.post(
                f"{API_URL}/api/voice/process",
                files={"audio": ("audio.wav", f, "audio/wav")},
                data={"output_format": output_format},
                timeout=120
            )
        
        if audio_resp.status_code == 200:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}")
            temp.write(audio_resp.content)
            temp.close()
            chat_text = f"You: {user_text}\nBot: {bot_text}"
            return temp.name, chat_text
        else:
            return None, f"Error getting audio"
            
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API. Is the backend running?"
    except Exception as e:
        return None, f"Error: {str(e)}"


def send_text_to_api(text, output_format="mp3"):
    if not text or not text.strip():
        return None, "Please enter a message"
    
    try:
        # Get text response first
        text_resp = requests.post(
            f"{API_URL}/api/text/chat-text",
            json={"text": text.strip()},
            timeout=120
        )
        
        bot_text = ""
        if text_resp.status_code == 200:
            bot_text = text_resp.json().get("response_text", "")
        
        # Get audio response
        resp = requests.post(
            f"{API_URL}/api/text/chat",
            json={"text": text.strip(), "output_format": output_format},
            timeout=120
        )
        
        if resp.status_code == 200:
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}")
            temp.write(resp.content)
            temp.close()
            chat_text = f"You: {text}\nBot: {bot_text}"
            return temp.name, chat_text
        else:
            error = resp.json().get("detail", "Unknown error")
            return None, f"Error: {error}"
            
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API. Is the backend running?"
    except Exception as e:
        return None, f"Error: {str(e)}"


def clear_conversation():
    try:
        requests.post(f"{API_URL}/api/conversation/clear", timeout=3)
        return None, None, "Conversation cleared!"
    except:
        return None, None, "Failed to clear conversation"


# ============ Gradio Interface ============

def create_app():
    with gr.Blocks(
        title="VoiceGraph",
        theme=gr.themes.Soft(),
        css=".gradio-container { max-width: 700px !important; margin: auto; }"
    ) as app:
        
        # Header
        gr.Markdown("# 🎙️ VoiceGraph")
        gr.Markdown("*Voice assistant powered by Whisper, LangGraph & Edge TTS*")
        
        # Status indicator
        status = "API Connected" if check_api() else "API Offline - Run: `python main.py`"
        gr.Markdown(f"**Status:** {status}")
        
        # Output format selector
        output_format = gr.Radio(
            choices=["mp3", "ogg", "wav"],
            value="mp3",
            label="Output Format",
            interactive=True
        )
        
        # ===== Voice Input Tab =====
        with gr.Tab("🎤 Voice Chat"):
            gr.Markdown("**Click microphone to record, then click Stop when done:**")
            
            # Audio input (microphone)
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="Record your message"
            )
            
            # Submit button
            voice_submit = gr.Button("Send Voice", variant="primary", size="lg")
            
            # Response audio player
            audio_output = gr.Audio(
                label="VoiceGraph Response",
                type="filepath",
                autoplay=True 
            )
            
            # Conversation display
            voice_chat_display = gr.Textbox(
                label="Conversation",
                lines=4,
                interactive=False
            )
            
            # Wire up voice chat
            voice_submit.click(
                fn=send_audio_to_api,
                inputs=[audio_input, output_format],
                outputs=[audio_output, voice_chat_display]
            )
        
        # ===== Text Input Tab =====
        with gr.Tab("⌨ Text Chat"):
            gr.Markdown("**Type your message:**")
            
            text_input = gr.Textbox(
                label="Your message",
                placeholder="Hello! How can I help?",
                lines=2
            )
            
            text_submit = gr.Button("Send Text", variant="primary", size="lg")
            
            text_audio_output = gr.Audio(
                label="VoiceGraph Response",
                type="filepath",
                autoplay=True
            )
            
            text_chat_display = gr.Textbox(
                label="Conversation",
                lines=4,
                interactive=False
            )
            
            # Wire up text chat
            text_submit.click(
                fn=send_text_to_api,
                inputs=[text_input, output_format],
                outputs=[text_audio_output, text_chat_display]
            )
            
            # Also allow Enter key to submit
            text_input.submit(
                fn=send_text_to_api,
                inputs=[text_input, output_format],
                outputs=[text_audio_output, text_chat_display]
            )
        
        # ===== Clear Button =====
        gr.Markdown("---")
        clear_btn = gr.Button("Clear Conversation", variant="secondary")
        clear_status = gr.Markdown("")
        
        clear_btn.click(
            fn=clear_conversation,
            outputs=[audio_output, text_audio_output, clear_status]
        )
        
        # Footer
        gr.Markdown("---")
        gr.Markdown("*VoiceGraph v1.0 • FastAPI + Gradio + Whisper + LangGraph + Edge TTS*")
    
    return app


# ============ Main ============

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
