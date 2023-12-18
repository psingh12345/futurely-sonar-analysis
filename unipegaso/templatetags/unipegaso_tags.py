from django import template
from unipegaso.models import *

register = template.Library()

@register.simple_tag
def get_student_full_name(stu_id):
    try:
        stu_obj = StudentDetail.objects.get(pk=stu_id)
        full_name = f"{stu_obj.first_name} {stu_obj.last_name}"
        return full_name
    except Exception as Error:
        print(f"Error in unipegaso template tag - {Error}")
        return "Anonymous User"
    
@register.simple_tag
def get_vdo_link(option):
    try:
        question = UnipegasoActionItemsNextQuestion.objects.filter(sno=9).first()
        option_obj = UnipegasoActionItemsNextQuestionOption.objects.filter(option=option, unipegaso_next_question=question).first()
        link_obj = UnipegasoVideoOptionLink.objects.filter(unipegaso_option=option_obj).first()
        print(link_obj)
        if link_obj:
            return link_obj.link
    except Exception as error:
        print(error)
    return "#"