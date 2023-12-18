from django.shortcuts import HttpResponse
from celery import shared_task
from django.core.mail import send_mail
import logging
from lib.helper import create_custom_event_for_celery_task


logger = logging.getLogger('watchtower')
logger_console = logging.getLogger('console')


@shared_task(bind=True)
def test_function(self, *args, **kwargs):
    # print(self)
    print(args)
    print(kwargs)
    for i in range(5):
        print(i)
    return "Done"


@shared_task(bind=True)
def send_email_task(self, subject, message, fromEmail, toEmail, id, ip_address, user_agent, influencer, page_url, current_page, email, custom_user_session_id):
    try:
        send_mail(subject, message, fromEmail, [toEmail])
        create_custom_event_for_celery_task(id, ip_address, user_agent, influencer, page_url, custom_user_session_id, event_id=16, meta_data={
            'page': current_page, 'email': email, 'subject': subject, 'msg': message})
        logger.info(
            f"Celery task - Lets talk query successfully submitted by : {fromEmail}")
    except Exception as e:
        create_custom_event_for_celery_task(id, ip_address, user_agent, influencer, page_url, custom_user_session_id, event_id=17, meta_data={
            'page': current_page, 'email': email, 'subject': subject, 'msg': message})
        logger.error(
            f"Celery task - Error to submit lets talk query, and username is : {fromEmail}")
