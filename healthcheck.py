import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    task_count = 0
    while True:
        try:
            res = requests.get('http://remote.mediatain.com:5566/healthcheck')
            if not res.ok:
                send_mail('healthcheck down')
                break

            res = requests.get('http://remote.mediatain.com:5566/metrics')
            if not res.ok:
                send_mail('metrics down')
                break
            
            data = res.text
            new_task_count = int(float(data.split('flower_task_runtime_seconds_bucket{le="+Inf",task="tasks.load_contracts_and_schedule_captures",worker="default-worker@')[1].split('\n')[0].split(' ')[-1]))

            if new_task_count <= task_count:
                send_mail('no new task')
                break
            task_count = new_task_count

            print('sleeping')
            time.sleep(5 * 60)
        except Exception as e:
            send_mail('something crashed')
            print(e)
            break

        

def send_mail(content):
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
"""

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


if __name__ == "__main__":
    send_mail('test')
    main()
    while True:
        pass