from django.db import models
from django.utils import timezone
from userauth.models import Person
# from django.utils.translation import ugettext_lazy as _


EVENT_NAMES = [
    ((1), ('Sign up - Stage 1 Success')),
    ((2), ('Sign up - Stage 2 Success')),
    ((3), ('Login - Success')),
    ((4), ('Login - Fail')),
    ((5), ('Payment - Success')),
    ((6), ('Payment - Fail')),
    ((7), ('Home')),
    ((8), ('Students')),
    ((9), ('High Schools')),
    ((10), ('About us')),
    ((11), ('dashboard')),
    ((12), ('404')),
    ((13), ('Course 1 purchase')),
    ((14), ('Course 1 and 2 purchase')),
    ((15), ('Cohort Info')),
    ((16), ('Student Query - Success')),
    ((17), ('Student Query - Fail')),
    ((18), ('Mentors')),
    ((19), ('Plans')),
    ((20), ('Sign up - Stage 1 Visited')),
    ((21), ('Sign up - Stage 2 Visited')),
    ((22), ('All cookies accepted')),
    ((23), ('Clicked on customize cookies')),
    ((24), ('Cookies policy page visited')),
    ((25), ('Privacy policy page visited')),
    ((26), ('Terms of use page visited')),
]


class TimeStampModel(models.Model):
    """TimeStamp Model"""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    modified_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True


class CustomEvent(TimeStampModel):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True, related_name="events")
    event_id = models.CharField(max_length=50, blank=False, null=False, choices=EVENT_NAMES)
    event_name = models.CharField(max_length=50, blank=False, null=False)
    user_agent = models.CharField(max_length=2000, blank=True, null=True)
    page_url = models.CharField(max_length=500, blank=True, null=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    custom_user_session_id = models.CharField(max_length=200, blank=False, null=False)
    meta_data = models.JSONField(default=dict)
    class Meta:
        verbose_name = 'CustomEvent'
        verbose_name_plural = 'CustomEvent'

    def __str__(self):
        return "{}".format(self.event_name)
