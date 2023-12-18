from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.forms.widgets import SelectDateWidget
from . models import Student, StudentParentsDetail
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core import validators

PERSON = get_user_model()

CHOICES_GENDER = [
    ("Select", _("Select")),
    ("Male", _("Male")),
    ("Female", _("Female")),
    ("Other", _("Other"))
]

class FuturelyFirstStageForm(forms.Form):
    first_name = forms.CharField(max_length=100, error_messages={"required": _("Please enter your first name")}, required=True)
    last_name = forms.CharField(max_length=100, error_messages={"required": _("Please enter your last name")}, required=True)
    password = forms.CharField(widget=forms.PasswordInput(),validators=[validate_password], required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(),required=True)
    email = forms.CharField(max_length=254, widget=forms.EmailInput(), error_messages={'invalid': 'Please enter the valid email address'}, required=True)
    gender = forms.ChoiceField(choices=CHOICES_GENDER, error_messages={"required": _("Please select the gender")}, required=True)
    contact_number = forms.CharField(max_length=20, required=False)

    def __init__(self, *args, **kwargs):
        super(FuturelyFirstStageForm, self).__init__(*args, **kwargs)
        # self.fields['first_name'].error_messages = {'required': 'custom required message'}

        # if you want to do it to all of them
        # for field in self.fields.values():
        #     field.error_messages = {'required':_('The field  is required').format(
        #         fieldname=field.label)}

CHOICES_HOW_KNOW_US = [
    ("Select", "Select"),
    ("Facebook", "Facebook"),
    ("Instagram", "Instagram"),
    ("Tik Tok", "Tik Tok"),
    ("Google", "Google"),
    ("Friends", _("Friends")),
    ("Parents", _("Parents")),
    ("School", _("School")),
    ("Radio", "Radio"),
    ("News Paper", _("News Paper")),
    ("Linkedin", "Linkedin"),
    ("Other", _("Other")),
]

class MiddleSchoolParentsDetailForm(forms.ModelForm):

    # def __init__(self, *args, **kwargs):
    #     super(MiddleSchoolParentsDetailForm, self).__init__(*args, **kwargs)
    #     attrs = {'required': True}
    #     for field in self.fields.values():
    #         field.widget.attrs = attrs
    class Meta:
        model = StudentParentsDetail
        fields = ('parent_name', 'parent_contact_number', 'parent_email')

class FuturelySecondStageForm(forms.Form):
    # discount_code = forms.CharField(max_length=50, error_messages={"required": _("Please enter the valid discount code")}, required=True)
    how_know_us = forms.ChoiceField(choices=CHOICES_HOW_KNOW_US, error_messages={"required": _("Please select the option")}, required=True)
    # parents_mobile_number = forms.CharField(max_length=20, error_messages={"required": _("Please enter parents mobile number")}, required=True)
    parents_mobile_number = forms.CharField(max_length=20,required=False)
    parents_email = forms.CharField(max_length=254, widget=forms.EmailInput(), required=False)
    # parents_email = forms.CharField(max_length=254, widget=forms.EmailInput(), error_messages={'invalid': 'Please enter the valid email address'}, required=True)
    how_know_us_other = forms.CharField(max_length=50, error_messages={"required": _("Please enter the other option")}, required=False)

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "text-box form-control",
                "name": "username",
                "placeholder": _("Email address"),

            }
        ), required=True,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "text-box form-control",
                "id": "loginPassInput",
                "value": "",
                "name": "password",
                "placeholder": _("Password"),

            }
        )
    )


class FutureLabPersonRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    username = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(FutureLabPersonRegisterForm, self).__init__(*args, **kwargs)
        attrs = {'class': 'form-control', 'required': True}
        # if self.instance and self.instance.pk:
        #     self.fields.pop('username', None)
        for field in self.fields.values():
            field.widget.attrs = attrs
        # self.fields['password'].required = False
        # self.fields['last_name'].required = False

    def clean(self):
        cleaned_data = super(FutureLabPersonRegisterForm, self).clean()
        password = cleaned_data.get("password")
        email = cleaned_data.get("email")
        try:
            validate_email(email)
        except forms.ValidationError as e:
            raise forms.ValidationError(_("Enter a valid email address"))

        if password == "" or password == None:
            self.fields.pop('password', None)

    def save(self, commit=True):
        m = super(FutureLabPersonRegisterForm, self).save(commit=False)
        m.set_password(self.cleaned_data['password'])
        if commit:
            m.save()
        return m

    class Meta:
        model = PERSON
        fields = ("first_name", "last_name", "username",
                  "email", "password", "contact_number", "how_know_us", "how_know_us_other", "gender",'gender_other')  # confirm_password

class PersonRegisterForm(forms.ModelForm):
    # confirm_password = forms.CharField(widget=forms.PasswordInput())
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    username = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(PersonRegisterForm, self).__init__(*args, **kwargs)
        # self.fields['how_know_us'].empty_label = "How did you get to know us?"
        # self.fields['how_know_us'].widget.choices = self.fields['how_know_us'].choices
        attrs = {'class': 'form-control', 'required': True}
        if self.instance and self.instance.pk:
            self.fields.pop('username', None)
        for field in self.fields.values():
            field.widget.attrs = attrs
        self.fields['how_know_us_other'].widget.attrs = {'required': False}
        self.fields['how_know_us'].widget.attrs = {'required': False}
        self.fields['contact_number'].widget.attrs = {'required': False}
        self.fields['gender_other'].widget.attrs = {'required': False}

    def clean(self):
        cleaned_data = super(PersonRegisterForm, self).clean()
        password = cleaned_data.get("password")
        # confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")
        # if password != confirm_password:
        #     raise forms.ValidationError("Password and Confirm Password does not match")
        try:
            validate_email(email)
        except forms.ValidationError as e:
            raise forms.ValidationError(_("Enter a valid email address"))
        # if password == "" or confirm_password == "" or  password == None or confirm_password == None:
        #     self.fields.pop('password', None)
            # self.fields.pop('confirm_password', None)
        if password == "" or password == None:
            self.fields.pop('password', None)

    def save(self, commit=True):
        m = super(PersonRegisterForm, self).save(commit=False)
        if commit:
            m.save()
        return m

    class Meta:
        model = PERSON
        fields = ("first_name", "last_name", "username",
                  "email", "password", "contact_number", "how_know_us", "how_know_us_other", "gender",'gender_other')  # confirm_password

class CounselorRegisterForm(forms.ModelForm):
    # confirm_password = forms.CharField(widget=forms.PasswordInput())
    password = forms.CharField(widget=forms.PasswordInput())
    # confirm_password = forms.CharField(widget=forms.PasswordInput())
    username = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(CounselorRegisterForm, self).__init__(*args, **kwargs)
        # self.fields['how_know_us'].empty_label = "How did you get to know us?"
        # self.fields['how_know_us'].widget.choices = self.fields['how_know_us'].choices
        attrs = {'class': 'form-control', 'required': True}
        if self.instance and self.instance.pk:
            self.fields.pop('username', None)
        for field in self.fields.values():
            field.widget.attrs = attrs
        self.fields['how_know_us_other'].widget.attrs = {'required': False}
        self.fields['how_know_us'].widget.attrs = {'required': False}
        self.fields['contact_number'].widget.attrs = {'required': False}
        self.fields['gender_other'].widget.attrs = {'required': False}
        # self.fields['confirm_password'].widget.attrs = {'required': False}

    def clean(self):
        cleaned_data = super(CounselorRegisterForm, self).clean()
        password = cleaned_data.get("password")
        # confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")
        # if password != confirm_password:
        #     raise forms.ValidationError("Password and Confirm Password does not match")
        try:
            validate_email(email)
        except forms.ValidationError as e:
            raise forms.ValidationError(_("Enter a valid email address"))
        # if password == "" or confirm_password == "" or  password == None or confirm_password == None:
        #     self.fields.pop('password', None)
            # self.fields.pop('confirm_password', None)
        if password == "" or password == None:
            self.fields.pop('password', None)

    def save(self, commit=True):
        m = super(CounselorRegisterForm, self).save(commit=False)
        if commit:
            m.save()
        return m

    class Meta:
        model = PERSON
        fields = ("first_name", "last_name", "username",
                  "email", "password", "contact_number", "how_know_us", "how_know_us_other", "gender",'gender_other')  # confirm_password

class PasswordResttingForm(PasswordResetForm):
    email = forms.CharField(max_length=254,
                            widget=forms.EmailInput(
                                attrs={
                                    "class": "text-box form-control email_validation",
                                    'required': True,
                                    'placeholder': _("Email address"),
                                }
                            )
                            )

    class Meta:
        fields = ('email')


class PasswordSetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "text-box form-control",
                "placeholder": _("Password"),
                "type": 'password',
            }
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "text-box form-control",
                "placeholder": _("Confirm new password"),
                "type": 'password',
            }
        )
    )

    class Meta:
        fields = ('new_password1', 'new_password2')


class StudentCompletionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentCompletionForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(StudentCompletionForm, self).clean()
        raw_data = self.data
        are_you_a_student = raw_data.get("are_you_a_student")

        if "are_you_a_student" in raw_data and are_you_a_student != "Yes" and are_you_a_student != "No":
            raise forms.ValidationError(_("Please select the correct option for 'Are You Student?'"))

    class Meta:
        model = Student
        fields = ['are_you_a_student', 'discount_coupon_code', 'number_of_offered_plans',"skip_course_dependency","is_course1_locked"]
        widgets = {'are_you_a_student': forms.HiddenInput()}


class EmailVerifyForm(forms.Form):
    email = forms.CharField(max_length=254,
                            widget=forms.EmailInput(
                                attrs={
                                    "class": "text-box form-control",
                                    'required': True,
                                    'placeholder': _("Email address"),
                                }
                            ), required=True
                            )

    class Meta:
        fields = ('email')
