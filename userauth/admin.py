from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from . models import Counselor, MasterOTP, Student, StudentSchoolDetail, School, Company, ClassYear, ClassName, Specialization, FuturelyAdmin, CountryDetails, StudentParentsDetail, StudentDeleteRequest, CounselorWithSpecialDashboard, HubspotCredential, CompanyWithSchoolDetail, CompanyDetail
from rangefilter.filters import DateRangeFilter
from related_admin import RelatedFieldAdmin
from related_admin import getter_for_related_field
from student.models import Todos, StudentsPlanMapper, StudentCohortMapper, StudentProgressDetail
from courses import models
from payment import models as PaymentModel

USER = get_user_model()

class PaymentInline(admin.TabularInline):
    model = PaymentModel.Payment
    fields = ('person', 'plan', "status", "coupon_code", "payment_method", "actual_amount", "discount",'tax_amount', "amount", "currency", "is_disputed", "dispute_type", "dispute_date", "refund", "refund_date", "stripe_id","payment_person_type","payment_subscription_type","payment_subscription_duration","payment_email_id","card_holder_name", "link_to_payment")
    readonly_fields = ['person', 'plan', "status", "coupon_code", "payment_method", "actual_amount", "discount",'tax_amount', "amount", "currency", "is_disputed", "dispute_type", "dispute_date", "refund", "refund_date", "stripe_id","payment_person_type","payment_subscription_type","payment_subscription_duration","payment_email_id","card_holder_name", "link_to_payment", ]
    extra=0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

class StudentCohortMapperInline(admin.TabularInline):
    model = StudentCohortMapper
    fields = ('stu_cohort_map_id', 'student', 'stu_cohort_lang', 'cohort', 'link_to_studentcohortmapper')
    readonly_fields = ['stu_cohort_map_id', 'student', 'stu_cohort_lang', 'cohort', 'link_to_studentcohortmapper',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class CohortInline(admin.TabularInline):
    model = models.Cohort
    fields = ('cohort_id', 'module', 'cohort_name', 'starting_date', 'price', 'duration', 'is_active', 'cohort_lang', 'cohort_type', 'link_to_cohort')
    readonly_fields = ['cohort_id', 'module', 'cohort_name', 'starting_date', 'price', 'duration', 'is_active', 'cohort_lang', 'cohort_type', 'link_to_cohort',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class StudentsPlanMapperInline(admin.TabularInline):
    model = StudentsPlanMapper
    fields = ('plans', 'plan_lang', 'is_trial_active', 'is_trial_expired', 'trial_type', 'trail_days', 'trial_start_date', 'trial_end_date', 'link_to_studentplanmapper')
    readonly_fields = ['plans', 'plan_lang', 'is_trial_active', 'is_trial_expired', 'trial_type', 'trail_days', 'trial_start_date', 'trial_end_date','link_to_studentplanmapper',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class StudentInline(admin.TabularInline):
    model = Student
    fields = ('are_you_a_student', 'are_you_fourteen_plus', 'company', 'discount_coupon_code', 'future_lab_form_status', 'src', 'number_of_offered_plans', 'skip_course_dependency', 'is_course1_locked', 'display_discounted_price_only', 'link_student')
    readonly_fields = ['are_you_a_student', 'are_you_fourteen_plus', 'company', 'discount_coupon_code', 'future_lab_form_status', 'src', 'number_of_offered_plans', 'skip_course_dependency', 'is_course1_locked', 'display_discounted_price_only', 'link_student',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

class CounselorInline(admin.TabularInline):
    model = Counselor
    fields = ('school_region', 'school_city', 'school_name', 'is_verified_by_futurely')
    readonly_fields = ['school_region', 'school_city', 'school_name', 'is_verified_by_futurely',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

class FuturelyAdminInline(admin.TabularInline):
    model = FuturelyAdmin
    fields = ('person','link_to_futurelyadmin',)
    readonly_fields = ['person','link_to_futurelyadmin',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


class TodosInline(admin.TabularInline):
    model = Todos
    fields = ('title', 'description', 'is_deleted')
    readonly = ['title', 'description', 'is_deleted',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(USER)
class PersonAdmin(UserAdmin):
    """User Admin"""
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',)
        }),)
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
    ]
    list_display = (
        "username",
        "first_name",
        "last_name",
        "gender",
        "gender_other",
        "is_active",
        "is_staff",
        "is_superuser",
        "email_verified",
        "contact_number",
        "how_know_us",
        "how_know_us_other",
        "last_visit",
        "country_name",
        "lang_code",
        "clarity_token",
    )
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'email_verified', 'how_know_us', ('created_at',DateRangeFilter))

    fieldsets = (
        ("Essentials", {"fields": ("username", "password",
                                   "last_login","last_visit" ,"date_joined", "modified_at")}),
        ("Personal Information", {
         "fields": ("first_name", "last_name", "email", "contact_number", "how_know_us", "how_know_us_other","lang_code","clarity_token" )}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "email_verified", 'user_permissions')}),

    )
    inlines = [FuturelyAdminInline, CounselorInline, StudentInline, StudentsPlanMapperInline, StudentCohortMapperInline,]

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["date_joined", "last_login", "modified_at"]
        else:
            return []

class StudentSchoolDetailsInline(admin.TabularInline):
    model = StudentSchoolDetail
    fields = ['class_year', 'class_name', 'specialization', 'school_region', 'school_city', 'school_name', 'school_type', 'graduation_year', 'link_to_studentschooldetail',]
    readonly_fields = ['class_year', 'class_name', 'specialization', 'school_region', 'school_city', 'school_name', 'school_type', 'graduation_year', 'link_to_studentschooldetail',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True




class ClassYearInline(admin.TabularInline):
    model = ClassYear
    fields = ['name', 'country']
    readonly_fields = ['name', 'country']
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(StudentParentsDetail)
class StudentParentsDetailAdmin(admin.ModelAdmin):
    raw_id_fields = ['student']
    fields = ['student', 'parent_name', 'parent_contact_number', 'parent_email','parent_email_from_reg']
    list_display = ('student', 'parent_name', 'parent_contact_number', 'parent_email','parent_email_from_reg')
    search_fields = ["student__person__username"]

class StudentParentsDetail(admin.TabularInline):
    model = StudentParentsDetail
    fields = ['student', 'parent_name', 'parent_contact_number', 'parent_email','parent_email_from_reg']
    readonly_fields = ['student', 'parent_name', 'parent_contact_number', 'parent_email','parent_email_from_reg']
    extra = 0
    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

class StudentProgressDetailInline(admin.TabularInline):
    model = StudentProgressDetail
    fields = ['endurance_score', 'confidence_score', 'awareness_score', 'curiosity_score']
    readonly_fields = ['endurance_score', 'confidence_score', 'awareness_score', 'curiosity_score']
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return True

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    
    fields = ["person", "are_you_a_student", "are_you_fourteen_plus", 'company', 'src', 'discount_coupon_code', 'future_lab_form_status', "number_of_offered_plans", "skip_course_dependency", "is_course1_locked", "display_discounted_price_only",'total_pcto_hours','is_welcome_video_played','is_step1_pdf_downloaded', "is_from_middle_school","is_from_fast_track_program","student_channel","privacy_policy_mandatory","accept_tracking","accept_data_third_party","accept_marketing", 'age','sponsor_compnay']
    list_display = ("person","person__username", "are_you_a_student", "are_you_fourteen_plus", 'company', 'src', 'discount_coupon_code', 'age','sponsor_compnay')
    search_fields = ["person__username"]
    list_filter = ['src', 'are_you_a_student', 'company',"number_of_offered_plans",'skip_course_dependency',"is_course1_locked","sponsor_compnay"]
    raw_id_fields = ['person']
    person__username = getter_for_related_field('person__username', short_description='Username')
    inlines = [StudentSchoolDetailsInline, StudentParentsDetail, StudentProgressDetailInline]

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []


@admin.register(StudentSchoolDetail)
class StudentSchoolDetailAdmin(admin.ModelAdmin):

    fields = ["student", "class_year", "class_name", "specialization", "school_region", "school_city", "school_name", "school_type", "graduation_year"]
    list_display = ("student","student__person__username", "class_year", "class_name", "specialization", "school_region", "school_city", "school_name", "school_type", "graduation_year")
    search_fields = ["student__person__username","school_region", "school_city", "school_name", "school_type", "graduation_year"]
    list_filter = ['specialization', 'class_name', 'class_year']
    raw_id_fields = ["student"]
    student__person__username = getter_for_related_field('student__person__username', short_description='Username')

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(Counselor)
class CounselorAdmin(admin.ModelAdmin):

    fields = ["person", "school_region", "school_city", "school_name", "company", "academic_session_start_date", "is_verified_by_futurely",'plans','coupon_code','is_for_fast_track_program_only', 'is_for_middle_school_only', 'is_trial_account','course_module']
    list_display = ("person","person__username", "school_region", "school_city", "school_name", "company", "academic_session_start_date", "is_verified_by_futurely")
    list_filter = [ "is_verified_by_futurely", "is_for_fast_track_program_only","is_for_middle_school_only","school_region", "school_city", "company", "school_name"]
    raw_id_fields = ["person",'course_module']
    search_fields = ['person__username']
    person__username = getter_for_related_field('person__username', short_description='Username')


    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(CounselorWithSpecialDashboard)
class CounselorWithSpecialDashboardAdmin(admin.ModelAdmin):
    list_display = ['pk', 'counselor', ]
    fields = ['counselor']
    raw_id_fields = ["counselor",]
    

@admin.register(FuturelyAdmin)
class FuturelyAdminAdmin(admin.ModelAdmin):

    fields = ["person",]
    list_display = ("person","person__username", )
    raw_id_fields = ["person"]
    search_fields = ['person__username']
    person__username = getter_for_related_field('person__username', short_description='Username')


    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):

    fields = ["name", "region", "city", "type", "is_verified","country"]
    list_display = ("name", "region", "city", "type", "is_verified",'country')
    search_fields = ["name", "region", "city", "type",'country']
    list_filter = ['is_verified', 'region', 'city','country']

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(CountryDetails)
class CountryDetailsAdmin(admin.ModelAdmin):

    fields = [ "region", "city","country"]
    list_display = ( "region", "city",'country')
    search_fields = ["region", "city",'country']
    list_filter = ['region', 'city','country']

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):

    fields = ["name", "country"]
    list_display = ("name", "country")
    search_fields = ["name"]
    list_filter = ['country']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []


@admin.register(CompanyDetail)
class CompanyDetailAdmin(admin.ModelAdmin):

    fields = ["company", "is_display_specific_job_posts"]
    list_display = ("company", "is_display_specific_job_posts")
    search_fields = ["company"]
    list_filter = ["company",'is_display_specific_job_posts']
    raw_id_fields = ['company',]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(ClassYear)
class ClassYearAdmin(admin.ModelAdmin):

    fields = ["name", "country", "year_sno"]
    list_display = ("name", "country")
    search_fields = ["name"]
    list_filter = ['country']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []
        
@admin.register(ClassName)
class ClassNameAdmin(admin.ModelAdmin):

    fields = ["name", "country", "name_sno"]
    list_display = ("name", "country")
    search_fields = ["name"]
    list_filter = ['country']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):

    fields = ["name", "country"]
    list_display = ("name", "country")
    search_fields = ["name"]
    list_filter = ['country']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return []
        else:
            return []

@admin.register(StudentDeleteRequest)
class StudentDeleteRequestAdmin(admin.ModelAdmin):
    fields = ['student', 'subject','reason_message', 'lang_code', 'is_status']
    list_display = ('student', 'subject', 'reason_message','lang_code', 'is_status')
    list_filter = ['lang_code', 'is_status']

admin.site.register(MasterOTP)
admin.site.unregister(Group)


@admin.register(HubspotCredential)
class HubspotCredentialAdmin(admin.ModelAdmin):
    list_display = ['title','value']

@admin.register(CompanyWithSchoolDetail)
class CompanyWithSchoolDetailAdmin(admin.ModelAdmin):
    list_display = ['id', 'company', 'company_path_type']
    raw_id_fields = ['company',]
    list_filter = ['company_path_type']