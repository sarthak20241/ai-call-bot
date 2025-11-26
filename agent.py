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
    dial_info = json.loads(ctx.job.metadata or "{}")
    phone_number = dial_info.get("phone_number")
    
    if not phone_number:
        print("ERROR: No phone number provided in job metadata")
        ctx.shutdown()
        return

    sip_trunk_id = dial_info.get("sip_trunk_id") or ctx.env.get("SIP_TRUNK_ID")
    if not sip_trunk_id:
        print("ERROR: SIP_TRUNK_ID not found in environment or metadata")
        ctx.shutdown()
        return
    
    sip_number = dial_info.get("sip_number") or ctx.env.get("SIP_NUMBER")
    if not sip_number:
        print("ERROR: SIP_NUMBER (caller ID) not found in environment or metadata")
        ctx.shutdown()
        return

    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=sip_trunk_id,
                sip_number=sip_number,
                sip_call_to=phone_number,
                participant_identity=phone_number,
                participant_name="Caller",
                wait_until_answered=True,
                krisp_enabled=True,
            )
        )
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
            noise_cancellation=noise_cancellation.BVCTelephony(),
        ),
    )

    await session.generate_reply(
        instructions="Greet the caller warmly. Introduce yourself and let them know you're calling to help. Ask how you can assist them today."
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-caller-agent",
        )
    )

