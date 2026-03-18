
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import datetime
import io
import os
import wave
from typing import Optional

import aiofiles
import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response import LLMAssistantAggregatorParams
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.transports.daily.transport import DailyParams

# ✅ Azure LLM (replaces GoogleLLMService)


load_dotenv(override=True)


transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
}


async def save_audio(audio: bytes, sample_rate: int, num_channels: int):
    if len(audio) > 0:
        filename = f"recording_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        with io.BytesIO() as buffer:
            with wave.open(buffer, "wb") as wf:
                wf.setsampwidth(2)
                wf.setnchannels(num_channels)
                wf.setframerate(sample_rate)
                wf.writeframes(audio)
            async with aiofiles.open(filename, "wb") as file:
                await file.write(buffer.getvalue())
        logger.info(f"Merged audio saved to {filename}")
    else:
        logger.info("No audio data to save")


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments, testing: Optional[bool] = False):
    # ✅ Use Azure LLM instead of Google
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
    )
    messages = [
        {
            "role": "system",
            "content": (
                """You are a helpful and professional hospital appointment booking assistant.

Your job is to help users book doctor appointments quickly and accurately.

Follow these rules:

1. Greet the user politely and ask how you can help.
2. Collect required information step-by-step:

   * Patient name
   * Age (optional)
   * Symptoms or reason for visit
   * Preferred doctor (if any)
   * Preferred date and time
3. If the user doesn’t know which doctor to choose:

   * Suggest the appropriate department (e.g., cardiologist, dermatologist, general physician).
4. Confirm details before booking:

   * Repeat all collected information clearly.
5. Ask for confirmation before finalizing the booking.
6. After confirmation:

   * Provide appointment details (doctor name, date, time, hospital/clinic).
7. Be concise, polite, and conversational.
8. Handle corrections gracefully if the user changes any detail.
9. If information is missing, ask follow-up questions.
10. Never assume unknown details — always ask.

Tone:

* Friendly, professional, and reassuring
* Clear and easy to understand
* Suitable for voice interaction

Example flow:
User: I want to book an appointment
Assistant: Sure, may I know your name?
...
Assistant: Based on your symptoms, I recommend a gener
""")
        },
    ]

    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)
    
    # NOTE: Watch out! This will save all the conversation in memory. You can
    # pass buffer_size to get periodic callbacks.
    audiobuffer = AudioBufferProcessor()

    pipeline = Pipeline(
        [
            transport.input(),          # Websocket input from client
            stt,                        # Speech-To-Text
            context_aggregator.user(),
            llm,                        # ✅ Azure LLM
            tts,                        # Text-To-Speech
            transport.output(),         # Websocket output to client
            audiobuffer,                # Used to buffer the audio in the pipeline
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        # Start recording.
        await audiobuffer.start_recording()
        # Kick off the conversation.
        messages.append(
            {
                "role": "system",
                "content": "Please introduce yourself to the user.",
            }
        )
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await task.cancel()

    @audiobuffer.event_handler("on_audio_data")
    async def on_audio_data(buffer, audio, sample_rate, num_channels):
        await save_audio(audio, sample_rate, num_channels)

    # handle_sigint is provided by runner_args
    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint, force_gc=True)
    await runner.run(task)


async def bot(runner_args: RunnerArguments, testing: Optional[bool] = False):
    """Main bot entry point compatible with Pipecat Cloud."""
    
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args, testing)


if __name__ == "__main__":
    from pipecat.runner.run import main
    main()