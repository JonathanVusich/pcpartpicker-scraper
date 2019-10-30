#!/usr/bin/env bash
python3.7 main.py --parallel=2
current_date_time="`date "+%Y-%m-%d %H:%M:%S"`";
git add .
git commit -m "Timestamp : ${current_date_time}"
git push