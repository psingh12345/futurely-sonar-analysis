from django import forms
from .models import ParentInfo

class ParentInfoForm(forms.ModelForm):
    parent_name = forms.CharField(widget=forms.TextInput(), required=True)
    parent_email = forms.EmailField(widget=forms.TextInput(), required=True)
    child_name = forms.CharField(widget=forms.TextInput(), required=True)
    child_email = forms.EmailField(widget=forms.TextInput(), required=False)
    child_number = forms.CharField(widget=forms.TextInput(), required=False)
    company_name = forms.CharField(required=False)
    school_path = forms.CharField(widget=forms.TextInput(), required=True)


    class Meta:
        model = ParentInfo
        fields = ['parent_name', 'parent_email', 'child_name', 'child_email', 'child_number', 'company_name', 'school_path']
