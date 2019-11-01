#!/usr/bin/env bash

set -e

cd /home/jonathan/repos/pcpartpicker-scraper
venv/bin/python main.py --parallel=2
venv/bin/python -m pip install --upgrade pcpartpicker
venv/bin/python -m pytest
current_date_time="`date "+%Y-%m-%d %H:%M:%S"`";
git add .
git commit -m "Timestamp : ${current_date_time}"
git push