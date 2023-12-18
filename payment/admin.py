from django.contrib import admin
from rangefilter.filters import DateRangeFilter
from .models import Payment, Coupon, Tax, TaxCollection, PaymentSubscriptionDetails, CouponDetail
from .forms import CouponAdminForm, CouponDetailAdminForm
from django.core.exceptions import ValidationError

class PaymentSubscriptionDetailsInline(admin.TabularInline):
    model = PaymentSubscriptionDetails
    fields = ('id', 'intent_id_of_invoice', 'invoice_status', 'amount', 'subscription_event_type', 'link_to_paymentsubscriptiondetails')
    readonly_fields = ['id', 'intent_id_of_invoice', 'invoice_status', 'amount', 'subscription_event_type', 'link_to_paymentsubscriptiondetails']
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    fields = [ 'person', 'plan', "status", "coupon_code", "payment_method", "actual_amount", "discount",'tax_amount', "amount", "currency", "is_disputed", "dispute_type", "dispute_date", "refund", "refund_date", "stripe_id","payment_person_type","payment_subscription_type","payment_subscription_duration","payment_email_id","card_holder_name", ]
    list_display = ("payment_id", 'person', 'plan', "status", "payment_subscription_type", "coupon_code", "actual_amount", "discount",'tax_amount', "amount", "currency", "stripe_id", "payment_email_id", "created_at", "modified_at")
    search_fields = ["person__username",'person__first_name','person__last_name',"stripe_id", "amount", "status", "coupon_code","payment_email_id"]
    list_filter = (('created_at', DateRangeFilter), 'plan','payment_person_type','payment_subscription_type',)
    raw_id_fields = ('person','plan')
    inlines = [PaymentSubscriptionDetailsInline,]
    # def has_add_permission(self, request):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return True

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     return qs

    # def get_readonly_fields(self, request, obj=None):
    #     if obj:
    #         return ["payment_id", 'person', 'plan', "status", "coupon_code", "payment_method", "actual_amount", "discount", "amount", "currency", "is_disputed", "dispute_type", "dispute_date", "refund", "refund_date", "stripe_id", "created_at", "modified_at"]
    #     else:
    #         return []


@admin.register(PaymentSubscriptionDetails)
class PaymentSubscriptionDetailsAdmin(admin.ModelAdmin):
    fields = ["payment_id", "intent_id_of_invoice", "invoice_status", "amount", "subscription_event_type"]
    list_display = ["payment_id", "intent_id_of_invoice", "invoice_status", "amount", "subscription_event_type"]
    search_fields = ["intent_id_of_invoice", "invoice_status"]
    raw_id_fields = ('payment_id',)

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    fields = [ 'tax_name','tax_display_name', 'tax_type', "tax_amount", "tax_country", "is_active"]
    list_display = ('tax_name','tax_display_name', 'tax_type', "tax_amount", "tax_country", "is_active", "created_at", "modified_at")
    search_fields = ["tax_country"]


@admin.register(TaxCollection)
class TaxCollectionAdmin(admin.ModelAdmin):
    fields = [ 'payment_id', 'tax_id', "tax_amount"]
    list_display = ('payment_id', 'tax_id', "tax_amount")


# @admin.register(PaymentCohort)
# class PaymentCohortAdmin(admin.ModelAdmin):
#     fields = ["payment", "cohort"]
#     list_display = ("payment", "cohort")
#     search_fields = []

#     def has_add_permission(self, request):
#         return False

#     def has_delete_permission(self, request, obj=None):
#         return False

#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs

#     def get_readonly_fields(self, request, obj=None):
#         if obj:
#             return ["payment", "cohort"]
#         else:
#             return []

class CouponDetailInline(admin.TabularInline):
    model = CouponDetail
    form = CouponDetailAdminForm
    fields = ['school','company','sponsor_compnay','cohort_program1','cohort_program2','cohort_program3']
    raw_id_fields = ('school','company','cohort_program1','cohort_program2','cohort_program3','sponsor_compnay')
    extra = 3
    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    form = CouponAdminForm
    fields = ["code", "name", "description", "coupon_type", "plan_type","plan", "discount_type", "start_date", "end_date", "is_active", "discount_value", "number_of_offered_plans","skip_course_dependency","is_course1_locked", "display_discounted_price_only",'is_fully_paid_by_school_or_company','is_for_middle_school','is_for_fast_track_program',"is_for_zanichelli"]
    list_display = ("code", "name", "coupon_type", "plan_type", "discount_type", "start_date", "end_date", "is_active", "discount_value",'is_for_middle_school','is_for_fast_track_program',"is_for_zanichelli")
    search_fields = ["code", "name", "coupon_type", "discount_type"]
    list_filter = ['coupon_type', 'discount_type', 'plan_type', 'is_active', ('end_date', DateRangeFilter), ('start_date', DateRangeFilter),'is_fully_paid_by_school_or_company','is_for_middle_school','is_for_fast_track_program',"is_for_zanichelli"]
    inlines = [CouponDetailInline,]
    # def has_add_permission(self, request):
    #     return True

    # def has_delete_permission(self, request, obj=None):
    #     return True

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(CouponDetail)
class CouponDetailAdmin(admin.ModelAdmin):
    search_fields = ['school', 'coupon']
    fields = ['school', 'coupon','cohort_program1','cohort_program2','cohort_program3','company','sponsor_compnay']
    list_display = ('school', 'coupon','cohort_program1','cohort_program2','cohort_program3','company','sponsor_compnay')
    list_filter = (('created_at', DateRangeFilter), 'school','coupon')
    raw_id_fields = ('school','coupon','cohort_program1','cohort_program2','cohort_program3','company','sponsor_compnay')
