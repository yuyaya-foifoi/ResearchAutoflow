from textwrap import dedent

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()
MODEL = "gpt-4o"
SMART_MODEL = "o1-mini-2024-09-12"

proposed_method_explain_prompt = """
この論文の提案法を示す部分のコードを抜き出して
"""


class ExtractCodeSchema(BaseModel):
    core_implementation_code: str


def extract_core_implementation(code: str, proposed_method):
    text = f"""
    ---- 提案法
    {proposed_method}

    ---- コード
    {code}

    """
    completion = client.chat.completions.create(
        model=SMART_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": proposed_method_explain_prompt},
            {"role": "user", "content": text},
        ],
    )

    o1_output = completion.choices[0].message
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": dedent(proposed_method_explain_prompt),
            },
            {"role": "user", "content": o1_output.content},
        ],
        response_format=ExtractCodeSchema,
    )

    return completion.choices[0].message.parsed
