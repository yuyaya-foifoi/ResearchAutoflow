import os

import boto3
from botocore.exceptions import NoCredentialsError


def upload_folder_to_s3(bucket, s3_folder, access_key, secret_key, region):
    MAX_FILE_SIZE = 1 * 1024 * 1024
    """フォルダ全体をS3にアップロード。ただし、10MB以上のファイルは除外"""
    folder_path = os.getcwd()
    try:
        # S3クライアントの作成
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

        # フォルダ内のすべてのファイルを再帰的にアップロード
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                local_path = os.path.join(root, file)
                file_size = os.path.getsize(local_path)  # ファイルサイズを取得

                # ファイルサイズが10MB以上の場合、スキップ
                if file_size > MAX_FILE_SIZE:
                    print(
                        f"Skipping {local_path} (size: {file_size / (1024 * 1024):.2f} MB)"
                    )
                    continue

                # S3のキーを作成（ローカルフォルダ構造を保持）
                relative_path = os.path.relpath(local_path, folder_path)
                s3_key = os.path.join(s3_folder, relative_path).replace(
                    "\\", "/"
                )

                # ファイルをアップロード
                s3_client.upload_file(local_path, bucket, s3_key)
                print(f"Uploaded {local_path} to s3://{bucket}/{s3_key}")
    except NoCredentialsError:
        print("AWS credentials not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
