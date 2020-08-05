# -*- coding: utf-8 -*-

import flask
import json
import smtplib
import requests
import pypinyin
from email.mime.text import MIMEText

"""
邮件报警使用比变量
"""
mail_host = "XXXX"
mail_user = "XXXX"
mail_pass = "XXXX"
sender = "XXXX"

"""
短信报警接口地址
"""
apollo_url = "XXXX"

"""
企业微信接口地址
"""
qiyeweixin_url = "XXXX"


with open('member.json', 'r', encoding='utf-8') as fp:
    configuration = json.load(fp)

def pinyin(user):
    s = ""
    for i in pypinyin.pinyin(user, style=pypinyin.NORMAL):
        s += s.join(i)
    return list(s.split(","))

def send_by_sms(data):
    if configuration["sms_switch"] == "on":
        requests.post(url=apollo_url, data=json.dumps(data))

def send_by_qiyeweixin(user, message):
    if configuration["wechat_switch"] == "on":
        headers = {"Content-Type": "application/json"}
        dict_send = {
            "service": "go.microv2.srv.WeWork",
            "endpoint": "WeWorkSRV.SendMsgBySystemApp"
        }
        dict_request = dict()
        dict_receiver = dict()
        dict_msg = dict()
        dict_receiver["user"] = user
        dict_msg["content"] = message
        dict_msg["type"] = "text"
        dict_request["receiver"] = dict_receiver
        dict_request["msg"] = dict_msg
        dict_send["request"] = dict_request
        requests.post(url=qiyeweixin_url, headers=headers, data=json.dumps(dict_send))

def send_by_mail(data):
    if configuration["mail_switch"] == "on":
        receiver = configuration["mail_receiver"]
        content = str(data["annotations"]["message"]).replace("#", "\n")
        title = str(data["annotations"]["message"])
        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = "{}".format(sender)
        message['To'] = ",".join(receiver)
        message['Subject'] = title
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receiver, message.as_string())
        smtpObj.quit()

app = flask.Flask(__name__)
@app.route('/alert', methods=['POST'])
def alert():
    data = json.loads(flask.request.data)
    new_alerts = []
    for alerts in data["alerts"]:
        if alerts["labels"]["attribute"] == "micro_service":
            alerts["labels"]["member"] = configuration["alarm_group"]["default_group"]
            user_name_pinyin = pinyin(configuration["alarm_group"]["default_group"])
            msg = str(alerts["annotations"]["message"]).replace("#", "\n")
            send_by_qiyeweixin(user_name_pinyin, msg)
            send_by_mail(alerts)
            print(alerts)
            for app_name in configuration["alarm_group"].keys():
                if alerts["labels"]["type"] == "service" and app_name in alerts["labels"]["pod"]:
                    alerts["labels"]["member"] = str(alerts["labels"]["member"] + "," +
                                                     configuration["alarm_group"][app_name])
                    user_name_pinyin = pinyin(str(configuration["alarm_group"][app_name]))
                    msg = str(alerts["annotations"]["message"]).replace("#", "\n")
                    send_by_qiyeweixin(user_name_pinyin, msg)
                    new_alerts.append(alerts)
                else:
                    new_alerts.append(alerts)
    data["alerts"] = new_alerts
    send_by_sms(data)
    return json.dumps({"code": "200"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
