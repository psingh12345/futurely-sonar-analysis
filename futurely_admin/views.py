from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from student.models import StudentCohortMapper, StudentScholarshipTestMapper, StudentScholarShipTest, StudentsPlanMapper, StudentActionItemDiary, StudentActionItemDiaryComment, CohortStepTrackerDetails, StudentActionItemDiaryAIComment,Stu_Notification, PersonNotification
from courses import models
from django.contrib.auth.decorators import login_required
from userauth import models as auth_mdl
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from datetime import datetime, timedelta, date
import pandas as pd
import json
import requests
import csv
from boto3.dynamodb.conditions import Attr, Key
import xlwt
import boto3
import logging
# from .task import send_mail_to_student
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from .forms import SendPashNotificationForm, CohortSendPushNotificationForm
from lib.hubspot_contact_sns import create_update_contact_hubspot
from payment.models import Payment, Coupon, CouponDetail
from dateutil.parser import parse
from django.db.models import Q
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from userauth.models import Person
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pdb
import pytz
from .helpers import send_push_notification
from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})



@login_required(login_url="/admin-login/")
def admin_dashboard_view(request):
    try:
        logger.info(f"In admin dashboard view : {request.user.username}")
        if request.user.person_role == "Student":
            logger.info(
                f"Redirected to home page from admin dashboard view for : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))
        if request.user.person_role == "Futurely_admin":
            if request.LANGUAGE_CODE == 'en-us':
                school_country = 'USA'
                all_schools = auth_mdl.School.objects.filter(
                    country='USA', is_verified=True)
            elif request.LANGUAGE_CODE == 'it':
                school_country = 'Italy'
                all_schools = auth_mdl.School.objects.filter(
                    country='Italy', is_verified=True)
            school_regions = all_schools.order_by(
                'region').values('region').distinct()
            # school_names = auth_mdl.StudentSchoolDetail.objects.order_by('school_name').values_list('school_name').distinct()
            school_name = request.session.get('school_name', '')
            school_city = request.session.get('school_city', '')
            school_region = request.session.get('school_region', '')
            stu_email = request.session.get('stu_email', '')
            discount_code = request.session.get("discount_code", "")
            cohort_id = request.session.get('cohort_id', '')
            start_date = request.session.get('start_date', '')
            context = {}
            template_name = "futurely_admin/admin_dashboard.html"
            if school_city != "" and school_name != "" and school_region != "":
                context['selected_school_name'] = school_name
                context['selected_school_city'] = school_city
                context['selected_school_region'] = school_region
                # school detail add in session
                request.session['school_name'] = school_name
                request.session['school_city'] = school_city
                request.session['school_region'] = school_region
                context['all_students'] = auth_mdl.StudentSchoolDetail.objects.filter(
                    school_name=school_name, school_region=school_region, school_city=school_city)
                context["school_regions"] = school_regions
                logger.info(
                    f"admin dashbaord visited by : {request.user.username}")
                return render(request, template_name, context)
            elif cohort_id != '' and start_date != '':
                students = StudentCohortMapper.objects.filter(
                    cohort__cohort_id=cohort_id, cohort__starting_date=start_date).values_list('student__pk', flat=True)
                context['all_students'] = auth_mdl.StudentSchoolDetail.objects.filter(
                    student__person__in=students)
                return render(request, template_name, context)
            elif stu_email != '':
                all_students = auth_mdl.StudentSchoolDetail.objects.filter(
                    student__person__username=stu_email)
                context['all_students'] = all_students
                context["school_regions"] = school_regions
                print(all_students)
                logger.info(
                    f"admin dashbaord visited by : {request.user.username}")
                return render(request, template_name, context)
            elif discount_code != "":
                all_students = auth_mdl.StudentSchoolDetail.objects.filter(
                    student__discount_coupon_code=discount_code)
                context['all_students'] = all_students
                context["school_regions"] = school_regions
                print(all_students)
                logger.info(
                    f"admin dashbaord visited by : {request.user.username}")
                return render(request, template_name, context)
            else:
                logger.info(
                    f"admin redirected to search page for : {request.user.username}")
                return HttpResponseRedirect(reverse("search_student_information"))
    except Exception as ex:
        logger.critical(
            f"Exception error in admin dashboard view {ex} : {request.user.username}")
    return HttpResponseRedirect(reverse("admin_login"))


@login_required(login_url="/admin-login/")
def futurely_admin_search_view(request):
    try:
        context = {}
        if request.user.person_role == "Student":
            logger.info(
                f"Redirected to home page from admin dashboard view for : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))
        elif request.user.person_role == "Counselor":
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if request.user.person_role == "Futurely_admin":
            if request.LANGUAGE_CODE == 'en-us':
                school_country = 'USA'
            elif request.LANGUAGE_CODE == 'it':
                school_country = 'Italy'
            all_schools = auth_mdl.School.objects.filter(
                country=school_country, is_verified=True)
            context['school_regions'] = all_schools.order_by(
                'region').values('region').distinct()
            allcohort = models.Cohort.cohortManager.lang_code(request.LANGUAGE_CODE).values(
                'cohort_name').distinct().order_by("-starting_date")
            context['allcohort'] = allcohort
            context['discount_codes'] = Coupon.objects.all().order_by(
                '-created_at')
            print(allcohort)
            if request.method == "POST":
                stu_email = request.POST.get('student-email', None)
                discount_code = request.POST.get('discount_code', None)
                cohort_name = request.POST.get('cohort', None)
                cohort_id = request.POST.get('cohort_date', None)
                if (stu_email):
                    request.session['school_name'] = ''
                    request.session['school_city'] = ''
                    request.session['school_region'] = ''
                    request.session['stu_email'] = stu_email
                    request.session['discount_code'] = ''
                    request.session['cohort_id'] = ''
                    request.session['start_date'] = ''
                    request.session['cohort_name'] = ''
                    logger.info(
                        f"admin redirect to dashboard for : {request.user.username}")
                    return HttpResponseRedirect(reverse("admin_dashboard"))
                elif (cohort_id != None and discount_code != None and cohort_name != None):
                    request.session['school_name'] = ''
                    request.session['school_city'] = ''
                    request.session['school_region'] = ''
                    request.session['stu_email'] = ''
                    request.session['discount_code'] = discount_code
                    request.session['cohort_id'] = cohort_id
                    request.session['cohort_name'] = cohort_name
                    # request.session['start_date'] = cohort_step
                    return HttpResponseRedirect(reverse('cohort_details'))
                elif (cohort_id != None):
                    request.session['school_name'] = ''
                    request.session['school_city'] = ''
                    request.session['school_region'] = ''
                    request.session['stu_email'] = ''
                    request.session['discount_code'] = ''
                    request.session['cohort_id'] = cohort_id
                    request.session['cohort_name'] = ''
                    # request.session['start_date'] = cohort_step
                    return HttpResponseRedirect(reverse('cohort_details'))
                elif (discount_code):
                    request.session['school_name'] = ''
                    request.session['school_city'] = ''
                    request.session['school_region'] = ''
                    request.session['stu_email'] = ''
                    request.session['discount_code'] = discount_code
                    request.session['cohort_id'] = ''
                    request.session['cohort_name'] = ''
                    request.session['start_date'] = ''
                    return HttpResponseRedirect(reverse("scholarship_students_information"))
                else:
                    school_name = request.POST.get('school-name')
                    school_city = request.POST.get('school-city')
                    school_region = request.POST.get('school-region')
                    request.session['school_name'] = school_name
                    request.session['school_city'] = school_city
                    request.session['school_region'] = school_region
                    request.session['stu_email'] = ''
                    request.session['discount_code'] = ''
                    request.session['cohort_id'] = ''
                    request.session['start_date'] = ''
                    request.session['cohort_name'] = ''
                    logger.info(
                        f"Admin redirect to dashboard for : {request.user.username}")
                    return HttpResponseRedirect(reverse("admin_dashboard"))
            else:
                logger.info(
                    f"Admin dashboard visited by : {request.user.username}")
                return render(request, "futurely_admin/admin_search.html", context)
    except Exception as err:
        logger.error(
            f"Error in futurely admin search view {err} for : {request.user.username}")
        return HttpResponseRedirect(reverse("admin_dashboard"))


@login_required(login_url="/admin-login/")
def counselor_stu_performance(request):
    try:
        logger.info(f"In Admin student performance : {request.user.username}")
        if request.user.person_role == "Student":
            user_name = request.user.username
            logger.info(
                f"Redirected student to home page at Admin student performance page for : {user_name}")
            return HttpResponseRedirect(reverse("home"))
        stu_id = request.GET.get('stu_id', None)
        person = auth_mdl.Person.objects.get(id=stu_id)
        stu_cohorts = person.stuMapID.all()
        logger.info(
            f"In Admin student performance page visited by : {request.user.username}")
        return render(request, "courses/counselor_stu_performance.html", {"stu_cohorts": stu_cohorts, "student": person})
    except Exception as ex:
        logger.error(
            f"Error in Admin student performance page {ex} : {request.user.username}")
        return HttpResponseRedirect(reverse('counselor_login'))


@login_required(login_url="/admin-login/")
def student_scholarship_detail(request):
    try:
        if request.method == "POST":
            stu_id = request.POST.get("stu_id", "")
            if stu_id != "":
                data = {"Question": [], "Answer": []}
                stu_obj = auth_mdl.Person.objects.get(pk=stu_id)
                stu_mapper = StudentScholarshipTestMapper.objects.filter(
                    student=stu_obj, is_applied=True).first()
                if stu_mapper is not None:
                    stu_ques_ans_obj = StudentScholarShipTest.objects.filter(
                        stu_scholarshipTest_mapper=stu_mapper).all()
                    for stu_details in stu_ques_ans_obj:
                        data["Question"].append(
                            stu_details.scholarshipTest_question.question)
                        data["Answer"].append(
                            stu_details.scholarshipTest_answer)
                return JsonResponse(data, status=200, safe=False)
        else:
            return JsonResponse({"msg": "error"}, status=200, safe=False)
    except Exception as Error:
        logger.error(
            f"Error in student scholarship details {Error} : {request.user.username}")
        return JsonResponse({"msg": "error"}, status=400, safe=False)


@login_required(login_url="/admin-login/")
def scholarship_information_view(request):
    try:
        student = request.user.username
        if request.user.person_role == "Student":
            logger.info(
                f"Redirected to home page from scholarship information view : {student}")
            return HttpResponseRedirect(reverse("home"))
        if request.user.person_role == "Counselor":
            logger.info(
                f"Redirected to home page from scholarship information view : {student}")
            return HttpResponseRedirect(reverse("counselor-dashboard"))
        if request.user.person_role == "Futurely_admin":
            if request.LANGUAGE_CODE == 'en-us':
                school_country = 'USA'
            elif request.LANGUAGE_CODE == 'it':
                school_country = 'Italy'
            context = {}
            school_name = request.session.get('school_name', '')
            school_city = request.session.get('school_city', '')
            school_region = request.session.get('school_region', '')
            stu_email = request.session.get('stu_email', '')
            discount_code = request.session.get('discount_code', '')
            context['selected_school_name'] = school_name
            context['selected_school_city'] = school_city
            context['selected_school_region'] = school_region
            cohort_id = request.session.get('cohort_id', '')
            start_date = request.session.get('start_date', '')
            if school_city != "" and school_name != "" and school_region != "":
                all_stu = auth_mdl.Person.objects.filter(student__student_school_detail__school_name=school_name,
                                                         student__student_school_detail__school_region=school_region,
                                                         student__student_school_detail__school_city=school_city).values_list('id', flat=True)
                stud = StudentScholarshipTestMapper.objects.filter(
                    student__in=all_stu, is_applied=True, lang_code=request.LANGUAGE_CODE).all()
                context['students'] = stud
                return render(request, "courses/scholarship_students_detail.html", context)
            elif cohort_id != '' and start_date != '':
                students = StudentCohortMapper.objects.filter(
                    cohort__cohort_id=cohort_id, cohort__starting_date=start_date).values_list('student__pk', flat=True)
                # context['all_students'] = auth_mdl.StudentSchoolDetail.objects.filter(student__person__in=students)
                stud = StudentScholarshipTestMapper.objects.filter(
                    student__in=students, is_applied=True, lang_code=request.LANGUAGE_CODE).all()
                context['students'] = stud
                return render(request, "courses/scholarship_students_detail.html", context)
            elif discount_code != "":
                all_stu = auth_mdl.Person.objects.filter(
                    student__discount_coupon_code=discount_code).values_list('id', flat=True)
                stud = StudentScholarshipTestMapper.objects.filter(
                    student__in=all_stu, is_applied=True, lang_code=request.LANGUAGE_CODE).all()
                context['students'] = stud
                return render(request, "courses/scholarship_students_detail.html", context)
            elif stu_email != "":
                all_stu = auth_mdl.Person.objects.filter(
                    username=stu_email).values_list('id', flat=True)
                stud = StudentScholarshipTestMapper.objects.filter(
                    student__in=all_stu, is_applied=True, lang_code=request.LANGUAGE_CODE).all()
                context['students'] = stud
                return render(request, "courses/scholarship_students_detail.html", context)
            else:
                return HttpResponseRedirect(reverse("search_student_information"))
    except Exception as Error:
        student = request.user.username
        logger.error(
            f"Error in scholarship information view {Error} : {student}")
        return HttpResponseRedirect(reverse('admin_login'))


@login_required(login_url="/admin-login/")
def bulk_email_panel_view(request):
    try:
        logger.info(f"In bulk email panel view : {request.user.username}")
        if request.user.person_role == "Student":
            user_name = request.user.username
            logger.info(
                f"Redirected to home page at email bulk panel view for : {user_name}")
            return HttpResponseRedirect(reverse("home"))

        if request.user.person_role == "Futurely_admin":
            if request.method == "POST":
                temp_id = request.POST.get("email_temp")
                res = models.EmailTemplate.objects.get(pk=int(temp_id))
                print("Result =>", res.template_file.url)
                logger.info(
                    f"return tesmplate at email bulk panel for : {request.user.username}")
                return HttpResponse(res.template_file)
            context = {}
            context['email_temp'] = models.EmailTemplate.objects.all()
            # context['form'] = FormEmailExcelData()
            logger.info(
                f"bulk email panel view page visited by : {request.user.username}")
            return render(request, "courses/bulk_email_panel.html", context)
    except Exception as ex:
        logger.error(
            f"Error Exception in bulk email panel view {ex} : {request.user.username}")
        return HttpResponseRedirect(reverse('counselor-dashboard'))


def read_file_funciton(filename, data, request):
    try:
        logger.info(
            f"In read file function called by : {request.user.username}")
        df = pd.read_excel(filename)
        for i in range(0, len(df["Email"])):
            data_dict = {}
            data_dict["First_name"] = df['First_name'][i]
            data_dict["Email"] = df["Email"][i]
            data.append(data_dict.copy())
            data_dict.clear()
        data = json.dumps(data)
        logger.info(
            f"json data return successfully for : {request.user.username}")
        return data
    except Exception as ex:
        # print(ex)
        user_name = request.user.username
        logger.error(
            f"Exception error in read file function {ex}: {user_name}")


@login_required(login_url="/admin-login/")
def save_excel_file(request):
    try:
        logger.info(f"In save excel file view : {request.user.username}")
        if request.method == "POST":
            temp_name = request.POST.get("templatetags", None)
            filename = request.FILES['upload_file']
            subject = request.POST.get("subject", None)
            description = request.POST.get("description", None)
            campaignname = request.POST.get("campaignname", None)
            res = models.EmailTemplate.objects.get(pk=int(temp_name))
            logger.info(f"Fetched the template by : {request.user.username}")
            if filename is not None and temp_name is not None:
                _datetime = datetime.now()
                datetime_str = _datetime.strftime("%Y-%m-%d-%H-%M-%S")
                file_name_split = filename.name.split('.')
                file_name_list = file_name_split[:-1]
                ext = file_name_split[-1]
                file_name_wo_ext = '.'.join(file_name_list)
                name_of_file = '{0}-{1}.{2}'.format(
                    file_name_wo_ext, datetime_str, ext)
                obj = models.EmailForwadingDetails(
                    excel_file=filename, emailtemplate_id=res)
                obj.save()
                logger.info(
                    f"emailforwading obj created by : {request.user.username}")
                messages.success(request, "File upload Successfuly!")
                data = []
                read_file_funciton(obj.excel_file.url, data, request)
                if data is not None:
                    response = {
                        "eventType": "campaign",
                        "data": data,
                        "template": res.template_file.url,
                        "Description": description,
                        "Subject": subject,
                        "Campaign": campaignname,
                    }
                    response_data = json.dumps(response)
                    try:
                        res = settings.CLIENTSNS.publish(
                            TopicArn='arn:aws:sns:ap-south-1:994790766462:SNSLambdaEmailTracking',
                            Message=response_data
                        )

                    except Exception as error:
                        print("Exception Error :", error)
                        logger.error(
                            f"Exception error in save excel file view {error} : {request.user.username}")
                        messages.warning(request, error)
                else:
                    # logger.warning(f"error in save excel file : {request.user.username}")
                    messages.warning(request, "Oops Please try again!!")
            else:
                logger.warning(
                    f"Form data is empty in save_excel_file : {request.user.username}")
                messages.warning(request, "Something went wrong!!")
        logger.info(
            "Redirected to bulk email_panel_view from save excel file  by : {request.user.username}")
        return HttpResponseRedirect(reverse("bulk_email_panel_view"))
    except Exception as err:
        logger.error(
            f"Exception error in save_excel_file {err} : {request.user.username}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))


@login_required(login_url="/admin-login/")
def cohortfilter(request):
    if (request.is_ajax and request.method == "POST"):
        cohortname = request.POST.get('cohortname', None)
        if cohortname:
            cohorts = models.Cohort.cohortManager.lang_code(
                request.LANGUAGE_CODE).filter(Q(cohort_name__iexact=cohortname))
            # if models.step_status.objects.filter(cohort=cohortget).exists()==True:
            if cohorts.count() > 0:
                cohortdates = list(cohorts.order_by(
                    '-starting_date').values_list('cohort_id', 'starting_date'))
                return JsonResponse({'message': 'success', 'cohort_dates': cohortdates, 'cohortname': cohortname}, status=200, safe=False)
    else:
        return JsonResponse({'msg': _('Something went wrong')}, status=400)


@login_required(login_url="/admin-login/")
def discountcodefilter(request):
    if (request.is_ajax and request.method == "POST"):
        discount_code_id = request.POST.get('discount_code_id', None)
        if discount_code_id:
            coupon_obj = Coupon.objects.get(code=discount_code_id)
            if coupon_obj:
                discount_code_details_cohorts = CouponDetail.objects.filter(
                    coupon=coupon_obj).all()
                if discount_code_details_cohorts.count() > 0:
                    cohort_list = []
                    for coupon_detail in discount_code_details_cohorts:
                        if coupon_detail.cohort_program1:
                            cohort_list.append(
                                [coupon_detail.cohort_program1.cohort_name, coupon_detail.cohort_program1.cohort_id])
                        if coupon_detail.cohort_program2:
                            cohort_list.append(
                                [coupon_detail.cohort_program2.cohort_name, coupon_detail.cohort_program2.cohort_id])
                        if coupon_detail.cohort_program3:
                            cohort_list.append(
                                [coupon_detail.cohort_program3.cohort_name, coupon_detail.cohort_program3.cohort_id])
                    return JsonResponse({'message': 'success', 'cohortname': cohort_list}, status=200, safe=False)
        else:
            return JsonResponse({'msg': _('Something went wrong')}, status=400)
    else:
        return JsonResponse({'msg': _('Something went wrong')}, status=400)


class CohortDetailsView(LoginRequiredMixin, View):
    template_name = "futurely_admin/cohort_details.html"

    def get(self, request):
        cohort_id = self.request.session.get('cohort_id', '')
        discount_code = self.request.session.get('discount_code', '')
        cohort_name = self.request.session.get('cohort_name', '')
        if cohort_id != "" and discount_code != "" and cohort_name != "":
            self.template_name = "futurely_admin/cohort_details2.html"
            context = {}
            cohorts_with_coupon = models.Cohort.objects.filter(
                Q(coupon_cohort_p1_info__coupon__code=discount_code) |
                Q(coupon_cohort_p2_info__coupon__code=discount_code) |
                Q(coupon_cohort_p3_info__coupon__code=discount_code)
            )
            cohorts = cohorts_with_coupon.filter(
                Q(cohort_name__iexact=cohort_name) & Q(cohort_id=cohort_id)).first()
            # cohorts = cohorts_with_coupon.filter(Q(cohort_name__iexact=cohort_name) & Q(cohort_id=cohort_id) & Q(cohortMapID__student__student__discount_coupon_code__in=discount_code_list)).first()
            if cohorts:
                context["cohorts"] = cohorts
                context["academic_session_start_date"] = cohorts.starting_date
                context["datenow"] = date.today()
                return render(self.request, self.template_name, context)
        if cohort_id == "" or cohort_id == None:
            logger.info(
                f"Cohort values in None : {self.request.user.username}")
            return HttpResponseRedirect(reverse("search_student_information"))
        else:
            context = {}
            cohorts = models.Cohort.cohortManager.lang_code(
                self.request.LANGUAGE_CODE).filter(cohort_id=cohort_id).first()
            if cohorts:
                context["cohorts"] = cohorts
                context["academic_session_start_date"] = cohorts.starting_date
                context["datenow"] = date.today()
                return render(self.request, self.template_name, context)
        logger.info(f"Cohort values in None : {self.request.user.username}")
        return HttpResponseRedirect(reverse("search_student_information"))


@login_required(login_url="/admin-login/")
def students_step_detail(request, cohort_id, step_status_id):
    try:
        context = {}
        cohort = models.Cohort.cohortManager.lang_code(
            request.LANGUAGE_CODE).get(cohort_id=cohort_id)
        step_status = cohort.cohort_step_status.filter(
            id=step_status_id).first()
        # step_student_data = step_status.step_status_id.all().order_by("-cohort_step_tracker_details")
        discount_code = request.session.get('discount_code', '')
        if discount_code != '':
            coupon_obj = Coupon.objects.filter(
                code=discount_code).values_list('code', flat=True)
            coupon_obj = list(coupon_obj)
            stu_payments = Payment.objects.filter(
                coupon_code__in=coupon_obj).values_list('person__id', flat=True)
            step_student_data = step_status.step_status_id.filter(stu_cohort_map__student__id__in=stu_payments).all(
            ).annotate().order_by('-cohort_step_tracker_details__last_commented_date_time')
        else:
            step_student_data = step_status.step_status_id.all().annotate().order_by(
                '-cohort_step_tracker_details__last_commented_date_time')
        context["cohort"] = cohort
        context["step_status"] = step_status
        context["step_student_data"] = step_student_data
        return render(request, 'futurely_admin/step_and_data.html', context)
    except Exception as Error:
        logger.error(
            f"Error in Studen_step_detail {Error} for : {request.user.email}")
        return HttpResponseRedirect(reverse("cohort_details"))


class PushNotificationByCohort(LoginRequiredMixin, View):
    template_name = "futurely_admin/send_push_notification_by_cohort.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context["cohorts_list"] = models.Cohort.objects.filter(
            starting_date__gte="2022-08-01")
        context["form"] = CohortSendPushNotificationForm()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = CohortSendPushNotificationForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            title = form.cleaned_data['title']
            body = form.cleaned_data['body']
            push_form = form.save(commit=False)
            response = send_push_notification(topic, body, title)
            if response != None:
                response_data = response.json()
                message_id = response_data['message_id']
                push_form.response_msg_id = message_id
                push_form.save()
                messages.success(request, _(
                    "Push notification sent successfully"))
            else:
                messages.error(request, _("Failed Push notification!"))
        else:
            messages.error(request, _("Failed Push notification!"))
        return HttpResponseRedirect(reverse('send_push_notification_by_cohort'))


class SendPushNotificationView(LoginRequiredMixin, View):
    template_name = "futurely_admin/send_push_notification.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context['form'] = SendPashNotificationForm()
        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = SendPashNotificationForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            title = form.cleaned_data['title']
            body = form.cleaned_data['body']
            push_form = form.save(commit=False)
            response = send_push_notification(topic, body, title)
            if response != None:
                response_data = response.json()
                message_id = response_data['message_id']
                push_form.response_msg_id = message_id
                push_form.save()
                messages.success(request, _(
                    "Push notification sent successfully"))
            else:
                messages.error(self.request, _("Something went wrong!"))
        else:
            messages.error(self.request, _("Something went wrong!"))
        return HttpResponseRedirect(reverse('send_push_notification'))


@login_required(login_url="/admin-login/")
def get_dynamodb(request):
    logger.info(f"In get dynamodb view : {request.user.username}")
    if request.user.person_role == "Student":
        logger.info(
            f"In get dynamodb view Redirected to home page : {request.user.username}")
        return HttpResponseRedirect(reverse("home"))

    try:
        if request.user.person_role == "Futurely_admin":
            context = {}
            table_dict = {}
            print("User Role: ", request.user.person_role)
            table1 = settings.DYNAMODB.Table("P_Campaign")
            table_data = table1.scan()
            logger.info(
                f"fetched the data from dynamodb at get dynamodb view : {request.user.username}")
            res = table_data["Items"]
            context["res"] = res
            if request.method == 'GET' and 'camp_id' in request.GET:
                Campaignid = request.GET['camp_id']
                print("ID :", Campaignid)
                camp_id_data = table1.query(
                    KeyConditionExpression=Key('ID').eq(Campaignid))["Items"]
                table_dict["from"] = camp_id_data[0]["from"]
                context["from"] = camp_id_data[0]["from"]
                context["template"] = camp_id_data[0]["message"]
                camp_name = camp_id_data[0]["compaign"]
                table_dict["template_url"] = camp_id_data[0]["message"]
                table_dict["ID"] = camp_id_data[0]["ID"]
                P_CampaignEmailDetail = settings.DYNAMODB.Table(
                    "P_CampaignEmailDetail")
                CampaignEmailDetailItems = P_CampaignEmailDetail.scan(
                    FilterExpression=Attr("Campaign_ID").eq(Campaignid))['Items']
                print('sent item count: ', len(CampaignEmailDetailItems))
                EmailEvent = settings.DYNAMODB.Table("P_EmailEvent")
                EmailEventItems = EmailEvent.scan(
                    FilterExpression=Attr("CampaignID").eq(Campaignid))['Items']
                print('item count of email event: ', len(EmailEventItems))
                clinet = settings.DYNAMODBCLIENT
                deliveryitems = clinet.execute_statement(
                    Statement="select eventType from P_EmailEvent where CampaignID='"+Campaignid+"' and eventType='Delivery'")["Items"]
                print('deliveryItems', len(deliveryitems))
                openitems = clinet.execute_statement(
                    Statement="select eventType from P_EmailEvent where CampaignID='"+Campaignid+"' and eventType='Open'")["Items"]
                print('deliveryItems', len(openitems))
                clickitems = clinet.execute_statement(
                    Statement="select eventType from P_EmailEvent where CampaignID='"+Campaignid+"' and eventType='Click'")["Items"]
                print('deliveryItems', len(clickitems))
                bounceitems = clinet.execute_statement(
                    Statement="select eventType from P_EmailEvent where CampaignID='"+Campaignid+"' and eventType='Bounce'")["Items"]
                print('deliveryItems', len(bounceitems))
                sentitems = clinet.execute_statement(
                    Statement="select status from P_CampaignEmailDetail where Campaign_ID='"+Campaignid+"' and status='Sent'")["Items"]
                print('deliveryItems', len(sentitems))
                context["sent"] = CampaignEmailDetailItems
                context["otherevent"] = EmailEventItems
                context["delivery"] = len(deliveryitems)
                context["open"] = len(openitems)
                context["click"] = len(clickitems)
                context["bounce"] = len(bounceitems)
                context["sent_count"] = len(sentitems)
                context["camp_name"] = "Results for Campaign: " + camp_name
                user_name = request.user.username
                logger.info(f"In get dynamodb view visited by {user_name}")
            return render(request, "futurely_admin/email_tracking_dashboard.html", context)
    except Exception as ex:
        print(ex)
        logger.error(
            f"Error Exception in get dynamodb view {ex} : {request.user.username}")
    return HttpResponseRedirect(reverse('admin_dashboard'))


@login_required(login_url="/admin-login/")
def student_performace_for_admin_view(request):
    try:
        logger.info(
            f"In students performance for Futurely Admin : {request.user.username}")
        if request.user.person_role == "Student":
            logger.info(
                f"Redirected to home page from admin dashboard view : {request.user.username}")
            return HttpResponseRedirect(reverse("home"))
        if request.user.person_role == "Futurely_admin":
            if request.LANGUAGE_CODE == 'en-us':
                school_country = 'USA'
                all_schools = auth_mdl.School.objects.filter(
                    country='USA', is_verified=True)
            elif request.LANGUAGE_CODE == 'it':
                school_country = 'Italy'
                all_schools = auth_mdl.School.objects.filter(
                    country='Italy', is_verified=True)
            school_regions = all_schools.order_by(
                'region').values('region').distinct()
            school_name = request.session.get('school_name', '')
            school_city = request.session.get('school_city', '')
            school_region = request.session.get('school_region', '')
            stu_email = request.session.get('stu_email', '')
            discount_code = request.session.get("discount_code", "")
            context = {}
            all_courses_students = []
            if school_name != '' and school_city != '' and school_region != '' or stu_email != '' or discount_code != '':
                if stu_email != "":
                    all_stu = auth_mdl.Person.objects.filter(
                        email=stu_email).values_list('id', flat=True)
                    logger.info(
                        f"fetch students performance with email for Futurely Admin : {request.user.username}")
                elif discount_code != "":
                    all_stu = auth_mdl.Person.objects.filter(
                        student__discount_coupon_code=discount_code).values_list('id', flat=True)
                    logger.info(
                        f"fetch students performance with discount code for Futurely Admin : {request.user.username}")
                else:
                    all_stu = auth_mdl.Person.objects.filter(student__student_school_detail__school_name=school_name,
                                                             student__student_school_detail__school_region=school_region,
                                                             student__student_school_detail__school_city=school_city).values_list('id', flat=True)
                    logger.info(
                        f"fetch students performance with school details for Futurely Admin : {request.user.username}")
                module_id = request.GET.get('module_id', None)
                context['selected_school_name'] = school_name
                context['selected_school_city'] = school_city
                context['selected_school_region'] = school_region
                logger.info(
                    f"all premium students - {all_stu} - fetched in students performance for Futurely Admin : {request.user.username}")
                courses = models.Modules.objects.filter(
                    module_lang=request.LANGUAGE_CODE, is_for_middle_school=False, is_for_fast_track_program=False)
                context['courses'] = courses
                if module_id is None:
                    course = courses.first()
                    context['module_id'] = course.module_id
                else:
                    course = courses.get(module_id=module_id)
                    context['module_id'] = course.module_id
                # for course in courses:
                stud = StudentCohortMapper.objects.filter(student__in=all_stu, cohort__module__module_id=course.module_id, stu_cohort_lang=request.LANGUAGE_CODE).all(
                ).order_by('student__first_name')  # .order_by("-stu_cohort_map__step_tracker__action_item_diary__student_actions_item_diary_id__created_at")
                steps = course.steps.exclude(is_backup_step=True).all()
                if (stud.count() > 0):
                    all_courses_students.append([stud, steps, course])
                logger.info(
                    f"all_courses_students -{all_courses_students}- for students performance fetched for Futurely Admin : {request.user.username}")
                context['all_courses_students'] = all_courses_students
                context["school_regions"] = school_regions
                logger.info(
                    f"Render students performance for Futurely Admin : {request.user.username}")
                return render(request, "futurely_admin/admin_student_details.html", context)
            else:
                return HttpResponseRedirect(reverse('search_student_information'))
    except Exception as err:
        logger.error(
            f"Exception Error in student_performace_for_counselor_view {err} : {request.user.username}")
    return HttpResponseRedirect(reverse('admin_login'))


def scholarship_approved_view(request):
    try:
        if request.method == "POST":
            request_post = request.POST
            scholarship_id = request_post.get("scholarship_id")
            stud_id = request_post.get("stu_id")
            student_obj = auth_mdl.Person.objects.get(id=stud_id)
            plan = StudentsPlanMapper.plansManager.lang_code(
                request.LANGUAGE_CODE).filter(student=student_obj).first()
            current_plan = plan.plans.plan_name
            if current_plan == "Community" or plan.is_trial_active == True:
                plan_to_upgarde = models.OurPlans.plansManager.lang_code(
                    request.LANGUAGE_CODE).filter(plan_name="Elite").first()
                plan.is_trial_active = False
                plan.plans = plan_to_upgarde
                stud = StudentScholarshipTestMapper.objects.get(
                    id=scholarship_id)
                if stud.is_applied == True:
                    currency = "usd"
                    if request.LANGUAGE_CODE == "it":
                        currency = "eur"
                    stu_discount_code = student_obj.student.discount_coupon_code
                    custom_user_session_id = request.session.get(
                        'CUSTOM_USER_SESSION_ID', '')
                    Payment.objects.create(stripe_id="", person=student_obj, plan=plan_to_upgarde, coupon_code=stu_discount_code,
                                           actual_amount=plan_to_upgarde.cost, discount=plan_to_upgarde.cost, amount="0", currency=currency, status="succeeded",
                                           payment_email_id=student_obj.email, custom_user_session_id=custom_user_session_id)
                    plan.save()
                    stud.status = "Approved"
                    stud.save()
                    keys_list = ['email', "scholarship_status"]
                    values_list = [stud.student.username, "Approved"]
                    create_update_contact_hubspot(
                        stud.student.username, keys_list, values_list)
                # send_mail_to_student.delay(student_obj.email, "Approved")
                # send_mail_to_student(student_obj.email, "Approved")
                return JsonResponse({"msg": "success"}, status=200, safe=False)
            return JsonResponse({"msg": "Plan already upgraded"}, status=200, safe=False)
    except Exception as err:
        print(err)
        return JsonResponse({"msg": "error"}, status=400, safe=False)


def declied_scholarship_view(request):
    try:
        school_name = request.session.get('school_name', '')
        school_city = request.session.get('school_city', '')
        school_region = request.session.get('school_region', '')
        discount_code = request.session.get('discount_code', '')
        student_email = request.session.get('stu_email', '')
        if school_city != "" and school_name != "" and school_region != "":
            all_stu = auth_mdl.Person.objects.filter(student__student_school_detail__school_name=school_name,
                                                     student__student_school_detail__school_region=school_region,
                                                     student__student_school_detail__school_city=school_city).values_list('id', flat=True)
            scho_students = StudentScholarshipTestMapper.objects.filter(
                student__in=all_stu, is_applied=True, status="Applied", lang_code=request.LANGUAGE_CODE).all()

        elif discount_code != "":
            all_stu = auth_mdl.Person.objects.filter(
                student__discount_coupon_code=discount_code).values_list('id', flat=True)
            scho_students = StudentScholarshipTestMapper.objects.filter(
                student__in=all_stu, is_applied=True, status="Applied", lang_code=request.LANGUAGE_CODE).all()

        elif student_email != "":
            all_stu = auth_mdl.Person.objects.filter(
                username=student_email).values_list('id', flat=True)
            scho_students = StudentScholarshipTestMapper.objects.filter(
                student__in=all_stu, is_applied=True, status="Applied", lang_code=request.LANGUAGE_CODE).all()
        else:
            logger.info(
                f"redirect to decline scholarship view : {request.user.username}")
            return HttpResponseRedirect(reverse("search_student_information"))
        if scho_students.count() > 0:
            stduent_emails = scho_students.values_list(
                'student__email', flat=True)
            # send_mail_to_student.delay(list(stduent_emails), "Declined")
            # send_mail_to_student(list(stduent_emails), "Declined")
            scho_students.update(status="Declined")
            for student_scho in stduent_emails:
                keys_list = ['email', "scholarship_status"]
                values_list = [student_scho, "Declined"]
                create_update_contact_hubspot(
                    student_scho, keys_list, values_list)
            logger.info(
                f"All student scholarship decline by the Futurely Admin : {request.user.username}")
            return HttpResponseRedirect(reverse("scholarship_students_information"))
        logger.info(
            f"redirect to decline scholarship view : {request.user.username}")
        return HttpResponseRedirect(reverse("search_student_information"))
    except Exception as Error:
        logger.error(f"Error in scholarship declined view : {Error}")
    return HttpResponseRedirect(reverse("scholarship_students_information"))


def submit_comment_function(person, stu_diary, comment, comment_pk=''):
    try:
        if comment_pk == '':
            comment_obj = StudentActionItemDiaryComment.objects.create(person=person,
                                                                       student_actions_item_diary_id=stu_diary, comment=comment)
            is_comment_obj_created = True
        else:
            comment_obj, is_comment_obj_created = StudentActionItemDiaryComment.objects.update_or_create(
                pk=comment_pk,
                person=person,
                student_actions_item_diary_id=stu_diary,
                defaults={"comment": comment})
        # comment_obj = StudentActionItemDiaryComment.objects.create(person=request.user,
        #     student_actions_item_diary_id=stu_diary, comment=comment)
        local_tz = pytz.timezone(settings.TIME_ZONE)
        dt = local_tz.localize(datetime.now())
        cohort_step_tracker = stu_diary.action_item_track.step_tracker
        obj, created = CohortStepTrackerDetails.objects.update_or_create(
            cohort_step_tracker=cohort_step_tracker,
            defaults={'last_commented_date_time': dt},
        )
        if is_comment_obj_created:
            obj.total_comments += 1
            obj.save()
        stu_step = comment_obj.student_actions_item_diary_id.action_item_track.step_tracker
        stu_step.last_commented_date_time = dt
        # stu_step.total_comments += 1
        stu_step.save()
        # stu_obj = auth_mdl.Person.objects.filter(email=stu_diary.email).first()
        notification_type = models.Notification_type.objects.filter(
            notification_type="Diary").first()
        student = comment_obj.student_actions_item_diary_id.action_item_track.step_tracker.stu_cohort_map.student
        models.Notification.objects.create(student=student, title=_(
            'Hey, the tutor commented on your diary! Check out the “My journal” section.'), notification_type=notification_type)
        logger.info(f"student diary comment created by : {person.username}")
        return True
    except:
        logger.error(
            f"Error in student diary comment created by : {person.username}")
        return False


def submit_comment_view(request):
    try:
        student = request.user.username
        if request.method == "POST":
            request_post = request.POST
            comment = request_post.get("comment")
            stu_ans_id = request_post.get("answer")
            comment_pk = request_post.get('comment_pk', '')
            stu_diary = get_object_or_404(
                StudentActionItemDiary, pk=stu_ans_id)
            is_comment_obj_created = False
            status = submit_comment_function(
                request.user, stu_diary, comment, comment_pk)
            # if comment_pk == '':
            #     comment_obj = StudentActionItemDiaryComment.objects.create(person=request.user,
            #         student_actions_item_diary_id=stu_diary, comment=comment)
            #     is_comment_obj_created = True
            # else:
            #     comment_obj, is_comment_obj_created = StudentActionItemDiaryComment.objects.update_or_create(
            #         pk=comment_pk,
            #         person=request.user,
            #         student_actions_item_diary_id=stu_diary,
            #         defaults={"comment": comment})
            # # comment_obj = StudentActionItemDiaryComment.objects.create(person=request.user,
            # #     student_actions_item_diary_id=stu_diary, comment=comment)
            # local_tz = pytz.timezone(settings.TIME_ZONE)
            # dt = local_tz.localize(datetime.now())
            # cohort_step_tracker = stu_diary.action_item_track.step_tracker
            # obj, created = CohortStepTrackerDetails.objects.update_or_create(
            #     cohort_step_tracker=cohort_step_tracker,
            #     defaults={'last_commented_date_time': dt},
            # )
            # if is_comment_obj_created:
            #     obj.total_comments += 1
            #     obj.save()
            # stu_step = comment_obj.student_actions_item_diary_id.action_item_track.step_tracker
            # stu_step.last_commented_date_time = dt
            # # stu_step.total_comments += 1
            # stu_step.save()
            # stu_obj = auth_mdl.Person.objects.filter(email=stu_diary.email).first()
            # notification_type = models.Notification_type.objects.filter(notification_type="General").first()
            # models.Notification.objects.create(student=stu_obj, title=_('Hey, the tutor commented on your diary! Check out the “My journal” section.'), notification_type=notification_type)
            # logger.info(f"student diary comment created by : {student}")
            if status:
                return JsonResponse({"msg": "created"}, status=201, safe=False)
        else:
            logger.error(f"Error in submit_comment_view : {student}")
            return JsonResponse({"msg": "Request error"}, status=400, safe=False)
    except Exception as Error:
        logger.error(
            f"Error in submit comment view {Error} : {request.user.username}")
    return JsonResponse({"msg": "Error"}, status=400, safe=False)


def excelfiledownload(request):
    try:
        logger.info(f"In excel file download view : {request.user.username}")
        # content-type of response
        response = HttpResponse(content_type='application/ms-excel')
        # decide file name
        response['Content-Disposition'] = 'attachment; filename="SampleFile.xls"'
        # creating workbook
        wb = xlwt.Workbook(encoding='utf-8')
        # adding sheet
        ws = wb.add_sheet("sheet1")
        # Sheet header, first row
        row_num = 0
        font_style = xlwt.XFStyle()
        # headers are bold
        font_style.font.bold = True
        columns = ['First_name', 'Email',]
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)
        font_style = xlwt.XFStyle()
        wb.save(response)
        logger.info(f"Excel file downloaded by : {request.user.username}")
        return response
    except Exception as err:
        user_name = request.user.username
        logger.error(
            f"Exception error in excel file download function {err} : {user_name}")


@login_required(login_url="/counselor-login/")
def account_settings_view_futurely_admin(request):
    context = {}
    current_user = request.user
    logger.info(
        f"In account_settings_view_counselor page called by : {current_user.username}")
    if request.user.person_role == "Student":
        logger.info(
            f"Redirected Student to account_settings_view_counselor from home : {current_user.userame}")
        return HttpResponseRedirect(reverse("home"))
    if request.user.person_role == "Counselor":
        logger.info(
            f"Redirected Student to account_settings_view_counselor from home : {current_user.userame}")
        return HttpResponseRedirect(reverse("counselor-dashboard"))
    try:
        if request.method == "POST":
            request_post = request.POST
            first_name = request_post.get('first_name', None)
            last_name = request_post.get('last_name', None)
            # email = request_post.get('email', None)
            if first_name:
                current_user.first_name = first_name
            if last_name:
                current_user.last_name = last_name
            # if email:
            #     current_user.email = email
            current_user.save()
            logger.info(
                f"Account settings updated at account_settings_view_counselor for : {current_user.username}")
        context['first_name'] = current_user.first_name
        context['last_name'] = current_user.last_name
        context['email'] = current_user.email
        context['current_user'] = current_user
        logger.info(
            f"Account settings counselor page visited by : {current_user.username}")
        return render(request, "futurely_admin/account-settings-futurely-admin.html", context)
    except Exception as error:
        current_user = request.user
        logger.critical(
            f"Error to account settings counselor page {error} for : {current_user.username}")
        return HttpResponseRedirect(reverse('admin_dashboard'))


@login_required(login_url="/admin-login/")
def ai_generated_comments_dashborad(request):
    context = {}
    all_ai_generated_comments = StudentActionItemDiaryAIComment.objects.all()
    ai_generated_comments = all_ai_generated_comments.filter(
        ai_comment_status='Generated')
    paginator = Paginator(ai_generated_comments, 10)
    page = request.GET.get('page')
    try:
        ai_comments = paginator.page(page)
    except PageNotAnInteger:
        ai_comments = paginator.page(1)
    except EmptyPage:
        ai_comments = paginator.page(paginator.num_pages)
    context['ai_generated_comments'] = ai_comments
    context['total_ai_comments'] = all_ai_generated_comments.count()
    context['total_ai_generated_comments'] = ai_generated_comments.count()
    context['total_ai_published_comments'] = all_ai_generated_comments.filter(ai_comment_status='Published').count()
    context['total_ai_modified_published_comments'] = all_ai_generated_comments.filter(ai_comment_status='Modified Published').count()
    context['total_ai_cancelled_comments'] = all_ai_generated_comments.filter(ai_comment_status='Cancelled').count()
    context['page'] = page
    return render(request, "futurely_admin/ai_generated_records.html", context)


@login_required(login_url="/admin-login/")
def publish_and_modify_ai_commnets(request):
    if request.method == "POST" and request.is_ajax:
        try:
            id = request.POST.get('id')
            ai_comment_type = request.POST.get('ai_comment_type')
            stu_ai_generated_obj = get_object_or_404(
                StudentActionItemDiaryAIComment, id=id)
            if stu_ai_generated_obj:
                if ai_comment_type == 'Published':
                    status = submit_comment_function(
                        request.user, stu_ai_generated_obj.student_actions_item_diary_id, stu_ai_generated_obj.ai_comment)
                    if status:
                        stu_ai_generated_obj.ai_comment_status = 'Published'
                        stu_ai_generated_obj.save()
                        student = stu_ai_generated_obj.student_actions_item_diary_id.action_item_track.step_tracker.stu_cohort_map.student
                        create_stu_diary_notification(student)
                        logger.info(
                            f"AI record published successfully by : {request.user.username}")
                        try:
                            keys_list = ['email', 'Is_diary_commented']
                            values_list = [student.username, 'Yes']
                            create_update_contact_hubspot(student.username, keys_list, values_list)
                            logger.info(f'Hubspot properties updated for : {student.username}')
                        except Exception as er:
                            logger.error(f'Error in update hubspot property Is_diary_commented {er} for : {student.username}')
                        return JsonResponse({"msg": "success"}, status=200, safe=False)
                    else:
                        logger.error(
                            f"AI record not published by : {request.user.username}")
                        return JsonResponse({"msg": "error"}, status)
                elif ai_comment_type == 'Modified':
                    ai_modified_comment = request.POST.get('ai_modified_data')
                    status = submit_comment_function(
                        request.user, stu_ai_generated_obj.student_actions_item_diary_id, ai_modified_comment)
                    if status:
                        stu_ai_generated_obj.ai_comment_status = 'Modified Published'
                        stu_ai_generated_obj.save()
                        student = stu_ai_generated_obj.student_actions_item_diary_id.action_item_track.step_tracker.stu_cohort_map.student
                        create_stu_diary_notification(student)

                        logger.info(
                            f"AI record published successfully by : {request.user.username}")
                        try:
                            keys_list = ['email', 'Is_diary_commented']
                            values_list = [student.username, 'Yes']
                            create_update_contact_hubspot(student.username, keys_list, values_list)
                            logger.info(f'Hubspot properties updated for : {student.username}')
                        except Exception as er:
                            logger.error(f'Error in update hubspot property Is_diary_commented {er} for : {student.username}')
                        return JsonResponse({"msg": "success"}, status=200, safe=False)
                    else:
                        logger.error(
                            f"AI record not published by : {request.user.username}")
                        return JsonResponse({"msg": "error"}, status)
            else:
                logger.error(
                    f"StudentActionItemDiaryAIComment obj not found dor request ID : {id}")
                return JsonResponse({"msg": "error"}, status=400, safe=False)
        except Exception as error:
            logger.error(f"Error occurred while publishing AI record: {error}")
    return JsonResponse({"msg": "error"}, status=400, safe=False)


def create_stu_diary_notification(student):
    notification_type_obj = models.Notification_type.objects.get(notification_type='Diary')
    PersonNotification.objects.update_or_create(
        person=student, notification_type=notification_type_obj)
    Stu_Notification.objects.create(student=student, type="Diary", title=_("La tua tutor ti ha scritto un messaggio nel diario di bordo"))


@login_required(login_url="/admin-login/")
def remove_ai_comments(request):
    if request.method == "POST" and request.is_ajax:
        try:
            id = request.POST.get('id')
            stu_ai_generated_obj = get_object_or_404(
                StudentActionItemDiaryAIComment, id=id)
            if stu_ai_generated_obj:
                stu_ai_generated_obj.ai_comment_status = 'Cancelled'
                stu_ai_generated_obj.save()
                logger.info(f"AI comment removed for ID : {id}")
                return JsonResponse({"msg": "success"}, status=200, safe=False)
            else:
                logger.error(
                    f"obj not found for request ID : {id}  at remove_ai_comments method ")
                return JsonResponse({"msg": "error"}, status=400, safe=False)
        except Exception as error:
            logger.error(
                f"An error occured while remove ai generated comment at remove_ai_comments method error: {error} ")
    return JsonResponse({"msg": "error"}, status=400, safe=False)


@login_required(login_url="/admin-login/")
def filter_ai_generated_comments(request,program_name):

    context = {}
    all_ai_generated_comments = StudentActionItemDiaryAIComment.objects.all()
    logger.info(f"Filtering ai comments for : {program_name}")
    if program_name == "from_middle_school":
        all_ai_generated_comments = all_ai_generated_comments.filter(student_actions_item_diary_id__action_item_track__step_tracker__stu_cohort_map__student__student__is_from_middle_school=True) 
    elif program_name == "from_fast_track_program":
        all_ai_generated_comments = all_ai_generated_comments.filter(student_actions_item_diary_id__action_item_track__step_tracker__stu_cohort_map__student__student__is_from_fast_track_program=True)
    ai_generated_comments = all_ai_generated_comments.filter(ai_comment_status='Generated')
    paginator = Paginator(ai_generated_comments, 5)
    page = request.GET.get('page')
    try:
        ai_comments = paginator.page(page)
    except PageNotAnInteger:
        ai_comments = paginator.page(1)
    except EmptyPage:
        ai_comments = paginator.page(paginator.num_pages)
        
    context['ai_generated_comments'] = ai_comments
    context['total_ai_comments'] = all_ai_generated_comments.count()
    context['total_ai_generated_comments'] = all_ai_generated_comments.filter(ai_comment_status='Generated').count()
    context['total_ai_published_comments'] = all_ai_generated_comments.filter(ai_comment_status='Published').count()
    context['total_ai_modified_published_comments'] = all_ai_generated_comments.filter(ai_comment_status='Modified Published').count()
    context['total_ai_cancelled_comments'] = all_ai_generated_comments.filter(ai_comment_status='Cancelled').count()
    context['school_program'] = program_name
    context['page'] = page
    logger.info(f"Successfully filtered AI comments for: {program_name}")
    return render(request, "futurely_admin/ai_generated_records.html", context)
