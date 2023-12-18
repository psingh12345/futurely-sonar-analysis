import logging
import datetime
from django.contrib.auth.decorators import login_required
from django.http.response import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.conf import settings
import pytz
from . import models
from courses import models as course_models
from django.contrib import messages
from lib.unixdateformatConverter import unixdateformat
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.query_utils import Q
from .tasks import exercise_cohort_step_tracker_creation

from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

logger_console_adapter = logging.getLogger('console')
logger_console = CustomLoggerAdapter(logger_console_adapter, {})

def all_courses(context, student_cohorts, user_name, student):
    context['avail_courses'] = None
    try:
        if student_cohorts.count() > 0:
            tot_steps = 0
            course_tot_steps = []
            for mycourse in student_cohorts:
                all_steps = mycourse.stu_cohort_map.all()
                tot_steps = all_steps.count()
                print(tot_steps)
                course_tot_steps.append(tot_steps)
                if tot_steps > 0:
                    if mycourse.is_completed == False:
                        last_step = all_steps.last()
                        if last_step.step_status_id.is_active:
                            status_cohort = mycourse.is_cohort_completed
                            mycourse.is_completed = status_cohort
                            mycourse.save()
                    pcto_status = mycourse.is_eligible_for_pcto_hour
                    if (pcto_status):
                        if student.student_channel == "fully_paid":
                            if (mycourse.cohort.module.module_id == 3):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-1", defaults={'pcto_hours': 20})
                                student.update_total_pcto_hour()
                            if (mycourse.cohort.module.module_id == 4 or mycourse.cohort.module.module_id == 5):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-2", defaults={'pcto_hours': 10})
                                student.update_total_pcto_hour()
                            if (mycourse.cohort.module.module_id == 7 or mycourse.cohort.module.module_id == 8 or mycourse.cohort.module.module_id == 9):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-FS", defaults={'pcto_hours': 20})
                                student.update_total_pcto_hour()
                            if (mycourse.cohort.module.module_id == 10):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-MS", defaults={'pcto_hours': 20})
                                student.update_total_pcto_hour()
                            if (mycourse.cohort.module.module_id == 11):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Job-Course", defaults={'pcto_hours': 20})
                                student.update_total_pcto_hour()
                        if student.student_channel == "free_channel":   
                            if (mycourse.cohort.module.module_id == 3):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-1", defaults={'pcto_hours': 10})
                                student.update_total_pcto_hour()
                            if (mycourse.cohort.module.module_id == 4 or mycourse.cohort.module.module_id == 5):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-2", defaults={'pcto_hours': 10})
                                # student_pcto_records.pcto_hours = 10
                                student.update_total_pcto_hour()
                                # student_pcto_records.save()
                            if (mycourse.cohort.module.module_id == 7 or mycourse.cohort.module.module_id == 8 or mycourse.cohort.module.module_id == 9):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-FS", defaults={'pcto_hours': 20})
                                student.update_total_pcto_hour()
                            if (mycourse.cohort.module.module_id == 10):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Course-MS", defaults={'pcto_hours': 20})
                                student.update_total_pcto_hour()
                            if (mycourse.cohort.module.module_id == 11):
                                student_pcto_records, created = models.StudentPCTORecord.objects.update_or_create(
                                    student=student, pcto_hour_source="Job-Course", defaults={'pcto_hours': 20})
                                student.update_total_pcto_hour()
        logger.info(f"All courses module executed successfully : {user_name}")
    except Exception as ex:
        print(ex)
        logger.error(f"Error to get all courses {ex} : {user_name}")
    return context

def get_step_and_ai(student_cohorts):
    latest_step_track_id = 0
    next_date = None
    break_outer_loop = False
    stu_action_item_no = None
    stu_step_sno = None
    for stu_cohort in student_cohorts:
        stu_steps = stu_cohort.stu_cohort_map.all()        
        break_inner_loop = False
        for step in stu_steps:
            if step.step_status_id.is_active == False:
                next_date = step.step_status_id.starting_date
                break_outer_loop = True
                break
            elif(step.step_status_id.is_active == True and step.is_completed == False):
                latest_step_track_id = step.step_track_id
                break_outer_loop = True
                stu_action_items = step.stu_action_items.filter(ActionItem__is_deleted=False).order_by("ActionItem__action_sno")
                for stu_action_item in stu_action_items:
                    if stu_action_item.is_completed == False :
                        stu_action_item_no = stu_action_item.ActionItem.action_sno
                        stu_step_sno = stu_action_item.ActionItem.step.step_sno
                        break_inner_loop = True
                        break
                if break_inner_loop:
                    break
        if break_outer_loop:
            break
    return latest_step_track_id , stu_action_item_no , next_date, stu_step_sno



# def student_total_steps_count(student_cohort):
# 	tot_steps_count = 0
# 	for step in student_cohort.stu_cohort_map.all():  
# 		total_action_item = step.step_status_id.tot_action_items
# 		try:
# 			completed_action_item = step.tot_completed
# 			tot_per=int(completed_action_item*100/total_action_item)
# 		except Exception as err:
# 			tot_per = 0
# 		tot_steps_count += tot_per
# 	if tot_steps_count > 0:
# 		return False
# 	else:
# 		return True


def get_all_webinars(lang_code, current_plan_type, dt):
    webinars = course_models.Webinars.published.lang_code(lang_code).filter(Q(datetime_to_mark_attendance__gte=dt, webinar_accessibility__plan_name__in=[current_plan_type,])).distinct()
    return webinars

def sync_notification(student):
    logger.info(f"In sync_notification function : {student.username}")
    mycourses = student.stuMapID.all()
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt = student.created_at
    #dt = local_tz.localize(datetime.datetime.now())
    # print(dt)
    stu_notifications = student.stu_notifications.filter(created_at__gte=dt)
    logger.info(f"student notification filter with created_at for : {student.username}")
    for stu_notify in stu_notifications:
        chk_noti = models.Stu_Notification.objects.filter(
            student=student, notification=stu_notify)
        if(chk_noti.count() == 0):
            notification = models.Stu_Notification(
                student=student, notification=stu_notify, title=stu_notify.title, type=stu_notify.notification_type.notification_type)
            notification.save()
            logger.info(f"In sync_notification function saved notification : {student.username}")
    if(mycourses):
        for mycourse in mycourses:
            all_notifications = mycourse.cohort.notifications.filter(
                created_at__gte=dt)
            for notify in all_notifications:
                chk_noti = models.Stu_Notification.objects.filter(
                    student=student, notification=notify)
                if(chk_noti.count() == 0):
                    notification = models.Stu_Notification(
                        student=student, notification=notify, title=notify.title, type=notify.notification_type.notification_type)
                    notification.save()
                    logger.info(f"In sync_notification function saved notification : {student.username}")

def dashboard_announcement(student):
    logger.info(f"In dashboard_announcement for : {student.username}")
    all_notifications = student.my_notifications.filter(type="Announcements", isread=False).order_by("-created_at")
    logger.info(f"all notification fetched with filter, order_by at dashboard_announcement function for : {student.username}")
    return all_notifications

def date_list(now):
    logger.info(f"date_list function called")
    delta = datetime.timedelta(days=15)
    last = now-delta
    next = now+delta
    dela = next-last
    dates = []
    for i in range(dela.days + 1):
        day = last + datetime.timedelta(days=i)
        dates.append(day)
    return dates

def calculate_endurance(mycourses):
    endurance_list = []
    step_sno = 0
    endurance_score = 0
    local_tz = pytz.timezone(settings.TIME_ZONE)
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
                    step_unloack_date = datetime.datetime.fromisoformat(step_unloack_date.isoformat())
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
                            final_date = datetime.datetime.fromisoformat(next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                            
                        else:
                            step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        #step_completion_date = datetime.datetime.fromisoformat(step_completion_date.isoformat())
                        #time_change = datetime.timedelta()
                        #step_completion_date = step_completion_date + time_change
                        step_completion_date = local_tz.localize(step_completion_date)
                        step_completed_date = step.modified_at
                        endurance_step_data['step_completed_date'] = step_completed_date
                        if(step_completed_date < step_completion_date):
                            print("Ok")
                            score = 100
                    else:
                        if steps.count() > step_sno:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = datetime.datetime.fromisoformat(next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        step_completion_date = local_tz.localize(step_completion_date)
                    endurance_step_data['score'] = score
                    endurance_score = endurance_score + score
                    current_date = datetime.datetime.today()
                    current_date = datetime.datetime.fromisoformat(current_date.isoformat())
                    current_date = local_tz.localize(current_date)
                    if current_date < step_completion_date:
                        if score > 0:
                            endurance_list.append(endurance_step_data)
                    else:
                        endurance_list.append(endurance_step_data)
                pass
        if(len(endurance_list) != 0):
            endurance_score = endurance_score / len(endurance_list)
            endurance_score = round(endurance_score, 2)
    except Exception as ex:
        print(ex)
    return endurance_list,endurance_score

def calculate_endurance_middle_school(mycourses):
    endurance_list = []
    step_sno = 0
    endurance_score = 0
    local_tz = pytz.timezone(settings.TIME_ZONE)
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
                    step_unloack_date = datetime.datetime.fromisoformat(step_unloack_date.isoformat())
                    endurance_step_data['step_sno'] = step_sno
                    endurance_step_data['step_unloack_date'] = step_unloack_date.date
                    endurance_step_data['step_completed_date'] = ''
                    endurance_step_data['step_title'] = step.step_status_id.step.title
                    if step.is_completed:
                        score = 50
                        # step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        # datetime.datetime.fromisoformat(steps[step_sno].step_status_id.starting_date.isoformat())
                        if step_sno == 1:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = datetime.datetime.fromisoformat(next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        #step_completion_date = datetime.datetime.fromisoformat(step_completion_date.isoformat())
                        #time_change = datetime.timedelta()
                        #step_completion_date = step_completion_date + time_change
                        step_completion_date = local_tz.localize(step_completion_date)
                        step_completed_date = step.modified_at
                        endurance_step_data['step_completed_date'] = step_completed_date
                        if(step_completed_date < step_completion_date):
                            print("Ok")
                            score = 100
                    else:
                        if step_sno == 1:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = datetime.datetime.fromisoformat(next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        step_completion_date = local_tz.localize(step_completion_date)
                    endurance_step_data['score'] = score
                    endurance_score = endurance_score + score
                    current_date = datetime.datetime.today()
                    current_date = datetime.datetime.fromisoformat(current_date.isoformat())
                    current_date = local_tz.localize(current_date)
                    if current_date < step_completion_date:
                        if score > 0:
                            endurance_list.append(endurance_step_data)
                    else:
                        endurance_list.append(endurance_step_data)
                pass
        if(len(endurance_list) != 0):
            endurance_score = endurance_score / len(endurance_list)
            endurance_score = round(endurance_score, 2)
    except Exception as ex:
        print(ex)
    return endurance_list, endurance_score

def get_fast_track_dashboard_elements(person, student_cohorts, current_plan, dt, lang_code, context):
    student_cohort = student_cohorts.first()
    # exercise_cohort_step_tracker_creation.apply_async(args=[person.username, person.pk, student_cohort.cohort_id])
    context['mycourse'] = student_cohort
    # context['tot_steps_count'] = student_total_steps_count(student_cohort)
    latest_step_track_id , stu_action_item_no , next_date, stu_step_sno = get_step_and_ai(student_cohorts)
    context['step_track_id'] = latest_step_track_id
    context['action_item'] = stu_action_item_no
    context['stu_step_sno'] = stu_step_sno
    context['next_date'] = next_date
    context['msg_continue_cta'] = _("Congratulations, you have completed all the available steps! The next step will unlock on ")
    context['webinars'] = get_all_webinars(lang_code, current_plan, dt)
    context['webinar_time'] = dt
    context['dashboard_announcements'] = dashboard_announcement(person)
    endurance_list, endurance_score = calculate_endurance(student_cohorts)
    kpis = {'confidence': 0, 'awareness': 0, 'curiosity': 0,'endurance_list':endurance_list,'endurance_score':endurance_score}
    try:
        kpis = person.student.student_endurance_score
        kpis = {'confidence': kpis.confidence_score, 'awareness': kpis.awareness_score, 'curiosity': kpis.curiosity_score,'endurance_list':endurance_list,'endurance_score':endurance_score}
    except:
        kpis = kpis
    context['kpis'] = kpis
    context['current_date'] = dt.date()
    context['dates'] = date_list(dt.date())
    welcome_video = course_models.WelcomeVideo.objects.filter(module_lang=lang_code,is_published = True).first()
    context['videos_objs'] = course_models.MyBlogVideos.objects.filter(is_for_fast_track=True).all()
    if welcome_video:
        context['welcome_video_link'] = welcome_video.video_link
    else:
        context['welcome_video_link'] = None
    return context

def get_middle_school_dashboard_elements(person, student_cohorts, current_plan, dt, lang_code, context):
    student_cohort = student_cohorts.first()
    # exercise_cohort_step_tracker_creation.apply_async(args=[person.username, person.pk, student_cohort.cohort_id])
    latest_step_track_id , stu_action_item_no , next_date, stu_step_sno = get_step_and_ai(student_cohorts)
    context['step_track_id'] = latest_step_track_id
    context['action_item'] = stu_action_item_no
    context['stu_step_sno'] = stu_step_sno
    context['mycourse'] = student_cohort
    # context['tot_steps_count'] = student_total_steps_count(student_cohort)
    context['dashboard_announcements'] = dashboard_announcement(person)
    endurance_list, endurance_score = calculate_endurance_middle_school(student_cohorts)
    kpis = {'confidence': 0, 'awareness': 0, 'curiosity': 0,'endurance_list':endurance_list,'endurance_score':endurance_score}
    try:
        kpis = person.student.student_endurance_score
        kpis = {'confidence': kpis.confidence_score, 'awareness': kpis.awareness_score, 'curiosity': kpis.curiosity_score,'endurance_list':endurance_list,'endurance_score':endurance_score}
    except:
        kpis = kpis
    context['kpis'] = kpis
    welcome_video = course_models.WelcomeVideo.objects.filter(module_lang=lang_code,is_published = True).first()
    if welcome_video:
        context['welcome_video_link'] = welcome_video.video_link
    else:
        context['welcome_video_link'] = None
    return context

@login_required(login_url="/login/")
def index_view(request):
    person = request.user
    request.session['is_from_job_course'] = False
    logger.info(f"In index_view page for : {person.username}")
    if request.user.person_role == "Counselor":
        logger.info(f"Redirected to counselor-dashboard from index_view page : {person.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(f"Redirected to counselor-dashboard from index_view page : {person.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    context = {}
    template_name = "student/new_plans/new-fast-track-dashboard.html"
    student_plan = models.StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).filter(student=person).first()
    print(student_plan)
    if request.user.clarity_token is None:
        request.user.clarity_token = request.session.get('clarity_token', '')
        request.user.save()
    else:
        request.session['clarity_token'] = request.user.clarity_token
    if student_plan:
        print("1")
        current_plan = student_plan.plans.plan_name
        local_tz = pytz.timezone(settings.TIME_ZONE)
        dt = local_tz.localize(datetime.datetime.now())
        now = dt.date()
        current_plan_name = request.session.get('current_plan_name', None)  
        if current_plan_name is None:
            request.session['current_plan_name'] = current_plan
        print(current_plan)
        student_cohorts = student_plan.stu_cohort_map.filter(stu_cohort_lang=request.LANGUAGE_CODE).order_by('cohort__module__module_priority')
        context = all_courses(context, student_cohorts, person.username, person.student)
        if current_plan == course_models.PlanNames.JobCourse.value:
            request.session['is_from_job_course'] = True
        if current_plan in [course_models.PlanNames.Community.value, course_models.PlanNames.Premium.value, course_models.PlanNames.Elite.value, course_models.PlanNames.Trial2022.value, course_models.PlanNames.Diamond.value]:
            return HttpResponseRedirect(reverse("home1"))
        elif current_plan == course_models.PlanNames.MiddleSchool.value:
            logger.info(f"In Middle school Dashboard view : {person.username}")
            context = get_middle_school_dashboard_elements(person, student_cohorts, current_plan, dt, request.LANGUAGE_CODE, context)
            template_name = "student/new_plans/new-middle-school-dashboard.html"
        else:
            logger.info(f"In Fast track Dashboard view : {person.username}")
            context = get_fast_track_dashboard_elements(person, student_cohorts, current_plan, dt, request.LANGUAGE_CODE, context)
            logger.info(f"Dashboard page visited by : {person.username}")
            template_name = "student/new_plans/new-fast-track-dashboard.html"
    else:
        return HttpResponseRedirect(reverse("home1"))

    # print(student.studentsplanmapper_set.plansManager.lang_code(request.LANGUAGE_CODE).all())
    # template_name = "student/index-new-plans-struct.html"
    return render(request, template_name , context)
