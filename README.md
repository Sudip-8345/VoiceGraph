# 🎙️ VoiceBot

A production-ready voice bot with human-like conversational AI, built with FastAPI, Streamlit, Whisper, LangGraph, and Edge TTS.

## Features

- **Speech-to-Text**: OpenAI Whisper (primary) with SpeechRecognition fallback
- **LLM**: OpenRouter API with customizable models
- **Text-to-Speech**: Microsoft Edge TTS (primary) with gTTS fallback
- **Orchestration**: LangGraph for reliable pipeline management
- **API**: FastAPI with async support and comprehensive error handling
- **Frontend**: Streamlit web interface for easy interaction

## Architecture

```
Audio Input → STT (Whisper) → LangGraph → LLM (OpenRouter) → TTS (Edge TTS) → Audio Output
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env and add your OpenRouter API key
```

### 3. Start the Backend

```bash
python main.py
```

API will be available at `http://localhost:8000`

### 4. Start the Frontend

```bash
streamlit run app.py
```

Frontend will be available at `http://localhost:8501`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/voice/process` | POST | Process audio → get audio response |
| `/api/voice/process-with-text` | POST | Process audio → get JSON with text |
| `/api/text/chat` | POST | Text input → audio response |
| `/api/text/chat-text` | POST | Text input → text response |
| `/api/conversation/clear` | POST | Clear conversation history |
| `/api/tts/voices` | GET | List available TTS voices |

## Usage Examples

### cURL - Voice Processing

```bash
curl -X POST "http://localhost:8000/api/voice/process" \
  -F "audio=@recording.wav" \
  -F "output_format=mp3" \
  --output response.mp3
```

### cURL - Text Chat

```bash
curl -X POST "http://localhost:8000/api/text/chat" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "output_format": "mp3"}' \
  --output response.mp3
```

### Python Client

```python
import requests

# Voice processing
with open("recording.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/voice/process",
        files={"audio": f},
        data={"output_format": "mp3"}
    )
    with open("response.mp3", "wb") as out:
        out.write(response.content)

# Text chat
response = requests.post(
    "http://localhost:8000/api/text/chat-text",
    json={"text": "What's the weather like?"}
)
print(response.json()["response_text"])
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `OPENROUTER_MODEL` | LLM model to use | `meta-llama/llama-3.1-8b-instruct:free` |
| `TTS_VOICE` | Edge TTS voice | `en-US-AriaNeural` |
| `TTS_RATE` | Speech rate | `+0%` |
| `MAX_AUDIO_DURATION_SECONDS` | Max input audio length | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Supported Audio Formats

**Input**: WAV (recommended), MP3, OGG, M4A, WebM, FLAC

**Output**: MP3, OGG (WhatsApp-ready), WAV

## Project Structure

```
VoiceBot/
├── .env.example        # Environment template
├── requirements.txt    # Python dependencies
├── config.py          # Configuration management
├── main.py            # FastAPI backend
├── app.py             # Streamlit frontend
├── modules/
│   ├── __init__.py
│   ├── stt.py         # Speech-to-Text
│   ├── tts.py         # Text-to-Speech
│   ├── llm.py         # LLM client
│   └── orchestrator.py # LangGraph pipeline
└── utils/
    ├── __init__.py
    ├── logger.py      # Logging utilities
    └── audio.py       # Audio processing
```

## Customization

### Change Bot Personality

Edit the `system_prompt` in [config.py](config.py) to customize the bot's personality and behavior.

### Change TTS Voice

Available voices can be listed via the API:

```bash
curl http://localhost:8000/api/tts/voices
```

Update `TTS_VOICE` in `.env` with your preferred voice.

### Use Different LLM Model

Browse available models at [OpenRouter](https://openrouter.ai/models) and update `OPENROUTER_MODEL` in `.env`.

## WhatsApp Integration

The bot outputs MP3/OGG audio compatible with WhatsApp. For WhatsApp integration:

1. Use the `/api/voice/process` endpoint
2. Set `output_format=ogg` for optimal WhatsApp compatibility
3. Send the response audio via WhatsApp Business API

## Troubleshooting

### "Cannot connect to API"
- Ensure the FastAPI backend is running (`python main.py`)
- Check if port 8000 is available

### "Speech recognition failed"
- Ensure FFmpeg is installed for audio processing
- Try using WAV format for input
- Check audio quality and volume

### "LLM API error"
- Verify your OpenRouter API key is correct
- Check your API credits/quota

## License

MIT License - see LICENSE file for details.
