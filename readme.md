step1: 

git clone https://github.com/supriya143d/testing.git

step2:   
follow below steps:

apk add py3-requests
python3 -c "import requests; print('OK')"
python3 -m venv venv
source venv/bin/activate
pip install requests

step3:

python send_sent_mails.py --csv recruiters.csv --drive-link "https://drive.google.com/uc?export=download&id=1JZkfPB4oiCtSWFosnHjnqVbMcXKXJhnU"
