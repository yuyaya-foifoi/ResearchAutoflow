import os
import shutil
from datetime import datetime, timedelta, timezone

import pandas as pd

from ..aws.s3 import upload_folder_to_s3
from ..openai_interaction.experiment import (
    create_experiment_summary,
    critic,
    explain_image,
    improve_python_code,
    update_idea,
    write_initial_python_code,
)
from ..paper_analysis.arxiv import analyze_papers_to_df
from .create_log import create_experiment_log
from .run_code import retry_code_until_success


def run_experiment(
    idea,
    initial_survey_df,
    num_experiment,
    bucket,
    s3_folder=None,
    access_key=None,
    secret_key=None,
    region=None,
):
    """
    研究アイデアに基づいて実験を実行し、結果を記録する関数

    Args:
        idea (str): 研究アイデア
        num_iterations (int, optional): 実験の繰り返し回数. Defaults to 3.

    Returns:
        tuple[str, pd.DataFrame]: (最終的な研究アイデア, 論文解析結果のDataFrame)
    """
    experiment_log = ""
    df_list = []
    df_list.append(initial_survey_df)

    jst = timezone(timedelta(hours=9))  # 日本時間（JST）
    jst_date = datetime.now(jst).strftime("%Y-%m-%d_%H-%M-%S")
    s3_folder = s3_folder + jst_date + "/"

    # 初回の実験
    print("=" * 30 + "初回実験" + "=" * 30)
    response = write_initial_python_code(idea)
    code = response.python_code
    code_desc = response.desc_of_python_code

    # 実験を指定回数繰り返す
    for iteration in range(num_experiment):
        os.makedirs(f"iteration_{iteration+1}", exist_ok=True)
        print(f"=" * 30 + f"実験{iteration + 1}/{num_experiment}" + "=" * 30)

        # コードの実行
        code, filename, stdout, stderr, stderr_summary = (
            retry_code_until_success(code)
        )
        new_file_path = os.path.join(f"iteration_{iteration+1}", filename)
        shutil.move(filename, new_file_path)

        try:
            if os.path.exists("experiment.png"):
                new_image_path = os.path.join(
                    f"iteration_{iteration+1}", f"experiment_{iteration+1}.png"
                )
                shutil.move("experiment.png", new_image_path)
                experiment_explanation = explain_image(
                    new_image_path, code, code_desc
                ).content
        except Exception as e:
            experiment_explanation = (
                f"コードに問題があってうまく動作しませんでした。何度も修正しましたが実行できないのでコードは根本的な修正が必要です。\n"
                f"エラー詳細: {str(stderr_summary)}"
            )

        # ログの記録
        experiment_log += "=" * 50 + f"試行{iteration + 1}" + "=" * 50
        experiment_log += "-" * 25 + f"\n現在の研究アイデア:\n{idea}\n"
        experiment_log += "-" * 25 + f"\nコード:\n{code}\n"
        experiment_log += "-" * 25 + f"\nコードの説明:\n{code_desc}\n"
        experiment_log += (
            "-" * 25 + f"\n実験結果の解析:\n{experiment_explanation}\n"
        )

        # 批評とアイデアの更新
        critic_message = critic(code, code_desc, experiment_explanation, "")
        experiment_log += (
            "-" * 25 + f"\n批評家からのコメント:\n{critic_message.content}\n"
        )
        idea_set = update_idea(
            idea, code, code_desc, experiment_explanation, critic_message, ""
        )

        # 論文解析
        try:
            survey_df = analyze_papers_to_df(idea_set.idea)
            df_list.append(survey_df)
            combined_df = pd.concat(df_list, ignore_index=True)
            combined_df.to_csv("survey_results.csv", index=False)
        except Exception as e:
            print(f"論文解析に失敗しました。エラー詳細: {str(e)}")

        # 次のイテレーションのための準備
        idea = f"{idea_set.idea}\n{idea_set.desc_of_idea}"

        # ログの保存
        with open("experiment.txt", "w", encoding="utf-8") as file:
            file.write(experiment_log)
        with open(
            os.path.join(f"iteration_{iteration+1}", "code_description.txt"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(code_desc)
        with open(
            os.path.join(f"iteration_{iteration+1}", "critic_message.txt"),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(critic_message.content)

        # 最終イテレーション以外でコードを改善
        if iteration < num_experiment - 1:
            improve_response = improve_python_code(
                idea,
                code,
                code_desc,
                experiment_explanation,
                critic_message,
                combined_df.to_string(),
            )
            code = improve_response.python_code
            code_desc = improve_response.desc_of_python_code

        experiment_log = create_experiment_log(".")
        experiment_summary = create_experiment_summary(experiment_log)
        with open("experiment_summary.txt", "w", encoding="utf-8") as file:
            file.write(experiment_summary.content)

        upload_folder_to_s3(bucket, s3_folder, access_key, secret_key, region)

    # return idea, combined_df
