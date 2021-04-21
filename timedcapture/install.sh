#!/bin/bash

echo ___________________Start___________________

conda create -n micro_process python=3.6.9 -y
conda activate micro_process
pip install -r requirements.txt
apt install ffmpeg


echo ___________________Finish___________________
