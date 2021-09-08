# encoding=utf8
import requests
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
APPLY_URL = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/apply?lessonAssoc=135585&semesterAssoc=221&bizTypeAssoc=2&studentAssoc=109184"
PRECHECK_URL="https://jw.ustc.edu.cn/for-std/course-adjustment-apply/preCheck"
GETRETAKE_URL="https://jw.ustc.edu.cn/for-std/course-adjustment-apply/getRetake?lessonIds=135585&studentId=109184&bizTypeId=2"
SAVE_URL="https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/save"
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

        session, login_ret = self.login()
        cookies = session.cookies
        headers = {
            'authority': 'jw.ustc.edu.cn',
            'origin': 'https://jw.ustc.edu.cn',
            'upgrade-insecure-requests': '1',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'referer': 'https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/apply?lessonAssoc=135585&semesterAssoc=221&bizTypeAssoc=2&studentAssoc=109184',
            'accept-language': 'zh-CN,zh;q=0.9',
            'Connection': 'close',
            'cookie': cookies,
        }
        #选课post数据的headers
        headers = {
            'Content-Type':'application/json;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Referer': 'https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/apply?lessonAssoc=135585&semesterAssoc=221&bizTypeAssoc=2&studentAssoc=109184'
        }
        #激活cookie用headers
        headers2 = {
            'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Referer': 'https://jw.ustc.edu.cn/for-std/course-select/turns/109184'
        }
        #个性化申请表单-save
        data = {
            'applyReason': '申请',
            'applyTypeAssoc': 1,
            'bizTypeAssoc': 2,
            'newLessonAssoc': 135585,
            'retake': False,
            'scheduleGroupAssoc': None,
            'semesterAssoc': 221,
            'studentAssoc': 109184,
        }
        #个性化申请表单-preCheck
        data2 = [{
            "newLessonAssoc": 135585,
            "studentAssoc": 109184,
            "semesterAssoc": 221,
            "bizTypeAssoc": 2,
            "applyTypeAssoc": 1,
            "applyReason": "申请",
            "retake": False,
            "scheduleGroupAssoc": None
        }]
        ret = session.get("https://jw.ustc.edu.cn/webroot/decision/login/cross/domain?fine_username=PB19000244&fine_password=682ef8d16f48228ea2e938c3f245a317&validity=-1")
        print(ret.text)
        ret = session.get("https://jw.ustc.edu.cn/")
        print(ret.cookies)
        ret = session.get("https://jw.ustc.edu.cn/for-std/course-select")
        print(ret.url)
        ret = session.get("https://jw.ustc.edu.cn/static/courseselect/template/open-turns.html", cookies=session.cookies)
        data_activate = {
            "bizTypeId": 2,
            "studentId": 109184
        }
        ret = session.post("https://jw.ustc.edu.cn/ws/for-std/course-select/open-turns", data=data_activate, headers=headers2)
        print(session.cookies.get_dict())
        ret = session.get("https://jw.ustc.edu.cn/for-std/course-select/109184/turn/461/select", cookies=session.cookies)
        print(ret.cookies)
        ret = session.get("https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/apply?lessonAssoc=135585&semesterAssoc=221&bizTypeAssoc=2&studentAssoc=109184")
        #getform0 = session.get(APPLY_URL)
        #print(getform0.text)
        print(session.cookies.get_dict())
        getform1 = session.post(PRECHECK_URL, data=json.dumps(data2), headers=headers)
        print(getform1)
        print(getform1.text)
        print(getform1.url)
        getform2 = session.get(GETRETAKE_URL)
        print(getform2.text)
        getform3 = session.post(SAVE_URL, data=json.dumps(data), headers=headers)
        print(getform3.text)
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
        ret = s.post(LOGIN_URL, data=data)
        print("login...")
        print(ret.cookies.get_dict)
        print(s.cookies.get_dict())
        return s, ret


if __name__ == "__main__":
    autorepoter = Report()
    ret = autorepoter.report()

