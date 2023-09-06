#!/usr/bin/python3
# encoding=utf8
import requests
import datetime
import time
import argparse
import json
import re
import pytz
import io
import os
from bs4 import BeautifulSoup
import PIL
import pytesseract
import urllib.parse
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

STUID='PB20051107'#学号
STUKEY=''#统一认证登录密码
MODE='grab'#模式,分为两种 "grab"和"monitor". monitor只监控, grab监控到又空余位置时进行抢课.


sckey = 'SCT218403TWUT6Xc89EE91yYPlGWyLsWO2'

LOGIN_URL="https://passport.ustc.edu.cn/login?service=https%3A%2F%2Fjw.ustc.edu.cn%2Fucas-sso%2Flogin"
RETURN_URL="https://jw.ustc.edu.cn/ucas-sso/login"



class Report(object):
    def __init__(self):
        self.stuid = STUID
        self.password = STUKEY
    def link_generate(self):
        session, login_ret = self.login()

        back = session.get("https://jw.ustc.edu.cn/")
        backurl = back.url
        if(backurl == 'https://jw.ustc.edu.cn/home'):
            print("login success!")
        else:
            print("login failed!")

        hl = hashlib.md5()
        STUID_MD5 = hl.update(STUID.encode(encoding='utf-8'))
        ret = session.get("https://jw.ustc.edu.cn/webroot/decision/login/cross/domain?fine_username={}&fine_password={}&validity=-1".format(STUID, hl.hexdigest()))
        print("first get success!")
        ret = session.get("https://jw.ustc.edu.cn/")
        print("second get success!")
        ret = session.get("https://jw.ustc.edu.cn/for-std/course-select")
        
        url_stuid = ret.url
        pos = url_stuid.rfind('/', 0, len(url_stuid))
        STDASSOC = url_stuid[pos+1:]

        data_enterinto = {
            "bizTypeId": 2,
            "studentId": STDASSOC,
        }

          
        semester_choice = list()
        semester_number = list()
        ret = session.get("https://jw.ustc.edu.cn/for-std/lesson-search/index/{}".format(STDASSOC))
        data = ret.text
        soup = BeautifulSoup(data, 'html.parser')
        for semester in soup.find("select", {"class": "semester"}):
            if(semester.string != '\n'):
                semester_choice.append(semester.string)
                semester_number.append(semester['value'])
        #choice_num = len(semester_choice)
        print("[id]\t--\tdetails")
        for i in range(0, 5):
            print("[{}]\t--\t{}".format(semester_number[i], semester_choice[i]))
        semester_user_choice = '322'#input("请选择你想抢课的课程所在的学期，输入最前面的序号：\n")
        
        class_info = {
            'season' : str(semester_user_choice),
            'stdAssoc' : STDASSOC,
            'classNum': str(CLASSNUM),
            'className': urllib.parse.quote(CLASSNAME),
            'classTeacher': urllib.parse.quote(CLASSTEACHER)
        }
        print("searching target class...")

        ALLCLASSINFO_URL="https://jw.ustc.edu.cn/for-std/lesson-search/semester/{season}/search/{stdAssoc}?codeLike={classNum}&courseNameZhLike={className}&teacherNameLike={classTeacher}".format(**class_info)

        ret = session.get(ALLCLASSINFO_URL)
        info = json.loads(ret.text)
        try:
            lessonId = info['data'][0]['id']
        except Exception as e:
            print(e)
            print("没有找到该课程，退出")
            exit()
        limitCount = info['data'][0]['limitCount']
        gxhlimitCount = info['data'][0]['courseApplyLimit']
        stdCount = info['data'][0]['stdCount']
        class_name = info['data'][0]['course']['nameZh']
        class_teacher = info['data'][0]['teacherAssignmentList'][0]['person']['nameZh']
        class_time = info['data'][0]['scheduleText']['dateTimePlacePersonText']['text']
        class_info['lessonId'] = lessonId
        
        print("--------------------------\ntarget class: " + class_name + "\nlesson id: " + str(lessonId) + "\ncurrent selected/limited count: " + str(stdCount) + '/' + str(limitCount) + '\n--------------------------')

        print("find existing selected class...")

        CLASSINFO_URL="https://jw.ustc.edu.cn/for-std/course-take-query/semester/{}/search?bizTypeAssoc=2&studentAssoc={}&courseNameZhLike={}&courseTakeStatusSetVal=1".format(int(class_info['season']), STDASSOC, urllib.parse.quote(class_name))
        ret = session.get(CLASSINFO_URL)
        if (len(json.loads(ret.text)['data']) == 0):
            GRAB_MODE = 0
            oldLessonAssoc = 0
        else:
            GRAB_MODE = 1
            oldLessonCode = json.loads(ret.text)['data'][0]['lessonCode']

            ret = session.get("https://jw.ustc.edu.cn/for-std/lesson-search/semester/{}/search/{}?codeLike={}&courseNameZhLike=&teacherNameLike=".format(int(class_info['season']), STDASSOC, oldLessonCode))

            oldLessonAssoc = json.loads(ret.text)['data'][0]['id']

        class_info['oldLessonAssoc'] = oldLessonAssoc

        APPLY_URL = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/apply?lessonAssoc={lessonId}&semesterAssoc={season}&bizTypeAssoc=2&studentAssoc={stdAssoc}".format(**class_info)
        PRECHECK_URL = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/preCheck"
        GETRETAKE_URL = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/getRetake?lessonIds={lessonId}&studentId={stdAssoc}&bizTypeId=2".format(**class_info)
        SAVE_URL = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/save"

        CHANGE_APPLY_URL = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/change-class-apply/change-class?lessonAssoc={lessonId}&oldLessonId={oldLessonAssoc}&bizTypeAssoc=2&semesterAssoc={season}&studentAssoc={stdAssoc}&applyTypeAssoc=5".format(**class_info)
        CHANGE_PRECHECK_URL = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/preCheck"
        ADD_DROP_REQUEST = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/add-drop-request"
        ADD_DROP_RESPOND = "https://jw.ustc.edu.cn/for-std/course-adjustment-apply/add-drop-response"
        ADD_REQUEST = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-request"
        ADDABLE_URL = "https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons"
        ADD_DROP_RESPONCE = "https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response"
        url_info = {
            'mode': GRAB_MODE,
            'all': ALLCLASSINFO_URL,
            'apply': APPLY_URL,
            'precheck': PRECHECK_URL,
            'getretake': GETRETAKE_URL,
            'save': SAVE_URL,
            'change_apply': CHANGE_APPLY_URL,
            'change_precheck': CHANGE_PRECHECK_URL,
            'drop_request': ADD_DROP_REQUEST,
            'drop_respond': ADD_DROP_RESPOND,
            'add-request':ADD_REQUEST,
            'addable':ADDABLE_URL,
            'add-drop-response':ADD_DROP_RESPONCE
        }
        counting = 0
        while True:
            ret = session.get(ALLCLASSINFO_URL)
            info = json.loads(ret.text)
            limitCount = info['data'][0]['limitCount']
            stdCount = info['data'][0]['stdCount']
            classtype_bool = stdCount >= limitCount and stdCount < gxhlimitCount
            if (CLASSTYPE == 'public'):
                classtype_bool = False
            if(stdCount < limitCount or classtype_bool):
                if(MODE == 'grab'):
                    print("Class not full {}/{}/{}, grabbing...".format(stdCount, limitCount, gxhlimitCount))
                    #requests.get(qqmsg_send+"注意！！{}({}) 课程人数未满！现在为{}/{}/{}人".format(class_name, class_teacher, stdCount, limitCount, gxhlimitCount))
                    url = f'https://sc.ftqq.com/{sckey}.send?text=课程人数未满&desp=课程人数未满'
                    requests.get(url)
                    retry_count=5
                    retVal = False
                    while not retVal:
                        retVal = self.report(session, class_info, url_info)
                        if retVal:
                            #requests.get(qqmsg_send+"抢课成功! 课程名:{}, 老师:{}".format(class_name, class_teacher))
                            url = f'https://sc.ftqq.com/{sckey}.send?text=抢课成功&desp=抢课成功'
                            requests.get(url)
                            #print(qqmsg_send+"抢课成功! 课程名:{}, 老师:{}".format(class_name, class_teacher))
                            print("Sucessfully grabbed!")
                            time.sleep(2)
                            exit(0)
                        else:
                            print("Failed, retry...")
                            url = f'https://sc.ftqq.com/{sckey}.send?text=抢课失败&desp=抢课失败'
                            requests.get(url)
                            retry_count = retry_count - 1
                            if(retry_count == 0):
                                continue
                else:
                    print("Class not full {}/{}/{}, push QQmsg...".format(stdCount, limitCount, gxhlimitCount))
                    url = f'https://sc.ftqq.com/{sckey}.send?text=课程人数未满&desp=课程人数未满'
                    requests.get(url)
                    #requests.get(qqmsg_send+"注意！！{}({}) 课程人数未满！现在为{}/{}/{}人".format(class_name, class_teacher, stdCount, limitCount, gxhlimitCount))
                    #requests.get(qqmsg_at+"\n{}({}) 课程人数未满！现在为{}/{}人".format(class_name, class_teacher, stdCount, limitCount))
            else:
                print("Class is full.")
                counting = counting + 1
                if(counting == 60):
                    counting = 1
                    print("{}({}) 课程人数已满！现在为{}/{}/{}人".format(class_name, class_teacher, stdCount, limitCount, gxhlimitCount))
                    # url = f'https://sc.ftqq.com/{sckey}.send?text=课程人数已满&desp=课程人数已满'
                    # requests.get(url)
                    #requests.get(qqmsg_send+"{}({}) 课程人数已满！现在为{}/{}/{}人".format(class_name, class_teacher, stdCount, limitCount, gxhlimitCount))
            try:
                time.sleep(TIME_INTERVAL)
            except Exception as e:
                print(e)
                time.sleep(60)

    def report(self, session, class_info, url_info):
        loginsuccess = False
        retrycount = 5
        cookies = session.cookies
        stdAssoc_ = int(class_info['stdAssoc'])
        headers0 = {
            "authority": "jw.ustc.edu.cn",
            "method": "POST",
            "path": "/ws/for-std/course-select/addable-lessons",
            "scheme": "https",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Length": "98",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://jw.ustc.edu.cn",
            "Referer": f'https://jw.ustc.edu.cn/for-std/course-select/{stdAssoc_}/turns/781/select',
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            "X-Requested-With": "XMLHttpRequest"
        }
        
        headers1 = {
            "authority": "jw.ustc.edu.cn",
            "method": "POST",
            "path": "/ws/for-std/course-select/add-request",
            "scheme": "https",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Length": "98",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://jw.ustc.edu.cn",
            "Referer": f'https://jw.ustc.edu.cn/for-std/course-select/{stdAssoc_}turns/781/select',
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            "X-Requested-With": "XMLHttpRequest"
        }
        headers2 = {
            "authority": "jw.ustc.edu.cn",
            "method": "POST",
            "path": "/ws/for-std/course-select/add-drop-response",
            "scheme": "https",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Length": "98",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://jw.ustc.edu.cn",
            "Referer": f'https://jw.ustc.edu.cn/for-std/course-select/{stdAssoc_}turns/781/select',
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            "X-Requested-With": "XMLHttpRequest"
        }
        data0 = {
            'studentId': stdAssoc_,
            'turnId': 781
        }
        
        data1 = {
            "studentAssoc": int(class_info['stdAssoc']),
            "lessonAssoc": int(class_info['lessonId']),
            "courseSelectTurnAssoc":781,
            "scheduleGroupAssoc": None,
            "virtualCost": 0
        }
        
        ret = session.post("https://jw.ustc.edu.cn/ws/for-std/course-select/addable-lessons", headers=headers0, data=data0)#url_info['addable-lessons']
        ret = session.post("https://jw.ustc.edu.cn/ws/for-std/course-select/add-request", headers=headers1, data=data1)#url_info['add-request']
        data0 = {
            'studentId': stdAssoc_,
            'requestId': ret.text
        }
        ret = session.post("https://jw.ustc.edu.cn/ws/for-std/course-select/add-drop-response", headers=headers2, data=data0)
        print(ret.text)
        if(ret.json()['success'] == True):
            return True
        else :
            print(ret.text)
            return False


    def login(self):
        retries = Retry(total=5,
                        backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        s = requests.Session()
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67"

        r = s.get(LOGIN_URL, params={"service": RETURN_URL})
        # x = re.search(r"""<input.*?name="CAS_LT".*?>""", r.text).group(0)
        # cas_lt = re.search(r'value="(LT-\w*)"', x).group(1)
        cas_lt = re.search(r'(LT-\w*)', r.text).group()
        print(cas_lt)
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
        print(data)
        ret = s.post(LOGIN_URL, data=data)
        print("login...")
        #print(ret.cookies.get_dict)
        #print(s.cookies.get_dict())
        return s, ret


if __name__ == "__main__":
    
    MODE = 'grab'#args.mode
    TIME_INTERVAL = 3#args.time
    CLASSNAME = '网络算法学'#args.name
    CLASSTEACHER = '华蓓'#args.teacher
    CLASSNUM = '011185.01'#args.classid
    CLASSTYPE = 'public'#args.classtype    
    
    autorepoter = Report()
    ret = autorepoter.link_generate()
