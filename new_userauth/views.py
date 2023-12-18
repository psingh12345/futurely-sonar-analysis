from django.http import JsonResponse
from axes.models import AccessAttempt
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.http import (
    url_has_allowed_host_and_scheme, urlsafe_base64_decode,
)
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from userauth.models import MasterOTP, Person, Student, StudentSchoolDetail, School, Company, ClassName, ClassYear, Specialization, Counselor, CountryDetails, StudentParentsDetail
from .forms import UserRegistrationForm, StudentCompletionForm, UserOnboardingRegisterForm, ForgotPasswordSetForm, FormWithCaptcha
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
)
from student.models import StudentsPlanMapper, StudentCohortMapper, StudentPCTORecord
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from courses.models import Modules, Cohort, Notification_type, OurPlans, PlanNames
from .helpers import check_discount_code_validation, send_email_message
from lib.hubspot_contact_sns import create_update_contact_hubspot
from student.models import Stu_Notification, PersonNotification
from student.tasks import exercise_cohort_step_tracker_creation, exercise_cohort_step_tracker_creation_without_celery
from django.contrib.auth import login, authenticate, logout, REDIRECT_FIELD_NAME, get_user_model, update_session_auth_hash
from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from payment.models import Coupon, CouponDetail, Payment
from lib.unixdateformatConverter import unixdateformat
from django.views.generic import View, TemplateView
from django.views.generic.edit import FormView
from django.utils.translation import ugettext as _
from userauth.forms import PasswordResttingForm
from django.urls import reverse, reverse_lazy
from lib.helper import create_custom_event
from django.conf import settings
from django.db.models import Q
from datetime import datetime
import logging
import pytz
from website.models import ParentInfo
from lib.custom_logging import CustomLoggerAdapter
import traceback
import json
import requests


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

logger_console_adapter = logging.getLogger('console')
logger_console = CustomLoggerAdapter(logger_console_adapter, {})


class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context


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

class PersonRegisterView(UserPassesTestMixin, View):

    template_name = "new_userauth/Registrati-come-studente.html"

    def test_func(self):
        if not self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    def get(self, request):
        context = {}
        request.session['lang'] = "it"
        logger.info("PersonRegisterView: get")
        return render(self.request, self.template_name, context)

    def post(self, request):
        context = {}
        first_stage = request.POST.get('first_stage', 'No')
        second_stage = request.POST.get('second_stage', 'No')
        third_stage = request.POST.get('third_stage', 'No')
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
        clarity_token = self.request.session.get('clarity_token', '')
        if first_stage == 'Yes' and second_stage == 'No' and third_stage == 'No':
            coupon_code = request.POST.get('discount_code')
            if coupon_code:
                local_tz = pytz.timezone(settings.TIME_ZONE)
                dt_now = local_tz.localize(datetime.now())
                coupon = Coupon.objects.filter(Q(start_date__lte=dt_now), Q(
                    end_date__gte=dt_now), Q(is_active=True), Q(code__iexact=coupon_code), Q(is_fully_paid_by_school_or_company=True)).first()
                coupon_detail_obj = CouponDetail.objects.filter(
                        coupon=coupon)
                if coupon_detail_obj.count() > 0 and coupon:
                    request.session['coupon_code'] = coupon_code
                    context['user_resgiter_form'] = UserRegistrationForm()
                    context['coupon_code'] = coupon_code
                    context['coupon_code_obj'] = coupon
                    if coupon.is_for_middle_school:
                        request.session['is_for_middle_school'] = True
                    return render(request, 'new_userauth/register1.html', context)
            error_message = "Il codice sconto non è corretto. Riprova oppure chiedi spiegazioni alla tua scuola o azienda"
            return render(request, self.template_name, {'coupon_code': coupon_code, 'error_message': error_message})
        elif first_stage == 'Yes' and second_stage == 'Yes' and third_stage == 'No':
            user_register_form = UserRegistrationForm(request.POST)
            context['user_resgiter_form'] = user_register_form
            email = request.POST.get('email', '')
            if user_register_form.is_valid():
                email = user_register_form.cleaned_data.get('email')
                coupon_code = request.session.get('coupon_code', None)
                if coupon_code:
                    coupon_detail = CouponDetail.objects.filter(
                        coupon__code=coupon_code).first()
                    if coupon_detail:
                        context['coupon_detail_obj'] = coupon_detail
                        context['coupon_code_obj'] = coupon_detail.coupon
                    else:
                        error_message = "Il codice sconto non è corretto. Riprova oppure chiedi spiegazioni alla tua scuola o azienda"
                        return render(request, self.template_name, {'coupon_code': coupon_code, 'error_message': error_message})    
                else:
                    error_message = "Il codice sconto non è corretto. Riprova oppure chiedi spiegazioni alla tua scuola o azienda"
                    return render(request, self.template_name, {'coupon_code': coupon_code, 'error_message': error_message})
                if Person.objects.filter(email=email).exists():
                    context['error_message'] = "L’e-mail inserita è già utilizzata. Riprova con una nuova e-mail."
                    context['email_error'] = "Yes"
                    context['user_resgiter_form'] = user_register_form
                    return render(request, 'new_userauth/register1.html', context)

                # are_you_fourteen_plus = request.POST.get(
                #     'are_you_fourteen_plus', 'No')
                # if are_you_fourteen_plus == 'No':
                #     context['are_you_fourteen_plus_error'] = "Error : 'Are you fourteen plus'"
                #     return render(request, 'new_userauth/register1.html', context)
                are_you_fourteen_plus = "Yes"
                password = user_register_form.cleaned_data.get('password')
                context['password'] = password
                context['user_resgiter_form'] = user_register_form
                all_companies = []
                companies_list = []
                school_names = []
                
                context['school_names'] = school_names
                context['companies'] = companies_list

                logger.info(
                    f"In post view of user-regitration-view called with language code : {request.LANGUAGE_CODE} : {email}")
                school_country = 'Italy'
                all_schools = CountryDetails.objects.filter(
                    country='Italy')
                all_companies = Company.objects.filter(country='Italy')
                context['companies'] = all_companies
                context['specilizations'] = Specialization.objects.filter(
                    country='Italy')
                context['class_names'] = ClassName.objects.filter(
                    country='Italy')
                context['class_years'] = ClassYear.objects.filter(
                    country='Italy')
                context['schools'] = School.objects.filter(
                    country=school_country).order_by('name')
                context['school_regions'] = all_schools.order_by(
                    'region').values('region').distinct()
                context['student_completion_form'] = StudentCompletionForm()
                return render(request, 'new_userauth/register2.html', context)
            logger.warning(f"User did not enter the valid data : {email}")
            return render(request, 'new_userauth/register1.html', context)

        elif first_stage == 'Yes' and second_stage == 'Yes' and third_stage == 'Yes':
            """ Final Registration"""
            user_register_form = UserRegistrationForm(request.POST)
            student_completion_form = StudentCompletionForm(request.POST)
            email = request.POST.get('email', '')
            coupon_code = request.session.get('coupon_code', None)
            is_coupon_code_exists = True
            coupon_objs = None
            coupon_detail_obj = None
            if coupon_code:
                coupon_objs = Coupon.objects.filter(code__iexact=coupon_code)
                if coupon_objs.count() > 0:
                    coupon_obj = coupon_objs.first()
                    coupon_detail_obj = CouponDetail.objects.filter(
                        coupon=coupon_obj).first()
                    if coupon_detail_obj:
                        context['coupon_detail_obj'] = coupon_detail_obj
                    else:
                        is_coupon_code_exists = False
                else:
                    is_coupon_code_exists = False
            else:
                is_coupon_code_exists = False
                logger.warning(
                    f"In Post request - registration stage 3 - coupon code is not found in the session for : {email}")
            if is_coupon_code_exists is False:
                error_message = "Il codice sconto non è corretto. Riprova oppure chiedi spiegazioni alla tua scuola o azienda"
                return render(request, self.template_name, {'coupon_code': coupon_code, 'error_message': error_message})    
            logger.info(
                f"In post view of user-regitration-view stage 3 called with language code : {request.LANGUAGE_CODE} : {email}")
            school_country = 'Italy'
            all_schools = CountryDetails.objects.filter(country='Italy')
            all_companies = Company.objects.filter(country='Italy')
            context['companies'] = all_companies
            context['specilizations'] = Specialization.objects.filter(
                country='Italy')
            context['class_names'] = ClassName.objects.filter(
                country='Italy')
            context['class_years'] = ClassYear.objects.filter(
                country='Italy')
            context['schools'] = School.objects.filter(
                country=school_country).order_by('name')
            number_of_plans = "3"
            skip_course_dependency = False
            is_course1_locked = False
            display_discounted_price_only = False
            is_fully_paid_by_school_or_company = False
            coupon_obj = None
            is_100_per_coupon_code = False
            cohort_program1 = None
            cohort_program2 = None
            cohort_program3 = None
            hubspot_school_type = "free_channel"
            plan_type_from_coupon = None
            student_company = None
            coupon_obj = coupon_objs.first()
            # coupon_obj = Coupon.objects.get(code__iexact=coupon_code)
            number_of_plans = coupon_obj.number_of_offered_plans
            skip_course_dependency = coupon_obj.skip_course_dependency
            is_course1_locked = coupon_obj.is_course1_locked
            discount_code_end_date = coupon_obj.end_date
            display_discounted_price_only = coupon_obj.display_discounted_price_only
            is_fully_paid_by_school_or_company = coupon_obj.is_fully_paid_by_school_or_company
            hubspot_plan_name = None
            hubspot_cohort_name_FT = None
            hubspot_cohort_name_MSP = None
            hubspot_cohort_startdate = None
            hubspot_cohort_name_JOB = None
            hubspot_is_from_fast_track_program = "None"
            hubspot_is_for_fast_track_program = "None"
            hubspot_student_parent_email_missing_from_landing=None
            hubspot_student_parent_email_from_landing_exists=None
            hubspot_student_parent_email_from_landing=None
            bit_other_school = False
            sponsor_compnay = None
            discount_type = coupon_obj.discount_type
            discount_value = int(coupon_obj.discount_value)
            if is_fully_paid_by_school_or_company == True:
                hubspot_school_type = "fully_paid"
                is_100_per_coupon_code = True
                discount_type = "Percentage"
            else:
                hubspot_school_type = "free_channel"
            # is_discount_code = True
            plan_type_from_coupon = coupon_obj.plan_type
            plan_name_from_coupon = coupon_obj.plan.title
            hubspot_plan_name = plan_name_from_coupon
            if plan_type_from_coupon == "Master":
                plan_type_from_coupon = "Elite"
            is_from_fast_track_program = False
            is_from_middle_school = False
            is_from_job_course = False
            if plan_type_from_coupon == PlanNames.FastTrack.value:
                is_from_fast_track_program = True

            if plan_type_from_coupon == PlanNames.MiddleSchool.value:
                is_from_middle_school = True

            if plan_type_from_coupon == PlanNames.JobCourse.value:
                is_from_job_course = True
                if coupon_detail_obj.sponsor_compnay:
                    sponsor_compnay = coupon_detail_obj.sponsor_compnay
            
            #Code if previous coupon code is used Premium Fast track
            if is_from_fast_track_program is False:
                is_from_fast_track_program = coupon_detail_obj.coupon.is_for_fast_track_program
            if is_from_middle_school is False:
                is_from_middle_school = coupon_detail_obj.coupon.is_for_middle_school

            if is_from_fast_track_program:
                hubspot_cohort_name_FT = coupon_detail_obj.cohort_program1.cohort_name
                hubspot_cohort_startdate = coupon_detail_obj.cohort_program1.starting_date
            elif is_from_middle_school:
                hubspot_cohort_name_MSP = coupon_detail_obj.cohort_program1.cohort_name
                hubspot_cohort_startdate = coupon_detail_obj.cohort_program1.starting_date
            elif is_from_job_course:
                hubspot_cohort_name_JOB = coupon_detail_obj.cohort_program1.cohort_name
                hubspot_cohort_startdate = coupon_detail_obj.cohort_program1.starting_date

            if is_from_fast_track_program:
                hubspot_is_from_fast_track_program = "Yes"
                hubspot_is_for_fast_track_program = "Yes"
            else:
                hubspot_is_from_fast_track_program = "No"
                hubspot_is_for_fast_track_program = "No"

            if coupon_detail_obj.company:
                student_company = coupon_detail_obj.company
            if coupon_detail_obj.school:
                school_region = coupon_detail_obj.school.region
                school_city = coupon_detail_obj.school.city
                school_name = coupon_detail_obj.school.name
                school_type = coupon_detail_obj.school.type

            else:
                school_region = request.POST.get(
                    'school-region', '')
                school_city = request.POST.get('school-city', '')
                school_name = request.POST.get('school-name', '')
                school_name_other = request.POST.get(
                    'school_name_other', '')
                if school_name == "Altro" or school_name == "Other":
                    school_name = school_name_other
                    bit_other_school = True
                school_type = request.POST.get('school-type', '')
            logger.info(
                f"In Post request - registration stage 3 - discount code details found : {email}")
            if user_register_form.is_valid() and student_completion_form.is_valid():
                gender = user_register_form.cleaned_data.get('gender')
                age = user_register_form.cleaned_data.get('age')
                terms_checkbox = request.POST.get('terms_checkbox')
                data_track_checkbox = request.POST.get('data_track_checkbox')
                third_partiest_checkbox = request.POST.get(
                    'third_partiest_checkbox')
                data_marketing_checkbox = request.POST.get(
                    'data_marketing_checkbox')
                password = user_register_form.cleaned_data.get('password')
                if terms_checkbox is None:
                    logger.warning(
                        f"User not accepted terms and conditions : {email}")
                    context['terms_checkbox_error'] = True
                    context['school_regions'] = all_schools.order_by(
                        'region').values('region').distinct()
                    context['password'] = password
                    context['student_completion_form'] = student_completion_form
                    context['user_resgiter_form'] = user_register_form
                    # return render(request, 'new_userauth/register2.html', {'student_completion_form': student_completion_form, 'user_resgiter_form': user_register_form})
                    return render(request, 'new_userauth/register2.html', context)

                data_track_checkbox = data_track_checkbox == 'on'
                third_partiest_checkbox = third_partiest_checkbox == 'on'
                data_marketing_checkbox = data_marketing_checkbox == 'on'

                # is_for_middle_school = request.session.get('is_for_middle_school', False)
                parent_name = ""
                if is_from_middle_school:
                    parent_email = request.POST.get('email', '')
                    parent_name = f"{request.POST.get('parent_first_name', '')} {request.POST.get('parent_last_name', '')}"
                else:
                    parent_email = request.POST.get('parent_email', '')
                    parent_name = f"{request.POST.get('parent_first_name', '')} {request.POST.get('parent_last_name', '')}"
                parent_contact_number = request.POST.get(
                    'parent_contact_number', '')
                if parent_email == "":
                    logger.warning(f"Parent email is empty : {email}")
                    context['school_regions'] = all_schools.order_by('region').values('region').distinct()
                    context['password'] = password
                    context['student_completion_form'] = student_completion_form
                    context['user_resgiter_form'] = user_register_form
                    return render(request, 'new_userauth/register2.html',context)
                person_completion_form = UserOnboardingRegisterForm(
                    request.POST)
                if person_completion_form.is_valid():
                    person = person_completion_form.save(commit=False)
                    person.username = email
                    person.lang_code = request.LANGUAGE_CODE
                    person.clarity_token = clarity_token
                    # are_you_a_student = student_completion_form.cleaned_data.get("are_you_a_student")
                    student = student_completion_form.save(commit=False)
                    student.person = person
                    # if are_you_a_student == "No" or are_you_a_student == "" or are_you_a_student == "no":
                    are_you_a_student = "Yes"
                    if coupon_obj.coupon_type == "Organization":
                        student.src = "company"
                    elif coupon_obj.coupon_type == "FutureLab":
                        student.src = 'future_lab'
                    else:
                        student.src = "general"
                    student.are_you_fourteen_plus = "Yes"
                    student.are_you_a_student = are_you_a_student
                    student.discount_coupon_code = coupon_code
                    student.number_of_offered_plans = number_of_plans
                    student.skip_course_dependency = skip_course_dependency
                    student.is_course1_locked = is_course1_locked
                    student.is_from_fast_track_program = is_from_fast_track_program
                    student.is_from_middle_school = is_from_middle_school
                    student.display_discounted_price_only = display_discounted_price_only
                    if student_company:
                        student.company = student_company
                    if sponsor_compnay:
                        student.sponsor_compnay = sponsor_compnay
                    person.save()
                    logger.info(
                        f"In Post request - new registration stage 2 - Person saved : {email}")
                    student.student_channel = hubspot_school_type
                    student.privacy_policy_mandatory = True
                    student.accept_tracking = data_track_checkbox
                    student.accept_data_third_party = third_partiest_checkbox
                    student.accept_marketing = data_marketing_checkbox
                    student.age = age
                    student.save()
                    hubspot_registration_parent_email = parent_email
                    logger.info(
                        f"In Post request - new registration stage 3 - Person-Student infomation saved : {email}")
                    StudentParentsDetail.objects.create(
                        student=student, parent_email=parent_email, parent_contact_number=parent_contact_number, parent_name=parent_name)
                    try:
                        if coupon_obj.coupon_type == "Organization":
                            student_already_exist = ParentInfo.objects.filter(Q(child_email=email) | Q(child_name=f"{person.first_name} {person.last_name}") | Q(child_name=f"{person.last_name} {person.first_name}")).first()
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
                                logger.error(f"{msg}")
                    except Exception as exp_parents_link:
                        logger.error(f"Error - {exp_parents_link} - to link student with parents info during registration for : {email}")
                    logger.info(
                        f"In Post request - futurelab registration stage 2 - Person-Student-Parents infomation saved : {email}")
                    request_post = request.POST
                    graduation_year = request_post.get('year', '')
                    class_year = request_post.get('class-year', '')
                    class_name = request_post.get('class-name', '')
                    class_specialization = request_post.get(
                        'class-specialization', '')
                    obj_stu_school_details = StudentSchoolDetail.objects.create(
                        student=student, school_region=school_region, school_city=school_city, school_name=school_name, school_type=school_type, graduation_year=graduation_year)
                    if class_year:
                        try:
                            obj_class_year = ClassYear.objects.get(
                                pk=class_year)
                            obj_stu_school_details.class_year = obj_class_year
                        except Exception as exx:
                            print(str(exx))
                            logger.warning(
                                f"Error of class-year at person-register-view {exx}: {email}")
                    if class_name:
                        try:
                            obj_class_name = ClassName.objects.get(
                                pk=class_name)
                            obj_stu_school_details.class_name = obj_class_name
                        except Exception as error:
                            print(str(error))
                            logger.warning(
                                f"Error of class_name at person-register-view {error}: {email}")
                    if class_specialization:
                        try:
                            obj_class_specialization = Specialization.objects.get(
                                pk=class_specialization)
                            obj_stu_school_details.specialization = obj_class_specialization
                        except Exception as error:
                            print(str(error))
                            logger.warning(
                                f"Error of class-specialization at person-register-view {error}: {email}")
                    obj_stu_school_details.save()
                    if bit_other_school:
                        School.objects.create(name=school_name, city = school_city, region = school_region, type = school_type, country= school_country)
                    submit_hubspot_form_with_email(request, email)

                    logger.info(
                        f"In Post request - futurelab registration stage 2 - Person-Student-school infomation saved : {email}")
                    try:
                        is_future_lab_student = "false"
                        local_tz = pytz.timezone(settings.TIME_ZONE)
                        dt_now = str(local_tz.localize(datetime.now()))
                        enrollDate = unixdateformat(datetime.now())
                        logger.info(
                            f"In hubspot signup parameter building for : {person.username}")
                        keys_list = ['email', 'firstname', 'lastname', "hubspot_first_name", "course_country", "hubspot_are_you_a_student", "hubspot_check_tos", "hubspot_class_name",
                                     "hubspot_class_specialization", "hubspot_class_year", "hubspot_contact_number", "hubspot_coupon_code_entered", "hubspot_email", "hubspot_how_know_us",
                                     "hubspot_how_know_us_other", "hubspot_language_code", "hubspot_last_name", "hubspot_school_name", "hubspot_school_city", "hubspot_school_region", "hubspot_student_type",
                                     "is_future_lab_student_registered", "is_student_registered", "hubspot_end_date_discount_code", "hubspot_enrollment_date", "hubspot_registration_url", "hubspot_gender", "hubspot_gender_other",
                                     "hubspot_registration_parent_email", "enroll_date", "hubspot_school_type", "hubspot_is_for_fast_track_program", "hubspot_is_from_fast_track_program"]
                        values_list = [person.username, person.first_name, person.last_name, person.first_name, school_country, student.are_you_a_student, "Yes", class_name, class_specialization, class_year, person.contact_number, student.discount_coupon_code, person.email, person.how_know_us, person.how_know_us_other, school_country, person.last_name, obj_stu_school_details.school_name,
                                       obj_stu_school_details.school_city,  obj_stu_school_details.school_region, student.src, is_future_lab_student, True, str(discount_code_end_date), dt_now, self.request.build_absolute_uri(), gender, "gender_other", parent_email, enrollDate, hubspot_school_type, hubspot_is_for_fast_track_program, hubspot_is_from_fast_track_program]
                        keys_list_parents = ['email','is_a_parents','hubspot_is_for_fast_track_program','hubspot_is_from_fast_track_program']
                        values_list_parents = [parent_email,'true', hubspot_is_for_fast_track_program,hubspot_is_from_fast_track_program]
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


                        logger.info(
                            f"In hubspot signup parameter update student contact : {person.username}")
                        create_update_contact_hubspot(
                            person.username, keys_list, values_list)
                        create_update_contact_hubspot(parent_email, keys_list_parents, values_list_parents)
                        logger.info(
                            f"In hubspot signup parameter update completed for : {person.username}")
                    except Exception as error:
                        logger.error(
                            f"Error at hubspot signup parameter update {error} for : {person.username}")
                    subject = _("Futurely - Verify your email address")
                    login(request, person)
                    # if is_from_job_course:
                    #     request.session['is_from_job_course'] = True
                    request.session['notifymsg'] = 1
                    if is_from_fast_track_program or is_from_job_course:
                        request.session['display_welcome_video'] = 1
                    
                    if school_name:
                        create_custom_event(request, 2, meta_data={'school_name': school_name, 'ctype': request.session.get(
                            'ctype', 'general'), 'plan': request.session.get('plan', '')})
                        logger.info(
                            f"Created custom event successfully for : {email}")
                    else:
                        create_custom_event(request, 2, meta_data={'ctype': request.session.get(
                            'ctype', 'general'), 'plan': request.session.get('plan', '')})
                        logger.info(
                            f"Created custom event successfully for : {email}")
                    # StudentPCTORecord.objects.create(
                    #     student=student, pcto_hours=1, pcto_hour_source="Future-lab")
                    # logger.info(
                    #     f"In Post request - futurelab registration stage 2 - Student PCTO hours added : {email}")
                    # student.update_total_pcto_hour()
                    if request.LANGUAGE_CODE == 'it':
                        status = send_email_message(
                            request, person, subject, 'userauth/email_content-it.html')
                    else:
                        status = send_email_message(
                            request, person, subject, 'userauth/email_content.html')
                    if person:
                        notification_type_objs = Notification_type.objects.all()
                        for single_notification_type in notification_type_objs:
                            PersonNotification.objects.update_or_create(
                                person=person, notification_type=single_notification_type)

                    lang_code = request.LANGUAGE_CODE
                    # if is_fully_paid_by_school_or_company == True and is_100_per_coupon_code == True:
                    selected_plan = OurPlans.objects.filter(
                        plan_lang=lang_code, plan_name=plan_type_from_coupon, title=plan_name_from_coupon).first()

                    currency = 'eur'
                    custom_user_session_id = request.session.get(
                        'CUSTOM_USER_SESSION_ID', '')
                    Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                                           plan=selected_plan, coupon_code=coupon_obj.code, actual_amount=selected_plan.cost, discount=selected_plan.cost, custom_user_session_id=custom_user_session_id)
                    # Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                    #                         plan=selected_plan, coupon_code="", actual_amount="0", discount="0", custom_user_session_id=custom_user_session_id)
                    logger.info(
                        f"payment obj updated for : {email} with 100 per coupon code {coupon_obj.code}")
                    stu_pln_obj, stu_pln_obj_created = StudentsPlanMapper.plansManager.lang_code(lang_code).update_or_create(
                        student=person, plan_lang=lang_code, defaults={'plans': selected_plan})
                    logger.info(
                        f"student plan mapper obj update_or_create at signup for : {email}")
                    try:
                        if plan_type_from_coupon in [PlanNames.Premium.value, PlanNames.FastTrack.value, PlanNames.MiddleSchool.value]:
                            cohort_program1 = coupon_detail_obj.cohort_program1
                        else:
                            cohort_program1 = coupon_detail_obj.cohort_program1
                            cohort_program2 = coupon_detail_obj.cohort_program2
                            if request.LANGUAGE_CODE == "it":
                                cohort_program3 = coupon_detail_obj.cohort_program3
                    except Exception as er:
                        logger.warning(
                            f"Coupon code does not have any linked cohort - {er} : {email}")
                    try:
                        if cohort_program1:
                            StudentCohortMapper.objects.create(
                                student=request.user, cohort=cohort_program1, stu_cohort_lang=request.LANGUAGE_CODE, student_plan=stu_pln_obj)
                            logger.info(
                                f"student cohort mapper obj 1 created at signup for : {email}")
                            try:
                                exercise_cohort_step_tracker_creation.apply_async(
                                    args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id])
                            except Exception as ex:
                                exercise_cohort_step_tracker_creation_without_celery(request.user.username, request.user.pk, coupon_detail_obj.cohort_program1.cohort_id)
                            request.session['is_first_time_on_dashboard'] = True
                            request.session['is_first_time_for_steps_screen'] = True
                        if cohort_program2:
                            StudentCohortMapper.objects.create(
                                student=request.user, cohort=cohort_program2, stu_cohort_lang=request.LANGUAGE_CODE, student_plan=stu_pln_obj)
                            logger.info(
                                f"student cohort mapper obj 2 created at signup for : {email}")
                            try:
                                exercise_cohort_step_tracker_creation.apply_async(
                                    args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id])
                            except Exception as ex:
                                exercise_cohort_step_tracker_creation_without_celery(request.user.username, request.user.pk, coupon_detail_obj.cohort_program2.cohort_id)
                        if cohort_program3:
                            StudentCohortMapper.objects.create(
                                student=request.user, cohort=cohort_program3, stu_cohort_lang=request.LANGUAGE_CODE, student_plan=stu_pln_obj)
                            logger.info(
                                f"student cohort mapper obj 3 created at signup for : {email}")
                            try:
                                exercise_cohort_step_tracker_creation.apply_async(
                                    args=[request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id])
                            except Exception as ex:
                                exercise_cohort_step_tracker_creation_without_celery(request.user.username, request.user.pk, coupon_detail_obj.cohort_program3.cohort_id)
                        student.save()
                    except Exception as ex_cohort:
                        logger.critical(f"Error -{ex_cohort} - to link cohort or steps with student during registration for : {email}")

                    try:
                        # hubspotContactupdateQueryAdded
                        logger.info(
                            f"In hubspot plan/cohort enroll signup building for : {request.user.username}")
                        if is_from_fast_track_program:
                            hubspot_cohort_startdate = unixdateformat(hubspot_cohort_startdate)
                            keys = ['email', 'hubspot_plan_name', 'hubspot_cohort_name_FT', 'hubspot_cohort_startdate']
                            val = [email,hubspot_plan_name,hubspot_cohort_name_FT,hubspot_cohort_startdate]
                            create_update_contact_hubspot(person.username, keys, val)
                        elif is_from_middle_school:
                            hubspot_cohort_startdate = unixdateformat(hubspot_cohort_startdate)
                            keys = ['email', 'hubspot_plan_name', 'hubspot_cohort_name_MSP', 'hubspot_cohort_startdate']
                            val = [email,hubspot_plan_name, hubspot_cohort_name_MSP,hubspot_cohort_startdate]
                            create_update_contact_hubspot(person.username, keys, val)
                        elif is_from_job_course:
                            hubspot_cohort_startdate = unixdateformat(hubspot_cohort_startdate)
                            keys = ['email', 'hubspot_plan_name', 'hubspot_cohort_name_JOB', 'hubspot_cohort_startdate']
                            val = [email,hubspot_plan_name, hubspot_cohort_name_JOB, hubspot_cohort_startdate]
                            create_update_contact_hubspot(person.username, keys, val)
                        logger.info(
                            f"hubspot cohort enroll at signup complete for : {request.user.username}")
                    except Exception as ex:
                        logger.error(
                            f"Error at hubspot plan/cohort enroll at signup  {ex} for : {request.user.username}")
                    return redirect(reverse("home"))
            logger.error(
                f'Data is not valid for user registration : {email}')
            context['student_completion_form'] = student_completion_form
            context['user_resgiter_form'] = user_register_form
            return render(request, 'new_userauth/register2.html', context)
        else:
            logger.error(f"invalid form for user registration : {email}")
            error_message = _("Please enter the valid data!")
            return render(request, self.template_name, context)


def get_school_region(request):
    school_country = request.GET.get('school_name', '')
    all_schools = CountryDetails.objects.filter(country=school_country)
    return JsonResponse(list(all_schools.values('region').distinct()), safe=False)


def lockout(request, credentials, *args, **kwargs):
    # response.status_code = 403  # Forbidden status
    context = {}
    context['captcha'] = FormWithCaptcha()
    context['message'] = "Il tuo account è stato bloccato a causa di troppi tentativi di accesso errati. Si prega di riprovare fra 2 ore."
    return render(request, "new_userauth/login.html", context)


class PersonloginView(View):

    template_name = "new_userauth/login.html"

    def get(self, request):
        context = {}
        is_counselor = request.GET.get('is_counselor', None)
        if is_counselor:
            context['is_counselor'] = is_counselor
        if request.user.is_authenticated:
            user_name = request.user.username
            if request.user.person_role == "Student":
                logger.info(
                    f"Redirected to Student dashboard from student-login view for : {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.user.person_role == "Counselor":
                logger.info(
                    f"Redirected to couselor-dashboard from student-login view for : {user_name}")
                return HttpResponseRedirect(reverse("counselor_program"))
            else:
                logger.info(
                    f"Redirected to admin-dashboard from student-login view for : {user_name}")
                return HttpResponseRedirect(reverse("admin_dashboard"))
        context['captcha'] = FormWithCaptcha()
        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """This is the post method of Login view and accepts only POST requests."""
        context = {}
        is_from_ios_app = request.session.get("is_from_ios_app", False)
        username = request.POST.get("username", '')
        password = request.POST.get("password", '')
        context['password'] = password
        user_type = request.POST.get("user_type", '')
        captcha_form = FormWithCaptcha(request.POST)

        if user_type == "student":
            active_tab = "student"
            context['stu_username'] = username
            if request.user.is_authenticated:
                student = self.request.user.username
                logger.info(
                    f"Redirected to home page from login-view for : {student}")
                is_from_mobile_app = request.session.get(
                    'is_from_mobile_app', False)
                if is_from_mobile_app:
                    get_cohort = StudentCohortMapper.objects.filter(
                        student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                    if get_cohort:
                        return HttpResponseRedirect(reverse("home") + '?cohort_name='+get_cohort.cohort.cohort_name)
                return HttpResponseRedirect(reverse("home"))

            if not captcha_form.is_valid():
                context['captcha'] = captcha_form
                context['active_tab'] = active_tab
                return render(request, self.template_name, context)
            try:
                user = Person.objects.get(Q(username=username))
                user = authenticate(
                    request=request, username=user.username, password=password)

            except Person.DoesNotExist:
                logger.warning(
                    f"User does Not exist at LoginView : {username}")
                user = None
            if user is not None and user.check_password(password):
                try:
                    student = Student.objects.get(person=user)
                    to_display_first_time_cookie_banner = request.session.get(
                        "to_display_first_time_cookie_banner", None)
                    login(request, user)
                    request.session['to_display_first_time_cookie_banner'] = to_display_first_time_cookie_banner
                    request.session['is_from_ios_app'] = is_from_ios_app
                    request.session['lang'] = user.lang_code
                    logger.info(
                        f"User looged in successfully at LoginView for : {user.username}")
                except Exception as err:
                    context["message"] = "E-mail o password sbagliata, riprova!"
                    logger.error(f"Error Login failed {err}: {username}")
                    context['captcha'] = captcha_form
                    context['active_tab'] = active_tab
                    return render(request, self.template_name, context)
                request.session['notifymsg'] = 1
                create_custom_event(request, 3, username)
                logger.info(
                    f"After logged In Redirected to Dashboard at LoginView : {username}")
                is_from_mobile_app = request.session.get(
                    'is_from_mobile_app', False)
                if is_from_mobile_app:
                    get_cohort = StudentCohortMapper.objects.filter(
                        student=request.user, stu_cohort_lang=request.LANGUAGE_CODE).first()
                    if get_cohort:
                        return HttpResponseRedirect(reverse("home") + '?cohort_name='+get_cohort.cohort.cohort_name)
                return HttpResponseRedirect(reverse("home"))

        elif user_type == "Counsellor":
            active_tab = "Counsellor"
            context['counsellor_username'] = username
            if request.user.is_authenticated:
                return HttpResponseRedirect(reverse("counselor-dashboard"))

            if not captcha_form.is_valid():
                context['captcha'] = captcha_form
                context['active_tab'] = active_tab
                return render(request, self.template_name, context)
            try:
                user = Person.objects.get(Q(username=username))
                user = authenticate(
                    request=request, username=user.username, password=password)
            except Person.DoesNotExist:
                logger.warning(
                    f"User does Not exist at CounselorLoginView : {username}")
                user = None
                context['is_counselor'] = 'Yes'
            if user is not None and user.check_password(password):
                try:
                    if user.person_role == "Counselor":
                        if captcha_form.is_valid():
                            login(request, user)
                            request.session['lang'] = user.lang_code
                            logger.info(
                                f"User looged in successfully at CounselorLoginView for : {user.username}")
                            # submit_hubspot_form_with_email(request, username)
                        else:
                            context['captcha'] = captcha_form
                            return render(request, self.template_name, context)
                    else:
                        context["message"] = "E-mail o password sbagliata, riprova!"
                        context['is_counselor'] = 'Yes'
                        logger.warning(
                            f"Invalid username or password counselor login : {request.user.username}")
                        context['captcha'] = captcha_form
                        return render(request, self.template_name, context)
                except Exception as error:
                    print(error)
                    context["message"] = "E-mail o password sbagliata, riprova!"
                    logger.error(f"Error counselor login {error} : {username}")
                    context['captcha'] = captcha_form
                    context['active_tab'] = active_tab
                    context['is_counselor'] = 'Yes'
                    return render(request, self.template_name, context)
                request.session['notifymsg'] = 1
                create_custom_event(request, 3)
                company_name = request.user.counselor.company
                if company_name is not None:
                    request.session['is_login_for_company'] = True
                logger.info(
                    f"Counselor Login - Successfully and Redirected to counselor-search : {request.user.username}")
                return HttpResponseRedirect(reverse("counselor-dashboard"))
            else:
                context['is_counselor'] = 'Yes'
        create_custom_event(request, 4, username)
        context["message"] = "E-mail o password sbagliata, riprova!"
        logger.warning(
            f"Login failed - invalid username and password : {username}")
        context['captcha'] = captcha_form
        context['active_tab'] = active_tab
        return render(request, self.template_name, context)


class RestPasswordEmailView(View):
    template_name = "new_userauth/reset_password_email.html"

    def get(self, request):
        context = {}
        if request.user.is_authenticated:
            user_name = request.user.username
            if request.user.person_role == "Student":
                logger.info(
                    f"Redirected to Student dashboard from student-login view for : {user_name}")
                return HttpResponseRedirect(reverse("home"))
            elif request.user.person_role == "Counselor":
                logger.info(
                    f"Redirected to couselor-dashboard from student-login view for : {user_name}")
                return HttpResponseRedirect(reverse("counselor_program"))
            else:
                logger.info(
                    f"Redirected to admin-dashboard from student-login view for : {user_name}")
                return HttpResponseRedirect(reverse("admin_dashboard"))
        context['form'] = PasswordResttingForm()
        context['captcha'] = FormWithCaptcha()
        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        form = PasswordResttingForm(request.POST)
        captcha_form = FormWithCaptcha(request.POST)
        if form.is_valid() and captcha_form.is_valid():
            email = form.cleaned_data.get("email")
            try:
                person = Person.objects.get(email=email)
                subject = _("Password reset requested")
                status = send_email_message(
                    request, person, subject, 'new_userauth/password_reset_email.html')
                if (status == True):
                    logger.info(
                        f"Sent email at password_reset for : {person.username}")
                    if request.LANGUAGE_CODE == 'it':
                        success_message = "Le istruzioni per reimpostare la password sono state inviate se esiste un account con l'indirizzo email fornito"
                    else:
                        success_message = "Instructions to reset your password have been sent if an account exists with the provided email address"
                    return render(request, self.template_name, {'form': form, 'success_message': success_message, 'captcha': captcha_form})
                    # return redirect("/landing-website/password_reset/done/")
                else:
                    msg = _(
                        "Please try again later")
                    logger.error(
                        f"Email not sent at password_reset for : {person.username}")
                    context['captcha'] = captcha_form
                    return render(request, self.template_name, {'form': form, 'message': msg, 'captcha': captcha_form})
            except Person.DoesNotExist:
                logger.warning(
                    f"User does Not exist at RestPasswordEmailView : {email}")
                if request.LANGUAGE_CODE == 'it':
                    success_message = "Le istruzioni per reimpostare la password sono state inviate se esiste un account con l'indirizzo email fornito"
                else:
                    success_message = "Instructions to reset your password have been sent if an account exists with the provided email address"
                context = {"success_message": success_message}
                context['form'] = form
                context['captcha'] = captcha_form
                return render(request, self.template_name, context)
        else:
            email = request.POST.get("email", '')
            context['captcha'] = captcha_form
            context['form'] = form
            # msg = _('Invalid form data')
            logger.error(
                f"Form is not valid at RestPasswordEmailView : {email}")
            return render(request, self.template_name, context)


UserModel = get_user_model()


INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


class LandingPasswordResetConfirmView(PasswordContextMixin, FormView):
    form_class = SetPasswordForm
    post_reset_login = False
    post_reset_login_backend = None
    reset_url_token = 'set-password'
    success_url = reverse_lazy('password_reset_complete')
    template_name = 'registration/password_reset_confirm.html'
    title = _('Enter new password')
    token_generator = default_token_generator

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        assert 'uidb64' in kwargs and 'token' in kwargs

        self.validlink = False
        self.user = self.get_user(kwargs['uidb64'])

        if self.user is not None:
            token = kwargs['token']
            if token == self.reset_url_token:
                session_token = self.request.session.get(
                    INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(
                        token, self.reset_url_token)
                    return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist, ValidationError):
            user = None
        return user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        del self.request.session[INTERNAL_RESET_SESSION_TOKEN]
        if self.post_reset_login:
            login(self.request, user, self.post_reset_login_backend)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context['validlink'] = True
        else:
            context.update({
                'form': None,
                'title': _('Password reset unsuccessful'),
                'validlink': False,
            })
        return context


class NewPasswordView(PasswordResetConfirmView):
    """This is set password view."""
    form_class = ForgotPasswordSetForm
    success_url = reverse_lazy('landing_website_password_reset_complete')


class RestPasswordDoneView(PasswordContextMixin, View):

    template_name = "new_userauth/password_reset_done.html"

    def get(self, request):
        context = {}
        return render(self.request, self.template_name, context)


class PasswordResetCompleteView(PasswordContextMixin, TemplateView):
    template_name = 'new_userauth/password_reset_complete.html'
    title = _('Password reset complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_url'] = resolve_url('/landing-website/login/')
        return context


# need to change class name and url and file name
class BecomeAnAmbassador(TemplateView):

    template_name = "new_userauth/Registrati-come-studente.html"
