# VoiceGraph

A voice bot with conversational AI, built with FastAPI, Gradio, Whisper, LangGraph, and Edge TTS.

## Features

- Speech-to-Text: Google Speech Recognition
- LLM: Groq (primary) with Google Gemini fallback
- Text-to-Speech: Microsoft Edge TTS
- Orchestration: LangGraph for pipeline management
- API: FastAPI backend
- Frontend: Gradio web interface

## Architecture

```
Audio Input -> STT -> LangGraph -> LLM -> TTS -> Audio Output
```

## Quick Start

### Backend (FastAPI)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

API available at http://localhost:8000

### Web App (Gradio)

```bash
cd WebApp
pip install -r requirements.txt
python app.py
```

App available at http://localhost:7860

## Deployment

### Hugging Face Spaces

The WebApp is deployed on Hugging Face Spaces. Files needed:
- app.py
- requirements.txt
- README.md (with YAML frontmatter)
- packages.txt (for system dependencies like ffmpeg)

Live demo: https://huggingface.co/spaces/tagc23/Voice-Bot

### CI/CD

GitHub Actions workflow automatically deploys to Hugging Face Spaces on push to main branch.

Setup:
1. Add secrets in GitHub repo settings: HF_TOKEN, HF_USERNAME, HF_SPACE_NAME
2. Push to main branch
3. Workflow deploys WebApp folder to HF Spaces

See `.github/workflows/deploy-to-hf.yml` for configuration.

## Environment Variables

| Variable | Description |
|----------|-------------|
| GROQ_API_KEY | Groq API key |
| GOOGLE_API_KEY | Google Gemini API key (fallback) |
| OPENROUTER_API_KEY | OpenRouter Api Key

## Challenges Faced

### Hugging Face Spaces Dependency Conflicts

The main challenge was `huggingface_hub` version conflicts. HF Spaces has a system-level `huggingface_hub` that cannot be overwritten by requirements.txt.

Issues encountered:
- `ImportError: cannot import name 'HfFolder' from 'huggingface_hub'` - This API was removed in newer versions
- `split_torch_state_dict_into_shards` import error with transformers
- Gradio version conflicts with gradio_client

Solutions:
- Removed explicit Gradio version from requirements.txt - let HF Spaces use its pre-installed version
- Replaced openai-whisper with SpeechRecognition library to avoid huggingface_hub dependency
- Used sdk_version in README.md YAML to specify Gradio version

### Audio Component Bug

Gradio 5.x had a JSON schema bug with Audio components (`TypeError: argument of type 'bool' is not iterable`). Fixed by using Gradio 6.x which is pre-installed on HF Spaces.

## Project Structure

```
VoiceBot/
├── main.py              # FastAPI backend
├── config.py            # Configuration
├── modules/             # STT, TTS, LLM, Orchestrator
├── utils/               # Logger, Audio utilities
├── WebApp/
│   ├── app.py           # Gradio web app
│   ├── requirements.txt
│   ├── README.md        # HF Spaces config
│   └── packages.txt     # System dependencies
└── .github/
    └── workflows/
        └── deploy-to-hf.yml  # CI/CD workflow
```

## License

MIT License
