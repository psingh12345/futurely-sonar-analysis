from django import forms
from .models import *

class StudentUniPegasoForm(forms.ModelForm):

    class Meta:
        model = StudentDetail
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'college', 'year_of_enrollment')