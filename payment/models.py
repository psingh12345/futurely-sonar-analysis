from django.db import models
from django.db.models import Q
from django.utils import timezone
from userauth.models import Person, School , Company
from courses.models import Cohort, PlanNames
from courses.models import OurPlans
from django.conf import settings
import datetime
import pytz
from lib.model_validators import validate_discount_value
from django.urls import reverse
from django.utils.html import format_html


COUPON_TYPE = [
    ('FutureLab', 'FutureLab'),
    ('Organization', 'Organization'),
    ("General", "General"),
]

DISCOUNT_TYPE = [
    ('Fixed', 'Fixed'),
    ("Percentage", "Percentage"),
]

PLAN_TYPE = [
    (PlanNames.Community.value, PlanNames.Community.value),
    (PlanNames.Premium.value, PlanNames.Premium.value),
    (PlanNames.Elite.value, PlanNames.Elite.value),
    (PlanNames.Diamond.value, PlanNames.Diamond.value),
    (PlanNames.Trial2022.value, PlanNames.Trial2022.value),
    (PlanNames.FastTrack.value, PlanNames.FastTrack.value),
    (PlanNames.MiddleSchool.value, PlanNames.MiddleSchool.value),
    ('Master', 'Master'),
    (PlanNames.JobCourse.value, PlanNames.JobCourse.value),
]
TAX_TYPE = [
    ('Fixed', 'Fixed'),
    ("Percentage", "Percentage"),
]
COUNTRIES = [
    ("USA", ("USA")),
    ("Italy", ("Italy")),
]

PAYMENT_USER_TYPE = (
    ("Direct", "Direct"),
    ("Platform", "Platform"),
)

PAYMENT_SUBSCRIPTION_TYPE = (
    ("One Time", "One Time"),
    ("Weekly", "Weekly"),
)

class TimeStampModel(models.Model):
    """TimeStamp Model"""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    modified_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True


class Payment(TimeStampModel):
    stripe_id = models.CharField(max_length=200, default='', blank=True)
    person=models.ForeignKey(Person, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)
    plan = models.ForeignKey(OurPlans, on_delete=models.DO_NOTHING, related_name="Plan", null=True)
    payment_method = models.CharField(max_length=200, default='Credit Card', blank=True, null=True)
    coupon_code = models.CharField(max_length=100, default='', blank=True, null=True)
    actual_amount = models.CharField(max_length=100, default='',  blank=True, null=True)
    discount = models.CharField(max_length=100, default='',  blank=True, null=True)
    tax_amount = models.DecimalField(default=0.0, blank=True,null=True, decimal_places=2, max_digits=10)
    is_disputed = models.BooleanField(default=False,null=True)
    dispute_type = models.CharField(max_length=200, default='',  blank=True, null=True)
    refund = models.CharField(max_length=200, default='',  blank=True, null=True)
    dispute_date = models.CharField(max_length=200, default='',  blank=True, null=True)
    refund_date = models.CharField(max_length=200, default='',  blank=True, null=True)
    amount = models.CharField(max_length=10,  blank=True, null=True)
    currency = models.CharField(max_length=30, default='',  blank=True, null=True)
    status = models.CharField(max_length=30, default='',  blank=True, null=True)
    custom_user_session_id = models.CharField(max_length=200, default="",  blank=True, null=True)
    payment_person_type = models.CharField(max_length=20, choices=PAYMENT_USER_TYPE, default='Platform', blank=True, null=True)
    payment_subscription_type = models.CharField(max_length=20, choices=PAYMENT_SUBSCRIPTION_TYPE, default="One Time", blank=True, null=True)
    payment_subscription_duration = models.IntegerField(default=1,blank=True, null=True)
    payment_email_id = models.CharField(max_length=75, default='',blank=True, null=True)
    card_holder_name = models.CharField(max_length=75, default='',blank=True, null=True)

    def link_to_payment(self):
        link = reverse("admin:payment_payment_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>')

    @property
    def payment_id(self):
        return f"F-{self.id+100000}"

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return "{} | {} | {} | {}".format(self.payment_id, self.person, self.plan, self.status)

class PaymentSubscriptionDetails(TimeStampModel):
    payment_id = models.ForeignKey(Payment, on_delete=models.CASCADE,related_name="paymentsubscriptiondetail")
    intent_id_of_invoice = models.CharField(max_length=100, blank=True, null=True)
    invoice_status = models.CharField(max_length=100, blank=True, null=True)
    amount = models.CharField(max_length=50, default='0')
    subscription_event_type = models.CharField(max_length=100, blank=True, null=True)

    def link_to_paymentsubscriptiondetails(self):
        link = reverse("admin:payment_paymentsubscriptiondetails_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>')

    class Meta:
        verbose_name = "PaymentSubscriptionDetail"
        verbose_name_plural = "PaymentSubscriptionDetails"

class ActiveCouponManager(models.Manager):
    def get_queryset(self):
        local_tz = pytz.timezone(settings.TIME_ZONE)
        dt_now = local_tz.localize(datetime.datetime.now())
        return super().get_queryset().filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True))
        #return super().get_queryset().filter(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(is_active=True), ~Q(coupon_type='FutureLab'), ~Q(coupon_type='Organization'))

class FutureLabCompanyCouponManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(Q(coupon_type='FutureLab') | Q(coupon_type='Organization'))

CHOICES_NUM_OF_PLANS =(
    ("2","2"),
    ("3","3"),
)

class Coupon(TimeStampModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100) # name of the discount like Future Lab discount, Christmas discount etc
    description = models.CharField(max_length=200, null=True, blank=True)
    coupon_type = models.CharField(max_length=50, default='General', choices=COUPON_TYPE)
    plan_type = models.CharField(max_length=30, default='Premium', choices=PLAN_TYPE)
    plan = models.ForeignKey(OurPlans, on_delete=models.CASCADE,related_name="coupons", null=True, blank=True)
    discount_type = models.CharField(max_length=30, default='Fixed', choices=DISCOUNT_TYPE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    discount_value = models.DecimalField(decimal_places=2, max_digits=10)
    objects = models.Manager() # The default manager.
    active_objects = ActiveCouponManager()
    futurelab_company_objects = FutureLabCompanyCouponManager()
    number_of_offered_plans = models.CharField(max_length=10, default="3", choices=CHOICES_NUM_OF_PLANS)
    skip_course_dependency = models.BooleanField(default=False, blank=True, null= True)
    is_course1_locked = models.BooleanField(default=False, blank=True, null= True)
    display_discounted_price_only = models.BooleanField(default=False, blank=True, null=True)
    is_fully_paid_by_school_or_company = models.BooleanField(default=False, blank=True, null=True)
    is_for_middle_school = models.BooleanField(default=False, blank=True, null=True)
    is_for_fast_track_program = models.BooleanField(default=False, blank=True, null= True)
    is_for_zanichelli = models.BooleanField(default=False, blank=True, null= True)
    # def clean(self,*args,**kwargs):
    #     validate_discount_value(self.discount_type, self.discount_value)
        

    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
    def __str__(self):
        return "{}".format(self.code)

class Tax(TimeStampModel):
    tax_name = models.CharField(max_length=50, unique=True)
    tax_display_name = models.CharField(max_length=50, default='', blank=True, null=True)
    tax_type = models.CharField(max_length=50, default='Percentage', choices=TAX_TYPE) 
    tax_amount = models.DecimalField(decimal_places=2, max_digits=10)
    tax_country = models.CharField(max_length=70, default='Italy', choices=COUNTRIES)
    is_active = models.BooleanField(default=False)
    
    
    def cal_tax_amount(self,total):
        tax_val = 0
        if self.tax_type == 'Percentage':
            tax_amount = round(float(self.tax_amount), 2)
            tax_val = total * tax_amount/100
            tax_val = round(float(tax_val), 2)
        else:
            # tax_val = self.tax_amount
            tax_val = round(float(self.tax_amount), 2)
        # print(f"Tax amount = {tax_val}")
        # print(f"Tax type = {self.tax_type}")
        return tax_val
    class Meta:
        verbose_name = 'Tax'
        verbose_name_plural = 'Taxes'
    def __str__(self):
        return "{}".format(self.tax_name)

class TaxCollection(TimeStampModel):
    payment_id=models.ForeignKey(Payment,on_delete=models.CASCADE,related_name="tax_collections")
    tax_id=models.ForeignKey(Tax,on_delete=models.CASCADE,related_name="tax_collections")
    tax_amount = models.DecimalField(decimal_places=2, max_digits=10)
    
    class Meta:
        verbose_name = 'TaxCollection'
        verbose_name_plural = 'TaxCollections'
    def __str__(self):
        return "{}".format(self.tax_name)

class CouponDetail(TimeStampModel):
    school = models.ForeignKey(School, on_delete=models.DO_NOTHING, related_name="school_information",blank=True, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.DO_NOTHING, related_name="coupon_detail",blank=True, null=True)
    cohort_program1 = models.ForeignKey(Cohort,on_delete=models.CASCADE, related_name="coupon_cohort_p1_info", blank=True, null=True)
    cohort_program2 = models.ForeignKey(Cohort,on_delete=models.CASCADE, related_name="coupon_cohort_p2_info", blank=True, null=True)
    cohort_program3 = models.ForeignKey(Cohort,on_delete=models.CASCADE, related_name="coupon_cohort_p3_info", blank=True, null=True)
    company = models.ForeignKey(Company,on_delete=models.DO_NOTHING , related_name = "company_information",blank=True , null= True)
    sponsor_compnay = models.ForeignKey(Company,on_delete=models.DO_NOTHING , related_name ="sponsor_company_information",blank=True , null= True)
    
    class Meta:
        verbose_name = 'CouponDetail'
        verbose_name_plural = 'CouponDetails'