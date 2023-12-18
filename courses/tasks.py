from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.translation import ugettext as _
import logging
from student import models

from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


@shared_task
def send_mail_to_student(student_email, status):    
    fromEmail = settings.EMAIL_HOST_USER
    toEmail = "rohit@myfuturely.com"
    if status == "Approved":
        template_name = "courses/scholarship_emails/scholarship_approved.html"
        subject = _("Your Scholarship Approved")
        ctx = {
            "username": student_email,
        }
        html_msg = get_template(template_name).render(ctx)
        msg = EmailMessage(subject, html_msg, fromEmail, [student_email, toEmail])
        msg.content_subtype = "html"
        msg.send()
        logger.info(f"E-Mail sent Successfully for : {student_email}")
        # models.Stu_Notification.objects.create(student=student_email, title=_("Congratulations, Your scholarship has been Approved."))
        return True

    elif status == "Applied":
        template_name = "student/scholarship_applied_email.html"
        subject = _("Your Scholarship Approved")
        ctx = {
            "username": student_email,
        }
        html_msg = get_template(template_name).render(ctx)
        msg = EmailMessage(subject, html_msg, fromEmail, [student_email, toEmail])
        msg.content_subtype = "html"
        msg.send()
        # models.Stu_Notification.objects.create(student=student_email, title=_("You have successfully applied for the scholarship"))
        logger.info(f"E-Mail sent Successfully for : {student_email}")
        return True

    elif status == "Declined":
        template_name = "courses/scholarship_emails/scholarship_declined.html"
        student_email.append(toEmail)
        subject = _("Your Scholarship Declined")
        ctx = {
            "username": student_email,
        }
        html_msg = get_template(template_name).render(ctx)
        msg = EmailMessage(subject, html_msg, fromEmail, student_email)
        msg.content_subtype = "html"
        msg.send()
        # models.Stu_Notification.objects.create(student=student_email, title=_("Sorry for that, Your scholarship has been declined."))
        logger.info(f"E-Mail sent Successfully for : {student_email}")
        return True
    else:
        return False


@shared_task(bind=True)
def hello(self):
    try:
        logger.info("celery task executed!")
        return 'Done!'
    except Exception as error:
        # send email to admintrator
        logger.error(f"Error in celery task : {error}")
        return f"{error}"

@shared_task
def simple_task(): 
    logger.info("celery task executed!")
    print('I am executing a simple_task')