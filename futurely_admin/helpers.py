import requests, logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

def send_push_notification(topic, body, title):
    response = None
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        data = {
                "to" : f"/topics/{topic}",
                "notification" : {
                    "body": body,
                    "title":title,
                }
            }
        header ={
            "Authorization":"key=AAAA53xVyrs:APA91bE4WFgT0SDSpJljU-xJBS_mOjf1MaBxu7vjA0B7FC8q3QKl7REWVU8NhY15ItVtl1iJy9GMoKMtGgEmf0_6gzZxwCYr3tv4J9yqJcDtYqfrm0b1uTB6yzgA7WCdgdQgO_cjedRL",
        }
        response = requests.post(url, headers=header, json=data)
        logger.info(f"Push notification sent successfully for topic : {topic}")
        return response
    except Exception as Err:
        logger.error(f"Error {Err} in send push notification for topic : {topic}")
    return response

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

    elif status == "Declined":
        template_name = "courses/scholarship_emails/scholarship_declined.html"
        subject = _("Your Scholarship Declined")
        for stu_email in student_email:
            ctx = {
                "username": stu_email,
            }
            html_msg = get_template(template_name).render(ctx)
            msg = EmailMessage(subject, html_msg, fromEmail, [stu_email])
            msg.content_subtype = "html"
            msg.send()
            # models.Stu_Notification.objects.create(student=student_email, title=_("Sorry for that, Your scholarship has been declined."))
            logger.info(f"E-Mail sent Successfully for : {stu_email}")
        return True
    else:
        return False