# LiveKit Twilio Outbound Caller with Gemini AI Agent

An outbound calling system that uses LiveKit Agents to make phone calls via Twilio SIP trunk, with Gemini Live API for realtime speech-to-speech conversation.

## Features

- **Outbound Calling**: Make phone calls using LiveKit SIP integration with Twilio
- **Gemini AI Agent**: Uses Gemini Live API for natural speech-to-speech conversation
- **REST API**: Simple REST API to trigger calls and manage call lifecycle
- **Initial Greeting**: AI agent greets the caller immediately after the call is answered
- **Call Management**: Track call status and hang up calls via API

## Prerequisites

- Python >= 3.9
- LiveKit Cloud account (or self-hosted LiveKit server)
- Google Gemini API key
- LiveKit outbound SIP trunk configured with Twilio
- Twilio account with SIP trunking enabled

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

- `LIVEKIT_URL`: Your LiveKit WebSocket URL (e.g., `wss://your-project.livekit.cloud`)
- `LIVEKIT_API_KEY`: Your LiveKit API key
- `LIVEKIT_API_SECRET`: Your LiveKit API secret
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `SIP_TRUNK_ID`: Your LiveKit outbound trunk ID (get from `lk sip outbound list`)
- `SIP_NUMBER`: Your caller ID (must be a valid Twilio phone number/DID or verified caller ID)

### 3. Get Your SIP Trunk ID

```bash
lk sip outbound list
```

Copy the trunk ID (e.g., `ST_xxxx`) to your `.env` file.

## Running the Agent

### Development Mode

Start the agent in development mode:

```bash
uv run agent.py dev
```

The agent will connect to LiveKit and wait for dispatch requests.

### Production Mode

Start the agent in production mode:

```bash
uv run agent.py start
```

## Running the API Server

Start the FastAPI server:

```bash
uv run uvicorn server:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /call

Trigger an outbound call.

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "agent_instructions": "Optional: Custom instructions for the agent",
  "sip_trunk_id": "Optional: Override default SIP trunk ID",
  "sip_number": "Optional: Caller ID (must be a valid Twilio DID or verified caller ID)"
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

Get the status of a call by room name.

**Response:**
```json
{
  "room_name": "outbound-1234567890",
  "status": "active",
  "num_participants": 2,
  "participants": [
    {
      "identity": "+1234567890",
      "name": "Caller",
      "state": "ACTIVE"
    }
  ]
}
```

### POST /call/{room_name}/hangup

Hang up a call by deleting the room.

**Response:**
```json
{
  "status": "success",
  "message": "Call in room outbound-1234567890 has been hung up"
}
```

## Example Usage

### Make an Outbound Call

```bash
curl -X POST "http://localhost:8000/call" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "sip_number": "+15555551234"
  }'
```

> **Note**: The `sip_number` (caller ID) must be a valid Twilio phone number (DID) that you own, or a verified caller ID in your Twilio account. If not provided, it will use the `SIP_NUMBER` environment variable.

### Check Call Status

```bash
curl "http://localhost:8000/call/outbound-1234567890/status"
```

### Hang Up a Call

```bash
curl -X POST "http://localhost:8000/call/outbound-1234567890/hangup"
```

## Architecture

1. **LiveKit Agent** (`agent.py`): Uses Gemini Live API for speech-to-speech conversation
2. **API Server** (`server.py`): REST API to trigger calls and manage call lifecycle
3. **Twilio SIP Integration**: Outbound trunk configured to route calls through Twilio
4. **Agent Dispatch**: Explicit agent dispatch ensures agent only joins when explicitly called

## How It Works

1. API receives a call request with a phone number
2. API creates a new room and dispatches the agent to it
3. Agent creates a SIP participant to make the outbound call
4. Agent waits for the call to be answered
5. Agent starts a session with Gemini Live API
6. Agent greets the caller and begins conversation
7. Conversation continues until call ends

## Configuration

### Agent Name

The agent is configured with an explicit name (`outbound-caller-agent`) which:
- Disables automatic dispatch (agent won't auto-join rooms)
- Ensures agent only joins when explicitly dispatched via Agent Dispatch API
- Required for telephony to prevent agents from joining rooms unexpectedly

### Gemini Live API

The agent uses Gemini Live API (`gemini-2.0-flash-exp`) for direct speech-to-speech conversation:
- No separate STT/TTS pipeline needed
- Natural, low-latency conversation
- Voice: "Puck" (can be changed in `agent.py`)

## Troubleshooting

### Agent Not Joining Room

- Ensure agent is running (`uv run agent.py dev`)
- Check that `agent_name` matches in both `agent.py` and `server.py`
- Verify LiveKit credentials are correct

### Call Not Connecting

- Verify SIP trunk is configured correctly
- Check that `SIP_TRUNK_ID` is correct (use `lk sip outbound list`)
- Ensure `SIP_NUMBER` (caller ID) is set and is a valid Twilio DID or verified caller ID
- Ensure Twilio SIP trunk is configured to route to LiveKit
- Check Twilio console to verify your phone number is active and caller ID is verified

### API Errors

- Check that LiveKit credentials are set in `.env.local`
- Verify API server is running
- Check logs for detailed error messages

## License

MIT

