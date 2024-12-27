from textwrap import dedent

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()
MODEL = "gpt-4o"
SMART_MODEL = "o1-mini-2024-09-12"

paper_explain_prompt = """
この論文の内容について詳しく説明して。
"""


class PaperSchema(BaseModel):
    introduction: str
    related_works: str
    proposed_method: str
    mathematical_formulation_of_proposed_method: str
    result: str
    conclusion: str
    future_work: str
    github_url: str


def explain_paper(paper_text: str):
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": dedent(paper_explain_prompt)},
            {"role": "user", "content": paper_text},
        ],
        response_format=PaperSchema,
    )

    return completion.choices[0].message.parsed
