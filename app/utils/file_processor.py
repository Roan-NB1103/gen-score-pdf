import pandas as pd
import chardet
from typing import Optional, List
import io


def detect_encoding(file_obj: io.BytesIO) -> str:
    """
    ファイルのエンコーディングを検出する

    Args:
        file_obj: バイナリモードで開いたファイルオブジェクト

    Returns:
        str: 検出されたエンコーディング
    """
    # ファイルポインタを先頭に戻す
    file_obj.seek(0)
    raw_data = file_obj.read()

    # エンコーディングを検出
    result = chardet.detect(raw_data)
    encoding = result["encoding"]

    # UTF-8とShift-JIS以外の場合はUTF-8として扱う
    if encoding.lower() not in ["utf-8", "shift-jis", "shift_jis"]:
        encoding = "utf-8"

    # ファイルポインタを先頭に戻す
    file_obj.seek(0)
    return encoding


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> Optional[str]:
    """
    データフレームのバリデーションを行う

    Args:
        df: 検証するデータフレーム
        required_columns: 必須カラムのリスト

    Returns:
        Optional[str]: エラーメッセージ。問題なければNone
    """
    # 必須カラムの存在チェック
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        return f"必須カラムが不足しています: {', '.join(missing_columns)}"

    # データ型のチェック
    try:
        # 点数を数値型に変換
        df["score"] = pd.to_numeric(df["score"])

        # 点数の範囲チェック
        if not df["score"].between(0, 100).all():
            return "点数は0から100の間である必要があります"

        # 必須項目の入力チェック
        for col in ["subject", "test_name", "sc_year", "last_name", "first_name"]:
            if df[col].isna().any():
                return f"{col}に空の値が含まれています"

        # 教科名のチェック
        valid_subjects = [
            "国語",
            "数学",
            "社会",
            "理科",
            "英語",
            "技術家庭",
            "音楽",
            "保健体育",
        ]
        invalid_subjects = set(df["subject"]) - set(valid_subjects)
        if invalid_subjects:
            return f"無効な教科名が含まれています: {', '.join(invalid_subjects)}"

    except Exception as e:
        return f"データの検証中にエラーが発生しました: {str(e)}"

    return None


def process_uploaded_file(uploaded_file) -> Optional[pd.DataFrame]:
    """
    アップロードされたファイルを処理する

    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト

    Returns:
        Optional[pd.DataFrame]: 処理されたデータフレーム。エラー時はNone
    """
    try:
        # ファイルタイプに応じた読み込み
        if uploaded_file.type == "text/csv":
            # CSVファイルの場合、エンコーディングを検出して読み込み
            encoding = detect_encoding(uploaded_file)
            df = pd.read_csv(uploaded_file, encoding=encoding)
        elif (
            uploaded_file.type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ):
            # Excelファイルの場合
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("サポートされていないファイル形式です")

        # データの整形
        df = df.map(
            lambda x: x.strip() if isinstance(x, str) else x
        )  # 文字列の前後の空白を削除

        # 必要なカラムの型変換
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df["score"] = df["score"].astype(int)

        # 文字列カラムの変換
        string_columns = ["subject", "test_name", "sc_year", "last_name", "first_name"]
        for col in string_columns:
            df[col] = df[col].astype(str)

        return df

    except Exception as e:
        raise Exception(f"ファイルの処理中にエラーが発生しました: {str(e)}")


def create_sample_data() -> pd.DataFrame:
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
