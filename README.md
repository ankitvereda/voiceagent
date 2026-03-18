# voiceagent

# Voice Agent - Pipecat Audio Application

A real-time voice conversational AI agent built with [Pipecat](https://github.com/pipecat-ai/pipecat) that supports multiple transport types including Twilio, Daily.co, and WebRTC.

## Features

- **Multi-transport support**: Twilio, Daily.co, WebRTC
- **Real-time speech processing**: Speech-to-Text (Deepgram), Text-to-LLM (OpenAI/Groq), Text-to-Speech (ElevenLabs)
- **Multiple AI Assistant Options**: 
  - General assistant (agent.py)
  - Hospital appointment booking assistant (agent1.py)
  - Custom assistant (a.py)
- **Audio recording**: Automatic conversation recording in WAV format
- **Metrics logging**: Built-in latency and performance tracking

## Prerequisites

- Python 3.10 or higher
- UV package manager (recommended) or pip
- API keys for:
  - OpenAI
  - Deepgram (STT)
  - ElevenLabs (TTS)
  - Daily.co (optional, for Daily transport)

## Setup

### 1. Clone & Install Dependencies


# Or using pip
uv pip install -r requiremnets.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# LLM Services
OPENAI_API_KEY=sk-...

# Speech Services
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=... 




```

Get your API keys from:
- **OpenAI**: https://platform.openai.com/api-keys
- **Deepgram**: https://console.deepgram.com/
- **ElevenLabs**: https://elevenlabs.io/

-

## Agent Options

### `agent.py` - General WebRTC Assistant
- Uses Groq LLM or OpenAI
- Supports Inworld TTS or ElevenLabs
- Smart turn detection using LocalSmartTurnAnalyzerV3
- Metrics logging for performance tracking
- Best for: WebRTC, Daily.co, and general conversations

**Services**:
- LLM: OpenAI gpt-4o-mini or Groq
- STT: Deepgram
- TTS: ElevenLabs or Inworld
- Transports: Daily, Twilio WebSocket, WebRTC

### `agent1.py` - Hospital Appointment Booking
- Specialized for medical appointment booking workflows
- Records all conversations to WAV files
- OpenAI gpt-4o-mini LLM
- ElevenLabs TTS
- Best for: Twilio or WebRTC integration with medical booking flows

**Services**:
- LLM: OpenAI gpt-4o-mini
- STT: Deepgram
- TTS: ElevenLabs
- Transports: Twilio WebSocket, WebRTC, Daily

### `a.py` - Alternative Assistant Configuration
- Similar to agent1.py but with different setup
- Hospital appointment booking assistant
- Audio recording enabled
- Best for: Testing and alternative deployment options

## Running the Application



### Option 1: Running Specific Agents

```bash


# Run agent1.py
python agent1.py --transport twilio

# Run a.py
python a.py
```

## Twilio Integration

### How It Works

1. **Twilio Webhook Configuration**: Configure Twilio to send WebSocket connections to your server
2. **Transport Handling**: Pipecat automatically detects Twilio connections and uses `FastAPIWebsocketParams`
3. **Audio Format**: Handles Twilio's 8kHz mono audio format automatically
4. **Frame Serialization**: Uses TwilioFrameSerializer for protocol compatibility

### Setup Steps

1. **Get Your Server URL**: Deploy or expose your server (e.g., with ngrok for testing)
   ```bash
   # In another terminal, expose local port 7860

   ```



3. **Test Connection**:
   - Call your Twilio number
   - Check server logs for connection details
   - Audio should stream to bot and responses should play back
