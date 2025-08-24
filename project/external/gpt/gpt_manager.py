from openai import AsyncOpenAI, OpenAI
from openai import Timeout
from dotenv import load_dotenv
import os
import asyncio
from io import BytesIO
from django.conf import settings

try:
    load_dotenv()

    # OpenAI API 키 설정
    CLIENT = OpenAI(api_key=settings.OPENAI_API_KEY)

    # model
    MODEL = "gpt-4o"
except Exception as e:
    print("gpt setting error")

# content가 string이 아닐수도 있다.
def create_message(role: str, content):
    message = {}
    message["role"] = role
    message["content"] = content

    return message

def get_gpt_file_id(file_bytes: bytes, filename: str = "image.jpg", purpose: str = "user_data"):
    buf = BytesIO(file_bytes)
    buf.name = filename                 
    uploaded = CLIENT.files.create(
        file=buf,                       
        purpose=purpose                 
    )
    return uploaded.id

def delete_gpt_file(file_id):
    CLIENT.files.delete(file_id=file_id)

# 특정 질문을 gpt에 물어본다. 실패하면 False를 리턴한다.
def ask_gpt(messages, model=MODEL, max_tokens = 32768):
    retries = 6
    delay = 1

    base_params = {
        "model": model,
        "input": messages,
    }
    # 모델에 따른 세부 설정 분기
    if model == "gpt-4.1":
        params = {
            **base_params,
            "temperature": 0.7,
            "max_output_tokens": max_tokens
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

    response = CLIENT.responses.create(
        **params,
    )

    return response.output_text
    

def test_gpt(question):
    messages = [create_message("user", question)]
    response = ask_gpt(messages, model='gpt-4.1')
    return response

