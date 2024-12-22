#!/bin/bash

# Ensure scripts fail on error
set -e

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install --with-deps chromium

# Set permissions
echo "Setting permissions..."
mkdir -p /home/appuser/.cache
chmod -R 777 /home/appuser/.cache

# Additional setup for Playwright
echo "Configuring Playwright..."
PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright
export PLAYWRIGHT_BROWSERS_PATH

echo "Setup completed successfully"
