import os
import json
import random
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from livekit import api

load_dotenv(".env")

app = FastAPI(title="Outbound Caller API")

# Initialize LiveKit API client
livekit_api = api.LiveKitAPI(
    url=os.getenv("LIVEKIT_URL"),
    api_key=os.getenv("LIVEKIT_API_KEY"),
    api_secret=os.getenv("LIVEKIT_API_SECRET"),
)


class CallRequest(BaseModel):
    phone_number: str
    agent_instructions: Optional[str] = None
    sip_trunk_id: Optional[str] = None
    sip_number: Optional[str] = None  # Caller ID (must be a valid Twilio DID or verified caller ID)


class CallResponse(BaseModel):
    room_name: str
    status: str
    message: str


@app.post("/call", response_model=CallResponse)
async def make_call(request: CallRequest):
    """
    Trigger an outbound call to the specified phone number.
    
    Args:
        request: CallRequest containing phone_number and optional agent_instructions
        
    Returns:
        CallResponse with room_name and status
    """
    # Generate a unique room name for this call
    room_name = f"outbound-{''.join(str(random.randint(0, 9)) for _ in range(10))}"
    
    # Get SIP trunk ID from environment or request
    sip_trunk_id = request.sip_trunk_id or os.getenv("SIP_TRUNK_ID")
    if not sip_trunk_id:
        raise HTTPException(
            status_code=400,
            detail="SIP_TRUNK_ID not provided in request or environment variables"
        )
    
    # Get caller ID (sip_number) from request or environment
    # This must be a valid Twilio phone number (DID) or verified caller ID
    sip_number = request.sip_number or os.getenv("SIP_NUMBER")
    if not sip_number:
        raise HTTPException(
            status_code=400,
            detail="SIP_NUMBER (caller ID) not provided in request or environment variables. Twilio requires a valid caller ID (either a Twilio DID or verified caller ID)."
        )
    
    # Prepare metadata for the agent
    metadata = {
        "phone_number": request.phone_number,
        "sip_trunk_id": sip_trunk_id,
        "sip_number": sip_number,
    }
    
    if request.agent_instructions:
        metadata["agent_instructions"] = request.agent_instructions
    
    try:
        # Dispatch agent to the room
        print(f"Dispatching agent to room: {room_name}, phone: {request.phone_number}, trunk: {sip_trunk_id}, caller ID: {sip_number}")
        dispatch_response = await livekit_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="outbound-caller-agent",  # Must match agent_name in agent.py
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
        print(f"Agent dispatch response: {dispatch_response}")
        
        return CallResponse(
            room_name=room_name,
            status="initiated",
            message=f"Call initiated to {request.phone_number}. Agent dispatched to room {room_name}."
        )
    except Exception as e:
        print(f"Error dispatching agent: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate call: {str(e)}"
        )


@app.get("/call/{room_name}/status")
async def get_call_status(room_name: str):
    """
    Get the status of a call by room name.
    
    Args:
        room_name: The room name for the call
        
    Returns:
        Dictionary with room status and participant information
    """
    try:
        # Get room information
        room_info = await livekit_api.room.list_rooms(
            api.ListRoomsRequest(names=[room_name])
        )
        
        if not room_info.rooms:
            return {
                "room_name": room_name,
                "status": "not_found",
                "message": "Room not found or call has ended"
            }
        
        room = room_info.rooms[0]
        participants = await livekit_api.room.list_participants(
            api.ListParticipantsRequest(room=room_name)
        )
        
        return {
            "room_name": room_name,
            "status": "active" if room.num_participants > 0 else "ended",
            "num_participants": room.num_participants,
            "participants": [
                {
                    "identity": p.identity,
                    "name": p.name,
                    "state": p.state.name,
                }
                for p in participants.participants
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get call status: {str(e)}"
        )


@app.post("/call/{room_name}/hangup")
async def hangup_call(room_name: str):
    """
    Hang up a call by deleting the room.
    
    Args:
        room_name: The room name for the call to hang up
        
    Returns:
        Dictionary with status message
    """
    try:
        await livekit_api.room.delete_room(
            api.DeleteRoomRequest(room=room_name)
        )
        
        return {
            "status": "success",
            "message": f"Call in room {room_name} has been hung up"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to hang up call: {str(e)}"
        )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Outbound Caller API is running"
    }

