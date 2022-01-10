#!/usr/bin/python3
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
import urllib.parse
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

STUID='XXXXXX'#学号
STUKEY='XXXXXX'#统一认证登录密码
MODE='monitor'#模式,分为两种 "grab"和"monitor". monitor只监控, grab监控到又空余位置时进行抢课.
#下面是qqbot推送参数
QQ='XXXXXX'
GROUP='XXXXXX'
QQAPIURL='http://XXX.XXX:XXX'

LOGIN_URL="https://passport.ustc.edu.cn/login?service=https%3A%2F%2Fjw.ustc.edu.cn%2Fucas-sso%2Flogin"
RETURN_URL="https://jw.ustc.edu.cn/ucas-sso/login"

qqmsg_send='{}/send_private_msg?user_id={}&message='.format(QQAPIURL, QQ)
qqmsg_chuo='{}/send_private_msg?user_id={}&message=[CQ:poke,qq={}]'.format(QQAPIURL, QQ, QQ)
qqmsg_at='{}/send_group_msg?group_id={}&message=[CQ:at,qq={}]'.format(QQAPIURL, GROUP, QQ)


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
        print("1 success!")
        ret = session.get("https://jw.ustc.edu.cn/")
        print("2 success!")
        ret = session.get("https://jw.ustc.edu.cn/for-std/course-select")
        url_stuid = ret.url
        pos = url_stuid.rfind('/', 0, len(url_stuid))
        STDASSOC = url_stuid[pos+1:]

        # 计算年份和学期
        time_year = time.strftime('%y', time.localtime())
        time_month = time.strftime('%m', time.localtime())
        if int(time_month) > 6:
            time_season = 1
        else:
            time_season = 0
        YEAR_SEASON = 40*int(time_year) - 639 + int(time_season)*20
        print(YEAR_SEASON)
        class_info={
            'season' : str(YEAR_SEASON),
            'stdAssoc' : STDASSOC,
            'classNum': str(CLASSNUM),
            'className': urllib.parse.quote(CLASSNAME),
            'classTeacher': urllib.parse.quote(CLASSTEACHER)
        }
        print("searching target class...\n")

        ALLCLASSINFO_URL="https://jw.ustc.edu.cn/for-std/lesson-search/semester/{season}/search/{stdAssoc}?codeLike={classNum}&courseNameZhLike={className}&teacherNameLike={classTeacher}".format(**class_info)
        
        print(ALLCLASSINFO_URL)
        ret = session.get(ALLCLASSINFO_URL)
        #print(ret.text)
        info = json.loads(ret.text)
        try:
            lessonId = info['data'][0]['id']
        except Exception as e:
            print(e)
            print("没有找到该课程，退出")
            exit()
        limitCount = info['data'][0]['limitCount']
        stdCount = info['data'][0]['stdCount']
        class_name = info['data'][0]['course']['nameZh']
        class_teacher = info['data'][0]['teacherAssignmentList'][0]['person']['nameZh']
        class_time = info['data'][0]['scheduleText']['dateTimePlacePersonText']['text']
        class_info['lessonId'] = lessonId
        print("target class: " + class_name + "\nlesson id: " + str(lessonId) + "\ncurrent selected/limited count: " + str(stdCount) + '/' + str(limitCount) + '\n')

        print("find existing selected class...")

        CLASSINFO_URL="https://jw.ustc.edu.cn/for-std/course-take-query/semester/{}/search?bizTypeAssoc=2&studentAssoc={}&courseNameZhLike={}&courseTakeStatusSetVal=1".format(int(class_info['season']), STDASSOC, urllib.parse.quote(class_name))
        ret = session.get(CLASSINFO_URL)
        if (len(json.loads(ret.text)['data']) == 0):
            GRAB_MODE = 0
            oldLessonAssoc = 0
        else:
            GRAB_MODE = 1
            oldLessonCode = json.loads(ret.text)['data'][0]['lessonCode']

            ret = session.get("https://jw.ustc.edu.cn/for-std/lesson-search/semester/{season}/search/{}?codeLike={}&courseNameZhLike=&teacherNameLike=".format(STDASSOC, oldLessonCode))

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
            'drop_respond': ADD_DROP_RESPOND
        }
        while True:
            ret = session.get(ALLCLASSINFO_URL)
            info = json.loads(ret.text)
            limitCount = info['data'][0]['limitCount']
            stdCount = info['data'][0]['stdCount']
            if(stdCount < limitCount):
                if(MODE == 'grab'):
                    print("Class not full {}/{}, grabbing...".format(stdCount, limitCount))
                    requests.get(qqmsg_send+"注意！！{}({}) 课程人数未满！现在为{}/{}人".format(class_name, class_teacher, stdCount, limitCount))
                    retry_count=5
                    retVal = False
                    while not retVal:
                        retVal = self.report(session, class_info, url_info)
                        if retVal:
                            print("Sucessfully grabbed!")
                            requests.get(qqmsg_send + "抢课成功! 课程名:{}, 老师:{}, 上课时间:{}".format(class_name, class_teacher, class_time))
                            exit(0)
                        else:
                            print("Failed, retry...")
                            retry_count = retry_count - 1
                            if(retry_count == 0):
                                continue
                else:
                    print("Class not full {}/{}, push QQmsg...".format(stdCount, limitCount))
                    requests.get(qqmsg_send+"注意！！{}({}) 课程人数未满！现在为{}/{}人".format(class_name, class_teacher, stdCount, limitCount))
                    requests.get(qqmsg_at+"\n{}({}) 课程人数未满！现在为{}/{}人".format(class_name, class_teacher, stdCount, limitCount))
            else:
                print("Class is full.")
                requests.get(qqmsg_send+"{}({}) 课程人数已满！现在为{}/{}人".format(class_name, class_teacher, stdCount, limitCount))
            time.sleep(60)
        return True
    def report(self, session, class_info, url_info):
        loginsuccess = False
        retrycount = 5
        cookies = session.cookies
        #选课post数据的headers
        headers = {
            'Content-Type':'application/json;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Referer': 'https://jw.ustc.edu.cn/for-std/course-adjustment-apply/selection-apply/apply?lessonAssoc={}&semesterAssoc={season}&bizTypeAssoc=2&studentAssoc={}'.format(class_info['lessonId'], class_info['stdAssoc'])
        }
        #激活cookie用headers
        headers2 = {
            'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Referer': 'https://jw.ustc.edu.cn/for-std/course-select/turns/{}'.format(class_info['stdAssoc'])
        }
        headers3 = {
            'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        #个性化申请表单-save
        data = {
            'applyReason': '申请',
            'applyTypeAssoc': 1,
            'bizTypeAssoc': 2,
            'newLessonAssoc': int(class_info['lessonId']),
            'retake': False,
            'scheduleGroupAssoc': None,
            'semesterAssoc': int(class_info['season']),
            'studentAssoc': int(class_info['stdAssoc']),
        }
        #个性化申请表单-preCheck
        data2 = [{
            "newLessonAssoc": int(class_info['lessonId']),
            "studentAssoc": int(class_info['stdAssoc']),
            "semesterAssoc": int(class_info['season']),
            "bizTypeAssoc": 2,
            "applyTypeAssoc": 1,
            "applyReason": "申请",
            "retake": False,
            "scheduleGroupAssoc": None
        }]
        data3 = [{
            "oldLessonAssoc": int(class_info['oldLessonAssoc']),
            "newLessonAssoc": int(class_info['lessonId']),
            "studentAssoc": int(class_info['stdAssoc']),
            "semesterAssoc": int(class_info['season']),
            "bizTypeAssoc": 2,
            "applyReason": "申请",
            "applyTypeAssoc": 5,
            "scheduleGroupAssoc": None
        }]
        data4 = {
            "studentAssoc": int(class_info['stdAssoc']),
            "semesterAssoc": int(class_info['season']),
            "bizTypeAssoc": 2,
            "applyTypeAssoc": 5,
            "checkFalseInsertApply": True,
            "lessonAndScheduleGroups":[{
                "lessonAssoc": int(class_info['lessonId']),
                "dropLessonAssoc": int(class_info['oldLessonAssoc']),
                "scheduleGroupAssoc": None
            }]
        }
        data_activate = {
            "bizTypeId": 2,
            "studentId": int(class_info['stdAssoc'])
        }
        ret = session.get("https://jw.ustc.edu.cn/static/courseselect/template/open-turns.html", cookies=session.cookies)
        
        ret = session.post("https://jw.ustc.edu.cn/ws/for-std/course-select/open-turns", data=data_activate, headers=headers2)

        ret = session.get("https://jw.ustc.edu.cn/for-std/course-select/{}/turn/461/select".format(class_info['stdAssoc']), cookies=session.cookies)
        
        if(url_info['mode'] == 0):
            ret = session.get(url_info['apply'])

            ret = session.post(url_info['change_precheck'], data=json.dumps(data2), headers=headers)

            ret = session.get(url_info['getretake'])

            ret = session.post(url_info['save'], data=json.dumps(data), headers=headers)

            if(ret.text == 'null'):
                return True
            else:
                return False
        else:
            ret = session.get(url_info['change_apply'])

            ret = session.post(url_info['precheck'], data=json.dumps(data3), headers=headers)

            ret = session.post(url_info['drop_request'], data=json.dumps(data4), headers=headers)

            print(ret)

            requestId = ret.text

            data_respond = {
                'studentId': class_info['stdAssoc'],
                'requestId': requestId
            }
            ret = session.post(url_info['drop_respond'], data=json.dumps(data_respond), headers=headers3)

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
        #print(ret.cookies.get_dict)
        #print(s.cookies.get_dict())
        return s, ret


if __name__ == "__main__":

#参数说明:
#   第一个参数为模式选择, grab为抢课模式, monitor为监控模式
#   第二个参数为两次查询间隔时间，单位为秒（默认为60）
#   第三个参数为课程中文名称
#   第四个参数为课程授课老师
#   第五个参数为课程号, 若前两项已经可以唯一确定则可以为空(如果不唯一的话, 不要为空!)
    parser = argparse.ArgumentParser(description='中国科学技术大学抢课脚本.')
    parser.add_argument('-m', '--mode', help='模式选择, grab为抢课模式, monitor为监控模式, 默认为监控模式.', type=str, default='monitor')
    parser.add_argument('-t', '--time', help='两次查询间隔时间，单位为秒 (默认为60).', type=int, default=60)
    parser.add_argument('name', help='选中课程的中文名称', type=str)
    parser.add_argument('teacher', help='选中课程的授课老师', type=str)
    parser.add_argument('classid', help='课程号, 若前两项已经可以唯一确定则可以为空(如果不唯一的话, 不要为空!)', type=str, default='', nargs='?')
    args = parser.parse_args()
    
    MODE = args.mode
    TIME_INTERVAL = args.time
    CLASSNAME = args.name
    CLASSTEACHER = args.teacher
    CLASSNUM = args.classid
    
    autorepoter = Report()
    ret = autorepoter.link_generate()
