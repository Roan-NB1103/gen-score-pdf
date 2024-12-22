#!/bin/bash

# システム更新とPythonのセットアップ
apt-get update
apt-get install -y python3-pip

# Playwrightのインストール
pip install playwright

# Playwrightブラウザのインストール
playwright install chromium
playwright install-deps chromium

# 権限の設定
chmod -R 777 /home/appuser/.cache/ms-playwright
