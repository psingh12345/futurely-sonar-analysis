# pylint: disable=trailing-whitespace
# import re
#from sys import orig_argv
#from time import process_time_ns
#from unicodedata import lookup
import re
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, request
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
import stripe
import json
from student.models import StudentCohortMapper, StudentsPlanMapper
from courses.models import Modules, Cohort, OurPlans
from userauth.models import Person
from .models import Payment, Coupon,CouponDetail, TaxCollection, PaymentSubscriptionDetails
from student.models import Stu_Notification
from django.utils.translation import ugettext as _
from lib.helper import create_custom_event, calculate_discount_parameters, calculate_discount_and_final_price, calculate_tax_and_price
import logging
from . import models as pay_modl
from django.db.models import FloatField
from django.db.models.functions import Cast
from django.db.models import Sum
from django.core.mail import message, send_mail, BadHeaderError, EmailMessage
from django.template.loader import render_to_string, get_template
from datetime import datetime, timedelta
from lib.hubspot_contact_sns import create_update_contact_hubspot
from django.db.models import Q
from lib.unixdateformatConverter import unixdateformat
from student.tasks import exercise_cohort_step_tracker_creation, link_with_action_items
from lib.custom_logging import CustomLoggerAdapter

adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


def check_and_map_from_trial_cohort(obj_student,cohort,plan_lang ):
    stu_cohort_map = StudentCohortMapper.objects.filter(student=obj_student, cohort__module__module_id=cohort.module.module_id, stu_cohort_lang=plan_lang)
    trial_cohort_exists = False
    if(stu_cohort_map.count() > 0):
        cohort_steps = cohort.cohort_step_status.all()
        stu_cohort_map = stu_cohort_map.first()
        old_all_steps = stu_cohort_map.stu_cohort_map.all()
        for i, step in enumerate(old_all_steps):
            if (step.step_status_id.step.step_id == cohort_steps[i].step.step_id):
                step.step_status_id = cohort_steps[i]
                step.save()
        stu_cohort_map.cohort = cohort
        stu_cohort_map.save()
        trial_cohort_exists = True
    return trial_cohort_exists

def auto_link_to_cohort(obj_student,coupon_obj,plan_lang,plan_name):
    cohort_program1 = None
    cohort_program2 = None
    cohort_program3 = None
    keys_list = []
    values_list = []
    coupon_detail_obj = CouponDetail.objects.filter(coupon=coupon_obj).first()
    if coupon_detail_obj:
        try:
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
        except Exception as er:
            logger.warning(f"Coupon code does not have any linked cohort : {er}")
        if cohort_program1:
            chk = check_and_map_from_trial_cohort(obj_student,cohort_program1,plan_lang)
            if chk == False:
                StudentCohortMapper.objects.create(student=obj_student, cohort=cohort_program1, stu_cohort_lang=plan_lang)
                logger.info(f"In payment page-auto link to cohort - async tasks request is generated: {obj_student.username}")
                exercise_cohort_step_tracker_creation.apply_async(args=[obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program1.cohort_id])
                # exercise_cohort_step_tracker_creation.delay(obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program1.cohort_id)
                # link_with_action_items.delay(obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program1.cohort_id)
            logger.info(f"student cohort mapper obj 1 created at signup for : {obj_student.username}")
            keys_list.append('hubspot_cohort_name_premium')
            values_list.append(cohort_program1.cohort_name)
            Hubspot_cohort_premium_start_date=unixdateformat(cohort_program1.starting_date)
            keys_list.append('hubspot_cohort_premium_start_date')
            values_list.append(Hubspot_cohort_premium_start_date)
        if cohort_program2:
            chk = check_and_map_from_trial_cohort(obj_student,cohort_program2,plan_lang)
            if chk == False:
                StudentCohortMapper.objects.create(student=obj_student, cohort=cohort_program2, stu_cohort_lang=plan_lang)
                logger.info(f"In payment page-auto link to cohort - async tasks request is generated: {obj_student.username}")
                exercise_cohort_step_tracker_creation.apply_async(args=[obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program2.cohort_id])
                # exercise_cohort_step_tracker_creation.delay(obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program2.cohort_id)
                # link_with_action_items.delay(obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program2.cohort_id)
            logger.info(f"student cohort mapper obj 2 created at signup for : {obj_student.username}")
            keys_list.append('hubspot_cohort_name_elite1')
            values_list.append(cohort_program2.cohort_name)
            Hubspot_cohort_elite1_start_date=unixdateformat(cohort_program2.starting_date)
            keys_list.append('hubspot_cohort_elite1_start_date')
            values_list.append(Hubspot_cohort_elite1_start_date)
        if cohort_program3:
            chk = check_and_map_from_trial_cohort(obj_student,cohort_program3,plan_lang)
            if chk == False:
                StudentCohortMapper.objects.create(student=obj_student, cohort=cohort_program3, stu_cohort_lang=plan_lang)
                logger.info(f"In payment page-auto link to cohort - async tasks request is generated: {obj_student.username}")
                exercise_cohort_step_tracker_creation.apply_async(args=[obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program3.cohort_id])
                # exercise_cohort_step_tracker_creation.delay(obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program3.cohort_id)
                # link_with_action_items.delay(obj_student.username, obj_student.pk, coupon_detail_obj.cohort_program3.cohort_id)
            logger.info(f"student cohort mapper obj 3 created at signup for : {obj_student.username}")
            keys_list.append('hubspot_cohort_name_elite2')
            values_list.append(cohort_program3.cohort_name)
            Hubspot_cohort_elite2_start_date=unixdateformat(cohort_program3.starting_date)
            keys_list.append('hubspot_cohort_elite2_start_date')
            values_list.append(Hubspot_cohort_elite2_start_date)  
    return keys_list, values_list


class OrderSummary(UserPassesTestMixin, TemplateView):
    """
    this is order-summary class for the payment.
    """
    template_name = "payment/order-summary.html"

    def test_func(self):
        if self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    def get(self, *args, **kwargs):
        context = {}
        student = self.request.user
        plan_id = self.request.session.get('plan_id', None)
        logger.info(f"In get view of order summary page and Plan_ID {plan_id} : {student.username}")
        if self.request.user.person_role == "Counselor":
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if self.request.user.person_role == "Futurely_admin":
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if self.request.session.get('coupon_code', None):
            del self.request.session['coupon_code']
        # coupon_code = self.request.session.get('coupon_code', None)
        payment_type = self.request.session.get("payment_type", "Weekly")
        print(payment_type)
        print("---------------")
        # try:
        #     payment_type = self.request.session.get("payment_type", None)
        #     logger.info(f"Payment_type fetched from order summary page with Plan_ID {plan_id} : {student.username}")
        # except Exception as er:
        #     logger.info(f"Error, payment_type not found from order summary page- {er} : {student.username}")

        if plan_id:
            #print(plan_id, self.request.LANGUAGE_CODE)
            try:
                our_plan_obj = OurPlans.plansManager.lang_code(
                    self.request.LANGUAGE_CODE).get(id=plan_id)
                logger.info(f"Plan object fetched with {our_plan_obj.plan_name} Plan and Plan ID-{plan_id} from order summary page : {student.username}")
                current_plan = StudentsPlanMapper.plansManager.lang_code(
                    self.request.LANGUAGE_CODE).filter(student=student).first()
                logger.info(f"current plan object fetched from order summary page: {student.username}")
                discount = 0
                # tax=0
                # ipdb.set_trace()
                is_discount_percent = False
                if payment_type == "One Time":
                    logger.info(f"In one time payment at order summary page: {student.username}")
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.cost)
                        logger.info(f"fetched total price when trial is activated at order summary page: {student.username}")
                    else:
                        if current_plan and current_plan.plans.plan_name == "Community" and our_plan_obj.plan_name != "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        elif current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        elif current_plan and current_plan.plans.plan_name == "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.upgrade_cost)
                            logger.info(f"upgrade cost as total price at order summary page: {student.username}")
                        else:
                            total_price = float(our_plan_obj.cost)
                            logger.info(f"plan cost fetched at order summary page: {student.username}")

                # if payment_type == "One Time":
                else:
                    # print("weekly ------------------")
                    logger.info(f"In weekly payment at order summary page: {student.username}")
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.weekly_cost)
                        logger.info(f"fetched total price(weekly cost) when trial is activated at order summary page: {student.username}")
                    else:
                        if current_plan and current_plan.plans.plan_name == "Community" and our_plan_obj.plan_name != "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.weekly_cost)
                            # Redirect to change the subscription duration from 10 week to 20.
                        else:
                            total_price = float(our_plan_obj.weekly_cost)
                            logger.info(f"fetched total price(weekly cost) at order summary page: {student.username}")
                if our_plan_obj:
                    one_time_total_price = float(our_plan_obj.cost)
                    context['our_plan_obj'] = our_plan_obj
                    actual_price = total_price
                    context['actual_price'] = actual_price
                    # tax_calculated_object
                    # if coupon_code:
                    #     discount_parameters = calculate_discount_parameters(self.request, coupon_code)
                    #     context['discount_code'] = coupon_code
                    #     context['is_discount_applied'] = True
                    # else:
                    discount_parameters = calculate_discount_parameters(self.request)
                    logger.info(f"calculated discount at order summary page: {student.username}")
                    if 'is_discount_percent' in discount_parameters:
                        is_discount_percent = discount_parameters['is_discount_percent']
                    if 'discount' in discount_parameters:
                        discount = discount_parameters['discount']
                    if 'code' in discount_parameters:
                        coupon_code = discount_parameters['code']
                        self.request.session['coupon_code'] = coupon_code
                    if 'name' in discount_parameters:
                        context['discount_name'] = discount_parameters['name']
                    else:
                        context['discount_name'] = _("Discount")
                    if 'is_futurelab_or_company_discount_applied' in discount_parameters:
                        context['is_futurelab_or_company_discount_applied'] = discount_parameters['is_futurelab_or_company_discount_applied']
                    if 'is_futurelab_or_company_coupon_expired_or_inactive' in discount_parameters:
                        context['is_futurelab_or_company_coupon_expired_or_inactive'] = discount_parameters[
                            'is_futurelab_or_company_coupon_expired_or_inactive']
                    if 'code' in discount_parameters:
                        context['discount_code'] = discount_parameters['code']
                    ###################################################
                    if payment_type == "Weekly":
                        if is_discount_percent:
                            context['discount'], context['total_price'] = calculate_discount_and_final_price(
                            total_price, discount, is_discount_percent)                        
                        else:
                            context['discount'], context['total_price'] = 0, total_price
                    else:
                        context['discount'], context['total_price'] = calculate_discount_and_final_price(
                            total_price, discount, is_discount_percent)
                    context['one_time_discount'], context['one_time_total_price'] = calculate_discount_and_final_price(
                            one_time_total_price, discount, is_discount_percent)
                tax_with_final_amount = calculate_tax_and_price(self.request, context['total_price'])
                logger.info(f"tax calculated at order summary page: {student.username}")
                context['tax_calculated_object'] = tax_with_final_amount
                tax_isactive = tax_with_final_amount['tax_isactive']
                if tax_isactive:
                    #total_tax_amount = tax_with_final_amount["total_tax_amount"]
                    context['amount_after_tax'] = tax_with_final_amount['amount_after_tax']
                else:
                    context['amount_after_tax'] = tax_with_final_amount['amount_after_tax']
                user_name = self.request.user.username
                context["payment_type"] = payment_type
                logger.info(f"Successfully visited  order summary get page: {user_name}")
            except Exception as ex:
                user_name = self.request.user.username
                logger.critical(f"Error at Order summary page {ex}: {user_name}")
                print(ex)
        else:
            user_name = self.request.user.username
            logger.warning(f"Plan id is missing while calling order summary page : {user_name}")
            return HttpResponseRedirect(reverse("home"))
        return render(self.request, self.template_name, context)

    def post(self, *args, **kwargs):
        """order-summary post view """
        student = self.request.user
        logger.info(f"In post view of order summary page: {student.username}")
        plan_id = self.request.session.get('plan_id', None)
        payment_type = self.request.POST.get("payment_type", None)
        if plan_id and payment_type:
            logger.info(f"Plan id and payment type linked at order summary page-post view: {student.username}")
            self.request.session["payment-type"] = payment_type
            person = self.request.user
            stu_plan = OurPlans.plansManager.lang_code(
                self.request.LANGUAGE_CODE).get(id=plan_id)
            current_plan = StudentsPlanMapper.plansManager.lang_code(
                self.request.LANGUAGE_CODE).filter(student=person).first()
            logger.info(f"plan obj and current plan obj linked at order summary page-post view: {student.username}")
            coupon_code = self.request.session.get('coupon_code', '')
            custom_user_session_id = self.request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            discount = 0
            is_discount_percent = False
            is_upgrade = False
            # upgrade_pay_sub_duration = 0
            self.request.session['is_upgrade'] = is_upgrade
            if payment_type == "Weekly":     
                if(current_plan and current_plan.is_trial_active):
                    total_price = float(stu_plan.weekly_cost)
                else:
                    if current_plan and current_plan.plans.plan_name == "Premium" and stu_plan.plan_name == "Elite":
                        total_price = float(stu_plan.weekly_cost)
                        logger.info(f"upgrade cost as total price at order summary page-post view: {student.username}")
                        # redriect to update subscription duration and update plan to Elite
                        try:
                            payment_obj  = Payment.objects.filter(person=person, status__in=["active", "canceled"], plan__plan_name__contains="Premium")
                            logger.info(f"fetched payment obj filter with(is_active, canceled) and premium plan upgrade to Elite plan : {student.username}")
                            if payment_obj.count() > 0:
                                payment_obj = payment_obj.first()
                                #payment_status_active_obj = payment_obj.filter(status="active").first()
                                #pay_sta_cancel_obj = payment_obj.filter(status="canceled").first()
                                if payment_obj.status == "active" and payment_obj.plan.plan_name == "Premium":
                                    payment_obj.plan = stu_plan
                                    payment_obj.payment_subscription_duration = stu_plan.weekly_cost_duration
                                    payment_obj.save()
                                    current_plan.plans = stu_plan
                                    current_plan.save()
                                    user_name = self.request.user
                                    logger.info(f"Premium Plan upgraded to Elite Plan Successfully order summary page-post view and redirectd in home page : {user_name}")
                                    return redirect(reverse("home"))
                                elif payment_obj.status == "canceled" and payment_obj.plan.plan_name == "Premium":
                                    total_price = float(stu_plan.weekly_cost)
                                    upgrade_pay_sub_duration = stu_plan.weekly_cost_duration - current_plan.plans.weekly_cost_duration
                                    is_upgrade = True
                                    self.request.session['is_upgrade'] = is_upgrade
                                    logger.info(f"upgraded plan canceled and create payment obj with weekly duration in order summary page-post : {student.username}")
                            else:
                                # Create subscription with current Plan!
                                user_name = self.request.user
                                logger.info(f"Subscription is not found in Payment table: {user_name}")
                                total_price = float(stu_plan.weekly_cost)
                        except Exception as ex:
                            print(ex)
                            user_name = self.request.user
                            logger.critical(f"Error Premium Plan upgrade to Elite Plan {ex}: {user_name}")
                    else:
                        total_price = float(stu_plan.weekly_cost) 
                logger.info(f"total price fetched order summary page-post view: {student.username}")
                if coupon_code:
                    discount_parameters = calculate_discount_parameters(
                        self.request, coupon_code)
                else:
                    discount_parameters = calculate_discount_parameters(
                        self.request)
                logger.info(f"discount calculated from order summary page-post view: {student.username}")
                if 'is_discount_percent' in discount_parameters:
                    is_discount_percent = discount_parameters['is_discount_percent']
                if 'discount' in discount_parameters:
                    discount = discount_parameters['discount']
                if 'code' in discount_parameters:
                    coupon_code = discount_parameters['code']
                else:
                    coupon_code = ""

                if self.request.LANGUAGE_CODE == 'en-us':
                    currency = 'usd'
                elif self.request.LANGUAGE_CODE == 'it':
                    currency = 'eur'

                if is_discount_percent:
                    discount, discounted_total_price = calculate_discount_and_final_price(
                        total_price, discount, is_discount_percent)
                else:
                    discount = 0
                    discounted_total_price = total_price
                if discounted_total_price > 0:
                    user_name = self.request.user.username
                    logger.info(f"Successfully redirected to confirm order : {user_name}")
                    return redirect(reverse("confirm-order"))
                logger.info(f"100 percentage discount code used and plan linked at order summary page-post view: {student.username}")
                Payment.objects.create(stripe_id='', amount=discounted_total_price, currency=currency, status='succeeded', person=self.request.user,
                                plan=stu_plan, coupon_code=coupon_code, actual_amount=total_price, discount=discount, custom_user_session_id=custom_user_session_id)
                logger.info(f"Payment table updated at order summary page-post view: {student.username}")
                stu_pln_obj,stu_pln_obj_created= StudentsPlanMapper.plansManager.lang_code(self.request.LANGUAGE_CODE).update_or_create(
                    student=person, plan_lang=self.request.LANGUAGE_CODE, defaults={'plans': stu_plan, 'is_trial_active':False})
                logger.info(f"Plan linked with stuPlanMapper order summary page-post view: {student.username}")
                coupon_obj = Coupon.objects.filter(code = coupon_code).first()
                # student = student.student
                keys_list_1 = []
                values_list_1 = []
                if coupon_obj:
                    skip_course_dependency = coupon_obj.skip_course_dependency
                    is_course1_locked = coupon_obj.is_course1_locked
                    is_fully_paid_by_school_or_company = coupon_obj.is_fully_paid_by_school_or_company
                    if is_fully_paid_by_school_or_company == True:
                        keys_list_1, values_list_1 = auto_link_to_cohort(person,coupon_obj,self.request.LANGUAGE_CODE,stu_plan.plan_name)
                    if stu_plan.plan_name != "Community":
                        # student = person.student
                        student = getattr(person, 'student', None)
                        if student:
                            student.skip_course_dependency = skip_course_dependency
                            student.is_course1_locked = is_course1_locked
                            if coupon_obj.coupon_type == "FutureLab":
                                student.src = "future_lab"
                            elif coupon_obj.coupon_type == "Organization":
                                student.src = "company"
                                coupon_details = CouponDetail.objects.filter(coupon=coupon_obj).first()
                                if coupon_details:
                                    if coupon_details.company:
                                        student.company = coupon_details.company
                            else:
                                student.src = "general"
                            # student.discount_coupon_code = ""
                            student.save()
                try:
                    # hubspotContactupdateQueryAdded
                    logger.info(f"In hubspot plan enroll weekly parameter building for : {self.request.user.username}")
                    if stu_plan.plan_name =='Premium':
                        if stu_pln_obj_created:
                            plan_created_at=str(stu_pln_obj.created_at)
                            premium_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                        else:
                            plan_created_at=str(stu_pln_obj.modified_at)
                            premium_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                        upgrade_date=premium_plan_enroll_date
                        keys_list = ["email","upgrade_date","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount","hubspot_applied_discount_code","premium_plan_enroll_date"] + keys_list_1
                        values_list = [self.request.user.username,upgrade_date, plan_created_at, "0",coupon_code,premium_plan_enroll_date] + values_list_1
                        create_update_contact_hubspot(self.request.user.username, keys_list, values_list)
                    if stu_plan.plan_name =='Elite':
                        if stu_pln_obj_created:
                            plan_created_at=str(stu_pln_obj.created_at)
                            elite_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                        else:
                            plan_created_at=str(stu_pln_obj.modified_at)
                            elite_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                        upgrade_date=elite_plan_enroll_date
                        keys_list = ["email","upgrade_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code","elite_plan_enroll_date"] + keys_list_1
                        values_list = [self.request.user.username,upgrade_date,plan_created_at, "0",coupon_code,elite_plan_enroll_date] + values_list_1
                        create_update_contact_hubspot(self.request.user.username, keys_list, values_list)
                    logger.info(f"hubspot plan enroll weekly parameter update complete for : {self.request.user.username}")
                except Exception as ex:
                    logger.critical(f"Error at hubspot plan enroll weekly parameter update {ex} for : {self.request.user.username}")
                user_name = self.request.user.username
                self.request.session['payment_type'] = payment_type
                logger.info(f"Successfully applied the coupon code and course purchased at cost 0 : {user_name}")
                return redirect(reverse("home"))

            if payment_type == "One Time":
                logger.info(f"In one time payment at order summary page-post view: {self.request.user.username}")
                if(current_plan and current_plan.is_trial_active):
                    total_price = float(stu_plan.cost)
                else:
                    if current_plan and current_plan.plans.plan_name == "Premium" and stu_plan.plan_name == "Elite":
                        total_price = float(stu_plan.upgrade_cost)
                    else:
                        total_price = float(stu_plan.cost)
                logger.info(f"total price fetched from order summary page-post view: {self.request.user.username}")
                print(f"Coupon_code:{coupon_code}")
                if coupon_code:
                    discount_parameters = calculate_discount_parameters(
                        self.request, coupon_code)
                else:
                    discount_parameters = calculate_discount_parameters(
                        self.request)
                logger.info(f"calculated discount from order summary page-post view: {self.request.user.username}")
                if 'is_discount_percent' in discount_parameters:
                    is_discount_percent = discount_parameters['is_discount_percent']
                if 'discount' in discount_parameters:
                    discount = discount_parameters['discount']
                if 'code' in discount_parameters:
                    coupon_code = discount_parameters['code']
                else:
                    coupon_code = ""
                if self.request.LANGUAGE_CODE == 'en-us':
                    currency = 'usd'
                elif self.request.LANGUAGE_CODE == 'it':
                    currency = 'eur'

                discount, discounted_total_price = calculate_discount_and_final_price(
                    total_price, discount, is_discount_percent)
                logger.info(f"calculate_discount_and_final_price from order summary page-post view: {self.request.user.username}")
            if discounted_total_price > 0:
                user_name = self.request.user.username
                logger.info(f"Successfully redirected to confirm order : {user_name}")
                self.request.session['payment_type'] = payment_type
                return redirect(reverse("confirm-order"))
            
            logger.info(f"100 percentage discount code used and plan linked at order summary page-post view: {self.request.user.username}")
            Payment.objects.create(stripe_id='', amount=discounted_total_price, currency=currency, status='succeeded', person=self.request.user,
                                plan=stu_plan, coupon_code=coupon_code, actual_amount=total_price, discount=discount, custom_user_session_id=custom_user_session_id)
            stu_pln_obj,stu_pln_obj_created = StudentsPlanMapper.plansManager.lang_code(self.request.LANGUAGE_CODE).update_or_create(
                student=person, plan_lang=self.request.LANGUAGE_CODE, defaults={'plans': stu_plan, 'is_trial_active':False})
            user_name = self.request.user.username
            coupon_obj = Coupon.objects.filter(code = coupon_code).first()
            keys_list_1 = []
            values_list_1 = []
            if coupon_obj:
                skip_course_dependency = coupon_obj.skip_course_dependency
                is_course1_locked = coupon_obj.is_course1_locked
                is_fully_paid_by_school_or_company = coupon_obj.is_fully_paid_by_school_or_company
                if is_fully_paid_by_school_or_company == True:
                    keys_list_1, values_list_1 = auto_link_to_cohort(person,coupon_obj,self.request.LANGUAGE_CODE,stu_plan.plan_name)
                if stu_plan.plan_name != "Community":
                    # student = person.student
                    student = getattr(person, 'student', None)
                    if student:
                        student.skip_course_dependency = skip_course_dependency
                        student.is_course1_locked = is_course1_locked
                        if coupon_obj.coupon_type == "FutureLab":
                            student.src = "future_lab"
                        elif coupon_obj.coupon_type == "Organization":
                            student.src = "company"
                            coupon_details = CouponDetail.objects.filter(coupon=coupon_obj).first()
                            if coupon_details:
                                if coupon_details.company:
                                    student.company = coupon_details.company
                        else:
                            student.src = "general"
                        # student.discount_coupon_code = ""
                        student.save()
            try:
                # hubspotContactupdateQueryAdded
                logger.info(f"In hubspot plan enroll one-time parameter building for : {self.request.user.username}")
                if stu_plan.plan_name =='Premium':
                    if stu_pln_obj_created:
                        plan_created_at=str(stu_pln_obj.created_at)
                        premium_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                    else:
                        plan_created_at=str(stu_pln_obj.modified_at)
                        premium_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                    upgrade_date=premium_plan_enroll_date
                    keys_list = ["email","upgrade_date","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount","hubspot_applied_discount_code","premium_plan_enroll_date"]  + keys_list_1
                    values_list = [self.request.user.username,upgrade_date, plan_created_at, "0",coupon_code,premium_plan_enroll_date] + values_list_1
                    create_update_contact_hubspot(self.request.user.username, keys_list, values_list)
                if stu_plan.plan_name =='Elite':
                    if stu_pln_obj_created:
                        plan_created_at=str(stu_pln_obj.created_at)
                        elite_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                    else:
                        plan_created_at=str(stu_pln_obj.modified_at)
                        elite_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                    upgrade_date=elite_plan_enroll_date
                    keys_list = ["email","upgrade_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code","elite_plan_enroll_date"] + keys_list_1
                    values_list = [self.request.user.username,upgrade_date,plan_created_at, "0",coupon_code,elite_plan_enroll_date] + values_list_1
                    create_update_contact_hubspot(self.request.user.username, keys_list, values_list)
                logger.info(f"In hubspot plan enroll one-time parameter update completed for : {self.request.user.username}")
            except Exception as ex:
                logger.critical(f"Error at hubspot plan enroll one-time parameter update {ex} for : {self.request.user.username}")
            user_name = self.request.user.username
            logger.info(f"Successfully applied the coupon code and course purchased at cost 0 : {user_name}")
            return redirect(reverse("home"))
        else:
            user_name = self.request.user.username
            logger.warning(f"Plan id is missing while calling order summary page : {user_name}")
            return HttpResponseRedirect(reverse("home"))


class ConfirmOrder(UserPassesTestMixin, TemplateView):
    """
    Confirm-Order class for the Student Payment.
    """
    template_name = "payment/confirm-order.html"

    def test_func(self):
        if self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    def get(self, *args, **kwargs):
        """confirm order class get method for student payment"""
        context = {}
        student = self.request.user
        logger.info(f"In get view of confirm order page: {student.username}")
        if self.request.user.person_role == "Counselor":
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if self.request.user.person_role == "Futurely_admin":
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        coupon_code = self.request.session.get('coupon_code', None)
        plan_id = self.request.session.get('plan_id', None)
        payment_type = self.request.session.get("payment-type", None)
        if plan_id and payment_type:
            try:
                our_plan_obj = OurPlans.plansManager.lang_code(
                    self.request.LANGUAGE_CODE).get(id=plan_id)
                current_plan = StudentsPlanMapper.plansManager.lang_code(
                    self.request.LANGUAGE_CODE).filter(student=student).first()
                logger.info(f"plan obj {our_plan_obj.plan_name} Plan, ID-{plan_id} and current plan obj linked at confirm order page-get view: {student.username}")
                discount = 0
                is_discount_percent = False
                if payment_type == "Weekly":
                    print("weekly")
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.weekly_cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Community" and our_plan_obj.plan_name != "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.weekly_cost)
                            logger.info(f"upgrade cost as total price {our_plan_obj.plan_name} Plan, ID-{plan_id} at confirm order : {student.username}")
                        else:
                            total_price = float(our_plan_obj.weekly_cost)
                            logger.info(f"upgrade cost as total price {our_plan_obj.plan_name} Plan, ID-{plan_id} at confirm order : {student.username}")
                elif payment_type == "One Time":
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Community" and our_plan_obj.plan_name != "Premium" and our_plan_obj.plan_name != "Elite":
                            logger.info(f"Redirect to home page with {current_plan.plan.plan_name} from confirm order : {student.username}")
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Elite":
                            logger.info(f"Redireted to home page from confirm order : {student.username}")
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.upgrade_cost)
                        else:
                            total_price = float(our_plan_obj.cost)
                    
                if our_plan_obj:
                    context['our_plan_obj'] = our_plan_obj
                    context['actual_price'] = total_price
                    if coupon_code:
                        discount_parameters = calculate_discount_parameters(
                            self.request, coupon_code)
                    else:
                        discount_parameters = calculate_discount_parameters(
                            self.request)
                    logger.info(f"calculated total amount with coupon code in confirm order page view for : {student.username}")
                    if 'is_discount_percent' in discount_parameters:
                        is_discount_percent = discount_parameters['is_discount_percent']
                    if 'discount' in discount_parameters:
                        discount = discount_parameters['discount']
                    if 'name' in discount_parameters:
                        context['discount_name'] = discount_parameters['name']
                    else:
                        context['discount_name'] = _("Discount")
                    
                    if payment_type == "Weekly":
                        if is_discount_percent:
                            context['discount'], context['total_price'] = calculate_discount_and_final_price(
                            total_price, discount, is_discount_percent)                        
                        else:
                            context['discount'], context['total_price'] = 0, total_price
                    else:
                        context['discount'], context['total_price'] = calculate_discount_and_final_price(
                            total_price, discount, is_discount_percent)                        

                    # context['tax_calculated_object'] = calculate_tax_and_price(self.request,context['total_price'])
                    cal_tax_obj = calculate_tax_and_price(self.request,context['total_price']) # change the price
                    context['tax_calculated_object'] = cal_tax_obj
                    tax_isactive = cal_tax_obj['tax_isactive']
                    if tax_isactive:
                        context['amount_after_tax'] = cal_tax_obj['amount_after_tax']
                    else:
                        context['amount_after_tax'] = cal_tax_obj['amount_after_tax']
                    self.request.session['order_confirmed'] = True
                    user_name = self.request.user.username
                    logger.info(f"Successfully visited confirm order page : {user_name}")
            except Exception as error:
                print(error)
                user_name = self.request.user.username
                logger.critical(f"Exception at confirm order {error} : {user_name}")
                return HttpResponseRedirect(reverse("home"))
                #print('########')
                #Redirect to order summary , with Error Message
        else:
            user_name = self.request.user.username
            logger.warning(f"Plan id is missing while calling order confirm  : {user_name}")
            return HttpResponseRedirect(reverse("home"))
        return render(self.request, self.template_name, context)


class PaymentView(UserPassesTestMixin, TemplateView):
    """PaymentView class for the student payment"""
    template_name = "payment/payment.html"

    def test_func(self):
        if self.request.user.is_authenticated:
            return True
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse("home"))

    def get(self, *args, **kwargs):
        """Get method in PaymentView"""
        print("In payment view")
        context = {}
        student = self.request.user
        logger.info(f"In get view of payment page: {student.username}")
        if self.request.user.person_role == "Counselor":
            logger.info(f"Redirected to counselor dashboard from paymentview page-get for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if self.request.user.person_role == "Futurely_admin":
            logger.info(f"Redirected to counselor dashboard from paymentview page-get for : {student.username}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        coupon_code = self.request.session.get('coupon_code', None)
        plan_id = self.request.session.get('plan_id', None)
        # session['pay_confirmed_bit'] == True is set when payment is processed successfully for this session. See def create_pay_confirmed_bit(request) method
        pay_confirmed_bit = self.request.session.get('pay_confirmed_bit', False)
        tax_isactive = False
        
        if plan_id and not pay_confirmed_bit:
            logger.info(f"pay_confirmed_bit is false at payment page for : {student.username}")
            if self.request.session.get('order_confirmed', False) is False:
                return redirect('order-summary')
            try:
                our_plan_obj = OurPlans.plansManager.lang_code(
                    self.request.LANGUAGE_CODE).get(id=plan_id)
                current_plan = StudentsPlanMapper.plansManager.lang_code(self.request.LANGUAGE_CODE).filter(student=student).first()
                logger.info(f"plan_obj {our_plan_obj.plan_name} Plan, ID-{plan_id} and current plan obj linked at paymentview page-post view : {student.username}")
                #print(current_plan)
                #print("Ok2----------------------------------")
                discount = 0
                is_discount_percent = False

                payment_type = self.request.session.get("payment-type", None)
                if payment_type == "Weekly":
                    print("weekly   ----------------------------")
                    logger.info(f"In weekly payment with {our_plan_obj.plan_name} Plan, {our_plan_obj.weekly_cost} cost at payment page: {student.username}")
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.weekly_cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Community" and our_plan_obj.plan_name != "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name != "Elite":
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Elite":
                            return redirect(reverse("home"))
                        
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.weekly_cost)
                        else:
                            total_price = float(our_plan_obj.weekly_cost)
                    
                    if coupon_code:
                        discount_parameters = calculate_discount_parameters(
                            self.request, coupon_code)
                        logger.info(f"discount params fetched with {coupon_code} for : {student.username}")
                    else:
                        discount_parameters = calculate_discount_parameters(
                            self.request)
                    if 'is_discount_percent' in discount_parameters:
                        is_discount_percent = discount_parameters['is_discount_percent']
                    if 'discount' in discount_parameters:
                        discount = discount_parameters['discount']

                    if payment_type == "Weekly":
                        if is_discount_percent:
                            context['discount'], context['total_price'] = calculate_discount_and_final_price(
                                total_price, discount, is_discount_percent)
                        else:
                            context['discount'], context['total_price'] = 0, total_price
                    else:
                        context['discount'], context['total_price'] = calculate_discount_and_final_price(
                                total_price, discount, is_discount_percent)
                    logger.info(f"Discount price-{context['discount']}, total price-{context['total_price']} for : {student.username}")
                    tax_calculated_object=calculate_tax_and_price(self.request,context['total_price'])
                    context["tax_calculated_object"] = tax_calculated_object
                    # cal_tax_obj = calculate_tax_and_price(self.request,total_price) # change the price
                    tax_isactive = tax_calculated_object['tax_isactive']
                    if tax_isactive:
                        context['amount_after_tax'] = tax_calculated_object['amount_after_tax']
                    else:
                        context['amount_after_tax'] = tax_calculated_object['amount_after_tax']
                    logger.info(f"price , discount and tax is calculated at payment view page: {student.username}")
                    if self.request.LANGUAGE_CODE == 'en-us':
                        context['publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY_FUTURELY
                        context['lang_code'] = "en"
                        # product_id = "prod_L4sMih7QgaGpjN" #Test
                        # product_id = "prod_L6rC6LRQeG6hiy" #Main id
                        product_id = settings.PRODUCT_ID_EN
                        currency = 'usd'
                        api_key = settings.STRIPE_API_KEY_FUTURELY
                        
                    elif self.request.LANGUAGE_CODE == 'it':
                        context['publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY_ORIENTAMI
                        context['lang_code'] = "it"
                        # product_id = "prod_Lt8pXOVL7ewCyQ" #Test
                        # product_id = "prod_Lt8X677gCPAtT7" #Main id
                        product_id = settings.PRODUCT_ID_IT
                        currency = 'eur'
                        api_key = settings.STRIPE_API_KEY_ORIENTAMI

                    ###############################################################
                    stripe.api_key = api_key
                    amount_for_stripe_price = context['amount_after_tax']
                    stripe_price_id = ""
                    st_p_obj = stripe.Price.list(product=product_id,lookup_keys = [f"{our_plan_obj.plan_name}{amount_for_stripe_price}",])
                    if len(st_p_obj['data']) <= 0:
                        unit_amount_decimal = round(amount_for_stripe_price*100, 2)
                        st_p = stripe.Price.create(
                        unit_amount_decimal=f"{unit_amount_decimal}",
                        currency=currency,
                        lookup_key = f"{our_plan_obj.plan_name}{amount_for_stripe_price}",
                        recurring={"interval": "week"},
                        product=product_id,
                        )
                        stripe_price_id = st_p.id
                        logger.info(f"strpe price-{amount_for_stripe_price} is created at payment page: {student.username}")
                    else:
                        stripe_price_id = st_p_obj['data'][0]['id']
                        logger.info(f"stripe price is used at payment page: {student.username}")
                    print("Stripe Price ID : ", stripe_price_id)
                    self.request.session['stripe_price_id'] = stripe_price_id
                    ###############################################################
                else:
                    logger.info(f"In one-time payment with {our_plan_obj.plan_name} Plan, {our_plan_obj.cost} cost at payment page: {student.username}")
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Community" and our_plan_obj.plan_name != "Premium" and our_plan_obj.plan_name != "Elite":
                            logger.info(f"Redirected to home page from payment page for : {student.username}")
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name != "Elite":
                            logger.info(f"Redirected to home page from payment page for : {student.username}")
                            return redirect(reverse("home"))
                        if current_plan and current_plan.plans.plan_name == "Elite":
                            logger.info(f"Redirected to home page from payment page for : {student.username}")
                            return redirect(reverse("home"))
                        
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.upgrade_cost)
                            logger.info(f"fetched the weekly upgrade cost {total_price} with {current_plan.plans.plan_name} Plan for : {student.username}")
                        else:
                            total_price = float(our_plan_obj.cost)
                    if coupon_code:
                        discount_parameters = calculate_discount_parameters(
                            self.request, coupon_code)
                        logger.info(f"discount params fetched with {coupon_code} coupon code for : {student.username}")
                    else:
                        discount_parameters = calculate_discount_parameters(
                            self.request)
                    logger.info(f"fetched the discount parameters with {coupon_code} coupon code in payment page for : {student.username}")
                    if 'is_discount_percent' in discount_parameters:
                        is_discount_percent = discount_parameters['is_discount_percent']
                    if 'discount' in discount_parameters:
                        discount = discount_parameters['discount']
                    context['discount'], context['total_price'] = calculate_discount_and_final_price(
                        total_price, discount, is_discount_percent)
                    logger.info(f"discount-price {context['discount']}, total-price {context['total_price']} with {coupon_code} coupon code at payment page for : {student.username}")
                    tax_calculated_object=calculate_tax_and_price(self.request,context['total_price'])
                    
                    context["tax_calculated_object"] = tax_calculated_object
                    tax_isactive = tax_calculated_object['tax_isactive']
                    if tax_isactive:
                        context['amount_after_tax'] = tax_calculated_object['amount_after_tax']
                    else:
                        context['amount_after_tax'] = tax_calculated_object['amount_after_tax']
                    logger.info(f"total tax amount {context['amount_after_tax']} with plan ID-{plan_id} at payment page for : {student.username}")
                user_name = self.request.user.username
                context['name'] = self.request.user.first_name + \
                    " " + self.request.user.last_name
                context['email'] = self.request.user.email
                if self.request.LANGUAGE_CODE == 'en-us':
                    context['publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY_FUTURELY
                    context['lang_code'] = "en"
                elif self.request.LANGUAGE_CODE == 'it':
                    context['publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY_ORIENTAMI
                    context['lang_code'] = "it"

                logger.info(f"Payment get view executed successfully : {user_name}")
                #print("Payment get view executed successfully")
            except Exception as exerr:
                user_name = self.request.user.username
                logger.critical(f"Error to load payment page {exerr}: {user_name}")
                print(exerr)
                return HttpResponseRedirect(reverse("home"))
                #redirect to order_confirm page with error message
            return render(self.request, self.template_name, context)
        else:
            user_name = self.request.user.username
            logger.warning(f"Plan id is missing while calling payment page : {user_name}")
            return HttpResponseRedirect(reverse("home"))

def direct_checkout_view(request, plan_id=None, coupon_code=None):
    """Direct-checkout-view function for the direct payment"""
    context = {}
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
    selected_payment_type = request.GET.get('payment_type','One Time')
    request.session['selected_payment_type'] = selected_payment_type
    if plan_id is None:
        context['error_msg_direct_payment_page'] = _("You entered the wrong plan, please check the plan again")
        logger.warning(f"Plan id is None : {custom_user_session_id}")
        return render(request, "payment/direct-payment.html", context)
    if request.LANGUAGE_CODE != 'it':
        logger.warning(f"language code must be Italian : {custom_user_session_id}")
        return HttpResponseRedirect(reverse("index"))

    if request.LANGUAGE_CODE == 'en-us':
        context['publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY_FUTURELY
        context['lang_code'] = "en" 
        # product_id = "prod_L6rC6LRQeG6hiy"
        # product_id = "prod_L4sMih7QgaGpjN" #Test Product
        product_id = settings.PRODUCT_ID_EN
        currency = 'usd'
        #To add product id for prod
        api_key = settings.STRIPE_API_KEY_FUTURELY
    elif request.LANGUAGE_CODE == 'it':
        context['publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY_ORIENTAMI
        context['lang_code'] = "it"
        # product_id = "prod_Lt8X677gCPAtT7"
        # product_id = "prod_Lt8pXOVL7ewCyQ" # Test Product
        product_id = settings.PRODUCT_ID_IT
        currency = 'eur'
        api_key = settings.STRIPE_API_KEY_ORIENTAMI

    stripe.api_key = api_key
    # print(stripe.Price.list(limit=3))
    # info_price = stripe.Price.retrieve(
    #      "price_1KLn67KIeNIVIx3fHwecLDTI",)
    # print(info_price)
    # info = stripe.Invoice.retrieve("in_1KQ3wwKIeNIVIx3fAotMnMGQ")
    # print(info)
    # print(info.id)
    # now = datetime.now()
    # now_plus_10 = now + timedelta(minutes = 10)
    # date_time_stamp = datetime.timestamp(now_plus_10)
    # invoice_update = stripe.Invoice.modify(data_object["id"], next_payment_attempt=date_time_stamp)
    # print("invoice_update : ", invoice_update)
    # print("---------------------")
    context['plan_id'] = plan_id
    try:
        our_plan_obj = OurPlans.plansManager.lang_code(request.LANGUAGE_CODE).filter(id=int(plan_id)).first()
        if our_plan_obj:
            weekly_total_price = float(our_plan_obj.weekly_cost)
            onetime_total_price = float(our_plan_obj.cost)
            is_discount_percent = False
            try:
                if coupon_code and Coupon.objects.filter(code__iexact=coupon_code).exists():
                    if our_plan_obj.plan_name == "Premium":
                        coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"), Q(discount_type="Percentage"))
                    elif our_plan_obj.plan_name == "Elite":
                        coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"), Q(discount_type="Percentage"))
                    logger.info(f"fetched the coupon obj in direct checkout with {coupon_code} coucpon code")
                    if coupon_obj:
                        request.session['coupon_code'] = coupon_code
                        discount_type = coupon_obj.discount_type
                        if discount_type == "Percentage":
                            is_discount_percent = True
                        discount = float(coupon_obj.discount_value)
                    if is_discount_percent:
                        weekly_discount, weekly_total_price = calculate_discount_and_final_price(weekly_total_price, discount, is_discount_percent)
                        logger.info(f"weekly Payment calculate discount-amount-{weekly_discount} and final-amount-{weekly_total_price} with {coupon_code} coupon code at direct-checkout view page")
                        one_time_discount, onetime_total_price = calculate_discount_and_final_price(onetime_total_price, discount, is_discount_percent)
                        logger.info(f"OneTime Payment calculate discount-amount-{one_time_discount} and final-amount-{onetime_total_price} with {coupon_code} coupon code at direct-checkout view page")

            except Exception as error:
                print(f"Exception error in coupon code : {error}")
                logger.critical(f"Error in direct payment : {error}")
            finally:
                context['is_discount_percent'] = is_discount_percent
                context['onetime_total_price'] = onetime_total_price
                context['weekly_total_price'] = weekly_total_price
            request.session['weekly_total_price'] = weekly_total_price
            request.session['onetime_total_price'] = onetime_total_price
            request.session['is_discount_percent'] = is_discount_percent
            
            cst = float(context['weekly_total_price'])
            #cst = float(our_plan_obj.weekly_cost)
            stripe_price_id = ""
            st_p_obj = stripe.Price.list(product=product_id,lookup_keys = [f"{our_plan_obj.plan_name}{cst}",])
            if len(st_p_obj['data']) <= 0:
                st_p = stripe.Price.create(
                unit_amount_decimal=f"{cst*100}",
                currency=currency,
                lookup_key = f"{our_plan_obj.plan_name}{cst}",
                recurring={"interval": "week"},
                product=product_id,
                )
                stripe_price_id = st_p.id
            else:
                stripe_price_id = st_p_obj['data'][0]['id']

            request.session['stripe_price_id'] = stripe_price_id
            # print (stripe.Price.list(product="prod_L2uVhsJoGbu2U4"))
            context['plan_obj'] = our_plan_obj
            context['payment_subscription_type'] = pay_modl.PAYMENT_SUBSCRIPTION_TYPE
            logger.info(f"at direct payment page render successfully : {custom_user_session_id}")
        else:
            context['error_msg_direct_payment_page'] = _("You entered the wrong plan, please check the plan again")
            logger.warning(f"Error at Direct-checkout-view page : entered the wrong plan id")
    except Exception as ex:
        print(ex)
        context['error_msg_direct_payment_page'] = _("You entered the wrong plan, please check the plan again")
        logger.critical(f"Error at Direct-checkout-view page : {ex}")
    return render(request, "payment/direct-payment.html", context)


def direct_payment_intent(request):
    """direct-payment-intent function for the create payment intent and create objects in payment table with payment type"""
    try:
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
        if request.LANGUAGE_CODE == 'en-us':
            currency = 'usd'
            api_key = settings.STRIPE_API_KEY_FUTURELY
        elif request.LANGUAGE_CODE == 'it':
            currency = 'eur'
            api_key = settings.STRIPE_API_KEY_ORIENTAMI
        
        stripe.api_key = api_key
        data = json.loads(request.body)
        email_id = data['email_id']
        card_holder_name = data["card_holder_name"]
        if(email_id == "" or card_holder_name == ""):
            logger.warning(f"Error in direct payment intent of email and card holder name empty : {custom_user_session_id}")
            return JsonResponse({'error': _('You must need to enter the email id and name')}, status=200, safe=False)
        
        plan_id = data['plan_id']
        payment_subscription_type = data['subscription_type']
        our_plan_obj = OurPlans.plansManager.lang_code(
                    request.LANGUAGE_CODE).get(id=plan_id)
        stu_obj = Person.objects.filter(username=email_id)
        is_email_exists = False
        if(stu_obj.count()>0):
            is_email_exists = True
            stu_obj = stu_obj.first()
            payment_user_obj = Payment.objects.filter(person=stu_obj, plan__plan_lang=request.LANGUAGE_CODE, status__in=["active","succeeded"]).exclude(plan__plan_name="Community")
        else:
            payment_user_obj = Payment.objects.filter(payment_email_id=email_id, plan__plan_lang=request.LANGUAGE_CODE, status__in=["active","succeeded"])
        
        total_no_weeks = our_plan_obj.weekly_cost_duration
        stripe_price_id = request.session['stripe_price_id']
        is_discount_percent = request.session.get('is_discount_percent')
        weekly_total_price = request.session.get('weekly_total_price')
        onetime_total_price = request.session.get('onetime_total_price')
        coupon_code = request.session.get("coupon_code", "")
        if payment_user_obj.count() <= 0:
            print("Create payment intent")
            if(payment_subscription_type == "Weekly"):
                if is_discount_percent:
                    total_price = float(weekly_total_price)
                else:
                    total_price = float(our_plan_obj.weekly_cost)
                actual_amount = float(our_plan_obj.weekly_cost)
                discount_amount = round(actual_amount - total_price, 2)
                actual_price = round(total_price * total_no_weeks,2)
                # Create a customer For Subscription.
                customer = stripe.Customer.create(
                    email=email_id,
                    name=card_holder_name,
                    description="This Customer For the Subbscription testing!",
                )
                # Create the subscription
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{
                        'price': stripe_price_id,
                    }],
                    payment_behavior='default_incomplete',
                    expand=['latest_invoice.payment_intent'],
                )
                custom_user_session_id = request.session.get(
                        'CUSTOM_USER_SESSION_ID', '')
                pay_obj = Payment.objects.create(stripe_id=subscription.id, 
                            coupon_code=coupon_code,
                            discount = discount_amount,
                            amount=total_price, currency=currency,
                            status=subscription.status,plan=our_plan_obj,  
                            actual_amount=actual_price,
                            custom_user_session_id=custom_user_session_id,
                            payment_person_type = "Direct",
                            payment_subscription_type = payment_subscription_type,
                            payment_subscription_duration = our_plan_obj.weekly_cost_duration,
                            payment_email_id = email_id,
                            card_holder_name = card_holder_name,
                            )
                # tot_amount = subscription["items"]["data"][0]["plan"]["amount"]
                pay_sub_obj = PaymentSubscriptionDetails.objects.create(
                    payment_id=pay_obj,
                    intent_id_of_invoice=subscription["latest_invoice"]["id"],
                    invoice_status=subscription["latest_invoice"]["status"],
                    amount=total_price,
                    subscription_event_type="subscription",
                )
                if(is_email_exists):
                    pay_obj.person = stu_obj
                    pay_obj.save()
                print("Payment Intent created and redirected to webhook response...")
                logger.info(f"Payment Intent created and redirected to webhook response : {email_id}")
                print("--------")
                return JsonResponse({'clientSecret': subscription.latest_invoice.payment_intent.client_secret, 'payment_intent_id': subscription.id, "is_email_exists": is_email_exists, "total_price": total_price}, safe=False)
            else:
                if is_discount_percent:
                    total_price = float(onetime_total_price)
                else:
                    total_price = int(our_plan_obj.cost)
                actual_amount = int(our_plan_obj.cost)
                discount_amount = round(actual_amount - total_price, 2)
                intent = stripe.PaymentIntent.create(
                    api_key=api_key,
                    amount=int(total_price * 100),
                    currency=currency,
                    payment_method_types=['card'],
                )
                custom_user_session_id = request.session.get(
                        'CUSTOM_USER_SESSION_ID', '')
                pay_obj = Payment.objects.create(stripe_id=intent.id,
                            coupon_code=coupon_code, 
                            amount=total_price, currency=currency, 
                            status=intent.status,plan=our_plan_obj,  
                            actual_amount=actual_amount,
                            discount=discount_amount,
                            custom_user_session_id=custom_user_session_id,
                            payment_person_type = "Direct",
                            payment_subscription_type = payment_subscription_type,
                            payment_email_id = email_id,
                            card_holder_name = card_holder_name,
                            )
                if(is_email_exists):
                    pay_obj.person = stu_obj
                    pay_obj.save()
                logger.info(f"Payment Intent created and redirected to webhook response : {email_id}")
                return JsonResponse({'clientSecret': intent.client_secret, 'payment_intent_id': intent.id, "is_email_exists": is_email_exists, "total_price": total_price}, safe=False)
        else:
            print("You have already paid, Please login to check course details...")
    except Exception as ex:
        print(ex)
        logger.error(f"Error in direct payment intent : {ex}")
    return JsonResponse({'error': _('It seems payment is already processed, or something went wrong. Press the Skip button below to go to your dashboard and if you do not see a payment success message there, then try again')}, status=200, safe=False)

@login_required()
def create_payment(request):
    """Create-payment-intent for the student payment"""
    # import ipdb
    # ipdb.set_trace()
    student = request.user
    card_body_data = json.loads(request.body)
    logger.info(f"In create payment intent : {student.username}")
    if request.LANGUAGE_CODE == 'en-us':
        currency = 'usd'
        api_key = settings.STRIPE_API_KEY_FUTURELY
    elif request.LANGUAGE_CODE == 'it':
        currency = 'eur'
        api_key = settings.STRIPE_API_KEY_ORIENTAMI

    try:
        """session['pay_confirmed_bit'] == True is set when payment is processed successfully for this session. See def create_pay_confirmed_bit(request) method"""
        pay_confirmed_bit = request.session.get('pay_confirmed_bit', False)
        if pay_confirmed_bit == False:
            total_price = 0
            final_total = 0
            plan_id = request.session.get('plan_id', None)
            coupon_code = request.session.get('coupon_code', None)
            payment_type = request.session.get('payment-type', None)
            stripe_price_id = request.session.get('stripe_price_id', None)
            is_upgrade = request.session.get('is_upgrade', False)
            discount = 0
            discount_calculated = 0
            is_discount_percent = False
            custom_user_session_id = request.session.get(
                'CUSTOM_USER_SESSION_ID', '')
            if plan_id:
                student = request.user
                current_plan = StudentsPlanMapper.plansManager.lang_code(
                    request.LANGUAGE_CODE).filter(student=student).first()
                our_plan_obj = OurPlans.plansManager.lang_code(
                    request.LANGUAGE_CODE).get(id=plan_id)
                logger.info(f"plan_obj {our_plan_obj.plan_name} Plan, ID-{plan_id} and current plan obj linked at create payment intent : {student.username}")

                ######### Add ###########
                if payment_type == "Weekly":
                    current_duration = 0
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.weekly_cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.weekly_cost)
                            current_duration = current_plan.plans.weekly_cost_duration
                            logger.info(f"updated cost fetched at create payment intent : {student.username}")
                        else:
                            total_price = float(our_plan_obj.weekly_cost)

                    if coupon_code:
                        discount_parameters = calculate_discount_parameters(
                            request, coupon_code)
                        logger.info(f"discount params fetched with {coupon_code} for : {student.username}")
                    else:
                        discount_parameters = calculate_discount_parameters(request)
                        coupon_code = ''
                    logger.info(f"fetched discount parameters in create payment intent for : {student.username}")
                    if 'is_discount_percent' in discount_parameters:
                        is_discount_percent = discount_parameters['is_discount_percent']
                    if 'discount' in discount_parameters:
                        discount = discount_parameters['discount']
                    if 'code' in discount_parameters:
                        coupon_code = discount_parameters['code']
                    else:
                        coupon_code = ""
                    if is_discount_percent:
                        discount_calculated, final_total = calculate_discount_and_final_price(
                            total_price, discount, is_discount_percent)
                        logger.info(f"discount calculated at create payment intent page view for : {student.username}")
                    else:
                        discount_calculated = 0
                        final_total = total_price
                    #print("All good before tax")
                    tax_calculated_object=calculate_tax_and_price(request,final_total)
                
                    if tax_calculated_object['tax_isactive'] == True:
                        amount_after_tax=tax_calculated_object['amount_after_tax']
                        tax_amount=tax_calculated_object['total_tax_amount']
                    else:
                        amount_after_tax=final_total
                        tax_amount=0.00
                    logger.info(f"final amount after tax {amount_after_tax} and tax_amount-{tax_amount} at create_payment for : {student.username}")
                    
                    # total_no_weeks = our_plan_obj.weekly_cost_duration
                    # total_price = float(our_plan_obj.weekly_cost)
                    total_no_weeks = our_plan_obj.weekly_cost_duration
                    actual_price = round(amount_after_tax * total_no_weeks,2)
                    # Create a customer For Subscription.
                    print(f"username: {student.username}, name: {student.first_name} {student.last_name}")
                    card_holder_name = card_body_data['name_on_card']
                    customer = stripe.Customer.create(
                        email=student.email,
                        name=card_holder_name,
                        description="This Customer For the Subbscription testing!",
                    )
                    
                    logger.info(f"customer created for subscription at create intent: {student.username}")
                    # Create the subscription
                    subscription = stripe.Subscription.create(
                        customer=customer.id,
                        items=[{
                            'price': stripe_price_id,
                        }],
                        payment_behavior='default_incomplete',
                        expand=['latest_invoice.payment_intent'],
                    )
                    logger.info(f"subscription created at create intent: {student.username}")
                    # print("subscription: ", subscription)
                    custom_user_session_id = request.session.get(
                            'CUSTOM_USER_SESSION_ID', '')
                    if is_upgrade:
                        pay_sub_duration = total_no_weeks - current_duration
                        pay_obj = Payment.objects.create(stripe_id=subscription.id,
                                    person=student,
                                    amount=amount_after_tax, currency=currency,
                                    status=subscription.status,plan=our_plan_obj,
                                    coupon_code=coupon_code,
                                    actual_amount=actual_price,
                                    custom_user_session_id=custom_user_session_id,
                                    payment_subscription_type = "Weekly",
                                    payment_subscription_duration = pay_sub_duration,
                                    payment_email_id = student.username,
                                    card_holder_name = card_holder_name,
                                    discount=discount_calculated,
                                    )
                        logger.info(f"subscription object create in payment table and upgraded Premium Plan to Elite Plan, ID-{plan_id}: {student.username}")
                    else:
                        pay_obj = Payment.objects.create(stripe_id=subscription.id,
                                    person=student, 
                                    amount=amount_after_tax, currency=currency,
                                    status=subscription.status,plan=our_plan_obj,
                                    coupon_code=coupon_code,
                                    actual_amount=actual_price,
                                    custom_user_session_id=custom_user_session_id,
                                    payment_subscription_type = "Weekly",
                                    payment_subscription_duration = our_plan_obj.weekly_cost_duration,
                                    payment_email_id = student.username,
                                    card_holder_name = card_holder_name,
                                    discount=discount_calculated,
                                    )
                        logger.info(f"subscription objects create with {our_plan_obj.plan_name} Plan, ID-{plan_id} in payment table at create intent: {student.username}")
                    tot_amount = subscription["items"]["data"][0]["plan"]["amount"]
                    pay_sub_obj = PaymentSubscriptionDetails.objects.create(
                        payment_id=pay_obj,
                        intent_id_of_invoice=subscription["latest_invoice"]["id"],
                        invoice_status=subscription["latest_invoice"]["status"],
                        amount=amount_after_tax,
                        subscription_event_type="subscription",
                    )
                    logger.info(f"subscription details table is updated at create intent: {student.username}")
                    print("Payment Intent created and redirected to webhook response...")
                    logger.info(f"Payment Intent created and redirected to webhook response : {student.username}")
                    print("---------------------")
                    return JsonResponse({'clientSecret': subscription.latest_invoice.payment_intent.client_secret, 'payment_intent_id': subscription.id}, safe=False)

                else:
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.upgrade_cost)
                            logger.info(f"fetched upgraded cost in create payment intent page view : {student.username}")
                        else:
                            total_price = float(our_plan_obj.cost)

                    if coupon_code:
                        discount_parameters = calculate_discount_parameters(
                            request, coupon_code)
                    else:
                        discount_parameters = calculate_discount_parameters(request)
                        coupon_code = ''
                    logger.info(f"discount parameters fetched {coupon_code} at create payment intent : {student.username}")
                    if 'is_discount_percent' in discount_parameters:
                        is_discount_percent = discount_parameters['is_discount_percent']
                    if 'discount' in discount_parameters:
                        discount = discount_parameters['discount']
                    if 'code' in discount_parameters:
                        coupon_code = discount_parameters['code']
                    else:
                        coupon_code = ""
                    discount_calculated, final_total = calculate_discount_and_final_price(
                        total_price, discount, is_discount_percent)
                    #print("All good before tax")
                    tax_calculated_object=calculate_tax_and_price(request,final_total)
                
                    if tax_calculated_object['tax_isactive'] == True:
                        amount_after_tax=tax_calculated_object['amount_after_tax']
                        tax_amount=tax_calculated_object['total_tax_amount']
                    else:
                        amount_after_tax=final_total
                        tax_amount=0.00
                    

                    intent = stripe.PaymentIntent.create(
                        api_key=api_key,
                        amount=int(amount_after_tax * 100),
                        currency=currency,
                        payment_method_types=['card'],
                    )
                    logger.info(f"intent created for one time at create intent view: {student.username}")
                    pay_obj = Payment.objects.create(stripe_id=intent.id,
                            person=request.user,
                            amount=amount_after_tax,
                            tax_amount=tax_amount,
                            currency=currency,
                            status=intent.status,
                            plan=our_plan_obj,
                            coupon_code=coupon_code,
                            actual_amount=total_price,
                            discount=discount_calculated,
                            custom_user_session_id=custom_user_session_id)
                    logger.info(f"Payment obj is created at create intent view for : {student.username}")
                    #request.session['coupon_code'] = coupon_code
                    if tax_calculated_object['tax_isactive'] == True:
                        all_taxes = tax_calculated_object['all_taxes']
                        for tax in all_taxes:
                            tax_amount_actual=tax.cal_tax_amount(final_total)
                            TaxCollection.objects.create(payment_id=pay_obj, tax_id=tax, tax_amount=tax_amount_actual)
                        logger.info(f"TaxCollections created at create payment intent with one time payment for : {student.username}")
                    user_name = request.user.username
                    logger.info(f"Payment intent is created : {user_name}")
                    return JsonResponse({'clientSecret': intent.client_secret, 'payment_intent_id': intent.id}, safe=False)
            else:
                user_name = request.user.username
                logger.warning(f"Plan id is missing while creating payment intent : {user_name}")
                return JsonResponse({'error': "Error"}, status=200, safe=False)
        else:
            user_name = request.user.username
            logger.warning(f"Payment has already been processed : {user_name}")
            return JsonResponse({'error': 'Payment has already been processed'}, status=200, safe=False)
    except Exception as e:
        #print(e)
        logger.critical(f"Error to create payment intent {e}: {student.username}")
        return JsonResponse({'error': str(e)}, status=200, safe=False)


@require_POST
@csrf_exempt
def payment_intent_webhook(request):
    """Stripe Webhook callback"""
    logger.info(f"In Payment intent webhook : {request}")
    account = request.GET.get("account", '')
    if account == 'futurely':
        # endpoint_secret = 'whsec_o5xFAYAX3u352ifkEFejuGqYUrzAEoqe' # Test Secret key 
        # endpoint_secret = 'whsec_zBTY8kh7WN1wMgsx1vSkiR66I2FpWnaJ'
        endpoint_secret = settings.ENDPOINT_SECRET_IT
        api_key = settings.STRIPE_API_KEY_FUTURELY

    elif account == 'orientami':
        # endpoint_secret = 'whsec_HjjJ9xRQrBDWlT5a1tjRZN3T6VplDdBW' # Test Secret key
        # endpoint_secret = 'whsec_cesi6Np5IHBGuzrQRYr96UpJrl4E9sgn'
        endpoint_secret = settings.ENDPOINT_SECRET_IT
        api_key = settings.STRIPE_API_KEY_ORIENTAMI


    payload = request.body
    logger.info(f"In Payment intent webhook-Payload : {payload}")
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    logger.info(f"In Payment intent webhook-sig_header : {sig_header}")
    event = None
    data = None

    try:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret)

        except ValueError as e:
            # Invalid payload
            logger.critical(f"Invalid payload webhook : {e}")
            return HttpResponse({str(e)}, content_type='application/json', status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.critical(f"Invalid signature at webhook : {e}")
            return HttpResponse({str(e)}, content_type='application/json', status=400)
        custom_user_session_id = ''
        admin_email = "rohit@myfuturely.com"
        obj_student = None
        if event.type == 'payment_intent.succeeded':
            print("payment_intent.succeeded")
            data_object = event["data"]["object"]
            payment_type = ""
            try:
                payment_type = data_object.description
            except Exception as ex:
                print("error")
                print(ex)
            if (payment_type != None) and ("Subscription" in payment_type or "subscription" in payment_type):
                print("In PaymentIntent Found as subscription!!")
            else:
                try:
                    intent_id = data_object.id
                    status = data_object.status
                    obj = Payment.objects.get(stripe_id=intent_id)
                    obj_plan = obj.plan
                    plan_lang = obj_plan.plan_lang
                    obj.status = status
                    obj.save()
                    is_registred = "register"
                    email = ""
                    if(obj.person is not None):
                        is_registred = "login"
                        obj_student = obj.person
                        email = obj_student.username
                        stu_pln_obj,stu_pln_obj_created=StudentsPlanMapper.plansManager.lang_code(plan_lang).update_or_create(
                            student=obj_student, plan_lang=plan_lang, defaults={'plans': obj_plan, 'is_trial_active':False})
                        Stu_Notification.objects.create(student=obj_student, title=_(
                            "Thank you. Your payment has been processed successfully"))
                        create_custom_event(request, 5, custom_user_session_id=custom_user_session_id, meta_data={
                                            'plan': obj_plan.plan_name, 'plan_title': obj_plan.title, 'student': obj_student.email})
                        coupon_code = obj.coupon_code
                        coupon_obj = Coupon.objects.filter(code = coupon_code).first()
                        student = obj_student.student
                        keys_list_1 = []
                        values_list_1 = []
                        if coupon_obj:
                            keys_list_1, values_list_1 = auto_link_to_cohort(obj_student,coupon_obj,plan_lang,obj_plan.plan_name)
                            if coupon_obj.coupon_type == "FutureLab":
                                student.src = "future_lab"
                            elif coupon_obj.coupon_type == "Organization":
                                student.src = "company"
                                coupon_details = CouponDetail.objects.filter(coupon=coupon_obj).first()
                                if coupon_details:
                                    if coupon_details.company:
                                        student.company = coupon_details.company
                            else:
                                student.src = "general"
                        # student.discount_coupon_code = ""
                        student.save()
                        obj.payment_email_id = obj_student.username
                        try:
                            # hubspotContactupdateQueryAdded
                            logger.info(f"In hubspot plan enroll intent webhook parameter building for : {email}")
                            if obj_plan.plan_name =='Premium':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    premium_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    premium_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                                upgrade_date=premium_plan_enroll_date
                                keys_list = ["email","upgrade_date","premium_plan_enroll_date","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount","hubspot_applied_discount_code"] + keys_list_1
                                values_list = [email,upgrade_date,premium_plan_enroll_date, plan_created_at, obj.amount,obj.coupon_code] + values_list_1
                                create_update_contact_hubspot(email, keys_list, values_list)
                            if obj_plan.plan_name =='Elite':
                                if stu_pln_obj_created:
                                    plan_created_at=str(stu_pln_obj.created_at)
                                    elite_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                                else:
                                    plan_created_at=str(stu_pln_obj.modified_at)
                                    elite_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                                upgrade_date=elite_plan_enroll_date
                                keys_list = ["email","upgrade_date","elite_plan_enroll_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code"] + keys_list_1
                                values_list = [email,upgrade_date,elite_plan_enroll_date,plan_created_at, obj.amount,obj.coupon_code] + values_list_1
                                create_update_contact_hubspot(email, keys_list, values_list)
                            logger.info(f"In hubspot plan enroll intent webhook parameter update completed for : {email}")
                        except Exception as ex:
                            logger.error(f"Error at hubspot plan enroll intent webhook parameter update {ex} for : {email}")
                    else:
                        email = obj.payment_email_id
                    try:
                        if request.LANGUAGE_CODE == 'it':
                            template_nam = "payment/email_templates/one-time-payment-success.html"
                            subject = "Futurely | Pagamento avvenuto con successo"
                            ctx = {
                                "email": email,
                                "domain": request.get_host(),
                                "user": obj.card_holder_name,
                                "protocol": 'https',
                                "url_type": is_registred,
                                "lang_code": request.LANGUAGE_CODE,
                                "amount": obj.amount,
                                "plan_name": obj.plan.plan_name,
                                "message": _("Thank you. Your payment has been processed successfully"),
                            }
                            html_msg = get_template(template_nam).render(ctx)
                            fromEmail = settings.EMAIL_HOST_USER
                            msg = EmailMessage(subject, html_msg, fromEmail, [email, admin_email])
                            msg.content_subtype = "html"
                            msg.send()
                            logger.info(f"Email sent for payment succeeded : {email}")
                            print(f"----Mail Send-----")
                        else:
                            #Waiting for template in Eng Lang
                            print("")
                        logger.info(f"Payment Succeeded : {email}")
                    except Exception as ex:
                        logger.warning(f"Error in send email : {ex}")
                except Exception as ex:
                    logger.warning(f"Error in webhook Payment Intent : {data_object.id} : Error: {ex}")
                    print(ex)
        
        elif event.type == 'payment_intent.processing':
            print("payment_intent.processing")
            print("----------")
            try:
                data_object = event.data.object
                payment_type = data_object.description
                intent_id = data_object.id
                status = data_object.status
                
                if (payment_type != None) and ("Subscription" in payment_type or "subscription" in payment_type):
                    print("In PaymentIntent Found as subscription!!")
                else:
                    obj = Payment.objects.get(stripe_id=intent_id)
                    obj.status = status
                    obj.save()
                    if(obj.person is not None):
                        obj_student = obj.person
                        Stu_Notification.objects.create(student=obj_student, title=_(
                            "Your payment is being processed. We will let you know as soon as it is received"))
                        logger.info(f"Payment in process : {obj_student.username}")
                    else:
                        logger.info(f"Payment in process : {obj.payment_email_id}")
            except Exception as ex:
                print(ex)
                logger.warning(f"Error To send email : {ex}")

        elif event.type == 'payment_intent.payment_failed':
            print("payment_intent.payment_failed")
            email = ""
            name = ""
            try:
                data_object = event.data.object
                payment_type = data_object.description
                intent_id = data_object.id
                status = data_object.status
                
                if (payment_type != None) and ("Subscription" in payment_type or "subscription" in payment_type):
                    print("In PaymentIntent Found as subscription!!")
                else:
                    obj = Payment.objects.get(stripe_id=intent_id)
                    obj.status = status
                    obj.save()
                    if(obj.person is not None):
                        obj_student = obj.person
                        Stu_Notification.objects.create(student=obj_student, title=_(
                            "Your payment is declined. Please check with your bank and try again"))
                        email = obj_student.username
                        logger.warning(f"Payment failed : {email}")
                    else:
                        email = obj.payment_email_id
                        logger.warning(f"Payment failed : {email}")

                    try:
                        if request.LANGUAGE_CODE == 'it':
                            template_nam = "payment/email_templates/one-time_payment_failed.html"
                            subject = "Futurely| Pagamento fallito"
                            ctx = {
                                "email": email,
                                "domain": request.get_host(),
                                "user": name,
                                "protocol": '',
                                "url_type": "",
                                "lang_code": request.LANGUAGE_CODE,
                                "amount": obj.amount,
                                "plan_name": obj.plan.plan_name,
                                "message": _("Your payment is declined. Please check with your bank and try again"),
                            }
                            html_msg = get_template(template_nam).render(ctx)
                            fromEmail = settings.EMAIL_HOST_USER
                            msg = EmailMessage(subject, html_msg, fromEmail, [email, admin_email])
                            msg.content_subtype = "html"
                            msg.send()
                            logger.info(f"Email sent for payment failed: {email}")

                    except Exception as ex:
                        print(ex)
                        logger.error(f"Error To send email : {ex}")
            except Exception as ex:
                print(ex)
                logger.critical(f"Payment Failed : {ex}")

        elif event.type == 'payment_intent.requires_action':
            print("payment_intent.requires_action")
            try:
                data_object = event.data.object
                payment_type = data_object.description
                intent_id = data_object.id
                status = data_object.status
                if (payment_type != None) and ("Subscription" in payment_type or "subscription" in payment_type):
                    print("In PaymentIntent Found as subscription!!")
                else:
                    obj = Payment.objects.get(stripe_id=intent_id)
                    obj.status = status
                    obj.save()
                    if(obj.person is not None):
                        obj_student = obj.person
                        Stu_Notification.objects.create(student=obj_student, title=_(
                            "Your payment could not be processed. Please contact our support before attempting to pay again"))
                        logger.warning(f"Payment needs admin action : {obj_student.username}")
                    else:
                        logger.warning(f"Payment needs admin action : {obj.payment_email_id}")
            except Exception as ex:
                print(ex)
                logger.critical(f"Payment requires action : {ex}")

        elif event.type == 'invoice.payment_succeeded':
            print("In Invoice Succeeded event")
            data_object = event["data"]["object"]
            logger.info(f"In Invoice Succeeded event : {data_object}")
            if data_object['billing_reason'] in ['subscription_create', "subscription_update", "subscription_cycle"]:
                try:
                    stripe_id = data_object["subscription"]
                    invoice_id = data_object["id"]
                    status = data_object["status"]
                    pay_obj = Payment.objects.get(stripe_id=stripe_id)
                    stripe.api_key = api_key
                    amount_stp = round(float(data_object.amount_paid)/100,2)
                    pay_sub_obj = PaymentSubscriptionDetails.objects.update_or_create(
                            payment_id=pay_obj,
                            intent_id_of_invoice=invoice_id,
                            defaults={
                            "invoice_status" : status,
                            "amount" : amount_stp,
                            "subscription_event_type":data_object['billing_reason'],
                            }
                        )
                    
                    #pay_subs_obj = PaymentSubscriptionDetails.objects.update_or_create(payment_id=pay_obj,intent_id_of_invoice=invoice_id, defaults={"invoice_status":status})
                    obj_plan = pay_obj.plan
                    plan_lang = obj_plan.plan_lang
                    payment_filter_obj = pay_obj.paymentsubscriptiondetail.all().filter(invoice_status=status)
                    is_registred = "register"
                    payment_intent_id = data_object['payment_intent']
                    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                    stripe.Subscription.modify(stripe_id, default_payment_method=payment_intent.payment_method)
                    print("Default Payment method is updated")
                    email = ""
                    if (payment_filter_obj.count() > 1):
                        pay_obj.amount = str(round( float(pay_obj.amount) + (amount_stp),2))
                        pay_obj.save()
                    if(pay_obj.person is not None):
                        obj_student = pay_obj.person
                        keys_list_1 = []
                        values_list_1 = []
                        if (payment_filter_obj.count()==1):
                            is_registred = "login"
                            StudentsPlanMapper.plansManager.lang_code(plan_lang).update_or_create(
                                student=obj_student, plan_lang=plan_lang, defaults={'plans': obj_plan, 'is_trial_active':False})
                            coupon_code = pay_obj.coupon_code
                            coupon_obj = Coupon.objects.filter(code = coupon_code).first()
                            student = obj_student.student
                            if coupon_obj:
                                keys_list_1, values_list_1 = auto_link_to_cohort(obj_student,coupon_obj,plan_lang,obj_plan.plan_name)
                                if coupon_obj.coupon_type == "FutureLab":
                                    student.src = "future_lab"
                                elif coupon_obj.coupon_type == "Organization":
                                    student.src = "company"
                                    coupon_details = CouponDetail.objects.filter(coupon=coupon_obj).first()
                                    if coupon_details:
                                        if coupon_details.company:
                                            student.company = coupon_details.company
                                else:
                                    student.src = "general"
                            # student.discount_coupon_code = ""
                            student.save()
                        create_custom_event(request, 5, custom_user_session_id=custom_user_session_id, meta_data={
                            'plan': obj_plan.plan_name, 'plan_title': obj_plan.title, 'student': obj_student.email})
                        Stu_Notification.objects.create(student=obj_student, title=_(
                            "Thank you. Your payment has been processed successfully"))
                        email = obj_student.username
                        logger.info(f"Payment Succeeded : {email}")
                        try:
                            # hubspotContactupdateQueryAdded
                            logger.info(f"In hubspot plan enroll Invoice Succeeded event parameter building for : {email}")
                            stu_pln_obj=StudentsPlanMapper.plansManager.lang_code(plan_lang).get(student=obj_student, plan_lang=plan_lang)
                            if obj_plan.plan_name =='Premium':
                                plan_created_at=str(stu_pln_obj.created_at)
                                premium_plan_enroll_date=unixdateformat(stu_pln_obj.created_at)
                                upgrade_date=premium_plan_enroll_date
                                keys_list = ["email","upgrade_date","premium_plan_enroll_date","hubspot_premium_plan_enroll_date","hubspot_premium_plan_paid_amount","hubspot_applied_discount_code"] + keys_list_1
                                values_list = [email,upgrade_date,premium_plan_enroll_date, plan_created_at, pay_obj.amount,pay_obj.coupon_code] + values_list_1
                                create_update_contact_hubspot(email, keys_list, values_list)
                            if obj_plan.plan_name =='Elite':
                                plan_created_at=str(stu_pln_obj.modified_at)
                                elite_plan_enroll_date=unixdateformat(stu_pln_obj.modified_at)
                                upgrade_date=elite_plan_enroll_date
                                keys_list = ["email","upgrade_date","elite_plan_enroll_date","hubspot_elite_plan_enroll_date","hubspot_elite_plan_paid_amount","hubspot_applied_discount_code"] + keys_list_1
                                values_list = [email,upgrade_date,elite_plan_enroll_date,plan_created_at, pay_obj.amount,pay_obj.coupon_code] + values_list_1
                                create_update_contact_hubspot(email, keys_list, values_list)
                            logger.info(f"In hubspot plan enroll Invoice Succeeded event parameter update completed for : {email}")
                        except Exception as ex:
                            logger.error(f"Error at hubspot plan enroll Invoice Succeeded event parameter update {ex} for : {email}")
                    else:
                        email = pay_obj.payment_email_id
                        logger.info(f"Payment Succeeded : {email}")
                    
                    try:
                        #Mail send Here
                        # template_nam = "payment/payment_email_content.html"
                        if request.LANGUAGE_CODE == 'it':
                            template_nam = "payment/email_templates/weekly-success-payment.html"
                            subject = "Futurely | Pagamento avvenuto con successo"
                            ctx = {
                                "email": email,
                                "domain": request.get_host(),
                                "user": pay_obj.card_holder_name,
                                "protocol": 'https',
                                "url_type": is_registred,
                                "lang_code": request.LANGUAGE_CODE,
                                "amount": f"{amount_stp}",
                                "plan_name": pay_obj.plan.plan_name,
                                "payment_subscription_duration": pay_obj.payment_subscription_duration,
                                "message": _("Thank you. Your payment has been processed successfully"),
                            }
                            html_msg = get_template(template_nam).render(ctx)
                            fromEmail = settings.EMAIL_HOST_USER
                            msg = EmailMessage(subject, html_msg, fromEmail, [email, admin_email])
                            msg.content_subtype = "html"
                            msg.send()
                            print(f"----Mail Send-------")
                            print(f"-------- Payment Succeeded {email} --------")
                            logger.info(f"Email sent for Payment Succeeded : {email}")
                       
                    except Exception as ex_mail:
                        print(f"Error to send Email : {ex_mail}")
                        logger.warning(f"Error to send Email : {ex_mail}")

                    if(payment_filter_obj.count() == pay_obj.payment_subscription_duration):
                        subscription_end_obj = stripe.Subscription.delete(pay_obj.stripe_id)
                        pay_obj.status = subscription_end_obj.status
                        pay_obj.save()
                        print("Subscription ENd")
                        logger.info(f"Subscription end successfully : {email}")
                except Exception as ex1:
                    print(ex1)
                    print("Error in Invoice succeeded in Payment Subscription")
                    logger.error(f"Error in Invoice succeeded in Payment Subscription : {ex1}")
                print("Invoice payment succeeded")
                print("----------")

        elif event.type == "invoice.payment_failed":
            # 4000 0000 0000 0341
            print("Invoice Payment failed")
            print(event)
            print("-------------------")

            # We need to check invoice payment failed after one succeess
            data_object = event["data"]["object"]
            logger.info(f"In Invoice payment_failed event : {data_object}")
            if data_object['billing_reason'] in ['subscription_create', "subscription_update", "subscription_cycle"]:
                try:
                    stripe_id = data_object["subscription"]
                    invoice_id = data_object["id"]
                    status = data_object["status"]
                    pay_obj = Payment.objects.get(stripe_id=stripe_id)
                    hosted_invoice_url = data_object['hosted_invoice_url']
                    print("hosted_invoice_url: ", hosted_invoice_url)
                    stripe.api_key = api_key
                    amount_stp = round(float(data_object.amount_paid)/100,2)
                    pay_sub_obj = PaymentSubscriptionDetails.objects.update_or_create(
                            payment_id=pay_obj,
                            intent_id_of_invoice=invoice_id,
                            defaults={
                            "invoice_status" : status,
                            "amount" : amount_stp,
                            "subscription_event_type":data_object['billing_reason'],
                            }
                        )
                        
                    obj_plan = pay_obj.plan
                    plan_lang = obj_plan.plan_lang
                    email = ""
                    is_user_active = False
                    is_registred = "register"
                    if(pay_obj.person is not None):
                        is_registred = "login"
                        obj_student = pay_obj.person
                        is_user_active = True
                        Stu_Notification.objects.create(student=obj_student, title=_(
                            "Your payment is declined. Please check with your bank and try again"))
                        email = obj_student.username
                        logger.warning(f"Payment failed : {email}")
                    else:
                        email = pay_obj.payment_email_id
                        logger.warning(f"Payment failed : {email}")

                    template_nam = ""
                    filter_data = pay_obj.paymentsubscriptiondetail.all().filter(invoice_status="open")
                    if(filter_data.count() == 1):
                        template_nam = "payment/email_templates/weekly-failed-payment-first-time.html"
                        print("warning mail sending....")
                        # now = datetime.now()
                        # now_plus_10 = now + timedelta(minutes = 10)
                        # date_time_stamp = datetime.timestamp(now_plus_10)
                        # invoice_update = stripe.Invoice.modify(data_object["id"], next_payment_attempt=date_time_stamp)
                        # print("invoice_update : ", invoice_update)
                        # print("---------------------")
                        #########################################################################################################
                        # invoice_retrive = stripe.Invoice.retrieve(invoice_id)                                                ###
                        # invoice_modify = stripe.Invoice.modify(invoice_retrive.id)                                           ###
                        # now = datetime.now()                                                                                 ###
                        # now_plus_10 = now + timedelta(minutes = 10)                                                          ###
                        # date_time_stamp = datetime.timestamp(now_plus_10)                                                    ###
                        # 1645094217.278092                                                                                    ###
                        # invoice_update = stripe.Invoice.modify(data_object["id"])                                            ###
                        # print("invoice_update : ", invoice_update)                                                           ###
                        #########################################################################################################

                    elif(filter_data.count() == 2):
                        print("Account mail sending....")
                        if is_user_active:
                            obj_student.is_active = False
                            obj_student.save()
                        """Add the block email template!!"""
                        template_nam = "payment/email_templates/weekly-fail-payment-02.html"

                    else:
                        print("payment invoice payment sending....")
                        template_nam = "payment/email_templates/weekly-fail-payment-02.html"
                        
                    try:
                        if request.LANGUAGE_CODE == "it":
                            template_nam = "payment/email_templates/weekly-fail-payment-02.html"
                            subject = "Futurely| Pagamento fallito"
                            ctx = {
                                "email": email,
                                "domain": request.get_host(),
                                "user": pay_obj.card_holder_name,
                                "protocol": 'https',
                                "url_type": is_registred,
                                "lang_code": request.LANGUAGE_CODE,
                                "hosted_invoice_url": hosted_invoice_url,
                                "amount": f"{amount_stp}",
                                "plan_name": pay_obj.plan.plan_name,
                                "message": "Payment Failed",
                            }
                            html_msg = get_template(template_nam).render(ctx)
                    
                            fromEmail = settings.EMAIL_HOST_USER
                            msg = EmailMessage(subject, html_msg, fromEmail, [email, admin_email])
                            msg.content_subtype = "html"
                            msg.send()
                            print(f"------>>>>>>>> Mail Sent <<<<<<<<<<-------")
                            logger.info(f"---->>>> Invoice Payment Failed {pay_obj.payment_email_id} <<<<----")
                        else:
                            logger.info(f"Mail not send, because language code didn't match : {email}")
                    except Exception as email_ex2:
                        print(email_ex2)
                        logger.error(f"Error in mail send : {email_ex2} : {email}")
                except Exception as ex1:
                    print(ex1)
                    print("Error in Invoice failed webhook")
                    logger.critical(f"Error in invoice Failed webhook : {ex1}: {data_object}")

        elif event.type == "invoice.payment_action_required":
            print("payment_action_required")
            data_object = event["data"]["object"]
            logger.info(f"In Invoice payment_action_required event : {data_object}")
            if data_object['billing_reason'] in ['subscription_create', "subscription_update"]:
                try:
                    stripe_id = data_object["subscription"]
                    invoice_id = data_object["id"]
                    status = data_object["status"]
                    pay_obj = Payment.objects.get(stripe_id=stripe_id)
                    stripe.api_key = api_key
                    pay_sub_obj = PaymentSubscriptionDetails.objects.update_or_create(
                            payment_id=pay_obj,
                            intent_id_of_invoice=invoice_id,
                            defaults={
                            "invoice_status" : status,
                            "amount" : round(float(data_object.amount_paid)/100,2),
                            "subscription_event_type":data_object['billing_reason'],
                            }
                        )
                    obj_plan = pay_obj.plan
                    plan_lang = obj_plan.plan_lang
                    email = ""
                    if(pay_obj.person is not None):
                        obj_student = pay_obj.person
                        Stu_Notification.objects.create(student=obj_student, title=_(
                            "Your payment could not be processed. Please contact our support before attempting to pay again"))
                        email = obj_student.username
                        logger.warning(f"Payment needs admin action : {email}")
                    else:
                        email = pay_obj.payment_email_id
                        logger.warning(f"Payment needs admin action : {email}")
                except Exception as ex1:
                    print(ex1)
                    print("Error in Invoice failed webhook")
                    logger.warning(f"Error in Invoice failed webhook : {ex1}")
            print("----------")

        elif event.type == 'customer.subscription.deleted':
            print("Subscription Deleted")
            try:
                subscription = event.data.object
                logger.info(f"In Invoice subscription deleted event : {subscription}")
                stripe_id = subscription.id
                status = subscription.status
                pay_obj = Payment.objects.get(stripe_id=stripe_id)
                pay_obj.status = status
                pay_obj.save()
                email = ""
                if(pay_obj.person is not None):
                    student_obj = pay_obj.person
                    email = student_obj.username
                    logger.info(f"Payment Subscription Ended : {email}")
                else:
                    email = pay_obj.payment_email_id
                    logger.info(f"Payment Subscription Ended : {email}")

                try:
                    if request.LANGUAGE_CODE == "it":
                        # template_nam = "payment/payment_email_content.html"
                        template_nam = "payment/email_templates/weekly-sub-pay-end.html"
                        subject = "Futurely | Hai completato con successo il pagamento per il primo percorso"
                        ctx = {
                            "email": email,
                            "domain": request.get_host(),
                            "user": pay_obj.card_holder_name,
                            "protocol": '',
                            "url_type": "",
                            "payment_subscription_duration": pay_obj.payment_subscription_duration,
                            "plan_name": pay_obj.plan.plan_name,
                            "lang_code": request.LANGUAGE_CODE,
                            "message": "Thank you. Your payment subscription has been ended successfully",
                        }
                        html_msg = get_template(template_nam).render(ctx)
                        fromEmail = settings.EMAIL_HOST_USER
                        msg = EmailMessage(subject, html_msg, fromEmail, [email, admin_email])
                        msg.content_subtype = "html"
                        msg.send()
                        print(f"----Mail Send-----{pay_obj.payment_email_id}--")
                    else:
                        print("mail not send!!")
                        logger.error(f"E-Mail not sent at subscription end in webhook callback : {email}")
                except Exception as ex_error:
                    print(ex_error)
                    logger.critical(f"Error in Subscription delete event : {ex_error} : {email}")
            except Exception as ex:
                print(ex)
                logger.critical(f"Error in Subscription delete event(for subscription end) : {ex}")
        
        elif event.type == 'customer.subscription.updated':
            try:
                subscription = event.data.object
                logger.info(f"In Invoice subscription updated event : {subscription}")
                stripe_id = subscription.id
                status = subscription.status
                obj = Payment.objects.get(stripe_id=stripe_id)
                obj.status = status
                obj.save()
                logger.info(f"Payment Subscription updated : {obj.payment_email_id}")
            except Exception as ex:
                logger.critical(f"error in subscription updated : {ex}")
        return HttpResponse(status=200)
    except Exception as e:
        print(e)
        logger.error(f"error in webhook : {e}")
        return HttpResponse({str(e)}, content_type='application/json', status=400)


@login_required()
def create_pay_confirmed_bit(request):
    """Create pay confirmed bit"""
    try:
        if request.method == "POST" and request.is_ajax:
            request_post = request.POST
            paymentIntentId = request_post.get('paymentIntentId', None)
            if paymentIntentId:
                request.session['pay_confirmed_bit'] = True
                request.session['pay_confirmed_bit_lang'] = request.LANGUAGE_CODE
                user_name = request.user.username
                logger.info(f"Create pay confirmed bit : {user_name}")
                return JsonResponse({'message': 'success'}, status=200, safe=False)
        return JsonResponse({'message': 'error'}, status=200, safe=False)
    except Exception as e:
        #print(e)
        user_name = request.user.username
        logger.critical(f"Error in create pay confirmed bit {e}: {user_name}")
        return JsonResponse({'error': str(e)}, status=403, safe=False)


@login_required()
def btn_go_back_clicked(request):
    """this function work for the go back if click on the back button then this function call by the ajax call"""
    try:
        if request.method == "POST" and request.is_ajax:
            if request.session.get('cohort_ids', None):
                del request.session['cohort_ids']
            if request.session.get('coupon_code', None):
                del request.session['coupon_code']
            logger.info(f"go back clicked by {request.user.username}")
            return JsonResponse({'message': 'success'}, status=200, safe=False)
        return JsonResponse({'message': 'error'}, status=200, safe=False)
    except Exception as e:
        #print(e)
        user_name = request.user.username
        logger.warning(f"error in btn go back clicked {e}: {user_name}")
        return JsonResponse({'message': 'error', 'error': str(e)}, status=200, safe=False)


@login_required()
def apply_coupon_code(request):
    """apply-coupon-code function for the apply coupon code"""
    try:
        if request.method == "POST" and request.is_ajax:
            student = request.user
            # Coupon.objects.all()
            request_post = request.POST
            coupon_code = request_post.get('coupon_code', None)
            remove_discount = request_post.get('remove-discount', None)
            payment_type = request_post.get('payment_type', None)
            logger.info(f"In apply_coupon_code function called with coupon_code {coupon_code} for : {student.username}")
            print("PaymenT Type: ", payment_type)
            if coupon_code and not remove_discount:
                total_price = 0
                plan_id = request.session.get('plan_id')
                discount_name = ''
                discount_value = 0
                is_discount_percent = False
                coupon_found = 'Yes'
                discount_parameters = calculate_discount_parameters(
                    request, coupon_code=coupon_code)
                logger.info(f"discount parameters fetched with {coupon_code} and plan ID-{plan_id} at apply_coupon_code view for : {student.username}")
                if 'is_discount_percent' in discount_parameters:
                    is_discount_percent = discount_parameters['is_discount_percent']
                if 'discount' in discount_parameters:
                    discount_value = discount_parameters['discount']
                    logger.info(f"{coupon_code} discount value - {discount_value} at apply_coupon_code for : {student.username}")
                if 'name' in discount_parameters:
                    discount_name = discount_parameters['name']
                    logger.info(f"{coupon_code} discount name - {discount_name} at apply_coupon_code for : {student.username}")
                if 'coupon_found' in discount_parameters:
                    if discount_parameters['coupon_found'] == False:
                        coupon_found = 'No'
                        logger.info(f"{coupon_code} Coupon_code not found at apply_coupon_code for : {student.username}")

                if plan_id:
                    student = request.user
                    current_plan = StudentsPlanMapper.plansManager.lang_code(
                        request.LANGUAGE_CODE).filter(student=student).first()
                    our_plan_obj = OurPlans.plansManager.lang_code(
                        request.LANGUAGE_CODE).get(id=plan_id)
                    logger.info(f"plan obj and current plan linked at apply coupon code view for : {student.username}")

                    if payment_type == "Weekly":
                        print("add coupon Weekly")
                        logger.info(f"Coupon Code {coupon_code} applied for {our_plan_obj.plan_name} Plan and Plan cost {our_plan_obj.weekly_cost} at apply coupon code for : {student.username}")
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.weekly_cost)
                            logger.info(f"fetched upgraded cost {total_price} at apply coupon code view for : {student.username}")
                        else:
                            total_price = float(our_plan_obj.weekly_cost)

                        if is_discount_percent:
                            total_discount, final_total = calculate_discount_and_final_price(
                            total_price, discount_value, is_discount_percent)
                            print("Coupon Apply")
                            logger.info(f"{coupon_code}-Coupon applied, total_discount-{total_discount}, final_total-{final_total} at apply_coupon_code for : {student.username}")
                        else:
                            total_discount = 0
                            final_total = total_price
                            print("Cupan Not Apply")
                            logger.info(f"{coupon_code} - Coupon not applied for weekly at apply_coupon_cod_view for : {student.username}")

                    if payment_type == "One Time":
                        print("add coupon One Time")
                        logger.info(f"Coupon Code {coupon_code} applied for {our_plan_obj.plan_name} Plan and Plan cost {our_plan_obj.cost} at apply coupon code for : {student.username}")
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.upgrade_cost)
                            logger.info(f"fetched the upgraded cost with this {coupon_code} at apply coupon code view for : {student.username}")
                        else:
                            total_price = float(our_plan_obj.cost)

                        total_discount, final_total = calculate_discount_and_final_price(
                            total_price, discount_value, is_discount_percent)
                        logger.info(f"{coupon_code}-Coupon applied, total_discount-{total_discount}, final_total-{final_total} at apply_coupon_code for : {student.username}")

                # tax_calculated_object=calculate_tax_and_price(request,final_total) #check this out 
                tax_calculated_object=calculate_tax_and_price(request,final_total) #check this out 
                logger.info(f"Tax calculated with final total-{final_total} at apply_coupon_code view for : {student.username}")
                tax_isactive = tax_calculated_object['tax_isactive']
                lst =[]
                if tax_isactive:
                    tax_amount_price = tax_calculated_object['total_tax_amount']
                    amount_after_tax = tax_calculated_object['amount_after_tax']
                    all_taxes = tax_calculated_object['all_taxes']
                    logger.info(f"total amount_after_tax-{amount_after_tax} and tax_amount_price-{tax_amount_price} with this {coupon_code} at apply_coupon_code for : {student.username}")
                    #lst = ['Tax_name', 'Tax_Amount']
                    for tax in all_taxes:
                        tax_name = tax.tax_display_name
                        tax_amount = tax.cal_tax_amount(final_total)
                        
                        lst.append([tax_name,tax_amount])
                else:
                    amount_after_tax = final_total
                if coupon_found == 'Yes':
                    request.session['coupon_code'] = coupon_code
                elif request.session.get('coupon_code', None):
                    #del request.session['coupon_code']
                    request.session['coupon_code'] = ""
                #print(lst)
                user_name = request.user.username
                # logger.info(f"Coupon code {coupon_code} applied at apply_coupon_code for : {user_name}")
                logger.info(f"Coupon code {coupon_code} applied, and Plan ID-{plan_id} at apply_coupon_code view for : {user_name}")    
                return JsonResponse({'message': 'success', 'total_discount': str(total_discount), 'final_total': final_total, 'discount_name': discount_name, 'coupon_found': coupon_found, 'tax_isactive': tax_isactive, 'amount_after_tax': amount_after_tax, 'all_taxes': lst}, status=200, safe=False)

            elif coupon_code and remove_discount and remove_discount == 'Yes':
                total_price = 0
                plan_id = request.session.get('plan_id')
                discount_name = _('Discount')
                discount_value = 0
                is_discount_percent = False
                student = request.user
                if plan_id:
                    current_plan = StudentsPlanMapper.plansManager.lang_code(
                        request.LANGUAGE_CODE).filter(student=student).first()
                    our_plan_obj = OurPlans.plansManager.lang_code(
                        request.LANGUAGE_CODE).get(id=plan_id)
                    logger.info(f"plan obj and current plan linked at apply coupon code view for : {student.username}")

                    if payment_type == "Weekly":
                        print("remove coupon Weekly")
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.weekly_cost)
                            logger.info(f"fetched the upgraded cost at apply coupon code for : {student.username}")
                        else:
                            total_price = float(our_plan_obj.weekly_cost)

                    if payment_type == "One Time":
                        print("remove coupon One Time")
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            logger.info(f"fetched the upgraded cost at apply coupon code for : {student.username}")
                            total_price = float(our_plan_obj.upgrade_cost)
                        else:
                            total_price = float(our_plan_obj.cost)

                total_discount, final_total = calculate_discount_and_final_price(
                    total_price, discount_value, is_discount_percent)
                logger.info(f"{coupon_code} -Applied Coupon removed, total_discount-{total_discount}, final_total-{final_total} at apply_coupon_code for : {student.username}")
                tax_calculated_object=calculate_tax_and_price(request,final_total)
                logger.info(f"Tax calculated with final total-{final_total} at apply_coupon_code view for : {student.username}")
                tax_isactive = tax_calculated_object['tax_isactive']
                lst =[]
                if tax_isactive:
                    amount_after_tax = tax_calculated_object['amount_after_tax']
                    all_taxes = tax_calculated_object['all_taxes']
                    #lst = ['Tax_name', 'Tax_Amount']
                    for tax in all_taxes:
                        tax_name = tax.tax_display_name
                        tax_amount = tax.cal_tax_amount(final_total)
                        
                        lst.append([tax_name,tax_amount])
                else:
                    amount_after_tax = final_total
                #print("Code Removed")
                request.session['coupon_code'] = "NULLCOUPONCODE"
                #print("OK")
                #if request.session.get('coupon_code', None):
                #del request.session['coupon_code']
                #    request.session['coupon_code'] = ""
                user_name = request.user.username
                logger.info(f"Coupon code {coupon_code} removed ID-{plan_id} at apply_coupon_code view for : {user_name}")
                # logger.info(f"Coupon code {coupon_code} removed at apply_coupon_code view for : {user_name}")
                return JsonResponse({'message': 'success', 'total_discount': str(total_discount), 'final_total': final_total, 'discount_name': discount_name, 'tax_isactive': tax_isactive, 'amount_after_tax': amount_after_tax, 'all_taxes': lst}, status=200, safe=False)
        user_name = request.user.username
        logger.warning(f"request ajax call warning at apply/remove coupon code : {user_name}")
        return JsonResponse({'message': 'error'}, status=200, safe=False)
    except Exception as e:
        #print(e)
        user_name = request.user.username
        logger.critical(f"Error while apply/remove coupon code {e}: {user_name}")
        return JsonResponse({'message': 'error', 'error': str(e)}, status=200, safe=False)



def payment_type_change_view(request):
    """this function for the change the payment type Ex: weekly or one-time and this function call with POST, is_ajax requests."""
    try:
        if request.method == "POST" and request.is_ajax:
            student = request.user
            logger.info(f"In payment type change view called by : {student.username}")
            request_post = request.POST
            plan_id = request.session.get('plan_id', None)
            payment_type = request_post.get("payment_type", None)
            coupon_code = request.session.get('coupon_code', None)
            data = {}
            if plan_id:
                our_plan_obj = OurPlans.plansManager.lang_code(
                        request.LANGUAGE_CODE).get(id=plan_id)
                #print(our_plan_obj)
                current_plan = StudentsPlanMapper.plansManager.lang_code(
                    request.LANGUAGE_CODE).filter(student=student).first()
                logger.info(f"plan obj {our_plan_obj.plan_name} plan and current obj linked at payment type change view for : {student.username}")
                discount = 0
                tax = 0
                discount_name = ''
                discount_value = 0
                is_discount_percent = False
                tax_isactive = False
                lst = []
                if payment_type == "Weekly":
                    print(f"{payment_type}")
                    is_discount_percent = False
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.weekly_cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.upgrade_cost)
                            logger.info(f"fetched upgraded cost at payment type change view for : {student.username}")
                        else:
                            total_price = float(our_plan_obj.weekly_cost)
                    
                    if coupon_code:
                        coupon_found = 'Yes'
                        discount_parameters = calculate_discount_parameters(
                            request, coupon_code=coupon_code)
                        logger.info(f"discount parameters fetched at payment type change view for : {student.username}")
                        if 'is_discount_percent' in discount_parameters:
                            is_discount_percent = discount_parameters['is_discount_percent']
                        if 'discount' in discount_parameters:
                            discount_value = discount_parameters['discount']
                        if 'name' in discount_parameters:
                            discount_name = discount_parameters['name']
                        if 'coupon_found' in discount_parameters:
                            if discount_parameters['coupon_found'] == False:
                                coupon_found = 'No'
                                logger.info(f"Coupon not found at payment type change view for : {student.username}")

                        if is_discount_percent:
                                total_discount, final_total = calculate_discount_and_final_price(
                                total_price, discount_value, is_discount_percent)
                                print("Coupan Apply")
                        else:
                            total_discount = 0
                            final_total = total_price
                            print("Cupan Not Apply")
                    else:
                        total_discount = 0
                        final_total = total_price
                        coupon_found = 'No'

                if payment_type == "One Time":
                    print(f"{payment_type}")
                    is_discount_percent = False
                    if(current_plan and current_plan.is_trial_active):
                        total_price = float(our_plan_obj.cost)
                    else:
                        if current_plan and current_plan.plans.plan_name == "Premium" and our_plan_obj.plan_name == "Elite":
                            total_price = float(our_plan_obj.upgrade_cost)
                            logger.info(f"fetched upgrade cost at payment type change view for : {student.username}")
                        else:
                            total_price = float(our_plan_obj.cost)

                    if coupon_code:
                        coupon_found = 'Yes'
                        discount_parameters = calculate_discount_parameters(
                            request, coupon_code=coupon_code)
                        logger.info(f"discount parameters fetched at payment type change view for : {student.username}")
                        if 'is_discount_percent' in discount_parameters:
                            is_discount_percent = discount_parameters['is_discount_percent']
                        if 'discount' in discount_parameters:
                            discount_value = discount_parameters['discount']
                        if 'name' in discount_parameters:
                            discount_name = discount_parameters['name']
                        if 'coupon_found' in discount_parameters:
                            if discount_parameters['coupon_found'] == False:
                                coupon_found = 'No'

                        total_discount, final_total = calculate_discount_and_final_price(
                        total_price, discount_value, is_discount_percent)
                        print("Coupan Apply")
                    else:
                        total_discount = 0
                        final_total = total_price
                        coupon_found = 'No'

                if our_plan_obj:
                    # data['our_plan_obj'] = our_plan_obj
                    actual_price = total_price
                    # discount, total_price = calculate_discount_and_final_price(
                    #     total_price, discount, is_discount_percent)
                    tax_calculated_object = calculate_tax_and_price(request, final_total)
                    # tax_calculated_object = calculate_tax_and_price(request, final_total)
                    all_taxes = tax_calculated_object['all_taxes']
                    if all_taxes.count() > 0:
                        tax_isactive = tax_calculated_object["tax_isactive"]
                        data["total_tax_amount"] = tax_calculated_object["total_tax_amount"]
                       
                        if tax_isactive:
                            amount_after_tax = tax_calculated_object['amount_after_tax']
                            #lst = ['Tax_name', 'Tax_Amount']
                            for tax in all_taxes:
                                tax_name = tax.tax_display_name
                                tax_amount = tax.cal_tax_amount(final_total)
                                lst.append([tax_name,tax_amount])
                        else:
                            amount_after_tax = actual_price
                    else:
                        amount_after_tax = actual_price
                    data["amount_after_tax"] = amount_after_tax
                    data["tax_isactive"] = tax_isactive
                    # print(lst)
                    data["all_taxes"] = lst
                    # data = json.dumps(data)
                print(data)
                logger.info(f"return json response at payment type change view for : {student.username}")
                # return JsonResponse({'message': 'success', 'tax_isactive': tax_isactive, 'amount_after_tax': amount_after_tax, 'all_taxes': lst}, status=200, safe=False)
                return JsonResponse({'message': 'success', 'total_discount': total_discount, 'final_total': final_total, 'discount_name': discount_name, 'coupon_found': coupon_found, 'tax_isactive': tax_isactive, 'amount_after_tax': amount_after_tax, 'all_taxes': lst}, status=200, safe=False)

            else:
                user_name = request.user.username
                logger.info(f"Error in payment page: {user_name}")
                return JsonResponse({"message": "error"}, status=200, safe=False)
        else:
            user_name = request.user.username
            logger.error(f"Error in payment page: {user_name}")
            return JsonResponse({"message": "error"}, status=200, safe=False)
    except Exception as ex:
        print(ex)
        user_name = request.user.username
        logger.critical(f"Error in payment type change {ex}: {user_name}")
    return JsonResponse({"message": "error"}, status=200, safe=False)     