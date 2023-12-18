from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
import logging, requests, os
from .models import *
from landing_website.forms import  ContactUsForm
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.core.validators import EmailValidator
from landing_website.tasks import send_email_after_submitting_contact_form
from lib.custom_logging import CustomLoggerAdapter
from django.utils.translation import ugettext as _
from lib.hubspot_contact_sns import create_update_contact_hubspot
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})


class HandleFormMIxin:
    
    form_class = None
    def post(self, request):
        try:
            context = {}
            custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
            logger.info(f"user requested post contact form at HandleFormMIxin for :{custom_user_session_id}")
            form = self.form_class(request.POST)
            subscribe_newsletter = request.POST.get('subscribe_newsletter', False)
            if form.is_valid():
                email = form.cleaned_data['email']
                contact_form = form.save(commit=False)
                if subscribe_newsletter:
                    contact_form.subscribe_newsletter = True
                    newsletter, created = Newsletter.objects.get_or_create(email=email)
                    if created:
                        logger.info(f'New newsletter created for email: {email}')
                    else:
                        logger.info(f'Newsletter already exists for email: {email}')
                contact_form.save()
                logger.info(f'contact form successfully submitted for : {email}')
                try:
                    logger.info(f'Creating hubspot properties for landing website contact form for : {email}')
                    firstname = form.cleaned_data['first_name']
                    organization_type = form.cleaned_data['organization']
                    lastname = form.cleaned_data['last_name']
                    company = form.cleaned_data['company_name']
                    ruolo_organizzazione = form.cleaned_data['role']
                    requirement_description = form.cleaned_data['concern']
                    contact_number = form.cleaned_data.get('phone_number', None)
                    keys_list = ["email","firstname", "lastname", "organization_type", "company", "ruolo_organizzazione", "requirement_description", "is_from_demo_form", "contact_number"]
                    values_list = [email,firstname, lastname, organization_type, company, ruolo_organizzazione, requirement_description,"true", contact_number]                 
                    create_update_contact_hubspot(email, keys_list, values_list)
                    logger.info(f'updated hubspot properties form landing website contact form for : {email}')
                except Exception as ex:
                    error(f'Error while creating hubspot properties: {email} : {ex}')
                send_email_after_submitting_contact_form.apply_async(args=[email])
                form = self.form_class()
                context["contact_us_form"] = form
                context['scroll_to_contactform'] = True
                messages.success(request, 'Request submitted')
                return render(request, self.template_name,context)
            else:
                logger.warning(f'Error while submitting: contact form is invalid for : {custom_user_session_id}')
                context = self.get_context_data()
                context["contact_us_form"] = form
                context['scroll_to_contactform'] = True
                return render(request, self.template_name,context)
        except Exception as error:
            logger.error(f"An error occurred in HandleFormMixin while submitting the contact us form error: {error}")
            context = self.get_context_data()
            context["contact_us_form"] = form
            context['scroll_to_contactform'] = True
            return render(request, self.template_name, context)


class LandingWebsiteView(HandleFormMIxin,View):
    template_name = "landing_website/index.html"
    form_class = ContactUsForm

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteView for: {custom_user_session_id}")
        context = {}
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        is_from_register_page = request.GET.get('contact-us', False)
        if is_from_register_page == "True":
            context['scroll_to_contactform'] = True
        context['contact_us_form'] = ContactUsForm()
        return render(self.request, self.template_name, context)
    
    def get_context_data(self):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"User entered in 'get_context_data' method of LandingWebsiteView to post contact form data for: {custom_user_session_id}")
        context = {}
        context['contact_us_form'] = self.form_class()
        return context
    
    

class LandingWebsiteCompanyView(HandleFormMIxin,View):
    template_name = "landing_website/company.html"
    form_class = ContactUsForm


    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteCompanyView for: {custom_user_session_id}")
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        context = {}
        context['contact_us_form'] = ContactUsForm()
        return render(self.request, self.template_name, context)
    
    def get_context_data(self):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"User entered in 'get_context_data' method of LandingWebsiteCompanyView to post contact form data for: {custom_user_session_id}")
        context = {}
        context['contact_us_form'] = self.form_class()
        return context
    

class LandingWebsiteSchoolView(HandleFormMIxin,View):
    template_name = "landing_website/school.html"
    form_class = ContactUsForm


    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteSchoolView for: {custom_user_session_id}")
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        context = {}
        context['contact_us_form'] = ContactUsForm()
        return render(self.request, self.template_name, context)
    
    def get_context_data(self):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"User entered in 'get_context_data' method of LandingWebsiteSchoolView to post contact form data for: {custom_user_session_id}")
        context = {}
        context['contact_us_form'] = self.form_class()
        return context


class LandingWebsiteUniversityView(HandleFormMIxin,View):
    template_name = "landing_website/university.html"
    form_class = ContactUsForm


    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteUniversityView for: {custom_user_session_id}")
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        context = {}
        context['contact_us_form'] = ContactUsForm()
        return render(self.request, self.template_name, context)

    def get_context_data(self):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        logger.info(f"User entered in 'get_context_data' method of LandingWebsiteUniversityView to post contact form data for: {custom_user_session_id}")
        context = {}
        context['contact_us_form'] = self.form_class()
        return context


class NewsletterFormView(View):  
    def post(self, request):
        try:
            email = request.POST.get('email')
            if email:
                logger.info(f'Received a request with an email for subscribing to the newsletter: {email}')
                validator = EmailValidator()
                try:
                    validator(email)
                except Exception:
                    logger.error(f'Invalid email address: {email}')
                    return JsonResponse({'success': False, 'message': _('Invalid email.')})
                
                newsletter = Newsletter(email=email)
                newsletter.save()
                logger.info(f'The user successfully subscribed to the newsletter: {email}')
                return JsonResponse({'success': True, 'message': _('Thank you for subscribing!')})
            else:
                return JsonResponse({'success': False, 'message': 'Email field is required.'})
        except Exception as error:
            logger.error(f"An error occurred while submit the news letter at NewsletterFormView : {error}")
            return JsonResponse({'success': False, 'message': _('Something went wrong.')})


class LandingWebsiteAboutView(TemplateView): 
    template_name = "landing_website/about.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteAboutView for: {custom_user_session_id}")
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        context = {}
        locale = request.LANGUAGE_CODE
        return render(self.request, self.template_name, context)

class LandingWebsiteMentorView(TemplateView):
    template_name = "landing_website/mentor.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteMentorView for: {custom_user_session_id}")
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        context = {}
        locale = request.LANGUAGE_CODE
        return render(self.request, self.template_name, context)


class LandingWebsiteFaqView(View):
    template_name = "landing_website/faq.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteFaqView for: {custom_user_session_id}")
        if request.user.is_authenticated:
            if request.user.person_role == "Student":
                return HttpResponseRedirect(reverse("home"))
            elif request.session.get('is_company',False):
                return HttpResponseRedirect(reverse("student_course_report"))
            else:
                return HttpResponseRedirect(reverse("counselor_program"))
        context = {}
        locale = request.LANGUAGE_CODE
        context['landing_website_faq'] = LandingWebsiteFaqModel.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.template_name, context)
    

class LandingWebsitePrivacyPolicyView(View):
    template_name = "landing_website/privacy-policy.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsitePrivacyPolicyView for: {custom_user_session_id}")
        context = {}
        locale = request.LANGUAGE_CODE
        context['privacy_policy'] = LandingWebsitePrivacyPolicy.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.template_name, context)
    

class LandingWebsiteTermsOfUseView(View):
    template_name = "landing_website/terms-of-use.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteTermsOfUseView for: {custom_user_session_id}")
        context = {}
        locale = request.LANGUAGE_CODE
        context['terms_of_use'] = LandingWebsiteTermsOfUse.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.template_name, context)

class TermsAndConditionsView(View):
    template_name = "landing_website/terms-and-conditions.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of TermsAndConditionsView for: {custom_user_session_id}")
        context = {}
        locale = request.LANGUAGE_CODE
        context['terms_of_use'] = TermsAndCondition.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.template_name, context)

class RegisterTermsAndConditionView(View):
    template_name = "landing_website/register-terms-and-conditions.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of RegisterTermsAndConditionView for: {custom_user_session_id}")
        context = {}
        locale = request.LANGUAGE_CODE
        context['terms_of_use'] = RegisterTermsAndCondition.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.template_name, context)

class LandingWebsiteCookiesPolicyView(View):
    templte_name = "landing_website/cookies-policy.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of LandingWebsiteCookiesPolicyView for: {custom_user_session_id}")
        context = {}
        locale = request.LANGUAGE_CODE
        context['cookies_policy'] = LandingWebsiteCookiesPolicy.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.templte_name, context)


class NewsLetterPrivacyPolicyView(View):
    templte_name = "landing_website/news-letter-privacy-policy.html"

    def get(self, request):
        request.session['lang'] = "it"
        logger.info("User entered in 'get' method of NewsLetterPrivacyPolicyView")
        context = {}
        locale = request.LANGUAGE_CODE
        context['news_letter_policy'] = NewsLetterPrivacyPolicy.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.templte_name, context)
    

class RegisterPrivacyPolicyView(View):
    templte_name = "landing_website/register-privacy-policy.html"

    def get(self, request):
        request.session['lang'] = "it"
        logger.info("User entered in 'get' method of RegisterPrivacyPolicyView")
        context = {}
        locale = request.LANGUAGE_CODE
        context['register_privacy_policy'] = RegisterPrivacyPolicy.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.templte_name, context)



class WebsitePolicyView(View):
    template_name = "landing_website/website-privacy-policy.html"

    def get(self, request):
        custom_user_session_id = self.request.session.get('CUSTOM_USER_SESSION_ID', '')
        request.session['lang'] = "it"
        logger.info(f"User entered in 'get' method of WebsitePolicyView for: {custom_user_session_id}")
        context = {}
        locale = request.LANGUAGE_CODE
        context['website_policy'] = WebsitePrivacyPolicy.objects.filter(locale=locale).order_by("sno").all()
        return render(self.request, self.template_name, context)
    

class DownloadPDFView(View):

    def get(self, request):
        try:
            filename = request.GET.get('filename')
            logger.info(f'Student requested a PDF file: {filename}')

            if filename == 'privacy_policy':
                privacy_policy_obj = LandingWebsitePrivacyPolicy.objects.all().first()
                file_url = privacy_policy_obj.download_pdf_file_link
                
            elif filename == "cookies_policy":
                cookies_policy_obj = LandingWebsiteCookiesPolicy.objects.all().first()
                file_url = cookies_policy_obj.download_pdf_file_link

            elif filename == "terms_of_use":
                terms_of_use_obj = LandingWebsiteTermsOfUse.objects.all().first()
                file_url = terms_of_use_obj.download_pdf_file_link

            elif filename == "register_policy":
                register_policy_obj = RegisterPrivacyPolicy.objects.all().first()
                file_url = register_policy_obj.download_pdf_file_link

            elif filename == "news_letter_policy":
                news_letter_policy_obj = NewsLetterPrivacyPolicy.objects.all().first()
                file_url = news_letter_policy_obj.download_pdf_file_link

            elif filename == "website_privacy_policy":
                website_privacy_policy = WebsitePrivacyPolicy.objects.all().first()
                file_url = website_privacy_policy.download_pdf_file_link
            elif filename == 'register_terms_and_conditions':
                register_terms_and_Condition = RegisterTermsAndCondition.objects.all().first()
                file_url = register_terms_and_Condition.download_pdf_file_link

            elif filename == 'terms_and_condition':
                terms_and_conditon = TermsAndCondition.objects.all().first()
                file_url = terms_and_conditon.download_pdf_file_link
            else:
                return render(request, "website/404.html",status=404)

            response = self.get_pdf_response(file_url)
            logger.info(f'student successfully download PDF file: {filename}')
            return response
        
        except Exception as error:
            logger.error(f'An error occurred in DownloadPDFView while downloading the PDF file: {error}')
            return render(request, "website/404.html",status=404)
        

    def get_pdf_response(self, file_url):
        file_name = file_url.split('/')[-1].split('.')[0]
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'
        
        pdf_data = requests.get(file_url).content
        response.write(pdf_data)
        
        return response
