import base64
from textwrap import dedent

from pydantic import BaseModel

from ..config.models import MODEL, WRITING_MODEL
from .prompt import EXTRACT_HTML_PROMPT, HTML_GENERATE_PROMPT
from .provider import call_llm


class HTMLSchema(BaseModel):
    HTML: str


def generate_html(
    idea: str, code, code_desc, exp_desc, critic_message, survey_df
):
    text = f"""
    ---idea
    {idea}

    ---code
    {code}

    ---code_desc
    {code_desc}

    ---exp_desc
    {exp_desc}

    ---critic_message
    {critic_message}

    ---survey_df
    {survey_df}
    """

    reasoning_model_output = call_llm(
        WRITING_MODEL, system_prompt=HTML_GENERATE_PROMPT, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=EXTRACT_HTML_PROMPT,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=HTMLSchema,
    )

    return formatted_model_output
