from django import template
from student import models as stu_mdl
from userauth import models as auth_mdl
import logging
from courses import models
from student.models import StudentCohortMapper,CohortStepTracker, StudentScholarshipTestMapper, StudentScholarShipTest, StudentsPlanMapper, StudentActionItemDiary, StudentActionItemDiaryComment


register = template.Library()

from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

logger_console_adapter = logging.getLogger('console')
logger_console = CustomLoggerAdapter(logger_console_adapter, {})

@register.simple_tag
def current_plan(request,person):
    try:
        plan = person.studentPlans.filter(plan_lang=request.LANGUAGE_CODE)
        if(plan.count() > 0):
            plan_name = plan[0].plans.plan_name
        else:
            plan_name = "Not selected any plan"
    except Exception as ex:
        print(ex, "template tag-------------------")
        plan_name = "None"
    return plan_name

@register.filter
def in_langcode(stu_cohort, langcode):
    return stu_cohort.filter(stu_cohort_lang=langcode)

@register.simple_tag
def student_step_completed(cohort_module, step_obj, stu_obj):
    complete_count = 0
    response = {}
    try:
        # for student in stu_obj:
        #     stu_cohort_mapper_obj = student.stuMapID.filter(cohort__module=cohort_module).first()
        #     # for step in stu_cohort_mapper_obj:
        #     if stu_cohort_mapper_obj:
        #         stu_step_obj = stu_cohort_mapper_obj.stu_cohort_map.filter(step_status_id__step=step_obj.step_id, is_completed=True)
        #         if stu_step_obj.count() > 0:
        #             complete_count +=1
        lst_stu = list(stu_obj.values_list('id',flat=True))
        if step_obj.step_id == 28:
            obj_stu_steps = CohortStepTracker.objects.filter(stu_cohort_map__student__in = lst_stu, step_status_id__step__in=[step_obj.step_id,59])
        else:
            obj_stu_steps = CohortStepTracker.objects.filter(stu_cohort_map__student__in = lst_stu, step_status_id__step=step_obj.step_id)
        # print(obj_stu_steps_completed.count(),'----------------------')
        obj_stu_step_completed = 0
        for obj_stu_step in obj_stu_steps:
            if obj_stu_step.is_step_50_percentage_completed:
                obj_stu_step_completed += 1
        stud_obj_count = stu_obj.count()
        complete_count = obj_stu_step_completed
        status = complete_count * 100 / stud_obj_count
        response["complete_count"] = complete_count
        response["complete_per"] = round(status, 2)
        return response
    except Exception as e:
        print(e)
        response["complete_count"] = 0
        response["complete_per"] = 0
        return response

@register.simple_tag
def course_50_percentage_completion_rate(cohort_module,stu_obj):
    count_students = 0
    for student in stu_obj:
        stu_cohort_mapper_obj = student.stuMapID.filter(cohort__module=cohort_module).first()
        # for step in stu_cohort_mapper_obj:
        print(stu_cohort_mapper_obj)
        if stu_cohort_mapper_obj:
            if stu_cohort_mapper_obj.is_cohort_50_percentage_completed_of_unlocked_steps:
                count_students +=1
    try:
        percentage = count_students * 100 / stu_obj.count()
        return round(percentage, 2)
    except:
        return 0

@register.simple_tag
def check_the_unlocked_3_steps(cohort_module,stu_obj):
    stu_cohort_mapper_obj = stu_obj.first().stuMapID.filter(cohort__module=cohort_module).first()
    total_unlocked_steps = stu_cohort_mapper_obj.total_unlocked_steps
    return total_unlocked_steps

@register.simple_tag
def filter_by_module(stu, module_id):
    cohort = stu.student.stuMapID.filter(cohort__module__module_id = module_id)
    return cohort