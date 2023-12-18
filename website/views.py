import re
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView
import pytz
from django.conf import settings
import datetime
from lib.helper import create_custom_event
from django.core.mail import message, send_mail

from courses import models
from .models import Webinars, MentorsInfo, Testimonials, Files , ParentInfo, CookiesSelectedData
from .models import Query, DiamnodQuery
from userauth.models import Company, CompanyWithSchoolDetail

from django.contrib.auth import get_user_model
from django.db.models import Q
import logging
from userauth import models as userauth_models
from payment import models as payment_models
import os
from student import models as student_models
from django.views.decorators.http import require_GET
# from courses.tasks import hello, simple_task
from courses.tasks import hello, simple_task
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from .tasks import test_function, send_email_task
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from lib.schedule_celery_tasks import schedule_hubspot_update
from .models import FaqModel
from courses.models import Cohort
from .forms import ParentInfoForm
from lib.hubspot_contact_sns import create_update_contact_hubspot
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

logger_console_adapter = logging.getLogger('console')
logger_console = CustomLoggerAdapter(logger_console_adapter, {})


PERSON = get_user_model()

class FaqRecord(TemplateView):
    template_name = 'faq/index.html'
    model = FaqModel
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locale = self.request.LANGUAGE_CODE
        context['faqs'] = FaqModel.objects.filter(local=locale)
        context['test'] = 'hello world'
        return context 
    
    def faq(request):
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        clarity_token = request.session.get('clarity_token', '')
        logger.info(f"FAQ policy is called by session id : {custom_user_session_id}")
        # create_custom_event(request, 27, custom_user_session_id)
        locale = request.LANGUAGE_CODE
        if locale == "it":
            faqs = FaqModel.objects.filter(locale=locale).order_by("sno").all()
            faqs = { 'faqs' : faqs }
            create_custom_event(request, meta_data={'clarity_token':clarity_token,'custom_user_session_id':custom_user_session_id})
            return render(request, "faq/index.html", faqs)
        else:
            return HttpResponseRedirect(reverse("index"))


class LandingPageView(TemplateView):
    template_name = "website/index.html"

    def get(self, request):
        # create the test task
        # schedule, created = CrontabSchedule.objects.get_or_create(hour = 1, minute = 5)
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
        clarity_token = self.request.session.get('clarity_token', '')
        user_agent = request.META.get('HTTP_USER_AGENT',None)
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        # print(timezone.localtime(date_now))
        # print(get_current_timezone())
        dt_new = date_now + datetime.timedelta(seconds=30)
        # dt_new_one = date_now + datetime.timedelta(seconds=60)
        # schedule_hubspot_update(request)
        # test_function.delay()
        # hello.delay()
        # print(dt_new)
        # hello.apply_async(eta=dt_new)
        # simple_task.apply_async(eta=dt_new_one)
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        # local_tz = pytz.timezone(settings.TIME_ZONE)
        # date_now = local_tz.localize(datetime.datetime.now())
        context = {}
        stu_testimonials = Testimonials.published.lang_code(
            request.LANGUAGE_CODE).filter(category="Student")
        # context['genrate_noti_bar'] = genarate_notification_bar(request)
        context['stu_testimonials'] = stu_testimonials
        context['year'] = date_now.year
        context['current_page'] = 'index'
        create_custom_event(request, event_id=7, meta_data={'clarity_token':clarity_token,'custom_user_session_id':custom_user_session_id})

        #logger.warning("WARNING From development")
        try:
            if user_agent != "ELB-HealthChecker/2.0":
                if(request.user.id):
                    user_name = request.user.username
                    logger.info(f"Landing page visited by : {user_name}")
                    logger_console.info(f"Landing page visited by : {user_name}")
                else:
                    logger.info(f"Landing page visited by : {custom_user_session_id}")
                    logger_console.info(f"Landing page visited by : {custom_user_session_id}")
        except Exception as exp:
            logger.warning(f"Failed to check user_agent for user {custom_user_session_id}")
        return render(request, self.template_name, context)
 

class LandingPageIOSView(TemplateView):
    template_name = "website/index.html"

    def get(self, request):
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        clarity_token = self.request.session.get('clarity_token', '')
        user_agent = request.META.get('HTTP_USER_AGENT',None)
        request.session["is_from_ios_app"] = True
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        context = {}
        stu_testimonials = Testimonials.published.lang_code(
            request.LANGUAGE_CODE).filter(category="Student")
        # context['genrate_noti_bar'] = genarate_notification_bar(request)  
        context['stu_testimonials'] = stu_testimonials
        context['year'] = date_now.year
        context['current_page'] = 'index'
        create_custom_event(request, event_id=7, meta_data={'clarity_token':clarity_token,'custom_user_session_id':custom_user_session_id})
        #logger.warning("WARNING From development")
        try:
            if user_agent != "ELB-HealthChecker/2.0":
                if(request.user.id):
                    user_name = request.user.username
                    logger.info(f"Landing page visited by : {user_name}")
                    logger_console.info(f"Landing page visited by : {user_name}")
                else:
                    logger.info(f"Landing page visited by : {custom_user_session_id}")
                    logger_console.info(f"Landing page visited by : {custom_user_session_id}")
        except Exception as exp:
            logger.warning(f"Failed to check user_agent for user {custom_user_session_id}")
        return render(request, self.template_name, context)
 
class LandingPageView_light(TemplateView):
    template_name = "website/index_light.html"

    def get(self, request):
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        context = {}
        stu_testimonials = Testimonials.published.lang_code(
            request.LANGUAGE_CODE).filter(category="Student")
        # context['genrate_noti_bar'] = genarate_notification_bar(request)
        context['stu_testimonials'] = stu_testimonials
        context['year'] = date_now.year
        context['current_page'] = 'index'
        # create_custom_event(request, event_id=7)
        #logger.warning("WARNING From development")
        return render(request, self.template_name, context)

class AboutView(TemplateView):
    template_name = "website/about.html"

    def get(self, request):
        clarity_token = self.request.session.get('clarity_token', '')
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')

        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                user_name = request.user.username
                logger.info(f"Aboutus page visited by : {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                user_name = request.user.username
                logger.info(f"Abountus page visited by : {user_name}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        context = {}
        context['year'] = date_now.year
        context['current_page'] = 'about'
        create_custom_event(request, event_id=10, meta_data={'clarity_token':clarity_token,'custom_user_session_id':custom_user_session_id})

        if(request.user.id):
            user_name = request.user.username
            logger.info(f"Aboutus page visited by : {user_name}")
        else:
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            logger.info(f"Aboutus page visited by : {custom_user_session_id}")
        return render(request, self.template_name, context)


class SchoolView(TemplateView):
    template_name = "website/school.html"

    def get(self, request):
        clarity_token = self.request.session.get('clarity_token', '')
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                user_name = request.user.username
                logger.info(f"Highschool page visited by : {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                user_name = request.user.username
                logger.info(f"Highschool page visited by : {user_name}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        context = {}
        school_testimonials = Testimonials.published.lang_code(
            request.LANGUAGE_CODE).filter(category="School")
        context['school_testimonials'] = school_testimonials
        context['year'] = date_now.year
        context['current_page'] = 'school'
        create_custom_event(request, event_id=9, meta_data={'clarity_token':clarity_token,'custom_user_session_id':custom_user_session_id})
        if(request.user.id):
            user_name = request.user.username
            logger.info(f"Highschool page visited by : {user_name}")
        else:
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            logger.info(f"Highschool page visited by : {custom_user_session_id}")
        return render(request, self.template_name, context)


class StudentView(TemplateView):
    template_name = "website/student.html"

    def get(self, request):
        clarity_token = self.request.session.get('clarity_token', '')
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                user_name = request.user.username
                logger.info(f"Student page visited by : {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                user_name = request.user.username
                logger.info(f"Student page visited by : {user_name}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        context = {}
        mentors_info = MentorsInfo.published.lang_code(
            request.LANGUAGE_CODE).all()
        webinars = Webinars.published.lang_code(request.LANGUAGE_CODE).all()
        context['mentors_info'] = mentors_info
        context['webinars'] = webinars
        context['year'] = date_now.year
        context['current_page'] = 'student'
        create_custom_event(request, event_id=8, meta_data={'clarity_token':clarity_token,'custom_user_session_id':custom_user_session_id})
        if(request.user.id):
            user_name = request.user.username
            logger.info(f"Student page visited by : {user_name}")
        else:
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            logger.info(f"Student page visited by : {custom_user_session_id}")
        return render(request, self.template_name, context)


class MentorView(TemplateView):
    template_name = "website/mentor.html"

    def get(self, request):
        clarity_token = self.request.session.get('clarity_token', '')
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                user_name = request.user.username
                logger.info(f"Mentor page visited by : {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                user_name = request.user.username
                logger.info(f"Mentor page visited by : {user_name}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        context = {}
        context['year'] = date_now.year
        context['current_page'] = 'mentor'
        create_custom_event(request, event_id=18, meta_data={'clarity_token':clarity_token,'custom_user_session_id':custom_user_session_id})
        if(request.user.id):
            user_name = request.user.username
            logger.info(f"Mentor page visited by : {user_name}")
        else:
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            logger.info(f"Mentor page visited by : {custom_user_session_id}")  
        return render(request, self.template_name, context)


class PriceView(TemplateView):

    template_name = "website/new-futurely-plans.html"

    def get(self, request):
        if request.LANGUAGE_CODE=='it':
            self.template_name = "website/futurely-plans-it.html"
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                user_name = request.user.username
                logger.info(f"Plan page visited by {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                user_name = request.user.username
                logger.info(f"Plan page visited by {user_name}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
        context = {}
        request.session['free_coupon_code'] = "forever10"
        selected_payment_type = request.session.get('selected_payment_type','One Time')
        free_coupon_code = "forever10"
        coupon_details = payment_models.Coupon.active_objects.filter(code__iexact=free_coupon_code).first()
        context['coupon_details'] = coupon_details
        coupon_code_exists = "None"
        if coupon_details:
            coupon_code_exists = "True"
        local_tz = pytz.timezone(settings.TIME_ZONE)
        date_now = local_tz.localize(datetime.datetime.now())
        
        context['all_plans'] = models.OurPlans.plansManager.lang_code(
            request.LANGUAGE_CODE).all()
        context['year'] = date_now.year
        context['current_page'] = 'price'
        context['selected_payment_type'] = selected_payment_type
        create_custom_event(request, event_id=19)
        if(request.user.id):
            user_name = request.user.username
            logger.info(f"Plan page visited by : {user_name}")
        else:
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            logger.info(f"Plan page visited by : {custom_user_session_id}")
        starting_date =  datetime.date.today()
        premium_cohort_start = Cohort.objects.filter(starting_date__gte=starting_date, module__module_id=3, is_active="Yes").order_by('starting_date').first()
        elite_cohort_start = Cohort.objects.filter(starting_date__gte=starting_date, module__module_id=4, is_active="Yes").order_by('starting_date').first()
        if premium_cohort_start:
            delta = premium_cohort_start.starting_date - starting_date
            context["premium_days_left"] = delta.days
        if elite_cohort_start:
            elite_delta = elite_cohort_start.starting_date - starting_date
            context["elite_days_left"] = elite_delta.days
        return render(request, self.template_name, context)


def page_not_found_404_view(request, exception):
    context = {}
    context['current_page'] = '404'
    if request.user.is_authenticated:
        if request.user.person_role == "Student":
            user_name = request.user.username
            logger.info(f"Page-not-found-404 called by : {user_name}")
        else:
            user_name = request.user.username
            logger.info(f"Page-not-found-404 called by : {user_name}")
    else:
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"Page-not-found-404 called by : {custom_user_session_id}")
    # create_custom_event(request, event_id=12)
    return render(request, "website/404.html", context, status=404)


def csrf_failure(request, reason=""):
    return HttpResponseRedirect(reverse("home"))


def contact_dimond_queries(request):
    try:
        if request.method == "POST" and request.is_ajax:
            request_post = request.POST
            phone = request_post.get('phone', None)
            email = request_post.get('email', None)
            # subject = request_post.get('subject', None)
            if phone and email:
                if request.user.id:
                    person = PERSON.objects.filter(
                        Q(id=request.user.id)).first()
                else:
                    person = PERSON.objects.filter(Q(email=email)).first()

                if person:
                    DiamnodQuery.objects.create(person=person, email=email, phone_num=phone, status="Open")
                else:
                    DiamnodQuery.objects.create(phone_num=phone, email=email, status="Open")
                return JsonResponse({'msg': 'Success'}, status=200)
            return JsonResponse({'msg': 'You must have to fill the phone, email id and queries....'}, status=400)
        else:
            return JsonResponse({'msg': 'We can not process your query'}, status=400)
    except Exception as e:
        print(e)
        return JsonResponse({'msg': 'We are unable to send your query , Please try later...'}, status=400)

def lets_talk_send_message(request):
    try:
        if request.method == "POST" and request.is_ajax:
            request_post = request.POST
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
            current_page = request.GET.get('page', '')
            name = request_post.get('name', None)
            email = request_post.get('email', None)
            message_body = request_post.get('message_body', None)
            subject = request_post.get('subject', None)
            if name and email and message_body:
                if request.user.id:
                    person = PERSON.objects.filter(
                        Q(id=request.user.id)).first()
                else:
                    person = PERSON.objects.filter(Q(email=email)).first()

                if person:
                    Query.objects.create(
                        person=person, name=name, email=email, message=message_body, status="Open")
                else:
                    Query.objects.create(
                        name=name, email=email, message=message_body, status="Open")
                fromEmail = settings.EMAIL_HOST_USER
                #toEmail = "no-reply@myfuturely.com"
                if(request.LANGUAGE_CODE == "it"):
                    toEmail = "contatto@myfuturely.com"
                else:
                    toEmail = "contact@myfuturely.com"
                msg = f"Email id is : {email} \n Message is : {message_body} ."
                try:
                    ip_address = get_client_ip(request)
                    user_agent = request.META.get('HTTP_USER_AGENT', None)
                    influencer = request.session.get('INFLUENCER', '')
                    page_url = request.get_full_path()
                    send_email_task.apply_async(args=[subject, msg, fromEmail, toEmail,request.user.id,ip_address,user_agent,influencer,page_url,current_page,email,custom_user_session_id])
                    return JsonResponse({'msg': 'Queries  successfully submitted'}, status=200)
                except:
                    return JsonResponse({'msg': 'We are unable to send your query , Please try later...'}, status=400)
            return JsonResponse({'msg': 'You must have to fill the name, email id and queries....'}, status=400)
        else:
            return JsonResponse({'msg': 'We can not process your query'}, status=400)
    except Exception as e:
        print(e)
        if(request.user.id):
            user_name = request.user.username
            logger.error(
                f"Error to submit lets talk query, and username is : {user_name}")
        else:
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            logger.error(
                f"Error to submit lets talk query, and session id is : {custom_user_session_id}")
        return JsonResponse({'msg': 'We are unable to send your query , Please try later...'}, status=400)

import mimetypes
import urllib.request
from django.core.files.storage import default_storage

def file_download_view(request,file_id):
    try:
        file_obj = Files.objects.get(id=file_id)
        fl_path = file_obj.file.url
        file = default_storage.open(str(file_obj.file), 'rb')
        
        #print(file_obj.file.path())
        #return HttpResponseRedirect(fl_path)
        # response1 = urllib.request.urlopen(fl_path) 
        # file = open(os.path.basename(fl_path), 'wb')
        # file.write(response1.read())
        # file.close()
        # file = open(os.path.basename(fl_path), 'rb')
        response = HttpResponse(file.read(), content_type="application/file")
        response['Content-Disposition'] = 'inline;filename=' + \
           os.path.basename(fl_path)
        logger.info(f"File downloaded by : {request.user.username}")
        return response
        #return HttpResponse("Hello")

    except Exception as ex:
        print(ex)
        logger.error(f"Error in File download : {ex}")
    raise Http404

def health_check_view(request):
    # del request.session["lang"]
    # display_lang_popup = request.session.get('display_lang_popup', None)
    # if(display_lang_popup is not None):
    #     del request.session['display_lang_popup']
    return HttpResponse("H")

from django.urls import resolve, Resolver404

def select_lang_at_initial_view(request):
    try:
        display_lang_popup = request.session.get('display_lang_popup', None)
        if display_lang_popup == "False" or display_lang_popup is None:
            return HttpResponseRedirect(reverse("index"))
    except Exception as exp:
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.error(f"Error to redirect the page from select language to index for user {exp}: {custom_user_session_id}")
    return render(request, "website/select_language.html")

def set_lang_view(request):
    if(request.user.id):
        user_name = request.user.username
        logger.info(
            f"Switch language is called by username : {user_name}")
    else:
        custom_user_session_id = request.session.get(
            'CUSTOM_USER_SESSION_ID', '')
        logger.info(
            f"Switch language is called by session id : {custom_user_session_id}")
    lang = request.GET.get("lang", None)
    url = request.session.get('reverse_url_from_setlang', None)
    print(url)
    try:
        if(url is None):
            url = request.GET.get("u", None)
            if(url is None):
                url = "/"

        print(url)
        request.session["lang"] = lang
        request.session['display_lang_popup'] = "False"
        request.session['reverse_url_from_setlang'] = None
        return redirect(url)
    except Exception as e:
        print(e)
        return redirect('/')
    # try:
    #     resolve(url)
    # except Resolver404:
    #     lang = "it"
    #     url = "/" 

from lib.helper import get_client_ip

@require_GET
def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: ",
    ]
    current_url_path = request._current_scheme_host + request.path
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
    ip_address = request.COOKIES.get("ip_address", None)
    user_agent = request.META.get('HTTP_USER_AGENT',None)
    if ip_address is None:
        ip_address = get_client_ip(request)
    if(request.user.id):
        user_name = request.user.username
        logger.info(f"Request processed in robots_txt for HTTP_USER_AGENT: {user_agent} ip_address: {ip_address}, visited url(Page): {current_url_path} and visited by : {user_name}")
    else:
        logger.info(f"Request processed in robots_txt for HTTP_USER_AGENT: {user_agent} ip_address: {ip_address}, visited url(Page): {current_url_path} and visited by : {custom_user_session_id}")   
    return HttpResponse("\n".join(lines), content_type="text/plain")

def cookie_accept_view(request):
    to_display_first_time_cookie_banner = request.session.get("to_display_first_time_cookie_banner", None)
    clarity_token = request.session.get('clarity_token', '')
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    cookies_type = request.POST.get('cookies_type')
    if to_display_first_time_cookie_banner is None:
        request.session['to_display_first_time_cookie_banner'] = "True"
        request.session['cookies_accepted'] = False
        cookies_accepted = False
        logger.info(f"In cookies accept view for session id : {custom_user_session_id}")
    else:
        request.session['to_display_first_time_cookie_banner'] = "False"
        request.session['cookies_accepted'] = True
        cookies_accepted = True
        create_custom_event(request, 22, custom_user_session_id)
        cookies_esperienza = False
        cookies_misurazione = False
        cookies_necessari = False
        if cookies_type == "Necessari":
            cookies_necessari = True
        elif cookies_type == "All":
            cookies_esperienza = True
            cookies_misurazione = True
            cookies_necessari = True
            
        cookies_obj, created = CookiesSelectedData.objects.update_or_create(
            custom_session_id=custom_user_session_id,
            clarity_id = clarity_token,
            defaults={
                "cookies_necessari": cookies_necessari,
                "cookies_esperienza": cookies_esperienza,
                "cookies_misurazione": cookies_misurazione,
                "cookies_selected_section": "Banner",
                }
            )
        logger.info(f"All cookies accepted by session id : {custom_user_session_id}")
    return JsonResponse({"cookies_accepted": cookies_accepted}, status=200, safe=False)

def cookies_data_save_view(request):
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    clarity_token = request.session.get('clarity_token', '')
    if request.method == "POST":
        request_post = request.POST
        print(request_post)
        cookies_necessari = request_post.get('cookies_necessari')
        if cookies_necessari == "true":
            cookies_necessari = True
        else:
            cookies_esperienza = False
        cookies_esperienza = request_post.get('cookies_esperienza')
        if cookies_esperienza == "true":
            cookies_esperienza = True
        else:
            cookies_esperienza = False
        cookies_misurazione = request_post.get('cookies_misurazione')
        if cookies_misurazione == "true":
            cookies_misurazione = True
        else:
            cookies_misurazione = False
        cookies_selected_section = request_post.get('cookies_selected_section')
        logger.info(f"Cookies data save view for session id : {custom_user_session_id}")
        cookies_obj, created = CookiesSelectedData.objects.update_or_create(
            custom_session_id=custom_user_session_id,
            clarity_id = clarity_token,
            defaults={
                
                "cookies_necessari": cookies_necessari,
                "cookies_esperienza": cookies_esperienza,
                "cookies_misurazione": cookies_misurazione,
                "cookies_selected_section": cookies_selected_section,
                }
            )
        logger.info(f"Cookies data updated in database for session id : {custom_user_session_id}")
        to_display_first_time_cookie_banner = request.session.get("to_display_first_time_cookie_banner", None)
        if to_display_first_time_cookie_banner is None:
            request.session['to_display_first_time_cookie_banner'] = "True"
            request.session['cookies_accepted'] = False
            cookies_accepted = False
            logger.info(f"In cookies accept view for session id : {custom_user_session_id}")
        else:
            request.session['to_display_first_time_cookie_banner'] = "False"
            request.session['cookies_accepted'] = True
            cookies_accepted = True
            create_custom_event(request, 22, custom_user_session_id)
            logger.info(f"All cookies accepted by session id : {custom_user_session_id}")
        return JsonResponse({"cookies_accepted": cookies_accepted}, status=200, safe=False)
    else:
        return JsonResponse({"cookies_accepted": False}, status=200, safe=False)

def privacy_policy(request):
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    logger.info(f"Privacy policy is called by session id : {custom_user_session_id}")
    create_custom_event(request, 25, custom_user_session_id)
    return render(request, "website/privacy_policy.html")


def cookies_policy(request):
    coustomize_cookies = request.GET.get('coustomize_cookies', False)
    if coustomize_cookies == "True":
        create_custom_event(request, 23)
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    logger.info(f"Cookies policy is called by session id : {custom_user_session_id}")
    create_custom_event(request, 24, custom_user_session_id)
    return render(request, "website/cookies_policy.html")

def terms_of_use(request):
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    logger.info(f"Terms of use is called by session id : {custom_user_session_id}")
    create_custom_event(request, 26, custom_user_session_id)
    return render(request, "website/terms_of_use.html")

def collect_student_parents_info(request):
    lang = request.session.get('lang', None)
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    # if lang == 'it':
    #     companies = Company.objects.filter(country="Italy")
    # else:
    #     companies = Company.objects.filter(country="USA")
    companies = CompanyWithSchoolDetail.objects.all()
    form = ParentInfoForm()
    logger.info(f"In collect_student_parents_info  and the user is: {custom_user_session_id}")
    context = {'companies': companies,'form':form}
    if request.method == 'POST':
        form = ParentInfoForm(request.POST)
        if form.is_valid(): 
            logger.info(f"Student-Parents info Form is valid for The User : {custom_user_session_id}")
            parent_name = form.cleaned_data['parent_name']
            parent_email = form.cleaned_data['parent_email']
            child_name = form.cleaned_data['child_name']
            child_email = form.cleaned_data.get('child_email', None)
            child_number = form.cleaned_data.get('child_number', None)
            school_path = form.cleaned_data.get('school_path')
            is_checked = request.POST.get('check_tos', False)
            if not is_checked:
                context["form"] = form
                context['tos_message'] = ('You must accept before proceeding')
                return render(request, "website/student_parents_lp.html",context)
            try:
                company_id = request.POST.get('company')
                company_name = Company.objects.get(id=company_id)
                logger.info(f"In hubspot signup parameter building for : {parent_email}")
                if school_path == "Scuola Superiore (Secondaria di secondo grado)":
                    child_number = str("+") + str("39") + str(child_number)
                    student_parent = ParentInfo(parent_name=parent_name, parent_email=parent_email, child_name=child_name, child_email=child_email, child_number=child_number,company_name=company_name, school_path=school_path)
                    keys_list = ['email','firstname','hubspot_company_name','hubspot_is_from_landing','hubspot_children_related_email','hubspot_children_related_name','hubspot_children_related_phone', 'hubspot_landing_path_type','parent_is_from_high_school']
                    values_list = [parent_email,parent_name,company_name.name,'Yes',child_email,child_name,child_number, school_path,'Yes']
                    keys_list2 = ['email','hubspot_children_related_email','hubspot_parents_email','firstname','hubspot_children_related_name','hubspot_company_name','hubspot_is_from_landing','hubspot_landing_path_type']
                    values_list2 = [child_email,child_email,parent_email,child_name,child_name,company_name.name,'Yes',school_path]

                else:
                    student_parent = ParentInfo(parent_name=parent_name, parent_email=parent_email, child_name=child_name,company_name=company_name, school_path=school_path)
                    keys_list = ['email','firstname','hubspot_company_name','hubspot_is_from_landing','hubspot_children_related_name', 'hubspot_landing_path_type','parent_is_from_middle_school']
                    values_list = [parent_email,parent_name,company_name.name,'Yes',child_name, school_path,'Yes']
                    
                student_parent.save()
                create_update_contact_hubspot(parent_email, keys_list, values_list)
                if school_path == "Scuola Superiore (Secondaria di secondo grado)":
                    create_update_contact_hubspot(child_email, keys_list2, values_list2)
                logger.info(f"Hubspot properties updated successfully for : {parent_email}")
                logger.info(f"Form submitted , redirected to thank you page for parent  :{parent_email} and student {child_email} ")
                context["form"] = form
                return render(request, "website/student_parents_lp_thankyou.html", {'form': form})
            except Exception as error:
                context["form"] = form
                logger.error(f" An Exception occured to save Student-parent information : {error} for parent - {parent_email}")
                return render(request, "website/student_parents_lp.html",context)
        else:
            context["form"] = form
            logger.warning(f"Form is invalid for The User : {custom_user_session_id}")
            return render(request, "website/student_parents_lp.html",context)
    return render(request,"website/student_parents_lp.html",context)

        

