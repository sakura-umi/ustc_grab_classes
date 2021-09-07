# encoding=utf8
import requests
import json
import time
import datetime
import pytz
import re
import sys
import argparse
import json
import io
import os
from bs4 import BeautifulSoup
import PIL
import pytesseract
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

STUID=XXXXXX
STUKEY=XXXXXX


LOGIN_URL="https://passport.ustc.edu.cn/login?service=https%3A%2F%2Fjw.ustc.edu.cn%2Fucas-sso%2Flogin"
RETURN_URL="https://jw.ustc.edu.cn/ucas-sso/login"
CLASSINFO_URL="https://jw.ustc.edu.cn/for-std/course-take-query/semester/221/search?bizTypeAssoc=2&studentAssoc=109184&courseNameZhLike=%E7%BC%96%E8%AF%91%E5%8E%9F%E7%90%86%E5%92%8C%E6%8A%80%E6%9C%AF&courseTakeStatusSetVal=1&_=1630905472080"
url_send = "http://qqbot.srpr.cc/send_private_msg?user_id=594547763&message="
url_send2 = "http://qq.srpr.cc:50080/send_private_msg?user_id=594547763&message="
url_chuo = "http://qqbot.srpr.cc/send_private_msg?user_id=594547763&message=[CQ:poke,qq=594547763]"
url_chuo2 = "http://qq.srpr.cc:50080/send_private_msg?user_id=594547763&message=[CQ:poke,qq=594547763]"

class Report(object):
    def __init__(self):
        self.stuid = STUID
        self.password = STUKEY

    def report(self):
        loginsuccess = False
        retrycount = 5
        session = self.login()
        cookies = session.cookies

        while True:
            getform = session.get(CLASSINFO_URL)
            retrycount = retrycount - 1
            data = getform.text
            info=json.loads(data)
            stuCount = info.get('data')[0].get('stdCount')

            if(stuCount != 141):
                message = "已选中人数发生变化！现在为"+str(stuCount)+"人！"
                print(message)
                try:
                    session.get(url_send2 + message)
                    session.get(url_chuo2 + message)
                except Exception as e:
                    print("\nerror.\n")
                    pass
                print('completed.\n')
            else:
                message = "已选中人数没有变化. 现在为"+str(stuCount)+"人."
                print(message)
                try:
                    session.get(url_send2 + message)
                except Exception as e:
                    print("\nerror\n")
                    pass
                print('completed\n')
            time.sleep(100)
        return True
    def login(self):
        retries = Retry(total=5,
                        backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        s = requests.Session()
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67"
        r = s.get(LOGIN_URL, params={"service": RETURN_URL})
        x = re.search(r"""<input.*?name="CAS_LT".*?>""", r.text).group(0)
        cas_lt = re.search(r'value="(LT-\w*)"', x).group(1)
        CAS_CAPTCHA_URL = "https://passport.ustc.edu.cn/validatecode.jsp?type=login"        
        r = s.get(CAS_CAPTCHA_URL)
        img = PIL.Image.open(io.BytesIO(r.content))
        pix = img.load()
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                r, g, b = pix[i, j]
                if g >= 40 and r < 80:
                    pix[i, j] = (0, 0, 0)
                else:
                    pix[i, j] = (255, 255, 255)
        lt_code = pytesseract.image_to_string(img).strip()
        data = {
            'model': 'uplogin.jsp',
            'service': 'https://jw.ustc.edu.cn/ucas-sso/login',
            'username': STUID,
            'password': STUKEY,
            'warn': '',
            'showCode': '1',
            'button': '',
            'CAS_LT': cas_lt,
            'LT': lt_code
        }
        s.post(LOGIN_URL, data=data)
        print("login...")
        return s


if __name__ == "__main__":
    autorepoter = Report()
    ret = autorepoter.report()

