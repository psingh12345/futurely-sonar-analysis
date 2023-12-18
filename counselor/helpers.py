from userauth import models as auth_mdl
from student.models import StudentCohortMapper
from courses import models
import logging 
from payment.models import Payment, Coupon, CouponDetail
from django.db.models import Q
from datetime import datetime, timedelta, date
import pdb, pytz
from django.conf import settings
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

def student_course_report(request, list_of_cohort):
    all_stu = None
    try:
        academic_session_start_date = request.user.counselor.academic_session_start_date
        academic_session_start_date = datetime.fromisoformat(request.user.counselor.academic_session_start_date.isoformat())
        local_tz = pytz.timezone(settings.TIME_ZONE)
        academic_session_start_date = local_tz.localize(academic_session_start_date)
        is_from_fast_track = request.session.get('is_from_fast_track', False)
        is_from_middle_school = request.session.get('is_from_middle_school', False)
        is_from_job_course = request.session.get('is_from_job_course', False)
        discount_code = request.session.get('selected_coupon_codes', [])
        is_all_student = request.session.get('is_all_student', False)
        plans = request.user.counselor.plans.all()
        # if len(discount_code) == 0:
        company_name = request.user.counselor.company
        coupon_obj = Coupon.objects.filter(Q(coupon_detail__company__name=company_name),Q(plan__in=plans), start_date__gte = academic_session_start_date, is_for_middle_school=is_from_middle_school, is_for_fast_track_program=is_from_fast_track).values_list('code',flat=True)
        coupon_obj = list(coupon_obj)
        request.session['selected_coupon_codes'] = coupon_obj
        discount_code = coupon_obj
        stu_payments = Payment.objects.filter(coupon_code__in = discount_code).values_list('person__id',flat=True)
        all_stu = auth_mdl.Person.objects.filter(Q(student__discount_coupon_code__in=discount_code) | Q(id__in=stu_payments),student__is_from_middle_school=is_from_middle_school, student__is_from_fast_track_program=is_from_fast_track, stuMapID__cohort__cohort_id__in = list_of_cohort).distinct().order_by('last_name')
        logger.info(f"get the data successfully for : {request.user.username}")
    except Exception as err:
        logger.info(f"Error in student course resport function {err} for : {request.user.username}")
    return all_stu

def student_helper_kpis(request):
    all_stu = []
    try:
        is_from_fast_track = request.session.get('is_from_fast_track', False)
        is_from_middle_school = request.session.get('is_from_middle_school', False)
        is_from_job_course = request.session.get('is_from_job_course', False)
        discount_code = request.session.get('selected_coupon_codes', [])
        class_name = request.session.get('class_name', None)
        class_year = request.session.get('class_year', None)
        specialization = request.session.get('specialization', None)
        total_students = request.session.get('total_students', None)
        # is_all_student = request.session.get('is_all_student', False)
        stu_payments = Payment.objects.filter(coupon_code__in = discount_code).values_list('person__id',flat=True)
        if total_students:
            all_stu = auth_mdl.Person.objects.filter(Q(student__discount_coupon_code__in=discount_code) | Q(id__in=stu_payments), student__is_from_middle_school=is_from_middle_school, student__is_from_fast_track_program=is_from_fast_track).values_list('id', flat=True)
        else:
            all_stu = auth_mdl.Person.objects.filter(Q(student__discount_coupon_code__in=discount_code) | Q(id__in=stu_payments), student__is_from_middle_school=is_from_middle_school, student__is_from_fast_track_program=is_from_fast_track, student__student_school_detail__class_year__name=class_year, student__student_school_detail__class_name__name=class_name, student__student_school_detail__specialization__name=specialization).values_list('id', flat=True)
        logger.info(f"get the data successfully for : {request.user.username}")
    except Exception as err:
        logger.error(f"Error in student helper kpis {err} for : {request.user.username}")
    return all_stu

def student_helper_kpis_company(request):
    all_stu = []
    try:
        is_from_fast_track = request.session.get('is_from_fast_track', False)
        is_from_middle_school = request.session.get('is_from_middle_school', False)
        is_from_job_course = request.session.get('is_from_job_course', False)
        discount_code = request.session.get('selected_coupon_codes', [])
        # is_all_student = request.session.get('is_all_student', False)
        list_of_cohort = request.session.get('list_of_cohort', [])
        stu_payments = Payment.objects.filter(coupon_code__in = discount_code).values_list('person__id',flat=True)
        all_stu = auth_mdl.Person.objects.filter(Q(student__discount_coupon_code__in=discount_code) | Q(id__in=stu_payments), student__is_from_middle_school=is_from_middle_school, student__is_from_fast_track_program=is_from_fast_track, stuMapID__cohort__cohort_id__in = list_of_cohort).distinct().values_list('id', flat=True)
        logger.info(f"get the data successfully for : {request.user.username}")
    except Exception as err:
        logger.error(f"Error in student helper kpis {err} for : {request.user.username}")
    return all_stu