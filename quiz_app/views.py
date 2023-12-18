from django.shortcuts import render, redirect
from django.views.generic import View
from .models import *
from lib.custom_logging import CustomLoggerAdapter
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings
from courses import models as course_models
from django.urls import reverse
import logging

adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

class QuizIndexView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = "quiz_app/index.html"

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.person_role == "Counselor":
                return HttpResponseRedirect(reverse("counselor-dashboard"))
            if request.user.person_role == "Futurely_admin":
                return HttpResponseRedirect(reverse("admin_dashboard"))
            if request.user.student.is_from_fast_track_program:
                context = {}
                context['videos_objs'] = course_models.MyBlogVideos.objects.filter(is_for_fast_track=True, status="published").all().order_by('sno')
                context['quiz_obj'] = Quiz.objects.filter(is_active=True)
                logger.info(f'Quiz: user visted at quiz index page for : {request.user.username}')
                return render(request, self.template_name, context)
            else:
                logger.error(f'Quiz: user not from fast track program for : {request.user.username}')
                return redirect('/home/')
        else:
            return redirect('/login/')


class StartQuizView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = 'quiz_app/questions.html'
    def get(self, request, quiz_id=None):
        try:
            if request.user.is_authenticated:
                if request.user.person_role == "Counselor":
                    return HttpResponseRedirect(reverse("counselor-dashboard"))
                if request.user.person_role == "Futurely_admin":
                    return HttpResponseRedirect(reverse("admin_dashboard"))
                username = request.user.username
                context = {}
                if quiz_id is None:
                    logger.error(f'Quiz: error in start quiz view, quiz id is none for : {username}')
                    request.session['is_created'] = False
                    request.session['is_refresh_the_page'] = False
                    return redirect('/quiz/')
                
                is_refresh_the_page = request.session.get('is_refresh_the_page', False)
                if is_refresh_the_page:
                    request.session['is_created'] = False
                    request.session['is_refresh_the_page'] = False
                    logger.error(f'Quiz: student refresh the page for : {username}')
                    return redirect('/quiz/')
                
                quiz_obj = Quiz.objects.filter(is_active=True, pk=quiz_id)
                if quiz_obj.count() > 0:
                    quiz_data = quiz_obj.first()
                    context['quiz_obj'] = quiz_data
                    is_created = request.session.get('is_created', False)
                    if is_created == False:
                        student_mapper_obj = QuizStudentMapper.objects.create(student=request.user, quiz=quiz_data)
                        stu_map_obj = student_mapper_obj.save()
                        logger.info(f'Student quiz mapper object created for : {username}')
                        request.session['quiz_mapper_id'] = student_mapper_obj.id
                        request.session['is_created'] = True
                    return render(request, self.template_name, context)
                else:
                    request.session['is_created'] = False
                    request.session['is_refresh_the_page'] = False
                    logger.warning(f'Quiz: error in start quiz view, quiz id is none for : {username}')
                    return redirect('/quiz/')
            else:
                return redirect('/login/')
            
        except Exception as error:
            logger.error(f'Quiz: error in start quiz view, {error} for : {request.user.username}')
            request.session['is_created'] = False
            request.session['is_refresh_the_page'] = False
            return redirect('/quiz/')
    
    def post(self, request, quiz_id=None):
        try:
            request_data = request.POST
            if quiz_id is None:
                logger.error(f'Quiz: error in start quiz view, quiz id is none for : {request.user.username}')
                return redirect('/quiz/')
            question_id = request_data.get('question')
            answer = request_data.get('answer')
            is_last_question = request_data.get('is_last_question')
            quiz_mapper_id = request.session.get('quiz_mapper_id', None)
            if quiz_mapper_id and question_id and answer and is_last_question:
                request.session['is_refresh_the_page'] = True
                user = request.user
                mapper_obj = QuizStudentMapper.objects.filter(pk=quiz_mapper_id, student=user)
                if mapper_obj.count() > 0:
                    student_map = mapper_obj.first()
                    question_obj = QuizQuestion.objects.get(pk=question_id)
                    # check the option with question table
                    correct_answer_point = question_obj.quiz.correct_answer_point
                    deduction_answer_point = question_obj.quiz.deduction_answer_point
                    options_obj = question_obj.question_options.filter(option=answer).first()
                    if options_obj.is_correct:
                        student_map.score += correct_answer_point
                    else:
                        student_map.score += deduction_answer_point
                    student_map.score = round(student_map.score, 2)
                    create_ans_obj = QuizStudentAnswer.objects.update_or_create(stu_mapper=student_map, question=question_obj, defaults={'answer': answer})
                    logger.info(f'Quiz: Answer submitted successfully for : {user.username}')
                    json_response = {}
                    if is_last_question == "Yes":
                        student_map.is_completed = True
                        json_response['is_completed'] = "Yes"
                        logger.info(f'Quiz: test successfully completed for : {request.user.username}')
                    logger.info(f'Quiz: return the successfully response for : {request.user.username}')
                    json_response['is_completed'] = "No"
                    student_map.save()
                    if is_last_question == "Yes":
                        email_response = send_result_mail(request)
                        logger.info(f'Quiz: send email response-{email_response} : {request.user.username}')
                    json_response['success'] = "Yes"
                    return JsonResponse(json_response)
                else:
                    logger.warning(f'Quiz: Student mapper is not exist for : {request.user.username}')
                    return JsonResponse({"error": "Qualcosa è andato storto."})
            else:
                logger.warning(f'Quiz: user submitted empty form for : {request.user.username}')
            return JsonResponse({"error": "Qualcosa è andato storto."})
        except Exception as Error:
            logger.error(f'Quiz: Error in startquizview - POST {Error} for : {request.user.username}')
            return JsonResponse({"error": "Qualcosa è andato storto."})

class TimeOutView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = 'quiz_app/time-out.html'
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.person_role == "Counselor":
                return HttpResponseRedirect(reverse("counselor-dashboard"))
            if request.user.person_role == "Futurely_admin":
                return HttpResponseRedirect(reverse("admin_dashboard"))
            context = {}
            quiz_mapper_id = request.session.get('quiz_mapper_id', None)
            user = request.user
            mapper_obj = QuizStudentMapper.objects.filter(pk=quiz_mapper_id, student=user).first()
            context['mapper_obj'] = mapper_obj
            logger.info(f'Quiz: Test time out for : {request.user.username}')
            request.session['is_created'] = False
            request.session['is_refresh_the_page'] = False
            return render(request, self.template_name, context)
        else:
            return redirect('/login/')

def send_result_mail(request):
    try:
        student_email = request.user.username
        template_name = 'quiz_app/send_email.html'
        subject = "Risultato della prova del test d’ingresso"
        quiz_mapper_id = request.session.get('quiz_mapper_id', None)
        user = request.user
        mapper_obj = QuizStudentMapper.objects.filter(pk=quiz_mapper_id, student=user).first()
        context = {
            "email": user.username,
            "data_obj": mapper_obj,
            "mapper_obj": mapper_obj,
        }
        html_msg = get_template(template_name).render(context)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [student_email])
        msg.content_subtype = "html"
        msg.send()
        logger.info(f"Quiz: E-Mail sent Successfully for : {student_email}")
        return True
    except Exception as Error:
        logger.error(f'Quiz: error in send mail {Error} for : {request.user.username}')
        return False

class FinalResultView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name = 'quiz_app/final-result.html'
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.person_role == "Counselor":
                return HttpResponseRedirect(reverse("counselor-dashboard"))
            if request.user.person_role == "Futurely_admin":
                return HttpResponseRedirect(reverse("admin_dashboard"))
            context = {}
            quiz_mapper_id = request.session.get('quiz_mapper_id', None)
            user = request.user
            mapper_obj = QuizStudentMapper.objects.filter(pk=quiz_mapper_id, student=user).first()
            context['mapper_obj'] = mapper_obj
            logger.info(f'Quiz: Test successfully completed by : {request.user.username}')
            request.session['is_created'] = False
            request.session['is_refresh_the_page'] = False
            return render(request, self.template_name, context)
        else:
            return redirect('/login/')