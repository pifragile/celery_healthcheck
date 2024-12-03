import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class HealthCheckException(Exception):
    pass

def sleep_mins(t):
    print(f'sleeping {t} minutes')
    time.sleep(t * 60)

def main():
    task_count = 0
    send_mail('starting healthcheck task...')
    crashed = False
    while True:
        try:
            try:
                res = requests.get('http://remote.mediatain.com:5566/healthcheck')
                res.raise_for_status()
                res = requests.get('http://remote.mediatain.com:5566/metrics')
                res.raise_for_status()
            except:
                raise HealthCheckException('healthcheck/metrics down')
            
            data = res.text
            new_task_count = int(float(data.split('flower_task_runtime_seconds_bucket{le="+Inf",task="tasks.load_contracts_and_schedule_captures",worker="scheduler-worker@')[1].split('\n')[0].split(' ')[-1]))

            if new_task_count <= task_count:
                raise HealthCheckException('no new task')
            task_count = new_task_count

        except Exception as e:
            if not crashed:
                send_mail('healthcheck failed', str(e))
            print(e)
            crashed = True
            sleep_mins(5)
            continue

        if crashed:
            send_mail('healthcheck recovered')
            crashed = False

        sleep_mins(5)

        

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