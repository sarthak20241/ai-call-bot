# AI-Powered Outbound Calling System

A production-ready outbound calling system that leverages LiveKit Agents, Twilio SIP trunking, and Google Gemini Live API to enable real-time AI-powered phone conversations. The system provides a RESTful API for initiating calls and managing call lifecycles with natural speech-to-speech interaction.

## 🚀 Key Features

- **Real-time Speech-to-Speech AI**: Powered by Google Gemini Live API for natural, low-latency conversations
- **Telephony Integration**: Seamless integration with Twilio via LiveKit SIP trunking
- **RESTful API**: Clean REST API for call management and monitoring
- **Production-Ready**: Error handling, call status tracking, and graceful shutdown
- **Noise Cancellation**: Built-in telephony-optimized noise cancellation for crystal-clear audio

## 🏗️ Architecture

The system consists of three main components:

1. **AI Agent** (`agent.py`): LiveKit agent using Gemini Live API for speech-to-speech conversation
2. **API Server** (`server.py`): FastAPI-based REST API for call orchestration
3. **SIP Integration**: Twilio SIP trunk configured for outbound calling

### System Flow

```
API Request → Agent Dispatch → SIP Call Initiation → Gemini AI Conversation
```

1. REST API receives call request with phone number
2. LiveKit creates room and dispatches AI agent
3. Agent initiates SIP call via Twilio trunk
4. Upon answer, Gemini Live API handles real-time conversation
5. Agent greets caller and maintains natural dialogue

## 🛠️ Technology Stack

- **Python 3.9+**: Core language
- **LiveKit Agents**: Voice AI framework
- **Google Gemini Live API**: Speech-to-speech AI model
- **FastAPI**: REST API framework
- **Twilio**: SIP trunking provider
- **LiveKit Cloud**: Real-time media infrastructure

## 📋 Prerequisites

- Python >= 3.9
- LiveKit Cloud account
- Google Gemini API key
- Twilio account with SIP trunking
- LiveKit outbound SIP trunk configured

## ⚙️ Installation

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd ai-call
uv sync
```

### 2. Environment Configuration

Create a `.env` file with the following variables:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
GOOGLE_API_KEY=your-google-api-key
SIP_TRUNK_ID=ST_xxxx
SIP_NUMBER=+1234567890
```

Get your SIP trunk ID:
```bash
lk sip outbound list
```

## 🚦 Usage

### Start the AI Agent

```bash
uv run agent.py dev
```

### Start the API Server

```bash
uv run uvicorn server:app --reload --port 8000
```

### Make an Outbound Call

```bash
curl -X POST "http://localhost:8000/call" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "sip_number": "+15555551234"
  }'
```

### Check Call Status

```bash
curl "http://localhost:8000/call/{room_name}/status"
```

### Hang Up Call

```bash
curl -X POST "http://localhost:8000/call/{room_name}/hangup"
```

## 📡 API Reference

### POST /call

Initiates an outbound call.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "agent_instructions": "Optional custom instructions",
  "sip_trunk_id": "Optional trunk override",
  "sip_number": "Optional caller ID override"
}
```

**Response:**
```json
{
  "room_name": "outbound-1234567890",
  "status": "initiated",
  "message": "Call initiated to +1234567890. Agent dispatched to room outbound-1234567890."
}
```

### GET /call/{room_name}/status

Retrieves call status and participant information.

**Response:**
```json
{
  "room_name": "outbound-1234567890",
  "status": "active",
  "num_participants": 2,
  "participants": [...]
}
```

### POST /call/{room_name}/hangup

Terminates an active call.

## 🔧 Technical Details

### Agent Configuration

- **Model**: Gemini 2.0 Flash Experimental
- **Voice**: Puck (configurable)
- **Dispatch**: Explicit agent dispatch for telephony reliability
- **Noise Cancellation**: BVCTelephony for optimal call quality

### Error Handling

- Comprehensive error handling for SIP connection failures
- Graceful shutdown on errors
- Detailed error messages for debugging

## 📝 License

MIT
