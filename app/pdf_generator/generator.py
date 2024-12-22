import asyncio
import base64
import os
import re
from typing import Dict, Any
from playwright.async_api import async_playwright

# 固定サイズ定数
FONT_SIZES = {"name": 36, "year": 36, "honorific": 29}  # 姓名用  # 学年用  # さん用

# レイアウト定数
LAYOUT = {
    "content_width": 77,  # コンテンツ幅（%）
    "name_width": 180,  # 姓名の幅（px）
    "margin": 20,  # 基本余白
    "name_space": 18,  # 姓名間の余白
}

# 教科と画像のマッピング
SUBJECT_IMAGES = {
    "国語": {"medal": "n_lang1.png", "ribbon": "n_lang2.png"},
    "数学": {"medal": "math1.png", "ribbon": "math2.png"},
    "社会": {"medal": "social1.png", "ribbon": "social2.png"},
    "理科": {"medal": "science1.png", "ribbon": "science2.png"},
    "英語": {"medal": "eng1.png", "ribbon": "eng2.png"},
    "技術家庭": {"medal": "tech1.png", "ribbon": "tech2.png"},
    "音楽": {"medal": "music1.png", "ribbon": "music2.png"},
    "保健体育": {"medal": "sport1.png", "ribbon": "sport2.png"},
}

# 改行が必要な教科
MULTILINE_SUBJECTS = {"技術家庭": "技術\n家庭", "保健体育": "保健\n体育"}


def encode_image_to_base64(image_path: str) -> str:
    """画像ファイルをBase64エンコード"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Warning: Could not load image {image_path}: {e}")
        return ""


def generate_pdf(data: Dict[str, Any]) -> bytes:
    """
    PDFを生成する

    Args:
        data: PDF生成に必要なデータ
            - subject: 教科名
            - test_name: テスト名
            - score: 点数
            - sc_year: 学年
            - last_name: 姓
            - first_name: 名
            - template_type: テンプレートタイプ
                - "得点掲示": 通常の点数表示
                - "点数アップ掲示": 点数の後ろにUPを表示

    Returns:
        bytes: 生成されたPDFデータ
    """
    from . import get_template_path

    # CSSファイルを読み込み（一度だけ読み込む）
    with open(get_template_path("css", "main.css"), "r", encoding="utf-8") as f:
        css_content = f.read()

    # HTMLテンプレートを読み込み
    with open(get_template_path("html", "index.html"), "r", encoding="utf-8") as f:
        html_content = f.read()

    # テンプレートタイプに応じた修正
    if data.get("template_type") == "点数アップ掲示":

        additional_css = """
        /* スコア全体のレイアウト調整 */
    .score-container {
        position: relative;
        width: 600px;  /* スコア表示エリアの幅を確保 */
    }
        /* 点数表示のコンテナ */
        .score {
        width: 485px;
        color: rgba(255,0,0,1);
        position: absolute;
        top: 136px;
        left: 178px;
        text-shadow: 8px 6px 6px rgba(0, 0, 0, 0.25);
        font-family: Inter;
        font-weight: Bold Italic;
        font-size: 227px;
        opacity: 1;
        text-align: center;
        } 

        /* 点UPのコンテナ */
        .point.point-up {
        position: absolute;
        top: 328px;
        left: 610px;  /* 元の.pointと同じ位置 */
        display: flex;
        align-items: baseline;
        white-space: nowrap;
        font-family: Inter;
        font-weight: Bold Italic;
        }

        /* 点の文字 */
        .point.point-up .ten {
            font-size: 104px;
            line-height: 1;
            color: black;
            font-family: Inter;
            font-weight: Bold Italic;
        }

        /* UPの文字 */
        .point.point-up .up {
            font-size: 60px; 
            line-height: 1;
            color: black;
            font-family: Inter;
            font-weight: Bold Italic;
            margin-left: 5px;
        }

        """
        # CSSを追加
        css_content += additional_css
        # HTMLのリプレイス
        html_content = html_content.replace(
            '<span class="point">点</span>',
            '<span class="point point-up"><span class="ten">点</span><span class="up">UP</span></span>',
        )

    # HTMLコンテンツを更新
    subject = data["subject"]
    html_content = html_content.replace(
        "[sc_year]{.sc_year}",
        str(data["sc_year"]),  # f'[{data["sc_year"]}]{{.sc_year}}'
    )
    html_content = html_content.replace(
        "[last_name]{.last_name}",
        str(data["last_name"]),  # f'[{data["last_name"]}]{{.last_name}}'
    )
    html_content = html_content.replace(
        "[first_name]{.first_name}",
        str(data["first_name"]),  # f'[{data["first_name"]}]{{.first_name}}'
    )
    html_content = html_content.replace(
        "[subject]{.subject}",
        str(data["subject"]),  # f'[{data["subject"]}]{{.subject}}'
    )
    html_content = html_content.replace(
        "[test_name]{.test_name}",
        str(data["test_name"]),  # f'[{data["test_name"]}]{{.test_name}}'
    )
    html_content = html_content.replace(
        "[score]{.score}",
        str(data["score"]),  # f'[{data["score"]}]{{.score}}'
    )

    # 教科に対応する画像の設定
    # subject_images = VALID_SUBJECTS[subject]
    subject_images = SUBJECT_IMAGES.get(subject, SUBJECT_IMAGES["国語"])

    # 画像をBase64エンコード
    image_files = {
        "medal": encode_image_to_base64(
            get_template_path("images", subject_images["medal"])
        ),
        "crest": encode_image_to_base64(get_template_path("images", "crest.png")),
        "ribbon": encode_image_to_base64(
            get_template_path("images", subject_images["ribbon"])
        ),
        "twinkle": encode_image_to_base64(get_template_path("images", "twinkle.png")),
    }

    image_files = {
        "medal": encode_image_to_base64(
            get_template_path("images", subject_images["medal"])
        ),
        "crest": encode_image_to_base64(get_template_path("images", "crest.png")),
        "ribbon": encode_image_to_base64(
            get_template_path("images", subject_images["ribbon"])
        ),
        "twinkle": encode_image_to_base64(get_template_path("images", "twinkle.png")),
    }

    # 画像パスをBase64に置換
    css_content = re.sub(
        r'(\.medal\s*{[^}]*background:\s*)url\("[^"]*"\)([^}]*})',
        f'\\1url("data:image/png;base64,{image_files["medal"]}")\\2',
        css_content,
    )
    css_content = re.sub(
        r'(\.ribbon\s*{[^}]*background:\s*)url\("[^"]*"\)([^}]*})',
        f'\\1url("data:image/png;base64,{image_files["ribbon"]}")\\2',
        css_content,
    )
    css_content = css_content.replace(
        'url("../images/crest.png")',
        f'url("data:image/png;base64,{image_files["crest"]}")',
    )
    css_content = css_content.replace(
        'url("../images/twinkle.png")',
        f'url("data:image/png;base64,{image_files["twinkle"]}")',
    )

    # リボンエリアのCSS追加
    css_content += f"""
        .ribbon {{
            width: 660px;
            height: 106px;
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover;
            position: absolute;
            top: 446px;
            left: 91px;
            display: flex;
            justify-content: center;
            align-items: flex-end;
        }}

        .name-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: {LAYOUT['content_width']}%;
            height: 66px;
            padding: 0 {LAYOUT['margin']}px;
            box-sizing: border-box;
        }}

        .name-group {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 {LAYOUT['name_space']}px;
            flex: 1;
            width: {LAYOUT['content_width']}%;
            height: 66px;
        }}

        /* 固定サイズのテキスト要素 */
        .sc_year, .honorific {{
            color: rgba(255,255,255,1);
            font-family: Inter;
            font-weight: Bold Italic;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}

        .sc_year {{
            font-size: {FONT_SIZES['year']}px;
            height: {FONT_SIZES['year']}px;
            line-height: {FONT_SIZES['year']}px;
            min-width: 80px;
            margin-left: {LAYOUT['margin']}px;
        }}

        .honorific {{
            font-size: {FONT_SIZES['honorific']}px;
            height: {FONT_SIZES['honorific']}px;
            line-height: {FONT_SIZES['honorific']}px;
            min-width: 50px;
            margin-left: {LAYOUT['name_space']}px;
        }}

        /* 姓名要素 */
        .last_name, .first_name {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: {LAYOUT['name_width']}px;
            height: 40px;
            font-size: {FONT_SIZES['name']}px;
            color: rgba(255,255,255,1);
            font-family: Inter;
            font-weight: Bold Italic;
            white-space: nowrap;
            text-align: center;
        }}
    """

    # 教科特有のスタイル追加
    if subject in MULTILINE_SUBJECTS:
        css_content += """
            .subject {
                position: absolute;
                white-space: pre-line;
                text-align: center;
                width: 150px;
                top: 140px;
                left: 36px;
                line-height: 1.2;
                font-size: 38px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                color: rgba(255,255,255,1);
                font-family: Inter;
                font-weight: Bold Italic;
            }
        """
    else:
        css_content += """
            .subject {
                position: absolute;
                white-space: nowrap;
                text-align: center;
                width: 150px;
                top: 155px;
                left: 36px;
                font-size: 38px;
                color: rgba(255,255,255,1);
                font-family: Inter;
                font-weight: Bold Italic;
            }
        """

    # 改行が必要な教科の処理
    if subject in MULTILINE_SUBJECTS:
        html_content = html_content.replace(
            f'<span class="subject">{subject}</span>',
            f'<span class="subject">{MULTILINE_SUBJECTS[subject]}</span>',
        )

    # Create final HTML
    html_with_css = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <link href="https://fonts.googleapis.com/css?family=Inter&display=swap" rel="stylesheet" />
            <style>
                {css_content}
                html, body {{
                    margin: 0;
                    padding: 0;
                    width: 842px;
                    height: 595px;
                    overflow: hidden;
                }}
            </style>
        </head>
        <body>
            {html_content.split('<body>')[1].split('</body>')[0]}
        </body>
    </html>
    """

    async def generate_pdf_async():
        # Generate PDF
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = await browser.new_page()
            await page.set_viewport_size({"width": 842, "height": 595})
            await page.set_content(html_with_css, wait_until="networkidle")
            await page.wait_for_timeout(1000)
            pdf_data = await page.pdf(
                width="842px",
                height="595px",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            await browser.close()
            return pdf_data

    return asyncio.run(generate_pdf_async())


if __name__ == "__main__":
    # テスト用のデータ
    test_data = {
        "subject": "数学",
        "test_name": "第1回定期考査",
        "score": 95,
        "sc_year": "小3",
        "last_name": "山田",
        "first_name": "太郎",
    }
    asyncio.run(generate_pdf(test_data))
