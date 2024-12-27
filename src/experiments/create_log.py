import os


def create_experiment_log(base_path):
    # 結果を格納するリスト
    result_str = ""

    # iteration_* フォルダを順に処理
    for folder_name in sorted(os.listdir(base_path)):
        folder_path = os.path.join(base_path, folder_name)
        if os.path.isdir(folder_path) and folder_name.startswith("iteration_"):

            # ファイルパスを作成
            code_description_path = os.path.join(
                folder_path, "code_description.txt"
            )
            critic_message_path = os.path.join(
                folder_path, "critic_message.txt"
            )

            # ファイル内容を読み込み
            try:
                with open(
                    code_description_path, "r", encoding="utf-8"
                ) as code_file:
                    code_description = code_file.read().strip()

                with open(
                    critic_message_path, "r", encoding="utf-8"
                ) as critic_file:
                    critic_message = critic_file.read().strip()

                # 各iterationの内容をフォーマット
                result_str += f"----- {folder_name}\n"
                result_str += f"<実験コード>\n{code_description}\n\n"
                result_str += f"<実験結果に対する批評>\n{critic_message}\n\n"

            except FileNotFoundError as e:
                print(f"Warning: {e}")

    return result_str
