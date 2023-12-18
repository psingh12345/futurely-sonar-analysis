from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import message, send_mail, BadHeaderError, EmailMessage
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string, get_template
from datetime import datetime
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import make_aware
import pytz, logging
from payment.models import *

from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

logger_console_adapter = logging.getLogger('console')
logger_console = CustomLoggerAdapter(logger_console_adapter, {})

def send_email_message(request, user, subject, template_nam):
    """
    this  function use for send mail and take  four argument request, user, subject,
    template then function is create a message then sent email.
    """
    try:
        #email_template_name = "userauth/email_content.html"
        ctx = {
            "email": user.email,
            "domain": request.get_host(),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "token": default_token_generator.make_token(user),
            "protocol": 'https',
            "lang_code": request.LANGUAGE_CODE,
        }
        html_msg = get_template(template_nam).render(ctx)
        # email=render_to_string(email_template_name,c)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [user.email])
        msg.content_subtype = "html"
        msg.send()
        logger.info(f"E-Mail sent Successfully for : {user.email}")
        return True
    except Exception as ex:
        logger.error(f"Error in send-email-message function {ex} for : {user.email}")
        return False

def check_discount_code_validation(request, coupon_code):
    ctype = request.session.get('ctype', None)
    qs = None
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt_now = local_tz.localize(datetime.now())
    if ctype and ctype == 'future_lab':
        qs = Coupon.objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code))
        #qs = Coupon.futurelab_company_objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code), Q(coupon_type='FutureLab'))
    elif ctype and ctype == 'company':
        qs = Coupon.objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code))
        #qs = Coupon.futurelab_company_objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code), Q(coupon_type='Organization'))
    else:
        qs = Coupon.objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code))
    if qs and len(qs) > 0:
        return True
    else:
        return False