#!/bin/bash

# Ensure scripts fail on error
set -e

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install chromium
playwright install-deps

# Set permissions
echo "Setting permissions..."
mkdir -p /home/appuser/.cache
chmod -R 777 /home/appuser/.cache

# Additional setup for Playwright
echo "Configuring Playwright..."
export PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright

echo "Setup completed successfully"
