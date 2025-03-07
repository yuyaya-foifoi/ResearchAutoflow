import base64
from textwrap import dedent

from openai import OpenAI
from pydantic import BaseModel

from ..config.models import ELITE_MODEL, MODEL, SMART_MODEL, REFLECTION_MODEL
from .prompt import (
    CODE_FORMAT_PROMPT,
    CODER_PROMPT,
    CRITIC_PROMPT,
    EXPERIMENT_EXPLANATION_PROMPT,
    EXPERIMENT_SUMMARY_PROMPT,
    FIX_CODE_PROMPT,
    IDEA_FORMAT_PROMPT,
    QUERY_FORMAT_PROMPT,
    SURVEY_QUERY_PROMPT,
    UPDATE_IDEA_PROMPT,
    wrap_up_prompt,
    REFLECTION_MODULE_PROMPT
)
from .provider import call_llm

client = OpenAI()


class CoderSchema(BaseModel):
    python_code: str
    desc_of_python_code: str


class IdeaSchema(BaseModel):
    idea: str
    desc_of_idea: str


def write_initial_python_code(text: str):

    reasoning_model_output = call_llm(
        ELITE_MODEL, system_prompt=CODER_PROMPT, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=CODE_FORMAT_PROMPT,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=CoderSchema,
    )

    return formatted_model_output


def fix_python_code(pythoncode: str, error_message: str):
    text = f"""
    ---python code
    {pythoncode}

    ---error message
    {error_message}
    """

    reasoning_model_output = call_llm(
        SMART_MODEL, system_prompt=FIX_CODE_PROMPT, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=CODE_FORMAT_PROMPT,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=CoderSchema,
    )

    return formatted_model_output


def improve_python_code(
    idea: str, code, code_desc, exp_desc, critic_message, survey_df, reflection_comment
):
    text = f"""
    ---idea
    {idea}

    ---previous_code
    {code}

    ---previou_code_desc
    {code_desc}

    ---exp_desc
    {exp_desc}

    ---critic_message
    {critic_message}

    ---survey_df
    {survey_df}

    ---reflection_comment
    {reflection_comment}
    """

    reasoning_model_output = call_llm(
        ELITE_MODEL, system_prompt=CODER_PROMPT, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=CODE_FORMAT_PROMPT,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=CoderSchema,
    )

    return formatted_model_output


def critic(code, code_desc, exp_desc, survey_df):
    text = f"""
    ---code
    {code}

    ---code_desc
    {code_desc}

    ---exp_desc
    {exp_desc}

    ---survey_df
    {survey_df}
    """

    reasoning_model_output = call_llm(
        ELITE_MODEL, system_prompt=CRITIC_PROMPT, user_prompt=text
    )

    return reasoning_model_output


def create_experiment_summary(experiment_log):

    reasoning_model_output = call_llm(
        ELITE_MODEL,
        system_prompt=EXPERIMENT_SUMMARY_PROMPT,
        user_prompt=experiment_log,
    )

    return reasoning_model_output


def wrap_up(log: str):

    model_output = call_llm(
        MODEL, system_prompt=wrap_up_prompt, user_prompt=log, temperature=0.7
    )

    return model_output


def update_idea(idea, code, code_desc, exp_desc, critic_message, survey_df, reflection_comment):
    text = f"""
    ---previous_idea
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

    ---reflection_comment
    {reflection_comment}
    """

    reasoning_model_output = call_llm(
        ELITE_MODEL, system_prompt=UPDATE_IDEA_PROMPT, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=IDEA_FORMAT_PROMPT,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=IdeaSchema,
    )

    return formatted_model_output


def generate_initial_idea(idea, survey_df):
    text = f"""
    ---previous_idea
    {idea}

    ---survey_df
    {survey_df}
    """

    reasoning_model_output = call_llm(
        ELITE_MODEL, system_prompt=UPDATE_IDEA_PROMPT, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=IDEA_FORMAT_PROMPT,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=IdeaSchema,
    )

    return formatted_model_output


def generate_query(idea):
    text = f"""
    ---previous_idea
    {idea}
    """

    reasoning_model_output = call_llm(
        ELITE_MODEL, system_prompt=SURVEY_QUERY_PROMPT, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=QUERY_FORMAT_PROMPT,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=IdeaSchema,
    )

    return formatted_model_output


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def explain_image(img_path, code, code_desc):
    log = f"""
  以下のコードと以下のコードの説明を踏まえて、画像からこの実験の結果を詳細に説明して。
  --- code
  {code}

  --- code_desc
  {code_desc}

  """
    base64_image = encode_image(img_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": EXPERIMENT_EXPLANATION_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": log},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            },
        ],
        max_tokens=2048,
    )
    return response.choices[0].message


# ------------------------------------ Reflection関係 ------------------------------------

def reflection(log, survey_df):
    text = f"""
    ---log
    {log}

    ---survey
    {survey_df}
    """

    reasoning_model_output = call_llm(
        REFLECTION_MODEL, system_prompt=REFLECTION_MODULE_PROMPT, user_prompt=text
    )

    return reasoning_model_output