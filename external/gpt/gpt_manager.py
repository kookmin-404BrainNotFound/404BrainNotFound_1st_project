from openai import AsyncOpenAI
from openai import Timeout
from dotenv import load_dotenv
import os
import asyncio

try:
    load_dotenv()

    # OpenAI API 키 설정
    CLIENT = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # model
    MODEL = "gpt-4o"
except Exception as e:
    print("gpt setting error")


def create_message(role: str, content: str):
    message = {}
    message["role"] = role
    message["content"] = content

    return message


# 특정 질문을 gpt에 물어본다. 실패하면 False를 리턴한다.
async def ask_gpt(messages, model=MODEL, max_tokens = 32768):
    retries = 6
    delay = 1

    base_params = {
        "model": model,
        "messages": messages,
    }
    # 모델에 따른 세부 설정 분기
    if model == "gpt-4.1":
        params = {
            **base_params,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
    elif model == "o4-mini":
        params = {
            **base_params,
            "max_completion_tokens": max_tokens,
            "reasoning_effort": "high",
        }
    elif model == "gpt-4o":
        params = {
            **base_params,
            "temperature": 1.0,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
    else:
        params = {
            **base_params,
            "temperature": 1.0,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }

    response = await CLIENT.chat.completions.create(
        **params,
    )

    result = response.choices[0].message.content
    return result
    

messages = [
    {
        "role": "user",
        "content": "안녕"
    }
]

async def test_gpt():
    summarize = await ask_gpt(messages, model='gpt-4.1')
    print(summarize)


asyncio.run(test_gpt())
