import streamlit as st
import pandas as pd
import numpy as np
import io
import zipfile
import tempfile
import os
from datetime import datetime
from pdf_generator.generator import generate_pdf, SUBJECT_IMAGES
from utils.file_processor import detect_encoding, validate_dataframe
import subprocess

# Playwrightのブラウザインストール
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        os.makedirs("/home/appuser/.cache", exist_ok=True)
        os.chmod("/home/appuser/.cache", 0o777)
    except Exception as e:
        print(f"Failed to install Playwright browser: {e}")

# ページ設定
st.set_page_config(page_title="成績表PDF生成アプリ", page_icon="📊", layout="wide")

# セッション状態の初期化
if "generated_pdfs" not in st.session_state:
    st.session_state.generated_pdfs = []

# 定数定義
REQUIRED_COLUMNS = [
    "subject",
    "test_name",
    "score",
    "sc_year",
    "last_name",
    "first_name",
]
SUBJECTS = list(SUBJECT_IMAGES.keys())
GRADE = ["小1", "小2", "小3", "小4", "小5", "小6", "中1", "中2", "中3"]


def validate_input(values):
    """入力値のバリデーション"""
    errors = []
    if not values["last_name"]:
        errors.append("姓を入力してください")
    if not values["first_name"]:
        errors.append("名を入力してください")
    if not 0 <= values["score"] <= 100:
        errors.append("点数は0から100の間で入力してください")
    return errors


def create_single_pdf():
    """1枚ずつPDF作成のUI"""
    st.subheader("1枚ずつ作成")

    with st.form("single_pdf_form"):
        col1, col2 = st.columns(2)

        with col1:
            subject = st.selectbox("教科", SUBJECTS, help="教科を選択してください")
            test_name = st.text_input(
                "テスト名", value="第1回定期考査", help="テスト名を入力してください"
            )
            score = st.number_input(
                "点数",
                min_value=0,
                max_value=100,
                value=100,
                help="0から100までの点数を入力してください",
            )

        with col2:
            sc_year = st.selectbox("学年", GRADE, help="学年を選択してください")
            last_name = st.text_input("姓", help="姓を入力してください")
            first_name = st.text_input("名", help="名を入力してください")

        submit = st.form_submit_button("PDFを作成", use_container_width=True)

    if submit:
        input_values = {
            "subject": subject,
            "test_name": test_name,
            "score": score,
            "sc_year": sc_year,
            "last_name": last_name,
            "first_name": first_name,
            "template_type": st.session_state.template_type,
        }

        errors = validate_input(input_values)
        if errors:
            for error in errors:
                st.error(error)
        else:
            try:
                with st.spinner("PDFを生成中..."):
                    pdf_data = generate_pdf(input_values)

                    # PDFのダウンロードボタンを表示
                    st.success("PDF生成が完了しました")
                    filename = f"{last_name}{first_name}_{subject}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.download_button(
                        "PDFをダウンロード",
                        pdf_data,
                        filename,
                        mime="application/pdf",
                        use_container_width=True,
                    )

            except Exception as e:
                st.error(f"PDF生成中にエラーが発生しました: {str(e)}")


def create_bulk_pdf():
    """まとめてPDF作成のUI"""
    st.subheader("まとめて作成")
    st.caption(
        "[教科｜テスト名｜点数｜学年｜姓｜名] の順で作成された表データをアップロードしてください。"
    )
    st.caption("詳しくはマニュアルをご参照ください。")
    # ファイルアップロード用のコンポーネント
    uploaded_file = st.file_uploader(
        "CSVまたはExcelファイルをアップロード",
        type=["csv", "xlsx"],
        help="UTF-8またはShift-JISエンコードのファイルをアップロードしてください。\n"
        f"必要な列: {', '.join(REQUIRED_COLUMNS)}",
    )

    if uploaded_file:
        try:
            # ファイルの読み込みとエンコーディング検出
            if uploaded_file.type == "text/csv":
                encoding = detect_encoding(uploaded_file)
                df = pd.read_csv(uploaded_file, encoding=encoding)
            else:  # Excel
                df = pd.read_excel(uploaded_file)

            # データフレームの検証
            validation_error = validate_dataframe(df, REQUIRED_COLUMNS)
            if validation_error:
                st.error(validation_error)
                return

            # データプレビューの表示
            st.write("データプレビュー:")
            st.dataframe(df.head(), use_container_width=True, hide_index=True)

            if st.button("PDFを一括生成", use_container_width=True):
                pdfs = []
                progress_text = "PDFを生成中..."
                progress_bar = st.progress(0, text=progress_text)

                try:
                    # 一時ディレクトリの作成
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # 各行のPDFを生成
                        for i, row in df.iterrows():
                            # 進捗状況の更新
                            progress = (i + 1) / len(df)
                            progress_bar.progress(
                                progress, text=f"{progress_text} ({i+1}/{len(df)})"
                            )

                            # PDF生成用のデータ作成
                            input_values = {
                                "subject": row["subject"],
                                "test_name": row["test_name"],
                                "score": row["score"],
                                "sc_year": row["sc_year"],
                                "last_name": row["last_name"],
                                "first_name": row["first_name"],
                                "template_type": st.session_state.template_type,
                            }

                            # PDF生成
                            pdf_data = generate_pdf(input_values)
                            filename = f"{row['last_name']}{row['first_name']}_{row['subject']}.pdf"
                            pdf_path = os.path.join(temp_dir, filename)

                            # 一時ファイルとして保存
                            with open(pdf_path, "wb") as f:
                                f.write(pdf_data)
                            pdfs.append((pdf_path, filename))

                        # ZIPファイルの作成
                        zip_filename = (
                            f"成績表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                        )
                        zip_path = os.path.join(temp_dir, zip_filename)

                        with zipfile.ZipFile(zip_path, "w") as zip_file:
                            for pdf_path, filename in pdfs:
                                zip_file.write(pdf_path, filename)

                        # ZIPファイルの読み込みとダウンロードボタンの表示
                        with open(zip_path, "rb") as f:
                            zip_data = f.read()

                        st.success(f"全{len(df)}件のPDF生成が完了しました")
                        st.download_button(
                            "ZIPファイルをダウンロード",
                            zip_data,
                            zip_filename,
                            mime="application/zip",
                            use_container_width=True,
                        )

                except Exception as e:
                    st.error(f"PDF生成中にエラーが発生しました: {str(e)}")
                finally:
                    progress_bar.empty()

        except Exception as e:
            st.error(f"ファイル処理中にエラーが発生しました: {str(e)}")


def main():
    st.title("成績表PDF生成アプリ")

    # モード選択
    mode = st.radio(
        "作成モードを選択",
        ["1枚ずつ作成", "まとめて作成"],
        horizontal=True,
        help="1枚ずつ作成：画面でデータを入力して作成します。 | まとめて作成：csvまたはExcelファイルをアップロードして、まとめて作成します。",
    )
    template = st.radio(
        "テンプレートを選択",
        ["得点掲示", "点数アップ掲示"],
        horizontal=True,
        help="得点掲示：各教科のテストの点数を表示 | 点数アップ掲示：点数の後ろにUPを表示",
    )
    # セッション状態にテンプレート選択を保存
    st.session_state.template_type = template

    st.divider()

    # 選択したモードに応じたUIの表示
    if mode == "1枚ずつ作成":
        create_single_pdf()
    else:
        create_bulk_pdf()


if __name__ == "__main__":
    main()
