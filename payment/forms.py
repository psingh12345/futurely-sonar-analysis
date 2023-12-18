from django import forms
from django.core.exceptions import ValidationError
from .models import Coupon, CouponDetail
from courses import models as courseMdl

class CouponDetailAdminForm(forms.ModelForm):
    class Meta:
        model = CouponDetail
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        school = cleaned_data.get('school')
        company = cleaned_data.get('company')
        sponsor_compnay = cleaned_data.get('sponsor_compnay')
        cohort_program1 = cleaned_data.get('cohort_program1')
        coupon = cleaned_data.get('coupon')
        if coupon is not None:
            if coupon.coupon_type == "Organization":
                if school is not None:
                    raise ValidationError('You can not link a school with an Organization coupon code.')
                if company is None:
                    raise ValidationError('You have to link this coupon code with a company.')
            else:
                if school is None:
                    raise ValidationError('You have to link a school with an Futurelab or general coupon code.')
                if company is not None:
                    raise ValidationError('You can not link this coupon code with a company.')
            if coupon.plan.plan_name == courseMdl.PlanNames.FastTrack.value:
                if cohort_program1 is None or cohort_program1.is_for_fast_track_program is False:
                    raise ValidationError('Please select the correct cohort')
                if sponsor_compnay:
                    raise ValidationError('Error - You can not link sponsor_compnay with Fast track coupon code.')
            elif coupon.plan.plan_name == courseMdl.PlanNames.MiddleSchool.value:
                if cohort_program1 is None or cohort_program1.is_for_middle_school is False:
                    raise ValidationError('Please select the correct cohort')
                if sponsor_compnay:
                    raise ValidationError('Error - You can not link sponsor_compnay with Middle School coupon code.')
            elif coupon.plan.plan_name == courseMdl.PlanNames.JobCourse.value:
                if cohort_program1 is None or cohort_program1.is_for_middle_school is True or cohort_program1.is_for_fast_track_program is True:
                    raise ValidationError('Please select the correct cohort')
        else:
            raise ValidationError('Coupon code is required')
        return cleaned_data

class CouponAdminForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = '__all__'

    def clean_plan_type(self):
        plan_type = self.cleaned_data.get('plan_type')
        if plan_type is None:
            raise ValidationError("Please select the Plan Type.")
        return plan_type
    
    def clean_plan(self):
        plan = self.cleaned_data.get('plan')
        plan_type = self.cleaned_data.get('plan_type')
        if plan is not None:
            if plan_type == courseMdl.PlanNames.FastTrack.value:
                if plan.plan_name != courseMdl.PlanNames.FastTrack.value:
                    raise ValidationError("Please select the any 'FastTrack' Plan.")
            elif plan_type == courseMdl.PlanNames.MiddleSchool.value:
                if plan.plan_name != courseMdl.PlanNames.MiddleSchool.value:
                    raise ValidationError("Please select the any 'MiddleSchool' Plan.")
            elif plan_type == courseMdl.PlanNames.JobCourse.value:
                if plan.plan_name != courseMdl.PlanNames.JobCourse.value:
                    raise ValidationError("Please select the any 'JobCourse' Plan.")
        else:
            raise ValidationError('Please select the Plan.')
        return plan
    
    def clean_discount_type(self):
        discount_type = self.cleaned_data.get('discount_type')
        if discount_type == 'Fixed':
            raise ValidationError("Please select the discount type of 'Percentage'.")
        return discount_type
    
    def clean_discount_value(self):
        discount_value = self.cleaned_data.get('discount_value')
        if discount_value != 100:
            raise ValidationError("You have to enter the value as 100% only")
        return discount_value
    
    def clean_is_fully_paid_by_school_or_company(self):
        is_fully_paid_by_school_or_company = self.cleaned_data['is_fully_paid_by_school_or_company']
        if self.cleaned_data['is_fully_paid_by_school_or_company'] == False:
            raise ValidationError("Please select it as 'True'.")
        return is_fully_paid_by_school_or_company
    
    def clean_is_for_fast_track_program(self):
        is_for_fast_track_program = self.cleaned_data['is_for_fast_track_program']
        plan_type = self.cleaned_data.get('plan_type')
        if plan_type == courseMdl.PlanNames.FastTrack.value:
            if is_for_fast_track_program == False:
                raise ValidationError("Please select the 'is_for_fast_track_program' - True.")
            
        elif plan_type == courseMdl.PlanNames.MiddleSchool.value:
            if is_for_fast_track_program:
                raise ValidationError("Please select the 'is_for_fast_track_program' - No.") 
            
        elif plan_type == courseMdl.PlanNames.JobCourse.value:
            if is_for_fast_track_program:
                raise ValidationError("Please select the 'is_for_fast_track_program' - No.")
            
        return is_for_fast_track_program
    
    def clean_is_for_middle_school(self):
        is_for_middle_school = self.cleaned_data['is_for_middle_school']
        plan_type = self.cleaned_data.get('plan_type')

        if plan_type == courseMdl.PlanNames.FastTrack.value:
            if is_for_middle_school:
                raise ValidationError("Please select the 'is_for_middle_school' - No.")
            
        elif plan_type == courseMdl.PlanNames.MiddleSchool.value:
            if is_for_middle_school == False:
                raise ValidationError("Please select the 'is_for_middle_school' - Yes.")
            
        elif plan_type == courseMdl.PlanNames.JobCourse.value:
            if is_for_middle_school:
                raise ValidationError("Please select the 'is_for_middle_school' - No.")
        return is_for_middle_school