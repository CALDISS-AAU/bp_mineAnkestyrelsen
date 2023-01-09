#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install poppler-utils
sudo apt-get install tesseract-ocr

sudo wget https://github.com/tesseract-ocr/tessdata/raw/4.00/dan.traineddata -P /usr/share/tesseract-ocr/4.00/tessdata

pip install --upgrade pip
pip install -r requirements.txt