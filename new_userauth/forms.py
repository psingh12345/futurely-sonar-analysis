
from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.forms.widgets import SelectDateWidget
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core import validators
from userauth.models import Student
from captcha.fields import ReCaptchaField 
from captcha.widgets import ReCaptchaV2Invisible, ReCaptchaV3, ReCaptchaV2Checkbox

PERSON = get_user_model()

CHOICES_GENDER_OPTIONS = [
    ("Male", _("Male")),
    ("Female", _("Female")),
    ("Other", _("Other")),
]

CHOICES_YES_NO = [
    ("Yes", _("Yes")),
    ("No", _("No")),
]

CHOICES_AGE = [
    ('14', '14'),
    ('15', '15'),
    ('16', '16'),
    ('17', '17'),
    ('18', '18'),
    ('19', '19'),
    ('20', '20'),
    ('21', '21'),
    ('22', '22'),
    ('23', '23'),
    ('24', '24'),
    ('25+', '25+'),
]

class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=100, error_messages={"required": _("Campo obbligatorio")}, required=True)
    last_name = forms.CharField(max_length=100, error_messages={"required": _("Campo obbligatorio")}, required=True)
    gender = forms.ChoiceField(choices=CHOICES_GENDER_OPTIONS, error_messages={"required": _("Campo obbligatorio")}, required=True)
    age = forms.ChoiceField(choices=CHOICES_AGE, error_messages={"required": _("Campo obbligatorio")}, required=False)
    # are_you_fourteen_plus = forms.ChoiceField(choices=CHOICES_YES_NO, error_messages={"required": _("Please select the option")}, required=True)
    contact_number = forms.CharField(max_length=20, error_messages={"required": _("Campo obbligatorio")}, required=True)
    email = forms.CharField(max_length=254, widget=forms.EmailInput(), error_messages={'invalid': 'Please enter the valid email address'}, required=True)
    password = forms.CharField(widget=forms.PasswordInput(),validators=[validate_password], min_length=8, required=True)

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)


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


class UserOnboardingRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    username = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(UserOnboardingRegisterForm, self).__init__(*args, **kwargs)
        attrs = {'class': 'form-control', 'required': True}
        for field in self.fields.values():
            field.widget.attrs = attrs

    def clean(self):
        cleaned_data = super(UserOnboardingRegisterForm, self).clean()
        password = cleaned_data.get("password")
        email = cleaned_data.get("email")
        try:
            validate_email(email)
        except forms.ValidationError as e:
            raise forms.ValidationError(_("Enter a valid email address"))

        if password == "" or password == None:
            self.fields.pop('password', None)

    def save(self, commit=True):
        m = super(UserOnboardingRegisterForm, self).save(commit=False)
        m.set_password(self.cleaned_data['password'])
        if commit:
            m.save()
        return m

    class Meta:
        model = PERSON
        fields = ("first_name", 
                  "last_name", 
                  "username",
                  "email", 
                  "password", 
                  "contact_number", 
                  "gender",
                  "contact_number")

class ForgotPasswordSetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input100 field-input",
                "placeholder": "Nuova password",
                "type": 'password',
                "id": "id_password1",
            }
        )
    )

    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "input100 field-input",
                "placeholder": "Ripeti la password",
                "type": 'password',
                "id": "id_password2"
            }
        )
    )

    class Meta:
        fields = ('new_password1', 'new_password2')

class FormWithCaptcha(forms.Form):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)