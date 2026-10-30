import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("strands").setLevel(logging.DEBUG)

from strands.bidi.agent import BidiAgent
from strands.bidi.io import AudioIO
from strands.bidi.models import BedrockNovaSonicModel


async def main():
    model = BedrockNovaSonicModel(
        model_id="amazon.nova-2-5-sonic",
        region="eu-north-1",
    )
    agent = BidiAgent(
        model=model,
        system_prompt="You are a friendly assistant. Keep replies short.",
    )
    audio = AudioIO(audio_processor=True)

    async def poke():
        await asyncio.sleep(5)
        try:
            await agent.send("Please say hello out loud in one sentence.")
            print(">>> sent text to model")
        except Exception as exc:
            print(">>> send failed:", exc)

    asyncio.create_task(poke())
    print(">>> test running, wait about 15 seconds...")
    await agent.run(inputs=[audio.input()], outputs=[audio.output()])


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("done")