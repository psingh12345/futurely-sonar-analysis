import os, ast, logging
from .models import *
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
from lib.custom_logging import CustomLoggerAdapter
from google.oauth2 import service_account
from googleapiclient.discovery import build
from random import randrange

adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

def certificate_result_function(is_certificate_result):
    if is_certificate_result == "Realistic":
        link_and_text = {"Sviluppo software": "#", 
                    "Tecnico industria agroalimentare": "#",
                    "Informatica ed elettronica": "#",}

    elif is_certificate_result == "Social":
        link_and_text = {"Management e comunicazione": "#",
                        "Marketing e vendite": "#",
                        "Risorse umane": "#",}


    elif is_certificate_result == "Artistic":
        link_and_text = {"Management e comunicazione": "#",
                        "Grafica e multimediale": "#",
                        "Disegno meccanico e stampa 3D": "#"}
        
    elif is_certificate_result == "Investigative":
        link_and_text = {"Cybersecurity": "#",
                        "Big Data": "#",
                        "Sostenibilità e ambiente": "#",}

    elif is_certificate_result == "Enterprising":
        link_and_text = {"Moda, tessile e maglieria": "#", 
                        "Marketing e vendite": "#",
                        "Amministrazione, finanza e controllo": "#"}

    elif is_certificate_result == "Conventional":
        link_and_text = {"Amministrazione e paghe": "#", 
                         "Amministrazione, finanza e controllo": "#",
                        "Big Data": "#"}
    else:
        link_and_text = {}
    return link_and_text


def render_to_pdf(request, certificate_logo, certificate_back, context_dict={}):
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
    # background = ImageReader(certificate_back)
    back_width = 297*mm
    back_height = 200*mm
    back_x = 0
    back_y = 0
    # pdf.drawImage(background, back_x, back_y, back_width, back_height)
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
    answers = IFOAStudentQuestionTracker.objects.filter(ifoa_question__sno=15, ifoa_student_detail=stu_obj)
    ans_dict = {}
    if answers.count() > 0:
        string_list = answers.first().answer
        list_from_string = ast.literal_eval(string_list)
        question = IFOAQuestion.objects.filter(sno=15).first()
        for op_list in list_from_string:
            option_obj = IFOAQuestionMCQOption.objects.filter(option=op_list, ifoa_question=question).first()
            link_obj = IFOAQuestionOptionLink.objects.filter(ifoa_question_option=option_obj)
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
    stu_obj = IFOAStudentDetail.objects.get(pk=current_user_id)
    stu_obj.certificate_link.save(basename(file_name), content=File(open(file_name, 'rb')))
    return file_name

def send_email(request, email, session_id):
    context_dict = {}
    current_user_id = request.session.get("current_user_id")
    certificate_logo = "static/unipegaso/images/logoIFOA.png"
    certificate_back="static/unipegaso/images/IFOA-certificate-back.png"
    stu_obj = IFOAStudentDetail.objects.filter(pk=current_user_id).first()
    mapper_obj = IFOAStudentPTMapper.objects.filter(ifoa_student_detail=stu_obj).first()
    context_dict['mapper_obj'] = mapper_obj
    context_dict['stu_obj'] = stu_obj
    context_dict["current_user_name"] = f"{stu_obj.first_name.upper()} {stu_obj.last_name.upper()}"
    context_dict["is_certificate_result"] = request.session.get('is_certificate_result')
    # pdf_file = render_to_pdf(request, certificate_logo, certificate_back, context_dict)
    # os.remove(os.path.join(pdf_file))
    template_name = "ifoa/send_email.html"
    student_email = stu_obj.email
    logo_url = "https://myfuturelybucket-prod.s3.eu-south-1.amazonaws.com/logoIFOA.jpg"
    # subject = "Scopri i risultati del percorso di orientamento!"
    subject = "Ifoa: ecco i risultati del percorso!"
    
    answers = IFOAStudentQuestionTracker.objects.filter(ifoa_question__sno=15, ifoa_student_detail=stu_obj)
    link_dict = {}
    if answers.count() > 0:
        string_list = answers.first().answer
        list_from_string = ast.literal_eval(string_list)
        question = IFOAQuestion.objects.filter(sno=15).first()
        link_dict = certificate_result_function(request.session.get('is_certificate_result'))
        for op_list in list_from_string:
            result_response = checkKey(link_dict, op_list)
            if result_response == False:
                option_obj = IFOAQuestionMCQOption.objects.filter(option=op_list, ifoa_question=question).first()
                link_obj = IFOAQuestionOptionLink.objects.filter(ifoa_question_option=option_obj)
                if link_obj.count():
                    li_obj = link_obj.first()
                    link_dict[op_list] = li_obj.link
                else:
                    link_dict[op_list] = ""

    try:
        stu_obj = IFOAStudentDetail.objects.get(pk=current_user_id)
        context = {
            "email": student_email,
            "domain": request.get_host(),
            "user": stu_obj.first_name,
            "protocol": 'https',
            "mapper_obj": mapper_obj,
            "logo_url": logo_url,
            "is_certificate_result": request.session.get('is_certificate_result'),
            "ans_dict": list(link_dict.items())[:4],
        }
        html_msg = get_template(template_name).render(context)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [student_email])
        msg.content_subtype = "html"
        msg.send()
        logger.info(f"IFOA: E-Mail sent Successfully for : {student_email}")
        return True
    except Exception as ex:
        logger.error(f"IFOA: Error in send-email-message function {ex} for : {email}")
        return False

def checkKey(dic, key):
    if key in dic.keys():
        return True
    else:
        return False

def create_certification(request, context):
    try:
        current_user_id = request.session.get("current_user_id")
        stu_obj = IFOAStudentDetail.objects.filter(pk=current_user_id).first()
        logger.info(f"IFOA: create_certification for : {stu_obj.email}")
        mapper_obj = IFOAStudentPTMapper.objects.filter(ifoa_student_detail=stu_obj).first()
        answers = IFOAStudentQuestionTracker.objects.filter(ifoa_question__sno=15, ifoa_student_detail=stu_obj)
        link_dict = {}
        if answers.count() > 0:
            logger.info(f"IFOA: create_certification answers for : {stu_obj.email}")
            stu_next_qtrak = answers.first()
            string_list = answers.first().answer
            list_from_string = ast.literal_eval(string_list)
            is_certificate_result = request.session.get('is_certificate_result')
            link_dict = certificate_result_function(is_certificate_result)
            for ans_val in list_from_string:
                result_response = checkKey(link_dict, ans_val)
                if result_response == False:
                    next_ques = stu_next_qtrak.ifoa_question
                    next_ques_option = next_ques.ifoa_question_option.filter(option=ans_val).first()

                    vdo_link_obj = next_ques_option.ifoa_question_option_link.first()
                    if vdo_link_obj:
                        link_dict[ans_val] = vdo_link_obj.video_link
                    else:
                        link_dict[ans_val] = "#"
        context['answers_list'] = list(link_dict.items())[:4]
        context['mapper_obj'] = mapper_obj
        context['student_name'] = f"{stu_obj.first_name.upper()} {stu_obj.last_name.upper()}"
        logger.info(f"IFOA: create_certification return context for : {stu_obj.email}")
        return context
    except Exception as Error:
        logger.error(f"IFOA: Error in create_certification : {Error}")
        return context

def update_google_sheet(request, student_obj, is_from_register=False):
    try:
        current_user_id = request.session.get("current_user_id")
        student_obj = IFOAStudentDetail.objects.get(pk=current_user_id)
        logger.info(f"IFOA: updating data in google sheet for : {student_obj.email}")
        credentials = service_account.Credentials.from_service_account_file('credentials.json')
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet_id = '1Y5SNYWvWrkV4RauabfOcRGLRdExUd5-hhkCye2gdqUU'
        if is_from_register:
            range_name = "Test registrati!A1:L18"
        else:
            range_name = 'Test completati!A1:L18'
        student_date = student_obj.created_at.strftime("%d/%m/%Y")

        try:
            is_certificate_result = request.session.get('is_certificate_result', 'Realistic')
            stu_next_ques_track_obj = IFOAStudentQuestionTracker.objects.filter(ifoa_student_detail=student_obj)

            soft_stu_next_ques_track_obj = stu_next_ques_track_obj.filter(ifoa_question__sno=11).first()
            soft_list =  ast.literal_eval(soft_stu_next_ques_track_obj.answer)
            soft_str = ""
            for soft_val in soft_list:
                soft_str = f"{soft_str} {soft_val};"
            hard_stu_next_ques_track_obj = stu_next_ques_track_obj.filter(ifoa_question__sno=13).first()
            hard_list =  ast.literal_eval(hard_stu_next_ques_track_obj.answer)
            hard_str = ""
            for hard_val in hard_list:
                hard_str = f"{hard_str} {hard_val};"
            last_stu_next_ques_track_obj = stu_next_ques_track_obj.filter(ifoa_question__sno=15).first()
            last_list =  ast.literal_eval(last_stu_next_ques_track_obj.answer)
            last_str = ""
            for last_val in last_list:
                last_str = f"{last_str} {last_val};"
            list_from_string = ast.literal_eval(last_stu_next_ques_track_obj.answer)
            is_certificate_result = request.session.get('is_certificate_result', '')
            link_dict = certificate_result_function(is_certificate_result)
            for ans_val in list_from_string:
                result_response = checkKey(link_dict, ans_val)
                if result_response == False:
                    next_ques = last_stu_next_ques_track_obj.ifoa_question
                    next_ques_option = next_ques.ifoa_question_option.filter(option=ans_val).first()
                    vdo_link_obj = next_ques_option.ifoa_question_option_link.first()
                    if vdo_link_obj:
                        link_dict[ans_val] = vdo_link_obj.video_link
                    else:
                        link_dict[ans_val] = "#"
            final_str = ""
            for value in list(link_dict.items())[:4]:
                final_str = f"{final_str} {value[0]};"
            test_result = student_obj.ifoa_student_detail.first().test_result
        except:
            is_certificate_result = request.session.get('is_certificate_result', '')
            soft_str = ""
            hard_str = ""
            last_str = ""
            final_str = ""
            test_result = ""
            pass
        values = [
            [student_obj.email,
            student_obj.first_name,
            student_obj.last_name,
            student_obj.gender,
            student_obj.date_of_birth.strftime("%d/%m/%Y"),
            student_obj.birth_place,
            student_obj.tax_id_code,
            student_obj.how_did_you_know_us,
            student_obj.phone_number,
            student_obj.assessment_status,
            student_date,
            student_obj.finalità_di_marketing,
            test_result,
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
        logger.info(f"IFOA: Google sheet updated successfully, status - {result} for : {student_obj.email}")
    except Exception as Error:
        logger.error(f"IFOA: Error in google sheet function - {Error} : {student_obj.email}")

def send_otp_mail(student_email, request):
    try:
        subject = "Verifica la tua identità"
        template_name = "ifoa/ifoa_otp_email.html"
        otp = randrange(1000000,9999999)
        request.session['otp'] = otp
        context = {
            'otp': otp
        }
        html_msg = get_template(template_name).render(context)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [student_email])
        msg.content_subtype = "html"
        response = msg.send()
        # print("Send email response ==> ", response)
        logger.info(f"IFOA: OTP sent for {otp} : {student_email}")
        return response
    except Exception as Error:
        logger.error(f"IFOA: Error in send_otp_mail : {Error}")
        return False