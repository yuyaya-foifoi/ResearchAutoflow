import base64
from textwrap import dedent

from pydantic import BaseModel

from ..config.models import MODEL, WRITING_MODEL
from .provider import call_llm

html_generate_prompt = """

## 入力要件
このジェネレータは以下の入力を必要とします：
1. Pythonコード（分析スクリプト、データ処理）
2. 調査結果（生データまたは処理済みの要約）
3. 実験結果
4. 査読者のコメント（フィードバックと批評点）

## 出力構造
以下のセクションを含むHTMLスライドを生成します：
1. 研究の目的 (Research Purpose)
2. 研究の背景 (Research Background)
3. 関連研究の概観 (Related Work Overview)
4. 関連研究と提案手法の関係性 (Relationship between Related Work and Proposed Method)
5. 提案手法 (Proposed Method)
6. 実験結果 (Experimental Results)
7. 査読者のコメント (Reviewer Comments)
8. Future Work

## 特定の要件
- 提案手法を図として説明して
- 先行研究を対比的に捉えたいので、先行研究は表で説明して
- 実験結果は文字で与えられるもののベースラインとの比較がわかるように図を作図して

## 出力のテンプレ（これを踏まえつつ、モダンなデザインのスライドにして）

<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>研究プレゼンテーション</title>
    <style>
        /* Slide styling */
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .slide-container {
            width: 100%;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        .slide {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            padding: 40px;
            page-break-after: always;
        }
        .slide-title {
            font-size: 28px;
            margin-top: 0;
            margin-bottom: 20px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            color: #2c3e50;
        }
        .content-section {
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .chart-container {
            width: 100%;
            height: 400px;
            margin: 20px 0;
        }
        code {
            font-family: Consolas, Monaco, 'Andale Mono', monospace;
            background: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 14px;
        }
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .comment-box {
            background: #f9f9f9;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
        }
        .highlight {
            background-color: #ffffcc;
            padding: 2px;
        }
        /* Navigation controls */
        .slide-controls {
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }
        .slide-controls button {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
        }
        @media print {
            .slide-controls {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="slide-container">
        <!-- Title Slide -->
        <div class="slide" id="slide-title">
            <h1 class="slide-title">研究タイトル</h1>
            <p class="author">研究者名</p>
            <p class="affiliation">所属</p>
            <p class="date">日付</p>
        </div>
        
        <!-- Research Purpose Slide -->
        <div class="slide" id="slide-purpose">
            <h2 class="slide-title">研究の目的</h2>
            <div class="content-section">
                <!-- Purpose content generated from inputs -->
            </div>
        </div>
        
        <!-- More slides for each section... -->
        
        <!-- Research Background -->
        <div class="slide" id="slide-background">
            <h2 class="slide-title">研究の背景</h2>
            <div class="content-section">
                <!-- Background content -->
            </div>
        </div>
        
        <!-- Related Work -->
        <div class="slide" id="slide-related-work">
            <h2 class="slide-title">関連研究の概観</h2>
            <div class="content-section">
                <!-- Related work content -->
            </div>
        </div>
        
        <!-- Relationship between Related Work and Proposed Method -->
        <div class="slide" id="slide-relationship">
            <h2 class="slide-title">関連研究と提案手法の関係性</h2>
            <div class="content-section">
                <!-- Relationship content -->
            </div>
        </div>
        
        <!-- Proposed Method -->
        <div class="slide" id="slide-method">
            <h2 class="slide-title">提案手法</h2>
            <div class="content-section">
                <!-- Method content -->
            </div>
        </div>
        
        <!-- Experimental Results -->
        <div class="slide" id="slide-results">
            <h2 class="slide-title">実験結果</h2>
            <div class="content-section">
                <!-- Results content -->
            </div>
        </div>
        
        <!-- Reviewer Comments -->
        <div class="slide" id="slide-comments">
            <h2 class="slide-title">査読者のコメント</h2>
            <div class="content-section">
                <!-- Comments content -->
            </div>
        </div>
        
        <!-- Future Work -->
        <div class="slide" id="slide-future">
            <h2 class="slide-title">Future Work</h2>
            <div class="content-section">
                <!-- Future work content -->
            </div>
        </div>
    </div>
    
    <!-- Navigation controls -->
    <div class="slide-controls">
        <button id="prev-slide">前へ</button>
        <button id="next-slide">次へ</button>
    </div>
    
    <script>
        // Simple slide navigation
        const slides = document.querySelectorAll('.slide');
        let currentSlide = 0;
        
        function showSlide(index) {
            // Hide all slides
            slides.forEach(slide => {
                slide.style.display = 'none';
            });
            
            // Show current slide
            slides[index].style.display = 'block';
        }
        
        // Initialize
        showSlide(currentSlide);
        
        // Event listeners
        document.getElementById('prev-slide').addEventListener('click', () => {
            currentSlide = Math.max(0, currentSlide - 1);
            showSlide(currentSlide);
        });
        
        document.getElementById('next-slide').addEventListener('click', () => {
            currentSlide = Math.min(slides.length - 1, currentSlide + 1);
            showSlide(currentSlide);
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight') {
                currentSlide = Math.min(slides.length - 1, currentSlide + 1);
                showSlide(currentSlide);
            } else if (e.key === 'ArrowLeft') {
                currentSlide = Math.max(0, currentSlide - 1);
                showSlide(currentSlide);
            }
        });
    </script>
</body>
</html>
"""

extract_html_prompt = """
あなたは優秀なフロントエンドエンジニアです。
HTMLのコードのみを抽出してください。
"""


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
        WRITING_MODEL, system_prompt=html_generate_prompt, user_prompt=text
    )
    formatted_model_output = call_llm(
        MODEL,
        system_prompt=extract_html_prompt,
        user_prompt=reasoning_model_output,
        temperature=0.7,
        schema=HTMLSchema,
    )

    return formatted_model_output
