import json
from dotenv import load_dotenv

from livekit import agents, api
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google, noise_cancellation

load_dotenv(".env")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful and friendly AI assistant making an outbound call.
            Greet the person warmly and offer your assistance. Be conversational and natural.
            Keep your responses concise and clear."""
        )


async def entrypoint(ctx: agents.JobContext):
    print(f"Agent entrypoint called for room: {ctx.room.name}")
    print(f"Job metadata: {ctx.job.metadata}")
    
    # Read phone number from job metadata
    dial_info = json.loads(ctx.job.metadata or "{}")
    phone_number = dial_info.get("phone_number")
    
    if not phone_number:
        print("ERROR: No phone number provided in job metadata")
        ctx.shutdown()
        return

    # Get SIP trunk ID from environment
    sip_trunk_id = dial_info.get("sip_trunk_id") or ctx.env.get("SIP_TRUNK_ID")
    if not sip_trunk_id:
        print("ERROR: SIP_TRUNK_ID not found in environment or metadata")
        ctx.shutdown()
        return
    
    # Get caller ID (sip_number) from metadata or environment
    # This must be a valid Twilio phone number (DID) or verified caller ID
    sip_number = dial_info.get("sip_number") or ctx.env.get("SIP_NUMBER")
    if not sip_number:
        print("ERROR: SIP_NUMBER (caller ID) not found in environment or metadata")
        print("Twilio requires a valid caller ID (either a Twilio DID or verified caller ID)")
        ctx.shutdown()
        return
    
    print(f"Making call to: {phone_number} using trunk: {sip_trunk_id}, caller ID: {sip_number}")

    # Create SIP participant to make outbound call
    sip_participant_identity = phone_number
    print(f"Creating SIP participant for call to {phone_number}...")
    try:
        sip_participant = await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                # This ensures the participant joins the correct room
                room_name=ctx.room.name,
                # This is the outbound trunk ID to use
                sip_trunk_id=sip_trunk_id,
                # The caller ID (must be a valid Twilio DID or verified caller ID)
                sip_number=sip_number,
                # The outbound phone number to dial
                sip_call_to=phone_number,
                participant_identity=sip_participant_identity,
                participant_name="Caller",
                # This will wait until the call is answered before returning
                wait_until_answered=True,
                krisp_enabled=True,  # Enable noise cancellation
            )
        )
        print(f"SUCCESS: SIP participant created: {sip_participant}")
        print(f"Call answered successfully for {phone_number}")
    except api.TwirpError as e:
        print(f"Error creating SIP participant: {e.message}, "
              f"SIP status: {e.metadata.get('sip_status_code')} "
              f"{e.metadata.get('sip_status')}")
        ctx.shutdown()
        return
    except Exception as e:
        print(f"Unexpected error creating SIP participant: {e}")
        ctx.shutdown()
        return

    # Create agent session with Gemini Live API for speech-to-speech conversation
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            temperature=0.8,
            instructions="""You are a helpful and friendly AI assistant making an outbound call.
            Greet the person warmly and offer your assistance. Be conversational and natural.
            Keep your responses concise and clear.""",
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # For telephony applications, use BVCTelephony for best results
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    # Generate initial greeting after call is answered
    await session.generate_reply(
        instructions="Greet the caller warmly. Introduce yourself and let them know you're calling to help. Ask how you can assist them today."
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Explicit agent name - disables automatic dispatch
            # Agent only joins when explicitly dispatched via Agent Dispatch API
            agent_name="outbound-caller-agent",
        )
    )

