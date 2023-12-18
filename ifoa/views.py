from django.shortcuts import render
from django.views.generic import View
from lib.custom_logging import CustomLoggerAdapter
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
import logging
from .forms import IFOAStudentDetailForm
from .models import *
from .helper import send_email, create_certification, update_google_sheet, send_otp_mail
from django.db.models import Q
import ipdb

adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

class IFOAIndexView(View):
    template_name = 'ifoa/index.html'
    def get(self, request, *args, **kwargs):
        try:
            context = {}
            request.session["lang"] = "it"
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            current_user_id = request.session.get("current_user_id", None)
            if current_user_id is not None:
                stu_obj = IFOAStudentDetail.objects.get(pk=current_user_id)
                context['stu_obj'] = stu_obj
                logger.info(f'IFOA: user authorised to visit ifoa index page : {custom_user_session_id}')
                test_count = request.session.get('test_count', 1)
                is_page_refresh = request.session.get('is_page_refresh', False)
                if is_page_refresh:
                    request.session.flush()
                    request.session["lang"] = "it"
                    logger.info(f"IFOA: refresh the page and flush the session")
                    return render(request, self.template_name, context)
                
                if test_count == 1:
                    logger.info(f"IFOA: user is on the first page")
                    pt_obj = IFOAPTQuestion.objects.filter(ifoa_test__type="IFOA")
                    ifoa_test = pt_obj[0].ifoa_test
                    IFOAStudentPTMapper.objects.update_or_create(ifoa_student_detail=stu_obj, defaults={'ifoa_test': ifoa_test})
                    context["questions"] = pt_obj
                    logger.info(f"IFOA: quiz page rendered(GET): {custom_user_session_id}")
                    request.session['is_page_refresh'] = True
                    return render(request, self.template_name, context)
                else:
                    request.session.flush()
                    request.session["lang"] = "it"
                    logger.info(f"IFOA: user visited Next-slide-view page for : {custom_user_session_id}")
                    return render(request, self.template_name, context)
            else:
                logger.info(f'IFOA: user visit index page : {custom_user_session_id}')
                return render(request, self.template_name, context)
        except Exception as e:
            request.session.flush()
            request.session["lang"] = "it"
            logger.error(f"IFOA: Error in index page : {e}")
            return render(request, self.template_name, context)


class IFOARegistrationView(View):
    template_name = 'ifoa/register.html'
    def get(self, request, *args, **kwargs):
        context = {}
        request.session["lang"] = "it"
        request.session['is_otp_verified'] = False
        context['student_registration_form'] = IFOAStudentDetailForm()
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        logger.info(f'IFOA: user visit registration page : {custom_user_session_id}')
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        context = {}
        student_registration_form = IFOAStudentDetailForm(request.POST)
        is_otp_verified = request.session.get('is_otp_verified', False) 
        if student_registration_form.is_valid() and is_otp_verified:
            student_detail = student_registration_form.save(commit=False)
            student_detail.assessment_status = "Started"
            student_detail.session_id = custom_user_session_id
            clarity_token = self.request.session.get('clarity_token', '')
            student_detail.clarity_token = clarity_token
            student_detail.is_otp_verified = True
            finalità_di_marketing = request.POST.get('finalità_di_marketing', 'No')
            informativa_sulla_privacy = request.POST.get('informativa_sulla_privacy', 'No')

            if finalità_di_marketing == "on":
                student_detail.finalità_di_marketing = "Yes"
            else:
                student_detail.finalità_di_marketing = "No"

            if informativa_sulla_privacy == "on":
                student_detail.informativa_sulla_privacy = "Yes"
            student_detail.save()
            logger.info(f"IFOA: Student created successfully for : {student_detail.email}")
            request.session["test_count"] = 1
            request.session["current_user_id"] = student_detail.pk
            request.session['uni_type_bit'] = 1
            logger.info(f'IFOA: google sheet function called for : {student_detail.email}')
            try:
                update_google_sheet(request, student_detail, is_from_register=True)
            except Exception as google_sheet_error:
                logger.error(f'IFOA: google sheet function error - {google_sheet_error} for : {student_detail.email}')
            return HttpResponseRedirect(reverse("ifoa_index"))
        
        context['student_registration_form'] = student_registration_form
        logger.warning(f'IFOA: form data invalid  : {custom_user_session_id}')
        return render(request, self.template_name, context)

class PTQuestionSubmitView(View):
    def post(self, request, *args, **kwargs):
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        context = {}
        if request.method == "POST":
            test_count = request.session.get('test_count', 1)
            current_user_id = request.session.get("current_user_id")
            if test_count == 1:
                try:
                    form_data = request.POST
                    form_qus_id = form_data.get('question', "")
                    answer = form_data.get('answer', "")
                    is_last_question = form_data.get('is_last_question', "")
                    if form_qus_id == "" and answer == "" and is_last_question == "":
                        logger.error(f'IFOA: user submitted empty form for : {custom_user_session_id}')
                        return JsonResponse({"error_msg": "Accetta prima di procedere."}, status=200)
                    uni_type_bit = request.session.get('uni_type_bit', 1)
                    question_obj = IFOAPTQuestion.objects.get(pk=form_qus_id)
                    ifoa_test = question_obj.ifoa_test
                    stu_obj = IFOAStudentDetail.objects.get(pk=current_user_id)
                    stu_mapper = IFOAStudentPTMapper.objects.filter(ifoa_student_detail=stu_obj, ifoa_test=ifoa_test).first()
                    create_ans_obj = IFOAStudentPTAnswer.objects.create(ifoa_student_mapper=stu_mapper, ifoa_question=question_obj, answer=answer, is_completed=True)
                    stu_obj.assessment_status = "Pending"
                    logger.info(f'IFOA: updated test status for : {stu_obj.email}')
                    stu_obj.save()
                    logger.info(f"IFOA: Saved the student object : {stu_obj.email}")
                    if create_ans_obj:
                        if is_last_question == "Yes":
                            logger.info(f"IFOA: user redirected to test result page from quiz post page for : {custom_user_session_id}")
                            request.session['test_count'] = 2
                            request.session['progress_bar_count'] = 60
                            request.session['total_next_question_count'] = 9
                            my_score = stu_mapper.calculate_my_score
                            sorted_my_score = sorted(my_score.items(), key=lambda x: x[1],reverse=True)
                            stu_mapper.test_result = sorted_my_score[0][0][1]
                            stu_mapper.is_completed = True
                            logger.info(f'IFOA: test successfully completed by student-id-{stu_obj.id}: {stu_obj.email}')
                            stu_mapper.save()
                            context['my_score'] = my_score
                            context['sorted_my_score'] = sorted_my_score
                            request.session['is_first_time'] = True
                            context['stu_mapper'] = stu_mapper
                            request.session['question_sno'] = 1
                            logger.info(f"IFOA: user visited TestResult-view page for : {custom_user_session_id}")
                            return render(request, "ifoa/pt_result.html", context)
                        else:
                            return JsonResponse({"success": "Yes"})
                    else:
                        return JsonResponse({"error": "Qualcosa è andato storto."})
                    
                except Exception as e:
                    logger.error(f"IFOA: Error in submitting the question : {e}")
                    return HttpResponse("error")
            elif test_count == 2 or test_count == 3:
                try:
                    logger.info(f"IFOA: user redirected to next slide from quiz post page for : {custom_user_session_id}")
                    is_first_time = request.session.get('is_first_time')
                    question_sno = request.session.get('question_sno', None)
                    if question_sno:
                        question_id = request.POST.get('question_id', None)
                        if question_id:
                            question_obj = IFOAQuestion.objects.get(id=question_id)
                        else:
                            question_obj = IFOAQuestion.objects.filter(sno=question_sno).first()
                        question_option_linked = None
                        if question_obj:
                            if is_first_time:
                                context['question'] = question_obj
                                request.session['is_first_time'] = False
                                return render(request, 'ifoa/pt_question_slide.html', context)
                            else:
                                answer = None
                                question_option_obj = None
                                question_option_link_obj = None
                                stu_obj = IFOAStudentDetail.objects.get(pk=current_user_id)
                                it_was_filtred_video = request.session.get('it_was_filtred_video', False)
                                if it_was_filtred_video is False:
                                    form_data = request.POST
                                    if question_obj.question_type == "MCQ":
                                        multi_selected_ques_sno = [9, 10, 11, 13, 15]
                                        if question_sno in multi_selected_ques_sno:
                                            dict_data = dict(form_data)
                                            ans_key = f"selector{question_obj.pk}"
                                            answer=dict_data[ans_key]
                                            logger.info(f"IFOA: Added the value in list for multiple selection for question-sno-{question_sno} : {stu_obj.email}")
                                        else:
                                            answer=form_data.get(f"selector{question_obj.pk}")
                                            question_option_obj = question_obj.ifoa_question_option.filter(option=answer).first()
                                            if question_option_obj:
                                                question_option_link_obj = question_option_obj.ifoa_question_option_link
                                        IFOAStudentQuestionTracker.objects.get_or_create(
                                            ifoa_student_detail=stu_obj,
                                            ifoa_question=question_obj, 
                                            defaults={"answer": answer}
                                        )
                                        if question_sno == 3:
                                            is_certificate_result = request.session.get('is_certificate_result', None)
                                            if is_certificate_result is None:
                                                request.session['is_certificate_result'] = answer
                                                logger.info(f"IFOA: Added the value in session for the generate certificate for question-sno-{question_sno}, Answer:- {answer}")
                                        question_option_linked = IFOAQuestionMCQOptionLinkedQuestion.objects.filter(ifoa_question_mcq_option=question_option_obj)
                                        if question_option_linked.count() > 0:
                                            request.session['option_linked_question'] = question_option_obj.pk
                                    elif question_obj.question_type == "Link" or question_obj.question_type == 'Text':
                                        IFOAStudentQuestionTracker.objects.get_or_create(
                                            ifoa_student_detail=stu_obj,
                                            ifoa_question=question_obj, 
                                            defaults={"answer": 'Done!'}
                                        )
                                    else:
                                        return JsonResponse({"error": "Qualcosa è andato storto."})
                                    
                                    if question_option_link_obj:
                                        try:
                                            context["video_link"] = question_option_link_obj.first().video_link
                                            context['question'] = question_obj
                                            context['filter_video_link'] = True
                                            request.session['it_was_filtred_video'] = True
                                            return render(request, 'ifoa/pt_question_slide.html', context)
                                        except:
                                            pass
                                    
                                request.session['it_was_filtred_video'] = False
                                question_sno = int(question_sno) + 1
                                request.session['question_sno'] = question_sno
                                if question_option_linked:
                                    if question_option_linked.count() > 0:
                                        question_obj = question_option_linked.filter(ifoa_question__sno=question_sno).first()
                                        context['question'] = question_obj.ifoa_question
                                        return render(request, 'ifoa/pt_question_slide.html', context)
                                else:
                                    try:
                                        option_linked_question = request.session.get('option_linked_question', None)
                                        if option_linked_question:
                                            question_option_linked = IFOAQuestionMCQOptionLinkedQuestion.objects.filter(ifoa_question_mcq_option=option_linked_question)
                                            question_obj = question_option_linked.filter(ifoa_question__sno=question_sno).first()
                                            context['question'] = question_obj.ifoa_question
                                            return render(request, 'ifoa/pt_question_slide.html', context)
                                    except:
                                        pass
                                    
                                question_obj = IFOAQuestion.objects.filter(sno=question_sno)
                                if question_obj.count() == 0:
                                    logger.info(f"IFOA: User visit Final page for : {custom_user_session_id}")
                                    return HttpResponseRedirect(reverse("ifoa_final_slide"))
                                else:
                                    question_obj = question_obj.first()
                                    context['question'] = question_obj
                                    return render(request, 'ifoa/pt_question_slide.html', context)
                    
                except Exception as e:
                    logger.error(f"IFOA: Error in submitting the question : {e}")
                    return JsonResponse({"error_msg": "Qualcosa è andato storto."}, status=400)
        else:
            logger.error(f"IFOA: Error in submitting the question : {custom_user_session_id}")
        return JsonResponse({"error": "Qualcosa è andato storto."})
    

class IFOAFinalSlide(View):
    template_name = "ifoa/final_slide.html"
    def get(self, request):
        try:
            context = {}
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            logger.info(f"IFOA: User visit Final page for : {custom_user_session_id}")
            current_user_id = request.session.get("current_user_id")
            stu_obj = IFOAStudentDetail.objects.filter(pk=current_user_id).first()
            if stu_obj:
                stu_obj.assessment_status = "Completed"
                stu_obj.save()
                logger.info(f"updated the assessment_status for : {stu_obj.email}")
                try:
                    send_mail =  send_email(request, stu_obj.email, custom_user_session_id)
                    logger.info(f"IFOA: Send email status -: {send_mail} for : {stu_obj.email}")
                except Exception as e:
                    logger.error(f"IFOA: Error in sending email : {e}")
                    pass
                update_google_sheet(request, stu_obj)
                logger.info(f"IFOA: User visited Final page for : {custom_user_session_id}")
                return render(request, self.template_name, context)
            logger.warning(f"IFOA: Redirected to register page from Final-page : {custom_user_session_id}")
            return HttpResponseRedirect(reverse("ifoa_register"))
        except Exception as error:
            logger.error(f'IFOA: Error in next_part from finish slide get method{error} for: {custom_user_session_id}')
            return HttpResponseRedirect(reverse("ifoa_register"))

class IFOACertificateView(View):
    template_name = "ifoa/ifoa-certificate.html"
    def get(self, request):
        context = {}
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        current_user_id = request.session.get("current_user_id")
        logger.info(f"IFOA: User visited Certificate page for : {current_user_id}")
        if current_user_id:
            context = create_certification(request, context)
            return render(self.request, self.template_name, context)
        logger.warning(f"IFOA: Redirected to register page from Certificate-page : {current_user_id}")
        return HttpResponseRedirect(reverse("ifoa_register"))
    
class OTPSendAndVerificationView(View):
    
    def post(self, request):
        send_otp = request.POST.get('send_otp', 'false')
        email = request.POST.get('email', None)
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        try:
            if send_otp == "true":
                logger.info(f"IFOA: User visited Send OTP page for : {email}")
                if email:
                    response = send_otp_mail(email, request)
                    if response:
                        return JsonResponse({"success": "OTP Sent Successfully."}, status=200)
                return JsonResponse({"error": "True"}, status=400)
            else:
                session_otp = request.session.get('otp', None)
                otp = request.POST.get('otp', None)
                if session_otp and otp:
                    otp = int(otp)
                    logger.info(f"IFOA: User visited Verify OTP page for : {email}")
                    if otp == session_otp:
                        request.session['is_otp_verified'] = True
                        return JsonResponse({"success": "OTP Verified Successfully."}, status=200)
                logger.warning(f'IFOA: error in session OTP for {custom_user_session_id} and email : {email}')
                return JsonResponse({"error": "True"}, status=400)
        except Exception as e:
            logger.error(f"IFOA: Error in sending otp : {e}")
        return JsonResponse({"error": "True"}, status=400)