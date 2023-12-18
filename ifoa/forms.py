from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import IFOAStudentDetail

class IFOAStudentDetailForm(forms.ModelForm):
    date_of_birth = forms.DateField(label=_("Date of Birth"), widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    class Meta:
        model = IFOAStudentDetail
        fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'birth_place', 'tax_id_code', 'email', 'phone_number', 'how_did_you_know_us']
