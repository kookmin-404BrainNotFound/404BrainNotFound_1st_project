from external.gpt.gpt_manager import *

messages = [
    {
        "role": "user",
        "content": "안녕"
    }
]

async def test_gpt():
    summarize = await ask_gpt(messages, model='gpt-4.1')