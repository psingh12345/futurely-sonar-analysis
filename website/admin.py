from django.contrib import admin
from .models import Query
from django.contrib.auth import get_user_model
from rangefilter.filters import DateRangeFilter
from .models import FaqModel
from . import models

# Register your models here.
USER = get_user_model()

@admin.register(FaqModel)
class FaqAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content']
    list_filter = ['locale']
    

@admin.register(models.Webinars)
class WebinarsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['title', 'description','publish_date','module_lang']
    list_filter = ['module_lang', ('publish_date', DateRangeFilter)]

@admin.register(models.MentorsInfo)
class MentorsInfoAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['m_name','title', 'description','module_lang']
    list_filter = ['module_lang']

@admin.register(models.DiamnodQuery)
class DiamnodQueryAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['email','phone_num', 'status']
    search_fields = ['email','phone_num']
    list_filter = ['status']

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    
    fields = ["person", "name", "email", 'message', 'status', 'modified_at', 'created_at']
    list_display = ("person", "name", "email", 'status', 'created_at')
    search_fields = ["name", "email", 'message', 'status']
    list_filter = ['status', ('created_at', DateRangeFilter)]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["person", "name", "email", 'message', 'status', 'modified_at', 'created_at']
        else:
            return []

@admin.register(models.Testimonials)
class TestimonialsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['name','designation','category','feedback','module_lang']
    list_filter = ['designation', 'category']

@admin.register(models.Files)
class FilesAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id','title','file','fileLink']
    search_fields = ["title",]
    

@admin.register(models.ParentInfo)
class ParentInfoAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = [ 'id', 'parent_name', 'parent_email' , 'child_name' , 'child_email' , 'child_number']

@admin.register(models.CookiesSelectedData)
class CookiesSelectedDataAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['clarity_id','custom_session_id','cookies_necessari','cookies_esperienza', 'cookies_misurazione', 'cookies_selected_section']
    list_filter = ['cookies_necessari', 'cookies_esperienza', 'cookies_misurazione', 'cookies_selected_section']
    search_fields = ['clarity_id','custom_session_id']