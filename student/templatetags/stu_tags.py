from django import template
from ..views import notification_view
from .. import models
from datetime import date, timedelta, datetime
import calendar
import pytz
from django.conf import settings
from userauth.models import Person, Student
from courses.models import Webinars
from student.models import StudentWebinarRecord, CohortStepTrackerDetails
# from student.models import GenerateNotificationBar, ReadGenerateNotificationBar

register = template.Library()

@register.simple_tag
def show_all_notifications(user):
    all_notifications=notification_view(user)
    return all_notifications

@register.simple_tag
def count_unread_notifications(user):
    all_notifications=notification_view(user)
    tot=all_notifications.filter(isread=False).count()
    return tot

@register.simple_tag
def update_notifymsg(request):
    request.session['notifymsg']=0

@register.simple_tag
def update_display_welcome_video(request):
    request.session['display_welcome_video']=0

@register.simple_tag
def step_total_per(step, total_action_item):
    try:
        completed_action_item = step.tot_completed
        tot_per=int(completed_action_item*100/total_action_item)
        CohortStepTrackerDetails.objects.update_or_create(cohort_step_tracker=step, defaults={"step_completion": tot_per})
    except:
        tot_per = 0
    return tot_per

@register.simple_tag
def left_bar(tot_per):
    val=0
    if(tot_per<50):
        val=tot_per*3.6
    else:
        val=180
    return int(val)

@register.simple_tag
def right_bar(tot_per):
    val=0
    if(tot_per<=50):
        val=0
    else:
        val=(tot_per-50)*3.6
    return int(val)

@register.simple_tag
def total_steps(all_courses):
    tot_steps=0
    for all_steps in all_courses:
        tot_steps=tot_steps+all_steps.count()
    
    return tot_steps

@register.simple_tag
def count_steps(tot):
    tot=tot+1
    return tot

@register.filter(name='times') 
def times(number):
    return range(number)

@register.simple_tag
def count_cohort_icon(tot):
    try:
        tot = int(tot)
        tot=tot-3
    except:
        tot=0
    return tot

@register.simple_tag
def add_two_number(num1,num2):
    try:
        tot=int(num1)+int(num2)
    except:
        tot = 0
    return tot

@register.simple_tag
def current_plan(request):
    try:
        student = request.user
        plan = models.StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).filter(student=student)
        if(plan.count() > 0):
            plan_name = plan[0].plans.plan_name
        else:
            plan_name = ""
    except:
        plan_name = ""
    return plan_name

@register.simple_tag
def current_plan_title(request):
    try:
        student = request.user
        plan = models.StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).filter(student=student)
        if(plan.count() > 0):
            plan=plan.first()
            if(plan.is_trial_active):
                if(plan.trial_type == "Community_to_Premium"):
                    if(request.LANGUAGE_CODE == "it"):
                        plan_name = f"Premium {plan.trail_days} giorni di prova gratuita"
                    else:
                        plan_name = f"Premium {plan.trail_days} days free trial"
                else:
                    if(request.LANGUAGE_CODE == "it"):
                        plan_name = f"Elite {plan.trail_days} giorni di prova gratuita"
                    else:
                        plan_name = f"Elite {plan.trail_days} days free trial"
            else:
                plan_name = plan.plans.plan_name

        else:
            plan_name = ""
    except:
        plan_name = ""
    return plan_name


@register.simple_tag
#@register.filter(name="define_found")
def define_found(request,val=None):
    request.session['count_my_c_found']=val
    return val

@register.simple_tag
def remove_found(request):
    del request.session['count_my_c_found']
    return "Done"

@register.simple_tag
#@register.filter(name="define_found")
def define_course_dependency(request,val=None):
    request.session['course_dependency']=val
    return val

#register.filter('define_found', define_found)

@register.simple_tag
def get_day_name(day):
    day=int(day)
    day_name = calendar.day_name[day]
    return day_name


@register.simple_tag
def date_for_weekday(day,time):
    day=int(day)
    today = date.today()
    weekday = today.weekday()
    meet_date = today + timedelta(days=day - weekday)
    meet_date = datetime.combine(meet_date,time)
    print(meet_date)
    return meet_date

@register.simple_tag
def css_version():
    return "1.1"

@register.filter
def to_char(value):
    return chr(64+value)

@register.simple_tag
def get_table_sno_for_stu_progress(page,counter):
    try:
        page = int(page)
        if(page == 1):
            return counter
        else:
            page = page - 1
            return page*20+counter
    except:
        return counter

@register.simple_tag
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
            stu_progress, is_created = models.StudentProgressDetail.objects.update_or_create(student=user.student, 
            defaults={'endurance_score': endurance_score})
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
    print(response)
    return response

@register.simple_tag
def get_step_info_for_admin(step, stu_steps):
    stu_step = None
    for stu_stp in stu_steps:
        print(stu_stp, "###################")
        if stu_stp.step_status_id.step.step_id == step.step_id:
            stu_step = stu_stp
            # print(stu_stp.step_status_id.step.title)
    return stu_step

@register.simple_tag
def get_steps_count(stu_id, request):
    user = Person.objects.get(pk=stu_id)
    mycourses = user.stuMapID.filter(stu_cohort_lang=request.LANGUAGE_CODE)
    steps = ''
    try:
        for i in range(mycourses.count()):
            steps = mycourses[i].stu_cohort_map.all()
    except Exception as ex:
        print(ex)
    return steps

# @register.simple_tag
# def genarate_notification_bar(request):
#     noti_bar = GenerateNotificationBar.objects.filter(start_date__date__gte='2022-03-24', end_date__date__lte='2022-03-25', is_active=True, country="US")
#     return noti_bar

# @register.simple_tag
# def check_read_notification(notification_id, request):
#     obj = GenerateNotificationBar.objects.get(pk=notification_id)
#     if ReadGenerateNotificationBar.objects.filter(gen_noti_bar=obj, student=request.user).exists():
#         response = True
#     else:
#         response = False
#     return response

@register.simple_tag
def is_webinar_already_joined(student, webinar):
    response = {}
    stu_webinar = student.student_webinar_record.filter(webinar=webinar).first()
    if stu_webinar is None:
        response['webinar_already_joined'] = False
        response['stu_webinar_status'] = True
        return False
    else:
        if stu_webinar.status == "Registered":
            response['stu_webinar_status'] = False
        response['webinar_already_joined'] = True
        return True

@register.simple_tag
def is_attendance_marked(student, webinar):
    stu_webinar = student.student_webinar_record.filter(webinar=webinar).first()
    if stu_webinar.status == "Registered":
        sts = False
    else:
        sts = True
    return sts

@register.filter()
def to_int(value):
    return int(value)


@register.simple_tag
def framework_filter(stu_ai_framework_answer, counter, range_count):
    try:
        ans_key = list(stu_ai_framework_answer.keys())[counter]
        ans_arr = stu_ai_framework_answer[ans_key]
        value = ans_arr[range_count]
        return value
    except Exception as Error:
        # print(f"{Error}")
        return ""

