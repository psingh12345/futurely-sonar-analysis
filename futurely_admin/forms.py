from dataclasses import fields
from pyexpat import model
from django import forms
from courses.models import EmailForwadingDetails, PushNotificationTopics, PushNotificationRecords, CohortPushNotificationRecords

class FormEmailExcelData(forms.ModelForm):
    class Meta:
        model = EmailForwadingDetails
        fields = ['excel_file', 'emailtemplate_id']

class SendPashNotificationForm(forms.ModelForm):
    class Meta:
        model = PushNotificationRecords
        fields = ['topic', 'title', 'body','response_msg_id']
        widgets = {'response_msg_id': forms.HiddenInput()}

class CohortSendPushNotificationForm(forms.ModelForm):
    class Meta:
        model = CohortPushNotificationRecords
        fields = ['topic', 'title', 'body','response_msg_id']
        widgets = {'response_msg_id': forms.HiddenInput()}