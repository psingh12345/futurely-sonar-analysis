from django.contrib import admin
from .models import CustomEvent
from rangefilter.filters import DateRangeFilter
from related_admin import RelatedFieldAdmin


@admin.register(CustomEvent)
class CustomEventAdmin(RelatedFieldAdmin):

    fields = ["person", "event_name", "user_agent", "page_url", "ip_address", "custom_user_session_id", "meta_data", "created_at"]
    list_display = ("person","person__username", "event_name", "user_agent", "page_url", "ip_address", "custom_user_session_id", "meta_data", "created_at")
    search_fields = ["person__username","event_name", "user_agent", "page_url", "ip_address", "custom_user_session_id", "meta_data"]
    list_filter = ["event_name", "event_id", ('created_at',DateRangeFilter)]

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["person", "event_name", "user_agent", "page_url", "ip_address", "custom_user_session_id", "meta_data", "created_at"]
        else:
            return []
