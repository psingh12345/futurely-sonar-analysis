import json, openai
import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.translation import ugettext as _
import logging
from . import models
from lib.hubspot_contact_sns import create_update_contact_hubspot
from django.contrib.auth import get_user_model
import pytz, datetime, json
from courses import models as courseMdl

# from lib.custom_logging import CustomLoggerAdapter

logger = logging.getLogger("watchtower")
# logger = CustomLoggerAdapter(adapter, {})

PERSON = get_user_model()


@shared_task(bind=True)
def update_hubspot_properties(self, email, keys_list, values_list):
    properties = []
    data_dict = {}
    try:
        logger.info(f"In hubspot sns module for : {email}")
        for idx in range(len(keys_list)):
            data_dict["property"] = keys_list[idx]
            data_dict["value"] = values_list[idx]
            properties.append(data_dict.copy())
            data_dict.clear()
        final_data_dict = {"properties": properties}
        data = json.dumps(final_data_dict)
        print(f"Date after dump : {data}")
        print(final_data_dict["properties"][0]["value"])
        response = settings.CLIENT.publish(
            TopicArn="arn:aws:sns:eu-south-1:994790766462:lambdasns", Message=data
        )
        logger.info(f"In hubspot sns triggered with response {response} for : {email}")
    except Exception as ex:
        logger.critical(
            f"Error at hubspot SNS module for parameter update {ex} for user : {email}"
        )


@shared_task(bind=True)
def create_hubspot_tickets(self, user, email, subject, question):
    try:
        logger.info(
            f"In celery task to create hubspot ticket for user - {email} and user {user}"
        )
        properties = {
            "hs_pipeline": "0",
            "hs_pipeline_stage": "1",
            "hs_ticket_priority": "HIGH",
            "hubspot_owner_id": "138612775",
            "subject": subject,
            "content": question,
            "email": email,
        }
        data = json.dumps(properties)
        response = settings.CLIENT.publish(
            TopicArn="arn:aws:sns:eu-south-1:994790766462:sns_create_hubspot_ticket",
            Message=data,
        )
        logger.info(
            f"In celery task to create hubspot ticket - SNS is published - for user - {email} and user {user}"
        )
    except Exception as ex:
        logger.error(
            f"Error to submit the ticket : {email} and user {user}: and exception is: {ex}"
        )


@shared_task(bind=True)
def step_completions(self, stu_map_cohort_id, stu_email):
    try:
        logger.info(f"Start the step completion task for : {stu_email}")
        all_tracker_steps = models.CohortStepTracker.objects.filter(
            stu_cohort_map=stu_map_cohort_id
        )
        for step in all_tracker_steps:
            if step.step_status_id.is_active:
                if step.is_completed:
                    logger.info(f"Step completion updated in step_completion : 100")
                    models.CohortStepTrackerDetails.objects.update_or_create(
                        cohort_step_tracker=step, defaults={"step_completion": 100}
                    )
                else:
                    completed_action_item = step.tot_completed
                    total_action_item = step.step_status_id.tot_action_items
                    tot_per = int(completed_action_item * 100 / total_action_item)
                    models.CohortStepTrackerDetails.objects.update_or_create(
                        cohort_step_tracker=step, defaults={"step_completion": tot_per}
                    )
                    logger.info(
                        f"Step completion updated in step_completion : {tot_per}"
                    )
            else:
                print("Empty!!")
    except Exception as Error:
        logger.info(f"Error at step-completion : {Error}")


def calculate_endurance(user, lang_code):
    mycourses = user.stuMapID.filter(stu_cohort_lang=lang_code)
    endurance_list = []
    step_sno = 0
    endurance_score = 0
    local_tz = pytz.timezone(settings.TIME_ZONE)
    try:
        for i in range(mycourses.count()):
            steps = mycourses[i].stu_cohort_map.all()
            for step_i, step in enumerate(steps):
                step_sno = step_sno + 1
                score = 0
                endurance_step_data = {}
                if step.step_status_id.is_active:
                    score = 0
                    step_unloack_date = step.step_status_id.starting_date
                    step_unloack_date = datetime.datetime.fromisoformat(
                        step_unloack_date.isoformat()
                    )
                    endurance_step_data["step_sno"] = step_sno
                    endurance_step_data["step_unloack_date"] = step_unloack_date.date
                    endurance_step_data["step_completed_date"] = ""
                    endurance_step_data["step_title"] = step.step_status_id.step.title
                    if step.is_completed:
                        score = 50
                        # step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        # datetime.datetime.fromisoformat(steps[step_sno].step_status_id.starting_date.isoformat())
                        if steps.count() > step_sno:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = (
                                datetime.datetime.fromisoformat(next_date.isoformat())
                                - step_unloack_date
                            )
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = (
                                step_unloack_date
                                + datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59
                                )
                            )  # test
                        # step_completion_date = datetime.datetime.fromisoformat(step_completion_date.isoformat())
                        # time_change = datetime.timedelta()
                        # step_completion_date = step_completion_date + time_change
                        step_completion_date = local_tz.localize(step_completion_date)
                        step_completed_date = step.modified_at
                        endurance_step_data["step_completed_date"] = step_completed_date
                        if step_completed_date < step_completion_date:
                            print("Ok")
                            score = 100
                    else:
                        if steps.count() > step_sno:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = (
                                datetime.datetime.fromisoformat(next_date.isoformat())
                                - step_unloack_date
                            )
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = (
                                step_unloack_date
                                + datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59
                                )
                            )
                        step_completion_date = local_tz.localize(step_completion_date)
                    endurance_step_data["score"] = score
                    endurance_score = endurance_score + score
                    # endurance_list.append(endurance_step_data)
                    current_date = datetime.datetime.today()
                    current_date = datetime.datetime.fromisoformat(
                        current_date.isoformat()
                    )
                    current_date = local_tz.localize(current_date)
                    if current_date < step_completion_date:
                        if score > 0:
                            endurance_list.append(endurance_step_data)
                    else:
                        endurance_list.append(endurance_step_data)
                pass
        if len(endurance_list) != 0:
            endurance_score = endurance_score / len(endurance_list)
    except Exception as ex:
        print(ex)
    return endurance_list, endurance_score


def calculate_endurance_middle_school(user, lang_code):
    mycourses = user.stuMapID.filter(stu_cohort_lang=lang_code)
    endurance_list = []
    step_sno = 0
    endurance_score = 0
    local_tz = pytz.timezone(settings.TIME_ZONE)
    try:
        for i in range(mycourses.count()):
            steps = mycourses[i].stu_cohort_map.all()
            for step_i, step in enumerate(steps):
                step_sno = step_sno + 1
                score = 0
                endurance_step_data = {}
                if step.step_status_id.is_active:
                    score = 0
                    step_unloack_date = step.step_status_id.starting_date
                    step_unloack_date = datetime.datetime.fromisoformat(
                        step_unloack_date.isoformat()
                    )
                    endurance_step_data["step_sno"] = step_sno
                    endurance_step_data["step_unloack_date"] = step_unloack_date.date
                    endurance_step_data["step_completed_date"] = ""
                    endurance_step_data["step_title"] = step.step_status_id.step.title
                    if step.is_completed:
                        score = 50
                        # step_completion_date = step_unloack_date + datetime.timedelta(days=7,hours=23, minutes=59, seconds=59) #test
                        # datetime.datetime.fromisoformat(steps[step_sno].step_status_id.starting_date.isoformat())
                        if step_sno == 1:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = (
                                datetime.datetime.fromisoformat(next_date.isoformat())
                                - step_unloack_date
                            )
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = (
                                step_unloack_date
                                + datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59
                                )
                            )  # test
                        # step_completion_date = datetime.datetime.fromisoformat(step_completion_date.isoformat())
                        # time_change = datetime.timedelta()
                        # step_completion_date = step_completion_date + time_change
                        step_completion_date = local_tz.localize(step_completion_date)
                        step_completed_date = step.modified_at
                        endurance_step_data["step_completed_date"] = step_completed_date
                        if step_completed_date < step_completion_date:
                            print("Ok")
                            score = 100
                    else:
                        if step_sno == 1:
                            next_date = steps[step_sno].step_status_id.starting_date
                            final_date = (
                                datetime.datetime.fromisoformat(next_date.isoformat())
                                - step_unloack_date
                            )
                            step_completion_date = step_unloack_date + final_date
                        else:
                            step_completion_date = (
                                step_unloack_date
                                + datetime.timedelta(
                                    days=7, hours=23, minutes=59, seconds=59
                                )
                            )
                        step_completion_date = local_tz.localize(step_completion_date)

                    endurance_step_data["score"] = score
                    endurance_score = endurance_score + score
                    current_date = datetime.datetime.today()
                    current_date = datetime.datetime.fromisoformat(
                        current_date.isoformat()
                    )
                    current_date = local_tz.localize(current_date)
                    if current_date < step_completion_date:
                        if score > 0:
                            endurance_list.append(endurance_step_data)
                    else:
                        endurance_list.append(endurance_step_data)
                pass
        if len(endurance_list) != 0:
            endurance_score = endurance_score / len(endurance_list)
    except Exception as ex:
        print(ex)
    return endurance_list, endurance_score


@shared_task(bind=True)
def update_endurance_score(self, stu_email, stu_id, lang_code):
    try:
        user = PERSON.objects.get(id=stu_id)
        if user.student.is_from_middle_school:
            endurance_list, endurance_score = calculate_endurance_middle_school(
                user, lang_code
            )
        else:
            endurance_list, endurance_score = calculate_endurance(user, lang_code)
        logger.info(f"In calculate_kpis function : {user.username}")
        mycourses = user.stuMapID.filter(stu_cohort_lang=lang_code)
        tot_confidence = 0
        tot_awareness = 0
        tot_curiosity = 0
        for i in range(mycourses.count()):
            confidence = 0
            awareness = 0
            curiosity = 0
            steps = mycourses[i].stu_cohort_map.all()
            for step_i, step in enumerate(steps):
                if step.is_completed is True:
                    if i == 0 and step_i == 0:
                        tot_confidence = 50
                        tot_awareness = 20
                        tot_curiosity = 12
                        confidence = confidence + 0.4
                        awareness = awareness + 2
                        curiosity = curiosity + 0.5
                    elif i == 0:
                        confidence = confidence + 0.4
                        awareness = awareness + 2
                        curiosity = curiosity + 0.5
                    else:
                        confidence = confidence + 0.9
                        awareness = awareness + 2.5
                        curiosity = curiosity + 1.8
            tot_awareness = tot_awareness + awareness
            tot_confidence = tot_confidence + confidence
            tot_curiosity = tot_curiosity + curiosity
            if tot_awareness > 100:
                tot_awareness = 100
            if tot_confidence > 100:
                tot_confidence = 100
            if tot_curiosity > 100:
                tot_curiosity = 100
        (
            stu_progress,
            is_created,
        ) = models.StudentProgressDetail.objects.update_or_create(
            student=user.student,
            defaults={
                "endurance_score": int(endurance_score),
                "confidence_score": int(tot_confidence),
                "awareness_score": int(tot_awareness),
                "curiosity_score": int(tot_curiosity),
            },
        )
        logger.info(f"Student Endurance Score >>>> :  {endurance_score}")
        logger.info(f"student progress report updated for :  {stu_email}")
    except Exception as error:
        logger.error(f"Error at endurance score {error} : {stu_email}")


@shared_task(bind=True)
def exercise_cohort_step_tracker_creation(self, stu_email, stu_id, cohort_id):
    try:
        logger.info(f"In Celery Task to link steps and action item : {stu_email}")
        course = models.StudentCohortMapper.objects.filter(
            student=stu_id, cohort=cohort_id
        )
        all_steps = models.courseMdl.step_status.objects.filter(cohort_id=cohort_id)
        hubspot_step_unlock_date = ""
        for i, step_stat in enumerate(all_steps):
            (
                cohort_step_track,
                is_created,
            ) = models.CohortStepTracker.objects.get_or_create(
                stu_cohort_map=course[0], step_status_id=step_stat
            )

            stu_cohort_name = course[0].cohort.cohort_name
            step_name = step_stat.step.title
            if is_created:
                logger.info(f"In Celery Task step({i+1}) linked: {stu_email}")
                title = f"Step {i+1} :- {step_stat.step.title}"
                todo_date = step_stat.starting_date
                hubspot_step_unlock_date = (
                    hubspot_step_unlock_date
                    + f"_Course-{step_stat.cohort.module.module_id}-Step{i+1}:{todo_date}"
                )
            action_items = cohort_step_track.step_status_id.step.action_items.all()
            try:
                for action_item in action_items:
                    (
                        action_item_track,
                        is_created_ac,
                    ) = models.StudentActionItemTracker.objects.get_or_create(
                        step_tracker=cohort_step_track, ActionItem=action_item
                    )
                    logger.info(
                        f"In Celery Task step({i+1}), Action Item({action_item.action_sno}) linked: {stu_email}"
                    )
                    action_type = action_item_track.ActionItem.action_type.datatype
                    if action_type == "Links":
                        action_item_links = action_item_track.ActionItem.links.filter(
                            is_deleted=False
                        ).all()
                        for ai_link in action_item_links:
                            (
                                ai_link_track,
                                is_created_ai,
                            ) = models.StudentActionItemLinks.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_link=ai_link,
                                defaults={"is_completed": "No"},
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI Link linked: {stu_email}"
                            )
                    elif action_type == "Diary":
                        action_item_diary = action_item_track.ActionItem.diary.filter(
                            is_deleted=False
                        ).all()
                        for ai_diary in action_item_diary:
                            (
                                ai_diary_track,
                                is_created,
                            ) = models.StudentActionItemDiary.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_diary=ai_diary,
                                defaults={
                                    "email": stu_email,
                                    "cohort_name": stu_cohort_name,
                                    "step_title": step_name,
                                },
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI Diary linked: {stu_email}"
                            )
                    elif action_type == "Exit":
                        action_item_exit_tickets = (
                            action_item_track.ActionItem.exit_tickets.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_exit in action_item_exit_tickets:
                            (
                                ai_exit_track,
                                is_created,
                            ) = models.StudentActionItemExitTicket.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_exit_ticket=ai_exit,
                                defaults={"is_completed": "No"},
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI Exit Ticket linked: {stu_email}"
                            )
                    elif action_type == "Table":
                        action_item_type_table = (
                            action_item_track.ActionItem.actionitem_type_table.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_table in action_item_type_table:
                            (
                                ai_table_track,
                                is_created,
                            ) = models.StudentActionItemTypeTable.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_type_table=ai_table,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "Google_Form":
                        action_item_google_form = (
                            action_item_track.ActionItem.actionitem_google_form.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_google_form in action_item_google_form:
                            (
                                ai_google_form_track,
                                is_created,
                            ) = models.StudentActionItemGoogleForm.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_google_form=ai_google_form,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "TableStep8":
                        actionitem_type_table_step8 = action_item_track.ActionItem.actionitem_type_table_step8.filter(
                            is_deleted=False
                        ).all()
                        for ai_table_s8 in actionitem_type_table_step8:
                            (
                                ai_table_s8_track,
                                is_created,
                            ) = models.StudentActionItemTypeTableStep8.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_type_table_step8=ai_table_s8,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "Framework":
                        action_item_framework = (
                            action_item_track.ActionItem.actionitem_framework.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_framework in action_item_framework:
                            (
                                ai_table_track,
                                is_created,
                            ) = models.StudentActionItemFramework.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_framework=ai_framework,
                                defaults={"is_completed": "No"},
                            )
                    else:
                        action_item_files = action_item_track.ActionItem.files.filter(
                            is_deleted=False
                        ).all()
                        for ai_file in action_item_files:
                            (
                                ai_file_track,
                                is_created,
                            ) = models.StudentActionItemFiles.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_file=ai_file,
                                defaults={"is_completed": "No"},
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI File linked: {stu_email}"
                            )
                    # status = action_item_track.is_action_item_completed
                    # action_item_track.is_completed = status
                    # action_item_track.save()
                logger.info(
                    f"In Celery Task step({i+1}) successfully linked with all action items: {stu_email}"
                )
            except Exception as exa:
                print(exa)
                logger.critical(
                    f"Error to link action item in celery function- {exa} for {stu_email}"
                )
        if hubspot_step_unlock_date != "":
            try:
                # hubspotContactupdateQueryAdded
                logger.info(
                    f"In hubspot step unlock date parameter building for : {stu_email}"
                )
                keys_list = ["email", "hubspot_step_unlocked_date"]
                values_list = [stu_email, hubspot_step_unlock_date]
                create_update_contact_hubspot(stu_email, keys_list, values_list)
                logger.info(
                    f"In hubspot step unlock date parameter update completed for : {stu_email}"
                )
            except Exception as ex:
                logger.error(
                    f"Error at hubspot step unlock date parameter update {ex} for : {stu_email}"
                )
    except Exception as ex:
        logger.critical(
            f"Error to link cohort step in ceelry function {ex} for : {stu_email}"
        )


def exercise_cohort_step_tracker_creation_without_celery(stu_email, stu_id, cohort_id):
    try:
        logger.info(f"In Celery Task to link steps and action item : {stu_email}")
        course = models.StudentCohortMapper.objects.filter(
            student=stu_id, cohort=cohort_id
        )
        all_steps = models.courseMdl.step_status.objects.filter(cohort_id=cohort_id)
        hubspot_step_unlock_date = ""
        for i, step_stat in enumerate(all_steps):
            (
                cohort_step_track,
                is_created,
            ) = models.CohortStepTracker.objects.get_or_create(
                stu_cohort_map=course[0], step_status_id=step_stat
            )

            stu_cohort_name = course[0].cohort.cohort_name
            step_name = step_stat.step.title
            if is_created:
                logger.info(f"In Celery Task step({i+1}) linked: {stu_email}")
                title = f"Step {i+1} :- {step_stat.step.title}"
                todo_date = step_stat.starting_date
                hubspot_step_unlock_date = (
                    hubspot_step_unlock_date
                    + f"_Course-{step_stat.cohort.module.module_id}-Step{i+1}:{todo_date}"
                )
            action_items = cohort_step_track.step_status_id.step.action_items.all()
            try:
                for action_item in action_items:
                    (
                        action_item_track,
                        is_created_ac,
                    ) = models.StudentActionItemTracker.objects.get_or_create(
                        step_tracker=cohort_step_track, ActionItem=action_item
                    )
                    logger.info(
                        f"In Celery Task step({i+1}), Action Item({action_item.action_sno}) linked: {stu_email}"
                    )
                    action_type = action_item_track.ActionItem.action_type.datatype
                    if action_type == "Links":
                        action_item_links = action_item_track.ActionItem.links.filter(
                            is_deleted=False
                        ).all()
                        for ai_link in action_item_links:
                            (
                                ai_link_track,
                                is_created_ai,
                            ) = models.StudentActionItemLinks.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_link=ai_link,
                                defaults={"is_completed": "No"},
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI Link linked: {stu_email}"
                            )
                    elif action_type == "Diary":
                        action_item_diary = action_item_track.ActionItem.diary.filter(
                            is_deleted=False
                        ).all()
                        for ai_diary in action_item_diary:
                            (
                                ai_diary_track,
                                is_created,
                            ) = models.StudentActionItemDiary.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_diary=ai_diary,
                                defaults={
                                    "email": stu_email,
                                    "cohort_name": stu_cohort_name,
                                    "step_title": step_name,
                                },
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI Diary linked: {stu_email}"
                            )
                    elif action_type == "Exit":
                        action_item_exit_tickets = (
                            action_item_track.ActionItem.exit_tickets.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_exit in action_item_exit_tickets:
                            (
                                ai_exit_track,
                                is_created,
                            ) = models.StudentActionItemExitTicket.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_exit_ticket=ai_exit,
                                defaults={"is_completed": "No"},
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI Exit Ticket linked: {stu_email}"
                            )
                    elif action_type == "Table":
                        action_item_type_table = (
                            action_item_track.ActionItem.actionitem_type_table.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_table in action_item_type_table:
                            (
                                ai_table_track,
                                is_created,
                            ) = models.StudentActionItemTypeTable.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_type_table=ai_table,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "Google_Form":
                        action_item_google_form = (
                            action_item_track.ActionItem.actionitem_google_form.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_google_form in action_item_google_form:
                            (
                                ai_google_form_track,
                                is_created,
                            ) = models.StudentActionItemGoogleForm.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_google_form=ai_google_form,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "TableStep8":
                        actionitem_type_table_step8 = action_item_track.ActionItem.actionitem_type_table_step8.filter(
                            is_deleted=False
                        ).all()
                        for ai_table_s8 in actionitem_type_table_step8:
                            (
                                ai_table_s8_track,
                                is_created,
                            ) = models.StudentActionItemTypeTableStep8.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_type_table_step8=ai_table_s8,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "Framework":
                        action_item_framework = (
                            action_item_track.ActionItem.actionitem_framework.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_framework in action_item_framework:
                            (
                                ai_table_track,
                                is_created,
                            ) = models.StudentActionItemFramework.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_framework=ai_framework,
                                defaults={"is_completed": "No"},
                            )
                    else:
                        action_item_files = action_item_track.ActionItem.files.filter(
                            is_deleted=False
                        ).all()
                        for ai_file in action_item_files:
                            (
                                ai_file_track,
                                is_created,
                            ) = models.StudentActionItemFiles.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_file=ai_file,
                                defaults={"is_completed": "No"},
                            )
                            logger.info(
                                f"In Celery Task step({i+1}), Action Item({action_item.action_sno}), AI File linked: {stu_email}"
                            )
                    # status = action_item_track.is_action_item_completed
                    # action_item_track.is_completed = status
                    # action_item_track.save()
                logger.info(
                    f"In Celery Task step({i+1}) successfully linked with all action items: {stu_email}"
                )
            except Exception as exa:
                print(exa)
                logger.critical(
                    f"Error to link action item in celery function- {exa} for {stu_email}"
                )
        if hubspot_step_unlock_date != "":
            try:
                # hubspotContactupdateQueryAdded
                logger.info(
                    f"In hubspot step unlock date parameter building for : {stu_email}"
                )
                keys_list = ["email", "hubspot_step_unlocked_date"]
                values_list = [stu_email, hubspot_step_unlock_date]
                create_update_contact_hubspot(stu_email, keys_list, values_list)
                logger.info(
                    f"In hubspot step unlock date parameter update completed for : {stu_email}"
                )
            except Exception as ex:
                logger.error(
                    f"Error at hubspot step unlock date parameter update {ex} for : {stu_email}"
                )
    except Exception as ex:
        logger.critical(
            f"Error to link cohort step in ceelry function {ex} for : {stu_email}"
        )


@shared_task
def link_with_action_items(stu_email, stu_id, cohort_id):
    try:
        logger.info(f"In exercise student task for : {stu_email}")
        course = models.StudentCohortMapper.objects.filter(
            student=stu_id, cohort=cohort_id
        )
        all_steps = models.courseMdl.step_status.objects.filter(cohort_id=cohort_id)
        hubspot_step_unlock_date = ""
        for i, step_stat in enumerate(all_steps):
            (
                cohort_step_track,
                is_created,
            ) = models.CohortStepTracker.objects.get_or_create(
                stu_cohort_map=course[0], step_status_id=step_stat
            )
            stu_cohort_name = course[0].cohort.cohort_name
            step_name = step_stat.step.title
            if is_created:
                title = f"Step {i+1} :- {step_stat.step.title}"
                todo_date = step_stat.starting_date
                hubspot_step_unlock_date = (
                    hubspot_step_unlock_date
                    + f"_Course-{step_stat.cohort.module.module_id}-Step{i+1}:{todo_date}"
                )
            action_items = cohort_step_track.step_status_id.step.action_items.all()
            try:
                for action_item in action_items:
                    (
                        action_item_track,
                        is_created_ac,
                    ) = models.StudentActionItemTracker.objects.get_or_create(
                        step_tracker=cohort_step_track, ActionItem=action_item
                    )
                    action_type = action_item_track.ActionItem.action_type.datatype
                    if action_type == "Links":
                        action_item_links = action_item_track.ActionItem.links.filter(
                            is_deleted=False
                        ).all()
                        for ai_link in action_item_links:
                            (
                                ai_link_track,
                                is_created_ai,
                            ) = models.StudentActionItemLinks.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_link=ai_link,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "Diary":
                        action_item_diary = action_item_track.ActionItem.diary.filter(
                            is_deleted=False
                        ).all()
                        for ai_diary in action_item_diary:
                            (
                                ai_diary_track,
                                is_created,
                            ) = models.StudentActionItemDiary.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_diary=ai_diary,
                                defaults={
                                    "email": stu_email,
                                    "cohort_name": stu_cohort_name,
                                    "step_title": step_name,
                                },
                            )
                    elif action_type == "Exit":
                        action_item_exit_tickets = (
                            action_item_track.ActionItem.exit_tickets.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_exit in action_item_exit_tickets:
                            (
                                ai_exit_track,
                                is_created,
                            ) = models.StudentActionItemExitTicket.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_exit_ticket=ai_exit,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "Table":
                        action_item_type_table = (
                            action_item_track.ActionItem.actionitem_type_table.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_table in action_item_type_table:
                            (
                                ai_table_track,
                                is_created,
                            ) = models.StudentActionItemTypeTable.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_type_table=ai_table,
                                defaults={"is_completed": "No"},
                            )

                    elif action_type == "Google_Form":
                        action_item_google_form = (
                            action_item_track.ActionItem.actionitem_google_form.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_google_form in action_item_google_form:
                            (
                                ai_google_form_track,
                                is_created,
                            ) = models.StudentActionItemGoogleForm.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_google_form=ai_google_form,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "TableStep8":
                        actionitem_type_table_step8 = action_item_track.ActionItem.actionitem_type_table_step8.filter(
                            is_deleted=False
                        ).all()
                        for ai_table_s8 in actionitem_type_table_step8:
                            (
                                ai_table_s8_track,
                                is_created,
                            ) = models.StudentActionItemTypeTableStep8.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_type_table_step8=ai_table_s8,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "Framework":
                        action_item_framework = (
                            action_item_track.ActionItem.actionitem_framework.filter(
                                is_deleted=False
                            ).all()
                        )
                        for ai_framework in action_item_framework:
                            (
                                ai_table_track,
                                is_created,
                            ) = models.StudentActionItemFramework.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_framework=ai_framework,
                                defaults={"is_completed": "No"},
                            )
                    elif action_type == "File":
                        action_item_files = action_item_track.ActionItem.files.filter(
                            is_deleted=False
                        ).all()
                        for ai_file in action_item_files:
                            (
                                ai_file_track,
                                is_created,
                            ) = models.StudentActionItemFiles.objects.get_or_create(
                                action_item_track=action_item_track,
                                action_item_file=ai_file,
                                defaults={"is_completed": "No"},
                            )
                    # status = action_item_track.is_action_item_completed
                    # action_item_track.is_completed = status
                    action_item_track.save()
            except Exception as exa:
                print(exa)
                logger.critical(f"Error at execercise page {exa} for {stu_email}")
        if hubspot_step_unlock_date != "":
            try:
                # hubspotContactupdateQueryAdded
                logger.info(
                    f"In hubspot step unlock date parameter building for : {stu_email}"
                )
                keys_list = ["email", "hubspot_step_unlocked_date"]
                values_list = [stu_email, hubspot_step_unlock_date]
                create_update_contact_hubspot(stu_email, keys_list, values_list)
                logger.info(
                    f"In hubspot step unlock date parameter update completed for : {stu_email}"
                )
            except Exception as ex:
                logger.error(
                    f"Error at hubspot step unlock date parameter update {ex} for : {stu_email}"
                )
    except Exception as ex:
        logger.critical(f"Error in exercise page view {ex} for : {stu_email}")


@shared_task
def exercise_cohort_step_tracker_hubspot_properties(stu_email, stu_id, cohort_id):
    try:
        course = models.StudentCohortMapper.objects.filter(
            student=stu_id, cohort=cohort_id
        ).first()
        logger.info(f"In exercise student task for : {stu_email}")
        hubspot_step_completion_rate = ""
        hubspot_step_completion_date = ""
        hubspot_is_step_completed_75 = ""
        all_tracker_steps = models.CohortStepTracker.objects.filter(
            stu_cohort_map=course
        )
        for i, step_track in enumerate(all_tracker_steps):
            obj_step_track = models.CohortStepTracker.objects.get(
                step_track_id=step_track.step_track_id
            )
            if obj_step_track.is_completed == False:
                step_track_stat = obj_step_track.is_step_completed
                obj_step_track.is_completed = step_track_stat
                obj_step_track.save()
                total_action_items = obj_step_track.stu_action_items.all().count()
                completed_action_items = obj_step_track.tot_completed
                if step_track_stat:
                    try:
                        step_completed_date = obj_step_track.modified_at
                        hubspot_step_completion_date = (
                            hubspot_step_completion_date
                            + f"_Course-{obj_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{step_completed_date}"
                        )
                    except:
                        logger.error(
                            f"Error while updating step completion date on hubspot for : {stu_email}"
                        )
                try:
                    # calculate %
                    if completed_action_items > 0:
                        Compute_completion_rate = 0
                        Compute_completion_rate = (
                            completed_action_items * 100.0 / total_action_items
                        )
                    else:
                        Compute_completion_rate = 0
                    hubspot_step_completion_rate = (
                        hubspot_step_completion_rate
                        + f"_Course-{obj_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{Compute_completion_rate}"
                    )
                    if Compute_completion_rate >= 75:
                        hubspot_is_step_completed_75 = (
                            hubspot_is_step_completed_75
                            + f"_Course-{obj_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:Yes"
                        )
                    else:
                        hubspot_is_step_completed_75 = (
                            hubspot_is_step_completed_75
                            + f"_Course-{obj_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:No"
                        )
                except Exception as ex:
                    logger.error(
                        f"Error while updating step completion rate on hubspot for : {stu_email}"
                    )
                    print(ex)
            else:
                hubspot_is_step_completed_75 = (
                    hubspot_is_step_completed_75
                    + f"_Course-{obj_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:Yes"
                )
                hubspot_step_completion_rate = (
                    hubspot_step_completion_rate
                    + f"_Course-{obj_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{100.00}"
                )
                step_completed_date = obj_step_track.modified_at
                hubspot_step_completion_date = (
                    hubspot_step_completion_date
                    + f"_Course-{obj_step_track.step_status_id.cohort.module.module_id}-Step{i+1}:{step_completed_date}"
                )
        try:
            # hubspotContactupdateQueryAdded
            logger.info(
                f"In hubspot step completion rate parameter building for : {stu_email}"
            )
            keys_list = [
                "email",
                "hubspot_step_completion_rate",
                "hubspot_step_completion_date",
                "hubspot_is_step_completed_75",
            ]
            values_list = [
                stu_email,
                hubspot_step_completion_rate,
                hubspot_step_completion_date,
                hubspot_is_step_completed_75,
            ]
            create_update_contact_hubspot(stu_email, keys_list, values_list)
            logger.info(
                f"In hubspot step completion rate parameter update completed for : {stu_email}"
            )
        except Exception as ex:
            logger.error(
                f"Error at hubspot step completion rate parameter update {ex} for : {stu_email}"
            )
    except Exception as err:
        print(err)
        logger.critical(
            f"Error in exercise step tracker task with celery {err} for : {stu_email}"
        )


@shared_task
def student_link_with_cohort(stu_email, cohort_id, lang_code):
    try:
        print("In student link with cohort....")
        logger.info(f"Student linked with cohort for : {stu_email}")
        cohort = models.courseMdl.Cohort.cohortManager.lang_code(lang_code).get(
            cohort_id=cohort_id
        )
        stu_cohort_map = models.StudentCohortMapper.objects.filter(
            student=stu_email,
            cohort__module__module_id=cohort.module.module_id,
            stu_cohort_lang=lang_code,
        )
        if stu_cohort_map.count() > 0:
            cohort_steps = cohort.cohort_step_status.all()
            stu_cohort_map = stu_cohort_map.first()
            old_all_steps = stu_cohort_map.stu_cohort_map.all()
            for i, step in enumerate(old_all_steps):
                if step.step_status_id.step.step_id == cohort_steps[i].step.step_id:
                    print(step.step_status_id)
                    step.step_status_id = cohort_steps[i]
                    print(step.step_status_id)
                    step.save()
            stu_cohort_map.cohort = cohort
            stu_cohort_map.save()
            logger.info(f"Course cohort is linked with student: {stu_email}")
        else:
            models.StudentCohortMapper.objects.update_or_create(
                student=stu_email, cohort=cohort, stu_cohort_lang=lang_code
            )
        try:
            # hubspotContactupdateQueryAdded
            logger.info(f"In hubspot cohort name parameter building for : {stu_email}")
            if cohort.module.module_id == 1 or cohort.module.module_id == 3:
                keys_list = ["email", "hubspot_cohort_name_premium"]
                values_list = [stu_email, cohort.cohort_name]
                create_update_contact_hubspot(stu_email, keys_list, values_list)
            if cohort.module.module_id == 2 or cohort.module.module_id == 4:
                keys_list = ["email", "hubspot_cohort_name_elite1"]
                values_list = [stu_email, cohort.cohort_name]
                create_update_contact_hubspot(stu_email, keys_list, values_list)
            if cohort.module.module_id == 5:
                keys_list = ["email", "hubspot_cohort_name_elite2"]
                values_list = [stu_email, cohort.cohort_name]
                create_update_contact_hubspot(stu_email, keys_list, values_list)
            logger.info(
                f"In hubspot cohort name parameter update completed for : {stu_email}"
            )
        except Exception as ex:
            logger.error(
                f"Error at hubspot cohort name parameter update {ex} for : {stu_email}"
            )
        return True
    except Exception as exp:
        print(exp)
        logger.critical(f"Error to link cohort with student: {stu_email}")
        return False


@shared_task(bind=True)
def send_email_task(self, id, first_name, last_name, email):
    try:
        email_template_name = "userauth/email_admin.html"
        fromEmail = settings.EMAIL_HOST_USER
        toEmail = "rohit@myfuturely.com"
        subject = "Futurely Payment!"
        user = f"{first_name} {last_name}"
        data = {
            "user": user,
            "id": id,
            "email": email,
        }
        html_msg = get_template(email_template_name).render(data)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [toEmail])
        msg.content_subtype = "html"
        msg.send()
        logger.info(f"Celery task - E-Mail sent to admin successfully for : {email}")
    except Exception as error:
        logger.error(
            f"Celery task - Error occurred at send_email_task while sending email for: {email}. Error: {str(error)}"
        )


@shared_task(bind=True)
def ai_generated_comment_for_stu_action_item_diary(
    self,
    stu_id,
    ans,
    stu_ai_diary_id,
    step_sno,
    ques_sno,
    is_from_fast_track,
    is_from_middle_school,
):
    try:
        person = PERSON.objects.filter(id=stu_id).first()
        if person:
            openai.api_type = "azure"
            openai.api_base = "https://canada-gpt-4.openai.azure.com/"
            openai.api_version = "2023-07-01-preview"
            openai.api_key = "4dee1e359fa542578b142683b25810ec"
            engine = "gpt-4-32k"
            response = None
            if is_from_fast_track and step_sno == "2" and ques_sno == "1":
                response = openai.ChatCompletion.create(
                    engine=engine,
                    messages=[
                        {
                            "role": "system",
                            "content": 'Stile di scrittura: Empatico, positivo, costruttivo. Usa un linguaggio semplice e comprensibile, evita frasi troppo lunghe o complesse.  \n\nSe la risposta dello studente sembra priva di significato o rilevanza, il modello dovrebbe rispondere con: "Ciao! ho visto che non hai avuto modo di concentrarti sulla compilazione del diario di bordo, non perderti l\'opportunità di utilizzare questo strumento così importante per il tuo futuro".',
                        },
                        {
                            "role": "user",
                            "content": "Ho paura di fare la scelta sbagliata e che poi debba cambiare università",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao Marta! Questa possiamo definirla una paura immaginaria, dettata dall'incertezza e dal fatto di non sapere come sarà il futuro. Come fare a non prendere scelte sbagliate? Quando prendiamo una scelta non sappiamo dove ci porterà, non conosciamo tutte le possibilità che quella scelta ci aprirà. Questo può metterci ansia e agitazione ma allo stesso tempo curiosità ed entusiasmo. Per trovare l'università più allineata a noi, ai nostri interessi, alle nostre caratteristiche, dobbiamo innanzitutto focalizzare quale delle nostre caratteristiche per noi è più importante, su quale competenza vogliamo puntare. Dobbiamo anche ricordarci che può accadere di prendere una scelta che in quel momento ci sembrava giusta per come eravamo in quel momento: questo non vuol dire che sia sbagliata, semplicemente possiamo renderci conto che non è più quello che fa al caso nostro. Cambiare strada non è di per sè un problema, accade tante volte: l'importante è saper valutare quali aspetti del percorso che abbiamo intrapreso non ci convincono e perchè, in maniera tale da poter scegliere un'alternativa che possa prendere in considerazione gli elementi che per noi sono importanti.",
                        },
                        {
                            "role": "user",
                            "content": "Ho paura di non sapere cosa voler fare e ho anche paura di avere dubbi e ripensamenti dopo aver preso una scelta.",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao Caterina! Io sono stata molto contenta della mia scelta (scienze dell'educazione e poi una magistrale in International and Comparative Education). Però credo sia importante riconoscere che lungo il percorso ho pensato \"e se avessi preso quest'altro percorso?\". Questa domanda mi sorgeva non perchè io fossi insoddisfatta del mio percorso ma semplicemente perchè sono una persona con interessi molto diversi. Con il tempo e l'esperienza ho imparato che se a volte ci vengono dei dubbi di questo tipo, non sono per forza un campanello d'allarme: semplicemente ognuno di noi ha tante sfumature e caratteristiche, quindi è normale avere desiderio di altro, specialmente di qualcosa di diverso rispetto a quello che abbiamo già o stiamo già facendo. L'importante è valutare tutti i criteri di scelta e gli elementi che per noi sono importanti (lo vedrai nello step 8). Questo ci permette di prendere una scelta che prende in considerazione tanti fattori, non solo ad esempio quanto ci piace o che lavoro ci porterà a fare un certo percorso. Vorrei aggiungere anche che spesso abbiamo l'idea di dover capire \"cosa fare nella vita\" come se ci fosse solo un percorso e una volta preso quella sarà la nostra strada. Sicuramente è importante capire cosa ci piace e in quale percorso vogliamo crescere professionalmente, però è importante anche ricordarsi che la vita evolve, cambia, nessun momento è mai uguale ad un altro, per cui è una scoperta continua capire cosa vogliamo fare nella vita. L'importante è chiedersi sempre se quello che facciamo in un certo momento ci fa bene e ci appaga!",
                        },
                        {
                            "role": "user",
                            "content": "Ho paura di avere una vita mediocre",
                        },
                        {
                            "role": "assistant",
                            "content": 'Ciao Filippo! Questa possiamo definirla una paura immaginaria, dettata dall\'incertezza e dal fatto di non sapere come sarà il futuro. Quali sono gli elementi che per te contraddistinguerebbero una "vita mediocre" ? Prova ad identificarli. Ad esempio, se scopri che "avere una vita mediocre" vuol dire fare qualcosa del quale non sei soddisfatto e appagato, hai un elemento sul quale intervenire: puoi cercare quali sono le situazioni e le esperienze che ti fanno sentire soddisfatto e trovare l\'elemento in comune a quelle esperienze da ricercare poi nelle tue scelte di vita (di studio o di lavoro)!',
                        },
                        {
                            "role": "user",
                            "content": f"Contesto: Futurely è un'organizzazione che si dedica all'orientamento scolastico e professionale, aiutando gli studenti a scoprire e comprendere le proprie passioni, talenti, e come queste si potrebbero tradurre in un percorso di studio o di carriera. Lo strumento principale utilizzato da Futurely è il 'diario di bordo', che serve come mezzo per gli studenti di esplorare e riflettere sui propri interessi e aspirazioni.\n\nContenuto dello step: [Nello Step 2 di Futurely, gli studenti sono guidati a riflettere sul tema delle paure, distinguendo tra paure reali e paure irrazionali. La psicologa di Futurely fornisce una spiegazione dettagliata su come riconoscere e gestire queste due tipologie di paure. Inoltre, questo step incoraggia gli studenti a focalizzarsi sulle loro passioni e a riconoscere quelle esperienze passate che sono state significative per loro. Gli studenti sono invitati a pensare a 3 eventi che li hanno particolarmente segnati e che riflettono i loro tratti personali. Infine, gli studenti aggiornano il loro diario di bordo per documentare le loro riflessioni e scoperte.]\n\nDomanda del diario di bordo: [Quando pensi al tuo futuro, cosa ti spaventa o preoccupa di più? Prova a rispondere distinguendo tra paure reali, paure immaginarie e paure che pensavi fossero reali ma non lo sono!]\n\nRisposta del ragazzo:  {ans}\n\nPrompt: Basandoti sul contenuto dello step e sulla risposta del ragazzo, e tenendo conto dello stile di scrittura richiesto, genera un commento che incoraggi la riflessione dell'individuo, sostenendo e rafforzando la sua autocomprensione e crescita personale.",
                        },
                    ],
                    temperature=0.65,
                    max_tokens=400,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                )
            elif is_from_fast_track and step_sno == "5" and ques_sno == "2":
                response = openai.ChatCompletion.create(
                    engine=engine,
                    messages=[
                        {
                            "role": "system",
                            "content": "Stile di scrittura: Empatico, positivo, costruttivo. Usa un linguaggio semplice e comprensibile, evita frasi troppo lunghe o complesse.  Se la risposta dello studente sembra priva di significato o rilevanza, il modello dovrebbe rispondere con: \"Ciao! ho visto che non hai avuto modo di concentrarti sulla compilazione del diario di bordo, non perderti l'opportunità di utilizzare questo strumento così importante per il tuo futuro",
                        },
                        {
                            "role": "user",
                            "content": "qual è davvero il criterio più importante per scegliere?",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao Annachiara! Non c'è un solo criterio più importante per scegliere, devi costruire tu la tua scala di criteri importanti. I criteri ti aiutano a non perdere di vista da dove sei partita e a capire meglio cosa è importante per te e quindi i tuoi obiettivi. Sicuramente la passione è importante in questo processo, per cui se dovessimo identificare un criterio che può guidare anche gli altri criteri (dove andare a studiare, fare qualcosa di teorico o pratico) è capire se l'idea di iniziare un certo percorso può suscitare emozioni positive in noi.",
                        },
                        {"role": "user", "content": "rette universitarie"},
                        {
                            "role": "assistant",
                            "content": "Ciao! Se vuoi informazioni sulle rette universitarie, ti consiglio di provare ad esplorare i siti delle singole università alle quali sei interessato. A seconda della tipologia di università (statale o privata) le rette potrebbero cambiare. Inoltre, c’è la possibilità di ottenere delle borse di studio in base a determinati criteri (reddito, numero di esami svolti in un anno). Questa è un’informazione preziosa da tenere a mente per considerare tutti i fattori che possono incidere sulla tua scelta!",
                        },
                        {
                            "role": "user",
                            "content": "come posso essere sicura che apprezzerò davvero l'università che ho scelto e non avrò paura di voler cambiare corso di studi?",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao! Queste domande possono aiutarti a mitigare le tue paure relative al futuro, ad esempio quella che citi \"paura di voler cambiare percorso di studi\". Quando prendiamo una scelta non sappiamo dove ci porterà, non conosciamo tutte le possibilità che quella scelta ci aprirà. Questo può metterci ansia e agitazione ma allo stesso tempo curiosità ed entusiasmo. Per trovare l'università più allineata a noi, ai nostri interessi, alle nostre caratteristiche, dobbiamo innanzitutto focalizzare quale delle nostre caratteristiche per noi è più importante, su quale competenza vogliamo puntare. Dobbiamo anche ricordarci che può accadere di prendere una scelta che in quel momento ci sembrava giusta per come eravamo in quel momento: questo non vuol dire che sia sbagliata, semplicemente possiamo renderci conto che non è più quello che fa al caso nostro. Cambiare strada non è di per sè un problema, accade tante volte: l'importante è saper valutare quali aspetti del percorso che abbiamo intrapreso non ci convincono e perchè, in maniera tale da poter scegliere un'alternativa che possa prendere in considerazione gli elementi che per noi sono importanti. ",
                        },
                        {
                            "role": "user",
                            "content": f"Contesto: Futurely è un'organizzazione che si dedica all'orientamento scolastico e professionale, aiutando gli studenti a scoprire e comprendere le proprie passioni, talenti, e come queste si potrebbero tradurre in un percorso di studio o di carriera. Lo strumento principale utilizzato da Futurely è il 'diario di bordo', che serve come mezzo per gli studenti di esplorare e riflettere sui propri interessi e aspirazioni.\n\nContenuto dello step: [\"Nel quinto step di Futurely, gli studenti elaborano i loro criteri di scelta per l'università e l'ateneo. Devono scaricare un documento che spiega i criteri e un elenco correlato. Dopo averlo letto, assegnano un voto a ogni criterio e aggiungono commenti. Devono definire i criteri più importanti per le decisioni future. Infine, aggiornano il loro diario di bordo per riflettere sulle scelte.”]\n\nDomanda del diario di bordo: [Su quali criteri non sei tanto sicuro e vorresti chiedere consiglio ad esperti?]\n\nRisposta del ragazzo:  {ans}\n\nPrompt: Basandoti sul contenuto dello step e sulla risposta del ragazzo, e tenendo conto dello stile di scrittura richiesto, genera un commento che incoraggi la riflessione dell'individuo, sostenendo e rafforzando la sua autocomprensione e crescita personale.",
                        },
                    ],
                    temperature=0.65,
                    max_tokens=400,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                )
            elif is_from_middle_school and step_sno == "2" and ques_sno == "1":
                response = openai.ChatCompletion.create(
                    engine=engine,
                    messages=[
                        {
                            "role": "system",
                            "content": "Stile di scrittura: Empatico, positivo, costruttivo. Usa un linguaggio molto semplice e comprensibile, evita frasi troppo lunghe o complesse. Il linguaggio deve essere accessibile ad un ragazzo di 11 anni. Se la risposta dello studente sembra priva di significato o rilevanza, il modello dovrebbe rispondere con: \"Ciao! ho visto che non hai avuto modo di concentrarti sulla compilazione del diario di bordo, non perderti l'opportunità di utilizzare questo strumento così importante per il tuo futuro",
                        },
                        {
                            "role": "user",
                            "content": "Io all’inizio delle medie avevo questa paura di socializzare con in miei compagni. Conoscevo già la maggior parte della classe ma per socializzare con gli altri poi non ci ho messo tanto alla fine. Mi sono fatta coraggio e ho detto vabbè mi butto come va va e adesso ho socializzato praticamente con tutta la classe e perfino con i prof",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao! L’esempio che hai fatto è perfetto! Spesso abbiamo paura di alcune cose anche se non sappiamo ancora come saranno! L’importante in questi casi, come hai fatto tu, è buttarsi sapendo che quella paura è solo nella nostra testa!",
                        },
                        {
                            "role": "user",
                            "content": "Da questo step ho imparato che avere paura del futuro è normale, bisogna seguire ciò che si ama e non bi sogna mai farsi influenzare dai giudizi altrui. Io molte volte ho paura del mio futuro è ora sto cercando qualcosa che mi piace veramente che posso portare avanti nel mio percorso",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao! L’esempio che hai fatto è perfetto! Spesso abbiamo paura di alcune cose anche se non sappiamo ancora come saranno! L’importante in questi casi, come dici tu, è buttarsi sapendo che quella paura del futuro è solo nella nostra testa!",
                        },
                        {
                            "role": "user",
                            "content": "All'inizio, quando avevo solo 5 anni, avevo molta paura di stare da solo in casa, perché avevo tante paure che mi frullavano in testa. Non avevo mai pensato di affrontare questo mio timore, che secondo me era diventato quasi una fobia. Fino a quando, un giorno, mia mamma ha deciso di lasciarmi da solo in casa, con mia sorella gemella, per andare fuori a buttare la spazzatura. Avevo tanta paura perché non la vedevo tornare. Ma grazie a mia sorella, che mi ha aiutato in quella circostanza, adesso avrei ancora paura di restare da solo. Ho imparato da questo step, che è importante imparare ad affrontare le proprie paura, perché se te le tiri dietro per tutta la vita, quando sarai grande sarà quasi impossibile non avere più paura.",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao! Grazie per aver raccontato questa tua paura. Proprio come hai spiegato, all’inizio le nostre paure ci “frullano in testa” : diventano quasi più grandi di quelle che sono, ce le immaginiamo. Poi, piano piano, riusciamo ad affrontarle, soprattutto se chiediamo aiuto o consiglio a qualcuno che ci vuole bene. ",
                        },
                        {
                            "role": "user",
                            "content": f"Contesto: Futurely è un'organizzazione che si dedica all'orientamento scolastico e professionale, aiutando gli studenti a scoprire e comprendere le proprie passioni, talenti, e come queste si potrebbero tradurre in un percorso di studio o di carriera. Lo strumento principale utilizzato da Futurely è il 'diario di bordo', che serve come mezzo per gli studenti di esplorare e riflettere sui propri interessi e aspirazioni.\n\nContenuto dello step: [Nel secondo step di Futurely, gli studenti delle scuole medie, in preparazione per la scelta delle superiori, affrontano il tema della paura. Approfondiranno la conoscenza di questa emozione, comprenderanno come si manifesta e come gestirla. L'esercizio interattivo li aiuterà a riconoscere e superare le paure, spesso legate a esperienze sconosciute. Un video di Steve Jobs illustrerà l'importanza di seguire le proprie passioni, nonostante i rischi e la paura del fallimento. Gli studenti sono invitati ad aggiornare il loro diario di bordo. ]\n\nDomanda del diario di bordo: [Cos’hai imparato da questo step? Puoi aiutarti con le seguenti domande guida: - Ripensa ad una paura che avevi e che sei riuscito ad affrontare. Come hai fatto? Cosa ti ha aiutato in quella situazione? Racconta.]\n\nRisposta del ragazzo:  {ans}\n\nPrompt: Basandoti sul contenuto dello step e sulla risposta del ragazzo, e tenendo conto dello stile di scrittura richiesto, genera un commento che incoraggi la riflessione dell'individuo, sostenendo e rafforzando la sua autocomprensione e crescita personale.",
                        },
                    ],
                    temperature=0.65,
                    max_tokens=400,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                )
            elif is_from_middle_school and step_sno == "5" and ques_sno == "1":
                response = openai.ChatCompletion.create(
                    engine=engine,
                    messages=[
                        {
                            "role": "system",
                            "content": "Stile di scrittura: Empatico, positivo, costruttivo. Usa un linguaggio molto semplice e comprensibile, evita frasi troppo lunghe o complesse. Il linguaggio deve essere accessibile ad un ragazzo di 11 anni. Se la risposta dello studente sembra priva di significato o rilevanza, il modello dovrebbe rispondere con: \"Ciao! ho visto che non hai avuto modo di concentrarti sulla compilazione del diario di bordo, non perderti l'opportunità di utilizzare questo strumento così importante per il tuo futuro",
                        },
                        {
                            "role": "user",
                            "content": "UNA BELLA PALESTRA, GLI AMICI E UN LABORATORIO BEN ATTREZZATO PERCHè SONO LE COSE PIù IMPORTANTI",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao! Ottimo, hai individuato tre criteri di scelta importanti per te, che ti guideranno nella scelta della scuola superiore. Adesso nella ricerca della scuola, tieni a mente questi criteri, soprattutto quelli che puoi scegliere, ad esempio una scuola che abbia un laboratorio attrezzato! Gli amici li troverai sempre 🙂",
                        },
                        {
                            "role": "user",
                            "content": "Mi interessa che la scuola abbia tutto il materiale necessario per i laboratori artistici, che sia un ambiente adatto a me e che sia abbastanza vicino a casa mia",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao! Ottimo, hai individuato tre criteri di scelta importanti per te, che ti guideranno nella scelta della scuola superiore. Adesso nella ricerca della scuola, tieni a mente questi criteri, soprattutto quelli che puoi scegliere, ad esempio una scuola che abbia un laboratorio artistico che ti piace!",
                        },
                        {
                            "role": "user",
                            "content": "I criteri di scelta più importanti per me sono un percorso allineato alle mie passioni, se no mi annoierei continuamente e non avrei voglia di studiare, le buone attrezzature ed i laboratori perchè così abbiamo più esperimenti e cose interattive da fare",
                        },
                        {
                            "role": "assistant",
                            "content": "Ciao! Ottimo, hai individuato tre criteri di scelta importanti per te, che ti guideranno nella scelta della scuola superiore. Adesso nella ricerca della scuola, tieni a mente questi criteri, soprattutto quelli che puoi scegliere, ad esempio una scuola che abbia un laboratorio artistico che ti piace e che offra un percorso con materie che ti piacciono!",
                        },
                        {
                            "role": "user",
                            "content": f"Contesto: Futurely è un'organizzazione che si dedica all'orientamento scolastico e professionale, aiutando gli studenti a scoprire e comprendere le proprie passioni, talenti, e come queste si potrebbero tradurre in un percorso di studio o di carriera. Lo strumento principale utilizzato da Futurely è il 'diario di bordo', che serve come mezzo per gli studenti di esplorare e riflettere sui propri interessi e aspirazioni.\n\nContenuto dello step: [Nel quinto step di Futurely, gli studenti sintetizzano quanto appreso per focalizzarsi sulle opzioni post-scuola media. L'obiettivo è elaborare criteri personali per la scelta del percorso scolastico futuro, usando gli esercizi precedenti di autoconoscenza. Questi criteri guideranno la ricerca e l'esplorazione delle opzioni. Dopo aver interpretato i criteri proposti, gli studenti dovranno assegnare loro un livello di importanza. Alcuni criteri potrebbero richiedere ulteriori riflessioni e generare domande per future fasi di ricerca. L'esercizio interattivo assiste nella definizione e priorità dei criteri. ]\n\nDomanda del diario di bordo: [Cos’hai imparato da questo step? Puoi aiutarti con le seguenti domande guida: Quali sono i criteri di scelta più importanti per te? Perché?]\n\nRisposta del ragazzo:  {ans}\n\nPrompt: Basandoti sul contenuto dello step e sulla risposta del ragazzo, e tenendo conto dello stile di scrittura richiesto, genera un commento che incoraggi la riflessione dell'individuo, sostenendo e rafforzando la sua autocomprensione e crescita personale.",
                        },
                    ],
                    temperature=0.65,
                    max_tokens=400,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                )

            else:
                response = None
            if response is not None:
                generated_ai_text = response["choices"][0]["message"]["content"]
                stu_diary_obj = models.StudentActionItemDiary.objects.get(
                    id=stu_ai_diary_id
                )
                models.StudentActionItemDiaryAIComment.objects.update_or_create(
                    student_actions_item_diary_id=stu_diary_obj,
                    defaults={"ai_comment": generated_ai_text},
                )
                logger.info(
                    f"ai records successfully created in StudentActionItemDiaryAIComment for : {person.username}"
                )
            else:
                logger.error(
                    f"There was an error with the request at ai_generated_response_for_stu_action_item_diary. Status code: {response.status_code}"
                )
        else:
            logger.error(
                f"user not found at method ai_generated_response_for_stu_action_item_diary"
            )
    except Exception as Error:
        logger.error(
            f"An error occured while requesting the api for generate ai text for student action item diary  error : {Error}"
        )


@shared_task
def notify_students_about_job_posting():
    plan = courseMdl.OurPlans.objects.filter(plan_name=courseMdl.PlanNames.JobCourse.value).first()
    courses = courseMdl.Courses.objects.filter(plan=plan).first()
    module = courses.module.first()
    all_jobcourse_cohort = module.cohort_module.all()

    notification_type = courseMdl.Notification_type.objects.filter(notification_type=courseMdl.PlanNames.JobCourse.value).first()
    if notification_type:
        if all_jobcourse_cohort.count()>0:
            for cohort in all_jobcourse_cohort:
                courseMdl.Notification.objects.create(
                    cohort=cohort,
                    notification_type=notification_type,
                    title=_("C’è una nuova offerta di lavoro per te!"),
                )