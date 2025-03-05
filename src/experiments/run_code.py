import subprocess
from datetime import datetime

import pytz

from ..llm_interaction.experiment import fix_python_code


def _filter_progress_bar(stderr: str) -> str:
    """進捗バー表示を除外してエラーメッセージを返す

    Args:
        stderr (str): 元のエラーメッセージ

    Returns:
        str: 進捗バーを除いたエラーメッセージ
    """
    # 進捗バー行を含まない行のみを抽出
    lines = [
        line
        for line in stderr.split("\n")
        if not all(
            char in "|█░▒▓═╩╦0123456789%<>MBs/."
            for char in line.replace(" ", "")
        )
    ]

    # 空の行を除去して結合
    return "\n".join(line for line in lines if line.strip())


def execute_python_code(code: str) -> tuple[str, str, str]:
    """
    Pythonコードを実行し、ファイル名、標準出力、エラー出力を返す関数

    Args:
        code (str): 実行するPythonコード

    Returns:
        tuple[str, str, str]: (ファイル名, 標準出力, エラー出力)
    """

    # JSTでの現在時刻を取得してファイル名を生成
    jst = pytz.timezone("Asia/Tokyo")
    current_time = datetime.now(jst)
    filename = f"code_{current_time.strftime('%Y%m%d_%H%M%S')}.py"

    # コードをファイルに書き出し
    with open(filename, "w", encoding="utf-8") as file:
        file.write(code)

    # ファイルを実行
    result = subprocess.run(
        ["python", filename], capture_output=True, text=True, timeout=None
    )

    return (
        filename,
        result.stdout,
        result.stderr,
        _filter_progress_bar(result.stderr),
    )


def retry_code_until_success(
    code: str, max_attempt: int = 15
) -> tuple[str, str, str, str]:
    """
    Pythonコードを実行し、エラーが発生した場合は修正を試みる関数

    Args:
        code (str): 実行するPythonコード
        max_attempt (int, optional): 最大修正試行回数. Defaults to 15.

    Returns:
        tuple[str, str, str, str]: (最終的なコード, 最終実行のファイル名, 標準出力, 標準エラー出力)
    """
    fix_attempts = 0

    while fix_attempts < max_attempt:
        filename, stdout, stderr, stderr_summary = execute_python_code(code)

        if not stderr:  # エラーがない場合
            return code, filename, stdout, stderr, stderr_summary

        print(f"エラー発生: {stderr_summary}")
        fix_attempts += 1
        print(f"修正試行 {fix_attempts}/{max_attempt}")

        if fix_attempts >= max_attempt:
            print("最大修正試行回数に達しました。")
            return code, filename, stdout, stderr, stderr_summary

        # エラーメッセージを基にコードを修正
        fix_code = fix_python_code(code, stderr_summary)
        code = fix_code.python_code

    return code, filename, stdout, stderr, stderr_summary
