import re
from django import template
from student import models as stu_mdl
from courses.models import OurPlans
from payment.models import Coupon
from django.db.models import Q

register = template.Library()

@register.simple_tag
def cal_tax_amount(tax,total):
    tax_amount = tax.cal_tax_amount(total)
    return tax_amount

@register.simple_tag
def calculate_discount_amount_req_coupon_code_onetime(request, plan_id):
    is_discount_percent = False
    if plan_id is not None:
        coupon_code = request.session.get('free_coupon_code',None)
        try:
            our_plan_obj = OurPlans.plansManager.lang_code(request.LANGUAGE_CODE).get(id=plan_id)
            total = float(our_plan_obj.cost)
            coupon_obj = None
            try:
                if our_plan_obj.plan_name == "Premium":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"))
                elif our_plan_obj.plan_name == "Elite":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"))
            except Exception as error:
                print("error :", error)
            if coupon_obj:
                discount_type = coupon_obj.discount_type
                discount = float(coupon_obj.discount_value)
                if 'percent' in discount_type.lower():
                    is_discount_percent = True
            else:
                discount_final_val = total
            if is_discount_percent:
                final_discount = total * discount/100
                final_discount = round(final_discount, 2)
                discount_final_val = round(total - final_discount,2)
            else:
                discount_final_val = round(total ,2)
        except Exception as ex:
            our_plan_obj = None
            print("Error :", ex)
    return discount_final_val

@register.simple_tag
def calculate_discount_amount_req_coupon_code_weekly(request, plan_id):
    is_discount_percent = False
    if plan_id is not None:
        coupon_code = request.session.get('free_coupon_code',None)
        try:
            our_plan_obj = OurPlans.plansManager.lang_code(request.LANGUAGE_CODE).get(id=plan_id)
            total = float(our_plan_obj.weekly_cost)
            coupon_obj = None
            try:
                if our_plan_obj.plan_name == "Premium":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"))
                elif our_plan_obj.plan_name == "Elite":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"))
            except Exception as error:
                print("error :", error)
            if coupon_obj:
                discount_type = coupon_obj.discount_type
                discount = float(coupon_obj.discount_value)
                if 'percent' in discount_type.lower():
                    is_discount_percent = True
            else:
                discount_final_val = total
            if is_discount_percent:
                final_discount = total * discount/100
                final_discount = round(final_discount, 2)
                discount_final_val = round(total - final_discount,2)
            else:
                discount_final_val = round(total ,2)
        except Exception as ex:
            our_plan_obj = None
            print("Error :", ex)
    return discount_final_val


@register.simple_tag
def calculate_amount_coupon_cod_onetime(request, plan_id):
    student = request.user
    is_discount_percent = False
    if plan_id is not None:
        coupon_code = student.student.discount_coupon_code
        coupon_details = Coupon.active_objects.filter(code__iexact=coupon_code).first()
        if coupon_details is None:
            coupon_code = request.session.get('coupon_code_after_trial',None)
        try:
            our_plan_obj = OurPlans.plansManager.lang_code(request.LANGUAGE_CODE).get(id=plan_id)
            total = float(our_plan_obj.cost)
            coupon_obj = None
            try:
                if our_plan_obj.plan_name == "Premium":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"))
                elif our_plan_obj.plan_name == "Elite":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"))
            except Exception as error:
                print("error :", error)
            if coupon_obj:
                discount_type = coupon_obj.discount_type
                discount = float(coupon_obj.discount_value)
                if 'percent' in discount_type.lower():
                    is_discount_percent = True
            else:
                discount_final_val = total
            if is_discount_percent:
                final_discount = total * discount/100
                final_discount = round(final_discount, 2)
                discount_final_val = round(total - final_discount,2)
            else:
                discount_final_val = round(total ,2)
        except Exception as ex:
            our_plan_obj = None
            print("Error :", ex)
    return discount_final_val

@register.simple_tag
def calculate_amount_coupon_cod(request, plan_id):
    student = request.user
    is_discount_percent = False
    if plan_id is not None:
        coupon_code = student.student.discount_coupon_code
        coupon_details = Coupon.active_objects.filter(code__iexact=coupon_code).first()
        if coupon_details is None:
            coupon_code = request.session.get('coupon_code_after_trial',None)
        try:
            our_plan_obj = OurPlans.plansManager.lang_code(request.LANGUAGE_CODE).get(id=plan_id)
            total = float(our_plan_obj.weekly_cost)
            coupon_obj = None
            try:
                if our_plan_obj.plan_name == "Premium":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"))
                elif our_plan_obj.plan_name == "Elite":
                    coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"))
            except Exception as error:
                print("error :", error)
            if coupon_obj:
                discount_type = coupon_obj.discount_type
                discount = float(coupon_obj.discount_value)
                if 'percent' in discount_type.lower():
                    is_discount_percent = True
            else:
                discount_final_val = total
            if is_discount_percent:
                final_discount = total * discount/100
                final_discount = round(final_discount, 2)
                discount_final_val = round(total - final_discount,2)
            else:
                discount_final_val = round(total ,2)
        except Exception as ex:
            our_plan_obj = None
            print("Error :", ex)
    return discount_final_val

@register.simple_tag
def to_float(val):
    try:
        val = round(float(val),2)
    except:
        pass
    return val
    