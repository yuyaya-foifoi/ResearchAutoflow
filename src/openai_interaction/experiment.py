import base64
from textwrap import dedent

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()
MODEL = "gpt-4o"  # o1-mini-2024-09-12 / gpt-4o
SMART_MODEL = "o1-mini-2024-09-12"  # o1-preview-2024-09-12, o1-mini-2024-09-12
ELITE_MODEL = "o1-preview-2024-09-12"

coder_prompt = """
あなたはユーザーの機械学習実験のアイデアを元に、コードを作成するAIです。
あなたはpythonコードと、その説明を出力します。

---- 注意点
- このpython_codeは絶対に説明などは含めないでください。
- 出力されたpythonコードは exec() を使って実行可能である必要があります
- ** GPUが使えるのでGPUを使う前提のコードで絶対にコーディングしてください **
- このpython codeは理論的な背景がが十分にある必要があります
- ** python_code内では全ての可視化を experiment.png という名前で、1枚の画像として実験のlogを画像としてカレントdirに保存してください**

---- 出力
python_code : pythonのコード（str）
desc_of_python_code : pythonのコードの理論的な説明や議論（str）
"""

coder_explain_prompt = """
あなたはユーザーが入力したpythonコードを出力し、それを解説するAIです。

---- 注意点
- このpython_codeは絶対に説明などは含めないでください。
- 出力されたpythonコードは exec() を使って実行可能である必要があります
- ** GPUが使えるのでGPUを使う前提のコードで絶対にコーディングしてください **
- このpython codeは理論的な背景がが十分にある必要があります
- ** python_code内では全ての可視化を experiment.png という名前で、1枚の画像として実験のlogを画像としてカレントdirに保存してください**
- 中間のlogをprintで見せる必要はないです。またプログレスバーも絶対に表示しないで

---- 出力
python_code : pythonのコード（str）
desc_of_python_code : pythonのコードの理論的な説明や議論（str）
"""

fix_code_prompt = """
あなたはユーザーが入力したpythonコードとエラー文を元に、正しく動くpythonコードを出力するAIです。

---- 注意点
- このpython_codeは絶対に説明などは含めないでください。
- 出力されたpythonコードは exec() を使って実行可能である必要があります
- ** GPUが使えるのでGPUを使う前提のコードで絶対にコーディングしてください **
- このpython codeは理論的な背景がが十分にある必要があります
- ** python_code内では全ての可視化を experiment.png という名前で、1枚の画像として実験のlogを画像としてカレントdirに保存してください**
- 中間のlogをprintで見せる必要はないです。またプログレスバーも絶対に表示しないで

---- 出力
python_code : pythonのコード（str）
desc_of_python_code : pythonのコードの理論的な説明や議論（str）
"""

improve_code_prompt = """
あなたはユーザーの機械学習実験のアイデアと、今までのコーディングに関する実験結果とそれに対する専門家のコメントを元に、コードを更新するAIです。
その際に今までのサーベイの結果も参考にしてください。

---- 注意点
- このpython_codeは絶対に説明などは含めないでください。
- 出力されたpythonコードは exec() を使って実行可能である必要があります
- ** GPUが使えるのでGPUを使う前提のコードで絶対にコーディングしてください **
- このpython codeは理論的な背景がが十分にある必要があります
- ** python_code内では全ての可視化を experiment.png という名前で、1枚の画像として実験のlogを画像としてカレントdirに保存してください**
- 中間のlogをprintで見せる必要はないです。またプログレスバーも絶対に表示しないで

---- 出力
python_code : pythonのコード（str）
desc_of_python_code : pythonのコードの理論的な説明や議論（str）
"""

critic_prompt = """
## 査読の目的
投稿された論文の実験セクションを中心に、研究の価値(Worthiness)、重要性(Values)、新規性(Novelty)を評価してください。
これらの評価においては入力されるサーベイ結果も活用してください。

## 評価手順

### ステップ1：まず以下の3点を評価してください
各項目を1-3で評価し、具体的な理由を述べてください。

1. Worthiness（研究の価値）
- スコア1：限定的な価値しかない
- スコア2：一定の価値がある
- スコア3：非常に価値が高い

確認ポイント：
□ 理論的な深さは十分か
□ 実用的な価値があるか
□ 分野への貢献度は高いか

2. Values（重要性）
- スコア1：重要性が低い
- スコア2：ある程度重要
- スコア3：非常に重要

確認ポイント：
□ 問題設定は重要か
□ 解決方法は適切か
□ コミュニティにとって価値があるか

3. Novelty（新規性）
- スコア1：既存研究の小さな改良程度
- スコア2：部分的に新しい
- スコア3：顕著な新規性がある

確認ポイント：
□ 技術的な新規性はあるか
□ 概念的な新しさはあるか
□ 既存研究と明確な違いがあるか

### ステップ2：実験の評価
実験が適切に行われているか確認してください。

必須チェック項目：
□ 主張を裏付ける実験が行われているか
□ 比較実験は公平か
□ 実験環境は明確に記述されているか
□ 再現性は確保されているか
□ 結果の解釈は適切か

## 評価時の注意点

1. 客観性を保つ
- 個人的な好みではなく、科学的な価値で判断する
- 具体的な根拠に基づいて評価する

2. 建設的なフィードバック
- 問題点の指摘だけでなく、改善案も提示する
- 実行可能な提案をする

3. 明確な説明
- 評価理由を具体的に説明する
- 曖昧な表現を避ける

## 評価例

良い評価の例：
「提案手法は[具体的な技術]において新規性があり、特に[具体的な点]が革新的です。実験では[具体的なデータ]で既存手法との比較が適切に行われており、[数値]の改善が示されています。」

避けるべき評価の例：
「面白い研究だと思います。実験も悪くないと思います。」（具体性に欠ける）
"""

wrap_up_prompt = """
あなたは優秀な研究論文の執筆者です。
実験に関するメモ書きを元に論文のような詳細な文章を執筆してください。
"""

explain_experiment = """
あなたは優れた機械学習の実験の査読者です。
与えられた実験のlogの画像からその実験の結果を詳細に説明して。
説明のポイントとして、全てのグラフの説明をした上で、そのグラフの定量情報を詳細に解説する必要があります。
"""

update_idea_prompt = """
# 機械学習研究アイデア生成プロンプト

あなたは機械学習のトップ国際会議の査読経験が豊富な研究者です。
現在の研究アイデアを以下の観点から分析・改善し、トップ国際会議に採択される可能性の高い研究アイデアを英語で生成してください。
その際に今までのサーベイの結果も参考にしてください。

## 入力情報の確認
- 現在の研究の方向性
- これまでの実験結果
- 見出された課題や限界

## アイデア生成の評価基準

### 1. 研究の価値 (Worthiness)
□ 理論的価値
- 理論的な深さと厳密性
- 新しい理論的洞察
- 既存理論との関連性

□ 実用的価値
- 実世界での適用可能性
- スケーラビリティ
- 計算効率性

□ 影響力
- 分野への貢献度
- 他研究への応用可能性
- 長期的なインパクト

### 2. 研究の重要性 (Values)
□ 問題設定
- 課題の重要性と普遍性
- 解決の緊急性
- コミュニティの関心度

□ アプローチ
- 手法の一般性
- 解決策の完全性
- 技術的な堅実性

□ コミュニティ価値
- 分野の発展への寄与
- 新しい研究方向の開拓
- 知見の共有価値

### 3. 新規性 (Novelty)
□ 技術的新規性
- アルゴリズムの革新性
- 実装の独自性
- 既存手法との差別化

□ 概念的新規性
- 問題設定の斬新さ
- 理論的フレームワークの新しさ
- パラダイムシフトの可能性

### 4. 実験的実現可能性
□ 検証可能性
- 主要な主張の実験的検証
- 比較実験の設計
- 再現性の確保

□ リソース要件
- 計算資源の現実性
- データの入手可能性
- 実装の複雑さ

## 出力フォーマット

```
# 改善された研究アイデア

## 1. コアアイデア
[1-2文で革新的なアイデアを簡潔に]

## 2. 主要な貢献
- 理論面：[具体的な理論的貢献]
- 技術面：[具体的な技術的貢献]
- 実用面：[具体的な実用的貢献]

## 3. 新規性のポイント
[既存研究との明確な差別化ポイント]

## 4. 実験計画の概要
- 主要な検証実験：[具体的な実験内容]
- 比較手法：[具体的なベースライン]
- 評価指標：[具体的な指標]

## 5. 予想されるインパクト
[研究分野への具体的な影響]
```

## 生成時の注意点

1. トップ国際会議のレベルを意識
- 理論的深さと技術的新規性のバランス
- 実験による十分な裏付け
- コミュニティへの明確な貢献

2. 実現可能性の考慮
- 現実的な実験設計
- 利用可能なリソースとの整合性
- 期間内での達成可能性

3. インパクトの最大化
- 分野への貢献度の明確化
- 将来の研究への発展性
- 実用的価値の提示
"""

idea_prompt = """
あなたは研究者のRQの整理者です。
研究者のメモ書きをもとに、研究アイデア（英語）と研究アイデアの説明（英語）に分けて。
"""

experiment_summary_prompt = """
以下の観点を説明して。
- この実験ではアイデアがどのように発展していったのか
- この実験を通して有望だと思う手法を発見できたのか。そしてそれは何なのか
- この実験を通して発見したアイデアは学術的な貢献が高いのか
"""


class CoderSchema(BaseModel):
    python_code: str
    desc_of_python_code: str


class IdeaSchema(BaseModel):
    idea: str
    desc_of_idea: str


def write_initial_python_code(text: str):
    completion = client.chat.completions.create(
        model=ELITE_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": coder_prompt},
            {"role": "user", "content": text},
        ],
    )
    o1_output = completion.choices[0].message

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": dedent(coder_explain_prompt)},
            {"role": "user", "content": o1_output.content},
        ],
        response_format=CoderSchema,
    )

    return completion.choices[0].message.parsed


def fix_python_code(pythoncode: str, error_message: str):
    text = f"""
    ---python code
    {pythoncode}

    ---error message
    {error_message}
    """
    completion = client.chat.completions.create(
        model=SMART_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": coder_prompt},
            {"role": "user", "content": text},
        ],
    )
    o1_output = completion.choices[0].message

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": dedent(fix_code_prompt)},
            {"role": "user", "content": o1_output.content},
        ],
        response_format=CoderSchema,
    )

    return completion.choices[0].message.parsed


def improve_python_code(
    idea: str, code, code_desc, exp_desc, critic_message, survey_df
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
    """

    completion = client.chat.completions.create(
        model=ELITE_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": coder_prompt},
            {"role": "user", "content": text},
        ],
    )
    o1_output = completion.choices[0].message
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": dedent(coder_explain_prompt)},
            {"role": "user", "content": o1_output.content},
        ],
        response_format=CoderSchema,
    )

    return completion.choices[0].message.parsed


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
    completion = client.chat.completions.create(
        model=ELITE_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": critic_prompt},
            {"role": "user", "content": text},
        ],
    )

    return completion.choices[0].message


def create_experiment_summary(experiment_log):

    completion = client.chat.completions.create(
        model=ELITE_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": experiment_summary_prompt},
            {"role": "user", "content": experiment_log},
        ],
    )

    return completion.choices[0].message


def wrap_up(log: str):
    completion = client.chat.completions.create(
        model=MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": wrap_up_prompt},
            {"role": "user", "content": log},
        ],
    )

    return completion.choices[0].message


def update_idea(idea, code, code_desc, exp_desc, critic_message, survey_df):
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
    """

    completion = client.chat.completions.create(
        model=ELITE_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": update_idea_prompt},
            {"role": "user", "content": text},
        ],
    )

    o1_output = completion.choices[0].message
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": dedent(idea_prompt)},
            {"role": "user", "content": o1_output.content},
        ],
        response_format=IdeaSchema,
    )

    return completion.choices[0].message.parsed


def generate_initial_idea(idea, survey_df):
    text = f"""
    ---previous_idea
    {idea}

    ---survey_df
    {survey_df}
    """

    completion = client.chat.completions.create(
        model=ELITE_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": update_idea_prompt},
            {"role": "user", "content": text},
        ],
    )

    o1_output = completion.choices[0].message
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": dedent(idea_prompt)},
            {"role": "user", "content": o1_output.content},
        ],
        response_format=IdeaSchema,
    )

    return completion.choices[0].message.parsed


def generate_query(idea):
    text = f"""
    ---previous_idea
    {idea}
    """

    completion = client.chat.completions.create(
        model=ELITE_MODEL,
        # temperature=0.2,
        messages=[
            {"role": "assistant", "content": update_idea_prompt},
            {"role": "user", "content": text},
        ],
    )

    o1_output = completion.choices[0].message
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": dedent(idea_prompt)},
            {"role": "user", "content": o1_output.content},
        ],
        response_format=IdeaSchema,
    )

    return completion.choices[0].message.parsed


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
            {"role": "system", "content": explain_experiment},
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
