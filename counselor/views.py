from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from student.models import StudentCohortMapper, StudentScholarshipTestMapper, StudentScholarShipTest, StudentsPlanMapper, StudentActionItemDiary, StudentActionItemDiaryComment, CohortStepTrackerDetails, CohortStepTracker
from courses import models
from django.contrib.auth.decorators import login_required
from userauth import models as auth_mdl
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from datetime import datetime, timedelta, date
import pandas as pd
import json, requests, csv
from boto3.dynamodb.conditions import Attr, Key
import xlwt
import boto3
import logging
# from .task import send_mail_to_student
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.translation import ugettext as _
# from .forms import SendPashNotificationForm, CohortSendPushNotificationForm
from lib.hubspot_contact_sns import create_update_contact_hubspot
from payment.models import Payment, Coupon, CouponDetail
from dateutil.parser import parse
from django.db.models import Q
from django.views.generic import ListView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from counselor.helpers import student_helper_kpis, student_course_report, student_helper_kpis_company
from userauth.models import Person
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pdb, pytz
from django.db.models import Count
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


@login_required(login_url="/counselor-login/")
def counselor_dashboard_view(request):
    try:
        template_name = "counselor/company_counselor_dashboard.html"
        logger.info(f"In counselor dashboard view : {request.user.username}")
        if request.user.person_role == "Student":
            logger.info(f"Redirected to home page from counselor dashboard view for : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))
        if request.user.person_role == "Counselor":
            academic_session_start_date = request.user.counselor.academic_session_start_date
            academic_session_start_date = datetime.fromisoformat(request.user.counselor.academic_session_start_date.isoformat())
            local_tz = pytz.timezone(settings.TIME_ZONE)
            academic_session_start_date = local_tz.localize(academic_session_start_date)
            is_from_high_school = request.session.get('is_from_high_school', False)
            is_from_fast_track = request.session.get('is_from_fast_track', False)
            is_from_middle_school = request.session.get('is_from_middle_school', False)
            is_from_job_course = request.session.get('is_from_job_course', False)
            is_search_parameter_satisfed = request.session.get('is_search_parameter_satisfed', False)
            is_company = request.session.get('is_company', False)
            # if is_search_parameter_satisfed:
            if request.user.counselor.is_verified_by_futurely:
                if is_from_fast_track or is_from_middle_school or is_from_high_school or is_from_job_course:
                    # cohort_id = request.session.get('cohort_id', None)
                    discount_code = request.session.get('selected_coupon_codes', [])
                    is_all_student = request.session.get('is_all_student', False)
                    all_students = None
                    if request.user.counselor.company is None:
                        # if len(discount_code) == 0:
                        class_name = request.GET.get('class_name', None)
                        class_year = request.GET.get('class_year', None)
                        specialization = request.GET.get('specialization', None)
                        total_students = request.GET.get('total_students', None)
                        plans = request.user.counselor.plans.all()
                        ifflow = request.GET.get('ifflow', None)
                        if ifflow:
                            school_name = request.user.counselor.school_name
                            school_region = request.user.counselor.school_region
                            school_city = request.user.counselor.school_city
                            coupon_obj = Coupon.objects.filter(Q(coupon_detail__school__name=school_name) & Q (coupon_detail__school__region=school_region) & Q(coupon_detail__school__city=school_city),Q(plan__in=plans), start_date__gte = academic_session_start_date, is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track).values_list('code',flat=True)
                            coupon_obj = list(coupon_obj)
                            request.session['selected_coupon_codes'] = coupon_obj
                            discount_code = coupon_obj
                            # if is_all_student:
                            stu_payments = Payment.objects.filter(coupon_code__in = discount_code).values_list('person__id',flat=True)
                            if class_name and class_year and specialization:
                                if class_year == 'None' or class_year == '':
                                    class_year = None
                                if class_name == 'None' or class_name == '':
                                    class_name = None
                                if specialization == 'None' or specialization == '':
                                    specialization = None
                            request.session['class_name'] = class_name
                            request.session['class_year'] = class_year
                            request.session['specialization'] = specialization
                            request.session['total_students'] = total_students
                            #     all_students = auth_mdl.Student.objects.filter(Q(discount_coupon_code__in=discount_code) | Q(person__id__in=stu_payments),
                            #         is_from_middle_school=is_from_middle_school, is_from_fast_track_program=is_from_fast_track, student_school_detail__class_name__name=class_name, student_school_detail__class_year__name=class_year).order_by('person__last_name').distinct().select_related('person').prefetch_related('student_school_detail','student_parent_detail')
                            # else:
                            #     all_students = auth_mdl.Student.objects.filter(Q(discount_coupon_code__in=discount_code) | Q(person__id__in=stu_payments),
                            #         is_from_middle_school=is_from_middle_school, is_from_fast_track_program=is_from_fast_track).order_by('person__last_name').distinct().select_related('person').prefetch_related('student_school_detail','student_parent_detail')
                            logger.info(f"fetched students details with school detail at counselor dashboard: {request.user.username}")
                            # template_name = "counselor/counselor_dashboard.html"
                            return HttpResponseRedirect(reverse('students_kpis'))
                        else:
                            return HttpResponseRedirect(reverse('counselor_program'))
                    else:
                        is_company = request.session.get("is_company", False)
                        # if len(discount_code) == 0:
                        
                        list_of_cohort = request.session.get('list_of_cohort', [])
                        company_name = request.user.counselor.company
                        plans = request.user.counselor.plans.all()
                        coupon_obj = Coupon.objects.filter(Q(coupon_detail__company__name=company_name),Q(plan__in=plans) ,Q(coupon_detail__cohort_program1__cohort_id__in=list_of_cohort) | Q(coupon_detail__cohort_program2__cohort_id__in=list_of_cohort) | Q(coupon_detail__cohort_program3__cohort_id__in=list_of_cohort), start_date__gte = academic_session_start_date, is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track).values_list('code',flat=True)
                        coupon_obj = list(coupon_obj)
                        request.session['selected_coupon_codes'] = coupon_obj
                        if request.user.is_linked_to_counselor_special_dashboard:
                            return HttpResponseRedirect(reverse('students_kpis'))
                        discount_code = coupon_obj
                        # if is_company is False:
                        #     return HttpResponseRedirect(reverse("student_course_report"))
                        stu_payments = Payment.objects.filter(coupon_code__in = discount_code).values_list('person__id',flat=True)
                        all_students = auth_mdl.Student.objects.filter(Q(discount_coupon_code__in=discount_code) | Q(person__id__in=stu_payments), is_from_middle_school=is_from_middle_school,
                            is_from_fast_track_program=is_from_fast_track, person__stuMapID__cohort__cohort_id__in = list_of_cohort).order_by('person__last_name').distinct().select_related('person').prefetch_related('student_school_detail','student_parent_detail')
                        logger.info(f"fetched students detail at counselor dashboard: {request.user.username}")
                        template_name = "counselor/company_counselor_dashboard.html"
                    # steps = models.step_status.objects.filter()
                    logger.info(f"counselor dashboard visited by : {request.user.username}")
                    return render(request, template_name,{"all_students": all_students})
                else:
                    return HttpResponseRedirect(reverse('counselor_program'))
            else:
                return render(request, template_name)
            # else:
            #     return HttpResponseRedirect(reverse('counselor_search'))
    except Exception as ex:
        logger.critical(f"Exception error in counselor dashboard view {ex} : {request.user.username}")
    return HttpResponseRedirect(reverse("counselor_login"))

@login_required(login_url="/counselor-login/")
def student_performace_for_counselor_view(request):
    try:
        logger.info(f"In students performance for Futurely Admin : {request.user.username}")
        if request.user.person_role == "Student":
                logger.info(f"Redirected to home page from counselor dashboard view : {request.user.username}")
                return HttpResponseRedirect(reverse("home"))
        if request.user.person_role == "Counselor":
            all_courses_students = []
            is_from_fast_track = request.session.get('is_from_fast_track', False)
            is_from_middle_school = request.session.get('is_from_middle_school', False)
            is_from_high_school = request.session.get('is_from_high_school', False)
            is_from_job_course = request.session.get('is_from_job_course', False)
            is_search_parameter_satisfed = request.session.get('is_search_parameter_satisfed', False)
            total_students = request.session.get('total_students', None)
            # class_name = request.session.get('class_name')
            # class_year = request.session.get('class_year')
            # if is_search_parameter_satisfed:
            # import pdb;
            # pdb.set_trace()
            if is_from_fast_track or is_from_middle_school or is_from_high_school or is_from_job_course:
                context = {}
                is_all_student = request.session.get('is_all_student', False)
                list_of_cohort = request.session.get('list_of_cohort', [])
                display_class_year_name = "No"
                if request.user.counselor.company is None:
                    all_stu = student_helper_kpis(request)
                else:
                    all_stu = student_helper_kpis_company(request)
                logger.info(f"Fetched students with company details at student_persormance_counselor_view for : {request.user.username}")
                module_id = request.GET.get('module_id', None)
                # import ipdb;
                # ipdb.set_trace()
                # if is_for_middle_school
                plans = request.user.counselor.plans.all()
                selected_course_module = request.user.counselor.course_module
                if selected_course_module:
                    courses = models.Modules.objects.filter(module_id=selected_course_module.module_id)
                    course = courses.first()
                    context['module_id'] = course.module_id
                else:
                    module_ids = models.Cohort.objects.filter(cohort_id__in=list_of_cohort).values_list('module_id', flat=True).distinct()
                    courses = models.Modules.objects.filter(module_lang=request.LANGUAGE_CODE, module_id__in=module_ids,  is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track)
                    print(courses)
                    if courses.count() == 0:
                        courses = models.Modules.objects.filter(module_lang=request.LANGUAGE_CODE,  is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track, course__plan__in = plans).distinct()
                    if module_id is None:
                        course = courses.first()
                        context['module_id'] = course.module_id
                    else:
                        course = courses.get(module_id=module_id)
                        context['module_id'] = course.module_id
                # if request.user.counselor.company is None:
                stud = StudentCohortMapper.objects.filter(student__in=all_stu, cohort__module__module_id=course.module_id, stu_cohort_lang=request.LANGUAGE_CODE).distinct().all().order_by('student__last_name') #.order_by("-stu_cohort_map__step_trackeraction_item_diary__student_actions_item_diary_id__created_at")
                stud = stud.select_related('student').prefetch_related('student__student__student_school_detail').prefetch_related('stu_cohort_map').prefetch_related('stu_cohort_map__cohort_step_tracker_details')
                # else:
                #     stud = StudentCohortMapper.objects.filter(student__in=all_stu, cohort__module__module_id=course.module_id, stu_cohort_lang=request.LANGUAGE_CODE, cohort__cohort_id__in = list_of_cohort).distinct().all().order_by('student__first_name')
                    # courses = courses.filter(module_id=course.module_id)
                steps = course.steps.exclude(is_backup_step=True).all()
                if(stud.count()>0):
                    all_courses_students.append([stud,steps,course])
                # print(all_courses_students)
                context["all_courses_students"] = all_courses_students
                context["courses"] = courses
                context['students_count'] = stud.count()
                context['total_students'] = total_students
                student_obj = stud.first()
                context['student_obj'] = student_obj
                if request.user.counselor.company is None:
                    if total_students:
                        display_class_year_name = "No"
                    else:
                        display_class_year_name = "Yes"
                context['display_class_year_name'] = display_class_year_name
                if(student_obj):
                    context['cohort_unlocked_setps'] = student_obj.total_unlocked_steps
                else:
                    context['cohort_unlocked_setps'] = 0
                return render(request, 'counselor/counselor_student_details.html', context)
            else:
                return HttpResponseRedirect(reverse('counselor_program'))
            # else:
            #     return HttpResponseRedirect(reverse('counselor_search'))
    except Exception as err:
        logger.error(f"Exception Error in student_performace_for_counselor_view {err} : {request.user.username}")
        return HttpResponseRedirect(reverse('counselor_login'))

class MiddleSchoolDashBoardView(View):
    template_name = "counselor/counselor-middle-school-dashboard.html"
    def get(self, request):
        try:
            logger.info(f"In students performance for Futurely Admin : {request.user.username}")
            if request.user.person_role == "Student":
                    logger.info(f"Redirected to home page from middle school counselor dashboard view : {request.user.username}")
                    return HttpResponseRedirect(reverse("home"))
            if request.user.person_role == "Counselor":
                if request.user.counselor.is_for_middle_school_only:
                    is_from_middle_school = request.session.get('is_from_middle_school', False)
                    all_courses_students = []
                    is_from_fast_track = request.session.get('is_from_fast_track', False)
                    is_from_high_school = request.session.get('is_from_high_school', False)
                    is_search_parameter_satisfed = request.session.get('is_search_parameter_satisfed', False)
                    total_students = request.session.get('total_students', None)
                    if is_from_fast_track or is_from_middle_school or is_from_high_school:
                        context = {}
                        is_all_student = request.session.get('is_all_student', False)
                        list_of_cohort = request.session.get('list_of_cohort', [])
                        display_class_year_name = "No"
                        if request.user.counselor.company is None:
                            all_stu = student_helper_kpis(request)
                        else:
                            all_stu = student_helper_kpis_company(request)
                        logger.info(f"Fetched students with company details at middle school counselor for : {request.user.username}")
                        module_id = request.GET.get('module_id', None)
                        
                        selected_course_module = request.user.counselor.course_module
                
                        if selected_course_module:
                            courses = models.Modules.objects.filter(module_id=selected_course_module.module_id)
                            course = courses.first()
                            context['module_id'] = course.module_id
                        else:
                            courses = models.Modules.objects.filter(module_lang=request.LANGUAGE_CODE, is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track)
                            if module_id is None:
                                course = courses.first()
                                context['module_id'] = course.module_id
                            else:
                                course = courses.get(module_id=module_id)
                                context['module_id'] = course.module_id
                        stud = StudentCohortMapper.objects.filter(student__in=all_stu, cohort__module__module_id=course.module_id, stu_cohort_lang=request.LANGUAGE_CODE).distinct().all().order_by('student__last_name') #.order_by("-stu_cohort_map__step_trackeraction_item_diary__student_actions_item_diary_id__created_at")
                        stud = stud.select_related('student').prefetch_related('student__student__student_school_detail').prefetch_related('stu_cohort_map').prefetch_related('stu_cohort_map__cohort_step_tracker_details')
                        steps = course.steps.exclude(is_backup_step=True).all()
                        if(stud.count()>0):
                            all_courses_students.append([stud,steps,course])
                        context["all_courses_students"] = all_courses_students
                        context["courses"] = courses
                        context['students_count'] = stud.count()
                        student_obj = stud.first()
                        context['student_obj'] = student_obj
                        if request.user.counselor.company is None:
                            if total_students:
                                display_class_year_name = "No"
                            else:
                                display_class_year_name = "Yes"
                        context['display_class_year_name'] = display_class_year_name
                        if(student_obj):
                            context['cohort_unlocked_setps'] = student_obj.total_unlocked_steps
                        else:
                            context['cohort_unlocked_setps'] = 0
                        return render(request, self.template_name, context)
                    else:
                        logger.info(f"Redirected to counselor_program from middle school counselor dashboard view : {request.user.username}")
                        return HttpResponseRedirect(reverse('counselor_program'))
                else:
                    logger.info(f"Redirected to counselor_program from middle school counselor dashboard view : {request.user.username}")
                    return HttpResponseRedirect(reverse('counselor_program'))
        except Exception as err:
            logger.error(f"Exception Error in middle school counselor dashboard view {err} : {request.user.username}")
            return HttpResponseRedirect(reverse('counselor_login'))

def get_diary_ques_answer(request):
    try:
        if request.method == "POST":
            cohort_step_trac_id = request.POST.get('cohort_step_trac_id', None)
            diary_ques_answer_list = []
            if cohort_step_trac_id:
                cohort_step_trac_obj = CohortStepTracker.objects.get(step_track_id=int(cohort_step_trac_id))
                for actionItems in cohort_step_trac_obj.stu_action_items.all():
                    for qus_and_ans in actionItems.action_item_diary_track.all():
                        diary_ques_answer_list.append({
                            "question": qus_and_ans.action_item_diary.question,
                            "answer": qus_and_ans.answer,
                        })
            return JsonResponse({'status':True, 'diary_ques_answer_list': diary_ques_answer_list}, safe=False)
    except Exception as err:   
        logger.error(f"Exception Error in get_diary_ques_answer {err} : {request.user.username}")
        return JsonResponse({'status':False, 'diary_ques_answer_list': []}, safe=False)


class StudentCourseReport(LoginRequiredMixin, View):
    login_url = '/login/'
    def get(self, request):
        context = {}
        if request.user.person_role == "Student":
            logger.info(f"Redirected to home page from counselor dashboard view for : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))
        if request.user.person_role == "Futurely_admin":
            return HttpResponseRedirect(reverse("admin_dashboard"))
        if request.user.person_role == "Counselor":
            is_from_high_school = request.session.get('is_from_high_school', False)
            is_from_fast_track = request.session.get('is_from_fast_track', False)
            is_from_middle_school = request.session.get('is_from_middle_school', False)
            is_from_job_course = request.session.get('is_from_job_course', False)
            discount_code = request.session.get('selected_coupon_codes', [])
            is_all_student = request.session.get('is_all_student', False)
            is_search_parameter_satisfed = request.session.get('is_search_parameter_satisfed', False)
            # if is_search_parameter_satisfed:
            if is_from_fast_track or is_from_middle_school or is_from_high_school or is_from_job_course:
                if request.user.counselor.company is None:
                    logger.info(f"Redirected to counselor-dashbord from StudentCourseReport for : {request.user.username}")
                    return HttpResponseRedirect(reverse('counselor-dashboard'))
                else:
                    request.session["is_company"] = True
                    cohort_program1 = None
                    cohort_program2 = None
                    cohort_program3 = None
                    # if is_all_student:
                        # check the program type, high_school=True and It > get 3 cohort, middle_school=True and It > get 1 cohort, Fast_track > for 1
                    list_of_cohort = request.session.get('list_of_cohort', [])
                    # cohort_obj = models.Cohort.objects.filter(cohort_id__in=list_of_cohort, is_for_middle_school=is_from_middle_school, 
                    #     is_for_fast_track_program=is_from_fast_track, is_active="Yes",cohort_lang=request.LANGUAGE_CODE).order_by('module__module_priority')
                    if is_from_fast_track:
                        cohort_obj = models.Cohort.objects.filter(cohort_id__in=list_of_cohort,is_for_fast_track_program=is_from_fast_track, is_active="Yes").prefetch_related('cohort_step_status').first()
                        context['cohorts'] = [cohort_obj]
                    elif is_from_middle_school:
                        cohort_obj = models.Cohort.objects.filter(cohort_id__in=list_of_cohort,is_for_middle_school=is_from_middle_school, is_active="Yes").prefetch_related('cohort_step_status').first()
                        context['cohorts'] = [cohort_obj]
                    elif is_from_job_course:
                        cohort_obj = models.Cohort.objects.filter(cohort_id__in=list_of_cohort, is_active="Yes").prefetch_related('cohort_step_status').first()
                        context['cohorts'] = [cohort_obj]
                    else:
                        if request.LANGUAGE_CODE == "it":
                            cohort_obj1 = models.Cohort.objects.filter(module__module_id=3,is_active="Yes").prefetch_related('cohort_step_status').first()
                            cohort_obj2 = models.Cohort.objects.filter(module__module_id=4,is_active="Yes").prefetch_related('cohort_step_status').first()
                            cohort_obj3 = models.Cohort.objects.filter(module__module_id=5,is_active="Yes").prefetch_related('cohort_step_status').first()
                            context['cohorts'] = [cohort_obj1, cohort_obj2, cohort_obj3]
                        else:
                            cohort_obj1 = models.Cohort.objects.filter(module__module_id=1,is_active="Yes").prefetch_related('cohort_step_status').first()
                            cohort_obj2 = models.Cohort.objects.filter(module__module_id=2,is_active="Yes").prefetch_related('cohort_step_status').first()
                            context['cohorts'] = [cohort_obj1, cohort_obj2]
                    # else:
                    #     cohort_start_date = request.session.get('cohort_start_date', None)
                    #     list_of_cohort = request.session.get('list_of_cohort', [])
                    #     # print(list_of_cohort)
                    #     cohort_obj = models.Cohort.objects.filter(cohort_id__in=list_of_cohort, starting_date=cohort_start_date, is_for_middle_school=is_from_middle_school, 
                    #         is_for_fast_track_program=is_from_fast_track, is_active="Yes",cohort_lang=request.LANGUAGE_CODE).order_by('module__module_priority').prefetch_related('cohort_step_status')
                    #     context['cohorts'] = cohort_obj
                    #     # print(cohort_obj, '---------------')
                        
                    all_stu = student_course_report(request, list_of_cohort)
                    # print(all_stu)
                    logger.info(f"Fetched students with company details at student_persormance_counselor_view for : {request.user.username}")
                context['all_stu_obj'] = all_stu
                print(all_stu)
                logger.info(f"student course report visited by : {request.user.username}")
                return render(request, "counselor/counselor_student_counse_report.html", context)
            else:
                return HttpResponseRedirect(reverse('counselor_search'))
            # else:
            #     return HttpResponseRedirect(reverse('counselor_search'))
        else:
            return HttpResponseRedirect(reverse("counselor-dashboard"))

@login_required(login_url="/counselor-login/")
def account_settings_view_counselor(request):
    context = {}
    current_user = request.user
    logger.info(f"In account_settings_view_counselor page called by : {current_user.username}")
    if request.user.person_role == "Student":
        logger.info(f"Redirected Student to account_settings_view_counselor from home : {current_user.username}")
        return HttpResponseRedirect(reverse("home"))
    if request.user.person_role == "Futurely_admin":
        logger.info(f"Redirected Student to account_settings_view_counselor from home : {current_user.username}")
        return HttpResponseRedirect(reverse("admin_dashboard"))
    try:
        if request.method == "POST":
            request_post = request.POST
            first_name = request_post.get('first_name', None)
            last_name = request_post.get('last_name', None)
            # email = request_post.get('email', None)
            if first_name:
                current_user.first_name = first_name
            if last_name:
                current_user.last_name = last_name
            # if email:
            #     current_user.email = email
            current_user.save()
            logger.info(f"Account settings updated at account_settings_view_counselor for : {current_user.username}")
        context['first_name'] = current_user.first_name
        context['last_name'] = current_user.last_name
        context['email'] = current_user.email
        context['current_user'] = current_user
        logger.info(f"Account settings counselor page visited by : {current_user.username}")
        return render(request, "counselor/account-settings-counselor.html", context)
    except Exception as error:
        current_user = request.user
        logger.critical(f"Error to account settings counselor page {error} for : {current_user.username}")
        return HttpResponseRedirect(reverse('counselor-dashboard'))

@login_required(login_url="/counselor-login/")
def counselor_select_program_view(request):
    try:
        if request.user.person_role == "Student":
            logger.info(f"Redirected to home page from counselor select program page view for : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))
        elif request.user.person_role == "Futurely_admin":
            logger.info(f"Redirected to admin_dashboard page from counselor select program page view for : {request.user.username}")
            return HttpResponseRedirect(reverse("admin_dashboard"))
        context = {}
        request.session['is_cta_btn'] = False
        program_type = request.GET.get("program_type", None)
        if program_type is not None:
            request.session['is_cta_btn'] = True
            request.session['is_from_middle_school'] = False
            request.session['is_from_fast_track'] = False
            request.session['is_from_high_school'] = False
            request.session['is_from_job_course'] = False
            if (program_type == "middle_school"):
                request.session['is_from_middle_school'] = True
            elif (program_type == "fast_track"):
                request.session['is_from_fast_track'] = True
            # elif (program_type == "all"):
            #     request.session['is_all_student'] = True
            else:
                request.session['is_from_high_school'] = True
            try:
                request.session.pop('is_all_student', None)
                request.session.pop('selected_coupon_codes', None)
                request.session.pop('cohort_start_date', None)
                request.session.pop('is_search_parameter_satisfed', None)
            except Exception as exp:
                logger.error(f"Error at counselor program view : {exp} : for user - {request.user.username}")
            return HttpResponseRedirect(reverse('counselor_search'))
        program_list_for_dropdown = []
        academic_session_start_date = request.user.counselor.academic_session_start_date
        academic_session_start_date = datetime.fromisoformat(request.user.counselor.academic_session_start_date.isoformat())
        local_tz = pytz.timezone(settings.TIME_ZONE)
        academic_session_start_date = local_tz.localize(academic_session_start_date)
        coupon_obj = None
        if request.user.counselor.company is None:
            request.session['is_company'] = False
            is_for_fast_track_program_only = request.user.counselor.is_for_fast_track_program_only
            is_for_middle_school_only = request.user.counselor.is_for_middle_school_only
            request.session['is_from_middle_school'] = False
            request.session['is_from_fast_track'] = False
            request.session['is_from_high_school'] = False
            request.session['is_from_job_course'] = False
            if is_for_fast_track_program_only:
                request.session['is_from_fast_track'] = True
            elif is_for_middle_school_only:
                request.session['is_from_middle_school'] = True
            else:
                counselor_plans = request.user.counselor.plans.filter(plan_name="JobCourse") #.first()
                if counselor_plans.count() > 0:
                    request.session['is_from_job_course'] = True
                else:
                    request.session['is_from_high_school'] = True
            
            # school_name = request.user.counselor.school_name
            # school_region = request.user.counselor.school_region
            # school_city = request.user.counselor.school_city
            # coupon_obj = Coupon.objects.filter(Q(coupon_detail__school__name=school_name) & Q (coupon_detail__school__region=school_region) & Q(coupon_detail__school__city=school_city), start_date__gte=academic_session_start_date)#.values_list('code',flat=True)
            return HttpResponseRedirect(reverse('class_section_students'))
        else:
            company_name = request.user.counselor.company
            is_company = True
            coupon_obj = None
            # import pdb; pdb.set_trace()
            request.session['is_company'] = is_company
            plans = request.user.counselor.plans.all()
            print(plans)

            coupon_obj = Coupon.objects.filter(Q(coupon_detail__company__name=company_name), Q(plan__in=plans), start_date__gte=academic_session_start_date)
            if coupon_obj.count() > 0:
                fasttrack = coupon_obj.filter(is_for_fast_track_program=True)
                if fasttrack.count() > 0:
                    program_list_for_dropdown.append("fast_track")
                middlesachool = coupon_obj.filter(is_for_middle_school=True)
                if middlesachool.count() > 0:
                    program_list_for_dropdown.append("middle_school")
                highschool = coupon_obj.filter(is_for_middle_school=False, is_for_fast_track_program=False)
                if len(highschool) > 0:
                    counselor_job_course = coupon_obj.filter(plan_type="JobCourse")
                    if counselor_job_course.count() > 0:
                        # request.session['is_from_job_course'] = True
                        program_list_for_dropdown.append("job_course")
                    else:
                        program_list_for_dropdown.append("high_school")
            else:
                logger.error(f"Wrong counselor account approved as we have no linked coupon code with this : {request.user.username}")
                return HttpResponseRedirect(reverse('counselor-dashboard'))
            if len(program_list_for_dropdown) >= 2:
                request.session['is_cta_btn'] = True
                context["program_list"] = program_list_for_dropdown
                coupon_list = list(coupon_obj.values_list("code", flat=True).distinct())
                all_students_count = auth_mdl.Student.objects.filter(discount_coupon_code__in=coupon_list)
                context['high_school_count'] = all_students_count.filter(is_from_middle_school=False, is_from_fast_track_program=False).count()
                context['middle_school_count'] = all_students_count.filter(is_from_middle_school=True, is_from_fast_track_program=False).count()
                context['fast_track_count'] = all_students_count.filter(is_from_middle_school=False, is_from_fast_track_program=True).count()
                context['all_students_count'] = all_students_count.count()
            else:
                if (program_list_for_dropdown[0] == "middle_school"):
                    request.session['is_from_middle_school'] = True
                elif (program_list_for_dropdown[0] == "fast_track"):
                    request.session['is_from_fast_track'] = True

                elif (program_list_for_dropdown[0] == "job_course"):
                    request.session['is_from_job_course'] = True
                # elif (program_type == "all"):
                #     request.session['is_all_student'] = True
                else:
                    request.session['is_from_high_school'] = True
                return HttpResponseRedirect(reverse('counselor_search'))
            # context["program_list"] = ["high_school", "middle_school", "fast_track"]
            # context['high_school_count'] = 0
            # context['middle_school_count'] = 0
            # context['fast_track_count'] = 0
            # context['all_students_count'] = 0
            return render(request, "counselor/select_program.html", context)
    except Exception as err:
        current_user = request.user
        logger.critical(f"Error to select program view page {err} for : {current_user.username}")
        return HttpResponseRedirect(reverse('counselor-dashboard'))

@login_required(login_url="/counselor-login/")
def counselor_search_view(request):
    try:
        context = {}
        is_company = False
        academic_session_start_date = request.user.counselor.academic_session_start_date
        academic_session_start_date = datetime.fromisoformat(request.user.counselor.academic_session_start_date.isoformat())
        local_tz = pytz.timezone(settings.TIME_ZONE)
        academic_session_start_date = local_tz.localize(academic_session_start_date)
        if request.user.person_role == "Student":
            logger.info(f"Redirected to home page from counselor seaching page view for : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))
        elif request.user.person_role == "Futurely_admin":
            logger.info(f"Redirected to admin_dashboard page from counselor seaching page view for : {request.user.username}")
            return HttpResponseRedirect(reverse("admin_dashboard"))
        if request.user.person_role == "Counselor":
            is_company = request.session.get('is_company', False)
            program_list_for_dropdown = []
            coupon_obj = None
            is_from_high_school = request.session.get('is_from_high_school', False)
            is_from_fast_track = request.session.get('is_from_fast_track', False)
            is_from_middle_school = request.session.get('is_from_middle_school', False)
            is_login_for_company = request.session.get('is_login_for_company', None)
            is_from_job_course = request.session.get('is_from_job_course', False)
            if is_from_fast_track == False and is_from_middle_school == False and is_from_high_school == False and is_from_job_course == False:
                request.session['is_from_high_school'] = True
                is_from_high_school = True
            if request.user.counselor.company is None:
                request.session['is_company'] = False
                # school_name = request.user.counselor.school_name
                # school_region = request.user.counselor.school_region
                # school_city = request.user.counselor.school_city
                # coupon_obj = Coupon.objects.filter(Q(coupon_detail__school__name=school_name) & Q (coupon_detail__school__region=school_region) & Q(coupon_detail__school__city=school_city), start_date__gte=academic_session_start_date, is_for_middle_school=is_from_middle_school, 
                # is_for_fast_track_program=is_from_fast_track)#.values_list('code',flat=True)
                return HttpResponseRedirect(reverse("counselor-dashboard"))
            else:
                company_name = request.user.counselor.company
                is_company = True
                request.session['is_company'] = is_company
                plans = request.user.counselor.plans.all()
                coupon_obj = Coupon.objects.filter(Q(coupon_detail__company__name=company_name),Q(plan__in=plans), start_date__gte = academic_session_start_date, 
                    is_for_middle_school=is_from_middle_school, is_for_fast_track_program = is_from_fast_track) 
                # coupon_obj = list(coupon_obj)
                coupon_details = []
                cohort1Data = []
                cohort2Data = []
                cohort3Data = []
                if coupon_obj is not None:
                    for coupon in coupon_obj:
                        coupon_details = coupon.coupon_detail.all()
                        for coupon_detail in coupon_details:
                            if coupon_detail.cohort_program1:
                                cohort1Data.append(coupon_detail.cohort_program1)
                            if coupon_detail.cohort_program2:
                                cohort2Data.append(coupon_detail.cohort_program2)
                            if coupon_detail.cohort_program3:
                                cohort3Data.append(coupon_detail.cohort_program3)
                    cohort1Data = set(cohort1Data)
                    cohort2Data = set(cohort2Data)
                    cohort3Data = set(cohort3Data)
                    cohort_coupon_data = {}
                    cohort_coupon_data_dsp = {}
                    list_of_cohort = []
                    for cohort_i in cohort1Data:
                        list_of_cohort.append(cohort_i.cohort_id)
                        codes = list(cohort_i.coupon_cohort_p1_info.filter(Q(coupon__in=coupon_obj)).values_list('coupon__code', flat=True))
                        if cohort_i.starting_date in cohort_coupon_data:
                            previous_codes = cohort_coupon_data[cohort_i.starting_date]
                            codes = previous_codes + codes
                            cohort_coupon_data[cohort_i.starting_date] = codes
                            cohort_coupon_data_dsp[cohort_i.starting_date] = codes
                        else:
                            cohort_coupon_data[cohort_i.starting_date] = codes
                            cohort_coupon_data_dsp[cohort_i.starting_date] = codes
                    
                    for cohort_i in cohort2Data:
                        list_of_cohort.append(cohort_i.cohort_id)
                        codes = list(cohort_i.coupon_cohort_p2_info.filter(Q(coupon__in=coupon_obj)).values_list('coupon__code', flat=True))
                        if cohort_i.starting_date in cohort_coupon_data:
                            previous_codes = cohort_coupon_data[cohort_i.starting_date]
                            codes = previous_codes + codes
                            cohort_coupon_data[cohort_i.starting_date] = codes
                        else:
                            cohort_coupon_data[cohort_i.starting_date] = codes
                    for cohort_i in cohort3Data:
                        list_of_cohort.append(cohort_i.cohort_id)
                        codes = list(cohort_i.coupon_cohort_p3_info.filter(Q(coupon__in=coupon_obj)).values_list('coupon__code', flat=True))
                        if cohort_i.starting_date in cohort_coupon_data:
                            previous_codes = cohort_coupon_data[cohort_i.starting_date]
                            codes = previous_codes + codes
                            cohort_coupon_data[cohort_i.starting_date] = codes
                        else:
                            cohort_coupon_data[cohort_i.starting_date] = codes
                    context['coupon_details'] = coupon_obj
                    cohort_start_dates = list(cohort_coupon_data.keys())
                    cohort_start_dates_dsp = sorted(list(cohort_coupon_data_dsp.keys()), reverse=True)
                    all_selected_coupon_codes = []
                    for item in cohort_coupon_data.values():
                        all_selected_coupon_codes = all_selected_coupon_codes + item
                    all_selected_coupon_codes = list(set(all_selected_coupon_codes))
                    # context['cohort_startdates'] = cohort_start_dates
                    context['cohort_startdates'] = cohort_start_dates_dsp
                    if request.method == "POST":
                        cohort_start_date = request.POST.get('cohort_start_date', None)
                        if cohort_start_date == "All":
                            request.session['is_all_student'] = True
                            request.session['list_of_cohort'] = list_of_cohort
                            request.session['selected_coupon_codes'] = all_selected_coupon_codes
                        else:
                            cohort_start_date = cohort_start_dates_dsp[int(cohort_start_date) - 1]
                            selected_coupon_codes = cohort_coupon_data[cohort_start_date]
                            request.session['selected_coupon_codes'] = selected_coupon_codes
                            request.session['cohort_start_date'] = str(cohort_start_date)
                            request.session['cohort_start_date_obj'] = cohort_start_date.strftime('%d-%m-%Y')
                            cohorts_list = list(models.Cohort.cohortManager.lang_code(request.LANGUAGE_CODE).filter(starting_date = cohort_start_date, cohort_id__in = list_of_cohort).values_list('cohort_id',flat=True))
                            request.session['list_of_cohort'] = cohorts_list
                            request.session['is_all_student'] = False
                            request.session["is_search_parameter_satisfed"] = True 
                        return HttpResponseRedirect(reverse("counselor-dashboard"))
                    else:
                        if len(cohort_start_dates_dsp) > 1:
                            request.session['is_cta_btn'] = True
                            return render(request,"counselor/counselor_search.html", context)
                        else:
                            if is_company:
                                # request.session['is_login_for_company'] = False
                                request.session['is_all_student'] = True
                                request.session['selected_coupon_codes'] = all_selected_coupon_codes
                                request.session['list_of_cohort'] = list_of_cohort
                                # return HttpResponseRedirect(reverse("student_course_report"))
                            else:
                                request.session['selected_coupon_codes'] = all_selected_coupon_codes
                                request.session['list_of_cohort'] = list_of_cohort
                            logger.info(f"Admin dashboard visited by : {request.user.username}")
                            return HttpResponseRedirect(reverse("counselor-dashboard"))
                else:
                    print("********************************")
                    logger.error(f"Conselor without any selected coupon code : {request.user.username}")
                    return HttpResponseRedirect(reverse("counselor-dashboard"))
    except Exception as err:
        logger.error(f"Error in counselor search view {err} for : {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))

@login_required(login_url="/counselor-login/")
def select_program_view(request):
    request.session['is_from_middle_school'] = False
    request.session['is_from_fast_track'] = False
    request.session['is_from_high_school'] = False
    if request.method == "POST":
        program = request.POST.get('programname', None)
        print(program, "#####################")
        if (program == "middle_school"):
            request.session['is_from_middle_school'] = True
        elif (program == "fast_track"):
            request.session['is_from_fast_track'] = True
        else:
            request.session['is_from_high_school'] = True
        request.session.pop('is_all_student', None)
        request.session.pop('selected_coupon_codes', None)
        request.session.pop('cohort_start_date', None)
        request.session.pop('is_search_parameter_satisfed', None)
        return JsonResponse({"message": "success"})
    request.session['is_from_high_school'] = True
    return JsonResponse({"message": "error"})

# @login_required(login_url="/admin-login/")
def cohort_filter_view(request):
    if(request.is_ajax and request.method == "POST"):
        cohortname = request.POST.get('cohortname', None)
        if cohortname:
            cohorts = models.Cohort.cohortManager.lang_code(request.LANGUAGE_CODE).filter(Q(cohort_name__iexact=cohortname))
            # if models.step_status.objects.filter(cohort=cohortget).exists()==True:
            if cohorts.count() > 0:
                cohortdates = list(cohorts.order_by('-starting_date').values_list('cohort_id','starting_date'))
                return JsonResponse({'message': 'success', 'cohort_dates': cohortdates, 'cohortname': cohortname }, status=200, safe=False)
    else:
        return JsonResponse({'msg': _('Something went wrong')}, status=400)

class ClassSectionListView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = "counselor/class_section_list.html"

    def get(self, request, *args, **kwargs):
        context = {}
        academic_session_start_date = request.user.counselor.academic_session_start_date
        academic_session_start_date = datetime.fromisoformat(request.user.counselor.academic_session_start_date.isoformat())
        local_tz = pytz.timezone(settings.TIME_ZONE)
        academic_session_start_date = local_tz.localize(academic_session_start_date)
        is_from_high_school = request.session.get('is_from_high_school', False)
        is_from_fast_track = request.session.get('is_from_fast_track', False)
        is_from_middle_school = request.session.get('is_from_middle_school', False)
        is_from_job_course = request.session.get('is_from_job_course', False)
        is_search_parameter_satisfed = request.session.get('is_search_parameter_satisfed', False)
        is_company = request.session.get('is_company', False)
        plans = request.user.counselor.plans.all()
        # if is_search_parameter_satisfed:
        if is_from_fast_track or is_from_middle_school or is_from_high_school or is_from_job_course:
            # cohort_id = request.session.get('cohort_id', None)
            discount_code = request.session.get('selected_coupon_codes', [])
            is_all_student = request.session.get('is_all_student', False)
            all_students = None
            if request.user.counselor.company is None:
                school_name = request.user.counselor.school_name
                school_region = request.user.counselor.school_region
                school_city = request.user.counselor.school_city
                coupon_obj = Coupon.objects.filter(Q(coupon_detail__school__name=school_name) & Q (coupon_detail__school__region=school_region) & Q(coupon_detail__school__city=school_city), Q(plan__in=plans), start_date__gte = academic_session_start_date, is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track).values_list('code',flat=True)
                coupon_obj = list(coupon_obj)
                request.session['selected_coupon_codes'] = coupon_obj
                discount_code = coupon_obj
                # if is_all_student:
                print(discount_code)
                stu_payments = Payment.objects.filter(coupon_code__in = discount_code).values_list('person__id',flat=True)
                all_students = auth_mdl.Student.objects.filter(Q(discount_coupon_code__in=discount_code) | Q(person__id__in=stu_payments), Q(is_from_middle_school=is_from_middle_school) | Q(is_from_fast_track_program=is_from_fast_track)).order_by('person__last_name').distinct().select_related('person').prefetch_related('student_school_detail','student_parent_detail')
                all_students_ids = all_students.values_list('id', flat=True)
                class_section_data = auth_mdl.StudentSchoolDetail.objects.filter(student__in=all_students_ids).order_by('class_year__year_sno','class_name__name').values('class_name__name', 'class_year__name','specialization__name').annotate(total=Count('id'))
                # class_section_data = all_students.filter(person__lang_code=request.LANGUAGE_CODE).values('student_school_detail__class_name__name', 'student_school_detail__class_year__name').distinct().annotate(total=Count('id'))
                # print(obj)
                context['class_section_data'] = class_section_data
                context['all_students'] = all_students
                context['is_from_middle_school'] = is_from_middle_school
                logger.info(f"fetched students details with school detail at counselor: {request.user.username}")
                # if is_from_middle_school:
                #     return HttpResponseRedirect(reverse('counselor-dashboard') + '?ifflow=True&total_students=' + str(all_students.count()))
                return render(self.request, self.template_name, context)
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        else:
            return HttpResponseRedirect(reverse("counselor-dashboard"))


class SingleStudentDetailView(View):
    template_name = "counselor/student-detail.html"

    def get(self, request, *args, **kwargs):
        try:
            if request.user.person_role == "Student":
                logger.info(f"Redirected to home page from counselor student detail view for : {request.user.username}")
                return HttpResponseRedirect(reverse("home"))
            
            elif request.user.person_role == "Futurely_admin":
                logger.info(f"Redirected to admin_dashboard page from counselor student detail view for : {request.user.username}")
                return HttpResponseRedirect(reverse("admin_dashboard"))
            
            elif request.user.person_role == "Counselor":
                context = {}
                student_id = self.request.GET.get('student_id', None)
                logger.info(f"counselor visited student detail page with student id: {student_id} at counselor: {request.user.username}")
                student_obj = auth_mdl.Person.objects.filter(id=student_id).first()
                context['student_obj'] = student_obj
                person_ptest_mapper = student_obj.person_ptest_mapper.first()
                sorted_my_score = []
                if person_ptest_mapper:
                    logger.info(f"fetched person ptest mapper at counselor: {request.user.username}")
                    my_score = person_ptest_mapper.calculate_my_score
                    if my_score:
                        logger.info(f"fetched my score at counselor: {request.user.username}")
                        sorted_my_score = sorted(my_score.items(), key=lambda x: x[1],reverse=True)
                        context['my_score'] = my_score
                        sorted_my_score = sorted_my_score[:3]
                    else:
                        logger.warning(f"my score not found for student: {student_id} at counselor: {request.user.username}") 
                else:
                    logger.warning(f"my score not found for student: {student_id} at counselor: {request.user.username}") 
                context['sorted_my_score'] = sorted_my_score
                stuMapID = student_obj.stuMapID.all()
                if stuMapID.count() > 0:
                    logger.info(f"fetched student cohort at counselor: {request.user.username}")
                    stu_cohort = stuMapID.first()
                    stu_cohort_map = stu_cohort.stu_cohort_map.all()
                    if stu_cohort_map.count() > 0:
                        logger.info(f"fetched student cohort map at counselor: {request.user.username}")
                        stu_steps = stu_cohort_map
                        logger.info(f"fetched student steps at counselor: {request.user.username}")
                        stu_step_tracker2 = stu_steps.filter(step_status_id__step__step_sno=2).first()
                        if stu_step_tracker2:
                            stu_step2_action_item_diary = stu_step_tracker2.stu_action_items.filter(ActionItem__action_type__datatype="Diary", ActionItem__is_deleted=False).first()
                            stu_step2_action_item_diary_q2 = stu_step2_action_item_diary.action_item_diary_track.filter(action_item_diary__sno=2).first()
                            if stu_step2_action_item_diary_q2:
                                context['stu_step2_action_item_diary_q2'] = stu_step2_action_item_diary_q2.answer
                            else:
                                context['stu_step2_action_item_diary_q2'] = ""
                        stu_step_tracker3 = stu_steps.filter(step_status_id__step__step_sno=3).first()
                        if stu_step_tracker3:
                            answer = []
                            stu_step3_ai3 = stu_step_tracker3.stu_action_items.filter(ActionItem__action_sno=3, ActionItem__is_deleted=False).first()
                            if stu_step3_ai3:
                                stu_step3_ai3_table = stu_step3_ai3.action_item_type_table_track.all().first()
                                if stu_step3_ai3_table:
                                    try:
                                        data = stu_step3_ai3_table.answer
                                        # Convert voto to integers for proper comparison
                                        data['voto'] = [int(i) for i in data['voto']]
                                        # Create a combined list, sort it based on the voto values in descending order, then unzip it
                                        combined = sorted(zip(data['voto'], data['commenti'], data['le_mie_competenze']), reverse=True)
                                        data['voto'], data['commenti'], data['le_mie_competenze'] = map(list, zip(*combined))
                                        answer = data['le_mie_competenze'][:4]
                                    except:
                                        answer = []
                            context['stu_step3_ai3_table_answer'] = answer
                        stu_step_tracker7 = stu_steps.filter(step_status_id__step__step_sno=7).first()
                        if stu_step_tracker7:
                            answer = []
                            stu_step7_action_ai3 = stu_step_tracker7.stu_action_items.filter(ActionItem__action_sno=3, ActionItem__is_deleted=False).first()
                            if stu_step7_action_ai3:
                                try:
                                    stu_step7_action_ai3_framework = stu_step7_action_ai3.action_item_framework_track.all().first()
                                    if stu_step7_action_ai3_framework:
                                        stu_step7_action_ai3_framework_answer = json.loads(stu_step7_action_ai3_framework.answer)
                                    answer = stu_step7_action_ai3_framework_answer["ans1"]
                                except:
                                    answer = []
                        context['stu_step7_action_ai3_framework_answer'] = answer
                        logger.info(f"fetched student detail at counselor: {request.user.username}")
                        return render(self.request, self.template_name, context)
            else:
                logger.info(f"Redirected to home page from counselor student detail view for : {request.user.username}")
                return HttpResponseRedirect(reverse('counselor-dashboard'))
            
        except Exception as Error:
            logger.error(f"Error while fetching student detail at counselor {Error}: {request.user.username}")
            return HttpResponseRedirect(reverse('counselor-dashboard'))