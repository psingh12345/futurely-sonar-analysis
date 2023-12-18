import json
import pandas as pd
from django.db.models import F, Sum
import pdb
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import calendar
import datetime
import logging
import os
from typing import ContextManager

import pytz
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, message, send_mail
# from typing_extensions import TypeGuard
from django.db.models.aggregates import Count
from django.db.models.query_utils import PathInfo, Q
from django.http import JsonResponse
from django.http.response import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.urls import reverse
from django.utils import html, timezone
from django.utils.decorators import method_decorator
from django.utils.functional import partition
from django.utils.timezone import localtime
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from courses.models import (Blog_post, Cohort, MyBlogVideos, MyGroups,
                            MyResources, MyVideos, Notification_type, OurPlans,
                            PersonalityTest, PersonalityTestQuestion,
                            ScholarshipTest, WebinarQuestionnaire, Webinars, WelcomeVideo, MyPdfs, TestCohortID,
                            ActionItemConnectWithOtherActionItem)
from lib.helper import (calculate_discount_and_final_price,
                        calculate_discount_parameters, create_custom_event)
from lib.hubspot_contact_sns import create_update_contact_hubspot
from lib.unixdateformatConverter import unixdateformat
from payment.models import Coupon, Payment
from userauth import models as userauth_models
from website.views import PERSON
from .tasks import send_email_task
from . import models
from .tasks import exercise_cohort_step_tracker_creation, link_with_action_items, update_endurance_score, step_completions, update_hubspot_properties, ai_generated_comment_for_stu_action_item_diary #create_hubspot_tickets
from lib.custom_logging import CustomLoggerAdapter
from datetime import timedelta
from django.db.models import Case, When, Value, BooleanField


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

logger_console_adapter = logging.getLogger('console')
logger_console = CustomLoggerAdapter(logger_console_adapter, {})


# @login_required(login_url="/login/")
# def generate_noti_bar_view(request):
#     if request.method == "POST" and request.is_ajax:
#         request_post = request.POST
#         notification_id = request_post.get('notification_id')
#         print("notification_id", notification_id)
#         noti_obj = models.GenerateNotificationBar.objects.get(id=int(notification_id))
#         read_noti_obj = models.ReadGenerateNotificationBar.objects.filter(gen_noti_bar=noti_obj, student=request.user)
#         if not read_noti_obj.exists():
#             print(read_noti_obj)
#             models.ReadGenerateNotificationBar.objects.create(student=request.user, gen_noti_bar=noti_obj, is_visible_marked=True)
#             logger.info(f"Create obj read notification at generate_noti_bar_view for : {request.user.username}")
#             return JsonResponse({"message": "notification closed"}, safe=False)
#     return JsonResponse({"message": "Something went wrong"}, safe=False)


def our_plans(request):
    logger.info(f"In our_plans called by : {request.user.username}")
    context = {}
    context['all_plans'] = models.courseMdl.OurPlans.plansManager.lang_code(
        request.LANGUAGE_CODE).all()
    logger.info(f"our plans obj visited by : {request.user.username}")
    return context


def get_trial_cohorts(request, context):
    student = request.user
    logger.info(f"In get_trial_cohorts called by : {student.username}")
    avail_courses = models.courseMdl.Modules.moduleManager.lang_code(
        request.LANGUAGE_CODE).all().order_by('module_priority')
    if (avail_courses):
        trial_cohorts_info = []
        context['avail_courses'] = avail_courses
        for course in avail_courses:
            trial_cohorts_info.append(models.courseMdl.Cohort.objects.filter(
                module=course.module_id, is_active="Yes", cohort_type="Trial", is_for_middle_school=False, is_for_fast_track_program=False))
        context['trial_cohorts_info'] = trial_cohorts_info
        logger.info(
            f"fetched cohorts in get_trial_cohorts for : {student.username}")
        return context
    else:
        return context


def get_all_plans(request):
    context = {}
    student = request.user
    logger.info(f"In get_all_plan called by : {student.username}")
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt = local_tz.localize(datetime.datetime.now())

    try:
        context = our_plans(request)
        all_plans = context['all_plans']

        plan = models.StudentsPlanMapper.plansManager.lang_code(
            request.LANGUAGE_CODE).filter(student=student)
        if (plan.count() > 0):
            context['plan'] = plan #.plans.all()
            plan = plan.first()
            context['current_plan_type'] = plan.plans.plan_name
            context['is_trial_expired'] = plan.is_trial_expired
            context['is_trial_active'] = plan.is_trial_active
            if (plan.is_trial_expired):
                if (plan.trial_type == "Community_to_Premium"):
                    context['trial_expired_plan_name'] = "elite"
                    p_plan = all_plans.filter(plan_name="Premium").first()
                    request.session['plan_id_to_upgrade'] = p_plan.id
                    e_plan = all_plans.filter(plan_name="Elite").first()
                    request.session['elite_plan_id_to_upgrade'] = e_plan.id
                else:
                    context['trial_expired_plan_name'] = "elite"
                    e_plan = all_plans.filter(plan_name="Elite").first()
                    request.session['plan_id_to_upgrade'] = e_plan.id

            if (plan.is_trial_active):
                plan_days_left = (plan.trial_end_date - dt).days+1
                context['plan_days_left'] = plan_days_left
                context['trial_end_date'] = plan.trial_end_date
                if (plan.trial_type == "Community_to_Premium"):
                    context['trial_plan_name'] = "elite"
                    p_plan = all_plans.filter(plan_name="Premium").first()
                    request.session['plan_id_to_upgrade'] = p_plan.id
                    e_plan = all_plans.filter(plan_name="Elite").first()
                    request.session['elite_plan_id_to_upgrade'] = e_plan.id
                else:
                    context['trial_plan_name'] = "elite"
                    e_plan = all_plans.filter(plan_name="Elite").first()
                    request.session['plan_id_to_upgrade'] = e_plan.id
            logger.info(
                f"fetched plan obj at get_all_plans : {student.username}")
            current_plan = ""
        else:
            # context
            current_plan = None
    except Exception as err:
        current_plan = None
        user_name = request.user.username
        logger.warning(f"Error in get_all_plans {err} : {user_name}")
    return context, current_plan


@login_required(login_url="/login/")
def welcome_recommendations_view(request):
    try:
        student = request.user
        logger.info(
            f"In welcome recommendation page called by : {student.username}")
        if request.user.person_role == "Counselor":
            logger.info(
                f"Redirected to counselor-dashboard at welcome recommendations view page for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if request.user.person_role == "Futurely_admin":
            logger.info(
                f"Redirected to counselor-dashboard at welcome recommendations view page for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        payment_type = request.session.get('payment_type', None)
        if payment_type is None:
            request.session['payment_type'] = "One Time"
            payment_type = "One Time"

        number_of_plans = student.student.number_of_offered_plans
        discount_code = student.student.discount_coupon_code
        # coupon_details = Coupon.active_objects.filter(code__iexact=discount_code).first()
        # if coupon_details is None:
        #     discount_code = request.session.get('coupon_code_after_trial','')

        student_type_from_coupon = ""
        coupon_details = ""
        try:
            if (discount_code != ""):
                coupon_details = Coupon.active_objects.filter(
                    code__iexact=discount_code).first()
                if coupon_details:
                    logger.info(
                        f"{discount_code}-Coupon obj linked at welcome_recommendations_view page for : {student.username}")
                    student_type_from_coupon = coupon_details.coupon_type
                    coupon_code_exists = student
                else:
                    coupon_code_exists = "None"
            else:

                coupon_code_exists = "None"
        except:
            context = {}
            coupon_code_exists = "None"
            context['coupon_code_applied'] = False
            print("No mantched coupon code found")  # error
            logger.info(
                f"{discount_code}-Coupon code didn't match for : {student.username}")

        # student_type_from_coupon
        if (number_of_plans == "2"):
            template_page = "student/welcome-page-new-plans.html"
        else:
            template_page = "student/welcome-page-new-plans.html"

        try:
            plan = models.StudentsPlanMapper.plansManager.lang_code(
                request.LANGUAGE_CODE).filter(student=student)
            logger.info(
                f"plan obj linked at welcome view page : {student.username}")
            plan_stu = plan.first()
            if (plan.count() > 0):
                if plan_stu.plans.plan_name != "Trial2022":
                    logger.info(
                        f"Redirected from recommendations to dashboard: {student.username}")
                    return HttpResponseRedirect(reverse("home"))

            context, current_plan = get_all_plans(request)
            # if plan_stu:
            #     context['is_trial_active'] = plan_stu.is_trial_active
            #     context['is_trial_expired'] = plan_stu.is_trial_expired
            if request.LANGUAGE_CODE == "it":
                template_page = "student/welcome-page-new-plans-it.html"
                try:
                    starting_date = datetime.date.today()
                    premium_cohort_start = Cohort.objects.filter(
                        starting_date__gte=starting_date, module__module_id=3).order_by('starting_date').first()
                    elite_cohort_start = Cohort.objects.filter(
                        starting_date__gte=starting_date, module__module_id=4).order_by('starting_date').first()
                    if premium_cohort_start is not None:
                        premium_delta = premium_cohort_start.starting_date - starting_date
                        context["premium_days_left"] = premium_delta.days
                    if elite_cohort_start is not None:
                        elite_delta = elite_cohort_start.starting_date - starting_date
                        context["elite_days_left"] = elite_delta.days
                except Exception as err:
                    print(err)
                    logger.warning(
                        f"Warning in get cohort next start date for : {student.username}")
            context = get_trial_cohorts(request, context)
            context['future_lab_form_filled'] = student.student.future_lab_form_status
            context['student_type_from_coupon'] = student_type_from_coupon
            context['cost_after_dis'] = 0
            context['coupon_details'] = coupon_details
            context['coupon_code_exists'] = coupon_code_exists
            context["payment_type"] = payment_type
            # print(student_type_from_coupon)
            print(context)
            logger.info(
                f"Successfully visited welcome recommendations page : {student.username}")
            return render(request, template_page, context)
        except Exception as ex:
            # print("Welcom error")
            context = our_plans(request)
            context = get_trial_cohorts(request, context)
            context['future_lab_form_filled'] = student.student.future_lab_form_status
            context['student_type_from_coupon'] = student_type_from_coupon
            logger.error(f"Error at welcome page {ex}: {student.username}")
            return render(request, template_page, context)
    except Exception as er:
        user_name = request.user.username
        logger.critical(
            f"Error in welcome_recommendations_page {er} : {user_name}")
        return HttpResponseRedirect(reverse("login"))


@login_required(login_url="/login/")
def buy_plan(request, plan_id):
    student = request.user
    logger.info(f"In buy_plan page called by : {student.username}")
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to counselor-dashboard at buy_plan view page for : {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to counselor-dashboard at buy_plan view page for : {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    try:
        payment_type = request.GET.get('payment_type', None)
        if payment_type:
            request.session["payment_type"] = payment_type
        print(payment_type)
        print(request.session["payment_type"])
        print("--------------------------")
        plan = models.StudentsPlanMapper.plansManager.lang_code(
            request.LANGUAGE_CODE).filter(student=student)
        logger.info(
            f"current plan obj linked at buy_plan view page for : {student.username}")

        if plan.count() > 0:
            plan_stu = plan.first()
            if plan_stu.plans.plan_name != "Trial2022":
                logger.info(
                    f"Redirected to home page from buy_plan page for : {student.username}")
                return HttpResponseRedirect(reverse("home"))
        selected_plan = models.courseMdl.OurPlans.plansManager.lang_code(
            request.LANGUAGE_CODE).get(id=plan_id)
        logger.info(f"Plan obj linked at buy_plan for : {student.username}")
        if selected_plan.plan_name == "Community":
            if request.LANGUAGE_CODE == 'en-us':
                currency = 'usd'
            elif request.LANGUAGE_CODE == 'it':
                currency = 'eur'
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=request.user,
                                   plan=selected_plan, coupon_code="", actual_amount="0", discount="0", custom_user_session_id=custom_user_session_id)
            logger.info(
                f"payment obj updated at buy_plan for : {student.username}")
            stu_pln_obj, stu_pln_obj_created = models.StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(
                student=request.user, plan_lang=request.LANGUAGE_CODE, defaults={'plans': selected_plan})
            logger.info(
                f"student plan obj update_or_create at buy_plan for : {student.username}")
            try:
                # hubspotContactupdateQueryAdded
                logger.info(
                    f"In hubspot plan enroll student buy plan community parameter building for : {request.user.username}")
                keys_list = ["email", "hubspot_community_plan_enroll_date",
                             "hubspot_community_plan_paid_amount", "community_plan_enroll_date"]
                if stu_pln_obj_created:
                    plan_created_at = str(stu_pln_obj.created_at)
                    community_plan_enroll_date = unixdateformat(
                        stu_pln_obj.created_at)
                else:
                    plan_created_at = str(stu_pln_obj.modified_at)
                    community_plan_enroll_date = unixdateformat(
                        stu_pln_obj.modified_at)

                values_list = [request.user.username,
                               plan_created_at, "0", community_plan_enroll_date]
                create_update_contact_hubspot(
                    request.user.username, keys_list, values_list)
                logger.info(
                    f"In hubspot plan enroll student buy plan community parameter update completed for : {request.user.username}")
            except Exception as ex:
                logger.error(
                    f"Error at hubspot plan enroll student buy plan community parameter update {ex} for : {request.user.username}")
            return redirect(reverse("home"))

        request.session['plan_id'] = plan_id
        user_name = request.user.username
        logger.info(f"Redirected to order-summary from buy_plan: {user_name}")
        return redirect('order-summary')

    except Exception as e:
        print(e)
        user_name = request.user.username
        logger.critical(f"Error at buy_plan view page {e} for : {user_name}")
        # messages.error(request, 'Plan does not exists...')
        return HttpResponseRedirect(reverse('futurely-plans'))


@login_required(login_url="/login/")
def buy_course(request, cohort_id):
    try:
        student = request.user
        logger.info(f"In buy_course view page : {student.username}")
        if request.user.person_role == "Counselor":
            logger.info(
                f"Redirected to counselor-dashboard at buy_course view page for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if request.user.person_role == "Futurely_admin":
            logger.info(
                f"Redirected to counselor-dashboard at buy_course view page for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        cohort = models.courseMdl.Cohort.objects.get(cohort_id=cohort_id)
        logger.info(f"Cohort fetched at buy_course for : {student.username}")
        status, previous_mdls = check_priority(request, cohort)
        if (status == True):
            # discount = 0
            request.session['cohort_ids'] = list(cohort_id)
            # request.session['discount'] = discount
            user_name = request.user.username
            logger.info(
                f"Redirected to order-summary from buyplan: {user_name}")
            return redirect('order-summary')
        else:
            messages.error(
                request, 'Please purchase course 1 to unlock this course.')
            user_name = request.user.username
            logger.warning(f"Error in buycourse page : {user_name}")
            return HttpResponseRedirect(reverse('futurely-plans'))
    except Exception as ex:
        messages.error(request, 'Operation failed!')
        user_name = request.user.username
        logger.critical(f"Error in buy course {ex}: {user_name}")
    return HttpResponseRedirect(reverse('futurely-plans'))


def sync_notification(student):
    logger.info(f"In sync_notification function : {student.username}")
    mycourses = student.stuMapID.all()
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt = student.created_at
    # dt = local_tz.localize(datetime.datetime.now())
    # print(dt)
    stu_notifications = student.stu_notifications.filter(created_at__gte=dt)
    logger.info(
        f"student notification filter with created_at for : {student.username}")
    for stu_notify in stu_notifications:
        chk_noti = models.Stu_Notification.objects.filter(
            student=student, notification=stu_notify)
        if (chk_noti.count() == 0):
            notification = models.Stu_Notification(
                student=student, notification=stu_notify, title=stu_notify.title, type=stu_notify.notification_type.notification_type)
            notification.save()
            logger.info(
                f"In sync_notification function saved notification : {student.username}")
    if (mycourses):
        for mycourse in mycourses:
            all_notifications = mycourse.cohort.notifications.filter(
                created_at__gte=dt)
            for notify in all_notifications:
                chk_noti = models.Stu_Notification.objects.filter(
                    student=student, notification=notify)
                if (chk_noti.count() == 0):
                    notification = models.Stu_Notification(
                        student=student, notification=notify, title=notify.title, type=notify.notification_type.notification_type)
                    notification.save()
                    logger.info(
                        f"In sync_notification function saved notification : {student.username}")


def notification_view(student):
    logger.info(f"In notification view function : {student.username}")
    sync_notification(student)
    my_alerts_lst = []
    my_alerts = student.person_notifications.all()
    logger.info(f"person notifications fetched for : {student.username}")
    for alrt in my_alerts:
        my_alerts_lst.append(alrt.notification_type.notification_type)
    all_notifications = student.my_notifications.filter(
        type__in=my_alerts_lst).order_by("-created_at")
    logger.info(
        f"all notification fetched with filter, order_by at notification_view for : {student.username}")
    return all_notifications


def dashboard_announcement(student):
    logger.info(f"In dashboard_announcement for : {student.username}")
    sync_notification(student)
    all_notifications = student.my_notifications.filter(
        type="Announcements", isread=False).order_by("-created_at")
    logger.info(
        f"all notification fetched with filter, order_by at dashboard_announcement function for : {student.username}")
    return all_notifications


def calculate_endurance_middle_school(user, lang_code):
    mycourses = user.stuMapID.filter(stu_cohort_lang=lang_code)
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
                    step_unloack_date = datetime.datetime.fromisoformat(
                        step_unloack_date.isoformat())
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
                            final_date = datetime.datetime.fromisoformat(
                                next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = step_unloack_date + \
                                datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59)  # test
                        # step_completion_date = datetime.datetime.fromisoformat(step_completion_date.isoformat())
                        # time_change = datetime.timedelta()
                        # step_completion_date = step_completion_date + time_change
                        step_completion_date = local_tz.localize(
                            step_completion_date)
                        step_completed_date = step.modified_at
                        endurance_step_data['step_completed_date'] = step_completed_date
                        if (step_completed_date < step_completion_date):
                            print("Ok")
                            score = 100
                    else:
                        if step_sno == 1:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = datetime.datetime.fromisoformat(
                                next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = step_unloack_date + \
                                datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59)  # test
                        step_completion_date = local_tz.localize(
                            step_completion_date)
                    endurance_step_data['score'] = score
                    endurance_score = endurance_score + score
                    current_date = datetime.datetime.today()
                    current_date = datetime.datetime.fromisoformat(
                        current_date.isoformat())
                    current_date = local_tz.localize(current_date)
                    if current_date < step_completion_date:
                        if score > 0:
                            endurance_list.append(endurance_step_data)
                    else:
                        endurance_list.append(endurance_step_data)
                pass
        if (len(endurance_list) != 0):
            endurance_score = endurance_score / len(endurance_list)
    except Exception as ex:
        print(ex)
    return endurance_list, endurance_score


def calculate_endurance(request):
    user = request.user
    mycourses = user.stuMapID.filter(stu_cohort_lang=request.LANGUAGE_CODE)
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
                    step_unloack_date = datetime.datetime.fromisoformat(
                        step_unloack_date.isoformat())
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
                            final_date = datetime.datetime.fromisoformat(
                                next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date

                        else:
                            step_completion_date = step_unloack_date + \
                                datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59)  # test
                        # step_completion_date = datetime.datetime.fromisoformat(step_completion_date.isoformat())
                        # time_change = datetime.timedelta()
                        # step_completion_date = step_completion_date + time_change
                        step_completion_date = local_tz.localize(
                            step_completion_date)
                        step_completed_date = step.modified_at
                        endurance_step_data['step_completed_date'] = step_completed_date
                        if (step_completed_date < step_completion_date):
                            print("Ok")
                            score = 100
                    else:
                        if steps.count() > step_sno:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = datetime.datetime.fromisoformat(
                                next_date.isoformat()) - step_unloack_date
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = step_unloack_date + \
                                datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59)  # test
                        step_completion_date = local_tz.localize(
                            step_completion_date)
                    endurance_step_data['score'] = score
                    endurance_score = endurance_score + score
                    current_date = datetime.datetime.today()
                    current_date = datetime.datetime.fromisoformat(
                        current_date.isoformat())
                    current_date = local_tz.localize(current_date)
                    if current_date < step_completion_date:
                        if score > 0:
                            endurance_list.append(endurance_step_data)
                    else:
                        endurance_list.append(endurance_step_data)
                pass
        if (len(endurance_list) != 0):
            endurance_score = endurance_score / len(endurance_list)
    except Exception as ex:
        print(ex)
    return endurance_list, endurance_score


def calculate_kpis(request):
    if request.user.student.is_from_middle_school:
        endurance_list, endurance_score = calculate_endurance_middle_school(
            request.user, request.LANGUAGE_CODE)
    else:
        endurance_list, endurance_score = calculate_endurance(request)
    user = request.user
    logger.info(f"In calculate_kpis function : {user.username}")
    mycourses = user.stuMapID.filter(stu_cohort_lang=request.LANGUAGE_CODE)
    tot_confidence = 0
    tot_awareness = 0
    tot_curiosity = 0
    for i in range(mycourses.count()):
        confidence = 0
        awareness = 0
        curiosity = 0
        steps = mycourses[i].stu_cohort_map.all()
        for step_i, step in enumerate(steps):
            if step.is_completed is True:
                if i == 0 and step_i == 0:
                    tot_confidence = 50
                    tot_awareness = 20
                    tot_curiosity = 12
                    confidence = confidence+0.4
                    awareness = awareness+2
                    curiosity = curiosity+0.5
                elif i == 0:
                    confidence = confidence+0.4
                    awareness = awareness+2
                    curiosity = curiosity+0.5
                else:
                    confidence = confidence+0.9
                    awareness = awareness+2.5
                    curiosity = curiosity+1.8
        tot_awareness = tot_awareness+awareness
        tot_confidence = tot_confidence+confidence
        tot_curiosity = tot_curiosity+curiosity
        if (tot_awareness > 100):
            tot_awareness = 100
        if (tot_confidence > 100):
            tot_confidence = 100
        if (tot_curiosity > 100):
            tot_curiosity = 100
    kpis = {'confidence': int(tot_confidence), 'awareness': int(
        tot_awareness), 'curiosity': int(tot_curiosity), 'endurance_list': endurance_list, 'endurance_score': int(endurance_score)}
    stu_progress, is_created = models.StudentProgressDetail.objects.update_or_create(student=user.student,
                                                                                     defaults={'endurance_score': int(endurance_score), 'confidence_score': int(tot_confidence),
                                                                                               'awareness_score': int(tot_awareness), 'curiosity_score': int(tot_curiosity)})
    logger.info(f"student progress report updated for : {user.username}")
    return kpis


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


def get_steps_info_for_todos(request, dt):
    logger.info(
        f"In get_steps_info_for_todos called by : {request.user.username}")
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt_now = local_tz.localize(datetime.datetime.now())
    date_now = dt_now.date()
    user = request.user
    my_courses = user.stuMapID.filter(
        cohort__cohort_type="Paid", stu_cohort_lang=request.LANGUAGE_CODE)
    logger.info(
        f"courses fetched at get_steps_info_for_todos for : {request.user.username}")
    lst_steps = []
    if (dt >= date_now):
        for i in range(my_courses.count()):
            steps = my_courses[i].stu_cohort_map.all()
            for step_i, step in enumerate(steps):
                if step.is_completed is False and step.step_status_id.is_active is True:
                    stp = f"Step {step_i+1}: {step.step_status_id.step.title}"
                    dct_stp = {"id": step.step_track_id, "stp_msg": stp}
                    lst_steps.append(dct_stp)
    return lst_steps


def get_todo(request, dt):
    student = request.user
    logger.info(f"In get_todo for : {student.username}")
    todos = request.user.todos.all().filter(dated=dt)
    lst_todos = []
    if (todos):
        for i, todo in enumerate(todos):
            msg = f"{html.escape(todo.title)}"
            dct_todo = {"id": todo.id, "msg": msg}
            lst_todos.append(dct_todo)
    lst_steps = get_steps_info_for_todos(request, dt)
    # lst_todos = lst_todos + lst_steps
    return lst_todos, lst_steps


def my_groups(request):
    user = request.user
    logger.info(f"In my_groups function called by : {user.username}")
    mycohorts = user.stuMapID.filter(stu_cohort_lang=request.LANGUAGE_CODE)
    logger.info(
        f"cohorts filter with language code at my_groups for : {user.username}")
    groups = []
    for mycohort in mycohorts:
        grps = mycohort.cohort.mygroups.all()
        if (grps.count() > 0):
            groups.append(grps)
    return groups


def my_resources(request):
    student = request.user
    resources = MyResources.resourceManager.lang_code(
        request.LANGUAGE_CODE).all()
    logger.info(
        f"resources filter with language code at my_resourses for : {student.username}")
    return resources


def my_videos(request):
    student = request.user
    videos = MyVideos.videoManager.lang_code(request.LANGUAGE_CODE).all()
    logger.info(
        f"videos filter with lang code at my_videos function for : {student.username}")
    return videos


@login_required(login_url="/login/")
def upgrade_plan(request, plan_id):
    try:
        student = request.user
        logger.info(f"In upgrade plan called by : {student.username}")
        if request.user.person_role == "Counselor":
            logger.info(
                f"Redirected to counselor-dashboard at upgrade_plan view page for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if request.user.person_role == "Futurely_admin":
            logger.info(
                f"Redirected to counselor-dashboard page at upgrade_plan view page for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        current_plan = models.StudentsPlanMapper.plansManager.lang_code(
            request.LANGUAGE_CODE).filter(student=student).first()
        logger.info(f"plan obj linked at upgrade plan : {student.username}")
        print("--------------------")
        if current_plan:
            current_plan_name = current_plan.plans.plan_name
            plan_to_upgarde = models.courseMdl.OurPlans.plansManager.lang_code(
                request.LANGUAGE_CODE).get(id=plan_id)
            logger.info(
                f"get plan obj at upgrade_plan for : {student.username}")
            plan_to_upgarde_name = plan_to_upgarde.plan_name
            if (current_plan.is_trial_active):
                request.session['plan_id'] = plan_id
                user_name = request.user.username
                logger.info(
                    f"Redirected to order-summary at upgrade_plan page for : {user_name}")
                return redirect('order-summary')
            else:
                if current_plan_name == "Community" and (plan_to_upgarde_name == "Premium" or plan_to_upgarde_name == "Elite"):
                    request.session['plan_id'] = plan_id
                    user_name = request.user.username
                    logger.info(
                        f"Redirected to order-summary at upgrade_plan page: {user_name}")
                    return redirect('order-summary')
                elif current_plan_name == "Premium" and plan_to_upgarde_name == "Elite":
                    user_name = request.user.username
                    logger.info(
                        f"Redirected to order-summary at updgrade_plan for : {user_name}")
                    request.session['plan_id'] = plan_id
                    return redirect('order-summary')
        logger.info(
            f"Redirected to order-summary from updgrade_plan for : {student.username}")
        return redirect('home')
    except Exception as ex:
        context = our_plans(request)
        logger.critical(
            f"Error in upgrade_plan {ex} : {request.user.username}")
        # messages.error(request, 'Plan does not exists...')
    return HttpResponseRedirect(reverse('futurely-plans'))

# def update_couponcode_futurelab_stu():
#     df=pd.read_excel('final_to_add.xlsx')
#     print(df)
#     for indx,row in df.iterrows():
#         lst_user=row['Email Id']
#         code = row['Code']
#         try:
#             person = userauth_models.Person.objects.get(username=lst_user)
#             print(person.student.id)
#             stu = userauth_models.Student.objects.get(person_id = person.id)
#             print(stu.discount_coupon_code)
#             print(stu.src)
#             print("-------------------")
#             stu.are_you_a_student="Yes"
#             stu.discount_coupon_code=code
#             stu.src = "future_lab"
#             stu.save()
#             print("Save")
#         except:
#             print("Error")
#     return None


def my_meetups(request, current_plan_type):
    if (current_plan_type == "Community"):
        # print("In community")
        """Meetup link will get displayed on 3rd week from sign up"""
        """Will gte display only till the start time + 30 min """
        student = request.user
        student_signed_up_date = student.created_at
        local_tz = pytz.timezone(settings.TIME_ZONE)
        dt = local_tz.localize(datetime.datetime.now())
        monday = student_signed_up_date - \
            datetime.timedelta(days=student_signed_up_date.weekday())
        monday2 = dt-datetime.timedelta(days=dt.weekday())
        display_time = (dt - datetime.timedelta(minutes=30)).time()
        current_week = int(((monday2 - monday).days / 7) + 1)
        # print(f" Current week : {current_week}")
        current_day = dt.weekday()
        # print(f"Display time : {display_time}")
        # print(student_signed_up_date.weekday())
        # print(calendar.day_name[student_signed_up_date.weekday()])
        obj_my_meetups = models.courseMdl.MeetupCommunity.objects.filter(Q(meet_week_number=current_week), Q(
            meet_day__gte=current_day), Q(is_Active=True), Q(meet_time__gte=display_time), Q(meetup_lang=request.LANGUAGE_CODE))
        return obj_my_meetups
    else:
        student = request.user
        mycohorts = student.stuMapID.filter(
            stu_cohort_lang=request.LANGUAGE_CODE)
        lst_my_meetups = []
        local_tz = pytz.timezone(settings.TIME_ZONE)
        dt = local_tz.localize(datetime.datetime.now())
        display_dt = dt - datetime.timedelta(minutes=30)
        for mycohort in mycohorts:
            meetup = mycohort.cohort.meetups.filter(Q(is_Active=True), Q(
                step_status__starting_date__lte=dt), Q(meet_date_time__gte=display_dt))[:1]
            if (meetup.count() > 0):
                lst_my_meetups.append(meetup)
        print(lst_my_meetups)
        return lst_my_meetups


@login_required(login_url="/login/")
def activate_trial_view(request, plan_type):
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt = local_tz.localize(datetime.datetime.now())
    student = request.user
    logger.info(f"In activate_trial_view page for : {student.username}")
    try:
        plan = models.StudentsPlanMapper.plansManager.lang_code(
            request.LANGUAGE_CODE).filter(student=student)
        if (plan.count() <= 0):
            selected_plan = models.courseMdl.OurPlans.plansManager.lang_code(
                request.LANGUAGE_CODE).get(plan_name="Trial2022")
            logger.info(
                f"plan obj and current plan linked at activate_trial_view for : {student.username}")
            if request.LANGUAGE_CODE == 'en-us':
                currency = 'usd'
            elif request.LANGUAGE_CODE == 'it':
                currency = 'eur'
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            Payment.objects.create(stripe_id='', amount="0", currency=currency, status='succeeded', person=student,
                                   plan=selected_plan, coupon_code="", actual_amount="0", discount="0", custom_user_session_id=custom_user_session_id)
            logger.info(
                f"Payment table updated at activate_trial_view page for : {student.username}")
            models.StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).update_or_create(
                student=student, plan_lang=request.LANGUAGE_CODE, defaults={'plans': selected_plan})
            logger.info(
                f"Plan linked with stuPlanMapper activate_trial_view page for : {student.username}")
        plan = models.StudentsPlanMapper.plansManager.lang_code(
            request.LANGUAGE_CODE).filter(student=student)
        plan = plan.first()
        if (plan.is_trial_expired == False):
            current_plan = plan.plans.plan_name
            chk_enter_plan_type = False
            for key, val in models.CHOICE_TRIAL_PLANS:
                if (val == plan_type):
                    chk_enter_plan_type = True
            if (current_plan == "Trial2022" and plan_type == "Community_to_Premium"):
                if (chk_enter_plan_type == True):
                    context = {}
                    context = get_trial_cohorts(request, context)
                    trial_cohorts_info = context['trial_cohorts_info']
                    if (plan_type == "Community_to_Premium"):
                        for trial_cohort in trial_cohorts_info[0]:
                            models.StudentCohortMapper.objects.update_or_create(
                                student=student, cohort=trial_cohort, stu_cohort_lang=request.LANGUAGE_CODE)
                            logger.info(
                                f"In activate trial async tasks request is generated: {student.username}")
                            request.session['is_first_time_on_dashboard'] = True
                            exercise_cohort_step_tracker_creation.apply_async(
                                args=[request.user.username, request.user.pk, trial_cohort.cohort_id])
                            # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, trial_cohort.cohort_id)
                            # link_with_action_items.delay(request.user.username, request.user.pk, trial_cohort.cohort_id)
                        logger.info(
                            f"student update_or_create with StudentCohortMapper at activate_trial_view for : {student.username}")
                        # our_plan_obj = OurPlans.plansManager.lang_code(
                        #     request.LANGUAGE_CODE).get(plan_name="Premium")
                        # logger.info(f"plan obj linked at activate_trial_view page for : {student.username}")
                        # plan.plans = our_plan_obj
                    else:
                        """Community_to_Elite"""
                        for trial_cohorts in trial_cohorts_info:
                            for trial_cohort in trial_cohorts:
                                models.StudentCohortMapper.objects.update_or_create(
                                    student=student, cohort=trial_cohort, stu_cohort_lang=request.LANGUAGE_CODE)
                                logger.info(
                                    f"In activate trial async tasks request is generated: {student.username}")
                                request.session['is_first_time_on_dashboard'] = True
                                exercise_cohort_step_tracker_creation.apply_async(
                                    args=[request.user.username, request.user.pk, trial_cohort.cohort_id])
                                # exercise_cohort_step_tracker_creation.delay(request.user.username, request.user.pk, trial_cohort.cohort_id)
                                # link_with_action_items.delay(request.user.username, request.user.pk, trial_cohort.cohort_id)
                        logger.info(
                            f"student update_or_create with StudentCohortMapper at activate_trial_view for : {student.username}")
                        # our_plan_obj = OurPlans.plansManager.lang_code(
                        #     request.LANGUAGE_CODE).get(plan_name="Elite")
                        # logger.info(f"plan obj linked at activate_trial_view page for : {student.username}")
                        # plan.plans = our_plan_obj
                    plan.is_trial_active = True
                    plan.trial_type = plan_type
                    plan.trail_days = plan.plans.trial_days
                    plan.trial_start_date = dt
                    plan.trial_end_date = dt + \
                        datetime.timedelta(days=plan.plans.trial_days)
                    plan.save()
                    user_name = request.user.username
                    logger.info(f"trail-plan-activated by : {user_name}")
                    try:
                        # hubspotContactupdateQueryAdded
                        logger.info(
                            f"In hubspot plan student trail activated parameter building for : {request.user.username}")
                        keys_list = ["email", "hubspot_free_trail_activated",
                                     "hubspot_end_free_trail", "hubspot_free_trail_expired", "Hubspot_free_trial_start_date", "end_free_trial_date"]
                        Hubspot_free_trial_start_date = unixdateformat(
                            plan.created_at)
                        end_free_trial_date = unixdateformat(
                            plan.trial_end_date)
                        values_list = [request.user.username, str(plan.is_trial_active), str(
                            plan.trial_end_date), str(plan.is_trial_expired), Hubspot_free_trial_start_date, end_free_trial_date]
                        create_update_contact_hubspot(
                            request.user.username, keys_list, values_list)
                        logger.info(
                            f"In hubspot plan student trail activated parameter update completed for : {request.user.username}")
                    except Exception as ex:
                        logger.error(
                            f"Error at hubspot plan student trail activated parameter update {ex} for : {request.user.username}")
        user_name = request.user.username
        logger.info(f"trail-plan-activate page visited by : {user_name}")
    except Exception as ex:
        user_name = request.user.username
        logger.critical(f"Error to activate trail plan {ex} for : {user_name}")
        print(ex)
    return HttpResponseRedirect(reverse("home"))


def deactivate_trial_plan(request, context):
    student = request.user
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt = local_tz.localize(datetime.datetime.now())
    try:
        plan = models.StudentsPlanMapper.plansManager.lang_code(
            request.LANGUAGE_CODE).get(student=student)
        if (plan.is_trial_active):
            if (dt >= plan.trial_end_date):
                # our_plan_obj = OurPlans.plansManager.lang_code(
                #     request.LANGUAGE_CODE).get(plan_name="Community")
                # plan.plans = our_plan_obj
                plan.is_trial_active = False
                plan.is_trial_expired = True
                plan.save()
                context['is_trial_active'] = plan.is_trial_active
                context['is_trial_expired'] = plan.is_trial_expired
                logger.info(
                    f"trial plan expired at deactivate_trial_plan for : {student.username}")
                try:
                    # hubspotContactupdateQueryAdded
                    logger.info(
                        f"In hubspot plan trail deactivate parameter building for : {request.user.username}")
                    keys_list = [
                        "email", "hubspot_free_trail_activated", "hubspot_free_trail_expired"]
                    values_list = [request.user.username, str(
                        plan.is_trial_active), str(plan.is_trial_expired)]
                    create_update_contact_hubspot(
                        request.user.username, keys_list, values_list)
                    logger.info(
                        f"In hubspot plan trail deactivate parameter update completed for : {request.user.username}")
                except Exception as ex:
                    logger.error(
                        f"Error at hubspot plan trail deactivate parameter update {ex} for : {request.user.username}")
        # current_plan = plan.plans.plan_name
        return plan
    except Exception as ex:
        print(ex)
        user_name = request.user.username
        logger.error(
            f"Error to deactivate trail plan function {ex} : {user_name}")
        return None


def check_status_of_scholarship_test(student, lang_code):
    obj = models.StudentScholarshipTestMapper.objects.filter(
        student=student, lang_code=lang_code).first()
    if obj is not None:
        sts = obj.is_applied
    else:
        sts = False
    return sts


def get_step_and_ai(request):
    latest_step_track_id = 0
    person = request.user
    student_cohorts = person.stuMapID.filter(
        stu_cohort_lang=request.LANGUAGE_CODE).order_by('cohort__module__module_priority')
    next_date = None
    break_outer_loop = False
    stu_action_item_no = None

    for stu_cohort in student_cohorts:
        stu_steps = stu_cohort.stu_cohort_map.all()
        break_inner_loop = False
        for step in stu_steps:
            if step.step_status_id.is_active == False:
                next_date = step.step_status_id.starting_date
                break_outer_loop = True
                break
            elif (step.step_status_id.is_active == True and step.is_completed == False):
                latest_step_track_id = step.step_track_id
                break_outer_loop = True
                stu_action_items = step.stu_action_items.filter(
                    ActionItem__is_deleted=False).order_by("ActionItem__action_sno")
                for stu_action_item in stu_action_items:
                    if stu_action_item.is_completed == False:
                        stu_action_item_no = stu_action_item.ActionItem.action_sno
                        break_inner_loop = True
                        break
                if break_inner_loop:
                    break
        if break_outer_loop:
            break
    return latest_step_track_id, stu_action_item_no, next_date


@login_required(login_url="/login/")
def index_view(request):
    student = request.user
    logger.info(f"In index_view page for : {student.username}")
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to counselor-dashboard from index_view page : {student.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to counselor-dashboard from index_view page : {student.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.clarity_token is None:
        request.user.clarity_token = request.session.get('clarity_token', '')
        request.user.save()
    else:
        request.session['clarity_token'] = request.user.clarity_token
    context = {}
    context, current_plan_1 = get_all_plans(request)
    if (current_plan_1 is None):
        logger.info(
            f"Redirected to index_view from futurely_plan page : {student.username}")
        return HttpResponseRedirect(reverse('futurely-plans'))
    deactivate_trial_plan(request, context)
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt = local_tz.localize(datetime.datetime.now())
    now = dt.date()
    stu = request.user
    student_plan = models.StudentsPlanMapper.plansManager.lang_code(request.LANGUAGE_CODE).filter(student=stu).first()
    print(student_plan)
    current_plan = student_plan.plans.plan_name
    current_plan_name = request.session.get('current_plan_name', None)  
    if current_plan_name is None:
        request.session['current_plan_name'] = current_plan
    if (request.method == "POST"):
        try:
            cohort_id = request.POST.get('cohort_id')
            # student_cohort_link = student_link_with_cohort(stu, cohort_id, request.LANGUAGE_CODE)
            cohort = models.courseMdl.Cohort.cohortManager.lang_code(
                request.LANGUAGE_CODE).get(cohort_id=cohort_id)
            stu_cohort_map = models.StudentCohortMapper.objects.filter(
                student=stu, cohort__module__module_id=cohort.module.module_id, stu_cohort_lang=request.LANGUAGE_CODE)
            if (stu_cohort_map.count() > 0):
                cohort_steps = cohort.cohort_step_status.all()
                stu_cohort_map = stu_cohort_map.first()
                old_all_steps = stu_cohort_map.stu_cohort_map.all()
                for i, step in enumerate(old_all_steps):
                    if (step.step_status_id.step.step_id == cohort_steps[i].step.step_id):
                        print(step.step_status_id)
                        step.step_status_id = cohort_steps[i]
                        print(step.step_status_id)
                        step.save()
                stu_cohort_map.cohort = cohort
                stu_cohort_map.save()
                user_name = request.user.username
                logger.info(
                    f"Course cohort is linked with student: {user_name}")
            else:
                models.StudentCohortMapper.objects.update_or_create(
                    student=stu, cohort=cohort, stu_cohort_lang=request.LANGUAGE_CODE)
            messages.success(request, _(
                "You’re in! Now the journey begins and you can start your first course"))
            try:
                # hubspotContactupdateQueryAdded
                logger.info(
                    f"In hubspot cohort name parameter building for : {request.user.username}")
                if cohort.module.module_id == 1 or cohort.module.module_id == 3:
                    keys_list = ["email", "hubspot_cohort_name_premium"]
                    values_list = [request.user.username, cohort.cohort_name]
                    Hubspot_cohort_premium_start_date = unixdateformat(
                        cohort.starting_date)
                    keys_list.append('Hubspot_cohort_premium_start_date')
                    values_list.append(Hubspot_cohort_premium_start_date)
                    create_update_contact_hubspot(
                        request.user.username, keys_list, values_list)
                if cohort.module.module_id == 2 or cohort.module.module_id == 4:
                    keys_list = ["email", "hubspot_cohort_name_elite1"]
                    values_list = [request.user.username, cohort.cohort_name]
                    Hubspot_cohort_elite1_start_date = unixdateformat(
                        cohort.starting_date)
                    keys_list.append('Hubspot_cohort_elite1_start_date')
                    values_list.append(Hubspot_cohort_elite1_start_date)
                    create_update_contact_hubspot(
                        request.user.username, keys_list, values_list)
                if cohort.module.module_id == 5:
                    keys_list = ["email", "hubspot_cohort_name_elite2"]
                    values_list = [request.user.username, cohort.cohort_name]
                    Hubspot_cohort_elite2_start_date = unixdateformat(
                        cohort.starting_date)
                    keys_list.append('Hubspot_cohort_elite2_start_date')
                    values_list.append(Hubspot_cohort_elite2_start_date)
                    create_update_contact_hubspot(
                        request.user.username, keys_list, values_list)
                logger.info(
                    f"In hubspot cohort name parameter update completed for : {request.user.username}")
            except Exception as ex:
                logger.error(
                    f"Error at hubspot cohort name parameter update {ex} for : {request.user.username}")
        except Exception as exp:
            print(exp)
            user_name = request.user.username
            logger.critical(f"Error to link cohort with student: {user_name}")
    request.session['course_dependency'] = stu.student.skip_course_dependency
    is_from_middle_school = request.user.student.is_from_middle_school
    is_from_fast_track_program = request.user.student.is_from_fast_track_program
    context = all_courses(
        request, context, is_from_middle_school, is_from_fast_track_program)
    current_plan_type = context['current_plan_type']
    is_trial_expired = context['is_trial_expired']
    is_trial_active = context['is_trial_active']
    context['my_meetups'] = my_meetups(request, current_plan_type)
    my_blog_videos = MyBlogVideos.published.lang_code(
        request.LANGUAGE_CODE).all()
    welcome_video = WelcomeVideo.objects.filter(
        module_lang=request.LANGUAGE_CODE, is_published=True).first()
    template_name = "student/index-trial.html"

    if current_plan_type == "Trial2022":
        if is_trial_active:
            template_name = "student/index-trial.html"
        elif is_trial_expired:
            all_plans = context['all_plans']
            entered_coupon_code = request.user.student.discount_coupon_code
            coupon_details = Coupon.active_objects.filter(
                code__iexact=entered_coupon_code).first()
            # if coupon_details is None:
            #     student_tmp = getattr(request.user, 'student', None)
            #     if student_tmp:
            #         student_tmp.discount_coupon_code = "forever10"
            #         student_tmp.save()
            #     entered_coupon_code = "forever10"
            #     coupon_details = Coupon.active_objects.filter(code__iexact=entered_coupon_code).first()
            request.session["coupon_code_after_trial"] = entered_coupon_code
            e_plan = all_plans.filter(plan_name="Elite").first()
            context['elite_plan'] = e_plan
            context['coupon_details'] = coupon_details

            template_name = "student/index-trial-expired.html"

    latest_step_track_id, stu_action_item_no, next_date = get_step_and_ai(
        request)
    context['step_track_id'] = latest_step_track_id
    context['action_item'] = stu_action_item_no
    context['next_date'] = next_date
    context['msg_continue_cta'] = _(
        "Congratulations, you have completed all the available steps! The next step will unlock on ")
    webinars = None
    if current_plan_type == "Community" or current_plan_type == "Trial2022":
        webinars = Webinars.published.lang_code(request.LANGUAGE_CODE).filter(
            datetime_to_mark_attendance__gte=dt, webinar_accessibility__plan_name__in=["Community"]).distinct()
    elif current_plan_type == "Premium":
        webinars = Webinars.published.lang_code(request.LANGUAGE_CODE).filter(
            datetime_to_mark_attendance__gte=dt, webinar_accessibility__plan_name__in=["Premium"]).distinct()
    elif current_plan_type == "Elite":
        webinars = Webinars.published.lang_code(request.LANGUAGE_CODE).filter(
            Q(datetime_to_mark_attendance__gte=dt, webinar_accessibility__plan_name__in=["Elite"])).distinct()
    # context['blogs'] = blogs
    context['is_applied_for_scholarship'] = check_status_of_scholarship_test(
        student, request.LANGUAGE_CODE)
    context['webinars'] = webinars
    context['webinar_time'] = dt
    context['dashboard_announcements'] = dashboard_announcement(request.user)
    kpis = calculate_kpis(request)
    # update_endurance_score.apply_async(args=[request.user.username, request.user.pk, request.LANGUAGE_CODE])
    context['kpis'] = kpis
    context['current_date'] = now
    context['dates'] = date_list(now)
    context['my_groups'] = my_groups(request)
    context['my_resources'] = my_resources(request)
    context['my_blog_videos'] = my_blog_videos
    if welcome_video:
        context['welcome_video_link'] = welcome_video.video_link
    else:
        context['welcome_video_link'] = None
    lst_todos, lst_steps = get_todo(request, now)
    context['lst_todos'] = lst_todos
    context['lst_steps'] = lst_steps
    student = getattr(stu, 'student', None)
    if student and student.src == 'future_lab':
        context['future_lab_form_filled'] = student.future_lab_form_status
    # context['all_notifications']= notification_view(request.user)
    if request.session.get('cohort_ids', None):
        del request.session['cohort_ids']
    if request.session.get('coupon_code', None):
        del request.session['coupon_code']
    if request.session.get('pay_confirmed_bit', None):
        del request.session['pay_confirmed_bit']
    user_name = request.user.username

    if is_from_middle_school:
        template_name = "student/index-middle-school.html"
    if is_from_fast_track_program:
        context['videos_objs'] = MyBlogVideos.objects.filter(is_for_fast_track=True).all()
        template_name = "student/fast-track-dashboard.html"
    logger.info(f"Dashboard page visited by : {user_name}")
    return render(request, template_name, context)


@login_required(login_url="/login/")
def play_welcome_video(request):
    logger.info(f"In play_welcome video called by : {request.user.username}")
    if (request.is_ajax):
        student = getattr(request.user, 'student', None)
        if student:
            student.is_welcome_video_played = True
            student.save()
            logger.info(
                f"In play_welcome video , video is played by : {request.user.username}")
    return JsonResponse({'msg': _('Welcome video watched')}, status=200)


@login_required(login_url="/login/")
def step1_pdf_downloaded(request):
    logger.info(f"In Step1 pdf download called by : {request.user.username}")
    if (request.is_ajax):
        student = getattr(request.user, 'student', None)
        if student:
            student.is_step1_pdf_downloaded = True
            student.save()
            logger.info(
                f"In step1 pdf download , downloaded by : {request.user.username}")
    return JsonResponse({'msg': _('Step1 pdf downloaded')}, status=200)


@login_required(login_url="/login/")
def add_todo_view(request):
    try:
        student = request.user
        logger.info(f"In add_todo_view called by : {student.username}")
        if (request.is_ajax and request.method == "POST"):
            title = request.POST.get('title')
            # desc = request.POST.get('desc')
            todo_date = request.POST.get('todo_date')
            todo_date = datetime.datetime.strptime(todo_date, '%Y-%m-%d')
            todo_obj = models.Todos(
                student=request.user, title=title, dated=todo_date)
            todo_obj.save()
            # local_tz = pytz.timezone(settings.TIME_ZONE)
            # dt = local_tz.localize(datetime.datetime.now())
            # now=dt.date()
            # lst_todos=get_todo(request,now)
            todo_title = html.escape(todo_obj.title)
            logger.info(
                f"Todo added at add_todo_view page for : {student.username}")
            return JsonResponse({'msg': _('Todo added'), 'todo_title': todo_title}, status=200)
        return JsonResponse({'msg': _('Something went wrong')}, status=400)
    except Exception as ex:
        print(ex)
        user_name = request.user.username
        logger.error(f"Error in add_todo {ex} for : {user_name}")
        return JsonResponse({'msg': _('Something went wrong')}, status=400)


@login_required(login_url="/login/")
def update_todo_view(request):
    try:
        student = request.user
        logger.info(f"In update_todo_view called by : {student.username}")
        if (request.is_ajax and request.method == "POST"):
            id = request.POST.get('id')
            msg = request.POST.get('msg')
            todo_obj = models.Todos.objects.get(id=id)
            todo_obj.title = msg
            todo_obj.save()
            todo_title = html.escape(todo_obj.title)
            user_name = request.user.username
            logger.info(f"Todo updated at update_todo_view for : {user_name}")
            return JsonResponse({'msg': _('Todo updated'), 'todo_title': todo_title}, status=200)
    except Exception as ex:
        print(ex)
        user_name = request.user.username
        logger.error(f"Error to update todo {ex} : {user_name}")
        return JsonResponse({'msg': _('Something went wrong')}, status=400)


@login_required(login_url="/login/")
def delete_todo_view(request):
    try:
        student = request.user
        logger.info(f"In delete todo view called by : {student.username}")
        if (request.is_ajax and request.method == "POST"):
            id = request.POST.get('id')
            todo_obj = models.Todos.objects.get(id=id)
            todo_obj.is_deleted = True
            todo_obj.save()
            todo_title = html.escape(todo_obj.title)
            user_name = request.user.username
            logger.info(f"Todo deleted : {user_name}")
            return JsonResponse({'msg': _('Todo deleted'), 'todo_title': todo_title}, status=200)
    except Exception as ex:
        print(ex)
        user_name = request.user.username
        logger.error(f"Error to delete todo {ex} : {user_name}")
        return JsonResponse({'msg':  _('Something went wrong')}, status=400)


@login_required(login_url="/login/")
def get_todo_view(request):
    try:
        student = request.user
        logger.info(f"In get_todo_view called by : {student.username}")
        if (request.is_ajax and request.method == "GET"):
            date = request.GET.get('date')
            todo_date = datetime.datetime.strptime(date, '%d-%m-%Y')
            todo_date = todo_date.date()
            lst_todos, lst_steps = get_todo(request, todo_date)
            user_name = request.user.username
            logger.info(f"Todo fetched at get_todo_view for : {user_name}")
            return JsonResponse({'lst_todos': lst_todos, 'lst_steps': lst_steps, 'msg': 'Ok'}, status=200)
    except Exception as ex:
        print(ex)
        print("Error")
        user_name = request.user.username
        logger.error(f"Error to get todo {ex} : {user_name}")
        return JsonResponse({'msg':  _('Something went wrong')}, status=400)


def create_hubspot_tickets(user, email, subject, question):
    try:
        logger.info(
            f"In create_hubspot_tickets function to create hubspot ticket for user - {email} and user {user}")
        ticket_owner = userauth_models.HubspotCredential.objects.filter(title='hubspot_ticket_owner').first()
        if ticket_owner:
            properties = {
                "hs_pipeline": "0",
                "hs_pipeline_stage": "1",
                "hs_ticket_priority": "HIGH",
                "hubspot_owner_id": ticket_owner.value, #"211640643",
                "subject": subject,
                "content": question,
                "email": email
            }
            data = json.dumps(properties)
            response = settings.CLIENT.publish(
                TopicArn='arn:aws:sns:eu-south-1:994790766462:sns_create_hubspot_ticket',
                Message=data
            )
            logger.info(
                f"In create hubspot ticket - SNS is published - for user - {email} and user {user}")
        else:
            logger.error(f"ticket_owner object is None for : {email} and user is {user}")
    except Exception as ex:
        logger.error(
            f"Error to submit the ticket : {email} and user {user}: and exception is: {ex}")


@login_required(login_url="/login/")
def contact_tutor_view(request):
    try:
        if request.is_ajax and request.method == "POST":
            logger.info(
                f"In contact_tutor_view called by : {request.user.username}")
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            questions = request.POST.get('questions')
            person = request.user
            if subject == "" or questions == "":
                return JsonResponse({'msg': _('Please fill out the subject and fields')}, status=400)
            models.Query.objects.create(
                person=person, message=questions, status="Open")
            fromEmail = settings.EMAIL_HOST_USER
            # toEmail = "no-reply@myfuturely.com"
            if (request.LANGUAGE_CODE == "it"):
                toEmail = "segreteria@myfuturely.com"
            else:
                toEmail = "counselors@myfuturely.com"
            msg = f"Student Email id is : {email} \nStudent Queries are : {questions} ."
            try:
                user_name = request.user.username
                # call celery to create tickets
                create_hubspot_tickets(user_name, email, subject, questions)
                # send_mail(subject, msg, fromEmail, [toEmail])
                create_custom_event(request, event_id=16, meta_data={
                                    'email': email, 'subject': subject, 'msg': msg})
                logger.info(
                    f"Query to tutor is succesfully submitted by: {user_name}")
                return JsonResponse({'msg': 'Queries  successfully'}, status=200)
            except Exception as exp:
                create_custom_event(request, event_id=17, meta_data={
                                    'email': email, 'subject': subject, 'msg': msg})
                user_name = request.user.username
                logger.error(
                    f"Error to submit the query - {exp} : {user_name}")
                return JsonResponse({'msg': _('We are unable to contact the tutor. Please try again later')}, status=400)
    except Exception as ex:
        print(ex)
        user_name = request.user.username
        logger.error(f"Error to submit the query : {user_name}")
        return JsonResponse({'msg': _('We are unable to contact the tutor. Please try again later')}, status=400)


@login_required(login_url="/login/")
def notification_update(request):
    try:
        student = request.user
        logger.info(f"In notification_update called by : {student.username}")
        notification_type = None
        if (request.is_ajax and request.method == "POST"):
            id = request.POST.get('id')
            notification = models.Stu_Notification.objects.get(
                id=id, student=request.user)
            notification.isread = True
            notification.save()
            if notification.type:
                notification_type = notification.type
            # print(notification.title)
            logger.info(
                f"notification updated at notification_update view page for : {student.username}")
        return JsonResponse({'msg': '','notification_type':notification_type}, status=200)
    except Exception as ex:
        logger.error(
            f"Error to notification update view {ex} : {request.user.username}")
        return JsonResponse({'error': ''}, status=400)


@login_required(login_url="/login/")
def account_settings_view(request):
    current_user = request.user
    logger.info(
        f"In account_settings_view page called by : {current_user.username}")
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to account_settings_view from couselor-dashboard page for : {current_user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to account_settings_view from couselor-dashboard page for : {current_user.username}")
        return HttpResponseRedirect(reverse("admin_dashboard"))
    context = {}
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
            context['success_message'] = _("Changes updated successfully")
            logger.info(
                f"Account setting updated at account_setting_view page for : {current_user.username}")
        context['first_name'] = current_user.first_name
        context['last_name'] = current_user.last_name
        context['email'] = current_user.email
        context['current_user'] = current_user
        logger.info(
            f"account_settings_view page visited by : {current_user.username}")
        return render(request, "student/account-settings.html", context)
    except Exception as err:
        logger.critical(
            f"Error to account setting {err} for : {current_user.username}")
    return HttpResponseRedirect(reverse("home"))


@login_required(login_url="/login/")
def account_notification_settings_view(request):
    try:
        context = {}
        current_user = request.user
        logger.info(
            f"In account_notification_settings_view page called by : {current_user.username}")
        if request.user.person_role == "Counselor":
            logger.info(
                f"Redirected to counselor-dashboard from account_notification_settings_view for : {current_user.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if request.user.person_role == "Futurely_admin":
            logger.info(
                f"Redirected to counselor-dashboard from account_notification_settings_view for : {current_user.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        context['notification_types'] = Notification_type.objects.filter(
            ~Q(notification_type='Announcements'))
        context['person_notifications_for_current_user'] = models.PersonNotification.objects.filter(
            person=current_user)
        if request.method == "POST":
            request_post = request.POST
            notification_type_id = request_post.get(
                'notification_type_id', None)
            is_checked = request_post.get('is_checked', None)
            if notification_type_id and is_checked:
                if is_checked == 'true':
                    notification_type_obj = Notification_type.objects.get(
                        pk=notification_type_id)
                    models.PersonNotification.objects.update_or_create(
                        person=current_user, notification_type=notification_type_obj)
                elif is_checked == 'false':
                    notification_type_obj = Notification_type.objects.get(
                        pk=notification_type_id)
                    models.PersonNotification.objects.filter(
                        person=current_user, notification_type=notification_type_obj).delete()
                logger.info(
                    f" Notification settings updated at account_notification_settings_view page for : {current_user.username}")
                return JsonResponse({'message': 'success'}, safe=False)
            logger.warning(
                f"Notification settings didn't updated at account_notification_settings_view page for : {current_user.username}")
            return JsonResponse({'message': 'failure'}, safe=False)
        return render(request, "student/account-notification-settings.html", context)
    except Exception as err:
        user_name = request.user.username
        logger.critical(
            f"Error to account notification settings view {err} for : {user_name}")
    return JsonResponse({'message': 'failure'}, safe=False)


@login_required(login_url="/login/")
def account_settings_changePass_view(request):
    context = {}
    current_user = request.user
    logger.info(
        f"In account_settings_changePass_view page called by : {current_user.username}")
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to counselor-dashboard from account_settings_changePass_view page for : {current_user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to counselor dashboard from account_settings_changePass_view page for : {current_user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    try:
        if request.method == "POST":
            request_post = request.POST
            current_password = request_post.get('cpassword', None)
            new_password = request_post.get('npassword', None)
            # email = request_post.get('email', None)
            if current_user.check_password(current_password):
                if current_password and new_password and current_password != new_password:
                    current_user.set_password(new_password)
                    context['message'] = _("Changes updated successfully")
                    logger.info(
                        f"Password changed successfully at account_settings_changePass_view page for : {current_user.username}")
                else:
                    context['message'] = _(
                        "New Password must be different from Current Password")
                    context['error'] = True
                    logger.error(
                        f"New Password must be different from Current Password : {current_user.username}")
                # if email:
                #     current_user.email = email
                current_user.save()
                login(request, current_user)
            else:
                context['message'] = _(
                        "La password attuale è sbagliata! Inserisci la password corretta.")
                context['error'] = True
                logger.warning(
                    f"Current password is wrong for current user : {current_user.username}")
        context['email'] = current_user.email
        return render(request, "student/account-change-password.html", context)
    except Exception as error:
        logger.critical(
            f"Error to account settings changePass page {error} for : {current_user.username}")
    return HttpResponseRedirect(reverse('home'))


@login_required(login_url="/counselor-login/")
def account_settings_changePass_view_counselor(request):
    context = {}
    current_user = request.user
    logger.info(
        f"In account_settings_changePass_view_counselor called by : {current_user.username}")
    if request.user.person_role == "Student":
        logger.info(
            f"Redirected to account_settings_changePass_view_counselor page at home for : {current_user.username}")
        return HttpResponseRedirect(reverse("home"))
    try:
        if request.method == "POST":
            request_post = request.POST
            current_password = request_post.get('cpassword', None)
            new_password = request_post.get('npassword', None)
            # email = request_post.get('email', None)
            if current_password and new_password and current_password != new_password:
                current_user.set_password(new_password)
                context['message'] = _("Changes updated successfully")
                logger.info(
                    f"Change password updated successfully at account_settings_changePass_view_counselor for : {current_user.username}")
            else:
                context['message'] = _(
                    "New Password must be different from Current Password")
                context['error'] = True
                logger.warning(
                    f"New Password must be different from Current Password : {current_user.username}")
            # if email:
            #     current_user.email = email
            current_user.save()
            login(request, current_user)
        context['email'] = current_user.email
        logger.info(
            f"account_settings_changePass_view_couselor page visited by : {current_user.username}")
        return render(request, "student/account-change-password-counselor.html", context)
    except Exception as err:
        logger.critical(
            f"Error to account settings changePass for counselor {err} : {current_user.username}")
    return HttpResponseRedirect(reverse("home"))


@login_required(login_url="/login/")
def post_detail(request, year, month, day, post):
    student = request.user
    try:
        logger.info(f"In post_details called by : {student.username}")
        blog = get_object_or_404(Blog_post, slug=post, status='published',
                                 publish_date__year=year, publish_date__month=month, publish_date__day=day)
        return render(request, 'student/blog-details.html', {'blog': blog})
    except Exception as err:
        logger.critical(
            f"Error in post details {err} for : {student.username}")


def all_courses(request, context, is_from_middle_school=False, is_from_fast_track_program=False):
    context['avail_courses'] = None
    try:
        current_plan_type = context['current_plan_type']
        is_trial_expired = context['is_trial_expired']
        is_trial_active = context['is_trial_active']
        plan = context['plan']
        current_plan = plan.first().plans
        stu_id = request.user.id
        student = request.user.student

        if (is_trial_active):
            mycourses = models.StudentCohortMapper.stuCohortManager.lang_code(
                request.LANGUAGE_CODE).filter(student=stu_id, cohort__cohort_type="Trial")
        else:
            mycourses = models.StudentCohortMapper.stuCohortManager.lang_code(
                request.LANGUAGE_CODE).filter(student=stu_id, cohort__cohort_type="Paid")
        courses_to_exclude = []
        module_to_exclude = []
        if (mycourses):
            tot_steps = 0
            course_tot_steps = []
            for mycourse in mycourses:
                all_steps = mycourse.stu_cohort_map.all()
                tot_steps = all_steps.count()
                print(tot_steps)
                course_tot_steps.append(tot_steps)
                is_first_time_on_dashboard = request.session.get(
                    'is_first_time_on_dashboard', False)
                if not is_first_time_on_dashboard:
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

                # tot_steps = tot_steps+course_steps
                # print(mycourse.cohort.cohort_step_status.all().count())
                # courses_to_exclude.append(mycourse.cohort.cohort_id)
                # module_to_exclude.append(mycourse.cohort.module.module_id)
            # print(module_to_exclude)
            # if(tot_steps == 0):
            #     is_course_started = False
            # else:
            #     is_course_started = True
            # context['is_course_started'] = is_course_started
            context['course_tot_steps'] = course_tot_steps
            if (is_trial_active):
                mycourses = models.StudentCohortMapper.stuCohortManager.lang_code(
                    request.LANGUAGE_CODE).filter(student=stu_id, cohort__cohort_type="Trial")
            else:
                mycourses = models.StudentCohortMapper.stuCohortManager.lang_code(
                    request.LANGUAGE_CODE).filter(student=stu_id, cohort__cohort_type="Paid")
            context['mycourses'] = mycourses

        avail_courses = models.courseMdl.Modules.moduleManager.lang_code(
            request.LANGUAGE_CODE).filter(is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track_program, course__plan__in=[current_plan]).distinct().order_by('module_priority')
            # request.LANGUAGE_CODE).filter(is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track_program).order_by('module_priority')
        print("avail_courses ------ ", avail_courses)
        active_courses = 0
        request.session['is_first_time_on_dashboard'] = False
        if (avail_courses):
            module_cohorts_info = []
            trial_cohorts_info = []
            for course in avail_courses:
                dt = datetime.date.today()
                monday = dt-datetime.timedelta(days=dt.weekday())
                if (course.is_active):
                    active_courses = active_courses + 1
                # module_cohorts_info.append(models.courseMdl.Cohort.objects.filter(module=course.module_id, starting_date__gte=monday, is_active="Yes")[:3])
                module_cohorts_info.append(models.courseMdl.Cohort.objects.filter(
                    module=course.module_id, starting_date__gte=dt, is_active="Yes", cohort_type="Paid", is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track_program)[:3])
                trial_cohorts_info.append(models.courseMdl.Cohort.objects.filter(
                    module=course.module_id, is_active="Yes", cohort_type="Trial", is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track_program)[:1])
                # module_cohorts_info.append(models.courseMdl.Cohort.objects.filter(module=course.module_id)[:3])
            context['avail_courses'] = avail_courses
            context['module_cohorts_info'] = module_cohorts_info
            context['active_courses'] = active_courses
            context['trial_cohorts_info'] = trial_cohorts_info
            print(f"Module info : {module_cohorts_info}")
            print(f"Trial Cohort info : {trial_cohorts_info}")
        user_name = request.user.username
        logger.info(f"All courses module executed successfully : {user_name}")
    except Exception as ex:
        print(ex)
        user_name = request.user.username
        logger.error(f"Error to get all courses {ex} : {user_name}")
    return context


@login_required(login_url="/login/")
def course_available(request):
    context = {}
    stu = request.user
    logger.info(f"In course_available page called by : {stu.username}")
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to couselor-dashboard from course_available page for : {stu.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to couselor-dashboard from course_available page for : {stu.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    # cohort_id = request.GET.get('cohort_id', None)
    try:
        if request.user.student.is_from_middle_school or request.user.student.is_from_fast_track_program:
            logger.info(
                f"Student redirect to middle school dashbord from course_available for : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))

        deactivate_trial_plan(request, context)
        if (request.method == "POST"):
            cohort_id = request.POST.get('cohort_id')
            cohort = models.courseMdl.Cohort.cohortManager.lang_code(
                request.LANGUAGE_CODE).get(cohort_id=cohort_id)
            logger.info(
                f"cohort obj linked at course_available for : {stu.username}")
            # print(cohort)
            models.StudentCohortMapper.objects.update_or_create(
                student=stu, cohort=cohort, stu_cohort_lang=request.LANGUAGE_CODE)
            messages.success(request, _(
                "You’re in! Now the journey begins and you can start your first course"))
        context, current_plan = get_all_plans(request)
        if (current_plan is None):
            logger.info(
                f"Redirected to futurely-plans from course_available for : {stu.username}")
            return HttpResponseRedirect(reverse('futurely-plans'))
        request.session['course_dependency'] = stu.student.skip_course_dependency
        context = all_courses(request, context)
        logger.info(f"course_available page visited by : {stu.username}")
        return render(request, "student/courses-avail.html", context)
    except Exception as err:
        logger.error(f"Error in course_available {err} for : {stu.username}")
        return HttpResponseRedirect(reverse("home"))


@login_required(login_url="/login/")
def course_cohort_map(request, cohort_id):

    return render(request, "student/courses-avail.html")


def check_priority(request, cohort):
    student = request.user
    logger.info(f"In check_priority function called by : {student.username}")
    status = False
    try:
        # current_module=models.courseMdl.Modules.moduleManager.lang_code(request.LANGUAGE_CODE).get(module_id=module)
        current_priority = cohort.module.module_priority
        previous_mdls = None
        if (current_priority == 1):
            status = True
        else:
            try:
                previous_mdls = models.courseMdl.Modules.moduleManager.lang_code(
                    request.LANGUAGE_CODE).get(module_priority=current_priority-1)
                logger.info(
                    f"fetched course at check_priority for : {student.username}")
                my_courses = request.user.stuMapID.all()
                if (my_courses.count() > 0):
                    for course in my_courses:
                        if (course.cohort.module.module_id == previous_mdls.module_id):
                            status = True
                else:
                    status = False
            except Exception as ex:
                print(ex)
                logger.error(
                    f"Error in check priority {ex} for : {student.username}")
    except Exception as e:
        print(e)
        # return to 404
        logger.error(
            f"Error in check priority {e} for : {request.user.username}")
    return status, previous_mdls


@login_required(login_url="/login/")
def course_overview(request, module):
    context = {}
    try:
        stu_id = request.user.id
        context['mycourses'] = None
        if (request.method == "POST"):
            cohort_id = request.POST.get("cohort_id")
            if (cohort_id == ''):
                context['message'] = "Please select any starting date"
            else:
                try:
                    cohort = models.courseMdl.Cohort.objects.get(
                        cohort_id=cohort_id)
                    chk_course = models.StudentCohortMapper.objects.filter(
                        student=request.user, cohort=cohort)
                    if (chk_course.count() == 0):
                        status, previous_mdls = check_priority(request, cohort)
                        if (status == True):
                            # discount = 0
                            request.session['cohort_ids'] = list(cohort_id)
                            # request.session['discount'] = discount
                            # return redirect('payment')
                            logger.info(
                                f"Redirected to order-summary from course overview : {request.user.username}")
                            return redirect('order-summary')
                        else:
                            context['buy_message'] = "Please purchase course 1 to unlock this course."
                            context['previous_mdls'] = previous_mdls.module_id
                    else:
                        context['message'] = "Course is already Purchased."
                except Exception as ex:
                    print(ex)
                    logger.error(
                        f"Error Exception in course overview {ex}: {request.user.username}")
                    context['message'] = "Error in purchasing the course. Please try again sometime."
        mycourses = models.StudentCohortMapper.objects.filter(student=stu_id)
        if (mycourses):
            context['mycourses'] = mycourses
        courses_to_exclude = []
        for mycourse in mycourses:
            courses_to_exclude.append(mycourse.cohort.cohort_id)
        courses_mdl_view = models.courseMdl.Modules.moduleManager.lang_code(
            request.LANGUAGE_CODE).get(module_id=module)
        dt = datetime.date.today()
        detail_from_cohort = models.courseMdl.Cohort.objects.filter(
            module=module, starting_date__gte=dt, is_for_middle_school=False, is_for_fast_track_program=False).exclude(cohort_id__in=courses_to_exclude)[:3]
        context['courses_view'] = courses_mdl_view
        context['detail_from_cohort'] = detail_from_cohort
        context['courses_view_steps'] = courses_mdl_view.steps.exclude(
            is_backup_step=True).all()
    except Exception as ex:
        print(ex)
        logger.error(f"Error in course overview {ex}: {request.user.username}")
        # need to redirect at 404 page

    return render(request, "student/courses-overview.html", context)


@login_required(login_url="/login/")
def buy_multiple_modules(request):
    # discount = 10
    if (request.method == "POST"):
        lst = request.POST.getlist('cohort_ids')
        request.session['cohort_ids'] = lst
        # request.session['discount'] = discount
        # return redirect('payment')
        user_name = request.user.username
        logger.info(
            f"Redirected to order summary from buy-multiple: {user_name}")
        return redirect('order-summary')
    context = all_courses(request)
    avail_courses = context['avail_courses']
    local_tz = pytz.timezone(settings.TIME_ZONE)
    dt = local_tz.localize(datetime.datetime.now())
    start_date = dt.date()
    cohort_lst = []
    if (avail_courses):
        for avail in avail_courses:
            cohort_lst.append(avail.cohort_module.all().filter(
                starting_date__gte=start_date)[:3])
        context['cohort_lst'] = cohort_lst
    # context["discount"] = discount
    return render(request, "student/courses-buy-multiple.html", context)

# import pandas as pd
# import math

# """Temp Script to update data on prod rds"""
# def link_exit_ticket_to_all_user():
#     try:
#         df = pd.read_excel("backdata/Exit_ticket_IT_S2_10_M1.xlsx")
#         df.fillna('', inplace=True)
#         df.Email = df.Email.str.strip()
#         lst = pd.unique(pd.Series(list(df.Email)))

#         lst_not_fount = []
#         print(lst)
#         #print(lst_stp)
#         #lst = ['ruggy.man05@gmail.com',]
#         stp_linked = []
#         for si,st in enumerate(lst):

#             all_persons = userauth_models.Person.objects.filter(username__iexact=st)
#             if(all_persons.count()>0):
#                 for person in all_persons:
#                     if(person.person_role == "Student"):
#                         print("#############################")
#                         print(f"{si} : {person.username} / {len(lst)}")
#                         stu_cohorts = person.stuMapID.filter(cohort__module__module_id=3)
#                         print(stu_cohorts)
#                         if(stu_cohorts.count()>0):
#                             for cohort_stu in stu_cohorts:
#                                 #if(cohort_stu.cohort_type == "Trial")
#                                 df_stu = df.loc[df['Email']==st]
#                                 lst_stp = pd.unique(pd.Series(list(df_stu.Step)))
#                                 print(lst_stp)
#                                 for lsi,stp_sno in enumerate(lst_stp):
#                                     print(f"{stp_sno}: / {len(lst_stp)}")
#                                     df_stu_st = df_stu.loc[df_stu['Step'] == stp_sno]
#                                     all_steps = cohort_stu.cohort.cohort_step_status.filter(step__step_sno=stp_sno)
#                                     for i, step_stat in enumerate(all_steps):
#                                         if(step_stat.is_active):
#                                             chk_cohort_step_track = models.CohortStepTracker.objects.filter(
#                                                 stu_cohort_map=cohort_stu, step_status_id=step_stat)
#                                             if(chk_cohort_step_track.count() == 0):
#                                                 cohort_step_track = models.CohortStepTracker(
#                                                     stu_cohort_map=cohort_stu, step_status_id=step_stat)
#                                                 cohort_step_track.save()
#                                                 print(f"Step Linked {i}")
#                                                 stp_linked.append(st)
#                                     stu_track_steps = cohort_stu.stu_cohort_map.filter(step_status_id__step__step_sno=stp_sno)
#                                     for stu_track_step in stu_track_steps:
#                                         if(stu_track_step.step_status_id.is_active):
#                                             if(stu_track_step.tot_completed>=1):
#                                                 print("Hiiiiiiiiiiiii")
#                                                 #stuActionItems = stu_track_step.stu_action_items.all()
#                                                 action_items = stu_track_step.step_status_id.step.action_items.all()
#                                                 for action_item in action_items:
#                                                     chk_action_item_track = models.StudentActionItemTracker.objects.filter(
#                                                         step_tracker=stu_track_step, ActionItem=action_item)
#                                                     if(chk_action_item_track.count() == 0):
#                                                         action_item_track = models.StudentActionItemTracker(step_tracker=stu_track_step, ActionItem=action_item)
#                                                         action_item_track.save()
#                                                         print("Action Item Linked")
#                                                     # else:
#                                                     #     print("All Action Item already linked..")
#                                                     action_item_track = models.StudentActionItemTracker.objects.get(step_tracker=stu_track_step, ActionItem=action_item)
#                                                     action_type = action_item_track.ActionItem.action_type.datatype
#                                                     if(action_type == "Exit"):
#                                                         action_item_exit_tickets = action_item_track.ActionItem.exit_tickets.all()
#                                                         for ai_exit in action_item_exit_tickets:
#                                                             print(f"Question : {ai_exit}")
#                                                             print(ai_exit.sno)
#                                                             #print(type(df_stu_st.Q1))
#                                                             b_answer = df_stu_st.iloc[0][f'Q{ai_exit.sno}']
#                                                             print(f"Answer : {b_answer}")
#                                                             chk_ai_exit_track = models.StudentActionItemExitTicket.objects.filter(
#                                                                 action_item_track=action_item_track, action_item_exit_ticket=ai_exit)
#                                                             if(chk_ai_exit_track.count() == 0):
#                                                                 ai_exit_track = models.StudentActionItemExitTicket(
#                                                                     action_item_track=action_item_track, action_item_exit_ticket=ai_exit,answer=b_answer, is_completed="Yes")
#                                                                 ai_exit_track.save()
#                                                                 print("Action Item Exit Filled...")
#                                                             else:
#                                                                 chk_ai_exit_track1 = chk_ai_exit_track.first()
#                                                                 chk_ai_exit_track1.is_completed="Yes"
#                                                                 if (chk_ai_exit_track1.answer == ''):
#                                                                     chk_ai_exit_track1.answer = b_answer
#                                                                 chk_ai_exit_track1.save()
#                                                                 print("Exit ticket already linked and marked as completed")
#                                                 stuActionItems = stu_track_step.stu_action_items.all()
#                                                 for stu_action in stuActionItems:
#                                                     action_type = stu_action.ActionItem.action_type.datatype
#                                                     if(action_type == "Exit"):
#                                                         stu_ai_track_id = stu_action.Action_item_track_id
#                                                         stu_ai_track_link_update = models.StudentActionItemTracker.objects.get(Action_item_track_id=stu_ai_track_id)
#                                                         status = stu_ai_track_link_update.is_action_item_completed
#                                                         stu_ai_track_link_update.is_completed = status
#                                                         print(status)
#                                                         stu_ai_track_link_update.save()
#                                                         print("Done")

#             else:
#                 lst_not_fount.append(st)
#                 print(f"{st} Email not found..")

#         print(lst_not_fount)
#         df_ls = pd.DataFrame(lst_not_fount,columns = ['Email'])
#         df_ls.to_excel("EmailNotfoundlst_IT_M1_S2_10.xlsx")
#         print(df_ls)
#         print(f"Step Linked : {stp_linked}")
#         df_stp = pd.DataFrame(stp_linked,columns = ['Email'])
#         df_stp.to_excel("EmailLinked_step_IT_M1_S2_10.xlsx")
#     except Exception as ex:
#         print(ex)
#     return None
# def update_data_for_all_user(request):
#     all_cohorts=Cohort.objects.all()
#     print(all_cohorts.count())
#     for cohort in all_cohorts:
#         all_cohort_stus = cohort.cohortMapID.all()
#         for cohort_stu in all_cohort_stus:
#             stu_track_steps = cohort_stu.stu_cohort_map.all()
#             for stu_track_step in stu_track_steps:
#                 stuActionItems = stu_track_step.stu_action_items.all()
#                 for stu_action in stuActionItems:
#                     stu_ai_track_id = stu_action.Action_item_track_id
#                     stu_ai_track_link_update = models.StudentActionItemTracker.objects.get(Action_item_track_id=stu_ai_track_id)
#                     status = stu_ai_track_link_update.is_action_item_completed
#                     stu_ai_track_link_update.is_completed = status
#                     stu_ai_track_link_update.save()
#                     print("Done")
#     return None

# def update_step_for_all_user(request):
#     all_cohorts=Cohort.objects.all()
#     print(all_cohorts.count())
#     for cohort in all_cohorts:
#         all_cohort_stus = cohort.cohortMapID.all()
#         for cohort_stu in all_cohort_stus:
#             stu_track_steps = cohort_stu.stu_cohort_map.all()
#             for stu_track_step in stu_track_steps:
#                 obj_step_track = models.CohortStepTracker.objects.get(step_track_id=stu_track_step.step_track_id)
#                 step_track_stat = obj_step_track.is_step_completed
#                 obj_step_track.is_completed = step_track_stat
#                 obj_step_track.save()
#     return None


@login_required(login_url="/login/")
def exercise_page_view(request, cohort_id):
    execution_start_time = datetime.datetime.today()
    print(
        f"Exercise start time : {execution_start_time} - ##########################")
    logger.info(f"In exercise_page_view called by : {request.user.username}")
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to exercise page view from counselor dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to exercise page view from counselor dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    context = {}
    c_plan = deactivate_trial_plan(request, context)

    if (c_plan is None or c_plan.plans.plan_name == "Community"):
        logger.info(
            f"Redirected to exercise page view from home page : {request.user.username}")
        return HttpResponseRedirect(reverse("home"))
    try:
        stu_id = request.user.id
        stu_email = request.user.email

        course = models.StudentCohortMapper.objects.filter(
            student=stu_id, cohort=cohort_id)
        logger.info(
            f"course obj linked at exercise page for : {request.user.username}")
        hubspot_step_completion_rate = ''
        hubspot_step_completion_date = ''
        hubspot_is_step_completed_75 = ''
        if (course.count() != 0):
            stu_cohort_name = course[0].cohort.cohort_name
            context, current_plan = get_all_plans(request)
            if (current_plan is None):
                context = {}
            # context['is_trial_active']= c_plan.is_trial_active
            context['course'] = course[0]
            context['module_title'] = course[0].cohort.module.title
            context['module_desc'] = course[0].cohort.module.description
            context['module_desc_length'] = len(context['module_desc'])
            all_steps = models.courseMdl.step_status.objects.filter(
                cohort_id=cohort_id)
            hubspot_step_unlock_date = ''
            is_first_time_for_steps_screen = request.session.get('is_first_time_for_steps_screen', False)
            for i, step_stat in enumerate(all_steps):
                cohort_step_track, is_created = models.CohortStepTracker.objects.get_or_create(stu_cohort_map=course[0], step_status_id=step_stat)
                step_name = step_stat.step.title
                if(is_created):
                    logger.info(f"In step-screen step({i+1}) linked: {request.user.username}")
                    todo_date = step_stat.starting_date
                    hubspot_step_unlock_date = hubspot_step_unlock_date + \
                        f"_Course-{step_stat.cohort.module.module_id}-Step{i+1}:{todo_date}"
                action_items = cohort_step_track.step_status_id.step.action_items.filter(is_deleted=False).all()
                try:
                    for action_item in action_items:
                        action_item_track, is_created_ac = models.StudentActionItemTracker.objects.get_or_create(step_tracker=cohort_step_track, ActionItem=action_item)
                        if is_first_time_for_steps_screen:
                            request.session['is_first_time_for_steps_screen'] = False
                            action_type = action_item_track.ActionItem.action_type.datatype
                            if (action_type == "Links"):
                                action_item_links = action_item_track.ActionItem.links.filter(is_deleted=False).all()
                                for ai_link in action_item_links:
                                    ai_link_track, is_created_ai = models.StudentActionItemLinks.objects.get_or_create(action_item_track=action_item_track, action_item_link=ai_link, defaults={'is_completed': 'No'})
                            elif (action_type == "Diary"):
                                action_item_diary = action_item_track.ActionItem.diary.filter(
                                    is_deleted=False).all()
                                for ai_diary in action_item_diary:
                                    ai_diary_track, is_created = models.StudentActionItemDiary.objects.get_or_create(action_item_track=action_item_track, action_item_diary=ai_diary,defaults={'email': stu_email, 'cohort_name': stu_cohort_name, 'step_title': step_name})
                            elif (action_type == "Exit"):
                                action_item_exit_tickets = action_item_track.ActionItem.exit_tickets.filter(
                                    is_deleted=False).all()
                                for ai_exit in action_item_exit_tickets:
                                    ai_exit_track, is_created = models.StudentActionItemExitTicket.objects.get_or_create(
                                        action_item_track=action_item_track, action_item_exit_ticket=ai_exit, defaults={'is_completed': 'No'})
                            elif (action_type == "Table"):
                                action_item_type_table = action_item_track.ActionItem.actionitem_type_table.filter(
                                    is_deleted=False).all()
                                for ai_table in action_item_type_table:
                                    ai_table_track, is_created = models.StudentActionItemTypeTable.objects.get_or_create(
                                        action_item_track=action_item_track, action_item_type_table=ai_table, defaults={'is_completed': 'No'})
                            elif (action_type == "Google_Form"):
                                action_item_google_form = action_item_track.ActionItem.actionitem_google_form.filter(
                                    is_deleted=False).all()
                                for ai_google_form in action_item_google_form:
                                    ai_google_form_track, is_created = models.StudentActionItemGoogleForm.objects.get_or_create(
                                        action_item_track=action_item_track, action_item_google_form=ai_google_form, defaults={'is_completed': 'No'})

                            elif (action_type == "TableStep8"):
                                actionitem_type_table_step8 = action_item_track.ActionItem.actionitem_type_table_step8.filter(
                                    is_deleted=False).all()
                                for ai_table_s8 in actionitem_type_table_step8:
                                    ai_table_s8_track, is_created = models.StudentActionItemTypeTableStep8.objects.get_or_create(
                                        action_item_track=action_item_track, action_item_type_table_step8=ai_table_s8, defaults={'is_completed': 'No'})
                            elif (action_type == "Framework"):
                                action_item_framework = action_item_track.ActionItem.actionitem_framework.filter(
                                    is_deleted=False).all()
                                for ai_framework in action_item_framework:
                                    ai_table_track, is_created = models.StudentActionItemFramework.objects.get_or_create(
                                        action_item_track=action_item_track, action_item_framework=ai_framework, defaults={'is_completed': 'No'})
                            else:
                                action_item_files = action_item_track.ActionItem.files.filter(
                                    is_deleted=False).all()
                                for ai_file in action_item_files:
                                    ai_file_track, is_created = models.StudentActionItemFiles.objects.get_or_create(
                                        action_item_track=action_item_track, action_item_file=ai_file, defaults={'is_completed': 'No'})
                        status = action_item_track.is_action_item_completed
                        action_item_track.is_completed = status
                        action_item_track.save()
                except Exception as exa:
                    print(exa)
                    logger.critical(
                        f"Error at execercise page {exa} for {request.user.username}")

                if (cohort_step_track.is_completed == False):
                    step_track_stat = cohort_step_track.is_step_completed
                    # print(step_track_stat)
                    cohort_step_track.is_completed = step_track_stat
                    cohort_step_track.save()
                    total_action_items = cohort_step_track.stu_action_items.filter(
                        ActionItem__is_deleted=False).count()
                    completed_action_items = cohort_step_track.tot_completed
                    if step_track_stat:
                        try:
                            step_completed_date = cohort_step_track.modified_at
                            hubspot_step_completion_date = hubspot_step_completion_date + \
                                f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{step_completed_date}"
                        except:
                            logger.error(
                                f"Error while updating step completion date on hubspot for : {request.user.username}")
                    try:
                        # calculate %
                        if completed_action_items > 0:
                            Compute_completion_rate = 0
                            Compute_completion_rate = (
                                completed_action_items*100.0/total_action_items)
                        else:
                            Compute_completion_rate = 0
                        models.CohortStepTrackerDetails.objects.update_or_create(
                            cohort_step_tracker=cohort_step_track, defaults={"step_completion": Compute_completion_rate})
                        hubspot_step_completion_rate = hubspot_step_completion_rate + \
                            f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{Compute_completion_rate}"
                        if Compute_completion_rate >= 75:
                            hubspot_is_step_completed_75 = hubspot_is_step_completed_75 + \
                                f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:Yes"
                        else:
                            hubspot_is_step_completed_75 = hubspot_is_step_completed_75 + \
                                f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:No"
                    except Exception as ex:
                        logger.error(
                            f"Error while updating step completion rate on hubspot for : {request.user.username}")
                        print(ex)
                else:
                    models.CohortStepTrackerDetails.objects.update_or_create(
                        cohort_step_tracker=cohort_step_track, defaults={"step_completion": 100})
                    hubspot_is_step_completed_75 = hubspot_is_step_completed_75 + \
                        f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:Yes"
                    hubspot_step_completion_rate = hubspot_step_completion_rate + \
                        f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{100.00}"
                    step_completed_date = cohort_step_track.modified_at
                    hubspot_step_completion_date = hubspot_step_completion_date + \
                        f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{step_completed_date}"

            if hubspot_step_unlock_date != '':
                try:
                    # hubspotContactupdateQueryAdded
                    logger.info(
                        f"In hubspot step unlock date parameter building for : {request.user.username}")
                    keys_list = ["email", "hubspot_step_unlocked_date"]
                    values_list = [request.user.username,
                                   hubspot_step_unlock_date]
                    create_update_contact_hubspot(
                        request.user.username, keys_list, values_list)
                    logger.info(
                        f"In hubspot step unlock date parameter update completed for : {request.user.username}")
                except Exception as ex:
                    logger.error(
                        f"Error at hubspot step unlock date parameter update {ex} for : {request.user.username}")
            
            try:
                # hubspotContactupdateQueryAdded
                logger.info(
                    f"In hubspot step completion rate parameter building for : {request.user.username}")
                keys_list = ["email", "hubspot_step_completion_rate",
                             "hubspot_step_completion_date", "hubspot_is_step_completed_75"]
                values_list = [request.user.username,
                               hubspot_step_completion_rate, hubspot_step_completion_date, hubspot_is_step_completed_75]
                create_update_contact_hubspot(
                    request.user.username, keys_list, values_list)
                logger.info(
                    f"In hubspot step completion rate parameter update completed for : {request.user.username}")
            except Exception as ex:
                logger.error(
                    f"Error at hubspot step completion rate parameter update {ex} for : {request.user.username}")
            all_tracker_steps = models.CohortStepTracker.objects.filter(
                stu_cohort_map=course[0])
            # stu_map_cohort_id = course[0].stu_cohort_map_id
            # stu_email = request.user.username
            # step_completions.apply_async(args=[stu_map_cohort_id, stu_email])
            context['all_steps'] = all_tracker_steps
            update_endurance_score.apply_async(
                args=[request.user.username, request.user.pk, request.LANGUAGE_CODE])
        else:
            # messages.error(request, 'Sorry, You can not access this module..') #all_steps
            logger.warning(
                f"User can not access this module : {request.user.username}")
            context['error_msg'] = _("Sorry, You can not access this module")
    except Exception as ex:
        logger.critical(
            f"Error in exercise page view {ex} for : {request.user.username}")
    execution_end_time = datetime.datetime.today() - execution_start_time
    print(
        f"Exercise end time : {execution_start_time} - {execution_end_time} - ##########################")
    return render(request, "student/exercise-page.html", context)


def check_next_step(request):

    person = request.user
    student_cohorts = person.stuMapID.filter(
        stu_cohort_lang=request.LANGUAGE_CODE)
    next_date = None
    next_step_status = "None"

    for stu_cohort in student_cohorts:
        stu_steps = stu_cohort.stu_cohort_map.all()
        for step in stu_steps:

            if step.step_status_id.is_active is False:
                next_date = step.step_status_id.starting_date
                next_step_status = "False"
            else:
                next_step_status = "True"

    return next_date, next_step_status


def check_step_is_completed(request, cohort_step_track, i):
    hubspot_step_completion_rate = ''
    hubspot_step_completion_date = ''
    hubspot_is_step_completed_75 = ''
    print(cohort_step_track)
    if (cohort_step_track.is_completed == False):
        step_track_stat = cohort_step_track.is_step_completed
        # print(step_track_stat)
        cohort_step_track.is_completed = step_track_stat
        cohort_step_track.save()
        total_action_items = cohort_step_track.stu_action_items.filter(
            ActionItem__is_deleted=False).count()
        completed_action_items = cohort_step_track.tot_completed
        if step_track_stat:
            try:
                step_completed_date = cohort_step_track.modified_at
                hubspot_step_completion_date = hubspot_step_completion_date + \
                    f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{step_completed_date}"
            except:
                logger.error(
                    f"Error while updating step completion date on hubspot for : {request.user.username}")
        try:
            # calculate %
            if completed_action_items > 0:
                Compute_completion_rate = 0
                Compute_completion_rate = (
                    completed_action_items*100.0/total_action_items)
            else:
                Compute_completion_rate = 0
            models.CohortStepTrackerDetails.objects.update_or_create(
                cohort_step_tracker=cohort_step_track, defaults={"step_completion": Compute_completion_rate})
            hubspot_step_completion_rate = hubspot_step_completion_rate + \
                f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{Compute_completion_rate}"
            if Compute_completion_rate >= 75:
                hubspot_is_step_completed_75 = hubspot_is_step_completed_75 + \
                    f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:Yes"
            else:
                hubspot_is_step_completed_75 = hubspot_is_step_completed_75 + \
                    f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:No"
        except Exception as ex:
            logger.error(
                f"Error while updating step completion rate on hubspot for : {request.user.username}")
            print(ex)
    else:
        models.CohortStepTrackerDetails.objects.update_or_create(
            cohort_step_tracker=cohort_step_track, defaults={"step_completion": 100})
        hubspot_is_step_completed_75 = hubspot_is_step_completed_75 + \
            f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:Yes"
        hubspot_step_completion_rate = hubspot_step_completion_rate + \
            f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{100.00}"
        step_completed_date = cohort_step_track.modified_at
        hubspot_step_completion_date = hubspot_step_completion_date + \
            f"_Course-{cohort_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{step_completed_date}"
        # ct_timestamp = datetime.datetime.now()
        update_endurance_score.apply_async(
            args=[request.user.username, request.user.pk, request.LANGUAGE_CODE])
    try:
        # hubspotContactupdateQueryAdded
        logger.info(
            f"In hubspot step completion rate parameter building for : {request.user.username}")
        keys_list = ["email", "hubspot_step_completion_rate",
                     "hubspot_step_completion_date", "hubspot_is_step_completed_75"]
        values_list = [request.user.username,
                       hubspot_step_completion_rate, hubspot_step_completion_date, hubspot_is_step_completed_75]
        create_update_contact_hubspot(
            request.user.username, keys_list, values_list)
        logger.info(
            f"In hubspot step completion rate parameter update completed for : {request.user.username}")
    except Exception as ex:
        logger.error(
            f"Error at hubspot step completion rate parameter update {ex} for : {request.user.username}")


@login_required(login_url="/login/")
def action_item_view(request, step_track_id, sno=0):
    # ai_status_new = request.POST.get('ai_status_new')
    context = {}
    is_next_action_item = False
    # next_date , next_step_status= check_next_step(request)
    logger.info(
        f"In action_item_view page called by : {request.user.username}")
    if request.user.person_role == "Counselor":
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    # c_plan = deactivate_trial_plan(request, context)
    # if (c_plan is None or c_plan.plans.plan_name == "Community"):
    #     return HttpResponseRedirect(reverse("home"))
    context, current_plan = get_all_plans(request)
    if (current_plan is None):
        context = {}
    # if(ai_status_new is not None):
    #     sno = int(ai_status_new)
    # else:
    sno = int(sno)
    current_sno = int(sno)
    if (sno > 0):
        sno = sno-1
    step_track_id = int(step_track_id)
    context['ai_counter'] = sno+1
    next_ai = sno+2
    context['next_ai'] = next_ai
    context['last_ai'] = sno
    context['step_track_id'] = step_track_id
    # context['step_no']=step_no
    context['cohortid'] = None
    # next_step_track_id = step_track_id + 1
    # context['next_step_track_id'] = next_step_track_id
    # context['next_date'] = next_date
    # context['next_step_status1'] = next_step_status
    mypdf_obj = MyPdfs.objects.filter(module_lang=request.LANGUAGE_CODE, is_published=True,
                                      is_for_middle_school=request.user.student.is_from_middle_school).first()

    try:
        stu_id = request.user.id
        access = False
        cohortStepTrack = models.CohortStepTracker.objects.get(
            step_track_id=step_track_id)
        context['cohortStepTrack'] = cohortStepTrack
        context['step_sno'] = cohortStepTrack.step_status_id.step.step_sno
        logger.info(
            f"cohortStepTrack obj linked for step_track_id-{step_track_id} and AI SNO-{sno} at action_item_view page for : {request.user.username}")
        context['mycohort'] = cohortStepTrack.stu_cohort_map.cohort
        cohortid = cohortStepTrack.stu_cohort_map.cohort.cohort_id
        test_cohort_id = TestCohortID.objects.filter(
            cohort__cohort_id=cohortid).first()
        if test_cohort_id:
            if request.method == "POST":
                request.session['session_next_ai'] = next_ai
                is_next_action_item = True
            template_name = "student/action-items-2.html"
        else:
            template_name = "student/action-items.html"
        context['cohortid'] = cohortid
        stu_cohort_map = cohortStepTrack.stu_cohort_map.student.id
        tot_steps_trackers = models.CohortStepTracker.objects.filter(
            stu_cohort_map=cohortStepTrack.stu_cohort_map).values_list("step_track_id", flat=True)
        lst_step_trackers = []
        for stp_trck in tot_steps_trackers:
            lst_step_trackers.append(stp_trck)
        # print(lst_step_trackers)
        # check_step_is_completed(request,cohortStepTrack,lst_step_trackers.index(int(step_track_id)))
        step_no = lst_step_trackers.index(int(step_track_id))+1
        context['step_no'] = step_no
        next_step_indx = lst_step_trackers.index(int(step_track_id))+1
        total_steps = len(lst_step_trackers)
        is_last_step = False
        next_step_status = False
        previous_step = False
        print(next_step_indx)
        print(total_steps)
        try:
            if (next_step_indx == total_steps):
                is_last_step = True
                previous_step = True
                pre_step_indx = lst_step_trackers.index(int(step_track_id))-1
                previous_step_track_id = lst_step_trackers[pre_step_indx]
                cohortStepTrack1 = models.CohortStepTracker.objects.get(
                    step_track_id=previous_step_track_id)
                context['previous_step_track_id_step_sno'] = cohortStepTrack1.step_status_id.step.step_sno
                context['previous_step_track_id'] = previous_step_track_id
            else:
                next_step_track_id = lst_step_trackers[next_step_indx]
                context['next_step_track_id'] = next_step_track_id
                next_cohortStepTrack = models.CohortStepTracker.objects.get(
                    step_track_id=next_step_track_id)
                context['next_cohortStepTrack'] = next_cohortStepTrack
                context['next_cohortStepTrack_step_sno'] = next_cohortStepTrack.step_status_id.step.step_sno
                context['next_step_msg'] = _("The next step will unlock on ")
                if next_cohortStepTrack.step_status_id.is_active:
                    next_step_status = True
                else:
                    next_step_status = False
                if step_no > 1:
                    previous_step = True
                if previous_step:
                    pre_step_indx = lst_step_trackers.index(int(step_track_id))-1
                    previous_step_track_id = lst_step_trackers[pre_step_indx]
                    cohortStepTrack1 = models.CohortStepTracker.objects.get(
                    step_track_id=previous_step_track_id)
                    context['previous_step_track_id_step_sno'] = cohortStepTrack1.step_status_id.step.step_sno
                    context['previous_step_track_id'] = previous_step_track_id
            logger.info(
                f"All good in action item next step code for step_track_id- {step_track_id}, AI SNO-{sno} for user : {request.user.username}")
        except Exception as ex_ai:
            logger.error(
                f"Error in action item next step code : {ex_ai}, for step_track_id- {step_track_id}, AI SNO-{sno} for user : {request.user.username}")
        context['is_last_step'] = is_last_step
        context['next_step_status'] = next_step_status
        context['previous_step'] = previous_step

        # print(lst_step_trackers)
        if mypdf_obj:
            context['my_pdf_link'] = mypdf_obj.pdf_file.url
        else:
            context['my_pdf_link'] = None
        if (stu_id == stu_cohort_map):
            access = True
        if (access == True):
            if (cohortStepTrack.step_status_id.is_active):
                context['step_title'] = cohortStepTrack.step_status_id.step.title
                context['step_description'] = cohortStepTrack.step_status_id.step.description
                context['step_description_length'] = len(
                    context['step_description'])
                context['module_title'] = cohortStepTrack.step_status_id.step.module.title
                action_items = cohortStepTrack.step_status_id.step.action_items.filter(
                    is_deleted=False).all()
                # context['action_items']=action_items
                for action_item in action_items:
                    action_item_track, is_created = models.StudentActionItemTracker.objects.get_or_create(
                        step_tracker=cohortStepTrack, ActionItem=action_item)
                    # if(chk_action_item_track.count() == 0):
                    #     action_item_track = models.StudentActionItemTracker(
                    #         step_tracker=cohortStepTrack, ActionItem=action_item)
                    #     action_item_track.save()

                """To be deleted"""
                # stu_action_items = cohortStepTrack.stu_action_items.all()
                # for stu_ai_track in stu_action_items:
                #     stu_ai_track_id = stu_ai_track.Action_item_track_id
                #     stu_ai_track_link_update = models.StudentActionItemTracker.objects.get(Action_item_track_id=stu_ai_track_id)
                #     status = stu_ai_track_link_update.is_action_item_completed
                #     stu_ai_track_link_update.is_completed = status
                #     stu_ai_track_link_update.save()
                """"""
                stu_action_items = cohortStepTrack.stu_action_items.filter(
                    ActionItem__is_deleted=False).exclude(ActionItem__action_type__datatype="Exit").order_by("ActionItem__action_sno").all()

                if cohortStepTrack.is_step_completed:
                    stu_exit_ticket_action_items = cohortStepTrack.stu_action_items.filter(
                        ActionItem__is_deleted=False, ActionItem__action_type__datatype="Exit").first()
                    ai_exit_ticket_track_id = stu_exit_ticket_action_items.Action_item_track_id
                    context = action_item_exit(request, ai_exit_ticket_track_id, context)

                lst_ai_to_display_as_lock = list(stu_action_items.filter(
                    is_completed=False).values_list('ActionItem__action_sno', flat=True))
                if len(lst_ai_to_display_as_lock) > 0:
                    lst_ai_to_display_as_lock.pop(0)
                context["lst_ai_to_display_as_lock"] = lst_ai_to_display_as_lock
                context['stu_action_items'] = stu_action_items
                access_lock_test_ai = True
                if test_cohort_id:
                    access_lock_test_ai = False
                    if stu_action_items[sno].ActionItem.action_sno in lst_ai_to_display_as_lock:
                        print("Access false")
                        access_lock_test_ai = False
                    else:
                        access_lock_test_ai = True
                if access_lock_test_ai:
                    if sno < stu_action_items.count():
                        action_type = stu_action_items[sno].ActionItem.action_type.datatype
                        ai_track_id = stu_action_items[sno].Action_item_track_id
                        context['ActionItemDesc'] = stu_action_items[sno].ActionItem.description
                        context['ActionItemTitle'] = stu_action_items[sno].ActionItem.title
                        if (action_type == "Links"):
                            stu_ai_links = action_items_links(
                                ai_track_id, request, cohortid, test_cohort_id)
                            context['stu_ai_data'] = stu_ai_links
                            context['action_type'] = "Links"
                            # print(stu_ai_links[0].action_item_link.linktype)
                        elif (action_type == "Diary"):
                            context = action_item_diary(
                                request, ai_track_id, context)
                            context['action_type'] = "Diary"
                        elif (action_type == "Exit"):
                            print(action_type)
                            context = action_item_exit(
                                request, ai_track_id, context)
                            context['action_type'] = "Exit"
                            print("All Ok")
                        elif (action_type == "Table"):
                            print("ai_track_id", ai_track_id)
                            context = action_items_type_table(
                                request, ai_track_id, context)
                            context['action_type'] = "Table"
                        elif (action_type == "Google_Form"):
                            print("ai_track_id", ai_track_id)
                            context = action_items_google_form(
                                request, ai_track_id, context)
                            context['action_type'] = "Google_Form"
                        elif (action_type == "TableStep8"):
                            context = action_items_type_table_step8(
                                request, ai_track_id, context)
                            context['action_type'] = "TableStep8"
                        elif (action_type == "Framework"):
                            context = action_item_framework(
                                request, ai_track_id, context)
                            context['action_type'] = "Framework"
                        else:
                            stu_ai_files = action_items_files(
                                ai_track_id, request, cohortid, test_cohort_id)
                            filetype = stu_ai_files[0].action_item_file.filetype.filetype
                            if (filetype in ["Assignments", "FileAssignmentInput"]):
                                # context['stu_ai_data'] = stu_ai_files
                                context = action_items_assignment_files(
                                    request, ai_track_id, context)
                                context['stu_ai_file_type'] = filetype
                                # if request.method == 'POST':
                                #     return redirect(reverse('action-items', args=(step_track_id, next_ai)))
                            elif filetype == "FileTextInput":
                                context = action_items_text_files(
                                    request, ai_track_id, context)
                                context['stu_ai_file_type'] = "FileTextInput"
                                # context['stu_ai_data'] = stu_ai_files
                            else:
                                context['stu_ai_file_type'] = "Others"
                                context['stu_ai_data'] = stu_ai_files
                            context['action_type'] = "Files"
                        ai_track_link_update = models.StudentActionItemTracker.objects.get(
                            Action_item_track_id=ai_track_id)
                        status = ai_track_link_update.is_action_item_completed
                        ai_track_link_update.is_completed = status
                        ai_track_link_update.save()
                        context['ai_track_link_update'] = ai_track_link_update
                        if test_cohort_id:
                            if status == True:
                                if action_type in ["Links", "Table", "TableStep8", "Files", "Google_Form", "Framework"]:
                                    if request.method == 'POST':
                                        return redirect(reverse('action-items', args=(step_track_id, next_ai)))
                        if status == True:
                            if action_type in ["Google_Form", "Framework", 'Table', 'TableStep8']:
                                if request.method == 'POST':
                                    if cohortStepTrack.is_step_completed:
                                        stu_exit_ticket_action_items = cohortStepTrack.stu_action_items.filter(
                                            ActionItem__is_deleted=False, ActionItem__action_type__datatype="Exit").first()
                                        ai_exit_ticket_track_id = stu_exit_ticket_action_items.Action_item_track_id
                                        context = action_item_exit(request, ai_exit_ticket_track_id, context)
                                        return render(request, template_name, context)
                                    else:
                                        return redirect(reverse('action-items', args=(step_track_id, next_ai)))
                            # else:
                            #     if cohortStepTrack.tot_completed == stu_action_items.count():
                            #         context['stu_ai_exit_tickets'] = ''
                            #         return redirect(reverse('action-items', args=(step_track_id, current_sno), kwargs=context))
                            # session_next_ai = request.session.get('session_next_ai', None)
                            # if session_next_ai is not None:
                            #     if current_sno != session_next_ai:
                            #         return redirect(reverse('action-items', args=(step_track_id, session_next_ai)))
                    elif cohortStepTrack.is_step_completed:
                        stu_exit_ticket_action_items = cohortStepTrack.stu_action_items.filter(
                            ActionItem__is_deleted=False, ActionItem__action_type__datatype="Exit").first()
                        ai_exit_ticket_track_id = stu_exit_ticket_action_items.Action_item_track_id
                        context = action_item_exit(request, ai_exit_ticket_track_id, context)
                    elif cohortStepTrack.is_step_completed == False:
                        return redirect(reverse('action-items', args=(step_track_id, sno)))
                    else:
                        context['error_msg'] = _("Url does not exists.")
                        logger.warning(
                            f"Url does not exists for Action Item wrong sno - {sno+1} : {request.user.username}")
                else:
                    context['error_msg'] = _(
                        "You are not allowed to access it.")
                    logger.warning(
                        f"In action item view user are not allowed to access it : {request.user.username}")
            else:
                context['error_msg'] = _("You are not allowed to access it.")
                logger.warning(
                    f"In action item view user are not allowed to access it : {request.user.username}")
                # return HttpResponseRedirect(reverse('module-steps',cohortid))
        else:
            context['error_msg'] = _(
                "You are not allowed to access locked step")
            logger.warning(
                f"In action item view user are not allowed to access it : {request.user.username}")
        try:
            check_step_is_completed(
                request, cohortStepTrack, lst_step_trackers.index(int(step_track_id)))
            logger.info(
                f"All good in action item page for step_track_id-{step_track_id}- and AI SNO-{sno} for user: {request.user.username}")
            if cohortStepTrack.is_step_completed:
                stu_exit_ticket_action_items = cohortStepTrack.stu_action_items.filter(
                    ActionItem__is_deleted=False, ActionItem__action_type__datatype="Exit").first()
                ai_exit_ticket_track_id = stu_exit_ticket_action_items.Action_item_track_id
                context = action_item_exit(request, ai_exit_ticket_track_id, context)


            is_step_completed = cohortStepTrack.is_step_50_percentage_completed
            cohort_completion_percentage = cohortStepTrack.stu_cohort_map.cohort_completion_percentage_for_counselor
            if cohort_completion_percentage >=70:
                is_70_percent_of_course_completed = 'Yes'
            else:
                is_70_percent_of_course_completed = 'No'

            if cohort_completion_percentage < 30:
                is_less_than_30_per_course_completed = 'Yes'
            else:
                is_less_than_30_per_course_completed = 'No'
                
            is_step_completed = 'Yes' if is_step_completed else 'No'
            keys_list = ['email', f'Is_step_{step_no}_completed','Is_70_per_of_course_completed','Is_less_than_30_per_course_completed']
            values_list = [request.user.username,is_step_completed,is_70_percent_of_course_completed,is_less_than_30_per_course_completed]
            create_update_contact_hubspot(request.user.username, keys_list, values_list)
            
        except Exception as ex_stp:
            logger.error(
                f"Error in Check step status in action item -{ex_stp}- for user : {request.user.username}")
    except Exception as ex:
        context['error_msg'] = _("Url does not exists.")
        logger.critical(
            f"Error in action item view {ex} : {request.user.username}")
    return render(request, template_name, context)





# @login_required(login_url="/login/")
# def action_item_view(request, step_track_id, sno=0):
#     # ai_status_new = request.POST.get('ai_status_new')
#     context = {}
#     is_next_action_item = False
#     # next_date , next_step_status= check_next_step(request)
#     logger.info(
#         f"In action_item_view page called by : {request.user.username}")
#     if request.user.person_role == "Counselor":
#         return HttpResponseRedirect(reverse("counselor-dashboard"))
#     if request.user.person_role == "Futurely_admin":
#         return HttpResponseRedirect(reverse("counselor-dashboard"))
#     # c_plan = deactivate_trial_plan(request, context)
#     # if (c_plan is None or c_plan.plans.plan_name == "Community"):
#     #     return HttpResponseRedirect(reverse("home"))
#     context, current_plan = get_all_plans(request)
#     if (current_plan is None):
#         context = {}
#     # if(ai_status_new is not None):
#     #     sno = int(ai_status_new)
#     # else:
#     sno = int(sno)
#     current_sno = int(sno)
#     if (sno > 0):
#         sno = sno-1
#     step_track_id = int(step_track_id)
#     context['ai_counter'] = sno+1
#     next_ai = sno+2
#     context['next_ai'] = next_ai
#     context['last_ai'] = sno
#     context['step_track_id'] = step_track_id
#     # context['step_no']=step_no
#     context['cohortid'] = None
#     # next_step_track_id = step_track_id + 1
#     # context['next_step_track_id'] = next_step_track_id
#     # context['next_date'] = next_date
#     # context['next_step_status1'] = next_step_status
#     mypdf_obj = MyPdfs.objects.filter(module_lang=request.LANGUAGE_CODE, is_published=True,
#                                       is_for_middle_school=request.user.student.is_from_middle_school).first()

#     try:
#         stu_id = request.user.id
#         access = False
#         cohortStepTrack = models.CohortStepTracker.objects.get(
#             step_track_id=step_track_id)
#         context['step_sno'] = cohortStepTrack.step_status_id.step.step_sno
#         logger.info(
#             f"cohortStepTrack obj linked for step_track_id-{step_track_id} and AI SNO-{sno} at action_item_view page for : {request.user.username}")
#         context['mycohort'] = cohortStepTrack.stu_cohort_map.cohort
#         cohortid = cohortStepTrack.stu_cohort_map.cohort.cohort_id
#         test_cohort_id = TestCohortID.objects.filter(
#             cohort__cohort_id=cohortid).first()
#         if test_cohort_id:
#             if request.method == "POST":
#                 request.session['session_next_ai'] = next_ai
#                 is_next_action_item = True
#             template_name = "student/action-items-2.html"
#         else:
#             template_name = "student/action-items.html"
#         context['cohortid'] = cohortid
#         stu_cohort_map = cohortStepTrack.stu_cohort_map.student.id
#         tot_steps_trackers = models.CohortStepTracker.objects.filter(
#             stu_cohort_map=cohortStepTrack.stu_cohort_map).values_list("step_track_id", flat=True)
#         lst_step_trackers = []
#         for stp_trck in tot_steps_trackers:
#             lst_step_trackers.append(stp_trck)
#         # print(lst_step_trackers)
#         # check_step_is_completed(request,cohortStepTrack,lst_step_trackers.index(int(step_track_id)))
#         step_no = lst_step_trackers.index(int(step_track_id))+1
#         context['step_no'] = step_no
#         next_step_indx = lst_step_trackers.index(int(step_track_id))+1
#         total_steps = len(lst_step_trackers)
#         is_last_step = False
#         next_step_status = False
#         previous_step = False
#         print(next_step_indx)
#         print(total_steps)
#         try:
#             if (next_step_indx == total_steps):
#                 is_last_step = True
#                 previous_step = True
#                 pre_step_indx = lst_step_trackers.index(int(step_track_id))-1
#                 previous_step_track_id = lst_step_trackers[pre_step_indx]
#                 cohortStepTrack1 = models.CohortStepTracker.objects.get(
#                     step_track_id=previous_step_track_id)
#                 context['previous_step_track_id_step_sno'] = cohortStepTrack1.step_status_id.step.step_sno
#                 context['previous_step_track_id'] = previous_step_track_id
#             else:
#                 next_step_track_id = lst_step_trackers[next_step_indx]
#                 context['next_step_track_id'] = next_step_track_id
#                 next_cohortStepTrack = models.CohortStepTracker.objects.get(
#                     step_track_id=next_step_track_id)
#                 context['next_cohortStepTrack'] = next_cohortStepTrack
#                 context['next_cohortStepTrack_step_sno'] = next_cohortStepTrack.step_status_id.step.step_sno
#                 context['next_step_msg'] = _("The next step will unlock on ")
#                 if next_cohortStepTrack.step_status_id.is_active:
#                     next_step_status = True
#                 else:
#                     next_step_status = False
#                 if step_no > 1:
#                     previous_step = True
#                 if previous_step:
#                     pre_step_indx = lst_step_trackers.index(int(step_track_id))-1
#                     previous_step_track_id = lst_step_trackers[pre_step_indx]
#                     cohortStepTrack1 = models.CohortStepTracker.objects.get(
#                     step_track_id=previous_step_track_id)
#                     context['previous_step_track_id_step_sno'] = cohortStepTrack1.step_status_id.step.step_sno
#                     context['previous_step_track_id'] = previous_step_track_id
#             logger.info(
#                 f"All good in action item next step code for step_track_id- {step_track_id}, AI SNO-{sno} for user : {request.user.username}")
#         except Exception as ex_ai:
#             logger.error(
#                 f"Error in action item next step code : {ex_ai}, for step_track_id- {step_track_id}, AI SNO-{sno} for user : {request.user.username}")
#         context['is_last_step'] = is_last_step
#         context['next_step_status'] = next_step_status
#         context['previous_step'] = previous_step

#         # print(lst_step_trackers)
#         if mypdf_obj:
#             context['my_pdf_link'] = mypdf_obj.pdf_file.url
#         else:
#             context['my_pdf_link'] = None
#         if (stu_id == stu_cohort_map):
#             access = True
#         if (access == True):
#             if (cohortStepTrack.step_status_id.is_active):
#                 context['step_title'] = cohortStepTrack.step_status_id.step.title
#                 context['step_description'] = cohortStepTrack.step_status_id.step.description
#                 context['step_description_length'] = len(
#                     context['step_description'])
#                 context['module_title'] = cohortStepTrack.step_status_id.step.module.title
#                 action_items = cohortStepTrack.step_status_id.step.action_items.filter(
#                     is_deleted=False).all()
#                 # context['action_items']=action_items
#                 for action_item in action_items:
#                     action_item_track, is_created = models.StudentActionItemTracker.objects.get_or_create(
#                         step_tracker=cohortStepTrack, ActionItem=action_item)
#                     # if(chk_action_item_track.count() == 0):
#                     #     action_item_track = models.StudentActionItemTracker(
#                     #         step_tracker=cohortStepTrack, ActionItem=action_item)
#                     #     action_item_track.save()

#                 """To be deleted"""
#                 # stu_action_items = cohortStepTrack.stu_action_items.all()
#                 # for stu_ai_track in stu_action_items:
#                 #     stu_ai_track_id = stu_ai_track.Action_item_track_id
#                 #     stu_ai_track_link_update = models.StudentActionItemTracker.objects.get(Action_item_track_id=stu_ai_track_id)
#                 #     status = stu_ai_track_link_update.is_action_item_completed
#                 #     stu_ai_track_link_update.is_completed = status
#                 #     stu_ai_track_link_update.save()
#                 """"""
#                 stu_action_items = cohortStepTrack.stu_action_items.filter(
#                     ActionItem__is_deleted=False).order_by("ActionItem__action_sno").all()
#                 lst_ai_to_display_as_lock = list(stu_action_items.filter(
#                     is_completed=False).values_list('ActionItem__action_sno', flat=True))
#                 if len(lst_ai_to_display_as_lock) > 0:
#                     lst_ai_to_display_as_lock.pop(0)
#                 context["lst_ai_to_display_as_lock"] = lst_ai_to_display_as_lock
#                 context['stu_action_items'] = stu_action_items
#                 access_lock_test_ai = True
#                 if test_cohort_id:
#                     access_lock_test_ai = False
#                     if stu_action_items[sno].ActionItem.action_sno in lst_ai_to_display_as_lock:
#                         print("Access false")
#                         access_lock_test_ai = False
#                     else:
#                         access_lock_test_ai = True
#                 if access_lock_test_ai:
#                     if sno < stu_action_items.count():
#                         action_type = stu_action_items[sno].ActionItem.action_type.datatype
#                         ai_track_id = stu_action_items[sno].Action_item_track_id
#                         context['ActionItemDesc'] = stu_action_items[sno].ActionItem.description
#                         context['ActionItemTitle'] = stu_action_items[sno].ActionItem.title
#                         if (action_type == "Links"):
#                             stu_ai_links = action_items_links(
#                                 ai_track_id, request, cohortid, test_cohort_id)
#                             context['stu_ai_data'] = stu_ai_links
#                             context['action_type'] = "Links"
#                             # print(stu_ai_links[0].action_item_link.linktype)
#                         elif (action_type == "Diary"):
#                             context = action_item_diary(
#                                 request, ai_track_id, context)
#                             context['action_type'] = "Diary"
#                         elif (action_type == "Exit"):
#                             print(action_type)
#                             context = action_item_exit(
#                                 request, ai_track_id, context)
#                             context['action_type'] = "Exit"
#                             print("All Ok")
#                         elif (action_type == "Table"):
#                             print("ai_track_id", ai_track_id)
#                             context = action_items_type_table(
#                                 request, ai_track_id, context)
#                             context['action_type'] = "Table"
#                         elif (action_type == "Google_Form"):
#                             print("ai_track_id", ai_track_id)
#                             context = action_items_google_form(
#                                 request, ai_track_id, context)
#                             context['action_type'] = "Google_Form"
#                         elif (action_type == "TableStep8"):
#                             context = action_items_type_table_step8(
#                                 request, ai_track_id, context)
#                             context['action_type'] = "TableStep8"
#                         elif (action_type == "Framework"):
#                             context = action_item_framework(
#                                 request, ai_track_id, context)
#                             context['action_type'] = "Framework"
#                         else:
#                             stu_ai_files = action_items_files(
#                                 ai_track_id, request, cohortid, test_cohort_id)
#                             filetype = stu_ai_files[0].action_item_file.filetype.filetype
#                             if (filetype in ["Assignments", "FileAssignmentInput"]):
#                                 # context['stu_ai_data'] = stu_ai_files
#                                 context = action_items_assignment_files(
#                                     request, ai_track_id, context)
#                                 context['stu_ai_file_type'] = filetype
#                                 # if request.method == 'POST':
#                                 #     return redirect(reverse('action-items', args=(step_track_id, next_ai)))
#                             elif filetype == "FileTextInput":
#                                 context = action_items_text_files(
#                                     request, ai_track_id, context)
#                                 context['stu_ai_file_type'] = "FileTextInput"
#                                 # context['stu_ai_data'] = stu_ai_files
#                             else:
#                                 context['stu_ai_file_type'] = "Others"
#                                 context['stu_ai_data'] = stu_ai_files
#                             context['action_type'] = "Files"
#                         ai_track_link_update = models.StudentActionItemTracker.objects.get(
#                             Action_item_track_id=ai_track_id)
#                         status = ai_track_link_update.is_action_item_completed
#                         ai_track_link_update.is_completed = status
#                         ai_track_link_update.save()
#                         context['ai_track_link_update'] = ai_track_link_update
#                         if test_cohort_id:
#                             if status == True:
#                                 if action_type in ["Links", "Table", "TableStep8", "Files", "Google_Form", "Framework"]:
#                                     if request.method == 'POST':
#                                         return redirect(reverse('action-items', args=(step_track_id, next_ai)))
#                         if status == True:
#                             if action_type in ["Google_Form", "Framework", 'Table', 'TableStep8']:
#                                 if request.method == 'POST':
#                                     return redirect(reverse('action-items', args=(step_track_id, next_ai)))
#                             # session_next_ai = request.session.get('session_next_ai', None)
#                             # if session_next_ai is not None:
#                             #     if current_sno != session_next_ai:
#                             #         return redirect(reverse('action-items', args=(step_track_id, session_next_ai)))
#                     else:
#                         context['error_msg'] = _("Url does not exists.")
#                         logger.warning(
#                             f"Url does not exists for Action Item wrong sno - {sno+1} : {request.user.username}")
#                 else:
#                     context['error_msg'] = _(
#                         "You are not allowed to access it.")
#                     logger.warning(
#                         f"In action item view user are not allowed to access it : {request.user.username}")
#             else:
#                 context['error_msg'] = _("You are not allowed to access it.")
#                 logger.warning(
#                     f"In action item view user are not allowed to access it : {request.user.username}")
#                 # return HttpResponseRedirect(reverse('module-steps',cohortid))
#         else:
#             context['error_msg'] = _(
#                 "You are not allowed to access locked step")
#             logger.warning(
#                 f"In action item view user are not allowed to access it : {request.user.username}")
#         try:
#             check_step_is_completed(
#                 request, cohortStepTrack, lst_step_trackers.index(int(step_track_id)))
#             logger.info(
#                 f"All good in action item page for step_track_id-{step_track_id}- and AI SNO-{sno} for user: {request.user.username}")
#         except Exception as ex_stp:
#             logger.error(
#                 f"Error in Check step status in action item -{ex_stp}- for user : {request.user.username}")
#     except Exception as ex:
#         context['error_msg'] = _("Url does not exists.")
#         logger.critical(
#             f"Error in action item view {ex} : {request.user.username}")
#     return render(request, template_name, context)

def download(request, path):
    logger.info(f"In download function called by : {request.user.username}")
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if (os.path.exists(file_path)):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/file")
            response['Content-Disposition'] = 'inline;filename=' + \
                os.path.basename(file_path)
            user_name = request.user.username
            logger.info(f"File downloaded by : {user_name}")
            return response
    raise Http404


def action_items_files(ai_track_id, request, cohortid, test_cohort_id):

    try:
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        action_item_files = stu_action_item_track.ActionItem.files.all()
        # cohortid = stu_action_item_track.step_tracker.stu_cohort_map.cohort.cohort_id
        for ai_file in action_item_files:
            ai_file_track, is_created = models.StudentActionItemFiles.objects.get_or_create(
                action_item_track=stu_action_item_track, action_item_file=ai_file)
            if (ai_file.filetype.filetype == "Others"):
                if test_cohort_id:
                    if request.method == 'POST':
                        ai_file_track.is_completed = "Yes"
                        ai_file_track.save()
                else:
                    ai_file_track.is_completed = "Yes"
                    ai_file_track.save()
        stu_ai_files = stu_action_item_track.action_item_file_track.all()
        return stu_ai_files
    except Exception as ex:
        logger.error(f"Exception Error In action item files : {ex}")
        return False


def action_items_type_table_step8(request, ai_track_id, context):
    try:
        stu_id = request.user.id
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        if (stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id):
            access = True
        if (access):
            if (request.method == "POST"):
                stu_ai_type_table_step8 = stu_action_item_track.action_item_type_table_step8_track.all()
                save_table_step8 = True
                for stu_ai in stu_ai_type_table_step8:
                    voto_ans = request.POST.get(f"voto{stu_ai.id}", '')
                    if (voto_ans == ''):
                        context[f'error_message_table_step8'] = _(
                            'You must complete before proceeding')
                        save_table_step8 = False

                if (save_table_step8 == True):
                    for stu_ai in stu_ai_type_table_step8:
                        voto_ans = request.POST.get(f"voto{stu_ai.id}", None)
                        comments_ans = request.POST.get(
                            f"commenti{stu_ai.id}", '')
                        stu_ai.rating_ans = int(voto_ans)
                        stu_ai.comments_ans = comments_ans
                        stu_ai.is_completed = "Yes"
                        stu_ai.save()
                    logger.info(
                        f"Table Step8 answer submitted by : {request.user.username}")
            else:
                action_item_table_step8_ques = stu_action_item_track.ActionItem.actionitem_type_table_step8.all()
                for ai_table_step8 in action_item_table_step8_ques:
                    ai_exit_ticket, is_created = models.StudentActionItemTypeTableStep8.objects.get_or_create(
                        action_item_track=stu_action_item_track, action_item_type_table_step8=ai_table_step8, defaults={'is_completed': 'No'})
            stu_ai_table_step8 = stu_action_item_track.action_item_type_table_step8_track.all()
            context['ai_track_id'] = ai_track_id
            context['stu_ai_table_step8'] = stu_ai_table_step8
    except Exception as ex:
        logger.error(
            f"Error in action item table step 8 view {ex} : {request.user.username}")
    return context


def action_items_google_form(request, ai_track_id, context):
    try:
        stu_id = request.user.id
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        google_form_obj = stu_action_item_track.ActionItem.actionitem_google_form.all()
        if stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id:
            access = True
        if access:
            if request.method == "POST":
                print(request.POST)
                request_data = request.POST
                stu_ai_google_forms = stu_action_item_track.action_item_google_form_track.all()
                save_google_form = True
                for stu_ai in stu_ai_google_forms:
                    ans = request.POST.get(f"google_form_ans{stu_ai.id}", '')
                    if (ans == ''):
                        dropdown_val = request.POST.getlist(
                            f"google_form_dropdown_options{stu_ai.id}")
                        if len(dropdown_val) > 0:
                            pass
                        else:
                            context[f'error_google_form_ans'] = _(
                                'You must complete before proceeding')
                            save_google_form = False

                if (save_google_form == True):
                    for stu_ai in stu_ai_google_forms:
                        ans = request.POST.get(
                            f"google_form_ans{stu_ai.id}", None)
                        dropdown_val = request.POST.getlist(
                            f"google_form_dropdown_options{stu_ai.id}")
                        if len(dropdown_val) > 0:
                            ans = dropdown_val
                        stu_ai.answer = ans
                        stu_ai.is_completed = "Yes"
                        stu_ai.save()
                        print(ans)
            else:
                for google_form_id in google_form_obj:
                    stu_ai_google_form, is_created = models.StudentActionItemGoogleForm.objects.get_or_create(
                        action_item_track=stu_action_item_track, action_item_google_form=google_form_id, defaults={"is_completed": "No"})
            stu_ai_google_form_obj = stu_action_item_track.action_item_google_form_track.all()
            context['stu_ai_google_form'] = stu_ai_google_form_obj
            # context["ai_google_form_answer"] = stu_ai_google_form.answer
            context["action_item"] = stu_action_item_track.ActionItem
            context["rating_range"] = range(11)

    except Exception as error:
        logger.error(
            f"Error in action item google form view {error} : {request.user.username}")
    return context


def action_item_framework(request, ai_track_id, context):
    try:
        stu_id = request.user.id
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        framework_id = stu_action_item_track.ActionItem.actionitem_framework.first()
        if (stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id):
            access = True
        if (access):
            if request.method == "POST":
                print(request.POST)
                request_data = request.POST
                data_dict = dict(request_data)
                data = {}
                if len(data_dict['ans1']) <= 2:
                    context["framework_error_msg"] = "Completare almeno 3 corsi di studio"
                    context["framework_questions"] = json.loads(
                        framework_id.questions)
                    stu_ai_framework, is_created = models.StudentActionItemFramework.objects.get_or_create(
                        action_item_track=stu_action_item_track, defaults={"action_item_framework": framework_id})
                    context['stu_ai_framework'] = stu_ai_framework
                    if stu_ai_framework.answer == '':
                        context["stu_ai_framework_answer"] = {}
                    else:
                        context["stu_ai_framework_answer"] = json.loads(
                            stu_ai_framework.answer)
                    context["range"] = range(5)
                    return context

                questions_len = len(json.loads(
                    framework_id.questions).keys()) + 1
                for i in range(1, questions_len):
                    key_name = f"ans{i}"
                    new_data_dict = []

                    for x in data_dict[key_name]:
                        # if x != '':
                        new_data_dict.append(x)
                    data[key_name] = new_data_dict
                data = json.dumps(data)
                stu_ai_framework, is_created = models.StudentActionItemFramework.objects.update_or_create(
                    action_item_track=stu_action_item_track, action_item_framework=framework_id, defaults={"answer": data, "is_completed": "Yes"})
                context['stu_ai_framework'] = stu_ai_framework
                context["stu_ai_framework_answer"] = json.loads(
                    stu_ai_framework.answer)
                ans = json.loads(stu_ai_framework.answer)
                context["range"] = range(len(ans['ans1']))
                context["framework_questions"] = json.loads(
                    framework_id.questions)
            else:
                action_item_obj = framework_id.action_item
                # import ipdb
                # ipdb.set_trace()
                stu_ai_framework, is_created = models.StudentActionItemFramework.objects.get_or_create(
                    action_item_track=stu_action_item_track, defaults={"action_item_framework": framework_id})
                new_action_item_obj = ActionItemConnectWithOtherActionItem.objects.filter(
                    primary_action_item=action_item_obj, ai_relation_type="AutoFill")
                if (new_action_item_obj.count() > 0):
                    new_ai_obj = new_action_item_obj.first()
                    sec_obj = new_ai_obj.secondary_action_item
                    primary_obj = new_ai_obj.primary_action_item
                    stu_ai_tracker_secodary_obj = stu_action_item_track.step_tracker.stu_cohort_map.stu_cohort_map.filter(
                        Q(stu_action_items__ActionItem=sec_obj)).first().stu_action_items.filter(ActionItem=sec_obj).first()
                    # stu_ai_tracker_primary_obj = stu_action_item_track.step_tracker.stu_cohort_map.stu_cohort_map.filter(Q(stu_action_items__ActionItem=primary_obj)).first().stu_action_items.filter(ActionItem=primary_obj).first()
                    if stu_ai_tracker_secodary_obj.action_item_framework_track.all().first().is_completed == "Yes":
                        if stu_ai_framework.is_completed == "No":
                            ans = stu_ai_tracker_secodary_obj.action_item_framework_track.all().first().answer
                            stu_ai_framework.is_completed = "Yes"
                            stu_ai_framework.answer = ans
                            stu_ai_framework.save()
                if is_created:
                    logger.info(
                        f'Student actionitem framework created for : {request.user.email}')
                else:
                    logger.info(
                        f'Student actionitem framework get the data for : {request.user.email}')
                context['stu_ai_framework'] = stu_ai_framework
                if stu_ai_framework.answer == '':
                    context["stu_ai_framework_answer"] = {}
                else:
                    context["stu_ai_framework_answer"] = json.loads(
                        stu_ai_framework.answer)
                if stu_ai_framework.is_completed == "Yes":
                    ans = json.loads(stu_ai_framework.answer)
                    context["range"] = range(len(ans['ans1']))
                else:
                    context["range"] = range(5)
                print(type(framework_id.questions))
                print(framework_id.questions)
                context["framework_questions"] = json.loads(
                    framework_id.questions)
    except Exception as ex:
        logger.error(
            f"Exception Error In action item framework field {ex} : {request.user.username}")
    return context


def action_items_type_table(request, ai_track_id, context):
    try:
        stu_id = request.user.id
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        type_table_id = stu_action_item_track.ActionItem.actionitem_type_table.first()
        if (stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id):
            access = True
        if (access):
            if request.method == "POST":
                print(request.POST)
                request_data = request.POST
                data = {}
                le_mie_competenze = []
                voto = []
                commenti = []
                total_rows = int(request_data['total_rows'])
                if (total_rows >= 3):
                    for i in range(0, total_rows):
                        _skill = request_data.get(
                            f'le_mie_competenze{i+1}', '')
                        _star = request_data.get(f'voto{i+1}', '')
                        _comment = request_data.get(f'commenti{i+1}', '')
                        if (_skill and _star) != '':
                            le_mie_competenze.append(_skill)
                            voto.append(_star)
                            commenti.append(_comment)
                    if len(le_mie_competenze) >= 3 and len(voto) >= 3:
                        data['le_mie_competenze'] = le_mie_competenze
                        data['voto'] = voto
                        data['commenti'] = commenti
                        stu_ai_type_table, is_created = models.StudentActionItemTypeTable.objects.update_or_create(
                            action_item_track=stu_action_item_track, action_item_type_table=type_table_id,
                            defaults={"answer": data, "is_completed": "Yes"})
                    else:
                        context["error_message"] = "Yes"
                        stu_ai_type_table, is_created = models.StudentActionItemTypeTable.objects.get_or_create(
                            action_item_track=stu_action_item_track, defaults={"action_item_type_table": type_table_id})
                else:
                    context["error_message"] = "Yes"
                    stu_ai_type_table, is_created = models.StudentActionItemTypeTable.objects.get_or_create(
                        action_item_track=stu_action_item_track, defaults={"action_item_type_table": type_table_id})
                context['stu_ai_type_table'] = stu_ai_type_table
                context["ai_table_answer"] = stu_ai_type_table.answer
                # context['action_item_ans_length'] = stu_ai_type_table.answer['le_mie_competenze']
            else:
                stu_ai_type_table, is_created = models.StudentActionItemTypeTable.objects.get_or_create(
                    action_item_track=stu_action_item_track, defaults={"action_item_type_table": type_table_id})
                if is_created:
                    logger.info(
                        f'Student actionitem type table created for : {request.user.email}')
                else:
                    logger.info(
                        f'Student actionitem type table get the data for : {request.user.email}')
                context['stu_ai_type_table'] = stu_ai_type_table
                context["ai_table_answer"] = stu_ai_type_table.answer
                # context['action_item_ans_length'] = stu_ai_type_table.answer['le_mie_competenze']

            results = []
            try:
                le_mie_competenze = stu_ai_type_table.answer['le_mie_competenze']
                voto = stu_ai_type_table.answer['voto']
                commenti = stu_ai_type_table.answer['commenti']
                for indx in range(0, len(le_mie_competenze)):
                    res = [le_mie_competenze[indx], voto[indx], commenti[indx]]
                    results.append(res)
                # [results[i].append(value) for values in stu_ai_type_table.answer.values() for i, value in enumerate(values)]
                context['ai_answers'] = results
                if len(le_mie_competenze) == 0:
                    total_rows = 3
                else:
                    total_rows = len(le_mie_competenze)
                context['total_rows'] = total_rows
            except:
                logger.info(
                    f"Action Item type table does not contain answer yet: {request.user.username}")
    except Exception as ex:
        logger.error(
            f"Exception Error In action item type table field {ex} : {request.user.username}")
    return context


def action_items_text_files(request, ai_track_id, context):
    try:
        stu_id = request.user.id
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        if (stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id):
            access = True
        if (access):
            if (request.method == "POST"):
                answer = request.POST.get('textarea_new_actionItem')
                if (len(answer) >= 450):
                    stu_ai_file_id = request.POST.get("stu_ai_file_id")
                    obj = models.StudentActionItemFiles.objects.get(
                        id=stu_ai_file_id)
                    obj.is_completed = "Yes"
                    obj.file_answer = answer
                    obj.save()
                    status = stu_action_item_track.is_action_item_completed
                    stu_action_item_track.is_completed = status
                    stu_action_item_track.save()
                else:
                    context['error_file_text_input'] = _(
                        "Your answer must be atleast 450 chars")
            else:
                action_item_file = stu_action_item_track.ActionItem.files.all()
                for ai_file in action_item_file:
                    ai_file_track, is_created = models.StudentActionItemFiles.objects.get_or_create(
                        action_item_track=stu_action_item_track, action_item_file=ai_file)
            stu_ai_file = stu_action_item_track.action_item_file_track.all()
            totalQuestion = stu_ai_file.count()
            totalAnswered = stu_ai_file.filter(is_completed="Yes").count()
            context['totalQuestion'] = totalQuestion
            context['totalAnswered'] = totalAnswered
            context['stu_data_file_text'] = stu_ai_file
            context['ai_track_id'] = ai_track_id
    except Exception as ex:
        logger.error(
            f"Exception Error In action item assignment field {ex} : {request.user.username}")
    return context


# Assignment Files

def action_items_assignment_files(request, ai_track_id, context):
    try:
        stu_id = request.user.id
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        if (stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id):
            access = True
        if (access):
            if (request.method == "POST"):
                if (len(request.FILES) != 0):
                    ans_assignment = request.FILES['ans_assignment']
                    file_size = ans_assignment.size/1024/1024
                    if (file_size <= 20):
                        stu_ai_file_id = request.POST.get("stu_ai_file_id")
                        obj = models.StudentActionItemFiles.objects.get(
                            id=stu_ai_file_id)
                        obj.is_completed = "Yes"
                        obj.uploaded_file = ans_assignment
                        obj.save()
                        status = stu_action_item_track.is_action_item_completed
                        stu_action_item_track.is_completed = status
                        stu_action_item_track.save()
                    else:
                        context['error_file_upload'] = _(
                            "The file size can not exceed 20 MB")
                else:
                    context['error_file_upload'] = _("Please upload file")
            else:
                action_item_file = stu_action_item_track.ActionItem.files.all()
                for ai_file in action_item_file:
                    ai_file_track, is_created = models.StudentActionItemFiles.objects.get_or_create(
                        action_item_track=stu_action_item_track, action_item_file=ai_file)
                    # if(chk_ai_file_track.count() == 0):
                    #     ai_file_track = models.StudentActionItemFiles(
                    #         action_item_track=stu_action_item_track, action_item_file=ai_file)
                    #     ai_file_track.save()
            stu_ai_file = stu_action_item_track.action_item_file_track.all()
            totalQuestion = stu_ai_file.count()
            totalAnswered = stu_ai_file.filter(is_completed="Yes").count()
            context['totalQuestion'] = totalQuestion
            context['totalAnswered'] = totalAnswered
            context['stu_data_assignment'] = stu_ai_file
            context['ai_track_id'] = ai_track_id
    except Exception as ex:
        logger.error(
            f"Exception Error In action item assignment field {ex} : {request.user.username}")
    return context


def action_items_links(ai_track_id, request, cohortid, test_cohort_id):
    try:
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        action_item_links = stu_action_item_track.ActionItem.links.all()
        # cohortid = stu_action_item_track.step_tracker.stu_cohort_map.cohort.cohort_id
        for ai_link in action_item_links:
            ai_link_track, is_created_ai = models.StudentActionItemLinks.objects.get_or_create(
                action_item_track=stu_action_item_track, action_item_link=ai_link, defaults={'is_completed': 'No'})
            # if(request.method == "POST"):
            if test_cohort_id:
                if (request.method == "POST"):
                    ai_link_track.is_completed = "Yes"
                    ai_link_track.save()
            else:
                if ai_link_track:
                    ai_link_track.is_completed = "Yes"
                    ai_link_track.save()
        stu_ai_links = stu_action_item_track.action_item_link_track.all()
        return stu_ai_links
    except Exception as ex:
        logger.error(f"Error In action item link : {ex}")
        return False


@login_required(login_url="/login/")
def submit_answer_view(request):
    try:
        logger.info(
            f"In submit_answer_view called by : {request.user.username}")
        custom_user_session_id = request.session.get(
            'CUSTOM_USER_SESSION_ID', '')
        if (request.is_ajax and request.method == "POST"):
            stu_ai_diary_id = request.POST.get('stu_ai_diary_id')
            ans = request.POST.get('answer')
            ai_track_id = request.POST.get('ai_track_id')
            obj = models.StudentActionItemDiary.objects.get(id=stu_ai_diary_id)
            obj.is_completed = "Yes"
            obj.answer = ans
            obj.save()
            diary_ques_sno = obj.action_item_diary.sno
            stu_action_item_track = models.StudentActionItemTracker.objects.get(
                Action_item_track_id=ai_track_id)
            status1 = stu_action_item_track.is_action_item_completed
            stu_action_item_track.is_completed = status1
            stu_action_item_track.save()
            stu_ai_diary = stu_action_item_track.action_item_diary_track.all()
            totalQuestion = stu_ai_diary.count()
            totalAnswered = stu_ai_diary.filter(is_completed="Yes").count()
            res = {
                'msg': 'successfully submitted',
                'totalQuestion': totalQuestion,
                'totalAnswered': totalAnswered,
                'ai_track_id': ai_track_id,
                'ai_status': status1,
                'diary_ques_sno':diary_ques_sno
            }
            if obj.action_item_diary.is_linked_with_ai_comment:
                step_sno = str(obj.action_item_diary.action_item.step.step_sno)
                ques_sno = str(obj.action_item_diary.sno)
                is_from_fast_track = request.user.student.is_from_fast_track_program
                is_from_middle_school = request.user.student.is_from_middle_school
                logger.info(
                    f"Celery task is going to start to generate the AI comment : {request.user.username}")
                # ai_generated_comment_for_stu_action_item_diary.apply_async(
                #     args=[request.user.id, ans, stu_ai_diary_id])
                ai_generated_comment_for_stu_action_item_diary.apply_async(
                    args=[request.user.id, ans, stu_ai_diary_id, step_sno, ques_sno, is_from_fast_track, is_from_middle_school])
            logger.info(
                f"In submit answer view answer submited : {request.user.username}")
            return JsonResponse(res, status=200)
    except Exception as ex:
        logger.error(
            f"Error in submit answer view {ex} : {request.user.username}")
        return JsonResponse({'msg': 'Error to submit the answer'}, status=400)


def action_item_diary(request, ai_track_id, context):  # Diary
    try:
        stu_id = request.user.id
        stu_email = request.user.email
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        stu_cohort_name = stu_action_item_track.step_tracker.stu_cohort_map.cohort.cohort_name
        step_name = stu_action_item_track.step_tracker.step_status_id.step.title
        if (stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id):
            access = True
        if (access):
            if (request.method == "POST"):
                ans = request.POST.get("answer1")
                stu_ai_diary_id = request.POST.get("stu_ai_diary_id")
                # obj=models.StudentActionItemDiary.objects.get(id=stu_ai_diary_id)
                # obj.is_completed="Yes"
                # obj.answer=ans
                # obj.save()
            else:
                action_item_diary = stu_action_item_track.ActionItem.diary.all()
                for ai_diary in action_item_diary:
                    ai_diary_track, is_created = models.StudentActionItemDiary.objects.get_or_create(
                        action_item_track=stu_action_item_track, action_item_diary=ai_diary, defaults={'email': stu_email, 'cohort_name': stu_cohort_name, 'step_title': step_name})
                    # if(chk_ai_diary_track.count() == 0):
                    #     ai_diary_track = models.StudentActionItemDiary(
                    #         action_item_track=stu_action_item_track, action_item_diary=ai_diary)
                    #     ai_diary_track.email = stu_email
                    #     ai_diary_track.cohort_name = stu_cohort_name
                    #     ai_diary_track.step_title = step_name
                    #     ai_diary_track.save()
            stu_ai_diary = stu_action_item_track.action_item_diary_track.all()
            totalQuestion = stu_ai_diary.count()
            totalAnswered = stu_ai_diary.filter(is_completed="Yes").count()
            context['totalQuestion'] = totalQuestion
            context['totalAnswered'] = totalAnswered
            context['ai_track_id'] = ai_track_id
            context['stu_ai_diary'] = stu_ai_diary
    except Exception as ex:
        logger.error(
            f"Error in action item diary view {ex} : {request.user.username}")
    return context


def action_item_exit(request, ai_track_id, context):
    try:
        stu_id = request.user.id
        access = False
        stu_action_item_track = models.StudentActionItemTracker.objects.get(
            Action_item_track_id=ai_track_id)
        if (stu_id == stu_action_item_track.step_tracker.stu_cohort_map.student.id):
            access = True
        if (access):
            context['exit_ticket_submitted'] = 'No'
            if (request.method == "POST"):
                stu_ai_exit_tickets = stu_action_item_track.action_item_exit_ticket_track.all()
                save_exit_ticket = True
                for stu_ai in stu_ai_exit_tickets:
                    ans = request.POST.get(f"exit_ticket_ans{stu_ai.id}", '')
                    if (ans == ''):
                        context[f'error_exit_ticket_ans'] = _(
                            'You must complete before proceeding')
                        save_exit_ticket = False

                if (save_exit_ticket == True):
                    for stu_ai in stu_ai_exit_tickets:
                        ans = request.POST.get(
                            f"exit_ticket_ans{stu_ai.id}", None)
                        stu_ai.answer = ans
                        stu_ai.is_completed = "Yes"
                        stu_ai.save()
                        print(ans)
                        ai_track_link_update = models.StudentActionItemTracker.objects.get(
                            Action_item_track_id=ai_track_id)
                        status = ai_track_link_update.is_action_item_completed
                        ai_track_link_update.is_completed = status
                        ai_track_link_update.save()
                    context['exit_ticket_submitted'] = 'Yes'
                # obj=models.StudentActionItemDiary.objects.get(id=stu_ai_diary_id)
                # obj.is_completed="Yes"
                # obj.answer=ans
                # obj.save()
            else:
                action_item_exit_ticket = stu_action_item_track.ActionItem.exit_tickets.all()
                for ai_exit_ticket in action_item_exit_ticket:
                    ai_exit_ticket, is_created = models.StudentActionItemExitTicket.objects.get_or_create(
                        action_item_track=stu_action_item_track, action_item_exit_ticket=ai_exit_ticket, defaults={'is_completed': 'No'})
                    # if(chk_ai_exit_ticket.count() == 0):
                    #     ai_exit_ticket_track = models.StudentActionItemExitTicket(
                    #         action_item_track=stu_action_item_track, action_item_exit_ticket=ai_exit_ticket)
                    #     ai_exit_ticket_track.is_completed = "Yes"
                    #     ai_exit_ticket_track.save()
            stu_ai_exit_tickets = stu_action_item_track.action_item_exit_ticket_track.all()
            totalQuestion = stu_ai_exit_tickets.count()
            totalAnswered = stu_ai_exit_tickets.filter(
                is_completed="Yes").count()
            context['totalQuestion'] = totalQuestion
            context['totalAnswered'] = totalAnswered
            context['ai_track_id'] = ai_track_id
            context['stu_ai_exit_tickets'] = stu_ai_exit_tickets
            context['stu_action_item_track'] = stu_action_item_track
    except Exception as ex:
        logger.error(
            f"Error in action item exit view {ex} : {request.user.username}")
    print("Out EXIT")
    return context


def my_personality_test_view_without_login(request):
    if (request.user.id):
        log_username = request.user.username
    else:
        log_username = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        context = {}
        custom_user_session_id = request.session.get(
            'CUSTOM_USER_SESSION_ID', '')
        personality_test = PersonalityTest.objects.filter(
            lang_code=request.LANGUAGE_CODE, is_active=True).first()
        if personality_test:
            stu_personality_test, is_created = models.StudentPersonalityTestMapper.objects.get_or_create(
                session_id=custom_user_session_id, is_created_by_loggedin_user=False, personality_test=personality_test, lang_code=request.LANGUAGE_CODE)
            if stu_personality_test.is_completed:
                logger.info(
                    f"Redirected to personality_test_result from my_personality_test_view_withot_login : {log_username}")
                return HttpResponseRedirect(reverse("personality_test_result"))
            link_pt_question_to_student(stu_personality_test)
            context['stu_personality_test'] = stu_personality_test
            tot_answered = stu_personality_test.tot_ques_completed
            tot_question = stu_personality_test.tot_question
            completed_per = int(tot_answered*100/tot_question)
            context['tot_answered'] = tot_answered
            context['tot_question'] = tot_question
            context['completed_per'] = completed_per
            context['last_answered'] = stu_personality_test.last_answered
            logger.info(
                f"Student started the my_personality_test_view_without_login for : {log_username}")
            return render(request, "student/pt_test_open.html", context)
    except Exception as ex:
        print(ex)
        logger.error(
            f"Error at logged in personality test view - {ex} for user - {log_username}")
    return HttpResponseRedirect(reverse("home"))


@login_required(login_url="/login/")
def my_personality_test_view(request):
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to my_personality_test_view page view from counselor-dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to my_personality_test_view page view from counselor-dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    student = request.user
    current_plan = models.StudentsPlanMapper.plansManager.lang_code(
        request.LANGUAGE_CODE).filter(student=student).first()
    try:
        if current_plan:
            current_plan_name = current_plan.plans.plan_name
            if current_plan_name == "Community":
                logger.info(
                    f"Redirected to home page from personality view as current plan is Community : {request.user.username}")
                return HttpResponseRedirect(reverse("home"))
            else:
                context = {}
                logger.info(
                    f"Student visited at my_personality_test_view : {request.user.username}")
                personality_test = PersonalityTest.objects.filter(
                    lang_code=request.LANGUAGE_CODE, is_active=True).first()
                stu_personality_test, is_created = models.StudentPersonalityTestMapper.objects.get_or_create(
                    student=student, personality_test=personality_test, lang_code=request.LANGUAGE_CODE)
                if stu_personality_test.is_completed:
                    logger.info(
                        f"Redirected to personality_test_result from my_personality_test_view : {request.user.username}")
                    return HttpResponseRedirect(reverse("personality_test_result"))
                link_pt_question_to_student(stu_personality_test)
                context['stu_personality_test'] = stu_personality_test
                tot_answered = stu_personality_test.tot_ques_completed
                tot_question = stu_personality_test.tot_question
                completed_per = int(tot_answered*100/tot_question)
                context['tot_answered'] = tot_answered
                context['tot_question'] = tot_question
                context['completed_per'] = completed_per
                context['last_answered'] = stu_personality_test.last_answered
                print(stu_personality_test)
                logger.info(
                    f"Student started the my_personality_test_view for : {request.user.username}")
                return render(request, "student/pt_test.html", context)
    except Exception as ex:
        logger.error(
            f"Error at logged in personality test view - {ex} for user - {request.user.username}")
    return HttpResponseRedirect(reverse("home"))


def personality_test_ajax_call(request):
    if (request.user.id):
        log_username = request.user.username
    else:
        log_username = request.session.get('CUSTOM_USER_SESSION_ID', '')
    try:
        logger.info(
            f"personality_test_ajax_call submit requested for : {log_username}")
        if request.method == "POST" and request.is_ajax:
            is_this_last = "False"
            request_post = request.POST
            selected_op = request_post.get('selected_option', "")
            question_id = request.POST.get("question_id", "")
            last_answered = request.POST.get("last_answered", "")
            question_sno = request.POST.get("question_sno", "")
            # add validation of int> last_answered
            if selected_op != "" and question_id != "" and last_answered != "":
                stu_ptest = models.StudentPersonalityTest.objects.filter(
                    id=question_id).first()
                if stu_ptest.is_completed:
                    logger.warning(
                        f"question_id_{question_id} this question is already completed : {log_username}")
                else:
                    logger.info(
                        f"question_id_{question_id} submited for : {log_username}")
                    stu_ptest.pt_answer = selected_op
                    stu_ptest.is_completed = True
                    stu_ptest.save()
                    obj = stu_ptest.stu_pt_mapper
                    obj.last_answered = int(last_answered)
                    obj.save()
                    tot_ques_completed = obj.tot_ques_completed
                    tot_question = obj.tot_question
                    completed_per = int(
                        obj.tot_ques_completed*100/obj.tot_question)
                    if (tot_ques_completed == tot_question):
                        sts = obj.is_pt_completed
                        obj.is_completed = sts
                        is_this_last = "True"
                        logger.info(
                            f"question_id_{question_id} submited the last question for : {log_username}")
                        obj.save()
                    # sno = int(question_sno)
                    logger.info(f'question_id_{question_id} - question sno is {question_sno} for : {log_username}')
                    return JsonResponse({"message": "success", "completed_per": completed_per, 'tot_ques_completed': tot_ques_completed, 'tot_question': tot_question, "is_this_last": is_this_last, "sno": question_sno}, status=200, safe=False)
        # return JsonResponse({"error": "something went wrong!!"}, status=400, safe=False)
    except Exception as er:
        print(er)
        logger.error(
            f"Error at personality_test_ajax_call {er} for : {log_username}")
    return JsonResponse({"message": "something went wrong!!"}, status=400, safe=False)


def link_pt_question_to_student(stu_personality_test):
    all_questions = stu_personality_test.personality_test.personalitytestquestions.all()
    for question in all_questions:
        models.StudentPersonalityTest.objects.get_or_create(
            stu_pt_mapper=stu_personality_test, pt_question=question)


def personality_test_result_view(request):
    try:
        reverse_url = ""
        template_name = ""
        if request.user.is_authenticated:
            reverse_url = "my_personality_test"
            template_name = "student/pt_result.html"
            student = request.user
            personality_test = student.person_ptest_mapper.filter(
                lang_code=request.LANGUAGE_CODE).first()
            if personality_test is None:
                reverse_url = "open_riasec_test"
                template_name = "student/pt_result_open.html"
                custom_user_session_id = request.session.get(
                    'CUSTOM_USER_SESSION_ID', '')
                personality_test = models.StudentPersonalityTestMapper.objects.filter(
                    session_id=custom_user_session_id, lang_code=request.LANGUAGE_CODE).first()
        else:
            reverse_url = "open_riasec_test"
            template_name = "student/pt_result_open.html"
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            personality_test = models.StudentPersonalityTestMapper.objects.filter(
                session_id=custom_user_session_id, lang_code=request.LANGUAGE_CODE).first()
        if personality_test is not None:
            if personality_test.is_completed:
                my_score = personality_test.calculate_my_score
                sorted_my_score = sorted(
                    my_score.items(), key=lambda x: x[1], reverse=True)
                return render(request, template_name, {'my_score': my_score, 'sorted_my_score': sorted_my_score})
            else:
                return HttpResponseRedirect(reverse(reverse_url))
    except Exception as ex:
        print(ex)
    return HttpResponseRedirect(reverse(reverse_url))


@login_required(login_url="/login/")
def my_diary_view(request):
    student = request.user
    logger.info(f"In my diary view called by : {student.username}")
    if request.user.person_role == "Counselor":
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    context = {}
    try:
        student = request.user
        context, current_plan_1 = get_all_plans(request)
        if (current_plan_1 is None):
            context = {}
        current_plan = models.StudentsPlanMapper.plansManager.lang_code(
            request.LANGUAGE_CODE).filter(student=student).first()
        if current_plan:
            current_plan_name = current_plan.plans.plan_name
            if current_plan_name == "Community":
                context['purchase_msg'] = _(
                    "The journal is available once you’ve purchased a course")
                if (current_plan.is_trial_expired):
                    my_cohort = student.stuMapID.filter(
                        stu_cohort_lang=request.LANGUAGE_CODE)
                    if (my_cohort.count() > 0):
                        context['module_title'] = my_cohort[0].cohort.module.title
            else:
                my_cohort = student.stuMapID.filter(
                    stu_cohort_lang=request.LANGUAGE_CODE)
                all_courses = []
                if (my_cohort.count() > 0):
                    context['my_cohort'] = my_cohort[0]
                    context['module_title'] = my_cohort[0].cohort.module.title
                    for cohort in my_cohort:
                        all_steps = cohort.stu_cohort_map.all()
                        all_courses.append(all_steps)
                    context['all_courses'] = all_courses
                else:
                    context['date_error'] = _(
                        "The journal is available once you’ve selected the start date")
        user_name = request.user.username
        logger.info(f"My dairy page visited by: {user_name}")
    except Exception as ex:
        context['error_msg'] = _(
            "The journal is available once you’ve purchased a course")
        logger.error(f"Error in my_diary_view {ex} : {request.user.username}")
    return render(request, "student/new-diary.html", context)



@login_required(login_url="/login/")
def is_student_read_diary_comments(request):
    try:
        if (request.is_ajax and request.method == "POST"):
            person = request.user
            logger.info(f"Student requested in the 'is_student_read_diary_comments' method to read the tutor's diary comment: {person.username}")
            cohort_step_tracker_id = request.POST['cohort_step_tracker_id']
            stu_cohort_tracker = models.CohortStepTracker.objects.filter(step_track_id=cohort_step_tracker_id).first()
            for all_diaries in stu_cohort_tracker.get_diary:
                for diary in all_diaries:
                    comments_student_actions_item_diary_objs = diary.comments_student_actions_item_diary.all()
                    for comments_student_actions_item_diary_obj in comments_student_actions_item_diary_objs:
                        if comments_student_actions_item_diary_obj:
                            if not comments_student_actions_item_diary_obj.is_read:
                                comments_student_actions_item_diary_obj.is_read = True
                                comments_student_actions_item_diary_obj.save()
                                logger.info(f"Student successfully read the diary comment of question: {diary.action_item_diary.question} for: {person.username}")
            to_check_all_steps = stu_cohort_tracker.stu_cohort_map.is_any_pending_diary_comment_to_read()
            logger.info(f"successfully checked the all unread comments of all ai diary at is_student_read_diary_comments: {request.user}")

        return JsonResponse({'message': 'success',"to_check_all_steps":to_check_all_steps}, status=200, safe=False)            
    except Exception as ex:
        return JsonResponse({'message': 'error', 'error': str(ex)}, status=400, safe=False)
         

from io import StringIO, BytesIO
from xhtml2pdf import pisa
from django.template import Context

@login_required(login_url="/login/")
def download_diario_conent(request):
    try:
        logger.info(f"Student requested to download pdf file : {request.user}")
        student = request.user
        my_cohort = student.stuMapID.filter(stu_cohort_lang=request.LANGUAGE_CODE)
        context_dict = {}
        all_courses = []

        logger.info(f"Extracting all the steps from the cohort for : {request.user}")
        for cohort in my_cohort:
            all_steps = cohort.stu_cohort_map.all()
            all_courses.append(all_steps)
            
        context_dict['all_courses'] = all_courses
        
        logger.info(f"Reading pdf template file from HTML for : {request.user}")
        template = get_template('student/pdf-file-for-student-my-diary.html')
        logger.info(f"Reading data in pdf file as context : {request.user}")
        html = template.render(context_dict)

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        logger.info(f"Export Pdf file endoded for : {request.user}")

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="report.pdf"'
        response.write(result.getvalue())
        logger.info(f"Student successfully download the my-diary pdf file: {request.user}")
        return response
        
    except Exception as err:
        logger.error(f"Error occurred while export the pdf file in download_diario_conent function")
        return HttpResponse('Failed to generate PDF', status=500)



@login_required(login_url="/login/")
def update_futurelab_form_status(request):
    try:
        if (request.is_ajax and request.method == "POST"):
            person = request.user
            logger.info(
                f"In update_futurelab_form_status page called by : {person.username}")
            student = getattr(person, 'student', None)
            if student and student.src == 'future_lab':
                student.future_lab_form_status = True
                student.save()
            return JsonResponse({'message': 'SUCCESS'}, status=200, safe=False)
    except Exception as ex:
        print(ex)
        logger.error(
            f"Error in update_futurelab_form_status {ex} for : {request.user.username}")
        return JsonResponse({'message': 'error', 'error': str(ex)}, status=400, safe=False)


def remove_test_users(request, email=None):
    if email is not None:
        user = userauth_models.Person.objects.filter(username=email).first()
        user.delete()
        msg = "user deleted successfully"
    else:
        msg = "Email not exist or None"
    return JsonResponse({"message": msg}, status=200, safe=False)


@login_required(login_url="/login/")
def send_email_view(request):
    try:
        if request.method == "POST" and request.is_ajax:
            student = request.user
            send_email_task.apply_async(args=[student.id,student.first_name,student.last_name,student.email])
            logger.info(f"email successfully sent for student: {student}")
            return JsonResponse({"msg": "success"}, status=200, safe=False)
    except Exception as error:
        student = request.user.email
        logger.error(f"Error occurred while sending email to: {student} at send_email_view Error: {str(error)}")
    return JsonResponse({"msg": "error"}, status=400, safe=False)


def link_scholarship_test_question_to_student(stu_scholarship_test):
    all_questions = stu_scholarship_test.scholarship_test.scholarship_test_questions.all()
    for question in all_questions:
        models.StudentScholarShipTest.objects.get_or_create(
            stu_scholarshipTest_mapper=stu_scholarship_test, scholarshipTest_question=question)


@login_required(login_url='/login/')
def student_scholarship_view(request):
    print("In student_scholarship_view")
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to exercise page view from counselor dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to exercise page view from counselor dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    student = request.user
    current_plan = models.StudentsPlanMapper.plansManager.lang_code(
        request.LANGUAGE_CODE).filter(student=student).first()
    try:
        if current_plan and student.student.src == "future_lab":
            if current_plan.plans.plan_name == "Community" or current_plan.is_trial_active == True:
                context = {}
                scholarship_test = ScholarshipTest.objects.filter(
                    lang_code=request.LANGUAGE_CODE, is_active=True).first()
                stu_scholarship_test, is_created = models.StudentScholarshipTestMapper.objects.get_or_create(
                    student=student, scholarship_test=scholarship_test, lang_code=request.LANGUAGE_CODE)
                # if stu_scholarship_test.is_applied:
                #     return HttpResponseRedirect(reverse("home"))
                link_scholarship_test_question_to_student(stu_scholarship_test)
                logger.info(
                    f"link scholarship test question to student for : { request.user.username }")
                context['stu_scholarship_test'] = stu_scholarship_test
                # context['stu_scholarship_test_ques'] = stu_scholarship_test.stu_scholarship_test_ques.filter(is_completed=True).all()
                context['stu_scholarship_test_ques'] = stu_scholarship_test.stu_scholarship_test_ques.all()
                tot_answered = stu_scholarship_test.tot_ques_completed
                tot_question = stu_scholarship_test.tot_question
                completed_per = int(tot_answered*100/tot_question)
                context['tot_answered'] = tot_answered
                context['tot_question'] = tot_question
                context['completed_per'] = completed_per
                context['last_answered'] = stu_scholarship_test.last_answered
                logger.info(
                    f"Scholarship test started by the : {student.username}")
                return render(request, 'student/scholarship.html', context)
    except Exception as error:
        print(error)
        user_name = request.user.username
        logger.critical(
            f"Error in Get Apply scholarship form - {error} : {user_name}")
    return HttpResponseRedirect(reverse("home"))


def send_mail_to_student(student_email, status):
    fromEmail = settings.EMAIL_HOST_USER
    toEmail = "rohit@myfuturely.com"
    if status == "Applied":
        template_name = "student/scholarship_applied_email.html"
        subject = _("Your Scholarship Applied")
        ctx = {
            "username": student_email,
        }
        html_msg = get_template(template_name).render(ctx)
        msg = EmailMessage(subject, html_msg, fromEmail,
                           [student_email, toEmail])
        msg.content_subtype = "html"
        msg.send()
        # models.Stu_Notification.objects.create(student=student_email, title=_("You have successfully applied for the scholarship"))
        logger.info(f"E-Mail sent Successfully for : {student_email}")
        return True
    else:
        return False


@login_required(login_url="/login/")
def scholarship_submit_ans_view(request):
    try:
        if request.method == "POST":
            is_applied = False
            request_post = request.POST
            ques_id = request_post.get('ques_id', "")
            ans = request_post.get('answer', "")
            last_ans = request_post.get('last_ans', "")
            if (ques_id != "" and ans != ""):
                stu_scholarship_test = models.StudentScholarShipTest.objects.get(
                    id=ques_id)
                stu_scholarship_test.scholarshipTest_answer = ans
                stu_scholarship_test.is_completed = True
                stu_scholarship_test.save()
                sno = stu_scholarship_test.scholarshipTest_question.sno
                question = f"question_{sno}"
                keys_list = ['email', question]
                values_list = [request.user.username, ans]
                create_update_contact_hubspot(
                    request.user.username, keys_list, values_list)
                stu_scholarshipTest_mapper = stu_scholarship_test.stu_scholarshipTest_mapper
                stu_scholarshipTest_mapper.last_answered = int(last_ans)
                stu_scholarshipTest_mapper.save()
                tot_ques_completed = stu_scholarshipTest_mapper.tot_ques_completed
                tot_question = stu_scholarshipTest_mapper.tot_question
                completed_per = int(tot_ques_completed*100/tot_question)

                if tot_ques_completed == tot_question:
                    sts = stu_scholarshipTest_mapper.is_stu_scholarship_test_completed
                    stu_scholarshipTest_mapper.is_applied = sts
                    stu_scholarshipTest_mapper.save()
                    # send_mail_to_student.delay(request.user.username, "Applied")
                    # send_mail_to_student(request.user.username, "Applied")
                    keys_list = ['email', "scholarship_status"]
                    values_list = [request.user.username, "Applied"]
                    create_update_contact_hubspot(
                        request.user.username, keys_list, values_list)
                    logger.info(
                        f"celery task created for mail send to Student : {request.user.username}")
                    is_applied = sts
                logger.info(
                    f"scholarship answer submited by : { request.user.username }")
                return JsonResponse({"msg": "success", "completed_per": completed_per, "is_completed": is_applied}, status=200, safe=False)
    except Exception as err:
        print(err)
        logger.error(
            f"Error in scholarship submit answer {err} for : {request.user.username}")
    return JsonResponse({"msg": "error"}, status=404, safe=False)


@login_required(login_url="/login/")
def reserve_my_webinar_seat(request):
    if request.method == "POST" and request.is_ajax:
        webinar_id = request.POST.get("webinar_id", None)
        if webinar_id:
            webinar = Webinars.objects.filter(id=webinar_id).first()
            if webinar is not None:
                if webinar.is_seat_vacant:
                    models.StudentWebinarRecord.objects.create(
                        student=request.user.student, webinar=webinar, seat_reserve=True)
                    webinar.allocated_seats = webinar.allocated_seats + 1
                    webinar.save()
                    try:
                        email = request.user.username
                        keys_list = [
                            'email', webinar.hubspot_properties['Reserve_seat_status']]
                        values_list = [request.user.username, "Yes"]
                        create_update_contact_hubspot(
                            request.user.username, keys_list, values_list)
                        # update_hubspot_properties.apply_async(args=[email, keys_list, values_list])
                        logger.info(
                            f"Hubspot properties are updated to reserve webinar seat for : {request.user.username}")
                    except Exception as error:
                        logger.error(
                            f"Error at reserve_my_webinar_seat for hubspot property {error} for : {request.user.username}")
                    messages.success(request, _(
                        "Congratulations! You have been successfully reserved your seat for webinar."))
                    return JsonResponse({"msg": "success", }, status=200, safe=False)
                else:
                    return JsonResponse({"msg": "Sorry, All seats are resevered...", }, status=200, safe=False)
            return JsonResponse({"msg": "error....", }, status=400, safe=False)
        else:
            return JsonResponse({"msg": "error"}, status=400, safe=False)
    else:
        return JsonResponse({"msg": "error"}, status=400, safe=False)


@login_required(login_url="/login/")
def pre_webinar_view(request, webinar_id):
    try:
        context = {}
        if request.method == "POST":
            try:
                student = request.user.student
                student_webinar_mapper_id = request.POST.get(
                    "student_webinar_mapper_id", None)
                stu_web_map_obj = models.StudentWebinarMapper.objects.get(
                    pk=student_webinar_mapper_id)
                webinar = stu_web_map_obj.webinar
                for stu_question in stu_web_map_obj.stu_webinar_test.all():
                    answer = request.POST.get(f"{stu_question.pk}")
                    stu_question.webinar_answer = answer
                    stu_question.is_completed = True
                    stu_question.save()
                    # models.StudentWebinarAnswer.objects.update_or_create(stu_webinar_mapper=stu_web_map_obj, webinar_question=question, defaults={'webinar_answer': answer, "is_completed": True})
                    logger.info(
                        f"Webinar answer submited by : {request.user.username}")
                if stu_web_map_obj.stu_webinar_test.count() == stu_web_map_obj.webinar_questionnaire.webinar_test_question.count():
                    stu_web_map_obj.is_completed = True
                    stu_web_map_obj.save()
                    models.StudentWebinarRecord.objects.create(
                        student=student, webinar=webinar, seat_reserve=True)
                    webinar.allocated_seats = webinar.allocated_seats + 1
                    webinar.save()
                    logger.info(
                        f"Webinar test completed by : {request.user.username}")
                    messages.success(request, _(
                        "Congratulations! You have been successfully reserved your seat for webinar."))
            except Exception as error:
                logger.error(
                    f"Error at pre-webinar post method {error} for : {request.user.username}")
                messages.error(request, _(
                    "Oops! webinar registration failed. Try again later."))
            return HttpResponseRedirect(reverse("home"))
        webinar_obj = Webinars.objects.get(pk=webinar_id)
        pre_webinar_obj = WebinarQuestionnaire.objects.filter(
            test_type='Pre', webinar=webinar_obj, lang_code=request.LANGUAGE_CODE).first()
        if webinar_obj is None:
            return HttpResponseRedirect(reverse("home"))
        stu_web_map_obj, created = models.StudentWebinarMapper.objects.get_or_create(
            webinar=webinar_obj, student=request.user, webinar_questionnaire=pre_webinar_obj, defaults={'lang_code': request.LANGUAGE_CODE})
        for question in stu_web_map_obj.webinar_questionnaire.webinar_test_question.all():
            obj, created = models.StudentWebinarAnswer.objects.get_or_create(
                stu_webinar_mapper=stu_web_map_obj, webinar_question=question)
        context["stu_web_mapper"] = stu_web_map_obj
        context["webinar_questionnaire_id"] = stu_web_map_obj.webinar_questionnaire.pk
        context["student_webinar_mapper_id"] = stu_web_map_obj.pk
        logger.info(f"Pre-webinar visited by : {request.user.username}")
        return render(request, "student/pre_webinar.html", context)
    except Exception as Err:
        logger.error(
            f"Error at Pre-webinar view {Err} for : {request.user.username}")
        messages.error(request, _(
            "Oops! webinar registration failed. Try again later."))
    return HttpResponseRedirect(reverse("home"))


def post_webinar_view(request, webinar_id):
    try:
        context = {}
        student = request.user.student
        username = request.user.username
        logger.info(f"In Post-webinar visited by : {username}")
        if request.method == "POST":
            attendance_code = request.POST.get("attendance_code", None)
            student_webinar_mapper_id = request.POST.get(
                "student_webinar_mapper_id", None)
            stu_web_map_obj = models.StudentWebinarMapper.objects.get(
                pk=student_webinar_mapper_id)
            webinar = stu_web_map_obj.webinar
            for stu_question in stu_web_map_obj.stu_webinar_test.all():
                question_id = f"{stu_question.pk}"
                answer = request.POST.get(question_id).strip()
                stu_question.webinar_answer = answer
                stu_question.is_completed = True
                stu_question.save()
                # obj, created = models.StudentWebinarAnswer.objects.update_or_create(stu_webinar_mapper=stu_web_map_obj, webinar_question=question, defaults={'webinar_answer': answer, "is_completed": True})
                logger.info(
                    f"Webinar answer submited by : {request.user.username}")
            if attendance_code == webinar.attendance_code:
                if stu_web_map_obj.stu_webinar_test.count() == stu_web_map_obj.webinar_questionnaire.webinar_test_question.count():
                    stu_webinar = models.StudentWebinarRecord.objects.filter(
                        student=student, webinar=webinar).first()
                    if stu_webinar is not None:
                        if stu_webinar.status == "Registered":
                            stu_webinar.status = "Attended"
                            stu_web_map_obj.is_completed = True
                            stu_web_map_obj.save()
                            stu_webinar.save()
                            models.StudentPCTORecord.objects.create(
                                student=student, webinar=stu_webinar, pcto_hours=webinar.pcto_hours)
                            student.update_total_pcto_hour()
                            messages.success(request, _(
                                "Congratulations! You have been successfully marked your attendance for webinar."))
                            logger.info(
                                f"Webinar test completed by : {request.user.username}")
                            try:
                                keys_list = [
                                    'email', webinar.hubspot_properties['Attendance_status']]
                                values_list = [request.user.username, "Yes"]
                                email = request.user.username
                                # update_hubspot_properties.apply_async(args=[email, keys_list, values_list])
                                create_update_contact_hubspot(
                                    request.user.username, keys_list, values_list)
                                logger.info(
                                    f"Hubspot properties are updated to mark attendance for : {request.user.username}")
                            except Exception as error:
                                logger.error(
                                    f"Error at reserve_my_webinar_seat for hubspot property {error} for : {request.user.username}")
                            return HttpResponseRedirect(reverse("home"))
            else:
                messages.error(request, _(
                    "The code entered is wrong. Try again with another code!"))
                logger.error(
                    f"Mark attendance code didn't match! for : {username}")
        webinar_obj = Webinars.objects.get(pk=webinar_id)
        post_webinar_obj = WebinarQuestionnaire.objects.filter(
            test_type='Post', webinar=webinar_obj, lang_code=request.LANGUAGE_CODE).first()
        if webinar_obj is None:
            return HttpResponseRedirect(reverse("home"))
        stu_web_map_obj, created = models.StudentWebinarMapper.objects.get_or_create(
            webinar=webinar_obj, student=request.user, webinar_questionnaire=post_webinar_obj, defaults={'lang_code': request.LANGUAGE_CODE})
        for question in stu_web_map_obj.webinar_questionnaire.webinar_test_question.all():
            obj, created = models.StudentWebinarAnswer.objects.get_or_create(
                stu_webinar_mapper=stu_web_map_obj, webinar_question=question)
        context["stu_web_mapper"] = stu_web_map_obj
        context["webinar_questionnaire_id"] = stu_web_map_obj.webinar_questionnaire.pk
        context["student_webinar_mapper_id"] = stu_web_map_obj.pk
        logger.info(f"Post-Webinar test visited by : {request.user.username}")
        return render(request, "student/post_webinar.html", context)
    except Exception as error:
        logger.error(
            f"Error in Post-webinar {error} for : { request.user.username}")
        messages.error(request, _(
            "Oops! webinar mark attendance failed. try again later."))
    return HttpResponseRedirect(reverse("home"))


@login_required(login_url="/login/")
def mark_attendance_for_webinar(request):
    if request.method == "POST" and request.is_ajax:
        webinar_id = request.POST.get('webinar_id', '')
        attendance_code = request.POST.get('attendance_code', '')
        if webinar_id == '' or attendance_code == '':
            return JsonResponse({"msg": "Something went wrong..."}, status=400, safe=False)
        else:
            student = request.user.student
            webinar = Webinars.objects.filter(id=webinar_id).first()
            stu_webinar = models.StudentWebinarRecord.objects.filter(
                student=student, webinar=webinar).first()
            if stu_webinar is not None:
                if stu_webinar.status == "Registered":
                    if attendance_code == webinar.attendance_code:
                        stu_webinar.status = "Attendant"
                        stu_webinar.save()
                        models.StudentPCTORecord.objects.create(
                            student=student, webinar=stu_webinar, pcto_hours=webinar.pcto_hours)
                        student.update_total_pcto_hour()
                        return JsonResponse({"msg": "success", }, status=200, safe=False)
                    else:
                        return JsonResponse({"msg": _("Invalid code"), }, status=200, safe=False)
                else:
                    return JsonResponse({"msg": _("Attendance already marked"), }, status=200, safe=False)
            else:
                return JsonResponse({"msg": _("Something went wrong")}, status=400, safe=False)
    else:
        return JsonResponse({"msg": _("Something went wrong")}, status=400, safe=False)

# @login_required(login_url="/login/")


def get_comments_view(request):
    try:
        person_email = request.user.username
        if request.method == "POST":
            response = {}
            request_post = request.POST
            diary_id = request_post.get('diary_id')
            diary_obj = models.StudentActionItemDiary.objects.get(pk=diary_id)
            student_email = diary_obj.email
            stduent_obj = userauth_models.Person.objects.filter(
                username=student_email).first()
            comments = models.StudentActionItemDiaryComment.objects.filter(
                student_actions_item_diary_id=diary_obj).all()
            stu_comment_list = []
            admin_comment_list = []
            is_admin = True
            if comments.count() > 0:
                if request.user.person_role == "Futurely_admin":
                    print("Futurely admin")
                    admin_comment = comments.filter(person=request.user)
                    is_admin = True
                elif request.user.person_role == "Student":
                    admin_comment = comments  # .filter(person=request.user)
                    print("Student")
                student_comment = comments.filter(person=stduent_obj)
                for comment in student_comment:
                    stu_comment_list.append(comment.comment)
                response["student_comment"] = stu_comment_list
                for admin_co in admin_comment:
                    if is_admin == False:
                        if admin_co.person.email == student_email:
                            pass
                    elif is_admin == True:
                        if admin_co.person.email == student_email:
                            pass
                        else:
                            admin_comment_list.append(
                                [admin_co.comment, admin_co.pk])
                response["admin_comment"] = admin_comment_list
            logger.info(f"get the comment for : {person_email}")
            response['message'] = 'success'
            return JsonResponse(response, status=200, safe=False)
        else:
            response['message'] = 'error'
            logger.error(f"Error at get comment for : {person_email}")
            return JsonResponse(response, status=200, safe=False)
    except Exception as error:
        logger.error(
            f"Error at get_comments_view for {error} : { request.user.username }")
        return JsonResponse({"msg": "error"}, status=400, safe=False)


@login_required(login_url='/login/')
def student_faq_view(request):
    context = {}
    locale = request.LANGUAGE_CODE
    context['student_faq'] = models.StudentFaq.objects.filter(
        locale=locale).order_by("sno").all()
    return render(request, 'student/faq.html', context)


@login_required(login_url="/login/")
def generate_certificate(request):

    try:
        student = request.user.student
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Certificato ore PCTO Futurely.pdf"'

        page_width = 297
        page_height = 210
        page_size = (page_width * mm, page_height * mm)

        pdf = canvas.Canvas(response, pagesize=page_size)

        logo = ImageReader('static/images/futurely-pcto-hour-certificate.png')
        logo_width = 850
        logo_height = 250
        x = (page_width * mm - logo_width) / 2
        y = page_height * mm - 50 - logo_height
        pdf.drawImage(logo, x, y, logo_width, logo_height)

        pdf.setFontSize(12)
        pdf.drawCentredString(page_width / 2 * mm, y - 5, "certifica che")
        pdf.setFont("Helvetica-Bold", 24)
        name = request.user.first_name + " " + request.user.last_name
        pdf.drawCentredString(page_width / 2 * mm, y - 50, name)

        course_name = "orientamento"

        pcto_hours = student.total_pcto_hours
        text = f"Ha completato con successo il percorso di "
        pdf.setFont("Helvetica", 15)
        pdf.drawCentredString(page_width / 2 * mm, y - 100, text)

        text = f"{course_name}"
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawCentredString(page_width / 2 * mm, y - 120, text)

        text = f"che equivale a {pcto_hours} ore PCTO"
        pdf.setFont("Helvetica", 15)
        pdf.drawCentredString(page_width / 2 * mm, y - 140, text)

        signature = ImageReader('static/images/Elisa-autograph.png')
        signature_width = 100
        signature_height = 70
        x = page_width * mm - 50 - signature_width
        y = 50
        pdf.drawImage(signature, x, y, signature_width, signature_height)

        month_dict = {
            "January": "Gennaio",
            "February": "Febbraio",
            "March": "Marzo",
            "April": "Aprile",
            "May": "Maggio",
            "June": "Giugno",
            "July": "Luglio",
            "August": "Agosto",
            "September": "Settembre",
            "October": "Ottobre",
            "November": "Novembre",
            "December": "Dicembre"
        }

        currentMonth = datetime.datetime.now().strftime("%B")
        current_month_italian = month_dict[currentMonth]
        currentYear = datetime.datetime.now().year
        place_month = "Milano," + " " + \
            current_month_italian + " " + str(currentYear)
        pdf.setFont("Helvetica", 12)
        pdf.drawString(page_width - 250, 80, place_month)
        pdf.drawCentredString(page_width / 2 * mm, y - 180, "")
        text = "*Il riconoscimento delle ore PCTO è a discrezione della scuola: il seguente certificato è valido solo in presenza di una convenzione attiva con Futurely"
        text_x = 80
        text_y = 30
        pdf.setFont("Helvetica", 10)
        pdf.drawString(text_x, text_y, text)
        pdf.save()
        models.CertificateDownload.objects.create(student=student)
    except Exception as error:
        logger.error(
            f"Unable to create certificate  {error} : for  { request.user.username }")
    return response



@login_required(login_url="/login/")
def job_posting(request):
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected to exercise page view from counselor dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    if request.user.person_role == "Futurely_admin":
        logger.info(
            f"Redirected to exercise page view from counselor dashboard: {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    student_plan = request.user.studentPlans.first()
    if student_plan.plans.plan_name == models.courseMdl.PlanNames.JobCourse.value:
        logger.info(
            f"In Job Posting - to search for posts: {request.user.username}")
        context = {}
        template_name = "student/job-posting.html"
        thirty_days_ago = timezone.now() - timedelta(days=30)
        student_company_name = None
        student_company = None
        is_display_specific_posts = False
        job_posts_obj = None
        if request.user.student.sponsor_compnay:
            student_company = request.user.student.sponsor_compnay
            student_company_name = request.user.student.sponsor_compnay.name
            logger.info(f"In Job Posting - Company is linked with student: {request.user.username}")
        if hasattr(student_company,'company_detail'):
            if student_company.company_detail.is_display_specific_job_posts:
                job_posts_obj = models.courseMdl.JobPosting.objects.filter(is_active=True, company_to_display_specific_jobs=student_company).annotate(
                    is_new=Case(
                        When(start_date__gte=thirty_days_ago, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ).order_by('-created_at')
                logger.info(f"In Job Posting - Company is linked with job, and displaying specific posts only : {request.user.username}")
                is_display_specific_posts = True
        if is_display_specific_posts is False:
            job_posts_obj = models.courseMdl.JobPosting.objects.filter(is_active=True).annotate(
                is_new=Case(
                    When(start_date__gte=thirty_days_ago, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ).order_by('-created_at')
        context['job_posts_obj'] = job_posts_obj
        logger.info(f"In Job Posting - returning control bck to template: {request.user.username}")
        return render(request, template_name, context)
    else:
        logger.warning(f"In Job Posting - Wrong student is trying to access: {request.user.username}")
        return HttpResponseRedirect(reverse("home"))

    