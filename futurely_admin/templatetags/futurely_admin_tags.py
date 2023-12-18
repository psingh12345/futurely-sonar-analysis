from django import template
from .. import models
from datetime import date, timedelta, datetime
import calendar
import pytz
from django.conf import settings
from userauth.models import Student, Person
from payment.models import Coupon, CouponDetail, Payment
from courses.models import Cohort, Steps
from django.db.models import Q

register = template.Library()

@register.simple_tag
def get_student_count(request, step_status_id):
    try:
        discount_code = request.session.get('discount_code', '')
        cohort_id = request.session.get('cohort_id', '')
        print("Discount Code :-", discount_code, 'Cohort ID :- ', cohort_id, 'Step Status ID :- ', step_status_id)
        cohort = Cohort.cohortManager.lang_code(request.LANGUAGE_CODE).get(cohort_id=cohort_id)
        step_status = cohort.cohort_step_status.filter(id= step_status_id).first()
        if discount_code != '':
            coupon_obj = Coupon.objects.filter(code=discount_code).values_list('code',flat=True)
            coupon_obj = list(coupon_obj)
            stu_payments = Payment.objects.filter(coupon_code__in = coupon_obj).values_list('person__id',flat=True)
            step_student_data = step_status.step_status_id.filter(stu_cohort_map__student__id__in=stu_payments).all()
            return step_student_data.count()
    except Exception as Error:
        print(f"Error in get stduent count for futurely-admin : {Error}")
    return 0