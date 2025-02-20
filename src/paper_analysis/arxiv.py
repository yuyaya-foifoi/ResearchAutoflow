import base64
import json
from io import BytesIO
from textwrap import dedent
from typing import Dict, List

import openai
import pandas as pd
import requests
from openai import OpenAI
from PIL import Image
from pydantic import BaseModel
from PyPDF2 import PdfReader

from ..openai_interaction.arxiv import explain_paper
from ..openai_interaction.github import (
    extract_core_implementation,
    fetch_github_code,
)


def fetch_arxiv_papers(query, max_results=10):
    """
    Fetch papers from arXiv API based on a query.

    Parameters:
        query (str): The search query (e.g., 'machine learning').
        max_results (int): Maximum number of results to fetch.

    Returns:
        list: A list of dictionaries containing paper information.
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        # Parse the response
        papers = []
        feed = response.text
        entries = feed.split("<entry>")[1:]  # Split into individual entries

        for entry in entries:
            title_start = entry.find("<title>") + len("<title>")
            title_end = entry.find("</title>")
            title = entry[title_start:title_end].strip()

            summary_start = entry.find("<summary>") + len("<summary>")
            summary_end = entry.find("</summary>")
            summary = entry[summary_start:summary_end].strip()

            link_start = entry.find("<id>") + len("<id>")
            link_end = entry.find("</id>")
            link = entry[link_start:link_end].strip()

            papers.append({"title": title, "summary": summary, "link": link})

        return papers
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []


def extract_text_from_arxiv_pdf(arxiv_url):
    # PDFデータを取得
    response = requests.get(arxiv_url)
    if response.status_code != 200:
        raise Exception(
            f"Failed to retrieve the PDF. Status code: {response.status_code}"
        )

    # PDFデータをメモリに展開
    pdf_file = BytesIO(response.content)
    reader = PdfReader(pdf_file)

    # 全ページのテキストを抽出
    text = ""
    for page in reader.pages:
        text += page.extract_text()
        text += "\n\n"  # 各ページの間に改行を追加

    return text


def analyze_papers_to_df(query: str, num_papers: int = 5) -> pd.DataFrame:
    """
    arXivから論文を検索し、解析結果をDataFrameとして返す

    Args:
        query (str): 検索クエリ
        num_papers (int): 取得する論文数

    Returns:
        pd.DataFrame: 解析結果のDataFrame
    """
    # arXivから論文を検索
    papers = fetch_arxiv_papers(query, max_results=num_papers)

    # 各論文の解析結果を格納するリスト
    analyzed_papers = []

    for paper in papers:
        try:
            # PDFのURLを作成
            pdf_url = paper["link"].replace("abs", "pdf") + ".pdf"

            # PDFからテキストを抽出
            pdf_text = extract_text_from_arxiv_pdf(pdf_url)

            # 論文を解析
            analysis = explain_paper(pdf_text)

            paper_dict = {
                "title": paper["title"],
                "link": paper["link"],
                "github_url": None,  # デフォルトでNone
                "introduction": analysis.introduction,
                "related_works": analysis.related_works,
                "proposed_method": analysis.proposed_method,
                "mathematical_formulation_of_proposed_method": analysis.mathematical_formulation_of_proposed_method,
                "result": analysis.result,
                "conclusion": analysis.conclusion,
                "future_work": analysis.future_work,
                "core_implementation_code": None,  # デフォルトでNone
                #'minimal_training_inference_code': None  # デフォルトでNone
            }

            # GitHubのコードが存在する場合のみ、関連フィールドを更新
            githubcodes = fetch_github_code(analysis.github_url)
            if githubcodes:
                code = extract_core_implementation(
                    githubcodes,
                    analysis.mathematical_formulation_of_proposed_method,
                )
                paper_dict.update(
                    {
                        "github_url": analysis.github_url,
                        "core_implementation_code": code.core_implementation_code,
                        #'minimal_training_inference_code': code.minimal_training_inference_code
                    }
                )

            analyzed_papers.append(paper_dict)

        except Exception as e:
            print(f"Error processing paper '{paper['title']}': {str(e)}")
            continue

    # DataFrameを作成
    if analyzed_papers:
        df = pd.DataFrame(analyzed_papers)
    else:
        # 空のDataFrameを作成（スキーマに合わせたカラムを持つ）
        df = pd.DataFrame(
            columns=[
                "title",
                "link",
                "github_url" "introduction",
                "related_works",
                "proposed_method",
                "mathematical_formulation_of_proposed_method",
                "result",
                "conclusion",
                "future_work",
                "core_implementation_code",
                #'minimal_training_inference_code'
            ]
        )

    return df
