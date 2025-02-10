import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# http://remote.mediatain.com:5566/api/tasks?queue=scheduler&limit=1
# http://remote.mediatain.com:5566/api/queues/length
# use basic auth
# signal success: https://hc-ping.com/d4e3366c-9a3d-44d4-82aa-5b85aa49e1ac
# signal failure
# https://hc-ping.com/d4e3366c-9a3d-44d4-82aa-5b85aa49e1ac/ERROR_CODE
class HealthCheckException(Exception):
    pass

def sleep_mins(t):
    print(f'sleeping {t} minutes')
    time.sleep(t * 60)

def main():
    last_task_id = None
    crashed = False
    auth = (os.environ.get("FLOWER_USER"), os.environ.get("FLOWER_PASS"))
    while True:
        try:
            try:
                res = requests.get('http://remote.mediatain.com:5566/healthcheck')
                res.raise_for_status()
                tasks = requests.get('http://remote.mediatain.com:5566/api/tasks?queue=scheduler&limit=1', auth=auth)
                tasks.raise_for_status()
                queues = requests.get('http://remote.mediatain.com:5566/api/queues/length', auth=auth)
                queues.raise_for_status()
            except:
                raise HealthCheckException('1')
            
            retrieved_task_ids = list(tasks.json().keys())
            if len(retrieved_task_ids) == 0 or retrieved_task_ids[0] == last_task_id:
                raise HealthCheckException('2')
            last_task_id = retrieved_task_ids[0]


            active_queues = queues.json()['active_queues']
            for q in active_queues:
                if q['messages'] > 100:
                        raise HealthCheckException('3')

            requests.get('https://hc-ping.com/d4e3366c-9a3d-44d4-82aa-5b85aa49e1ac')
        except Exception as e:
            if not crashed:
                requests.get(f'https://hc-ping.com/d4e3366c-9a3d-44d4-82aa-5b85aa49e1ac/{str(e)}')
            print(e)
            crashed = True
            sleep_mins(5)
            continue

        if crashed:
            requests.get('https://hc-ping.com/d4e3366c-9a3d-44d4-82aa-5b85aa49e1ac')
            crashed = False

        sleep_mins(1)

        

def send_mail(content, detail=''):
    import smtplib, ssl
    port = 587  # For SSL
    smtp_server = os.environ.get("SMTP_SERVER")
    sender_email = os.environ.get("FROM_EMAIL")
    receiver_email = os.environ.get("TO_EMAIL")
    password = os.environ.get('EMAIL_PASS')
    message = f"""From: Celery Alert <{sender_email}>
To: Receiver <{receiver_email}>
MIME-Version: 1.0
Content-type: text/html
Subject: Celery Alert!

<h1>{content}</h1>
<p>{detail}</p>
"""

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


if __name__ == "__main__":
    main()