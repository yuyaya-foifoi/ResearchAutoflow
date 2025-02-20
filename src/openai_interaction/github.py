from textwrap import dedent

import os
import re
import urllib.parse
import requests

from openai import OpenAI
from pydantic import BaseModel
from ..config.models import MODEL, SMART_MODEL

client = OpenAI()

proposed_method_explain_prompt = """
この論文の提案法を示す部分の必要最低限のコードを抜き出して。このコードは短ければ短いほど良いです。
"""


class ExtractCodeSchema(BaseModel):
    core_implementation_code: str


def fetch_github_code(github_url, max_tokens=50000):
    """
    GitHub URLからコードを取得する関数

    Args:
        github_url (str): GitHubのURL（例：https://github.com/username/repository）
        max_tokens (int): 取得するトークンの最大数（デフォルト: 50000）

    Returns:
        str: レスポンステキスト（エラーの場合はNone）
    """
    # GitHubのURLからリポジトリパスを抽出
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/?.*", github_url)
    if not match:
        print("Invalid GitHub URL")
        return None

    repo_path = match.group(1)

    # ベースURLとパラメータの設定
    base_url = "https://uithub.com"
    params = {
        "accept": "text/plain",
        "maxTokens": str(max_tokens),
        "ext": "py",
    }

    try:
        # URLの構築
        url = f"{base_url}/{repo_path}"

        # パラメータを追加してエンコード
        full_url = f"{url}?{urllib.parse.urlencode(params)}"

        # リクエストの送信
        response = requests.get(full_url)

        # ステータスコードの確認
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: Status code {response.status_code}")
            return None

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None



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
