"""
ファイル処理ユーティリティモジュール
CSV/Excelファイルの読み込みと検証を行う機能を提供
"""

import pandas as pd
import chardet
from typing import Optional, List, Union, BinaryIO, Dict, Any
import io

__version__ = "1.0.0"

# 定数定義
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
ALLOWED_ENCODINGS = {"utf-8", "shift-jis", "shift_jis"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# カラム定義
REQUIRED_COLUMNS = [
    "subject",  # 教科
    "test_name",  # テスト名
    "score",  # 点数
    "sc_year",  # 学年
    "last_name",  # 姓
    "first_name",  # 名
]


class FileProcessError(Exception):
    """ファイル処理に関するエラー"""

    pass


def detect_encoding(file_obj: Union[BinaryIO, bytes]) -> str:
    """
    ファイルのエンコーディングを検出する

    Args:
        file_obj: バイナリモードで開いたファイルオブジェクトまたはバイトデータ

    Returns:
        str: 検出されたエンコーディング

    Raises:
        FileProcessError: エンコーディング検出に失敗した場合
    """
    try:
        # ファイルポインタを先頭に戻す
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
            raw_data = file_obj.read()
        else:
            raw_data = file_obj

        # エンコーディングを検出
        result = chardet.detect(raw_data)
        detected_encoding = result["encoding"].lower()

        # 許可されたエンコーディングかチェック
        if detected_encoding in ALLOWED_ENCODINGS:
            return detected_encoding
        return "utf-8"  # デフォルトはUTF-8

    except Exception as e:
        raise FileProcessError(f"エンコーディングの検出に失敗しました: {str(e)}")
    finally:
        # ファイルポインタを先頭に戻す
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)


def validate_dataframe(df: pd.DataFrame) -> Optional[str]:
    """
    データフレームのバリデーションを行う

    Args:
        df: 検証するデータフレーム

    Returns:
        Optional[str]: エラーメッセージ。問題なければNone
    """
    from pdf_generator import VALID_SUBJECTS

    # 必須カラムの存在チェック
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        return f"必須カラムが不足しています: {', '.join(missing_columns)}"

    try:
        # 点数を数値型に変換
        df["score"] = pd.to_numeric(df["score"])

        # 点数の範囲チェック
        invalid_scores = df[~df["score"].between(0, 100)]
        if not invalid_scores.empty:
            return "点数は0から100の間である必要があります"

        # 必須項目の入力チェック
        for col in REQUIRED_COLUMNS:
            if df[col].isna().any():
                return f"{col}に空の値が含まれています"

        # 教科名のチェック
        invalid_subjects = set(df["subject"]) - set(VALID_SUBJECTS.keys())
        if invalid_subjects:
            return f"無効な教科名が含まれています: {', '.join(invalid_subjects)}"

    except Exception as e:
        return f"データの検証中にエラーが発生しました: {str(e)}"

    return None


def process_file(file_obj: BinaryIO, file_extension: str) -> pd.DataFrame:
    """
    アップロードされたファイルを処理する

    Args:
        file_obj: アップロードされたファイルオブジェクト
        file_extension: ファイルの拡張子 (.csvまたは.xlsx)

    Returns:
        pd.DataFrame: 処理されたデータフレーム

    Raises:
        FileProcessError: ファイル処理中にエラーが発生した場合
    """
    try:
        # ファイルサイズチェック
        file_obj.seek(0, 2)  # ファイル末尾に移動
        file_size = file_obj.tell()
        if file_size > MAX_FILE_SIZE:
            raise FileProcessError(
                f"ファイルサイズが大きすぎます。上限: {MAX_FILE_SIZE/1024/1024}MB"
            )
        file_obj.seek(0)  # ファイル先頭に戻る

        # ファイル形式に応じた読み込み
        if file_extension.lower() == ".csv":
            encoding = detect_encoding(file_obj)
            df = pd.read_csv(file_obj, encoding=encoding)
        elif file_extension.lower() == ".xlsx":
            df = pd.read_excel(file_obj)
        else:
            raise FileProcessError("サポートされていないファイル形式です")

        # データの整形
        df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)

        # バリデーション
        error_msg = validate_dataframe(df)
        if error_msg:
            raise FileProcessError(error_msg)

        return df

    except pd.errors.EmptyDataError:
        raise FileProcessError("ファイルにデータが含まれていません")
    except Exception as e:
        if isinstance(e, FileProcessError):
            raise
        raise FileProcessError(f"ファイルの処理中にエラーが発生しました: {str(e)}")


def get_sample_data() -> pd.DataFrame:
    """
    サンプルデータを生成する（開発・テスト用）

    Returns:
        pd.DataFrame: サンプルデータを含むデータフレーム
    """
    data = {
        "subject": ["国語", "数学", "英語"],
        "test_name": ["第1回定期考査"] * 3,
        "score": [95, 88, 92],
        "sc_year": ["小3"] * 3,
        "last_name": ["山田", "鈴木", "佐藤"],
        "first_name": ["太郎", "花子", "一郎"],
    }
    return pd.DataFrame(data)


__all__ = [
    "process_file",
    "validate_dataframe",
    "detect_encoding",
    "get_sample_data",
    "REQUIRED_COLUMNS",
    "ALLOWED_EXTENSIONS",
    "FileProcessError",
]
