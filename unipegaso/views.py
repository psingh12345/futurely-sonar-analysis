from django.shortcuts import render
from .models import *
from .forms import StudentUniPegasoForm
from django.views.generic import View
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
import logging, requests
from django.template.loader import render_to_string, get_template
from django.conf import settings
from django.core.mail import message, send_mail, BadHeaderError, EmailMessage
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import blue
from django.core.files import File
from os.path import basename
import datetime
import ast, os, pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.core.files.storage import default_storage
from lib.custom_logging import CustomLoggerAdapter

adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


class UniPegasoIndexView(View):
    template_name = "unipegaso/index.html"

    def get(self, request):
        request.session["lang"] = "it"
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        current_user_id = request.session.get("current_user_id", None)
        context = {}
        if current_user_id is not None:
            try:
                stu_obj = StudentDetail.objects.get(pk=current_user_id)
                logger.info(f"unipegaso: user authorised to visit quiz-view(GET): {custom_user_session_id}")
                test_count = request.session.get('test_count', 1)
                # test_count = request.session['test_count'] = 1
                is_page_refresh = request.session.get('is_page_refresh', False)
                if is_page_refresh:
                    request.session.flush()
                    logger.info(f"unimercatorum: refresh the page and flush the session")
                    return render(request, self.template_name, context)
                if test_count == 1:
                    # pt_obj = UniPegasoActionItemsPTQuestion.objects.filter(unipegaso_test__type="PT")[:5]
                    pt_obj = UniPegasoActionItemsPTQuestion.objects.filter(unipegaso_test__type="PT")
                    unipegaso_test = pt_obj[0].unipegaso_test
                    UnipagesoStudentPTMapper.objects.update_or_create(student_detail=stu_obj, defaults={"unipegaso_test": unipegaso_test})
                    context["questions"] = pt_obj
                    logger.info(f"unipegaso: quiz page rendered(GET): {custom_user_session_id}")
                    request.session['is_page_refresh'] = True
                    return render(request, self.template_name, context)
                else:
                    test_count =  request.session.get('test_count', None)
                    current_user_id =  request.session.get('current_user_id', None)
                    logger.info(f"unipegaso: user visited Next-slide-view page for : {custom_user_session_id}")
                    return render(request, self.template_name, context)
            except Exception as Err:
                try:
                    request.session.flush()
                except:
                    logger.error(f"unipegaso: Error at index view to pop the elements for : {custom_user_session_id}")
                logger.info(f"unipegaso: Error in unipegaso index-view {Err} : {custom_user_session_id}")
                return render(request, self.template_name, context)
        else:
            try:
                request.session.flush()
            except:
                logger.error(f"unipegaso: Error at index view to pop the elements for : {custom_user_session_id}")
            logger.info(f"unipegaso: user visited Next-slide-view page for : {custom_user_session_id}")
            # student_obj = StudentDetail.objects.get(pk=157)
            # update_google_sheet(request, student_obj)
            return render(request, self.template_name, context)

def pt_test_submit(request):
    custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
    if request.method == "POST":
        test_count = request.session.get('test_count')
        context = {}
        if test_count == 1:
            try:
                custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
                current_user_id = request.session.get("current_user_id")
                logger.info(f"unipegaso: user submitted Quiz-view POST request for : {custom_user_session_id}")
                form_data = request.POST
                form_qus_id = form_data.get('question', "")
                answer = form_data.get('answer', "")
                is_last_question = form_data.get('is_last_question', "")
                if form_qus_id == "" and answer == "" and is_last_question == "":
                    return JsonResponse({"error_msg": "Accetta prima di procedere"}, status=200)
                uni_type_bit = request.session.get('uni_type_bit', 1)
                question = UniPegasoActionItemsPTQuestion.objects.filter(unipegaso_test__type="PT", id=form_qus_id).first()
                unipegaso_test = question.unipegaso_test
                stu_obj = StudentDetail.objects.get(pk=current_user_id)
                stu_mapper = UnipagesoStudentPTMapper.objects.filter(student_detail=stu_obj, unipegaso_test=unipegaso_test).first()
                created_obj = UnipegasoStudentPTAnswer.objects.create(unipegaso_student_mapper=stu_mapper, 
                    unipegaso_question=question,is_completed=True,answer=answer)
                stu_obj.assessment_status = "Pending"
                stu_obj.save()
                logger.info(f"unipegaso: user quiz answer submited successfully for : {custom_user_session_id}")
                if created_obj:
                    if is_last_question == "Yes":
                        logger.info(f"unipegaso: user redirected to test result page from quiz post page for : {custom_user_session_id}")
                        request.session['test_count'] = 2
                        request.session['progress_bar_count'] = 60
                        request.session['total_next_question_count'] = 9
                        stu_mapper = UnipagesoStudentPTMapper.objects.filter(student_detail=stu_obj).first()
                        my_score = stu_mapper.calculate_my_score
                        sorted_my_score = sorted(my_score.items(), key=lambda x: x[1],reverse=True)
                        stu_mapper.rising_test_result = sorted_my_score[0][0][1]
                        stu_mapper.is_completed = True
                        stu_mapper.save()
                        context['my_score'] = my_score
                        context['sorted_my_score'] = sorted_my_score
                        request.session['is_first_time'] = True
                        context['stu_mapper'] = stu_mapper
                        logger.info(f"unipegaso: user visited TestResult-view page for : {custom_user_session_id}")
                        return render(request, "unipegaso/test_result.html", context)
                    else:
                        return JsonResponse({"success": "Yes"})
                else:
                    return JsonResponse({"error": "Qualcosa è andato storto!!"})
            except Exception as Error:
                if custom_user_session_id:
                    logger.error(f"Unipegaso: Error in p-test post {Error} : {custom_user_session_id}")
                else:
                    logger.error(f"Unipegaso: Error in p-test post {Error}")
            return JsonResponse({"error_msg": "Qualcosa è andato storto"})

        elif test_count == 2 or test_count == 3:
            try:
                is_next_question_slide = request.POST.get('is_next_question_slide', "False")
                logger.info(f"unipegaso: user submitted Quiz-view POST request for : {custom_user_session_id}")
                is_video_filter = request.POST.get('is_video_filter', "False")
                print(f"is_next_question_slide = {is_next_question_slide}")
                print(f"is_video_filter = {is_video_filter}")
                if is_next_question_slide == "True":
                    next_count = int(request.POST.get('next_count', 3))
                    request.session["test_count"] = 3
                    is_first_time = request.session.get('is_first_time')
                    if is_first_time:
                        question_sno = str(1)
                        request.session['question_sno'] = question_sno
                        request.session['is_first_time'] = False
                        context["button_is_active"] = True
                    else:
                        is_first_time = request.session.get('is_first_time')
                        next_question = request.GET.get("next", "False")
                        if is_first_time:
                            question_sno = str(1)
                            request.session['question_sno'] = question_sno
                            request.session['is_first_time'] = False
                            context["button_is_active"] = True
                        else:
                            if next_question == "True":
                                question_sno = request.session.get("question_sno")
                                request.session['question_sno'] = str(int(question_sno)+1)
                    question_sno = request.session.get("question_sno")
                    progress_bar_count = request.session.get('progress_bar_count', 60)
                    uni_action_item_next_obj = UnipegasoActionItemsNextQuestion.objects.filter(sno=question_sno)
                    if uni_action_item_next_obj.count() == 0:
                        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
                        logger.info(f"unipegaso: User visit Final page for : {custom_user_session_id}")
                        current_user_id = request.session.get("current_user_id")
                        stu_obj = StudentDetail.objects.filter(pk=current_user_id).filter()
                        # stu_obj = StudentDetail.objects.filter(session_id=custom_user_session_id).first()
                        if stu_obj:
                            stu_obj.assessment_status = "Completed"
                            stu_obj.save()
                            send_mail =  send_email(request, stu_obj.email, custom_user_session_id)
                            # update the google sheet file
                            update_google_sheet(request, stu_obj)
                            logger.info(f"unipegaso: User visited Final page for : {custom_user_session_id}")
                            return render(request, "unipegaso/finish-slide.html", context)
                    ai_next_obj = uni_action_item_next_obj.first()
                    context["button_is_active"] = False
                    if ai_next_obj.question_type == "Link":
                        context["video_link"] = ai_next_obj.unipegaso_next_videos.first().video_link
                        context["ai_next_obj"] = ai_next_obj
                        context["button_is_active"] = True
                    context["question"] = ai_next_obj
                    logger.info(f"unipegaso: user visited Next-slide-view page for : {custom_user_session_id}")
                    print(f"context : {context}")
                    return render(request, "unipegaso/slides-and-videos.html", context)
                else:
                    logger.info(f"unipegaso: user visit Next-slide-view page for : {custom_user_session_id}")
                    form_data = request.POST
                    question_sno = request.session.get("question_sno")
                    questions = UnipegasoActionItemsNextQuestion.objects.get(sno=question_sno)
                    answer = None
                    if question_sno == "4" or question_sno == "5" or question_sno == "7" or question_sno == "8" or question_sno == "9":
                        dict_data = dict(form_data)
                        ans_key = f"selector{questions.pk}"
                        answer=dict_data[ans_key]
                    else:
                        answer=form_data.get(f"selector{questions.pk}")
                        logger.info(f"unipegaso: Added the value in session for the generate certificate for question-sno-{question_sno}, Answer:- {answer}")
                    current_user_id = request.session.get("current_user_id")
                    stu_obj = StudentDetail.objects.get(pk=current_user_id)
                    UnipagesoStudentNextQuestionTracker.objects.get_or_create(
                        student_detail=stu_obj,
                        unipegaso_ai_next_question=questions, 
                        defaults={"answer": answer}
                    )
                    if question_sno == "2":
                        is_certificate_result = request.session.get('is_certificate_result', None)
                        if is_certificate_result is None:
                            qus = UnipegasoActionItemsNextQuestion.objects.get(sno=2)
                            nq_obj = UnipagesoStudentNextQuestionTracker.objects.filter(student_detail=stu_obj, unipegaso_ai_next_question=qus).first()
                            request.session['is_certificate_result'] = nq_obj.answer
                    logger.info(f"unipegaso: answer submited at Next-slide-view post page for : {custom_user_session_id}")
                    if(is_video_filter == "True"):
                        # if question_sno == 3:
                        context["button_is_active"] = True
                        opt_obj = questions.unipegaso_next_option.filter(option=answer).first()
                        video_link = opt_obj.unipegaso_option_video_link.first()
                        context["video_link"] = video_link.link
                        context["question"] = questions
                        context["filter_video_link"] = True
                        logger.info(f"unipegaso: user visited Next-slide-view page for : {custom_user_session_id}")
                        print(f"context 1: {context}")
                        return render(request, "unipegaso/slides-and-videos.html", context)
                    request.session['question_sno'] = str(int(question_sno)+1)
                    question_sno = int(question_sno)+1
                    uni_action_item_next_obj = UnipegasoActionItemsNextQuestion.objects.filter(sno=question_sno)
                    if uni_action_item_next_obj.count() == 0:
                        uni_type_bit = request.session.get('uni_type_bit', 1)
                        if uni_type_bit == 1:
                            return HttpResponseRedirect(reverse("finish_slide"))
                        elif uni_type_bit == 2:
                            return HttpResponseRedirect(reverse("unimercatorum_finish_slide"))
                        else:
                            return HttpResponseRedirect(reverse("utsanraffaele_finish_slide"))
                    ai_next_obj = uni_action_item_next_obj.first()
                    context["button_is_active"] = False
                    if ai_next_obj.question_type == "Link":
                        context["video_link"] = ai_next_obj.unipegaso_next_videos.first().video_link
                        context["button_is_active"] = True
                    context["question"] = ai_next_obj
                    logger.info(f"unipegaso: user visited Next-slide-view page for : {custom_user_session_id}")
                    print(f"context 2 : {context}")
                    return render(request, "unipegaso/slides-and-videos.html", context)
            except Exception as Error:
                if custom_user_session_id:
                    logger.error(f"Unipegaso: Error in pt_test_submit function for {Error} : {custom_user_session_id}")
                else:
                    logger.error(f"Unipegaso: Error in pt_test_submit function for {Error}")
                
                return JsonResponse({"error_msg": "Qualcosa è andato storto!"}, status=400)
        else:
            logger.error(f"Error: user  trying to submit pt answer and test_count:- {test_count} for : {custom_user_session_id}")
            return JsonResponse({"error_msg": "Qualcosa è andato storto!"}, status=400)
    else:
        if custom_user_session_id:
            logger.warning(f"uunipegaso: user is trying to submit Quiz-view with GET request for : {custom_user_session_id}")
        else:
            logger.warning("unipegaso: user is trying to submit Quiz-view with GET request")
        
        return JsonResponse({"error_msg": "Qualcosa è andato storto!"}, status=400)

class RegisterPageView(View):
    template_name = "unipegaso/register.html"

    def get(self, request):
        try:
            context = {}
            context['student_registration_form'] = StudentUniPegasoForm()
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"unipegaso: User visit register page by  : {custom_user_session_id}")
            api_response = requests.get("https://orienta.pegaso.multiversity.click/api/get/ecp-active-no-master")
            if api_response.status_code == 200:
                logger.info(f"unipegaso: API response {api_response.status_code} for : {custom_user_session_id}")
                # context["options"] = ApprovedCentreOption.objects.filter(option_type="UniPegaso").all()
                context["options"] = api_response.json()
            else:
                logger.error(f"unipegaso: Error in register-get view API response for : {custom_user_session_id}")
                context["options"] = {}
            logger.info(f"unipegaso: User visited register page by  : {custom_user_session_id}")
            return render(request, self.template_name, context)
        except Exception as error:
            logger.error(f' Error in registration get method{error} for: {custom_user_session_id}')
            return render(request, self.template_name)
    
    def post(self, request):
        try:
            context = {}
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"unipegaso: user visit to register-post : {custom_user_session_id}")
            stu_form = StudentUniPegasoForm(request.POST or None)
            if stu_form.is_valid():
                logger.info(f"unipegaso: user visit to register-post and form is valid : {custom_user_session_id}")
                student_detail = stu_form.save(commit=False)
                contracted_center = request.POST['are_you_taking_this_test_at_a_contracted_center']
                if contracted_center == "Yes":
                    contracted_center_other = request.POST['test_at_a_contracted_center_other']
                    student_detail.test_at_a_contracted_center_other = contracted_center_other
                else:
                    student_detail.are_you_taking_this_test_at_a_contracted_center = True
                student_detail.session_id = custom_user_session_id
                student_detail.assessment_status = "Started"
                logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
                clarity_token = self.request.session.get('clarity_token', '')
                student_detail.clarity_token = clarity_token
                student_detail.save()
                logger.info(f"unipegaso: Student created successfully for : {student_detail.email}")
                request.session["test_count"] = 1
                request.session["current_user_id"] = student_detail.pk
                request.session['uni_type_bit'] = 1
                return HttpResponseRedirect(reverse("unipegaso_index"))
            else:
                logger.warning(f"unipegaso: Invalid form student not created Error {stu_form.errors} for: {custom_user_session_id}")
                context['student_registration_form'] = stu_form
                return render(request, self.template_name, context)
        except Exception as error:
            logger.error(f' Error in registration submit method{error} for: {custom_user_session_id}')
            messages.error(request, "Qualcosa è andato storto. per favore riprova più tardi!")
            return HttpResponseRedirect(reverse("unipegaso_register"))

class FinishSlideView(View):
    template_name = "unipegaso/finish-slide.html"
    def get(self, request):
        try:
            context = {}
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"unipegaso: User visit Final page for : {custom_user_session_id}")
            current_user_id = request.session.get("current_user_id")
            stu_obj = StudentDetail.objects.filter(pk=current_user_id).first()
            if stu_obj:
                stu_obj.assessment_status = "Completed"
                stu_obj.save()
                send_mail =  send_email(request, stu_obj.email, custom_user_session_id)
                logger.info(f"unipegaso: Send email status -{send_mail} for : {stu_obj.email}")
                update_google_sheet(request, stu_obj)
                logger.info(f"unipegaso: User visited Final page for : {custom_user_session_id}")
                return render(request, self.template_name, context)
            logger.warning(f"unipegaso: Redirected to register page from Final-page : {custom_user_session_id}")
            return HttpResponseRedirect(reverse("unipegaso_register"))
        except Exception as error:
            logger.error(f'unipegaso: Error in next_part from finish slide get method{error} for: {custom_user_session_id}')
            return HttpResponseRedirect(reverse("unipegaso_register"))


def certificate_result_function(is_certificate_result):
    if is_certificate_result == "Realistic":
        link_and_text = {"Ingegneria delle infrastrutture e della mobilità sostenibile": "https://www.unimercatorum.it/corsi-di-laurea/ingegneria-delle-infrastrutture-per-una-mobilita-sostenibile", 
                    "Ingegneria gestionale": "https://www.unimercatorum.it/corsi-di-laurea/ingegneria-gestionale",
                    "Ingegneria informatica": "https://www.unimercatorum.it/corsi-di-laurea/ingegneria-informatica",
                    "Informatica per le aziende digitali": "https://www.unipegaso.it/lauree-triennali/informatica-per-le-aziende-digitali"}

    elif is_certificate_result == "Investigative":
        link_and_text = {"Gestione di impresa": "https://www.unimercatorum.it/corsi-di-laurea/gestione-di-impresa",
                        "Statistica e big data": "https://www.unimercatorum.it/corsi-di-laurea/statistica-e-big-data",
                        "Scienze giuridiche": "https://www.unimercatorum.it/corsi-di-laurea/scienze-giuridiche",
                        "Scienze e tecniche psicologiche": "https://www.unimercatorum.it/corsi-di-laurea/scienze-e-tecniche-psicologiche"}


    elif is_certificate_result == "Artistic":
        link_and_text = {"Lettere, sapere umanistico e formazione": "https://www.unipegaso.it/lauree-triennali/lettere-sapere-umanistico-e-formazione",
                        "Comunicazione e multimedialità": "https://www.unimercatorum.it/corsi-di-laurea/comunicazione-e-multimedialita",
                        "Moda e design industriale": "https://www.uniroma5.it/triennale/triennale-indirizzo-design.html"}
        
    elif is_certificate_result == "Social":
        link_and_text = {"Scienze politiche e relazioni internazionali": "https://www.unimercatorum.it/corsi-di-laurea/scienze-politiche-e-relazioni-internazionali",
                        "Lettere, sapere umanistico e formazione": "https://www.unipegaso.it/lauree-triennali/lettere-sapere-umanistico-e-formazione",
                        "Sociologia e innovazione": "https://www.unimercatorum.it/corsi-di-laurea/sociologia-e-innovazione",
                        "Scienze dell’educazione": "https://www.unipegaso.it/lauree-triennali/scienze-educazione-e-formazione"}

    elif is_certificate_result == "Enterprising":
        link_and_text = {"Economia aziendale": "https://www.unipegaso.it/lauree-triennali/economia-aziendale", 
                        "Gestione di impresa": "https://www.unimercatorum.it/corsi-di-laurea/gestione-di-impresa",
                        "Ingegneria gestionale": "https://www.unimercatorum.it/corsi-di-laurea/ingegneria-gestionale"}

    elif is_certificate_result == "Conventional":
        link_and_text = {"Economia aziendale": "https://www.unimercatorum.it/corsi-di-laurea/scienze-giuridiche", "Scienze giuridich": "https://www.unimercatorum.it/corsi-di-laurea/scienze-giuridiche",
                        "Ingegneria informatica": "https://www.unimercatorum.it/corsi-di-laurea/ingegneria-informatica"}
    else:
        link_and_text = {}
    return link_and_text

def render_to_pdf(request, certificate_logo,certificate_back, context_dict={}):
    name = context_dict['current_user_name']
    # ts store timestamp of current time
    curent_time = datetime.datetime.now()
    time_stamp = curent_time.timestamp()
    file_name = f"Certificate_test_{time_stamp}.pdf"
    page_width = 297
    page_height = 200
    page_size = (page_width * mm, page_height * mm)
    pdf = canvas.Canvas(file_name, pagesize=page_size)
    pdf.setTitle(f"Certifica - {name}")
    background = ImageReader(certificate_back)
    back_width = 297*mm
    back_height = 200*mm
    back_x = 0
    back_y = 0
    pdf.drawImage(background, back_x, back_y, back_width, back_height)
    logo = ImageReader(certificate_logo)
    logo_width = 240
    logo_height = 110
    x = (page_width * mm - logo_width) / 2
    y = page_height * mm - 15 - logo_height
    pdf.drawImage(logo, x, y, logo_width, logo_height, mask='auto')
    pdf.setFontSize(14)
    pdf.setFont("Helvetica-Bold",18)
    pdf.drawCentredString(page_width / 2 * mm, y - 30 , "certifica che")
    pdf.setFont("Helvetica-Bold",24)
    pdf.drawCentredString(page_width / 2 * mm, y - 70 , name )
    text = f"Ha completato il test di orientamento approfondendo le proprie inclinazione e competenze."
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(page_width / 2 * mm, y - 110 , text )
    text = f"Alla luce di questo, ecco alcuni consigli di specializzazione universitarie in linea con la personalità e gli"
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(page_width / 2 * mm, y - 145 , text )
    text = f"interessi emersi nell’assessment:"
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(page_width / 2 * mm, y - 162 , text )
    stu_obj = context_dict['stu_obj']
    answers = UnipagesoStudentNextQuestionTracker.objects.filter(unipegaso_ai_next_question__sno=9, student_detail=stu_obj)
    ans_dict = {}
    if answers.count() > 0:
        string_list = answers.first().answer
        list_from_string = ast.literal_eval(string_list)
        question = UnipegasoActionItemsNextQuestion.objects.filter(sno=9).first()
        for op_list in list_from_string:
            option_obj = UnipegasoActionItemsNextQuestionOption.objects.filter(option=op_list, unipegaso_next_question=question).first()
            link_obj = UnipegasoVideoOptionLink.objects.filter(unipegaso_option=option_obj)
            if link_obj.count():
                li_obj = link_obj.first()
                ans_dict[op_list] = li_obj.link
            else:
                ans_dict[op_list] = ""
    x = 221
    y = 225
    for key, value in ans_dict.items():
        pdf.setFont("Helvetica", 14)
        text = key
        text_width = pdf.stringWidth(text, "Helvetica", 14)
        pdf.drawString(page_width / 2 * mm - 150, y, text)
        pdf.setLineWidth(1)
        pdf.line(page_width / 2 * mm - 150, x, page_width / 2 * mm + text_width - 150, x)
        url_link = value
        pdf.linkURL(url=url_link, rect=(page_width / 2 * mm - 150, y, page_width / 2 * mm + text_width - 150, y), thickness=1, color=blue)
        y = y - 25
        x = y - 4
    is_certificate_result = request.session.get('is_certificate_result')
    link_and_text = certificate_result_function(is_certificate_result)
    for key, value in link_and_text.items():
        pdf.setFont("Helvetica", 14)
        text = key
        text_width = pdf.stringWidth(text, "Helvetica", 14)
        pdf.drawString(page_width / 2 * mm - 150, y, text)
        pdf.setLineWidth(1)
        pdf.line(page_width / 2 * mm - 150, x, page_width / 2 * mm + text_width - 150, x)
        url_link = value
        pdf.linkURL(url=url_link, rect=(page_width / 2 * mm - 150, y, page_width / 2 * mm + text_width - 150, y), thickness=10, color=blue)
        y = y - 25
        x = y - 4

    text = f"Questi consigli sono preziosi e ti aiutano ad approfondire le tue potenzialità. Cliccando su ciascuna area di specializzazione "
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(page_width / 2 * mm, y-15 , text )
    text = f"puoi approfondire i diversi piani e materie di studio più in linea con la tua personalità. Se invece vuoi confrontarti con un "
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(page_width / 2 * mm, y-30 , text )
    text = f"esperto per approfondire i corsi proposti, chiama il numero 800-185-095."
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(page_width / 2 * mm, y-45 , text )
    pdf.showPage()
    pdf.save()
    current_user_id = request.session.get("current_user_id")
    stu_obj = StudentDetail.objects.get(pk=current_user_id)
    stu_obj.certificate_link.save(basename(file_name), content=File(open(file_name, 'rb')))
    return file_name


def send_email(request, email, session_id):
    context_dict = {}
    current_user_id = request.session.get("current_user_id")
    uni_type_bit = request.session.get('uni_type_bit', 1)
    if uni_type_bit == 1:
        certificate_logo = "static/unipegaso/images/logo_certificate_unipegaso.png"
        certificate_back="static/unipegaso/images/Pegaso-certificato_back.jpg"
    elif uni_type_bit == 2:
        certificate_logo = "static/unipegaso/images/certi-mercatorum-logo.png" #certificate_uni_mercatorum.png
        certificate_back="static/unipegaso/images/Mercatorum-certificato_back.jpg"
    else:
        certificate_logo = "static/unipegaso/images/certi_raffaele-logo.png" #certificate_san_raffaele.png
        certificate_back="static/unipegaso/images/SanRaf-certificato_back.jpg"
    stu_obj = StudentDetail.objects.filter(pk=current_user_id).first()
    mapper_obj = UnipagesoStudentPTMapper.objects.filter(student_detail=stu_obj).first()
    context_dict['mapper_obj'] = mapper_obj
    context_dict['stu_obj'] = stu_obj
    context_dict["current_user_name"] = f"{stu_obj.first_name.upper()} {stu_obj.last_name.upper()}"
    context_dict["is_certificate_result"] = request.session.get('is_certificate_result')

    pdf_file = render_to_pdf(request, certificate_logo, certificate_back, context_dict)
    os.remove(os.path.join(pdf_file))
    template_name = "unipegaso/send_email.html"
    current_user_id = request.session.get("current_user_id")
    stu_obj = StudentDetail.objects.filter(pk=current_user_id).first()
    # mapper_obj = UnipagesoStudentPTMapper.objects.filter(student_detail=stu_obj).first()
    student_email = stu_obj.email
    if uni_type_bit == 1:
        logo_url = "https://myfuturelybucket-prod.s3.eu-south-1.amazonaws.com/logo.png"
        subject = "Ecco l’università giusta per te!"
    elif uni_type_bit == 2:
        logo_url = "https://myfuturelybucket-prod.s3.eu-south-1.amazonaws.com/certificate_uni_mercatorum.png"
        subject = "Ecco l’università giusta per te!"
    else:
        logo_url = "https://myfuturelybucket-prod.s3.eu-south-1.amazonaws.com/certificate_san_raffaele.png"
        subject = "Ecco l’università giusta per te!"
    
    answers = UnipagesoStudentNextQuestionTracker.objects.filter(unipegaso_ai_next_question__sno=9, student_detail=stu_obj)
    ans_dict = {}
    if answers.count() > 0:
        string_list = answers.first().answer
        list_from_string = ast.literal_eval(string_list)
        question = UnipegasoActionItemsNextQuestion.objects.filter(sno=9).first()
        for op_list in list_from_string:
            option_obj = UnipegasoActionItemsNextQuestionOption.objects.filter(option=op_list, unipegaso_next_question=question).first()
            link_obj = UnipegasoVideoOptionLink.objects.filter(unipegaso_option=option_obj)
            if link_obj.count():
                li_obj = link_obj.first()
                ans_dict[op_list] = li_obj.link
            else:
                ans_dict[op_list] = ""

    try:
        context = {
            "email": student_email,
            "domain": request.get_host(),
            "user": stu_obj.first_name,
            "protocol": 'https',
            "mapper_obj": mapper_obj,
            "logo_url": logo_url,
            "button_url": stu_obj.certificate_link.url,
            "is_certificate_result": request.session.get('is_certificate_result'),
            "ans_dict": ans_dict,
        }
        html_msg = get_template(template_name).render(context)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [student_email])
        msg.content_subtype = "html"
        msg.send()
        logger.info(f"unipegaso: E-Mail sent Successfully for : {student_email}")
        return True
    except Exception as ex:
        logger.error(f"unipegaso: Error in send-email-message function {ex} for : {email}")
        return False

def checkKey(dic, key):
    if key in dic.keys():
        return True
    else:
        return False
    
def create_certification(request, context):
    try:
        current_user_id = request.session.get("current_user_id")
        stu_obj = StudentDetail.objects.filter(pk=current_user_id).first()
        mapper_obj = UnipagesoStudentPTMapper.objects.filter(student_detail=stu_obj).first()
        answers = UnipagesoStudentNextQuestionTracker.objects.filter(unipegaso_ai_next_question__sno=9, student_detail=stu_obj)
        link_dict = {}
        if answers.count() > 0:
            stu_next_qtrak = answers.first()
            string_list = answers.first().answer
            list_from_string = ast.literal_eval(string_list)
            is_certificate_result = request.session.get('is_certificate_result')
            link_dict = certificate_result_function(is_certificate_result)
            for ans_val in list_from_string:
                result_response = checkKey(link_dict, ans_val)
                if result_response == False:
                    next_ques = stu_next_qtrak.unipegaso_ai_next_question
                    next_ques_option = next_ques.unipegaso_next_option.filter(option=ans_val).first()
                    vdo_link_obj = next_ques_option.unipegaso_option_video_link.first()
                    if vdo_link_obj:
                        link_dict[ans_val] = vdo_link_obj.link
                    else:
                        link_dict[ans_val] = "#"
        context['answers_list'] = link_dict
        context['mapper_obj'] = mapper_obj
        context['student_name'] = f"{stu_obj.first_name.upper()} {stu_obj.last_name.upper()}"
        return context
    except Exception as Error:
        logger.error(f"unipegaso: Error in create certification : {Error}")
        return context
    

class CertificateView(View):
    template_name = "unipegaso/unipegaso_certificate.html"
    def get(self, request):
        context = {}
        current_user_id = request.session.get("current_user_id")
        if current_user_id:
            context = create_certification(request, context)
            return render(self.request, self.template_name, context)
        return HttpResponseRedirect(reverse("unipegaso_register"))


class UniMercatorumView(View):
    template_name = 'unimercatorum/index.html'
    def get(self, request):
        request.session["lang"] = "it"
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        current_user_id = request.session.get("current_user_id", None)
        context = {}
        if current_user_id is not None:
            try:
                stu_obj = StudentDetail.objects.get(pk=current_user_id)
                logger.info(f"unimercatorum: user authorised to visit quiz-view(GET): {custom_user_session_id}")
                test_count = request.session.get('test_count', 1)
                is_page_refresh = request.session.get('is_page_refresh', False)
                if is_page_refresh:
                    request.session.flush()
                    logger.info(f"unimercatorum: refresh the page and flush the session")
                    return render(request, self.template_name, context)
                if test_count == 1:
                    pt_obj = UniPegasoActionItemsPTQuestion.objects.filter(unipegaso_test__type="PT") #[:2]
                    unipegaso_test = pt_obj[0].unipegaso_test
                    UnipagesoStudentPTMapper.objects.update_or_create(student_detail=stu_obj, defaults={"unipegaso_test": unipegaso_test})
                    context["questions"] = pt_obj
                    logger.info(f"unimercatorum: quiz page rendered(GET): {custom_user_session_id}")
                    request.session['is_page_refresh'] = True
                    return render(request, self.template_name, context)
                else:
                    test_count =  request.session.get('test_count', None)
                    current_user_id =  request.session.get('current_user_id', None)
                    logger.info(f"unimercatorum: user visited Next-slide-view page for : {custom_user_session_id}")
                    return render(request, self.template_name, context)
            except Exception as Err:
                try:
                    request.session.flush()
                except:
                    logger.error(f"unimercatorum: Error at index view to pop the elements for : {custom_user_session_id}")
                logger.info(f"unimercatorum: user visited Next-slide-view page for : {custom_user_session_id}")
                return render(request, self.template_name, context)
        else:
            try:
                request.session.flush()
            except:
                logger.error(f"unimercatorum: Error at index view to pop the elements for : {custom_user_session_id}")
            logger.info(f"unimercatorum: user visited Next-slide-view page for : {custom_user_session_id}")
            return render(request, self.template_name, context)
    
class UniMercatorumRegisterPageView(View):
    template_name = "unimercatorum/register.html"

    def get(self, request):
        try:
            context = {}
            context['student_registration_form'] = StudentUniPegasoForm()
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"unimercatorum: User visit register page by  : {custom_user_session_id}")
            # context["options"] = ApprovedCentreOption.objects.filter(option_type="Mercatorum").all()
            api_response = requests.get("https://orienta.mercatorum.multiversity.click/api/get/ecp-active-no-master")
            if api_response.status_code == 200:
                logger.info(f"unimercatorum: API response {api_response.status_code} for : {custom_user_session_id}")
                context["options"] = api_response.json()
            else:
                logger.error(f"unimercatorum: Error in register-get view API response for : {custom_user_session_id}")
                context["options"] = {}
            logger.info(f"unimercatorum: User visited register page by  : {custom_user_session_id}")
            return render(request, self.template_name, context)
        except Exception as error:
            logger.error(f' Error in registration get method{error} for: {custom_user_session_id}')
            return render(request, self.template_name)
    
    def post(self, request):
        try:
            context = {}
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"unimercatorum: user visit to register-post : {custom_user_session_id}")
            stu_form = StudentUniPegasoForm(request.POST)
            if stu_form.is_valid():
                logger.info(f"unimercatorum: user visit to register-post and form is valid : {custom_user_session_id}")
                student_detail = stu_form.save(commit=False)
                contracted_center = request.POST['are_you_taking_this_test_at_a_contracted_center']
                if contracted_center == "Yes":
                    contracted_center_other = request.POST['test_at_a_contracted_center_other']
                    student_detail.test_at_a_contracted_center_other = contracted_center_other
                else:
                    student_detail.are_you_taking_this_test_at_a_contracted_center = True
                student_detail.session_id = custom_user_session_id
                logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
                clarity_token = self.request.session.get('clarity_token', '')
                student_detail.clarity_token = clarity_token
                student_detail.assessment_status = "Started"
                student_detail.save()
                logger.info(f"unimercatorum: Student created successfully for : {student_detail.email}")
                request.session["test_count"] = 1
                request.session['uni_type_bit'] = 2
                request.session["current_user_id"] = student_detail.pk
                return HttpResponseRedirect(reverse("unimercatorum_index"))
            else:
                logger.warning(f"unimercatorum: Invalid form student not created Error {stu_form.errors} for: {custom_user_session_id}")
                context['student_registration_form'] = stu_form
                return render(request, self.template_name, context)
        except Exception as error:
            logger.error(f'unimercatorum: Error in registration submit method{error} for: {custom_user_session_id}')
            messages.error(request, "Qualcosa è andato storto. per favore riprova più tardi!")
            return HttpResponseRedirect(reverse("unimercatorum_register"))


def update_google_sheet(request, student_obj):
    try:
        current_user_id = request.session.get("current_user_id")
        uni_type_bit = request.session.get('uni_type_bit', 1)
        student_obj = StudentDetail.objects.get(pk=current_user_id)
        logger.info(f"unipegaso: updating data in google sheet for : {student_obj.email}")
        credentials = service_account.Credentials.from_service_account_file('credentials.json')
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = '1970XD0WLCADeJcRpPywxjCNXzi0af-Eb-NTRcUiLYO8'
        if uni_type_bit == 1:
            range_name = 'Lista Studenti UniPegaso!A1:L18'
        elif uni_type_bit == 2:
            range_name = 'Lista Studenti Mercatorum!A1:L18'
        else:
            range_name = 'Lista Studenti San Raffaele!A1:L18'
        student_date = student_obj.created_at.strftime("%d/%m/%Y")
        is_contracted_center =  student_obj.are_you_taking_this_test_at_a_contracted_center
        if is_contracted_center:
            contracted_center = "NO"
        else:
            contracted_center = "SI"
        is_certificate_result = request.session.get('is_certificate_result', 'Realistic')
        stu_next_ques_track_obj = UnipagesoStudentNextQuestionTracker.objects.filter(student_detail=student_obj)
        soft_stu_next_ques_track_obj = stu_next_ques_track_obj.filter(unipegaso_ai_next_question__sno=4).first()
        soft_list =  ast.literal_eval(soft_stu_next_ques_track_obj.answer)
        soft_str = ""
        for soft_val in soft_list:
            soft_str = f"{soft_str} {soft_val};"
        hard_stu_next_ques_track_obj = stu_next_ques_track_obj.filter(unipegaso_ai_next_question__sno=5).first()
        hard_list =  ast.literal_eval(hard_stu_next_ques_track_obj.answer)
        hard_str = ""
        for hard_val in hard_list:
            hard_str = f"{hard_str} {hard_val};"
        last_stu_next_ques_track_obj = stu_next_ques_track_obj.filter(unipegaso_ai_next_question__sno=9).first()
        last_list =  ast.literal_eval(last_stu_next_ques_track_obj.answer)
        last_str = ""
        for last_val in last_list:
            last_str = f"{last_str} {last_val};"
        list_from_string = ast.literal_eval(last_stu_next_ques_track_obj.answer)
        is_certificate_result = request.session.get('is_certificate_result')
        link_dict = certificate_result_function("Realistic")
        for ans_val in list_from_string:
            result_response = checkKey(link_dict, ans_val)
            if result_response == False:
                next_ques = last_stu_next_ques_track_obj.unipegaso_ai_next_question
                next_ques_option = next_ques.unipegaso_next_option.filter(option=ans_val).first()
                vdo_link_obj = next_ques_option.unipegaso_option_video_link.first()
                try:
                    link_dict[ans_val] = vdo_link_obj.link
                except:
                    link_dict[ans_val] = "#"
        final_str = ""
        for k, v in link_dict.items():
            final_str = f"{final_str} {k} ({v}); "
        final_str=final_str[:-2]
        values = [
            [student_obj.email,
            student_obj.first_name,
            student_obj.last_name,
            student_date,
            student_obj.phone_number,
            contracted_center,
            student_obj.assessment_status,
            student_obj.test_at_a_contracted_center_other,
            student_obj.year_of_enrollment,
            student_obj.certificate_link.url,
            is_certificate_result,
            soft_str,
            hard_str,
            last_str,
            final_str,
            ]
        ]
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        logger.info(f"unipegaso: Google sheet updated successfully, status - {result} for : {student_obj.email}")
    except Exception as Error:
        logger.error(f"unipegaso: Error in google sheet function - {Error} : {student_obj.email}")

class UniMercatorumFinishSlideView(View):
    template_name = "unipegaso/finish-slide.html"
    def get(self, request):
        try:
            context = {}
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"unipegaso: User visit Final page for : {custom_user_session_id}")
            current_user_id = request.session.get("current_user_id")
            stu_obj = StudentDetail.objects.filter(pk=current_user_id).first()
            if stu_obj:
                stu_obj.assessment_status = "Completed"
                stu_obj.save()
                logger.info(f"updated the assessment_status for : {stu_obj.email}")
                send_mail =  send_email(request, stu_obj.email, custom_user_session_id)
                logger.info(f"unipegaso: Send email status -: {send_mail} for : {stu_obj.email}")
                update_google_sheet(request, stu_obj)
                logger.info(f"unipegaso: User visited Final page for : {custom_user_session_id}")
                return render(request, self.template_name, context)
            logger.warning(f"unipegaso: Redirected to register page from Final-page : {custom_user_session_id}")
            return HttpResponseRedirect(reverse("unipegaso_register"))
        except Exception as error:
            logger.error(f'unipegaso: Error in next_part from finish slide get method{error} for: {custom_user_session_id}')
            return HttpResponseRedirect(reverse("unipegaso_register"))

class UniMercatorumCertificateView(View):
    template_name = "unimercatorum/certificate.html"
    def get(self, request):
        context = {}
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        current_user_id = request.session.get("current_user_id")
        logger.info(f"unipegaso: User-{current_user_id} visit Final page for : {custom_user_session_id}")
        if current_user_id:
            context = create_certification(request, context)
            logger.info(f"unipegaso: render certificate html for user-{current_user_id} : {custom_user_session_id}")
            return render(self.request, self.template_name, context)
        return HttpResponseRedirect(reverse("unimercatorum_register"))



class UTSanRaffaeleView(View):
    template_name = 'utsanraffaele/index.html'
    def get(self, request):
        request.session["lang"] = "it"
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        current_user_id = request.session.get("current_user_id", None)
        logger.info(f"unipegaso: User-{current_user_id} visit Final page for : {custom_user_session_id}")
        context = {}
        if current_user_id is not None:
            try:
                stu_obj = StudentDetail.objects.get(pk=current_user_id)
                logger.info(f"utsanraffaele: user authorised to visit quiz-view(GET): {custom_user_session_id}")
                test_count = request.session.get('test_count', 1)
                is_page_refresh = request.session.get('is_page_refresh', False)
                if is_page_refresh:
                    request.session.flush()
                    logger.info(f"Utsanraffaele: refresh the page and flush the session")
                    return render(request, self.template_name, context)
                if test_count == 1:
                    pt_obj = UniPegasoActionItemsPTQuestion.objects.filter(unipegaso_test__type="PT")
                    unipegaso_test = pt_obj[0].unipegaso_test
                    UnipagesoStudentPTMapper.objects.update_or_create(student_detail=stu_obj, defaults={"unipegaso_test": unipegaso_test})
                    context["questions"] = pt_obj
                    logger.info(f"utsanraffaele: quiz page rendered(GET): {custom_user_session_id}")
                    request.session['is_page_refresh'] = True
                    return render(request, self.template_name, context)
                else:
                    test_count =  request.session.get('test_count', None)
                    current_user_id =  request.session.get('current_user_id', None)
                    logger.info(f"utsanraffaele: user visited Next-slide-view page for : {custom_user_session_id}")
                    return render(request, self.template_name, context)
            except Exception as Err:
                try:
                    print(Err)
                    request.session.flush()
                    logger.info(f"Utsanraffaele: flush the session!!")
                except:
                    logger.error(f"utsanraffaele: Error at index view to pop the elements for : {custom_user_session_id}")
                logger.info(f"utsanraffaele: user visited Next-slide-view page for : {custom_user_session_id}")
                return render(request, self.template_name, context)
        else:
            try:
                request.session.flush()
                logger.info(f"Utsanraffaele: flush the session!!")
            except:
                logger.error(f"utsanraffaele: Error at index view to pop the elements for : {custom_user_session_id}")
            logger.info(f"utsanraffaele: user visited Next-slide-view page for : {custom_user_session_id}")
            return render(request, self.template_name, context)

class UTSanRaffaeleRegisterPageView(View):
    template_name = "utsanraffaele/register.html"

    def get(self, request):
        try:
            context = {}
            context['student_registration_form'] = StudentUniPegasoForm()
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"utsanraffaele: User visit register page by  : {custom_user_session_id}")
            context["options"] = ApprovedCentreOption.objects.all()
            logger.info(f"utsanraffaele: User visited register page by  : {custom_user_session_id}")
            return render(request, self.template_name, context)
        except Exception as error:
            logger.error(f' Error in registration get method{error} for: {custom_user_session_id}')
        return render(request, self.template_name)
    
    def post(self, request):
        try:
            context = {}
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"utsanraffaele: user visit to register-post : {custom_user_session_id}")
            stu_form = StudentUniPegasoForm(request.POST or None)
            if stu_form.is_valid():
                logger.info(f"utsanraffaele: user visit to register-post and form is valid : {custom_user_session_id}")
                student_detail = stu_form.save(commit=False)
                student_detail.session_id = custom_user_session_id
                logger.info(f"Clarity token collected from session for : {custom_user_session_id}")
                clarity_token = self.request.session.get('clarity_token', '')
                student_detail.clarity_token = clarity_token

                student_detail.assessment_status = "Started"
                student_detail.save()
                logger.info(f"utsanraffaele: Student created successfully for : {student_detail.email}")
                request.session["test_count"] = 1
                request.session['uni_type_bit'] = 3
                request.session["current_user_id"] = student_detail.pk
                return HttpResponseRedirect(reverse("utsanraffaele_index"))
            else:
                logger.warning(f"utsanraffaele: Invalid form student not created Error {stu_form.errors} for: {custom_user_session_id}")
                context['student_registration_form'] = stu_form
                return render(request, self.template_name, context)
        except Exception as error:
            logger.error(f'utsanraffaele: Error in registration submit method{error} for: {custom_user_session_id}')
            messages.error(request, "Qualcosa è andato storto. per favore riprova più tardi!")
            return HttpResponseRedirect(reverse("utsanraffaele_register"))

class UTSanRaffaeleFinishSlideView(View):
    template_name = "unipegaso/finish-slide.html"

    def get(self, request):
        try:
            context = {}
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"unipegaso: User visit Final page for : {custom_user_session_id}")
            current_user_id = request.session.get("current_user_id")
            stu_obj = StudentDetail.objects.filter(pk=current_user_id).first()
            if stu_obj:
                stu_obj.assessment_status = "Completed"
                stu_obj.save()
                send_mail =  send_email(request, stu_obj.email, custom_user_session_id)
                logger.info(f"unipegaso: Send email status -{send_mail} for : {stu_obj.email}")
                update_google_sheet(request, stu_obj)
                logger.info(f"unipegaso: render html page Final page for : {custom_user_session_id}")
                return render(request, self.template_name, context)
            logger.warning(f"unipegaso: Redirected to register page from Final-page : {custom_user_session_id}")
            return HttpResponseRedirect(reverse("unipegaso_register"))
        except Exception as error:
            logger.error(f'unipegaso: Error in next_part from finish slide get method{error} for: {custom_user_session_id}')
            return HttpResponseRedirect(reverse("unipegaso_register"))

class UTSanRaffaeleCertificateView(View):
    template_name = "utsanraffaele/certificate.html"
    def get(self, request):
        context = {}
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        current_user_id = request.session.get("current_user_id")
        logger.info(f"utsanraffaele: User visit Final page for : {custom_user_session_id}")
        if current_user_id:
            context = create_certification(request, context)
            logger.info(f"utsanraffaele: render html page for : {custom_user_session_id}")
            return render(self.request, self.template_name, context)
        logger.warning(f"utsanraffaele: User redirected to register page for : {custom_user_session_id}")
        return HttpResponseRedirect(reverse("unipegaso_register"))