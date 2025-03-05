from textwrap import dedent

from anthropic import Anthropic
from openai import OpenAI


def call_anthropic_model(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
):
    client = Anthropic()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    message = client.messages.create(
        model=model_name,
        max_tokens=12800,
        messages=messages,
    )
    return message.content[0].text


def call_openai_model(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature=None,
    schema=None,
):
    client = OpenAI()

    # Create the messages array
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Prepare common parameters
    params = {
        "model": model_name,
        "messages": messages,
    }

    # Only add temperature for non-reasoning models
    if model_name not in REASONING_MODELS:
        params["temperature"] = temperature

    # Handle schema if provided
    if schema is not None:
        params["response_format"] = schema
        completion = client.beta.chat.completions.parse(**params)
        return completion.choices[0].message.parsed
    else:
        completion = client.chat.completions.create(**params)
        return completion.choices[0].message.content


PROVIDER_FUNCTION_MAP = {
    "anthropic": call_anthropic_model,
    "openai": call_openai_model,
}

MODEL_PROVIDER_MAP = {
    # openai
    "gpt-4o": "openai",
    "o3-mini-2025-01-31": "openai",
    "o1-2024-12-17": "openai",
    # anthropic
    "claude-3-7-sonnet-20250219": "anthropic",
}

REASONING_MODELS = ["o3-mini-2025-01-31", "o1-2024-12-17"]


def call_llm(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature=None,
    schema=None,
):
    provider = MODEL_PROVIDER_MAP[model_name]

    if provider not in PROVIDER_FUNCTION_MAP:
        raise ValueError(f"No implementation for provider: {provider}")

    if provider == "anthropic":
        return PROVIDER_FUNCTION_MAP[provider](
            model_name, system_prompt, user_prompt
        )
    else:
        return PROVIDER_FUNCTION_MAP[provider](
            model_name, system_prompt, user_prompt, temperature, schema
        )
