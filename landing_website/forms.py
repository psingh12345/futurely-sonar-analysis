from django import forms
from .models import Newsletter, ContactUs


class ContactUsForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ('first_name','last_name','email','organization','organization_name_other','role','concern','phone_number', 'company_name')