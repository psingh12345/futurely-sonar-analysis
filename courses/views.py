import email
from email import header
from os import stat
import re
from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from student.models import StudentCohortMapper, StudentScholarshipTestMapper, StudentScholarShipTest, StudentsPlanMapper, StudentActionItemDiary, StudentActionItemDiaryComment, CohortStepTrackerDetails
from . import models
from django.contrib.auth.decorators import login_required
from userauth import models as auth_mdl
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from datetime import datetime, timedelta, date
import pandas as pd
import xlwt
import boto3
import logging, pytz
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
from django.views.generic import (
    ListView,
    DetailView,
    View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from userauth.models import Person
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from lib.custom_logging import CustomLoggerAdapter

adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

# Create your views here.

def calculate_endurance_and_step(stu_id, course, request):
    user = Person.objects.get(pk=stu_id)
    mycourses = user.stuMapID.filter(stu_cohort_lang=request.LANGUAGE_CODE)
    stu_mycourse = user.stuMapID.filter(stu_cohort_lang=request.LANGUAGE_CODE, cohort__module = course).first()
    endurance_list = []
    step_sno = 0
    steps = 0
    endurance_score = 0
    try:
        for i in range(mycourses.count()):
            steps = mycourses[i].stu_cohort_map.all()
            for step_i, step in enumerate(steps):
                step_sno = step_sno + 1
                score = 0
                endurance_step_data = {}
                if step.step_status_id.is_active:
                    score = 0
                    step_unloack_date = step.step_status_id.starting_date
                    step_unloack_date = datetime.fromisoformat(step_unloack_date.isoformat())
                    endurance_step_data['step_sno'] = step_sno
                    endurance_step_data['step_unloack_date'] = step_unloack_date.date
                    endurance_step_data['step_completed_date'] = ''
                    endurance_step_data['step_title'] = step.step_status_id.step.title
                    if step.is_completed:
                        score = 50
                        # step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        # datetime.datetime.fromisoformat(steps[step_sno].step_status_id.starting_date.isoformat())
                        if steps.count() > step_sno:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = datetime.fromisoformat(next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = step_unloack_date + timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        #step_completion_date = datetime.datetime.fromisoformat(step_completion_date.isoformat())
                        #time_change = datetime.timedelta()
                        #step_completion_date = step_completion_date + time_change
                        local_tz = pytz.timezone(settings.TIME_ZONE)
                        step_completion_date = local_tz.localize(step_completion_date)
                        step_completed_date = step.modified_at
                        endurance_step_data['step_completed_date'] = step_completed_date
                        if(step_completed_date < step_completion_date):
                            # print("Ok")
                            score = 100
                    endurance_step_data['score'] = score
                    endurance_score = endurance_score + score
                    endurance_list.append(endurance_step_data)
                pass
        if(len(endurance_list) != 0):
            endurance_score = endurance_score / len(endurance_list)
    except Exception as ex:
        print(ex)
    try:
        if stu_mycourse:
            steps = stu_mycourse.stu_cohort_map.all()
        if(steps.count()==0):
            steps = 0
    except:
        steps = 0
    response = {'endurance': round(endurance_score, 2), 'steps': steps}
    #print(response)
    return response

def get_step_info_for_admin(step, stu_steps):
    stu_step = None
    for stu_stp in stu_steps:
        if stu_stp.step_status_id.step.step_id == step.step_id:
            stu_step = stu_stp
            # print(stu_stp.step_status_id.step.title)
    return stu_step

def step_total_per(completed_action_item, total_action_item):
    try:
        tot_per=int(completed_action_item*100/total_action_item)
    except:
        tot_per = 100
    return tot_per

from itertools import chain

def students_kpis_csv(request, all_courses_students,response=None):
    """ student progress report"""
    logger.info("Generating student progress report in CSV format")
    headers = ['Email', 'Name', 'Class Year', 'Plan Type','Endurance'] #'step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8', 'step9', 'step10'])
    name_list = []
    email_list = []
    class_year_list = []
    endurance_list = []
    plan_type = []
    df_data_list = []
    steps_list = []
    max_columns = 0
    for course_stu in all_courses_students:
        for stu in course_stu[0]:
            name = stu.student.first_name + ' ' + stu.student.last_name
            name_list.append(name)
            email = stu.student.email
            email_list.append(email)

            class_year = stu.student.student.student_school_detail.class_year
            class_year_list.append(class_year)
            sno_list = list(range(1, int(len(name_list)+1)))
            stu_id = stu.student.id
            plan_type_data = stu.student.studentPlans.filter(plan_lang=request.LANGUAGE_CODE)[0].plans.plan_name
            plan_type.append(plan_type_data)

            course = course_stu[2]
            endurance_data = calculate_endurance_and_step(stu_id, course, request)
            endurance_list.append(endurance_data['endurance'])
            print("Headers > ", headers)
            if endurance_data['steps'] == 0:
                for i, step in enumerate(course_stu[1]):
                    steps_list.append("-")
            else:
                for i, step in enumerate(course_stu[1]):
                    get_step_info = get_step_info_for_admin(step, endurance_data['steps'])
                    if get_step_info:
                        if get_step_info.step_status_id.is_active:
                            if get_step_info.is_first_action_item_completed:
                                total_per = step_total_per(get_step_info.tot_completed, step.action_items.all().count())
                                steps_list.append("{}%".format(total_per))
                            else:
                                steps_list.append("0%")
                        else:
                            steps_list.append("-")
                    else:
                        steps_list.append("-")
                     

            for email, name ,year,plan,endurance in zip(email_list, name_list,class_year_list,plan_type,endurance_list):
                row = list(chain([email,name,year,plan,endurance], steps_list))
                df_data_list.append(row)
                max_columns = max(max_columns, len(row))
                [lst.clear() for lst in [email_list, name_list,class_year_list,endurance_list,steps_list,plan_type]]

    myvar = max_columns-5
    stepss = headers+["Step {}".format(i) for i in range(1, myvar+1)]
    df = pd.DataFrame(df_data_list)
    df = pd.concat([pd.DataFrame([stepss]), df], ignore_index=True)
    df.to_csv(path_or_buf=response, index=False, header=False, encoding='utf8')
    logger.info("Finished generating student progress report in CSV format")
    return response

# class CSVDownloadForCousnelorView(View):
#     def get(self, request):
#         school_name = request.session.get('school_name', '')
#         school_city = request.session.get('school_city', '')
#         school_region = request.session.get('school_region', '')
#         stu_email = request.session.get('stu_email', '')
#         discount_code = request.session.get('discount_code', '')
#         cohort_id = request.session.get('cohort_id', '')
#         start_date = request.session.get('start_date', '')
#         response = HttpResponse(content_type='text/csv')
#         writer = csv.writer(response)
#         if request.user.person_role == "Futurely_admin" or request.user.person_role == "Counselor" and '/students-kpis/' in request.GET.get('current_url'):
#             all_courses_students = []
#             print("################################")
#             if school_name != '' and school_city != '' and school_region != '' or stu_email != '' or discount_code != '':
#                 if stu_email != "":
#                     all_stu = auth_mdl.Person.objects.filter(email=stu_email).values_list('id', flat=True)
#                     logger.info(f"fetch students performance with email for Futurely Admin : {request.user.username}")
#                 elif discount_code != "":
#                     all_stu = auth_mdl.Person.objects.filter(student__discount_coupon_code=discount_code).values_list('id', flat=True)
#                     logger.info(f"fetch students performance with discount code for Futurely Admin : {request.user.username}")
#                 else:
#                     all_stu = auth_mdl.Person.objects.filter(student__student_school_detail__school_name=school_name,
#                         student__student_school_detail__school_region=school_region,
#                         student__student_school_detail__school_city=school_city).values_list('id', flat=True)
#                     logger.info(f"fetch students performance with school details for Futurely Admin : {request.user.username}")

#                 logger.info(f"all premium students - {all_stu} - fetched in students performance for Futurely Admin : {request.user.username}")
#                 courses = models.Modules.objects.filter(module_lang=request.LANGUAGE_CODE)
#                 for course in courses:
#                     stud = StudentCohortMapper.objects.filter(student__in=all_stu, cohort__module__module_id=course.module_id, stu_cohort_lang=request.LANGUAGE_CODE).all()#.order_by("-stu_cohort_map__step_tracker__action_item_diary__student_actions_item_diary_id__created_at")
#                     steps = course.steps.exclude(is_backup_step=True).all()
#                     if(stud.count()>0):
#                         all_courses_students.append([stud,steps,course])
#                 logger.info(f"all_courses_students -{all_courses_students}- for students performance fetched for Futurely Admin : {request.user.username}")
                
#                 response = students_kpis_csv(request,all_courses_students,response)
#                 return response
#             else:
#                 academic_session_start_date = request.user.counselor.academic_session_start_date
#                 local_tz = pytz.timezone(settings.TIME_ZONE)
#                 dt = local_tz.localize(datetime.now())
#                 all_courses_students = []
#                 # all_stu = []
#                 if request.user.counselor.company is None:
#                     school_name = request.user.counselor.school_name
#                     school_region = request.user.counselor.school_region
#                     school_city = request.user.counselor.school_city
#                     # print(school_name, school_region, school_city)
#                     all_stu = auth_mdl.Person.objects.filter(created_at__gte=academic_session_start_date, student__student_school_detail__school_name=school_name,student__student_school_detail__school_region=school_region,student__student_school_detail__school_city=school_city).values_list('id', flat=True)
#                     # print(list(all_stu))
#                     logger.info(f"Fetched students with school details at student_persormance_counselor_view for : {request.user.username}")
#                     # all_students_ids = auth_mdl.StudentSchoolDetail.objects.filter(school_name=school_name,school_region=school_region,school_city=school_city).only('id').all()
#                 else:
#                     all_stu = auth_mdl.Person.objects.filter(created_at__gte=academic_session_start_date, student__company=request.user.counselor.company ).values_list('id', flat=True)
#                     logger.info(f"Fetched students with company details at student_persormance_counselor_view for : {request.user.username}")
#                 courses = models.Modules.objects.filter(module_lang=request.LANGUAGE_CODE)
#                 page = request.GET.get('page')
#                 for course in courses:
#                     stud = StudentCohortMapper.objects.filter(student__in=all_stu, cohort__module__module_id=course.module_id, stu_cohort_lang=request.LANGUAGE_CODE).all()#.order_by("-stu_cohort_map__step_trackeraction_item_diary__student_actions_item_diary_id__created_at")
#                     steps = course.steps.exclude(is_backup_step=True).all()
#                     if(stud.count()>0):
#                         all_courses_students.append([stud,steps,course])

#                 response = students_kpis_csv(request,all_courses_students,response)
#                 return response
#         else:
#             academic_session_start_date = request.user.counselor.academic_session_start_date
#             local_tz = pytz.timezone(settings.TIME_ZONE)
#             dt = local_tz.localize(datetime.now())
#             all_courses_students = []
#             if request.user.counselor.company is None:
#                 school_name = request.user.counselor.school_name
#                 school_region = request.user.counselor.school_region
#                 school_city = request.user.counselor.school_city
#                 all_stu = auth_mdl.Person.objects.filter(created_at__gte=academic_session_start_date, student__student_school_detail__school_name=school_name,student__student_school_detail__school_region=school_region,student__student_school_detail__school_city=school_city).values_list('id', flat=True)
#                 logger.info(f"Fetched students with school details at student_persormance_counselor_view for : {request.user.username}")
#             else:
#                 all_stu = auth_mdl.Person.objects.filter(created_at__gte=academic_session_start_date, student__company=request.user.counselor.company ).values_list('id', flat=True)
#                 logger.info(f"Fetched students with company details at student_persormance_counselor_view for : {request.user.username}")
#             courses = models.Modules.objects.filter(module_lang=request.LANGUAGE_CODE)
            
#             for course in courses:
#                 stud = StudentCohortMapper.objects.filter(student__in=all_stu, cohort__module__module_id=course.module_id, stu_cohort_lang=request.LANGUAGE_CODE).all()#.order_by("-stu_cohort_map__step_trackeraction_item_diary__student_actions_item_diary_id__created_at")
#                 steps = course.steps.exclude(is_backup_step=True).all()
#                 if(stud.count()>0):
#                     all_courses_students.append([stud,steps,course])

#                 response = students_kpis_csv(request,all_courses_students, response)
#                 return response
