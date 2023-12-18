from celery import shared_task
import logging
from django.core.mail import send_mail
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


@shared_task(bind=True)
def send_email_after_submitting_contact_form(self,email):
    logger.info(f"Sending email to: {email}")
    subject = 'Contact Us Request'
    message = f'A contact us request has been submitted with the email: {email}'
    from_email = 'noreply@example.com'
    recipient_list = ['rohitkbti007@gmail.com']
    try:
        send_mail(subject, message, from_email, recipient_list)
        logger.info(f"Email sent successfully to: {recipient_list}. at send_email_after_submitting_contact_form ")
    except Exception as e:
        logger.error(f"Failed to send email Error: {str(e)} at send_email_after_submitting_contact_form")
