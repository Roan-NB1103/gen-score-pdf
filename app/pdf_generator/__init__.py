import os
from typing import Dict, Any, Optional
from .generator import generate_pdf

# バージョン情報
__version__ = "1.0.0"

# パス設定
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(PACKAGE_DIR, "templates")
IMAGES_DIR = os.path.join(TEMPLATES_DIR, "images")
CSS_DIR = os.path.join(TEMPLATES_DIR, "css")

# 定数定義
VALID_SUBJECTS = {
    "国語": {"medal": "n_lang1.png", "ribbon": "n_lang2.png"},
    "数学": {"medal": "math1.png", "ribbon": "math2.png"},
    "社会": {"medal": "social1.png", "ribbon": "social2.png"},
    "理科": {"medal": "science1.png", "ribbon": "science2.png"},
    "英語": {"medal": "eng1.png", "ribbon": "eng2.png"},
    "技術家庭": {"medal": "tech1.png", "ribbon": "tech2.png"},
    "音楽": {"medal": "music1.png", "ribbon": "music2.png"},
    "保健体育": {"medal": "sport1.png", "ribbon": "sport2.png"},
}

MULTILINE_SUBJECTS = {"技術家庭": "技術\n家庭", "保健体育": "保健\n体育"}

# 設定のデフォルト値
DEFAULT_CONFIG = {
    "font_name": "Inter",
    "default_subject": "国語",
    "score_range": (0, 100),
}


def validate_data(data: Dict[str, Any]) -> Optional[str]:
    """
    入力データのバリデーション

    Args:
        data: 検証する入力データ

    Returns:
        Optional[str]: エラーメッセージ。問題なければNone
    """
    required_fields = [
        "subject",
        "test_name",
        "score",
        "sc_year",
        "last_name",
        "first_name",
    ]

    # 必須フィールドの存在チェック
    for field in required_fields:
        if field not in data:
            return f"必須フィールドが不足しています: {field}"
        if not data[field]:
            return f"{field}が空です"

    # 教科名の検証
    if data["subject"] not in VALID_SUBJECTS:
        return f"無効な教科名です: {data['subject']}"

    # 点数の検証
    try:
        score = int(data["score"])
        if not (0 <= score <= 100):
            return "点数は0から100の間である必要があります"
    except ValueError:
        return "点数は整数である必要があります"

    return None


def get_template_path(template_type: str, filename: str) -> str:
    """
    テンプレートファイルの絶対パスを取得

    Args:
        template_type: テンプレートのタイプ（'images', 'css', 'html'）
        filename: ファイル名

    Returns:
        str: テンプレートファイルの絶対パス
    """
    if template_type == "images":
        return os.path.join(IMAGES_DIR, filename)
    elif template_type == "css":
        return os.path.join(CSS_DIR, filename)
    else:  # html
        return os.path.join(TEMPLATES_DIR, filename)


def create_pdf(data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> bytes:
    """
    PDFを生成する際のメインインターフェース

    Args:
        data: PDF生成に必要なデータ
        config: 追加の設定（オプション）

    Returns:
        bytes: 生成されたPDFデータ
    """
    # 設定の初期化
    current_config = DEFAULT_CONFIG.copy()
    if config:
        current_config.update(config)

    # データのバリデーション
    error = validate_data(data)
    if error:
        raise ValueError(error)

    # PDFの生成
    try:
        return generate_pdf(data)
    except Exception as e:
        raise RuntimeError(f"PDF生成中にエラーが発生しました: {str(e)}")


__all__ = ["create_pdf", "validate_data", "get_template_path", "VALID_SUBJECTS"]
