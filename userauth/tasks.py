from celery import shared_task
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import  get_template
from django.conf import settings
import logging
from django.core.mail import EmailMessage
# from django.utils.translation import ugettext as _
# import logging, json, requests, traceback
from django.contrib.auth import get_user_model
PERSON = get_user_model()
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


@shared_task(bind = True)
def test_func_task(self):
    # print(self[0])
    # print(self[1])
    # print(self.hubspotutk)
    print("It's working for userauth application!")
    return "DONE!"

# @shared_task(name="submit_hubspot_for_login", bind=True)
# def submit_hubspot_for_login(email, hubspotutk):
#     hubspot_user_tracking_id = hubspotutk
#     logger.info("Submitting hubspot for email %s, hubspot tracking id %s", email, hubspot_user_tracking_id)
#     hubspot_portal_id = "20116637"
#     hubspot_form_id = "893db2db-bf2e-4d76-b3bd-ebba0910b3da"
#     url = "https://api.hsforms.com/submissions/v3/integration/submit/{}/{}".format(hubspot_portal_id, hubspot_form_id)
#     headers = {}
#     headers['Content-Type'] = 'application/json'
#     data = json.dumps({
#         'fields': [
#             {
#                 'name': 'email',
#                 'value': email
#             },
#         ],
#         'cookies': {
#             'hutk': hubspot_user_tracking_id
#         }
#     })
#     r = requests.post(data=data, url=url, headers=headers)
#     logger.info("Submitted hubspot for email %s, hubspot tracking id %s with status code %s", email, hubspot_user_tracking_id, r.status_code)
#     result = {"status": "SUCCESS"} #"Hubspot properties updated for the Login!"
#     return "SUCCESS"
#     # except Exception as e:
#     #     logger.error("Error in submitting hubspot form for email %s, exception %s", email, str(e))
#     #     logger.error(traceback.print_exc())
#     #     result = {"status": "FAILED"}
#     #     return "FAILED"


@shared_task(bind=True)
def send_email_message_task(self,email,domain,user_id,subject,language_code,template_name):
    try:
        user = PERSON.objects.get(pk=user_id)
        ctx = {
            "email": email,
            "domain": domain,
            'uid': urlsafe_base64_encode(force_bytes(user_id)),
            "user": user,
            "token": default_token_generator.make_token(user),
            "protocol": 'https',
            "lang_code": language_code,
        }
        html_msg = get_template(template_name).render(ctx)
        # email=render_to_string(email_template_name,c)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [user.email])
        msg.content_subtype = "html"
        msg.send()
        logger.info(f" send_email_message_task Mail successfully sent  to : {email}")
    except Exception as ex:
        logger.error(f"Error in send_email_message_task function {ex} for : {email}")
