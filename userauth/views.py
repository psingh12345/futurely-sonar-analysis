from datetime import datetime
from multiprocessing import context
# from turtle import delay
from django.shortcuts import render
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.db.models import Q
from django.views.generic.base import View
import requests
from .forms import PersonRegisterForm, StudentCompletionForm, PasswordResttingForm, \
    PasswordSetForm, EmailVerifyForm, LoginForm, FutureLabPersonRegisterForm, MiddleSchoolParentsDetailForm, CounselorRegisterForm
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.urls import reverse_lazy
import stripe
import json
import traceback
from django.contrib.auth import get_user_model
from .models import MasterOTP, Person, Student, StudentSchoolDetail, School, Company, ClassName, ClassYear, Specialization, Counselor, CountryDetails, StudentParentsDetail
from courses.models import Modules, Cohort, Notification_type, OurPlans
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string, get_template
from django.template import Context
from django.core.mail import message, send_mail, BadHeaderError, EmailMessage
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import ugettext as _
from student.models import Stu_Notification, PersonNotification
from lib.helper import create_custom_event
from payment.models import Coupon, Payment, CouponDetail
from student.models import StudentsPlanMapper, StudentCohortMapper, StudentPCTORecord
import pytz
import random
import math
from django.utils import html
import logging
from lib.hubspot_contact_sns import create_update_contact_hubspot
from lib.unixdateformatConverter import unixdateformat
# from userauth.tasks import submit_hubspot_for_login, test_func_task
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from student.tasks import exercise_cohort_step_tracker_creation, link_with_action_items
import time
from website.models import ParentInfo
from userauth.tasks import send_email_message_task
from lib.custom_logging import CustomLoggerAdapter

adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


PERSON = get_user_model()

"""
@method_decorator(login_required, name="dispatch")
class IndexView(TemplateView):
    template_name = "student/index.html"
    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        context["test_data"] = "Test Data"
        return context
"""
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
 
def signupstage1_placeholders(context):
    context["placeholder_email"] = _("Email address")
    context["placeholder_first_name"] = _("First name")
    context["placeholder_last_name"] = _("Last name")
    context["placeholder_password"] = _("Password")
    context["placeholder_confirm_password"] = _("Conferma Password")
    context["placeholder_contact_number"] = _("Contact number")
    context["placeholder_how_know_other"] = _("If other, enter the source here")
    context["placeholder_gender_other"] = _("Gender")
    return context

# """
#     This method is used to associate a new email on hubspot whenever there is a new sign in or registrationa
# """
def submit_hubspot_form_with_email(request, email):
    try:
        hubspot_user_tracking_id = request.COOKIES.get('hubspotutk', '')
        logger.info("Submitting hubspot for email %s, hubspot tracking id %s",
                    email, hubspot_user_tracking_id)

        hubspot_portal_id = "20116637"
        hubspot_form_id = "893db2db-bf2e-4d76-b3bd-ebba0910b3da"
        url = "https://api.hsforms.com/submissions/v3/integration/submit/{}/{}".format(
            hubspot_portal_id, hubspot_form_id)
        headers = {}
        headers['Content-Type'] = 'application/json'

        data = json.dumps({
            "fields": [
                {
                    "name": "email",
                    "value": email
                },
            ],
            "cookies": {
                "hutk": hubspot_user_tracking_id
            }
        })

        r = requests.post(data=data, url=url, headers=headers)
        logger.info("Submitted hubspot for email %s, hubspot tracking id %s with status code %s",
                    email, hubspot_user_tracking_id, r.status_code)
    except Exception as e:
        logger.error("Error in submitting hubspot form for email %s, exception %s",
                        email, str(e))
        logger.error(traceback.print_exc())

class PersonRegistrationView(UserPassesTestMixin, TemplateView):
    """
    PersonRegistrationView class for the registration.
    [summary]
    Args:
        TemplateView ([type]): [description]
    Returns:
        [type]: [description]
    """
    template_name = "userauth/signup.html"

    def test_func(self):
        if not self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    # def get_context_data(self, *args, **kwargs):
    #     ctype = self.request.GET.get('ctype', None)
    #     plan = self.request.GET.get('plan', None)
    #     self.request.session['ctype'] = ctype if ctype else 'general'
    #     if plan:
    #         self.request.session['plan'] = plan
    #     context = super(PersonRegistrationView, self).get_context_data(*args, **kwargs)
    #     context["person_register_form"] = PersonRegisterForm()
    #     return context


    def get(self, *args, **kwargs):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        ctype = self.request.GET.get('ctype', None)
        plan = self.request.GET.get('plan', None)

        coupon_code = self.request.session.get('coupon_code', None)
        coupon_type = self.request.session.get('coupon_type', None)
        if self.request.LANGUAGE_CODE == "it":
            if not coupon_code or coupon_type != 'Organization':
                logger.info(f"Coupon Code is not available for {custom_user_session_id}")
                url = reverse('index') + '?validate_discount_code=true'
                return HttpResponseRedirect(url)
        self.request.session['ctype'] = ctype if ctype else 'general'
        if plan:
            self.request.session['plan'] = plan
        context = {} #super(PersonRegistrationView, self).get_context_data(*args, **kwargs)
        context["person_register_form"] = PersonRegisterForm()
        context = signupstage1_placeholders(context)
        create_custom_event(self.request, 20, meta_data={'ctype':self.request.GET.get('ctype', 'general'), 'plan': self.request.GET.get('plan', '')})
        logger.info(f"Signup page person register view in get method called by : {custom_user_session_id}")
        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        this is post method of PersonRegistrationView, this method accept the POST requests.
        """
        request_post = request.POST
        email_for_log = request_post.get('email')
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
        clarity_token = self.request.session.get('clarity_token', '')
        logger.info(f"In post view of person-regitration-view : {email_for_log}")
        context = super(PersonRegistrationView, self).get_context_data(*args, **kwargs)
        all_companies = []

        if request.LANGUAGE_CODE == 'en-us':
            logger.info(f"In post view of person-regitration-view called with language code : {request.LANGUAGE_CODE} : {email_for_log}")
            school_country = 'USA'
            all_schools = CountryDetails.objects.filter(country='USA')
            all_companies = Company.objects.filter(country='USA')
            context['companies'] = all_companies
            context['specilizations'] = Specialization.objects.filter(country='USA')
            context['class_names'] = ClassName.objects.filter(country='USA')
            context['class_years'] = ClassYear.objects.filter(country='USA')
            email_html_content = "userauth/email_content.html"
        elif request.LANGUAGE_CODE == 'it':
            logger.info(f"In post view of person-regitration-view called with language code : {request.LANGUAGE_CODE} : {email_for_log}")
            school_country = 'Italy'
            all_schools = CountryDetails.objects.filter(country='Italy')
            all_companies = Company.objects.filter(country='Italy')
            context['companies'] = all_companies
            context['specilizations'] = Specialization.objects.filter(country='Italy')
            context['class_names'] = ClassName.objects.filter(country='Italy')
            context['class_years'] = ClassYear.objects.filter(country='Italy')
            email_html_content = "userauth/email_content-it.html"
        context['school_regions'] = all_schools.order_by('region').values('region').distinct()
        if 'hdn_first_name' in request_post:
            student_completion_form = StudentCompletionForm(request_post)
            errors_list = []
            first_name = request_post.get('hdn_first_name')
            last_name = request_post.get('hdn_last_name')
            gender = request_post.get('hdn_gender')
            email = request_post.get('hdn_email')
            password = request_post.get('hdn_password')
            confirm_password = request_post.get('hdn_password')
            contact_number = request_post.get('hdn_contact_number')
            how_know_us = request_post.get('hdn_how_know_us')
            how_know_us_other = request_post.get('hdn_how_know_us_other')
            gender_other = request_post.get('hdn_gender_other')
            company_name = request_post.get('company-name','')
            tos_agreed = request_post.get('check_tos', 'No')
            discount_code=request_post.get('future_lab_code','')

            if password != confirm_password:
                    context["person_register_form"] = person_register_form
                    context['confirm_password_error'] = _("Confirm Password does not match")
                    return render(request, "userauth/signup.html", context)
            
            # sp_data_agreed = request_post.get('check_sp_data', 'No')
            discount_code_end_date = ''
            student_type = request.session.get('ctype','')
            coupon_code_status = False
            if password != confirm_password:
                return render(request, "userauth/signup.html", context)

            if discount_code.strip() != '':
                coupon_code_status = check_discount_code_validation(request, discount_code)
            if student_type == "future_lab" or student_type == "company":
                if discount_code.strip() == '':
                    context["student_completion_form"] = student_completion_form
                    context['discount_code_none'] = _('Invalid discount code')
                    logger.warning(f"Signup page stage 2 - Future lab - Invalid discount code : {email}")
                    return render(request, "userauth/signup_next.html", context)
                else:
                    if(coupon_code_status == False):
                        context["student_completion_form"] = student_completion_form
                        context['discount_code_none'] = _('Invalid discount code')
                        logger.warning(f"Signup page stage 2 - Future lab - Invalid discount code : {email}")
                        return render(request, "userauth/signup_next.html", context)

            if tos_agreed != 'Checked':
                context["student_completion_form"] = student_completion_form
                context['tos_message'] = _('You must accept before proceeding')
                print(f"tos not checked")
                logger.warning(f"Signup page stage 2 - Not selected tos checkbox : {email}")
                return render(request, "userauth/signup_next.html", context)
            # if sp_data_agreed != 'Checked':
            #     context["student_completion_form"] = student_completion_form
            #     context['sp_data_message'] = _("You must accept before proceeding")
            #     return render(request, "userauth/signup_next.html", context)
            context['first_name'] = first_name
            context['last_name'] = last_name
            context['gender'] = gender
            context['email'] = email
            context['password'] = password
            context['contact_number'] = contact_number
            context['how_know_us'] = how_know_us
            context['how_know_us_other'] = how_know_us_other
            context['gender_other'] = gender_other
            school_region = request_post.get('school-region', '')
            school_city = request_post.get('school-city', '')
            school_name = request_post.get('school-name', '')
            school_name_other = request_post.get('school_name_other', '')
            bit_other_school = False
            if student_type != "future_lab":
                if(school_region == "" ):
                    context['school_region_message'] = _('You must select before proceeding')
                    context['school_city_message'] = _('You must select before proceeding')
                    context['school_name_message'] = _('You must select before proceeding')
                    context["student_completion_form"] = student_completion_form
                    logger.warning(f"Signup page stage 2 - Not selected school region : {email}")
                    return render(request, "userauth/signup_next.html", context)
                elif(school_city == ""):
                    context['school_city_message'] = _('You must select before proceeding')
                    context['school_name_message'] = _('You must select before proceeding')
                    context["student_completion_form"] = student_completion_form
                    logger.warning(f"Signup page stage 2 - Not selected school city : {email}")
                    return render(request, "userauth/signup_next.html", context)
                elif(school_name == ""):
                    context['school_name_message'] = _('You must select before proceeding')
                    context["student_completion_form"] = student_completion_form
                    logger.warning(f"Signup page stage 2 - Not selected school name : {email}")
                    return render(request, "userauth/signup_next.html", context)
                elif(school_name == "Other"):
                    if(school_name_other == ''):
                        context['school_name_message'] = _('You must enter before proceeding')
                        context["student_completion_form"] = student_completion_form
                        logger.warning(f"Signup page stage 2 - Not selected school name other : {email}")
                        return render(request, "userauth/signup_next.html", context)
                    else:
                        bit_other_school = True
                        school_name = school_name_other

                
            if student_completion_form.is_valid():
                hubspot_student_parent_email_missing_from_landing=None
                hubspot_student_parent_email_from_landing_exists=None
                hubspot_student_parent_email_from_landing=None
                person = None
                try:
                    person = PERSON.objects.create_user(first_name=first_name, last_name=last_name, username=email, email=email, password=password, contact_number=contact_number,how_know_us=how_know_us,how_know_us_other=how_know_us_other, gender=gender, gender_other=gender_other,lang_code=request.LANGUAGE_CODE, country_name=school_country,clarity_token=clarity_token)
                except Exception as erro:
                    print(erro)
                    # context["message"] = [f"The email {email} already exists in the system."]
                    context["person_register_form"] = PersonRegisterForm()
                    context = signupstage1_placeholders(context)
                    logger.error(f"Error email already exist in person register view {erro} : {email}")
                    return render(request, "userauth/signup.html", context)

                student = student_completion_form.save(commit=False)
                student.person = person
                student.src = self.request.session.get('ctype', 'general')
                student.are_you_fourteen_plus = "Yes"
                free_coupon_code = request.session.get('free_coupon_code',None)
                student.discount_coupon_code = discount_code
                # if discount_code == '':
                #     student.discount_coupon_code = free_coupon_code
                number_of_plans = "3"
                skip_course_dependency = False
                is_course1_locked = False
                display_discounted_price_only = False
                is_fully_paid_by_school_or_company = False
                coupon_obj = None
                is_100_per_coupon_code = False
                coupon_detail_obj = None
                hubspot_school_type = "free_channel"
                hubspot_is_from_fast_track_program = "None"
                hubspot_is_for_fast_track_program = "None"
                is_from_middle_school = False
                is_from_fast_track_program = False
                try:
                    if(discount_code != "" and coupon_code_status == True):
                        coupon_obj = Coupon.objects.get(code__iexact=discount_code)
                        number_of_plans = coupon_obj.number_of_offered_plans
                        skip_course_dependency = coupon_obj.skip_course_dependency
                        is_course1_locked = coupon_obj.is_course1_locked
                        is_from_middle_school = coupon_obj.is_for_middle_school
                        is_from_fast_track_program = coupon_obj.is_for_fast_track_program
                        if is_from_fast_track_program:
                            hubspot_is_from_fast_track_program = "Yes"
                            hubspot_is_for_fast_track_program = "Yes"
                        else:
                            hubspot_is_from_fast_track_program = "No"
                            hubspot_is_for_fast_track_program = "No"
                        discount_code_end_date = coupon_obj.end_date
                        display_discounted_price_only = coupon_obj.display_discounted_price_only
                        is_fully_paid_by_school_or_company = coupon_obj.is_fully_paid_by_school_or_company
                        discount_type = coupon_obj.discount_type
                        if coupon_obj.coupon_type == "FutureLab":
                            if coupon_obj.is_fully_paid_by_school_or_company == True:
                                hubspot_school_type = "fully_paid"
                                student.student_channel = "fully_paid"
                                student.save()
                            else:
                                hubspot_school_type = "free_channel"
                                student.student_channel = "free_channel"
                                student.save()
                            student.src = "future_lab"
                        discount_value = int(coupon_obj.discount_value)
                        if discount_type == "Percentage" and discount_value == 100:
                            is_100_per_coupon_code = True
                        coupon_detail_obj = CouponDetail.objects.filter(coupon=coupon_obj).first()
                        try:
                            if coupon_detail_obj:
                                school_region = coupon_detail_obj.school.region
                                school_city = coupon_detail_obj.school.city
                                school_name = coupon_detail_obj.school.name
                        except:
                            logger.warning(f"School details are not linked with coupon code: {coupon_obj.code} : {email}")
                            # school_type = coupon_detail_obj.school.type
                except Exception as error:
                    print(error)
                    logger.warning(f"Error of discount_code at person-register-view {error}: {email}")
                
                try:
                    if(company_name != ""):
                        student.company = Company.objects.get(pk=company_name)
                except Exception as error:
                    print(str(error))
                    logger.warning(f"Error of company at person-register-view {error}: {email}")
                
                student.number_of_offered_plans = number_of_plans
                student.skip_course_dependency = skip_course_dependency
                student.is_course1_locked = is_course1_locked
                student.display_discounted_price_only = display_discounted_price_only
                student.is_from_middle_school = is_from_middle_school
                student.is_from_fast_track_program = is_from_fast_track_program
                student.save()
                school_type = ''
                graduation_year = request_post.get('year', '')
                class_year = request_post.get('class-year', '')
                class_name = request_post.get('class-name', '')
                class_specialization = request_post.get('class-specialization', '')
                parent_email = request_post.get('parent_email', '')
                hubspot_registration_parent_email = parent_email
                if parent_email:
                    student_parent_details = StudentParentsDetail.objects.create(student=student,parent_email=parent_email,parent_email_from_reg=parent_email)
                try:
                    if coupon_obj:
                        if coupon_obj.coupon_type == "Organization":
                            student.src = "company"
                            coupon_details = CouponDetail.objects.filter(coupon=coupon_obj).first()
                            if coupon_details:
                                if coupon_details.company:
                                    student.company = coupon_details.company
                            student.save()
                            student_already_exist = ParentInfo.objects.filter(Q(child_email=email) | Q(child_name=f"{first_name} {last_name}") | Q(child_name=f"{last_name} {first_name}")).first()
                            if student_already_exist:
                                if person.contact_number == "" or person.contact_number is None or person.contact_number == "None":
                                    person.contact_number = student_already_exist.child_number
                                    person.save()
                                logger.info("Student Parents info exist Hubspot property assigned")
                                hubspot_student_parent_email_from_landing_exists="Yes"
                                #student_parent_details = StudentParentsDetail.objects.create(student=student,parent_name = student_already_exist.parent_name ,parent_email=student_already_exist.parent_email)
                                student_parent_details, created = StudentParentsDetail.objects.update_or_create(student=student,defaults={'parent_name': student_already_exist.parent_name,'parent_email':student_already_exist.parent_email})
                                student_parent_details.save()
                                hubspot_student_parent_email_from_landing = student_already_exist.parent_email
                                # hubspot_registration_parent_email = student_already_exist.parent_email
                                logger.info(f"Student Parents Details auto populated in ParentsInfo Table {email}")
                            else:
                                logger.info("Student Parents info not exist Hubspot property assigned")
                                hubspot_student_parent_email_missing_from_landing="Yes"
                                msg = str("The student - ") + str(email)  + str(" registered on the platform with company coupon and does not have any prior linked parent details")
                                # Add this opertion into celery
                                # subject = str("Parent Student Info Not Matched")
                                # fromEmail = settings.EMAIL_HOST_USER
                                # toEmail = "rohit@myfuturely.com"
                                # send_mail(subject, msg, fromEmail, [toEmail])
                                # logger.info(f"Student Does Not exist in our ParentsInfo Database {email} ")
                                logger.error(f"{msg}")

                except Exception as exp:
                    logger.error(f"Error -{exp}- to link student with parents info during registration for : {email}")
                if student and student.are_you_a_student == 'Yes':
                    obj_school_details = StudentSchoolDetail.objects.create(student=student, school_region=school_region, school_city=school_city, school_name=school_name, school_type=school_type, graduation_year=graduation_year)
                    if class_year:
                        try:
                            obj_class_year = ClassYear.objects.get(pk=class_year)
                            obj_school_details.class_year = obj_class_year
                        except Exception as exx:
                            print(str(exx))
                            logger.warning(f"Error of class-year at person-register-view {exx}: {email}")
                    if class_name:
                        try:
                            obj_class_name = ClassName.objects.get(pk=class_name)
                            obj_school_details.class_name = obj_class_name
                        except Exception as error:
                            print(str(error))
                            logger.warning(f"Error of class_name at person-register-view {error}: {email}")
                    if class_specialization:
                        try:
                            obj_class_specialization = Specialization.objects.get(pk=class_specialization)
                            obj_school_details.specialization = obj_class_specialization
                        except Exception as error:
                            print(str(error))
                            logger.warning(f"Error of class-specialization at person-register-view {error}: {email}")
                    obj_school_details.save()
                if bit_other_school:
                    School.objects.create(name=school_name, city = school_city, region = school_region, type = school_type, country= school_country)
                #if student and student.are_you_a_student == 'Yes' and school_region and school_city and school_name:
                #    School.objects.update_or_create(name=school_name, defaults={'city': school_city, 'region': school_region, 'type': school_type, 'country': school_country })
                
                submit_hubspot_form_with_email(request, email)
                
                try:
                    # hubspotContactupdateQueryAdded
                    if student.src == "future_lab":
                        is_future_lab_student="true"
                    else:
                        is_future_lab_student="false"   
                    local_tz = pytz.timezone(settings.TIME_ZONE)
                    dt_now = str(local_tz.localize(datetime.now()))
                    enrollDate=unixdateformat(datetime.now())
                    logger.info(f"In hubspot signup parameter building for : {person.username}")
                    keys_list = ['email','firstname', 'lastname', "hubspot_first_name", "course_country", "hubspot_are_you_a_student", "hubspot_check_tos", "hubspot_class_name",
                    "hubspot_class_specialization", "hubspot_class_year", "hubspot_contact_number", "hubspot_coupon_code_entered", "hubspot_email", "hubspot_how_know_us",
                    "hubspot_how_know_us_other", "hubspot_language_code", "hubspot_last_name", "hubspot_school_name", "hubspot_school_city", "hubspot_school_region", "hubspot_student_type",
                    "is_future_lab_student_registered", "is_student_registered", "hubspot_end_date_discount_code", "hubspot_enrollment_date",
                     "hubspot_registration_url","hubspot_gender","hubspot_gender_other","enroll_date","hubspot_school_type", "hubspot_is_for_fast_track_program","hubspot_is_from_fast_track_program","hubspot_registration_parent_email"]
                    values_list = [person.username,person.first_name,person.last_name, person.first_name, school_country, student.are_you_a_student, "Yes", class_name, class_specialization, class_year, person.contact_number, student.discount_coupon_code, person.email, person.how_know_us, person.how_know_us_other, school_country, person.last_name, obj_school_details.school_name,
                    obj_school_details.school_city,  obj_school_details.school_region, student.src, is_future_lab_student, True, str(discount_code_end_date), dt_now, self.request.build_absolute_uri(),
                    gender,gender_other,enrollDate,hubspot_school_type,hubspot_is_for_fast_track_program, hubspot_is_from_fast_track_program,hubspot_registration_parent_email]
                    is_from_registration_flow=None
                    keys_list_parents = ['email','is_a_parents','hubspot_is_for_fast_track_program','hubspot_is_from_fast_track_program']
                    values_list_parents = [hubspot_registration_parent_email,'true', hubspot_is_for_fast_track_program,hubspot_is_from_fast_track_program]
                    if hubspot_student_parent_email_missing_from_landing:
                        logger.info("Student Parents info not exist Hubspot property added in list")
                        keys_list.append('hubspot_student_parent_email_missing_from_landing')
                        values_list.append(hubspot_student_parent_email_missing_from_landing)
                    if hubspot_student_parent_email_from_landing_exists:
                        logger.info("Student Parents info exist Hubspot property added in list")
                        keys_list.append('hubspot_student_parent_email_from_landing_exists')
                        values_list.append(hubspot_student_parent_email_from_landing_exists)
                        keys_list.append('hubspot_student_parent_email_from_landing')
                        values_list.append(hubspot_student_parent_email_from_landing)
                        keys_list_parents.append('hubspot_is_from_landing')
                        values_list_parents.append(hubspot_student_parent_email_from_landing_exists)
                    else:
                        keys_list_parents.append('hubspot_is_from_landing')
                        values_list_parents.append('No')
                        keys_list_parents.append('is_from_registration_flow')
                        values_list_parents.append('Yes')
                    
                    create_update_contact_hubspot(person.username, keys_list, values_list)
                    logger.info(f"In hubspot signup parameter update completed for : {person.username}")
                    logger.info(f"In hubspot signup parameter update parent contact : {hubspot_registration_parent_email}")
                    create_update_contact_hubspot(hubspot_registration_parent_email, keys_list_parents, values_list_parents)

                except Exception as error:
                    logger.error(f"Error at hubspot signup parameter update {error} for : {person.username}")
                subject = _("Futurely - Verify your email address")
                login(request,person)
                request.session['notifymsg']=1
                request.session['display_welcome_video']=1
                if school_name:
                    create_custom_event(request, 2, meta_data={'school_name': school_name, 'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                    logger.info(f"Created custom event successfully for : {email}")
                else:
                    create_custom_event(request, 2, meta_data={'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                    logger.info(f"Created custom event successfully for : {email}")
                status=send_email_message(request,person,subject,email_html_content)
                if student.src == "future_lab":
                    StudentPCTORecord.objects.create(student=student, pcto_hours=1, pcto_hour_source="Future-lab")
                    logger.info(f"In Post request - futurelab registration stage 2 - Student PCTO hours added : {email}")
                    student.update_total_pcto_hour()
                if person:
                    notification_type_objs = Notification_type.objects.all()
                    for single_notification_type in notification_type_objs:
                        PersonNotification.objects.update_or_create(
                            person=person, notification_type=single_notification_type)
                
                if is_fully_paid_by_school_or_company == True and is_100_per_coupon_code == True:
                    # coupon_detail_obj = CouponDetail.objects.filter(coupon=coupon_obj).first()
                    cohort_program1 = None
                    cohort_program2 = None
                    cohort_program3 = None
                    plan_name_from_coupon = coupon_obj.plan_type
                    if plan_name_from_coupon == "Master":
                        plan_name_from_coupon = "Elite"
                    selected_plan = OurPlans.objects.filter(plan_lang=request.LANGUAGE_CODE, plan_name=plan_name_from_coupon).first()
                    if request.LANGUAGE_CODE == 'en-us':
                        currency = 'usd'
                    elif request.LANGUAGE_CODE == 'it':
                        currency = 'eur'
                    custom_user_session_id = request.session.get(
                        'CUSTOM_USER_SESSION_ID', '')
                    Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                                plan=selected_plan, coupon_code=coupon_obj.code, actual_amount=selected_plan.cost, discount=selected_plan.cost, custom_user_session_id=custom_user_session_id)
                    # Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                    #                         plan=selected_plan, coupon_code="", actual_amount="0", discount="0", custom_user_session_id=custom_user_session_id)
                    logger.info(f"payment obj updated for : {email} with 100 per coupon code {coupon_obj.code}")
                    stu_pln_obj, stu_pln_obj_created = StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(
                        student=person, plan_lang=request.LANGUAGE_CODE, defaults={'plans': selected_plan})
                    logger.info(f"student plan mapper obj update_or_create at signup for : {email}")
                    try:
                        if plan_name_from_coupon == "Premium":
                            cohort_program1 = coupon_detail_obj.cohort_program1
                        else:
                            cohort_program1 = coupon_detail_obj.cohort_program1
                            cohort_program2 = coupon_detail_obj.cohort_program2
                            if request.LANGUAGE_CODE == "it":
                                cohort_program3 = coupon_detail_obj.cohort_program3
                    except Exception as er:
                        logger.warning(f"Coupon code does not have any linked cohort - {er}: {email}")
                    if cohort_program1:
                        StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program1, stu_cohort_lang=request.LANGUAGE_CODE)
                        logger.info(f"student cohort mapper obj 1 created at signup for : {email}")
                        exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id])
                        # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id)
                        # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id)
                        request.session['is_first_time_on_dashboard'] = True
                    if cohort_program2:
                        StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program2, stu_cohort_lang=request.LANGUAGE_CODE)
                        logger.info(f"student cohort mapper obj 2 created at signup for : {email}")
                        exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id])
                        # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id)
                        # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id)
                    if cohort_program3:
                        StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program3, stu_cohort_lang=request.LANGUAGE_CODE)
                        logger.info(f"student cohort mapper obj 3 created at signup for : {email}")
                        exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id])
                        # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id)
                        # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id)
                    # student.discount_coupon_code = ""
                    student.save()
                    # Add celey task here for create step and step tracker.
                    # exercise_cohort_step_tracker_creation, 
                    # exercise_cohort_step_tracker

                    if(status == True):
                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                        logger.info(f"Email sent and User created Person-register-view page-post : {email}")
                    else:
                        Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                        context["message"] = _("Error to send mail to verify Email, Please check email id")
                        logger.error(f"Error Email not sent and user created Person-register-view page-post : {email}")
                    try:
                        # hubspotContactupdateQueryAdded
                        logger.info(f"In hubspot plan/cohort enroll signup building for : {request.user.username}")
                        if plan_name_from_coupon =='Premium':
                            if stu_pln_obj_created:
                                plan_created_at=str(stu_pln_obj.created_at)
                                premiumPlanEnrollDate=unixdateformat(stu_pln_obj.created_at)
                            else:
                                plan_created_at=str(stu_pln_obj.modified_at)
                                premiumPlanEnrollDate=unixdateformat(stu_pln_obj.modified_at)
                            coupon_end_date=unixdateformat(coupon_obj.end_date)
                            Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
                            keys_list = ["email","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount",
                            "hubspot_applied_discount_code",'hubspot_cohort_name_premium','premium_plan_enroll_date',
                            'end_date_discount_code','hubspot_cohort_premium_start_date']
                            values_list = [request.user.username, plan_created_at, "0",coupon_obj.code,cohort_program1.cohort_name,
                            premiumPlanEnrollDate,coupon_end_date,Hubspot_cohort_premium_start_date]
                            create_update_contact_hubspot(request.user.username, keys_list, values_list)

                            keys_list_parents = ['email','parents_cohort_premium_start_date']
                            values_list_parents = [hubspot_registration_parent_email,Hubspot_cohort_premium_start_date]
                            if is_from_fast_track_program:
                                keys_list_parents.append('parents_cohort_fasttrack_start_date')
                                values_list_parents.append(Hubspot_cohort_premium_start_date)
                            logger.info(f"In hubspot signup parameter update parent contact : {hubspot_registration_parent_email}")
                            create_update_contact_hubspot(hubspot_registration_parent_email, keys_list_parents, values_list_parents)

                        if plan_name_from_coupon =='Elite':
                            if stu_pln_obj_created:
                                plan_created_at=str(stu_pln_obj.created_at)
                                elitePlanEnrollDate=unixdateformat(stu_pln_obj.created_at)
                            else:
                                plan_created_at=str(stu_pln_obj.modified_at)
                                elitePlanEnrollDate=unixdateformat(stu_pln_obj.modified_at)
                            keys_list = ["email","elite_plan_enroll_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code"]
                            values_list = [request.user.username,elitePlanEnrollDate,plan_created_at, "0",coupon_obj.code]
                            keys_list_parents = ['email']
                            values_list_parents = [hubspot_registration_parent_email]

                            end_date_discount_code=unixdateformat(coupon_obj.end_date)
                            keys_list.append('end_date_discount_code')
                            values_list.append(end_date_discount_code)
                            if cohort_program1:
                                keys_list.append('hubspot_cohort_name_premium')
                                values_list.append(cohort_program1.cohort_name)
                                Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
                                keys_list.append('hubspot_cohort_premium_start_date')
                                values_list.append(Hubspot_cohort_premium_start_date)
                                keys_list_parents.append('parents_cohort_premium_start_date')
                                values_list_parents.append(Hubspot_cohort_premium_start_date)
                            if cohort_program2:
                                keys_list.append('hubspot_cohort_name_elite1')
                                values_list.append(cohort_program2.cohort_name)
                                Hubspot_cohort_elite1_start_date=unixdateformat(cohort_program2.starting_date)
                                keys_list.append('hubspot_cohort_elite1_start_date')
                                values_list.append(Hubspot_cohort_elite1_start_date)
                                # elite_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                                # keys_list.append('elite_plan_enroll_date')
                                # values_list.append(elite_plan_enroll_date)
                                keys_list_parents.append('parents_cohort_elite1_start_date')
                                values_list_parents.append(Hubspot_cohort_elite1_start_date)
                            if cohort_program3:
                                keys_list.append('hubspot_cohort_name_elite2')
                                values_list.append(cohort_program3.cohort_name)
                                Hubspot_cohort_elite2_start_date=unixdateformat(cohort_program3.starting_date)
                                keys_list.append('hubspot_cohort_elite2_start_date')
                                values_list.append(Hubspot_cohort_elite2_start_date)
                                keys_list_parents.append('parents_cohort_elite2_start_date')
                                values_list_parents.append(Hubspot_cohort_elite2_start_date)
                            
                            create_update_contact_hubspot(request.user.username, keys_list, values_list)
                            logger.info(f"In hubspot signup parameter update parent contact : {hubspot_registration_parent_email}")
                            if is_from_fast_track_program:
                                keys_list_parents.append('parents_cohort_fasttrack_start_date')
                                values_list_parents.append(Hubspot_cohort_premium_start_date)
                            create_update_contact_hubspot(hubspot_registration_parent_email, keys_list_parents, values_list_parents)
                        logger.info(f"hubspot plan/cohort enroll at signup complete for : {request.user.username}")
                    except Exception as ex:
                        logger.error(f"Error at hubspot plan/cohort enroll at signup  {ex} for : {request.user.username}")
                    # logger.info(f"Register User did not exist in Payment Model : {email} ")
                    is_from_mobile_app = request.session.get('is_from_mobile_app', False)
                    if is_from_mobile_app:
                        get_cohort = StudentCohortMapper.objects.filter(student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                        if get_cohort:
                            return HttpResponseRedirect(reverse("home")+ '?cohort_name='+get_cohort.cohort.cohort_name)
                    return redirect(reverse("home"))

                plan_from_landing_website = request.session.get('plan', '')
                if plan_from_landing_website == "trial2022":
                    return redirect('trail-plan-activate', plan_type="Community_to_Premium")
                # ################################################################################ #
                # ############# Check The User In Payment Model exist or not ##################### #
                # ################################################################################ #
                lang_code = request.LANGUAGE_CODE
                is_from_ios_app = request.session.get("is_from_ios_app", False)
                check_payment_obj = Payment.objects.filter(payment_email_id=email, status__in=["active", "succeeded"], plan__plan_lang=lang_code).order_by("-plan__id")
                if check_payment_obj.count() > 0:
                    one_time_payment_check_obj = check_payment_obj.filter(payment_subscription_type="One Time")
                    if one_time_payment_check_obj.count() > 0:
                        one_time_payment_obj = one_time_payment_check_obj.first()
                        if one_time_payment_obj.person is None:
                            # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                            StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=one_time_payment_obj.plan)
                            Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                            one_time_payment_obj.person = person
                            one_time_payment_obj.save()
                            logger.info(f"Register user mapped with StudentPlanMapper and Payment type(One Time) : {email}")
                            return HttpResponseRedirect(reverse("home"))
                    
                    weekly_person_pay_check_obj = check_payment_obj.filter(payment_subscription_type="Weekly")
                    if weekly_person_pay_check_obj.count() > 0:
                        for weekkly_obj in weekly_person_pay_check_obj:
                            pid_paysubdetail = weekkly_obj.paymentsubscriptiondetail.filter(invoice_status="paid")
                            if pid_paysubdetail.count() > 0:
                                if weekkly_obj.person is None:
                                    # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                    StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=weekkly_obj.plan)
                                    Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                    weekkly_obj.person = person
                                    weekkly_obj.save()
                                    break
                        logger.info(f"Register user mapped with StudentPlanMapper and Payment type(Weekly) : {email}")
                        return HttpResponseRedirect(reverse("home"))
                if(status == True):
                    Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                    logger.info(f"Email sent and User created Person-register-view page-post : {email}")
                else:
                    Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                    context["message"] = _("Error to send mail to verify Email, Please check email id")
                    logger.error(f"Error Email not sent and user created Person-register-view page-post : {email}")
                return HttpResponseRedirect(reverse("futurely-plans"))
            else:
                for form_errors_list in student_completion_form.errors.values():
                    for error in form_errors_list:
                        errors_list.append(error)
            print(f"Hello in stage 2 form not valid")
            context["student_completion_form"] = student_completion_form
            context['message'] = errors_list
            logger.error(f"Error Form not valid stage 2 : {email}")
            return render(request, "userauth/signup_next.html", context)

        else:
            message = []
            person_register_form = PersonRegisterForm(request_post)
            are_you_fourteen_plus = request_post.get('are_you_fourteen_plus', '')
            context["are_you_fourteen_plus"] = are_you_fourteen_plus
            context = signupstage1_placeholders(context)
            if are_you_fourteen_plus != 'Yes':
                message.append(_("Select correct option for 'Are you 14+?'"))
                context["person_register_form"] = person_register_form
                context["message"] = message
                logger.warning(f"Signup page stage 1 - user didn't Select correct option for 'Are you 14+' : {email_for_log}")
                return render(request, "userauth/signup.html", context)
            if person_register_form.is_valid():
                email = person_register_form.cleaned_data.get("email", None)
                gender = person_register_form.cleaned_data.get("gender", None)
                gender_other = person_register_form.cleaned_data.get("gender_other", '')
                submit_hubspot_form_with_email(request, email)
                password = person_register_form.cleaned_data.get(
                    "password", None)
                confirm_password = person_register_form.cleaned_data.get(
                    "confirm_password", None)
                first_name = person_register_form.cleaned_data.get(
                    "first_name", None)
                last_name = person_register_form.cleaned_data.get(
                    "last_name", None)
                contact_number = person_register_form.cleaned_data.get(
                    "contact_number", None)
                how_know_us = person_register_form.cleaned_data.get("how_know_us", None)
                how_know_us_other = person_register_form.cleaned_data.get(
                    "how_know_us_other", None)

                if password != confirm_password:
                    context["person_register_form"] = person_register_form
                    context['confirm_password_error'] = _("Confirm Password does not match")
                    return render(request, "userauth/signup.html", context)

                if gender == None :
                    context["person_register_form"] = person_register_form
                    context['person_gender_error'] = _("You must select before proceeding")
                    logger.warning(f"Signup page stage 1 - Didn't select 'Gender' : {email}")
                    return render(request, "userauth/signup.html", context)
                
                if how_know_us == None or how_know_us.strip() == '':
                    context["person_register_form"] = person_register_form
                    context["how_know_us_error"] = _("You must select before proceeding")
                    logger.warning(f"Signup page stage 1 - Didn't select 'How know us' : {email}")
                    return render(request, "userauth/signup.html", context)
                 
                if how_know_us == "Other" and (how_know_us_other == None or how_know_us_other.strip() == '') :
                    context["person_register_form"] = person_register_form
                    context["how_know_us_other_error"] = _("You must enter before proceeding")
                    logger.warning(f"Signup page stage 1 - Didn't enter 'How know us other' : {email}")
                    return render(request, "userauth/signup.html", context)

                if PERSON.objects.filter(Q(username__iexact=email)).exists():
                    context["person_register_form"] = person_register_form
                    context["email_error"] = _("The email already exists in the system")
                    logger.warning(f"Signup page stage 1 - E-mail already exists : {email}")
                    return render(request, "userauth/signup.html", context)
                try:
                    validate_password(password=password)
                except Exception as error:
                    logger.error(f"Error at PersonRegitrationView {error} : {email_for_log}")
                    # errors_list = []
                    # for form_errors_list in student_completion_form.errors.values():
                    #     for error in form_errors_list:
                    #         errors_list.append(error)
                    context["person_register_form"] = person_register_form
                    context["password_validation_errors"] = _("Your password must contain 1 uppercase, 1 lowercase, 1 numeric, and has at least 6 characters.")
                    logger.warning(f"Signup page stage 1 - Password is not valid : {email}")
                    return render(request, "userauth/signup.html", context)

                context['email'] = email
                context['password'] = password
                context['first_name'] = first_name
                context['last_name'] = last_name
                context['gender'] = gender
                context['contact_number'] = contact_number
                context['how_know_us'] = how_know_us
                context['how_know_us_other'] = how_know_us_other
                context['gender_other']= gender_other
                student_completion_form = StudentCompletionForm()
                context['student_completion_form'] = student_completion_form
                context['first_request'] = 'Yes'
                create_custom_event(request, 1, meta_data={'ctype':request.GET.get('ctype', 'general'), 'plan': request.GET.get('plan', '')})
                create_custom_event(request, 21, meta_data={'ctype':request.GET.get('ctype', 'general'), 'plan': request.GET.get('plan', '')})
                logger.info(f"Signup page stage 1 - create custom event for : {email}")
                logger.info(f"Signup page stage 1 successfully submitted : {email}")
                return render(request, "userauth/signup_next.html", context)
            else:
                print(person_register_form.errors.as_data())
                logger.warning(f"Signup page stage 1 - Form error 'For session' : {email_for_log}")
                logger.warning(f"Signup page stage 1 - Form error 'Form is not valid' : {person_register_form.errors.as_data()}")
            context["person_register_form"] = person_register_form
        return super(TemplateView, self).render_to_response(context)

def futurelab_register_create_custom_event(request):
    if request.method == "POST":
        request_post = request.POST
        email = request_post.get("email")
        logger.info(f"Custom event create for : {email}")
        create_custom_event(request, 1)
        return JsonResponse({"msg": "success"}, status=200, safe=False)
    return JsonResponse({"msg": "error"}, status=400, safe=False)

def email_sent_view(request):
    """This function for the send email."""
    return render(request, "userauth/email-verify-sent.html")

def email_not_verified_view(request):
    """this function for the email not verified."""
    return render(request, "userauth/email-not-verified.html")


def send_email_message(request, user, subject, template_nam):
    """
    this  function use for send mail and take  four argument request, user, subject,
    template then function is create a message then sent email.
    """
    try:
        #email_template_name = "userauth/email_content.html"

        email = user.email
        domain =  request.get_host()
        user_id = user.pk
        language_code = request.LANGUAGE_CODE
        send_email_message_task.apply_async(args=[email,domain,user_id,subject,language_code,template_nam])

        logger.info(f"E-Mail sent Successfully for : {user.username}")
        return True
    except Exception as ex:
        logger.error(f"Error occurred in send_email_message function for: {user.username}. Error: {str(ex)}")
        return False

def email_verify_view(request):
    """
    this function for the email verification.
    """
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    if(request.method == 'POST'):
        form = EmailVerifyForm(request.POST)
        if(form.is_valid()):
            data = form.cleaned_data['email']
            associated_users = PERSON.objects.filter(Q(email=data))
            if(associated_users.exists()):
                for user in associated_users:
                    subject = _("Futurely - verify your email address")
                    if request.LANGUAGE_CODE == 'it':
                        status = send_email_message(request, user, subject, 'userauth/email_content-it.html')
                    else:
                        status = send_email_message(request, user, subject, 'userauth/email_content.html')
                    if(status == True):
                        logger.info(f"Mail sent for email verification at email verify view for : {user.username}")
                        return HttpResponseRedirect(reverse("email-sent"))
                    else:
                        msg = _("Error to send an email, please check email address or try again")
                        logger.warning(f"Error Email not sent in email verify view : {user.username}")
                        return render(request, "userauth/email-forwarding.html", {'form': form, 'message': msg})
            else:           
                msg = _("Invalid email")
                return render(request, "userauth/email-forwarding.html", {'form': form,'message': msg})
        else:
            return render(request, "userauth/email-forwarding.html", {'form': form})
    else:
        form = EmailVerifyForm()
        logger.info(f"Email-verify-view visited by : {custom_user_session_id}")
        return render(request, "userauth/email-forwarding.html", {'form': form})

def auto_link_to_cohort(obj_student,coupon_obj,plan_lang,plan_name):
    cohort_program1 = None
    cohort_program2 = None
    cohort_program3 = None
    keys_list = []
    values_list = []
    coupon_detail_obj = CouponDetail.objects.filter(coupon=coupon_obj).first()
    if coupon_detail_obj:
        if plan_name == "Premium":
            if coupon_detail_obj.cohort_program1:
                cohort_program1 = coupon_detail_obj.cohort_program1
        else:
            if coupon_detail_obj.cohort_program1:
                cohort_program1 = coupon_detail_obj.cohort_program1
            if coupon_detail_obj.cohort_program2:
                cohort_program2 = coupon_detail_obj.cohort_program2
            if plan_lang == "it":
                if coupon_detail_obj.cohort_program3:
                    cohort_program3 = coupon_detail_obj.cohort_program3
        if cohort_program1:
            StudentCohortMapper.objects.create(student=obj_student, cohort=cohort_program1, stu_cohort_lang=plan_lang)
            logger.info(f"student cohort mapper obj 1 created at signup for : {obj_student.username}")
            keys_list.append('hubspot_cohort_name_premium')
            values_list.append(cohort_program1.cohort_name)
            Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
            keys_list.append('hubspot_cohort_premium_start_date')
            values_list.append(Hubspot_cohort_premium_start_date)
        if cohort_program2:
            StudentCohortMapper.objects.create(student=obj_student, cohort=cohort_program2, stu_cohort_lang=plan_lang)
            logger.info(f"student cohort mapper obj 2 created at signup for : {obj_student.username}")
            keys_list.append('hubspot_cohort_name_elite1')
            values_list.append(cohort_program2.cohort_name)
            Hubspot_cohort_elite1_start_date=unixdateformat(cohort_program2.starting_date)
            keys_list.append('hubspot_cohort_elite1_start_date')
            values_list.append(Hubspot_cohort_elite1_start_date)
        if cohort_program3:
            StudentCohortMapper.objects.create(student=obj_student, cohort=cohort_program3, stu_cohort_lang=plan_lang)
            logger.info(f"student cohort mapper obj 3 created at signup for : {obj_student.username}")
            keys_list.append('hubspot_cohort_name_elite2')
            values_list.append(cohort_program3.cohort_name)
            Hubspot_cohort_elite2_start_date=unixdateformat(cohort_program3.starting_date)
            keys_list.append('hubspot_cohort_elite2_start_date')
            values_list.append(Hubspot_cohort_elite2_start_date)
    return keys_list, values_list

@login_required(login_url="/login/")
def user_from_ios_view(request,plan_name):
    is_from_mobile_app = request.session.get('is_from_mobile_app',False)
    if is_from_mobile_app:
        try:
            email = request.user.username
            logger.info(f"User entered in IOS view to unlock plan and cohort : {email}")
            if request.LANGUAGE_CODE == 'en-us':
                currency = 'usd'
            elif request.LANGUAGE_CODE == 'it':
                currency = 'eur'
            student = request.user.student
            coupon_code = student.discount_coupon_code
            coupon_obj = Coupon.objects.filter(code = coupon_code).first()
            keys_list_1 = []
            values_list_1 = []
            if coupon_obj:
                logger.info(f"User entered in IOS view , Coupon code found : {email}")
                custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
                selected_plan = OurPlans.objects.filter(plan_lang=request.LANGUAGE_CODE, plan_name=plan_name).first()
                if selected_plan:
                    logger.info(f"User entered in IOS view ,  plan found : {email}")
                    current_plan_mapper = StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).filter(student=request.user, plan_lang=request.LANGUAGE_CODE,plans=selected_plan).first()
                    if current_plan_mapper is None:
                        Payment.objects.create(stripe_id='paid_from_ios_app', amount="0", currency=currency, status='succeeded', person=request.user,
                                    plan=selected_plan, coupon_code=coupon_obj.code, actual_amount=selected_plan.cost, discount=selected_plan.cost, custom_user_session_id=custom_user_session_id)
                        # logger.info(f"payment obj updated for : {email} with 100 per coupon code {coupon_obj.code}")
                        stu_pln_obj, stu_pln_obj_created = StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(
                            student=request.user, plan_lang=request.LANGUAGE_CODE, defaults={'plans': selected_plan})
                        # logger.info(f"student plan mapper obj update_or_create at signup for : {email}")
                        keys_list_1, values_list_1 = auto_link_to_cohort(request.user,coupon_obj,request.LANGUAGE_CODE,selected_plan.plan_name)
                        try:
                            # hubspotContactupdateQueryAdded
                            logger.info(f"In hubspot plan enroll details from ios app for : {email}")
                            if stu_pln_obj.plan_name =='Premium':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    premium_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    premium_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                                upgrade_date=premium_plan_enroll_date
                                keys_list = ["email","upgrade_date","premium_plan_enroll_date","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount","hubspot_applied_discount_code"] + keys_list_1
                                values_list = [email,upgrade_date,premium_plan_enroll_date, plan_created_at, "0",coupon_code] + values_list_1
                                create_update_contact_hubspot(email, keys_list, values_list)
                            if stu_pln_obj.plan_name =='Elite':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    elite_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    elite_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                                upgrade_date=elite_plan_enroll_date
                                keys_list = ["email","upgrade_date","elite_plan_enroll_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code"] + keys_list_1
                                values_list = [email,upgrade_date,elite_plan_enroll_date,plan_created_at, "0",coupon_code] + values_list_1
                                create_update_contact_hubspot(email, keys_list, values_list)
                            logger.info(f"In hubspot plan enroll intent webhook parameter update completed for : {email}")
                        except Exception as ex:
                            logger.error(f"Error at hubspot plan enroll intent webhook parameter update {ex} for : {email}")
                else:
                    logger.error(f"Error - User in IOS view ,  plan not found : {email}")
        except Exception as ex:
            logger.error(f"Error - User in IOS view : {email} - {ex}")
    return HttpResponseRedirect(reverse("home"))

class EmailActivateView(View):
    """
    This function for the email verification activated.
    """
    def get(self, request, uidb64, token):
        status=False
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = PERSON.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, PERSON.DoesNotExist):
            logger.warning(f"user does not exist at Email-Activate-view for : {uid}")
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            if request.user.is_authenticated:
                status=True
                logger.info(f"Email verification done : {request.user.username}")
                logout(request)
            user.email_verified = True
            user.save()
            Stu_Notification.objects.create(student=user, title=_("Congratulations, your email address has been linked to your account"))
            if status == True:
                login(request,user)
                logger.info(f"Email Address has been linked at Email-activate-view for : {user.username}")
            return render(request, "userauth/email-activation-status.html")
        else:
            # invalid link
            msg = _("Verification link is already used or expired")
            logger.info(f"Verification link is already used or expired : {user}")
            return render(request, "userauth/email-activation-status.html", {'message': msg})
            # return render(request, 'userauth/email-not-verified.html')  

def coupon_code_exists(request):
    """This function check the coupon code exists or not and this function use with ajax call."""
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        if request.method == "POST" and request.is_ajax:
            data = {}
            request_post = request.POST
            coupon_code = request_post.get('coupon_code', None)
            ctype = request.session.get('ctype', None)
            coupon_code_exist = None
            if coupon_code:
                local_tz = pytz.timezone(settings.TIME_ZONE)
                dt_now = local_tz.localize(datetime.now())
                if ctype and ctype == 'future_lab':
                    coupon_code_exist = Coupon.objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code))
                    #coupon_code_exist = Coupon.futurelab_company_objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code), Q(coupon_type='FutureLab'))
                elif ctype and ctype == 'company':
                    coupon_code_exist = Coupon.objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code))
                    #coupon_code_exist = Coupon.futurelab_company_objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code), Q(coupon_type='Organization'))
                else:
                    coupon_code_exist = Coupon.objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code))
                if coupon_code_exist and len(coupon_code_exist) > 0:
                    logger.info(f"check coupon code at coupon_code_exists for : {coupon_code}")
                    return JsonResponse({'message': 'success'}, status=200, safe=False)
            else:
                logger.warning(f"coupon code is None at coupon_code_exists : {custom_user_session_id}")
        return JsonResponse({'message': 'error'}, status=200, safe=False)
    except Exception as error:
        print(error)
        logger.warning(f"Error in coupon-code-exists {error}: {custom_user_session_id}")
        return JsonResponse({'error': str(error)}, status=403, safe=False)



def get_school_details_by_name(request):
    """
    this function get school school details by the name and function work
    with ajax call, then return the exact values of school details.
    """
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        if request.method == "POST" and request.is_ajax:
            request_post = request.POST
            school_name = request_post.get('school_name', None)
            if school_name:
                obj_school = School.objects.filter(Q(name__iexact=school_name))
                if obj_school:
                    logger.info(f"get school details by the school name - {school_name} : {custom_user_session_id}")
                    return JsonResponse({'message': 'success', 'school_name': obj_school[0].name, 'school_region': obj_school[0].region, 'school_type': obj_school[0].type, 'school_city': obj_school[0].city}, status=200, safe=False)
        logger.warning(f"Error in get schhol details by name : {custom_user_session_id}")
        return JsonResponse({'message': 'error'}, status=200, safe=False)
    except Exception as error:
        print(error)
        logger.error(f"Error get school details by name {error} : {custom_user_session_id}")
        return JsonResponse({'error': str(error)}, status=403, safe=False)

def get_school_cities_by_region(request):
    """
    this function get school cities by the region and function work
    with ajax call, then return the exact values of country details.
    """
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        if request.method == "POST" and request.is_ajax:
            request_post = request.POST
            school_region = request_post.get('school_region', None)
            if school_region:
                obj_school = CountryDetails.objects.filter(Q(region__iexact=school_region))
                if obj_school:
                    all_cities = list(obj_school.order_by('city').values_list('city', flat=True).distinct())
                    print(all_cities)
                    return JsonResponse({'message': 'success', 'all_cities': all_cities, 'school_region': school_region }, status=200, safe=False)
        logger.warning(f"Error in get schhol, cities by region name : {custom_user_session_id}")
        return JsonResponse({'message': 'error'}, status=200, safe=False)
    except Exception as error:
        print(error)
        logger.error(f"Error get school cities by region {error} : {custom_user_session_id}")
        return JsonResponse({'error': str(error)}, status=403, safe=False)

def get_school_names_by_city_and_region(request):
    """
    This function fetch school names by city and region
    """
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        if request.method == "POST" and request.is_ajax:
            request_post = request.POST
            school_region = request_post.get('school_region', None)
            school_city = request_post.get('school_city', None)
            print(school_region)
            print(school_city)
            if school_region and school_city:
                obj_school = School.objects.filter(Q(region__iexact=school_region),Q(city__iexact=school_city),Q(is_verified=True))
                if obj_school:
                    all_schools = list(obj_school.order_by('name').values_list('name',flat=True).distinct())
                    lst_schools = []
                    for sch in all_schools:
                        lst_schools.append(html.escape(sch))
                    logger.info(f"get-school-name-by-city-and-region for : {custom_user_session_id}")
                    return JsonResponse({'message': 'success', 'all_schools': lst_schools, 'school_region': school_region }, status=200, safe=False)
                else:
                    lst_schools = []
                    logger.info(f"get-school-name-by-city-and-region for : {custom_user_session_id}")
                    return JsonResponse({'message': 'success',  'school_region': school_region, 'all_schools': lst_schools }, status=200, safe=False)
        logger.warning(f"Error in get schhol name by city and region name : {custom_user_session_id}")
        return JsonResponse({'message': 'error'}, status=200, safe=False)
    except Exception as error:
        print(error)
        logger.warning(f"get school names by city and region {error} : {custom_user_session_id}")
        return JsonResponse({'error': str(error)}, status=403, safe=False)

class CounselorRegistrationView(UserPassesTestMixin, TemplateView):
    """
    this is the class of CounselorRegistrationView for registraion.
    """
    template_name = "userauth/counselor_registration.html"

    def test_func(self):
        if not self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    def get(self, request, *args, **kwargs):
        """this is the get method of CounselorRegistrationView and accepts the get requests"""
        context = {} #super(PersonRegistrationView, self).get_context_data(*args, **kwargs)
        ctype = self.request.GET.get('ctype', None)
        self.request.session['ctype'] = ctype if ctype else 'general'
        context["person_register_form"] = CounselorRegisterForm()
        if request.LANGUAGE_CODE == 'en-us':
            school_country = 'USA'
            all_schools = CountryDetails.objects.filter(country='USA')
            if ctype == "company":
                all_companies = Company.objects.filter(country='USA')
                context['companies'] = all_companies
        elif request.LANGUAGE_CODE == 'it':
            school_country = 'Italy'
            all_schools = CountryDetails.objects.filter(country='Italy')
            if ctype == "company":
                all_companies = Company.objects.filter(country='Italy')
                context['companies'] = all_companies
        
        context['school_regions'] = all_schools.order_by('region').values('region').distinct()
        
        context = signupstage1_placeholders(context)
        print(context['school_regions'])
        logger.info(f"user render at counselorRegistrationView")
        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """this is the post method of CounselorRegistrationView and accepts the post requests"""
        context = {}
        request_post = request.POST
        all_companies = []
        ctype = self.request.session.get('ctype', None)
        clarity_token = self.request.session.get('clarity_token', '')
        company_obj = ""
        person_register_form = CounselorRegisterForm(request_post)
        if person_register_form.is_valid():
            errors_list = []
            email = person_register_form.cleaned_data.get("email", None)
            gender = person_register_form.cleaned_data.get("gender", None)
            password = person_register_form.cleaned_data.get(
                "password", None)
            first_name = person_register_form.cleaned_data.get(
                "first_name", None)
            last_name = person_register_form.cleaned_data.get(
                "last_name", None)
            contact_number = person_register_form.cleaned_data.get(
                "contact_number", None)
            how_know_us = person_register_form.cleaned_data.get("how_know_us", None)
            how_know_us_other = person_register_form.cleaned_data.get(
                "how_know_us_other", None)
            gender_other = person_register_form.cleaned_data.get(
                "gender_other", '')
            school_name = request_post.get('school-name')
            school_city = request_post.get('school-city')
            school_region=request_post.get('school-region')
            company_name=request_post.get('company-name')
            # context['first_name'] = first_name
            # context['last_name'] = last_name
            # context['email'] = email
            # context['password'] = password
            # context['contact_number'] = contact_number
            # context['how_know_us'] = how_know_us
            # context['how_know_us_other'] = how_know_us_other
            if how_know_us == None or how_know_us.strip() == '':
                context["person_register_form"] = person_register_form
                context["how_know_us_error"] = _("You must select before proceeding")
                logger.warning(f"Didn't select the option of 'how_know_us' in counselor registration view-post : {email}")
                return render(request, "userauth/counselor_registration.html", context)
            if ctype == "company":
                print(f"Ctype >>>>>> : {ctype}")
                if(company_name == ""):
                    context["person_register_form"] = person_register_form
                    context["how_know_us_error"] = _("You must select before proceeding")
                    logger.warning(f"Didn't select the option of 'company' in counselor registration view-post : {email}")
                    return render(request, "userauth/counselor_registration.html", context)
                else:
                    company_obj = Company.objects.get(pk=company_name)
            else:
                if(school_region == ""):
                    context['school_region_message'] = _('You must select before proceeding')
                    context['school_city_message'] = _('You must select before proceeding')
                    context['school_name_message'] = _('You must select before proceeding')
                    context["person_register_form"] = person_register_form
                    logger.warning(f"Didn't select the option of 'school_region' in counselor registration view-post : {email}")
                    return render(request, "userauth/counselor_registration.html", context)
                elif(school_city == ""):
                    context['school_city_message'] = _('You must select before proceeding')
                    context['school_name_message'] = _('You must select before proceeding')
                    context["person_register_form"] = person_register_form
                    logger.warning(f"Didn't select the option of 'school_city' in counselor registration view-post : {email}")
                    return render(request, "userauth/counselor_registration.html", context)
                elif(school_name == ""):
                    context['school_name_message'] = _('You must select before proceeding')
                    context["person_register_form"] = person_register_form
                    logger.warning(f"Didn't select the option of 'school_name' in counselor registration view-post : {email}")
                    return render(request, "userauth/counselor_registration.html", context)
                elif(gender == None):
                    context["gender_error"] = _('You must select before proceeding')
                    context["person_register_form"] = person_register_form
                    logger.warning(f"Didn't select the option of 'Gender' in counselor registration view-post : {email}")
                    return render(request, "userauth/counselor_registration.html", context)
            
            if how_know_us == "Other" and (how_know_us_other == None or how_know_us_other.strip() == '') :
                context["person_register_form"] = person_register_form
                context["how_know_us_other_error"] = _("You must enter before proceeding")
                logger.warning(f"Didn't select the option of 'how_know_us_other' in counselor registration view-post : {email}")
                return render(request, "userauth/counselor_registration.html", context)

            if PERSON.objects.filter(Q(username__iexact=email)).exists():
                context["person_register_form"] = person_register_form
                context["email_error"] = _("The email already exists in the system")
                logger.warning(f"Error counselor register - the email already exists : {email}")
                return render(request, "userauth/counselor_registration.html", context)
            try:
                validate_password(password=password)
            except Exception as e:
                print(e)
                errors_list = []
                # for err in e.error_list:
                #     errors_list.extend(err)
                for form_errors_list in person_register_form.errors.values():
                    for error in form_errors_list:
                        errors_list.append(error)
                context["student_completion_form"] = person_register_form
                context["person_register_form"] = person_register_form
                context["password_validation_errors"] = _("Your password must contain 1 uppercase, 1 lowercase, 1 numeric, and has at least 6 characters.")
                logger.warning(f"counselor register - Password error {e}: {email}")
                return render(request, "userauth/counselor_registration.html", context)
            person = None
            try:
                person = PERSON.objects.create_user(first_name=first_name, last_name=last_name, username=email, email=email, password=password, contact_number=contact_number,how_know_us=how_know_us,how_know_us_other=how_know_us_other, gender=gender, gender_other=gender_other, lang_code=request.LANGUAGE_CODE,clarity_token=clarity_token)
                if ctype == "company":
                    counselor = Counselor.objects.create(person=person, company=company_obj)
                    logger.info(f"Counselor account created with company name: {email}")
                else:
                    counselor = Counselor.objects.create(person=person,school_name=school_name,school_region=school_region,school_city=school_city)
                    logger.info(f"Counselor account created with school details : {email}")
                submit_hubspot_form_with_email(request, email)
            except Exception as e:
                print(e)
                logger.error(f"Error counselor register - Email is already exists {e} : {email}")
                # context["message"] = [f"The email {email} already exists in the system."]
                context["person_register_form"] = CounselorRegisterForm()
                context = signupstage1_placeholders(context)
                return render(request, "userauth/counselor_registration.html", context)
            subject = _("Futurely - Verify your email address")
            login(request,person)
            request.session['notifymsg']=1
            if request.LANGUAGE_CODE == 'it':
                status=send_email_message(request,person,subject,"userauth/email_content-it.html")
            else:
                status=send_email_message(request,person,subject,"userauth/email_content.html")
            if person:
                notification_type_objs = Notification_type.objects.all()
                for single_notification_type in notification_type_objs:
                    PersonNotification.objects.update_or_create(
                        person=person, notification_type=single_notification_type)
            if(status == True):
                Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                logger.info(f"Email sent - counselor register - Account created : {person.username}")
            else:
                Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                context["message"] = _("Error to send mail to verify Email, Please check email id")
                logger.error(f"Error to send mail, email id is not valid at couselorRegisterationView for : {person.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        else:
            errors_list = []
            for form_errors_list in person_register_form.errors.values():
                for error in form_errors_list:
                    errors_list.append(error)

            context["student_completion_form"] = person_register_form
            context['message'] = errors_list
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
            logger.error(f"Form validation error at couselorRegistrationView page : {custom_user_session_id}")
            return render(request, "userauth/counselor_registration.html", context)




class CounselorLoginView(TemplateView):
    """Counselor Login View >>> Only counselor login this class """

    def post(self, request, *args, **kwargs):
        """this is the post method of counselor login view."""
        username = request.POST.get("username")
        password = request.POST.get("password")
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("counselor_program"))
        try:
            user = PERSON.objects.get(Q(username=username))
            user = authenticate(username=user.username, password=password)
        except PERSON.DoesNotExist:
            logger.warning(f"User does Not exist at CounselorLoginView : {username}")
            user = None
        if user is not None and user.check_password(password):
            try:
                #counselor=Counselor.objects.get(person=user)
                if user.person_role == "Counselor":
                    login(request, user)
                    logger.info(f"User looged in successfully at CounselorLoginView for : {user.username}")
                    clarity_token = self.request.session.get('clarity_token', '')
                    logger.info(f"Clarity token collected from session for : {user.username}")
                    user.clarity_token = clarity_token
                    user.save()
                    submit_hubspot_form_with_email(request, username)
                else:
                    context = {"message": _("Login failed: Invalid username or password")}
                    logger.warning(f"Invalid username or password counselor login : {request.user.username}")
                    return render(request, "userauth/counselor_login.html", context)
            except Exception as error:
                print(error)
                context = {"message": _("Login failed: Invalid username or password")}
                logger.error(f"Error counselor login {error} : {username}")
                return render(request, "userauth/counselor_login.html", context)
            request.session['notifymsg'] = 1
            create_custom_event(request, 3)
            company_name = request.user.counselor.company
            if company_name is not None:
                request.session['is_login_for_company'] = True
            logger.info(f"Counselor Login - Successfully and Redirected to counselor-search : {request.user.username}")
            return HttpResponseRedirect(reverse("counselor_program"))

        else:
            create_custom_event(request, 4)
            context = {"message": _(
                "Login failed: Invalid username or password")}
            logger.warning(f"Error Login Failed: Invalid username and password : {request.user.username}")
            return render(request, "userauth/counselor_login.html", context)

    def get(self, request, *args, **kwargs):
        """This is the GET method of the couselor login view."""
        if request.user.is_authenticated:
            user_name = request.user.username
            if request.user.person_role == "Futurely_admin":
                user_name = request.user.username
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("admin_dashboard"))
            elif request.user.person_role == "Counselor":
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("counselor_program"))
            else:
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("home"))
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"counselor-Login page visited by : {custom_user_session_id}")
        return render(request, "userauth/counselor_login.html")

class AdminLoginView(TemplateView):
    """ Futurely Admin Login View >>> Only admin login this class """

    def post(self, request, *args, **kwargs):
        """this is the post method of counselor login view."""
        username = request.POST.get("username")
        password = request.POST.get("password")
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        try:
            user = PERSON.objects.get(Q(username=username))
            user = authenticate(username=user.username, password=password)
        except PERSON.DoesNotExist:
            logger.warning(f"User does Not exist at CounselorLoginView : {username}")
            user = None
        if user is not None and user.check_password(password):
            try:
                #counselor=Counselor.objects.get(person=user)
                if user.person_role == "Futurely_admin":
                    login(request, user)
                    logger.info(f"User looged in successfully at CounselorLoginView for : {user.username}")
                    submit_hubspot_form_with_email(request, username)
                else:
                    context = {"message": _("Login failed: Invalid username or password")}
                    logger.warning(f"Invalid username or password counselor login : {request.user.username}")
                    return render(request, "userauth/futurely_admin_login.html", context)
            except Exception as error:
                print(error)
                context = {"message": _("Login failed: Invalid username or password")}
                logger.error(f"Error Admin login {error} : {username}")
                return render(request, "userauth/futurely_admin_login.html", context)
            request.session['notifymsg'] = 1
            create_custom_event(request, 3)
            logger.info(f"Admin Login - Successfully and Redirected to Admin-dashboard : {request.user.username}")
            return HttpResponseRedirect(reverse("admin_dashboard"))

        else:
            create_custom_event(request, 4)
            context = {"message": _(
                "Login failed: Invalid username or password")}
            logger.warning(f"Error Login Failed: Invalid username and password : {request.user.username}")
            return render(request, "userauth/futurely_admin_login.html", context)

    def get(self, request, *args, **kwargs):
        """This is the GET method of the couselor login view."""
        if request.user.is_authenticated:
            user_name = request.user.username
            if request.user.person_role == "Futurely_admin":
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("admin_dashboard"))
            elif request.user.person_role == "Counselor":
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
            else:
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("home"))
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"counselor-Login page visited by : {custom_user_session_id}")
        return render(request, "userauth/futurely_admin_login.html")


class LoginView(TemplateView):
    """This is the Student login view class and this class have two method ex: GET and POST."""

    def post(self, request, *args, **kwargs):
        """This is the post method of Login view and accepts only POST requests."""
        is_from_ios_app = request.session.get("is_from_ios_app",False)
        username = request.POST.get("username")
        password = request.POST.get("password")
        if request.user.is_authenticated:
            student = self.request.user.username
            logger.info(f"Redirected to home page from login-view for : {student}")
            is_from_mobile_app = request.session.get('is_from_mobile_app', False)
            if is_from_mobile_app:
                get_cohort = StudentCohortMapper.objects.filter(student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                if get_cohort:
                    return HttpResponseRedirect(reverse("home")+ '?cohort_name='+get_cohort.cohort.cohort_name)
            return HttpResponseRedirect(reverse("home"))
        try:
            user = PERSON.objects.get(Q(username=username))
            user = authenticate(username=user.username, password=password)

        except PERSON.DoesNotExist:
            logger.warning(f"User does Not exist at LoginView : {username}")
            user = None
        if user is not None and user.check_password(password):
            try:
                student=Student.objects.get(person=user)
                login(request, user)
                request.session['is_from_ios_app'] = is_from_ios_app
                logger.info(f"User looged in successfully at LoginView for : {user.username}")
                clarity_token = self.request.session.get('clarity_token', '')
                logger.info(f"Clarity token collected from session for : {user.username}")
                user.clarity_token = clarity_token
                user.save()
                # submit_hubspot_form_with_email(request, username)
                # hubspotutk = request.COOKIES.get('hubspotutk', '')
                # submit_hubspot_for_login.delay([username, hubspotutk])
                # schedule, created = IntervalSchedule.objects.get_or_create(
                # PeriodicTasks.objects.get_or_create()
            except Exception as err:
                context = {"message": _(
                "Login failed: Invalid username or password")}
                logger.error(f"Error Login failed {err}: {username}")
                return render(request, "userauth/login-new.html", context)
            request.session['notifymsg'] = 1
            create_custom_event(request, 3, username)
            logger.info(f"After logged In Redirected to Dashboard at LoginView : {username}")
            is_from_mobile_app = request.session.get('is_from_mobile_app', False)
            if is_from_mobile_app:
                get_cohort = StudentCohortMapper.objects.filter(student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                if get_cohort:
                    return HttpResponseRedirect(reverse("home")+ '?cohort_name='+get_cohort.cohort.cohort_name)
            return HttpResponseRedirect(reverse("home"))
        else:
            create_custom_event(request, 4, username)
            context = {"message": _(
                "Login failed: Invalid username or password")}
            logger.warning(f"Login failed - invalid username and password : {username}")
            return render(request, "userauth/login-new.html", context)

    def get(self, request, *args, **kwargs):
        """This is  GET method of student login view and this method accepts only GET requests."""
        if request.user.is_authenticated:
            user_name = request.user.username
            if request.user.person_role == "Student":
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.user.person_role == "Counselor":
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
            else:
                logger.info(f"Redirected to couselor-dashboard from couselor-login view for : {user_name}")
                return HttpResponseRedirect(reverse("admin_dashboard"))
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"Login page visited by : {custom_user_session_id}")
        # local_tz = pytz.timezone(settings.TIME_ZONE)
        # date_now = local_tz.localize(datetime.datetime.now() )
        # dt_new = date_now + datetime.timedelta(seconds=60)
        hubspotutk = request.COOKIES.get('hubspotutk', '')
        email = "rohitkbti007@gmail.com"
        schedule, created = CrontabSchedule.objects.get_or_create(hour = 6, minute = 24)
        # schedule, created = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.SECONDS)
        # task = PeriodicTask.objects.create(crontab=schedule, name="submit_hubspot_for_login_"+"1", task='userauth.tasks.submit_hubspot_for_login',  args = json.dumps([email,hubspotutk]))
        # task_1 = PeriodicTask.objects.update_or_create(name="submit_hubspot_for_login_"+"1", defaults={'crontab': schedule, "task": "userauth.tasks.submit_hubspot_for_login", 'args': json.dumps([email,hubspotutk])})
        task_2 = PeriodicTask.objects.update_or_create(name="test_func_tas_"+"1", defaults={'crontab': schedule, "task": "userauth.tasks.test_func_task", "args": json.dumps([email,hubspotutk]), "kwargs":json.dumps({"email": email, "hubspotutk": hubspotutk}), 'one_off': True})
        return render(request, "userauth/login-new.html")


class LogoutView(TemplateView):
    """This is Logout view class"""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            lang = request.session.get('lang', None)
            is_from_ios_app = request.session.get("is_from_ios_app", False)
            current_user=request.user.person_role
            user_name = request.user.username
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            is_from_mobile_app = request.session.get('is_from_mobile_app',False)
            logout(request)
            request.session['lang'] = lang
            request.session['is_from_mobile_app'] = is_from_mobile_app
            request.session['CUSTOM_USER_SESSION_ID'] = custom_user_session_id
            request.session['is_from_ios_app'] = is_from_ios_app
            if current_user == "Counselor":
                logger.info(f"{current_user} logout successfully : {user_name}")
                # return HttpResponseRedirect(reverse("counselor_login"))
                return HttpResponseRedirect(reverse("login") + f"?is_counselor=Yes")
            elif current_user == "Futurely_admin":
                logger.info(f"{current_user} logout successfully : {user_name}")
                return HttpResponseRedirect(reverse("admin_login"))
            logger.info(f"User logout successfully : {user_name}")
            return HttpResponseRedirect(reverse("login"))
        else:
            return HttpResponseRedirect(reverse('login'))


class SetPasswordView(PasswordResetConfirmView):
    """This is set password view."""
    form_class = PasswordSetForm
    # custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
    # logger.info(f"Password Reseting at Set-password-view")
    # success_url=reverse_lazy('password_success')


def password_reset(request):
    """THis is password reset function."""
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    if(request.method == "POST"):
        form = PasswordResttingForm(request.POST)
        if(form.is_valid()):
            data = form.cleaned_data['email']
            associated_users = PERSON.objects.filter(Q(email=data))
            if(associated_users.exists()):
                for user in associated_users:
                    subject = _("Password reset requested")
                    status = send_email_message(
                        request, user, subject, 'userauth/pass_reset/password_reset_email.html')
                    """
                    c={
                        "email":user.email,
                        "domain":'127.0.0.1:8000',
                        'site_name':'tecsbti.com',
                        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                        "user":user,
                        "token":default_token_generator.make_token(user),
                        "protocol":'http',
                    }
                    email=render_to_string(email_template_name,c)
                    try:
                        fromEmail=settings.EMAIL_HOST_USER
                        print(fromEmail)
                        print(user.email)
                        send_mail(subject, email, fromEmail, [user.email], fail_silently=False)
                        print("done email")
                    except BadHeaderError:
                        return HttpResponse('Invalid Header found.')
                    """
                    if(status == True):
                        logger.info(f"Sent email at password_reset for : {user.username}")
                        return redirect("/password_reset/done/")
                    else:
                        msg = _(
                            "Please try again later")
                        logger.error(f"Email not sent at password_reset for : {user.username}")
                        return render(request, "userauth/pass_reset/password_reset_form.html", {'form': form, 'message': msg})
            else:
                msg = _(
                    "Email address is not registered")
                logger.warning(f"Email address is not registed at password_reset : {data}")
                return render(request, "userauth/pass_reset/password_reset_form.html", {'form': form, 'message': msg})
    else:
        form = PasswordResttingForm()
        logger.info(f"Password reset page visited by : {custom_user_session_id}")
        return render(request, "userauth/pass_reset/password_reset_form.html", {'form': form})

def check_email_view(request):
    """this function is check email view in Person model, email exist or not."""
    if request.method == "POST" and request.is_ajax:
        is_exists = False
        email = request.POST.get('email', "")
        print("Email => ", email)
        if email != "" and PERSON.objects.filter(Q(username__iexact=email)).exists():
            is_exists = True
            logger.info(f"Email is exist True at check_email_view for : {email}")
            return JsonResponse({"message": "success", "is_exists": is_exists})
        else:
            logger.warning(f"Email is not exist True at check_email_view for : {email}")
            return JsonResponse({"message": "success", "is_exists": is_exists})
    return JsonResponse({"message": "error", "is_exists": is_exists})

@login_required(login_url="/login/")
def delete_student_account_view(request):
    try:
        student = request.user.username
        logger.info(f"function call for account delete : {student}")
        person = Person.objects.get(pk=request.user.pk)
        person.delete()
        logger.info(f"student account delete successfully : {student}")
        return HttpResponseRedirect(reverse("login"))
    except Exception as error:
        logger.error(f"Error in delete account {error} : {request.user.username}")
        return HttpResponseRedirect(reverse("account-settings"))

def otp_verification(request):
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        if request.method == "POST":
            request_post = request.POST
            stu_email = request_post.get("stu_email", "")
            otp_status = request_post.get("otp_status", "No")
            if stu_email != "" and otp_status == "Yes":
                request.session["is_otp_verified"] = True
                logger.info(f"set the variable for otp verification : {stu_email}")
                return JsonResponse({"msg": "success"}, status=200, safe=False)
            return JsonResponse({"msg": "Error"}, status=200, safe=False)
    except Exception as Error:
        logger.error(f"Error at otp verification {Error} : {custom_user_session_id}")
    return JsonResponse({"msg": "Error"}, status=400, safe=False)

class PersonFutureLabRegistrationView(UserPassesTestMixin, TemplateView):
    """
    PersonRegistrationView class for the registration.
    """
    # template_name = "userauth/futurelabsignup1.html"
    # is_phone_view = False
    # if is_phone_view is True:
    #     template_name = "userauth/mobile_signup_stage_combine.html"

    def test_func(self):
        if not self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))


    def get(self, request, *args, **kwargs):
        context = {} #super(PersonRegistrationView, self).get_context_data(*args, **kwargs)
        context['placeholder_of_first_name'] = _("Enter your first name")
        context['placeholder_of_last_name'] = _("Enter your last name")
        context['placeholder_of_phone_number'] = _("Enter your mobile number")
        context['placeholder_of_email'] = _("Enter your e-mail id")
        context['placeholder_of_password'] = _("Enter new password")
        self.request.session["is_otp_verified"] = False
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        is_phone_view = request.session.get('is_phone_view')
        if is_phone_view == True:
            template_name = "userauth/mobile_signup_stage_combine.html"
        else:
            template_name = "userauth/futurelabsignup1.html"
        if request.LANGUAGE_CODE == 'en-us':
            logger.info(f"In post view of person-regitration-view called with language code : {request.LANGUAGE_CODE} : {custom_user_session_id}")
            school_country = 'USA'
            context['class_years'] = ClassYear.objects.filter(country='USA')
            context['specilizations'] = Specialization.objects.filter(country='USA')
            context['class_names'] = ClassName.objects.filter(country='USA')
            context['school_cities'] = School.objects.filter(country="USA", is_verified=True)
        elif request.LANGUAGE_CODE == 'it':
            logger.info(f"In post view of person-regitration-view called with language code : {request.LANGUAGE_CODE} : {custom_user_session_id}")
            school_country = 'Italy'
            context['class_years'] = ClassYear.objects.filter(country=school_country)
            context['specilizations'] = Specialization.objects.filter(country='Italy')
            context['class_names'] = ClassName.objects.filter(country='Italy')
            context['school_cities'] = School.objects.filter(country=school_country, is_verified=True)
        ctype = self.request.GET.get('ctype', None)
        plan = self.request.GET.get('plan', None)
        self.request.session['ctype'] = ctype if ctype else 'future_lab'
        if plan:
            self.request.session['plan'] = plan
        context["person_register_form"] = FutureLabPersonRegisterForm()
        student_completion_form = StudentCompletionForm()
        context = signupstage1_placeholders(context)
        context['student_completion_form'] = student_completion_form
        context['is_phone_view'] = is_phone_view
        create_custom_event(self.request, 20, meta_data={'ctype':self.request.GET.get('ctype', 'general'), 'plan': self.request.GET.get('plan', '')})
        logger.info(f"Signup page person register view in get method called by : {custom_user_session_id}")
        return render(self.request, template_name, context)

    def post(self, request, *args, **kwargs):
        """
        this is post method of PersonRegistrationView, this method accept the POST requests.
        """
        is_phone_view = self.request.session.get('is_phone_view', False)
        if is_phone_view is True:
            template_name = "userauth/mobile_signup_stage_combine.html"
        else:
            template_name = "userauth/futurelabsignup1.html"
        request_post = request.POST
        # email_for_log = request_post.get('email')
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"In post view of person-regitration-view : {custom_user_session_id}")
        context = super(PersonFutureLabRegistrationView, self).get_context_data(*args, **kwargs)
        # hdn_first_name, hdn_last_name, hdn_gender, hdn_gender_other, hdn_contact_number, 
        # hdn_class_year, hdn_school_name, hdn_school_city, future_lab_code
        student_completion_form = StudentCompletionForm(request_post)
        person_register_form = FutureLabPersonRegisterForm(request_post)
        errors_list = []
        if person_register_form.is_valid():
            first_name = person_register_form.cleaned_data.get("first_name", "")
            last_name = person_register_form.cleaned_data.get("last_name", "")
            gender = person_register_form.cleaned_data.get("gender")
            gender_other = person_register_form.cleaned_data.get("gender_other")
            email = person_register_form.cleaned_data.get("email")
            password = person_register_form.cleaned_data.get("password")
            contact_number = person_register_form.cleaned_data.get("contact_number", "")
            how_know_us = person_register_form.cleaned_data.get("how_know_us")
            how_know_us_other = person_register_form.cleaned_data.get("how_know_us_other")
            company_name = request_post.get("company-name")
            p_contact_number = request_post.get('p_contact_number', '')
            p_email = request_post.get('p_email', '')
            is_otp_verified = self.request.session.get("is_otp_verified", False)
            
            if(is_otp_verified == False):
                context["student_completion_form"] = student_completion_form
                context['otp_error_msg'] = _('You must verified the OTP before proceeding.')
                logger.warning(f"Signup page stage 2 - Not verified the OTP : {email}")
                context['person_register_form'] = person_register_form
                return render(request, template_name, context)

            if(first_name == ""):
                context["student_completion_form"] = student_completion_form
                context['first_name_error_msg'] = _('You must enter the first name before proceeding.')
                logger.warning(f"Signup page stage 1 - Not enter the first name : {email}")
                context['person_register_form'] = person_register_form
                return render(request, template_name, context)

            if(last_name == ""):
                context["student_completion_form"] = student_completion_form
                context['last_name_error_msg'] = _('You must enter the last name before proceeding.')
                logger.warning(f"Signup page stage 1 - Not enter the last name : {email}")
                context['person_register_form'] = person_register_form
                return render(request, template_name, context) 

            if(p_contact_number == ""):
                context["student_completion_form"] = student_completion_form
                context['p_number_error_msg'] = _('You must enter the Parents number before proceeding.')
                logger.warning(f"Signup page stage 1 - Not enter the parents mobile number : {email}")
                context['person_register_form'] = person_register_form
                return render(request, template_name, context)

            if(p_email == ""):
                context["student_completion_form"] = student_completion_form
                context['p_email_error_msg'] = _('You must enter the Parents Email before proceeding.')
                logger.warning(f"Signup page stage 1 - Not enter the parents email : {email}")
                context['person_register_form'] = person_register_form
                return render(request, template_name, context)

            if(contact_number == ""):
                context["student_completion_form"] = student_completion_form
                context['number_error_msg'] = _('You must enter the phone number before proceeding.')
                logger.warning(f"Signup page stage 1 - Not enter the mobile number : {email}")
                context['person_register_form'] = person_register_form
                return render(request, template_name, context)


            tos_agreed = request_post.get('check_tos', 'No')
            discount_code=request_post.get('future_lab_code','')
            if discount_code == "":
                context["student_completion_form"] = student_completion_form
                context['tos_message'] = _('You must applied the coupon code before proceeding')
                print(f"coupon code not applied")
                logger.warning(f"Signup page stage 2 - Not applied the coupon code : {email}")
                context['person_register_form'] = person_register_form
                return render(request, template_name, context)
            else:
                discount_code_status = Coupon.objects.filter(code__iexact=discount_code).exists()
                if not discount_code_status:
                    logger.warning(f"Signup page stage 2 - Not applied the coupon code : {email}")
                    context['person_register_form'] = person_register_form
                    context["student_completion_form"] = student_completion_form
                    context['discount_code_error_msg'] = _("You must applied the coupon code before proceeding")
                    return render(request, template_name, context)
            discount_code_end_date = ''

            if is_phone_view == False:
                if tos_agreed != 'Checked':
                    context["student_completion_form"] = student_completion_form
                    context['tos_message'] = _('You must accept before proceeding')
                    print(f"tos not checked")
                    logger.warning(f"Signup page stage 2 - Not selected tos checkbox : {email}")
                    context['person_register_form'] = person_register_form
                    return render(request, template_name, context)
            school_region = request_post.get('school-region', '')
            school_city = request_post.get('school-city', '')
            school_name = request_post.get('school-name', '')
            school_name_other = request_post.get('school_name_other', '')
            school_country = request_post.get('school_country', '')
            bit_other_school = False
            if(email == "" ):
                context["student_completion_form"] = student_completion_form
                context['person_register_form'] = person_register_form
                context['email_error_msg'] = _("You must enter the email before proceeding")
                logger.warning(f"Signup page stage 2 - Email is None : {custom_user_session_id}")
                return render(request, template_name, context)
            
            if student_completion_form.is_valid():
                person = None
                try:
                    person = person_register_form.save(commit=False)
                    person.username = email
                    person.save()
                except Exception as erro:
                    print(erro)
                    context["message"] = [f"The email {email} already exists in the system."]
                    context['person_register_form'] = person_register_form
                    logger.error(f"Error email already exist in person register view {erro} : {email}")
                    return render(request, template_name, context)

                student = student_completion_form.save(commit=False)
                student.person = person
                student.src = self.request.session.get('ctype', 'future_lab')
                student.are_you_fourteen_plus = "Yes"
                student.discount_coupon_code = discount_code
                number_of_plans = "3"
                skip_course_dependency = False
                is_course1_locked = False
                display_discounted_price_only = False
                try:
                    if(discount_code != ""):
                        coupon_details = Coupon.objects.get(code__iexact=discount_code) # check the discount obj in coupon details
                        number_of_plans = coupon_details.number_of_offered_plans
                        skip_course_dependency = coupon_details.skip_course_dependency
                        is_course1_locked = coupon_details.is_course1_locked
                        discount_code_end_date = coupon_details.end_date
                        display_discounted_price_only = coupon_details.display_discounted_price_only

                except Exception as error:
                    print(error)
                    logger.warning(f"Error of discount_code at person-register-view {error}: {email}")
                
                try:
                    if(company_name is not None):
                        student.company = Company.objects.get(pk=company_name)
                except Exception as error:
                    print(str(error))
                    logger.warning(f"Error of company at person-register-view {error}: {email}")
                
                student.number_of_offered_plans = number_of_plans
                student.skip_course_dependency = skip_course_dependency
                student.is_course1_locked = is_course1_locked
                student.display_discounted_price_only = display_discounted_price_only
                student.save()

                student_parent_details = StudentParentsDetail.objects.create(student=student, parent_contact_number=p_contact_number, parent_email=p_email)
                print("student_parent_details : ", student_parent_details)
                school_type = ''
                graduation_year = request_post.get('year', '')
                class_year = request_post.get('class-year', '')
                class_name = request_post.get('class-name', '')
                class_specialization = request_post.get('class-specialization', '')
            
                if student and student.are_you_a_student == 'Yes':
                    obj_school_details = StudentSchoolDetail.objects.create(student=student, school_region=school_region, school_city=school_city, school_name=school_name, school_type=school_type, graduation_year=graduation_year)
                    if class_year:
                        try:
                            obj_class_year = ClassYear.objects.get(pk=class_year)
                            obj_school_details.class_year = obj_class_year
                        except Exception as exx:
                            print(str(exx))
                            logger.warning(f"Error of class-year at person-register-view {exx}: {email}")
                    if class_name:
                        try:
                            obj_class_name = ClassName.objects.get(pk=class_name)
                            obj_school_details.class_name = obj_class_name
                        except Exception as error:
                            print(str(error))
                            logger.warning(f"Error of class_name at person-register-view {error}: {email}")
                    if class_specialization:
                        try:
                            obj_class_specialization = Specialization.objects.get(pk=class_specialization)
                            obj_school_details.specialization = obj_class_specialization
                        except Exception as error:
                            print(str(error))
                            logger.warning(f"Error of class-specialization at person-register-view {error}: {email}")
                    obj_school_details.save()
                if bit_other_school:
                    School.objects.create(name=school_name, city = school_city, region = school_region, type = school_type, country= school_country)
                submit_hubspot_form_with_email(request, email)
                
                try:
                    if student.src == "future_lab":
                        is_future_lab_student="true"
                    else:
                        is_future_lab_student="false"   
                    local_tz = pytz.timezone(settings.TIME_ZONE)
                    dt_now = str(local_tz.localize(datetime.now()))
                    enrollDate=unixdateformat(datetime.now())
                    logger.info(f"In hubspot signup parameter building for : {person.username}")
                    keys_list = ['email','firstname', 'lastname', "hubspot_first_name", "course_country", "hubspot_are_you_a_student", "hubspot_check_tos", "hubspot_class_name",
                    "hubspot_class_specialization", "hubspot_class_year", "hubspot_contact_number", "hubspot_coupon_code_entered", "hubspot_email", "hubspot_how_know_us",
                    "hubspot_how_know_us_other", "hubspot_language_code", "hubspot_last_name", "hubspot_school_name", "hubspot_school_city", "hubspot_school_region", "hubspot_student_type",
                    "is_future_lab_student_registered", "is_student_registered", "hubspot_end_date_discount_code", "hubspot_enrollment_date", "hubspot_registration_url","hubspot_gender","hubspot_gender_other",
                    "hubspot_registration_parent_email","hubspot_registration_parent_phone_number","enroll_date"]
                    values_list = [person.username,person.first_name,person.last_name, person.first_name, school_country, student.are_you_a_student, "Yes", class_name, class_specialization, class_year, person.contact_number, student.discount_coupon_code, person.email, person.how_know_us, person.how_know_us_other, school_country, person.last_name, obj_school_details.school_name,
                    obj_school_details.school_city,  obj_school_details.school_region, student.src, is_future_lab_student, True, str(discount_code_end_date), dt_now, self.request.build_absolute_uri(),gender,
                    gender_other,p_email,p_contact_number,enrollDate]
                    create_update_contact_hubspot(person.username, keys_list, values_list)
                    logger.info(f"In hubspot signup parameter update completed for : {person.username}")
                except Exception as error:
                    logger.error(f"Error at hubspot signup parameter update {error} for : {person.username}")
                subject = _("Futurely - Verify your email address")
                login(request,person)
                request.session['notifymsg']=1
                request.session['display_welcome_video']=1
                if school_name:
                    create_custom_event(request, 2, meta_data={'school_name': school_name, 'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                    logger.info(f"Created custom event successfully for : {email}")
                else:
                    create_custom_event(request, 2, meta_data={'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                    logger.info(f"Created custom event successfully for : {email}")
                StudentPCTORecord.objects.create(student=student, pcto_hours=1, pcto_hour_source="Future-lab")
                logger.info(f"Created student pcto record for : {email}")
                if request.LANGUAGE_CODE == 'it':
                    status=send_email_message(request,person,subject,'userauth/email_content-it.html')
                else:
                    status=send_email_message(request,person,subject,'userauth/email_content.html')
                
                if person:
                    notification_type_objs = Notification_type.objects.all()
                    for single_notification_type in notification_type_objs:
                        PersonNotification.objects.update_or_create(
                            person=person, notification_type=single_notification_type)

                # ################################################################################ #
                # ############# Check The User In Payment Model exist or not ##################### #
                # ################################################################################ #
                lang_code = request.LANGUAGE_CODE
                check_payment_obj = Payment.objects.filter(payment_email_id=email, status__in=["active", "succeeded"], plan__plan_lang=lang_code).order_by("-plan__id")
                if check_payment_obj.count() > 0:
                    if(status == True):
                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                        logger.info(f"Email sent and User created Person-register-view page-post : {email}")
                    else:
                        Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                        context["message"] = _("Error to send mail to verify Email, Please check email id")
                        logger.error(f"Error Email not sent and user created Person-register-view page-post : {email}")
                    one_time_payment_check_obj = check_payment_obj.filter(payment_subscription_type="One Time")
                    if one_time_payment_check_obj.count() > 0:
                        one_time_payment_obj = one_time_payment_check_obj.first()
                        if one_time_payment_obj.person is None:
                            # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                            StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=one_time_payment_obj.plan)
                            Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                            one_time_payment_obj.person = person
                            one_time_payment_obj.save()
                            logger.info(f"Register user mapped with StudentPlanMapper and Payment type(One Time) : {email}")
                            return HttpResponseRedirect(reverse("home"))
                    
                    weekly_person_pay_check_obj = check_payment_obj.filter(payment_subscription_type="Weekly")
                    if weekly_person_pay_check_obj.count() > 0:
                        for weekkly_obj in weekly_person_pay_check_obj:
                            pid_paysubdetail = weekkly_obj.paymentsubscriptiondetail.filter(invoice_status="paid")
                            if pid_paysubdetail.count() > 0:
                                if weekkly_obj.person is None:
                                    # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                    StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=weekkly_obj.plan)
                                    Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                    weekkly_obj.person = person
                                    weekkly_obj.save()
                                    break
                        logger.info(f"Register user mapped with StudentPlanMapper and Payment type(Weekly) : {email}")
                        return HttpResponseRedirect(reverse("home"))

                if(status == True):
                    Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                    logger.info(f"Email sent and User created Person-register-view page-post : {email}")
                    return HttpResponseRedirect(reverse("futurely-plans"))
                else:
                    Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                    context["message"] = _("Error to send mail to verify Email, Please check email id")
                    logger.error(f"Error Email not sent and user created Person-register-view page-post : {email}")
                    return HttpResponseRedirect(reverse("futurely-plans"))
            else:
                print("Error form not valid")
                for form_errors_list in student_completion_form.errors.values():
                    for error in form_errors_list:
                        errors_list.append(error)
            print(f"Hello in stage 2 form not valid")
            context["student_completion_form"] = student_completion_form
            context['message'] = errors_list
            logger.error(f"Error Form not valid stage 2 : {email}")
            return render(request, template_name, context)
        context["person_register_form"] = person_register_form
        return super(TemplateView, self).render_to_response(context)

from .forms import FuturelyFirstStageForm, FuturelySecondStageForm

class NewSingupView(UserPassesTestMixin, TemplateView):

    def test_func(self):
        if not self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    def get(self, request, *args, **kwargs):
        context = {}
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"In futurelab registration stage 1 : {custom_user_session_id}")
        is_phone_view = self.request.session.get('is_phone_view', False)
        if is_phone_view is True:
            context['placeholder_of_first_name'] = _("Enter your first name")
            context['placeholder_of_last_name'] = _("Enter your last name")
            context['placeholder_of_phone_number'] = _("Enter your mobile number")
            context['placeholder_of_email'] = _("Enter your e-mail id")
            context['placeholder_of_password'] = _("Enter new password")
            template_name = "userauth/mobile_signup_stage_1.html"
        else:
            template_name = "userauth/futurelabsignup_new.html"
        ctype = 'future_lab'
        coupon_code = self.request.session.get('coupon_code', None)
        coupon_type = self.request.session.get('coupon_type',None)
        if self.request.LANGUAGE_CODE == "it":
            if not coupon_code or coupon_type != 'FutureLab':
                logger.info(f"Coupon Code is not available for {custom_user_session_id}")
                url = reverse('index') + '?validate_discount_code=true'
                return HttpResponseRedirect(url)
        # plan = self.request.GET.get('plan', None)
        self.request.session['ctype'] = ctype
        context['first_stage_form'] = FuturelyFirstStageForm()
        logger.info(f"get method called for the futurelab register view by : {custom_user_session_id}")
        return render(request, template_name, context)
    
    def post(self, request, *args, **kwargs):
        context = {}
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
        clarity_token = self.request.session.get('clarity_token', '')
        is_phone_view = self.request.session.get('is_phone_view', False)
        if is_phone_view is True:
            context["discount_code_placeholder"] = _("Enter the Discount Code")
            context["par_mobile_placeholder"] = _("Enter your Parent’s Number")
            context["par_email_placeholder"] = _("Your Parent’s E-mail ID")
            template_name = "userauth/mobile_signup_stage_1.html"
            template_name_2 = "userauth/mobile_signup_stage_2.html"
        else:
            template_name = "userauth/futurelabsignup_new.html"
            template_name_2 = "userauth/futurelabsignup3.html"
        first_stage_form = FuturelyFirstStageForm(self.request.POST)
        second_stage_form = FuturelySecondStageForm(request.POST or None)
        is_otp_verified = request.session.get("is_otp_verified", False)
        back_btn = request.POST.get("backbtn", "No")
        if back_btn == "Yes":
            context['first_stage_form'] = FuturelyFirstStageForm(self.request.POST)
            context["gender"] = request.POST.get('gender')
            context["countryCode"] = request.POST.get('countryCode', '')
            logger.info(f"Clicked on the backbutton on the futurelab register view by : {custom_user_session_id}")
            return render(request, template_name, context)
        # print(is_otp_verified)
        # if is_otp_verified == False:
        #     context["otp_error_msg"] = _("Please enter the valid OTP")
        #     context['first_stage_form']=first_stage_form
        #     return render(request, template_name, context)
        otp = request.POST.get("otp", "")
        request_post = request.POST
        if first_stage_form.is_valid() or second_stage_form.is_valid():
            second_stage_form = FuturelySecondStageForm(request.POST or None)
            student_completion_form = StudentCompletionForm(request.POST or None)
            email = first_stage_form.cleaned_data.get("email")
            logger.info(f"In Post request - futurelab registration stage 1 : {email}")
            first_name = first_stage_form.cleaned_data.get("first_name")
            last_name = first_stage_form.cleaned_data.get("last_name")
            gender = first_stage_form.cleaned_data.get("gender")
            password = first_stage_form.cleaned_data.get("password")
            confirm_password = first_stage_form.cleaned_data.get("confirm_password")
            contact_number = first_stage_form.cleaned_data.get("contact_number")
            # context['fullname'] = f"{first_name} {last_name}"
            if password and confirm_password and password != confirm_password:
                context['first_stage_form'] = first_stage_form
                context["student_completion_form"] = student_completion_form
                context["confirm_password_error"] = _("Please enter correct confirm password")
                return render(request, "userauth/futurelabsignup_new.html", context)
            
            context["contact_number"] = contact_number
            context["email"] = email
            context["first_name"] = first_name
            context["last_name"] = last_name
            context["gender"] = gender
            context["password"] = password
            context['first_stage_form'] = first_stage_form
            context['second_stage_form'] = FuturelySecondStageForm()
            context["student_completion_form"] = StudentCompletionForm()
            context["otp"] = otp
            context["countryCode"] = request.POST.get('countryCode')
            if request.LANGUAGE_CODE == 'en-us':
                school_country = 'USA'
                context['class_years'] = ClassYear.objects.filter(country='USA')
                context['specilizations'] = Specialization.objects.filter(country='USA')
                context['class_names'] = ClassName.objects.filter(country='USA')
                # context['school_cities'] = School.objects.filter(country="USA", is_verified=True)
            elif request.LANGUAGE_CODE == 'it':
                school_country = 'Italy'
                context['class_years'] = ClassYear.objects.filter(country=school_country)
                context['specilizations'] = Specialization.objects.filter(country='Italy')
                context['class_names'] = ClassName.objects.filter(country='Italy')
                # context['school_cities'] = School.objects.filter(country=school_country, is_verified=True)
            if second_stage_form.is_valid() and student_completion_form.is_valid():
                logger.info(f"In Post request - futurelab registration stage 2 : {email}")
                is_discount_code = False
                school_region = ""
                school_city = ""
                school_name = ""
                school_type = ''
                context['second_stage_form'] = second_stage_form
                context["student_completion_form"] = student_completion_form
                # discount_code = student_completion_form.cleaned_data.get("discount_coupon_code")
                discount_code = request_post.get('future_lab_code', '')
                discount_code = self.request.session.get('coupon_code', None)
                # email = first_stage_form.cleaned_data.get("email")
                number_of_plans = "3"
                skip_course_dependency = False
                is_course1_locked = False
                display_discounted_price_only = False
                is_fully_paid_by_school_or_company = False
                coupon_obj = None
                coupon_detail_obj = None
                is_100_per_coupon_code = False
                cohort_program1 = None
                cohort_program2 = None
                cohort_program3 = None
                hubspot_school_type = "free_channel"
                plan_name_from_coupon = None
                try:
                    if discount_code.strip() == '':
                        context['second_stage_form'] = second_stage_form
                        context["student_completion_form"] = student_completion_form
                        context["discount_error_msg"] = _("Please enter the valid discount code")
                        logger.error(f"In Post request - futurelab registration stage 2 - discount code not found : {email}")
                        return render(request, template_name_2, context)
                    else:
                        coupon_code_status = check_discount_code_validation(request, discount_code)
                        if(coupon_code_status == False):
                            context['second_stage_form'] = second_stage_form
                            context["student_completion_form"] = student_completion_form
                            context["discount_error_msg"] = _("Please enter the valid discount code")
                            logger.error(f"In Post request - futurelab registration stage 2 - discount code not found : {email}")
                            return render(request, template_name_2, context)
                        logger.info(f"In Post request - futurelab registration stage 2 - To check discount code details : {email}")
                        coupon_obj = Coupon.objects.get(code__iexact=discount_code) # check the discount obj in coupon details
                        number_of_plans = coupon_obj.number_of_offered_plans
                        skip_course_dependency = coupon_obj.skip_course_dependency
                        is_course1_locked = coupon_obj.is_course1_locked
                        discount_code_end_date = coupon_obj.end_date
                        display_discounted_price_only = coupon_obj.display_discounted_price_only
                        is_fully_paid_by_school_or_company = coupon_obj.is_fully_paid_by_school_or_company
                        discount_type = coupon_obj.discount_type
                        discount_value = int(coupon_obj.discount_value)
                        if coupon_obj.is_fully_paid_by_school_or_company == True:
                            hubspot_school_type = "fully_paid"
                        else:
                            hubspot_school_type = "free_channel"
                        if discount_type == "Percentage" and discount_value == 100:
                            is_100_per_coupon_code = True
                        # is_discount_code = True
                        plan_name_from_coupon = coupon_obj.plan_type
                        if plan_name_from_coupon == "Master":
                            plan_name_from_coupon = "Elite"
                        coupon_detail_obj = CouponDetail.objects.filter(coupon=coupon_obj).first()
                        if coupon_detail_obj:
                            school_region = coupon_detail_obj.school.region
                            school_city = coupon_detail_obj.school.city
                            school_name = coupon_detail_obj.school.name
                            school_type = coupon_detail_obj.school.type
                            
                            logger.info(f"In Post request - futurelab registration stage 2 - discount code details found : {email}")
                        else:
                            #create custom event : students of futurelab without school details
                            logger.error(f"In Post request - futurelab registration stage 2 - discount code details not found : {email}")   
                except Exception as error:
                    context['second_stage_form'] = second_stage_form
                    context["student_completion_form"] = student_completion_form
                    context["discount_error_msg"] = _("Please enter the valid discount code")
                    logger.error(f"Error of discount_code at futurelab-register-view {error}: {email}")
                    return render(request, template_name_2, context)
                person_completion_form = FutureLabPersonRegisterForm(request.POST)
                if person_completion_form.is_valid():
                    person = person_completion_form.save(commit=False)
                    person.clarity_token = clarity_token
                    person.username = email
                    person.lang_code = request.LANGUAGE_CODE
                    # are_you_a_student = student_completion_form.cleaned_data.get("are_you_a_student")
                    student = student_completion_form.save(commit=False)
                    student.person = person
                    # if are_you_a_student == "No" or are_you_a_student == "" or are_you_a_student == "no":
                    are_you_a_student = "Yes"
                    student.src = 'future_lab'
                    student.are_you_fourteen_plus = "Yes"
                    student.are_you_a_student = are_you_a_student
                    student.discount_coupon_code = discount_code
                    student.number_of_offered_plans = number_of_plans
                    student.skip_course_dependency = skip_course_dependency
                    student.is_course1_locked = is_course1_locked
                    student.display_discounted_price_only = display_discounted_price_only
                    person.save()
                    logger.info(f"In Post request - futurelab registration stage 2 - Person saved : {email}")
                    student.student_channel = hubspot_school_type
                    student.save()
                    student.save()
                    logger.info(f"In Post request - futurelab registration stage 2 - Person-Student infomation saved : {email}")
                    p_contact_number = second_stage_form.cleaned_data.get("parents_mobile_number")
                    p_email = second_stage_form.cleaned_data.get("parents_email")
                    StudentParentsDetail.objects.create(student=student, parent_contact_number=p_contact_number, parent_email=p_email)
                    # school_name_other = request_post.get('school_name_other', '')
                    # school_country = request_post.get('school_country', '')
                    logger.info(f"In Post request - futurelab registration stage 2 - Person-Student-Parents infomation saved : {email}")
                    graduation_year = request_post.get('year', '')
                    class_year = request_post.get('class-year', '')
                    class_name = request_post.get('class-name', '')
                    class_specialization = request_post.get('class-specialization', '')
                    # bit_other_school = False
                    # if is_discount_code:
                        # discount_obj = CouponDetail.objects.filter(coupon=coupon_details).first()
                        # if discount_obj is not None and student.are_you_a_student == 'Yes':
                    obj_stu_school_details = StudentSchoolDetail.objects.create(student=student, school_region=school_region, school_city=school_city, school_name=school_name, school_type=school_type, graduation_year=graduation_year)
                    if class_year:
                        try:
                            obj_class_year = ClassYear.objects.get(pk=class_year)
                            obj_stu_school_details.class_year = obj_class_year
                        except Exception as exx:
                            print(str(exx))
                            logger.warning(f"Error of class-year at person-register-view {exx}: {email}")
                    if class_name:
                        try:
                            obj_class_name = ClassName.objects.get(pk=class_name)
                            obj_stu_school_details.class_name = obj_class_name
                        except Exception as error:
                            print(str(error))
                            logger.warning(f"Error of class_name at person-register-view {error}: {email}")
                    if class_specialization:
                        try:
                            obj_class_specialization = Specialization.objects.get(pk=class_specialization)
                            obj_stu_school_details.specialization = obj_class_specialization
                        except Exception as error:
                            print(str(error))
                            logger.warning(f"Error of class-specialization at person-register-view {error}: {email}")
                    obj_stu_school_details.save()
                    logger.info(f"In Post request - futurelab registration stage 2 - Person-Student-school infomation saved : {email}")
                    # if bit_other_school:
                    #     School.objects.create(name=school_name, city = school_city, region = school_region, type = school_type, country= school_country)
                    # submit_hubspot_form_with_email(request, email)
                    try:
                        is_future_lab_student="true"   
                        local_tz = pytz.timezone(settings.TIME_ZONE)
                        dt_now = str(local_tz.localize(datetime.now()))
                        enrollDate=unixdateformat(datetime.now())
                        logger.info(f"In hubspot signup parameter building for : {person.username}")
                        keys_list = ['email','firstname', 'lastname', "hubspot_first_name", "course_country", "hubspot_are_you_a_student", "hubspot_check_tos", "hubspot_class_name",
                        "hubspot_class_specialization", "hubspot_class_year", "hubspot_contact_number", "hubspot_coupon_code_entered", "hubspot_email", "hubspot_how_know_us",
                        "hubspot_how_know_us_other", "hubspot_language_code", "hubspot_last_name", "hubspot_school_name", "hubspot_school_city", "hubspot_school_region", "hubspot_student_type",
                        "is_future_lab_student_registered", "is_student_registered", "hubspot_end_date_discount_code", "hubspot_enrollment_date", "hubspot_registration_url","hubspot_gender","hubspot_gender_other",
                        "hubspot_registration_parent_email","hubspot_registration_parent_phone_number","enroll_date","hubspot_school_type"]
                        values_list = [person.username,person.first_name,person.last_name, person.first_name, school_country, student.are_you_a_student, "Yes", class_name, class_specialization, class_year, person.contact_number, student.discount_coupon_code, person.email, person.how_know_us, person.how_know_us_other, school_country, person.last_name, obj_stu_school_details.school_name,
                        obj_stu_school_details.school_city,  obj_stu_school_details.school_region, student.src, is_future_lab_student, True, str(discount_code_end_date), dt_now, self.request.build_absolute_uri(),gender,"gender_other",p_email,p_contact_number,enrollDate,hubspot_school_type]
                        logger.info(f"In hubspot signup parameter update student contact : {person.username}")
                        create_update_contact_hubspot(person.username, keys_list, values_list)
                        logger.info(f"In hubspot signup parameter update completed for : {person.username}")
                        
                    except Exception as error:
                        logger.error(f"Error at hubspot signup parameter update {error} for : {person.username}")
                    subject = _("Futurely - Verify your email address")
                    login(request,person)
                    request.session['notifymsg']=1
                    request.session['display_welcome_video']=1
                    if school_name:
                        create_custom_event(request, 2, meta_data={'school_name': school_name, 'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                        logger.info(f"Created custom event successfully for : {email}")
                    else:
                        create_custom_event(request, 2, meta_data={'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                        logger.info(f"Created custom event successfully for : {email}")
                    StudentPCTORecord.objects.create(student=student, pcto_hours=1, pcto_hour_source="Future-lab")
                    logger.info(f"In Post request - futurelab registration stage 2 - Student PCTO hours added : {email}")
                    student.update_total_pcto_hour()
                    if request.LANGUAGE_CODE == 'it':
                        status=send_email_message(request,person,subject,'userauth/email_content-it.html')
                    else:
                        status=send_email_message(request,person,subject,'userauth/email_content.html')
                    if person:
                        notification_type_objs = Notification_type.objects.all()
                        for single_notification_type in notification_type_objs:
                            PersonNotification.objects.update_or_create(
                                person=person, notification_type=single_notification_type)

                    lang_code = request.LANGUAGE_CODE
                    if is_fully_paid_by_school_or_company == True and is_100_per_coupon_code == True:
                        selected_plan = OurPlans.objects.filter(plan_lang=lang_code, plan_name=plan_name_from_coupon).first()
                        if lang_code == 'en-us':
                            currency = 'usd'
                        elif lang_code == 'it':
                            currency = 'eur'
                        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
                        Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                                    plan=selected_plan, coupon_code=coupon_obj.code, actual_amount=selected_plan.cost, discount=selected_plan.cost, custom_user_session_id=custom_user_session_id)
                        # Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                        #                         plan=selected_plan, coupon_code="", actual_amount="0", discount="0", custom_user_session_id=custom_user_session_id)
                        logger.info(f"payment obj updated for : {email} with 100 per coupon code {coupon_obj.code}")
                        stu_pln_obj, stu_pln_obj_created = StudentsPlanMapper.plansManager.lang_code(lang_code).update_or_create(
                            student=person, plan_lang=lang_code, defaults={'plans': selected_plan})
                        logger.info(f"student plan mapper obj update_or_create at signup for : {email}")
                        try:
                            if plan_name_from_coupon == "Premium":
                                cohort_program1 = coupon_detail_obj.cohort_program1
                            else:
                                cohort_program1 = coupon_detail_obj.cohort_program1
                                cohort_program2 = coupon_detail_obj.cohort_program2
                                if request.LANGUAGE_CODE == "it":
                                    cohort_program3 = coupon_detail_obj.cohort_program3
                        except Exception as er:
                            logger.warning(f"Coupon code does not have any linked cohort - {er} : {email}")
                        if cohort_program1:
                            StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program1, stu_cohort_lang=request.LANGUAGE_CODE)
                            logger.info(f"student cohort mapper obj 1 created at signup for : {email}")
                            exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id])
                            # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id)
                            # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id)
                            request.session['is_first_time_on_dashboard'] = True
                        if cohort_program2:
                            StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program2, stu_cohort_lang=request.LANGUAGE_CODE)
                            logger.info(f"student cohort mapper obj 2 created at signup for : {email}")
                            exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id])
                            # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id)
                            # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id)
                        if cohort_program3:
                            StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program3, stu_cohort_lang=request.LANGUAGE_CODE)
                            logger.info(f"student cohort mapper obj 3 created at signup for : {email}")
                            exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id])
                            # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id)
                            # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id)
                        # student.discount_coupon_code = ""
                        student.save()
                        try:
                            # hubspotContactupdateQueryAdded
                            logger.info(f"In hubspot plan/cohort enroll signup building for : {request.user.username}")
                            if plan_name_from_coupon =='Premium':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    premiumPlanEnrollDate=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    premiumPlanEnrollDate=unixdateformat(stu_pln_obj.modified_at)
                                
                                coupon_end_date=unixdateformat(coupon_obj.end_date)
                                Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
                                keys_list = ["email","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount","hubspot_applied_discount_code",'hubspot_cohort_name_premium',
                                'premium_plan_enroll_date','end_date_discount_code','hubspot_cohort_premium_start_date']
                                values_list = [request.user.username, plan_created_at, "0",coupon_obj.code,cohort_program1.cohort_name,
                                premiumPlanEnrollDate,coupon_end_date,Hubspot_cohort_premium_start_date]
                                create_update_contact_hubspot(request.user.username, keys_list, values_list)
                            if plan_name_from_coupon =='Elite':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    elitePlanEnrollDate=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    elitePlanEnrollDate=unixdateformat(stu_pln_obj.modified_at)
                                keys_list = ["email","elite_plan_enroll_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code"]
                                values_list = [request.user.username,elitePlanEnrollDate,plan_created_at, "0",coupon_obj.code]
                                end_date_discount_code=unixdateformat(coupon_obj.end_date)
                                keys_list.append('end_date_discount_code')
                                values_list.append(end_date_discount_code)
                                if cohort_program1:
                                    keys_list.append('hubspot_cohort_name_premium')
                                    values_list.append(cohort_program1.cohort_name)
                                    Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
                                    keys_list.append('hubspot_cohort_premium_start_date')
                                    values_list.append(Hubspot_cohort_premium_start_date)
                                if cohort_program2:
                                    keys_list.append('hubspot_cohort_name_elite1')
                                    values_list.append(cohort_program2.cohort_name)
                                    Hubspot_cohort_elite1_start_date=unixdateformat(cohort_program2.starting_date)
                                    keys_list.append('hubspot_cohort_elite1_start_date')
                                    values_list.append(Hubspot_cohort_elite1_start_date)
                                    # elite_plan_enroll_date=unixdateformat(plan_created_at)
                                    # keys_list.append('elite_plan_enroll_date')
                                    # values_list.append(elite_plan_enroll_date)
                                if cohort_program3:
                                    keys_list.append('hubspot_cohort_name_elite2')
                                    values_list.append(cohort_program3.cohort_name)
                                    Hubspot_cohort_elite2_start_date=unixdateformat(cohort_program3.starting_date)
                                    keys_list.append('hubspot_cohort_elite2_start_date')
                                    values_list.append(Hubspot_cohort_elite2_start_date)
                                create_update_contact_hubspot(request.user.username, keys_list, values_list)
                            logger.info(f"hubspot plan/cohort enroll at signup complete for : {request.user.username}")
                        except Exception as ex:
                            logger.error(f"Error at hubspot plan/cohort enroll at signup  {ex} for : {request.user.username}")
                        return redirect(reverse("home"))
                    check_payment_obj = Payment.objects.filter(payment_email_id=email, status__in=["active", "succeeded"], plan__plan_lang=lang_code).order_by("-plan__id")
                    if check_payment_obj.count() > 0:
                        if(status == True):
                            Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                            logger.info(f"Email sent and User created Person-register-view page-post : {email}")
                        else:
                            Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                            context["message"] = _("Error to send mail to verify Email, Please check email id")
                            logger.error(f"Error Email not sent and user created Person-register-view page-post : {email}")
                        one_time_payment_check_obj = check_payment_obj.filter(payment_subscription_type="One Time")
                        if one_time_payment_check_obj.count() > 0:
                            one_time_payment_obj = one_time_payment_check_obj.first()
                            if one_time_payment_obj.person is None:
                                # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=one_time_payment_obj.plan)
                                Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                one_time_payment_obj.person = person
                                one_time_payment_obj.save()
                                logger.info(f"Register user mapped with StudentPlanMapper and Payment type(One Time) : {email}")
                                return HttpResponseRedirect(reverse("home"))
                        
                        weekly_person_pay_check_obj = check_payment_obj.filter(payment_subscription_type="Weekly")
                        if weekly_person_pay_check_obj.count() > 0:
                            for weekkly_obj in weekly_person_pay_check_obj:
                                pid_paysubdetail = weekkly_obj.paymentsubscriptiondetail.filter(invoice_status="paid")
                                if pid_paysubdetail.count() > 0:
                                    if weekkly_obj.person is None:
                                        # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                        StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=weekkly_obj.plan)
                                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                        weekkly_obj.person = person
                                        weekkly_obj.save()
                                        break
                            logger.info(f"Register user mapped with StudentPlanMapper and Payment type(Weekly) : {email}")
                            return HttpResponseRedirect(reverse("home"))

                    if(status == True):
                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                        logger.info(f"Email sent and User created Person-register-view page-post : {email}")
                        return HttpResponseRedirect(reverse("futurely-plans"))
                    else:
                        Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                        context["message"] = _("Error to send mail to verify Email, Please check email id")
                        logger.error(f"Error Email not sent and user created Person-register-view page-post : {email}")
                    one_time_payment_check_obj = check_payment_obj.filter(payment_subscription_type="One Time")
                    if one_time_payment_check_obj.count() > 0:
                        one_time_payment_obj = one_time_payment_check_obj.first()
                        if one_time_payment_obj.person is None:
                            # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                            StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=one_time_payment_obj.plan)
                            Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                            one_time_payment_obj.person = person
                            one_time_payment_obj.save()
                            logger.info(f"Register user mapped with StudentPlanMapper and Payment type(One Time) : {email}")
                            is_from_mobile_app = request.session.get('is_from_mobile_app', False)
                            if is_from_mobile_app:
                                get_cohort = StudentCohortMapper.objects.filter(student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                                if get_cohort:
                                    return HttpResponseRedirect(reverse("home")+ '?cohort_name='+get_cohort.cohort.cohort_name)
                            return HttpResponseRedirect(reverse("home"))
                    
                    weekly_person_pay_check_obj = check_payment_obj.filter(payment_subscription_type="Weekly")
                    if weekly_person_pay_check_obj.count() > 0:
                        for weekkly_obj in weekly_person_pay_check_obj:
                            pid_paysubdetail = weekkly_obj.paymentsubscriptiondetail.filter(invoice_status="paid")
                            if pid_paysubdetail.count() > 0:
                                if weekkly_obj.person is None:
                                    # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                    StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=weekkly_obj.plan)
                                    Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                    weekkly_obj.person = person
                                    weekkly_obj.save()
                                    break
                        logger.info(f"Register user mapped with StudentPlanMapper and Payment type(Weekly) : {email}")
                        is_from_mobile_app = request.session.get('is_from_mobile_app', False)
                        if is_from_mobile_app:
                            get_cohort = StudentCohortMapper.objects.filter(student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                            if get_cohort:
                                return HttpResponseRedirect(reverse("home")+ '?cohort_name='+get_cohort.cohort.cohort_name)
                        return HttpResponseRedirect(reverse("home"))

                    if(status == True):
                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                        logger.info(f"Email sent and User created Person-register-view page-post : {email}")
                        return HttpResponseRedirect(reverse("futurely-plans"))
                    else:
                        context["first_stage_form"] = FuturelyFirstStageForm(self.request.POST)
                        return render(request, template_name, context)

            if Person.objects.filter(username=email).exists():
                context["email_error"] = _("The email already exists in the system")
                context['first_stage_form'] = first_stage_form
                return render(request, template_name, context)
            
            return render(request, template_name_2, context)
        else:
            context["first_stage_form"] = FuturelyFirstStageForm(self.request.POST)
            return render(request, template_name, context)


def generate_otp(request):
    if request.method == "POST":
        digits = [i for i in range(0, 10)]
        otp = ""
        message = "error"
        for i in range(6):
            index = math.floor(random.random() * 10)
            otp += str(digits[index])
        request_post = request.POST
        ph_number = request_post.get("phone_number")
        first_name = request_post.get("first_name")
        if ph_number is not None:
            otp_send_link = f"https://smsotp.in/index.php/smsapi/httpapi/?uname=protp&password=454545&sender=VOWELD&tempid=1607100000000220702&receiver={ph_number}&route=TA&msgtype=1&sms=Dear {first_name} your otp is {otp} - http://voweldigital.in"
            # reponse = requests.get(otp_send_link)
            # print("OTP RESPONSE =>>", reponse)
            status = 200
            message = "success"
            print(">>", otp_send_link)
            request.session["gen_otp"] = otp
        else:
            status = 404
            message = "error"
            request.session["gen_otp"] = otp
        return JsonResponse({"msg": message, "otp": otp}, status=status, safe=False)
    else:
        return JsonResponse({"msg": "You must Enter contact Number before proceeding.", "otp": otp}, status=400, safe=False)


def check_master_code(request):
    """This function check the coupon code exists or not and this function use with ajax call."""
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        is_exists = "No"
        if request.method == "POST" and request.is_ajax:
            request_post = request.POST
            otp = request_post.get('otp', None)
            if otp is not None:
                if MasterOTP.objects.filter(otp=otp).exists():
                    is_exists = "Yes"
                    request.session["is_otp_verified"] = True
                    logger.info(f"check the master otp code for : {custom_user_session_id}")
                else:
                    is_exists = "No"
            return JsonResponse({'msg': "success", "is_exists": is_exists}, status=200, safe=False)
    except Exception as error:
        print(error)
        logger.error(f"Error in check_master_code {error}: {custom_user_session_id}")
        return JsonResponse({'error': str(error)}, status=403, safe=False)  

class MiddleSchoolRegistration(UserPassesTestMixin, TemplateView):
    # template_name_1 = "userauth/middle-school-register-first-stage.html"
    # template_name_2 = "userauth/middle-school-register-second-stage.html"

    def test_func(self):
        if not self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    def get(self, *args, **kwargs):
        coupon_code = self.request.session.get('coupon_code', None)
        coupon_type = self.request.session.get('coupon_type',None)
        if self.request.LANGUAGE_CODE == "it":
            if not coupon_code or  coupon_type != "is_for_middle_school":
                url = reverse('index') + '?validate_discount_code=true'
                return HttpResponseRedirect(url)
        context = {}
        is_phone_view = self.request.session.get('is_phone_view', False)
        if is_phone_view:
            context['placeholder_of_first_name'] = _("Enter your first name")
            context['placeholder_of_last_name'] = _("Enter your last name")
            context['placeholder_of_phone_number'] = _("Enter your mobile number")

            context['placeholder_of_email'] = _("Parent’s E-mail ID")
            context['placeholder_of_password'] = _("Enter new password")
            template_name = "userauth/middle-school-mobile-first-stage.html"
        else:
            template_name = "userauth/middle-school-register-first-stage.html"
        context['first_stage_form'] = FuturelyFirstStageForm()
        return render(self.request, template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
        clarity_token = self.request.session.get('clarity_token', '')

        
        is_phone_view = self.request.session.get('is_phone_view', False)
        if is_phone_view:
            context["discount_code_placeholder"] = _("Enter the Discount Code")
            context["par_mobile_placeholder"] = _("Enter your Parent’s Number")
            context["par_name_mobile_placeholder"] = _("Enter your Parent’s Name")
            context["par_email_placeholder"] = _("Your Parent’s E-mail ID")
            template_name = "userauth/middle-school-mobile-first-stage.html"
            template_name_2 = "userauth/middle-school-mobile-second-stage.html"
        else:
            template_name = "userauth/middle-school-register-first-stage.html"
            template_name_2 = "userauth/middle-school-register-second-stage.html"

        if request.LANGUAGE_CODE == 'en-us':
            logger.info(f"In post view of middle-school-regitration-view called with language code : {request.LANGUAGE_CODE} : {custom_user_session_id}")
            school_country = 'USA'
            all_schools = CountryDetails.objects.filter(country='USA')
            email_html_content = "userauth/email_content.html"
        elif request.LANGUAGE_CODE == 'it':
            logger.info(f"In post view of middle-school-regitration-view called with language code : {request.LANGUAGE_CODE} : {custom_user_session_id}")
            school_country = 'Italy'
            all_schools = CountryDetails.objects.filter(country='Italy')
            email_html_content = "userauth/email_content-it.html"
        context['school_regions'] = all_schools.order_by('region').values('region').distinct()

        first_stage_form = FuturelyFirstStageForm(self.request.POST)
        second_stage_form = MiddleSchoolParentsDetailForm(request.POST or None)
        back_btn = request.POST.get("backbtn", "No")
        if back_btn == "Yes":
            context['first_stage_form'] = FuturelyFirstStageForm(self.request.POST)
            context["gender"] = request.POST.get('gender')
            context["countryCode"] = request.POST.get('countryCode', '')
            logger.info(f"Clicked on the backbutton on the middle-school-regitration-view by : {custom_user_session_id}")
            return render(request, "userauth/middle-school-register-first-stage.html" , context)
        otp = request.POST.get("otp", "")
        request_post = request.POST
        if first_stage_form.is_valid() or second_stage_form.is_valid():
            student_completion_form = StudentCompletionForm(request.POST or None)
            email = first_stage_form.cleaned_data.get("email")
            logger.info(f"In Post request - middle-school-regitration-view stage 1 : {email}")
            first_name = first_stage_form.cleaned_data.get("first_name")
            last_name = first_stage_form.cleaned_data.get("last_name")
            gender = first_stage_form.cleaned_data.get("gender")
            password = first_stage_form.cleaned_data.get("password")
            confirm_password = first_stage_form.cleaned_data.get("confirm_password")

            if password and confirm_password and password != confirm_password:
                first_stage_form.add_error('confirm_password', _('Passwords do not match.'))
                context['first_stage_form'] = first_stage_form
                context["student_completion_form"] = student_completion_form
                context["confirm_password_error_msg"] = _("Please enter the valid confirm password")
                return render(request, "userauth/middle-school-register-first-stage.html" , context)
                
            
            contact_number = first_stage_form.cleaned_data.get("contact_number")
            context["contact_number"] = contact_number
            context["email"] = email
            context["first_name"] = first_name
            context["last_name"] = last_name
            context["gender"] = gender
            context["password"] = password
            # context["confirm_password"]=confirm_password
            context['first_stage_form'] = first_stage_form
            context['second_stage_form'] = MiddleSchoolParentsDetailForm()
            context["student_completion_form"] = StudentCompletionForm()
            context["otp"] = otp
            context["countryCode"] = request.POST.get('countryCode')
            if request.LANGUAGE_CODE == 'en-us':
                school_country = 'USA'
                context['class_years'] = ClassYear.objects.filter(country='USA')
                context['specilizations'] = Specialization.objects.filter(country='USA')
                context['class_names'] = ClassName.objects.filter(country='USA')
                # context['school_cities'] = School.objects.filter(country="USA", is_verified=True)
            elif request.LANGUAGE_CODE == 'it':
                school_country = 'Italy'
                context['class_years'] = ClassYear.objects.filter(country=school_country)
                context['specilizations'] = Specialization.objects.filter(country='Italy')
                context['class_names'] = ClassName.objects.filter(country='Italy')
            if second_stage_form.is_valid() and student_completion_form.is_valid():
                logger.info(f"In Post request - futurelab registration stage 2 : {email}")
                is_discount_code = False
                school_region = ""
                school_city = ""
                school_name = ""
                school_type = ''
                context['second_stage_form'] = second_stage_form
                context["student_completion_form"] = student_completion_form
                discount_code = request.POST.get('future_lab_code')
                # discount_code = student_completion_form.cleaned_data.get("discount_coupon_code")
                number_of_plans = "3"
                skip_course_dependency = False
                is_course1_locked = False
                display_discounted_price_only = False
                is_fully_paid_by_school_or_company = False
                coupon_obj = None
                coupon_detail_obj = None
                is_100_per_coupon_code = False
                cohort_program1 = None
                cohort_program2 = None
                cohort_program3 = None
                hubspot_school_type = "free_channel"
                plan_name_from_coupon = None
                hubspot_is_for_middle_school = "None"
                try:
                    if discount_code.strip() == '':
                        context['second_stage_form'] = second_stage_form
                        context["student_completion_form"] = student_completion_form
                        context["discount_error_msg"] = _("Please enter the valid discount code")
                        logger.error(f"In Post request - middle-school-regitration-view stage 2 - discount code not found : {email}")
                        return render(request, template_name_2, context)
                    else:
                        coupon_code_status = check_discount_code_validation(request, discount_code)
                        if(coupon_code_status == False):
                            context['second_stage_form'] = second_stage_form
                            context["student_completion_form"] = student_completion_form
                            context["discount_error_msg"] = _("Please enter the valid discount code")
                            logger.error(f"In Post request - middle-school-regitration-view stage 2 - discount code not found : {email}")
                            return render(request, template_name_2, context)
                        logger.info(f"In Post request - middle-school-regitration-view stage 2 - To check discount code details : {email}")
                        coupon_obj = Coupon.objects.get(code__iexact=discount_code) # check the discount obj in coupon details
                        number_of_plans = coupon_obj.number_of_offered_plans
                        skip_course_dependency = coupon_obj.skip_course_dependency
                        is_course1_locked = coupon_obj.is_course1_locked
                        discount_code_end_date = coupon_obj.end_date
                        display_discounted_price_only = coupon_obj.display_discounted_price_only
                        is_fully_paid_by_school_or_company = coupon_obj.is_fully_paid_by_school_or_company
                        is_for_middle_school = coupon_obj.is_for_middle_school
                        if coupon_obj.is_for_middle_school:
                            hubspot_is_for_middle_school = "Yes"
                        else:
                            hubspot_is_for_middle_school = "No"
                        discount_type = coupon_obj.discount_type
                        discount_value = int(coupon_obj.discount_value)
                        if coupon_obj.is_fully_paid_by_school_or_company == True:
                            hubspot_school_type = "fully_paid"
                        else:
                            hubspot_school_type = "free_channel"
                        if discount_type == "Percentage" and discount_value == 100:
                            is_100_per_coupon_code = True
                        # is_discount_code = True
                        plan_name_from_coupon = coupon_obj.plan_type
                        if plan_name_from_coupon == "Master":
                            plan_name_from_coupon = "Elite"
                        coupon_detail_obj = CouponDetail.objects.filter(coupon=coupon_obj).first()
                        if coupon_detail_obj:
                            try:
                                school_region = coupon_detail_obj.school.region
                                school_city = coupon_detail_obj.school.city
                                school_name = coupon_detail_obj.school.name
                                school_type = coupon_detail_obj.school.type   
                                logger.info(f"In Post request - middle-school-regitration-view stage 2 - discount code details found : {email}")
                            except:
                                logger.warning(f"In Middle school coupon code: school is not linked with coupon code : {email}")
                        else:
                            logger.error(f"In Post request - middle-school-regitration-view stage 2 - discount code details not found : {email}")   
                except Exception as error:
                    context['second_stage_form'] = second_stage_form
                    context["student_completion_form"] = student_completion_form
                    context["discount_error_msg"] = _("Please enter the valid discount code")
                    logger.error(f"Error of discount_code at middle-school-regitration-view {error}: {email}")
                    return render(request, template_name_2, context)
                person_completion_form = FutureLabPersonRegisterForm(request.POST)
                if person_completion_form.is_valid():
                    person = person_completion_form.save(commit=False)
                    person.username = email
                    person.clarity_token = clarity_token
                    person.lang_code = request.LANGUAGE_CODE
                    student = student_completion_form.save(commit=False)
                    student.person = person
                    are_you_a_student = "Yes"
                    student.src = 'future_lab'
                    student.are_you_fourteen_plus = "Yes"
                    student.are_you_a_student = are_you_a_student
                    student.discount_coupon_code = discount_code
                    student.number_of_offered_plans = number_of_plans
                    student.skip_course_dependency = skip_course_dependency
                    student.is_course1_locked = is_course1_locked
                    student.display_discounted_price_only = display_discounted_price_only
                    student.is_from_middle_school = True
                    person.save()
                    logger.info(f"In Post request - middle-school-regitration-view stage 2 - Person saved : {email}")
                    student.student_channel = hubspot_school_type
                    student.save()
                    logger.info(f"In Post request - middle-school-regitration-view stage 2 - Person-Student infomation saved : {email}")
                    student_parents_form = second_stage_form.save(commit=False)
                    student_parents_form.student = student
                    student_parents_form.save()
                    logger.info(f"In Post request - middle school registration stage 2 - Person-Student-Parents infomation saved : {email}")
                    graduation_year = request_post.get('year', '')
                    class_year = request_post.get('class-year', '')
                    class_name = request_post.get('class-name', '')
                    class_specialization = request_post.get('class-specialization', '')
                    obj_stu_school_details = StudentSchoolDetail.objects.create(student=student, school_region=school_region, school_city=school_city, school_name=school_name, school_type=school_type)
                    logger.info(f"In Post request - middle-school-regitration-view stage 2 - Person-Student-school infomation saved : {email}")
                    try:
                        is_future_lab_student="false"   
                        local_tz = pytz.timezone(settings.TIME_ZONE)
                        dt_now = str(local_tz.localize(datetime.now()))
                        enrollDate=unixdateformat(datetime.now())
                        logger.info(f"In hubspot signup parameter building for : {person.username}")
                        keys_list = ['email','firstname', 'lastname', "hubspot_first_name", "course_country", "hubspot_are_you_a_student", "hubspot_check_tos", "hubspot_class_name",
                        "hubspot_class_specialization", "hubspot_class_year", "hubspot_contact_number", "hubspot_coupon_code_entered", "hubspot_email", "hubspot_how_know_us",
                        "hubspot_how_know_us_other", "hubspot_language_code", "hubspot_last_name", "hubspot_school_name", "hubspot_school_city", "hubspot_school_region", "hubspot_student_type",
                        "is_future_lab_student_registered", "is_student_registered", "hubspot_end_date_discount_code", "hubspot_enrollment_date", "hubspot_registration_url","hubspot_gender","hubspot_gender_other",
                        "hubspot_registration_parent_email","hubspot_registration_parent_phone_number","enroll_date","hubspot_school_type", "is_from_middle_school", "is_for_middle_school"]
                        values_list = [person.username,person.first_name,person.last_name, person.first_name, school_country, student.are_you_a_student, "Yes",
                         class_name, class_specialization, class_year, person.contact_number, student.discount_coupon_code, person.email, person.how_know_us, 
                         person.how_know_us_other, school_country, person.last_name, obj_stu_school_details.school_name,
                        obj_stu_school_details.school_city,  obj_stu_school_details.school_region, student.src, is_future_lab_student, 
                        True, str(discount_code_end_date), dt_now, self.request.build_absolute_uri(),gender,
                        "gender_other",student_parents_form.parent_email,student_parents_form.parent_contact_number,enrollDate,hubspot_school_type, "Yes", hubspot_is_for_middle_school]
                        create_update_contact_hubspot(person.username, keys_list, values_list)
                        logger.info(f"In hubspot middle-school-regitration-view parameter update completed for : {person.username}")
                    except Exception as error:
                        logger.error(f"Error at hubspot middle-school-regitration-view parameter update {error} for : {person.username}")
                    subject = _("Futurely - Verify your email address")
                    login(request,person)
                    request.session['notifymsg']=1
                    request.session['display_welcome_video']=1
                    if school_name:
                        create_custom_event(request, 2, meta_data={'school_name': school_name, 'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                        logger.info(f"Created custom event successfully middle-school-regitration-view for : {email}")
                    else:
                        create_custom_event(request, 2, meta_data={'ctype':request.session.get('ctype', 'general'), 'plan': request.session.get('plan', '')})
                        logger.info(f"Created custom event successfully for : {email}")
                    StudentPCTORecord.objects.create(student=student, pcto_hours=1, pcto_hour_source="Future-lab")
                    logger.info(f"In Post request - middle-school-regitration-view stage 2 - Student PCTO hours added : {email}")
                    student.update_total_pcto_hour()
                    if request.LANGUAGE_CODE == 'it':
                        status=send_email_message(request,person,subject,'userauth/email_content-it.html')
                    else:
                        status=send_email_message(request,person,subject,'userauth/email_content.html')
                    if person:
                        notification_type_objs = Notification_type.objects.all()
                        for single_notification_type in notification_type_objs:
                            PersonNotification.objects.update_or_create(
                                person=person, notification_type=single_notification_type)

                    lang_code = request.LANGUAGE_CODE
                    if is_fully_paid_by_school_or_company == True and is_100_per_coupon_code == True:
                        selected_plan = OurPlans.objects.filter(plan_lang=lang_code, plan_name=plan_name_from_coupon).first()
                        if lang_code == 'en-us':
                            currency = 'usd'
                        elif lang_code == 'it':
                            currency = 'eur'
                        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
                        Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                                    plan=selected_plan, coupon_code=coupon_obj.code, actual_amount=selected_plan.cost, discount=selected_plan.cost, custom_user_session_id=custom_user_session_id)
                        logger.info(f"payment obj updated for : {email} with 100 per coupon code {coupon_obj.code}")
                        stu_pln_obj, stu_pln_obj_created = StudentsPlanMapper.plansManager.lang_code(lang_code).update_or_create(
                            student=person, plan_lang=lang_code, defaults={'plans': selected_plan})
                        logger.info(f"student plan mapper obj update_or_create at middle-school-regitration-view for : {email}")
                        try:
                            if plan_name_from_coupon == "Premium":
                                cohort_program1 = coupon_detail_obj.cohort_program1
                            else:
                                cohort_program1 = coupon_detail_obj.cohort_program1
                                cohort_program2 = coupon_detail_obj.cohort_program2
                                if request.LANGUAGE_CODE == "it":
                                    cohort_program3 = coupon_detail_obj.cohort_program3
                        except Exception as er:
                            logger.warning(f"Coupon code does not have any linked cohort at middle-school-regitration-view - {er} for : {email}")
                        if cohort_program1:
                            StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program1, stu_cohort_lang=request.LANGUAGE_CODE)
                            logger.info(f"student cohort mapper obj 1 created at middle-school-regitration-view for : {email}")
                            exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id])
                            # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id)
                            # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id)
                            request.session['is_first_time_on_dashboard'] = True
                        if cohort_program2:
                            StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program2, stu_cohort_lang=request.LANGUAGE_CODE)
                            logger.info(f"student cohort mapper obj 2 created at middle-school-regitration-view for : {email}")
                            exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id])
                            # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id)
                            # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id)
                        if cohort_program3:
                            StudentCohortMapper.objects.create(student=request.user, cohort=cohort_program3, stu_cohort_lang=request.LANGUAGE_CODE)
                            logger.info(f"student cohort mapper obj 3 created at middle-school-regitration-view for : {email}")
                            exercise_cohort_step_tracker_creation.apply_async(args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id])
                            # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id)
                            # link_with_action_items.delay(request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id)
                        # student.discount_coupon_code = ""
                        student.save()
                        try:
                            # hubspotContactupdateQueryAdded
                            logger.info(f"In hubspot plan/cohort enroll middle-school-regitration-view building for : {request.user.username}")
                            if plan_name_from_coupon =='Premium':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    premiumPlanEnrollDate=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    premiumPlanEnrollDate=unixdateformat(stu_pln_obj.modified_at)
                                
                                coupon_end_date=unixdateformat(coupon_obj.end_date)
                                Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
                                keys_list = ["email","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount","hubspot_applied_discount_code",'hubspot_cohort_name_premium',
                                'premium_plan_enroll_date','end_date_discount_code','hubspot_cohort_premium_start_date']
                                values_list = [request.user.username, plan_created_at, "0",coupon_obj.code,cohort_program1.cohort_name,
                                premiumPlanEnrollDate,coupon_end_date,Hubspot_cohort_premium_start_date]
                                create_update_contact_hubspot(request.user.username, keys_list, values_list)
                            if plan_name_from_coupon =='Elite':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    elitePlanEnrollDate=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    elitePlanEnrollDate=unixdateformat(stu_pln_obj.modified_at)
                                keys_list = ["email","elite_plan_enroll_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code"]
                                values_list = [request.user.username,elitePlanEnrollDate,plan_created_at, "0",coupon_obj.code]
                                end_date_discount_code=unixdateformat(coupon_obj.end_date)
                                keys_list.append('end_date_discount_code')
                                values_list.append(end_date_discount_code)
                                if cohort_program1:
                                    keys_list.append('hubspot_cohort_name_premium')
                                    values_list.append(cohort_program1.cohort_name)
                                    Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
                                    keys_list.append('hubspot_cohort_premium_start_date')
                                    values_list.append(Hubspot_cohort_premium_start_date)
                                if cohort_program2:
                                    keys_list.append('hubspot_cohort_name_elite1')
                                    values_list.append(cohort_program2.cohort_name)
                                    Hubspot_cohort_elite1_start_date=unixdateformat(cohort_program2.starting_date)
                                    keys_list.append('hubspot_cohort_elite1_start_date')
                                    values_list.append(Hubspot_cohort_elite1_start_date)
                                    # elite_plan_enroll_date=unixdateformat(plan_created_at)
                                    # keys_list.append('elite_plan_enroll_date')
                                    # values_list.append(elite_plan_enroll_date)
                                if cohort_program3:
                                    keys_list.append('hubspot_cohort_name_elite2')
                                    values_list.append(cohort_program3.cohort_name)
                                    Hubspot_cohort_elite2_start_date=unixdateformat(cohort_program3.starting_date)
                                    keys_list.append('hubspot_cohort_elite2_start_date')
                                    values_list.append(Hubspot_cohort_elite2_start_date)
                                create_update_contact_hubspot(request.user.username, keys_list, values_list)
                            logger.info(f"hubspot plan/cohort enroll at middle-school-regitration-view complete for : {request.user.username}")
                        except Exception as ex:
                            logger.error(f"Error at hubspot plan/cohort enroll at middle-school-regitration-view  {ex} for : {request.user.username}")
                            return redirect(reverse("home"))
                    check_payment_obj = Payment.objects.filter(payment_email_id=email, status__in=["active", "succeeded"], plan__plan_lang=lang_code).order_by("-plan__id")
                    if check_payment_obj.count() > 0:
                        if(status == True):
                            Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                            logger.info(f"Email sent and User created middle-school-regitration-view page-post : {email}")
                        else:
                            Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                            context["message"] = _("Error to send mail to verify Email, Please check email id")
                            logger.error(f"Error Email not sent and user created middle-school-regitration-view page-post : {email}")
                        one_time_payment_check_obj = check_payment_obj.filter(payment_subscription_type="One Time")
                        if one_time_payment_check_obj.count() > 0:
                            one_time_payment_obj = one_time_payment_check_obj.first()
                            if one_time_payment_obj.person is None:
                                # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=one_time_payment_obj.plan)
                                Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                one_time_payment_obj.person = person
                                one_time_payment_obj.save()
                                logger.info(f"at middle-school-regitration-view user mapped with StudentPlanMapper and Payment type(One Time) : {email}")
                                return HttpResponseRedirect(reverse("home"))
                        
                        weekly_person_pay_check_obj = check_payment_obj.filter(payment_subscription_type="Weekly")
                        if weekly_person_pay_check_obj.count() > 0:
                            for weekkly_obj in weekly_person_pay_check_obj:
                                pid_paysubdetail = weekkly_obj.paymentsubscriptiondetail.filter(invoice_status="paid")
                                if pid_paysubdetail.count() > 0:
                                    if weekkly_obj.person is None:
                                        # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                        StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=weekkly_obj.plan)
                                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                        weekkly_obj.person = person
                                        weekkly_obj.save()
                                        break
                            logger.info(f"At middle-school-regitration-view user mapped with StudentPlanMapper and Payment type(Weekly) : {email}")
                            return HttpResponseRedirect(reverse("home"))

                    if(status == True):
                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                        logger.info(f"Email sent and User created middle-school-regitration-view page-post : {email}")
                        return HttpResponseRedirect(reverse("futurely-plans"))
                    else:
                        Stu_Notification.objects.create(student=person, title=_("Error to send verification mail to verify Email, Please check email id"))
                        context["message"] = _("Error to send mail to verify Email, Please check email id")
                        logger.error(f"Error Email not sent and user created middle-school-regitration-view page-post : {email}")
                    one_time_payment_check_obj = check_payment_obj.filter(payment_subscription_type="One Time")
                    if one_time_payment_check_obj.count() > 0:
                        one_time_payment_obj = one_time_payment_check_obj.first()
                        if one_time_payment_obj.person is None:
                            # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                            StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=one_time_payment_obj.plan)
                            Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                            one_time_payment_obj.person = person
                            one_time_payment_obj.save()
                            logger.info(f"At middle-school-regitration-view user mapped with StudentPlanMapper and Payment type(One Time) : {email}")
                            is_from_mobile_app = request.session.get('is_from_mobile_app', False)
                            if is_from_mobile_app:
                                get_cohort = StudentCohortMapper.objects.filter(student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                                if get_cohort:
                                    return HttpResponseRedirect(reverse("home")+ '?cohort_name='+get_cohort.cohort.cohort_name)
                            return HttpResponseRedirect(reverse("home"))
                    
                    weekly_person_pay_check_obj = check_payment_obj.filter(payment_subscription_type="Weekly")
                    if weekly_person_pay_check_obj.count() > 0:
                        for weekkly_obj in weekly_person_pay_check_obj:
                            pid_paysubdetail = weekkly_obj.paymentsubscriptiondetail.filter(invoice_status="paid")
                            if pid_paysubdetail.count() > 0:
                                if weekkly_obj.person is None:
                                    # If the payment is weekly them we need get the paymentsubdet from with Payment obj and check the invoice status (PAID)and mao the plan! 
                                    StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(student=person, plans=weekkly_obj.plan)
                                    Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                                    weekkly_obj.person = person
                                    weekkly_obj.save()
                                    break
                        logger.info(f"middle-school-regitration-view user mapped with StudentPlanMapper and Payment type(Weekly) : {email}")
                        is_from_mobile_app = request.session.get('is_from_mobile_app', False)
                        if is_from_mobile_app:
                            get_cohort = StudentCohortMapper.objects.filter(student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                            if get_cohort:
                                return HttpResponseRedirect(reverse("home")+ '?cohort_name='+get_cohort.cohort.cohort_name)
                        return HttpResponseRedirect(reverse("home"))

                    if(status == True):
                        Stu_Notification.objects.create(student=person, title=_("An email has been sent to you, please confirm your email address"))
                        logger.info(f"Email sent and User created middle-school-regitration-view page-post : {email}")
                        return HttpResponseRedirect(reverse("futurely-plans"))
                    else:
                        context["first_stage_form"] = FuturelyFirstStageForm(self.request.POST)
                        return render(request, template_name, context)

            if Person.objects.filter(username=email).exists():
                context["email_error"] = _("The email already exists in the system")
                context['first_stage_form'] = first_stage_form
                logger.warning(f"Email already exist in the system at middle-school-regitration-view for : {email}")
                return render(request, template_name, context)
            context['second_stage_form'] = second_stage_form
            context["student_completion_form"] = StudentCompletionForm()
            return render(request, template_name_2, context)
        else:
            context["first_stage_form"] = FuturelyFirstStageForm(self.request.POST)
            return render(request, template_name, context)


def check_coupon_view(request):
    if request.method == 'POST':
        try:
            coupon_code = request.POST.get('coupon_code')
            if coupon_code:
                local_tz = pytz.timezone(settings.TIME_ZONE)
                dt_now = local_tz.localize(datetime.now())
                coupon = Coupon.objects.filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), Q(code__iexact=coupon_code)).first()
                # coupon = Coupon.objects.get(code=coupon_code)
                if coupon:
                    if coupon.is_for_fast_track_program == True:
                        request.session['coupon_code'] = coupon_code
                        request.session['coupon_type'] = coupon.coupon_type
                        logger.info(f"Coupon Code is of type Fast Track {coupon_code}")
                        return JsonResponse({'is_valid': True, 'redirect_url': 'is_for_fast_track_program'})
                    elif coupon.is_for_middle_school == True:
                        request.session['coupon_code'] = coupon_code
                        request.session['coupon_type'] = f"is_for_middle_school"
                        logger.info(f"Coupon Code is of type Middle School {coupon_code}")
                        return JsonResponse({'is_valid': True, 'redirect_url': 'is_for_middle_school'})
                    elif coupon.coupon_type == 'FutureLab':
                        request.session['coupon_code'] = coupon_code
                        request.session['coupon_type'] = coupon.coupon_type
                        logger.info(f"Coupon Code is of type FutureLab {coupon_code}")
                        return JsonResponse({'is_valid': True, 'redirect_url': 'futurelab_signup_new'})
                        # return HttpResponseRedirect(reverse("futurelab_signup_new"))
                    elif coupon.coupon_type == 'Organization':
                        request.session['ctype'] = "company"
                        request.session['coupon_code'] = coupon_code
                        request.session['coupon_type'] = coupon.coupon_type
                        logger.info(f"Coupon Code is of type Organization {coupon_code}")
                        return JsonResponse({'is_valid': True, 'redirect_url': 'organization_coupon'})
                else:
                    return JsonResponse({'is_valid': False})
        except Exception as exp:
            return JsonResponse({'is_valid': False})
    return JsonResponse({'is_valid': False})
