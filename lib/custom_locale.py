from django.conf import settings
import uuid
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.http import HttpResponseRedirect
from django.urls import get_script_prefix, is_valid_path, reverse
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin
from lib.helper import get_client_ip, get_location_by_ip, is_http_user_agent_from_crawler, is_http_user_agent_from_mobile
#from userauth import models
from datetime import datetime, timedelta
import pytz
import logging
from django.utils import timezone
from hashlib import blake2b



logger = logging.getLogger('watchtower')
logger_console = logging.getLogger('console')


class SelectLangMiddleware(MiddlewareMixin):
    """
    Custom Locale MiddleWare
    """
    response_redirect_class = HttpResponseRedirect

    def process_request(self, request):
        if request.GET.get('influencer', None):
            request.session['INFLUENCER'] = request.GET.get('influencer')
        is_from_mobile_app = request.GET.get('is_from_mobile_app', None)
        if is_from_mobile_app is None:
            is_from_mobile_app = request.session.get('is_from_mobile_app',None)
            if is_from_mobile_app is None:
                is_from_mobile_app = False
        if is_from_mobile_app in ("True", "true", True):
            is_from_mobile_app = True
        else:
            is_from_mobile_app = False
        request.session['is_from_mobile_app'] = is_from_mobile_app

        is_from_ios_app = request.GET.get('is_from_ios_app', None)
        if is_from_ios_app is None:
            is_from_ios_app = request.session.get('is_from_ios_app',None)
            if is_from_ios_app is None:
                is_from_ios_app = False
        if is_from_ios_app in ("True", "true", True):
            is_from_ios_app = True
        else:
            is_from_ios_app = False
        request.session['is_from_ios_app'] = is_from_ios_app
        user_agent = request.META.get('HTTP_USER_AGENT',None)
        http_accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', None)
        current_url_path = request._current_scheme_host + request.path
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        if user_agent is not None:
            is_phone_view = is_http_user_agent_from_mobile(user_agent)
            request.session['is_phone_view'] = is_phone_view
        else:
            is_phone_view = False
            request.session['is_phone_view'] = False
        
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        clarity_token = request.session.get('clarity_token', None)
        if user_agent is not None:
            request.session['is_phone_view'] = is_http_user_agent_from_mobile(user_agent)
        else:
            request.session['is_phone_view'] = False
        if not custom_user_session_id:
            uuid_one = str(uuid.uuid1())
            request.session['CUSTOM_USER_SESSION_ID'] = uuid_one
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            
        if not clarity_token:
            try:
                logger.info(f"In Hashing module to create  custom clarity ID for session : {custom_user_session_id} ")
                salt = uuid.uuid4().hex
                salted_value = salt + custom_user_session_id
                hash_object = blake2b(salted_value.encode(), digest_size=4)
                clarity_id = hash_object.hexdigest()
                logger.info(f"Custom clarity ID created for session : {custom_user_session_id} is  : {clarity_id}")
                request.session["clarity_token"] = clarity_id
            except Exception as Error:
                logger.error(f"An error occurred while creating custom clarity ID:{Error} for session : {custom_user_session_id}")

        lang = None
        
        if "unipegaso" in current_url_path or "unimercatorum" in current_url_path or "utsanraffaele" in current_url_path :
            lang = "it"
        
        if not lang:
            lang = request.GET.get('lang', None)
            if lang:
                request.session['is_url_lang_prioritise'] = "True"
                request.session['display_lang_popup'] = "False"

        if not lang:
            if request.user.is_authenticated:
                try:
                    is_url_lang_prioritise = request.session.get('is_url_lang_prioritise', None)
                    if is_url_lang_prioritise is None or is_url_lang_prioritise == "False":
                        lang = request.user.lang_code
                    else:
                        lang = "it"
                except:
                    logger.error(f"Error to get lang code in custom middleware for authenticated user : {request.user.username}")
            else:
                lang = "it"
                request.session['is_url_lang_prioritise'] = "False"
        
        if not lang:
            lang = request.session.get('lang', None)
        
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = is_language_prefix_patterns_used(
            urlconf)
        language = translation.get_language_from_request(
            request, check_path=i18n_patterns_used)
        language_from_path = translation.get_language_from_path(
            request.path_info) #Get browser lang
        if not language_from_path and i18n_patterns_used and not prefixed_default_language:
            language = settings.LANGUAGE_CODE

        # if country and country == 'Italy':
        #     language = 'it'
        is_request_from_crawler = False
        if user_agent is None:
            logger.warning(f"User agent is None for session id: {custom_user_session_id}")
            is_request_from_crawler = True
        else:
            logger.info(f"Request is forwarded to check is HTTP_USER_AGENT: {user_agent} from crawler for {custom_user_session_id}")
            is_request_from_crawler = is_http_user_agent_from_crawler(user_agent)
            logger.info(f"Request is checked and HTTP_USER_AGENT: {user_agent} from crawler is {is_request_from_crawler} for {custom_user_session_id}")

        if not lang:
            print(language)
            if language == "it":
                logger.info(f"By default langugae is {language} from settings for {custom_user_session_id}")
                lang = "it"
            else:
                logger.info(f"By default langugae is {language} and initial select lang url is called for {custom_user_session_id}")
                lang = "en"
                if is_request_from_crawler == False:
                    display_lang_popup = request.session.get('display_lang_popup', None)
                    if display_lang_popup is None:
                        request.session['display_lang_popup'] = "True"
                        request.session['reverse_url_from_setlang'] = request.build_absolute_uri()

        if not is_request_from_crawler:
            request.session['lang'] = lang

        if lang == 'it':
            language = 'it'
        else:
            language = 'en-us'
        logger.info(f"language code {lang} set by : {custom_user_session_id}")
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        if(request.LANGUAGE_CODE == "it"):
            request.TIME_ZONE = 'Europe/Rome'
            # timezone.activate(request.TIME_ZONE)
        else:
            request.TIME_ZONE = 'UTC'
        
        # if request.session.get('ctype', None):
            # ctype = request.GET.get('ctype', None)
            # request.session['ctype'] = ctype if ctype else 'general'

    def process_response(self, request, response):
        # try:
        #     if request.COOKIES.get("ip_address", None) == None:
        #         ip_address = get_client_ip(request)
        #         response.set_cookie("ip_address", ip_address, max_age=604800)
        #         # response.cookies['ip_address']['expires'] = datetime.today() + timedelta(days=7)
        #         logger.info(f"IP address does not exist in request cookies : {ip_address}")
        #     if request.COOKIES.get('country', None) == None:
        #         ip_address = request.COOKIES.get("ip_address", None)
        #         if ip_address == None:
        #             ip_address = get_client_ip(request)
        #             response.set_cookie("ip_address", ip_address, max_age=604800)
        #             logger.info(f"IP address does not exist in response cookies : {ip_address} and added in cookies")
        #         else:
        #             ip_address = request.COOKIES.get("ip_address")
        #         resp = get_location_by_ip(ip_address)
        #         if 'country' in resp:
        #             country = resp['country']
        #             response.set_cookie("country", country, max_age=604800)
        #             logger.info(f"Country does not exist in response cookies : {ip_address} and added in cookies")
        # except Exception as error:
        #     print(error)
        #     logger.error(f"Error in custom middleware : {error}")
        language = translation.get_language()
        language_from_path = translation.get_language_from_path(
            request.path_info)
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = is_language_prefix_patterns_used(
            urlconf)

        if (response.status_code == 404 and not language_from_path and
                i18n_patterns_used and prefixed_default_language):
            # Maybe the language code is missing in the URL? Try adding the
            # language prefix and redirecting to that URL.
            language_path = '/%s%s' % (language, request.path_info)
            path_valid = is_valid_path(language_path, urlconf)
            path_needs_slash = (
                not path_valid and (
                    settings.APPEND_SLASH and not language_path.endswith('/') and
                    is_valid_path('%s/' % language_path, urlconf)
                )
            )

            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                # Insert language after the script prefix and before the
                # rest of the URL
                language_url = request.get_full_path(force_append_slash=path_needs_slash).replace(
                    script_prefix,
                    '%s%s/' % (script_prefix, language),
                    1
                )
                return self.response_redirect_class(language_url)

        if not (i18n_patterns_used and language_from_path):
            patch_vary_headers(response, ('Accept-Language',))
        response.headers.setdefault('Content-Language', language)
        return response



class CustomLocaleMiddleware(MiddlewareMixin):
    """
    Custom Locale MiddleWare
    """
    response_redirect_class = HttpResponseRedirect

    def process_request(self, request):
        if request.GET.get('influencer', None):
            request.session['INFLUENCER'] = request.GET.get('influencer')
        is_from_mobile_app = request.GET.get('is_from_mobile_app', None)
        if is_from_mobile_app is None:
            is_from_mobile_app = request.session.get('is_from_mobile_app',None)
            if is_from_mobile_app is None:
                is_from_mobile_app = False
        if is_from_mobile_app in ("True", "true", True):
            is_from_mobile_app = True
        else:
            is_from_mobile_app = False
        request.session['is_from_mobile_app'] = is_from_mobile_app

        is_from_ios_app = request.GET.get('is_from_ios_app', None)
        if is_from_ios_app is None:
            is_from_ios_app = request.session.get('is_from_ios_app',None)
            if is_from_ios_app is None:
                is_from_ios_app = False
        if is_from_ios_app in ("True", "true", True):
            is_from_ios_app = True
        else:
            is_from_ios_app = False
        request.session['is_from_ios_app'] = is_from_ios_app
        user_agent = request.META.get('HTTP_USER_AGENT',None)
        http_accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', None)
        current_url_path = request._current_scheme_host + request.path
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        if user_agent is not None:
            is_phone_view = is_http_user_agent_from_mobile(user_agent)
            request.session['is_phone_view'] = is_phone_view
            # request.session['is_phone_view'] = True
        else:
            is_phone_view = False
            request.session['is_phone_view'] = False
        
        # if is_phone_view is False:
        #     request.session["is_from_ios_app"] = False
        user_agent = request.META.get('HTTP_USER_AGENT',None)
        current_url_path = request._current_scheme_host + request.path
        custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
        clarity_token = request.session.get('clarity_token', None)
        if user_agent is not None:
            request.session['is_phone_view'] = is_http_user_agent_from_mobile(user_agent)
            # request.session['is_phone_view'] = True
        else:
            request.session['is_phone_view'] = False
        if not custom_user_session_id:
            uuid_one = str(uuid.uuid1())
            request.session['CUSTOM_USER_SESSION_ID'] = uuid_one
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', None)
            
        if not clarity_token:
            try:
                logger.info(f"In Hashing module to create  custom clarity ID for session : {custom_user_session_id} ")
                salt = uuid.uuid4().hex
                salted_value = salt + custom_user_session_id
                hash_object = blake2b(salted_value.encode(), digest_size=4)
                clarity_id = hash_object.hexdigest()
                logger.info(f"Custom clarity ID created for session : {custom_user_session_id} is  : {clarity_id}")
                request.session["clarity_token"] = clarity_id
            except Exception as Error:
                logger.error(f"An error occurred while creating custom clarity ID:{Error} for session : {custom_user_session_id}")

        lang = None
        try:
            url_for_it = current_url_path
            url_for_en = current_url_path
            url_for_default = current_url_path
            
            path_from_request = request.path
            if path_from_request is not None:
                sub_paths = path_from_request.split('/')
                number_of_paths = len(sub_paths)
                # Check if it's a url starting with /it
                if number_of_paths > 1 and (sub_paths[0] == "" and sub_paths[1] == "it"):
                    logger.info(f"Accessing the it path: visited url(Page): {current_url_path} \
                        and visited by : {custom_user_session_id}, and user agent; {user_agent}")
                    lang = 'it'
                    # remove 'it' from the url path
                    sub_paths.pop(1)
                    url_for_default = request._current_scheme_host + "/".join(sub_paths)
                    sub_paths.insert(1, "en")
                    url_for_en = request._current_scheme_host + "/".join(sub_paths)
                elif number_of_paths > 1 and (sub_paths[0] == "" and sub_paths[1] == "en"):
                    logger.info(f"Accessing the en path: visited url(Page): {current_url_path} \
                        and visited by : {custom_user_session_id}, and user agent; {user_agent}")
                    lang = 'en'
                    # remove 'en' from the url path
                    sub_paths.pop(1)
                    url_for_default = request._current_scheme_host + "/".join(sub_paths)
                    sub_paths.insert(1, "it")
                    url_for_it = request._current_scheme_host + "/".join(sub_paths)
                else:
                    sub_paths.insert(1, "it")
                    url_for_it = request._current_scheme_host + "/".join(sub_paths)
                    sub_paths.pop(1)
                    sub_paths.insert(1, "en")
                    url_for_en = request._current_scheme_host + "/".join(sub_paths)

            request.URL_FOR_IT = url_for_it
            request.URL_FOR_EN = url_for_en
            request.URL_FOR_DEFAULT = url_for_default
        except Exception as error:
            logger.error(f"Error {error} in checking the path starting with italy, url: {current_url_path} customer_session_id : {custom_user_session_id}")
        if "unipegaso" in current_url_path or "unimercatorum" in current_url_path or "utsanraffaele" in current_url_path :
            lang = "it"
        
        if not lang:
            lang = request.GET.get('lang', None)
            if lang:
                request.session['is_url_lang_prioritise'] = "True"
                request.session['display_lang_popup'] = "False"

        if not lang:
            if request.user.is_authenticated:
                try:
                    is_url_lang_prioritise = request.session.get('is_url_lang_prioritise', None)
                    if is_url_lang_prioritise is None or is_url_lang_prioritise == "False":
                        lang = request.user.lang_code
                except:
                    logger.error(f"Error to get lang code in custom middleware for authenticated user : {request.user.username}")
            else:
                request.session['is_url_lang_prioritise'] = "False"
        
        if not lang:
            lang = request.session.get('lang', None)
        country = None
        try:
            ip_address = request.COOKIES.get("ip_address", None)
            if ip_address is None:
                ip_address = get_client_ip(request)
                # resp = get_location_by_ip(ip_address)
                # logger.info(f"IP address does not exist in request cookies : {ip_address} and visited by - {custom_user_session_id}")
                # if 'country' in resp:
                #    country = resp['country']
                # else:
                #     country = request.COOKIES.get("country", None)
                #     logger.info(f"country name fetched from cookies - {country} for user - {custom_user_session_id} ")
            if(request.user.id):
                user_name = request.user.username
                logger.info(f"Request processed for ip_address: {ip_address}, visited url(Page): {current_url_path}, http_accept_lang : {http_accept_lang} and visited by : {user_name}")
            else:
                logger.info(f"Request processed for ip_address: {ip_address}, visited url(Page): {current_url_path},  http_accept_lang : {http_accept_lang} and visited by : {custom_user_session_id}")
        except Exception as error:
            if(request.user.id):
                user_name = request.user.username
                logger.error(f"Error In CustomLocaleMiddleware, IP address not found {error} and url: {current_url_path} called by : {user_name}")
            else:
                logger.error(f"Error In CustomLocaleMiddleware, IP address not found {error} and url: {current_url_path} called by : {custom_user_session_id}")
        
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = is_language_prefix_patterns_used(
            urlconf)
        language = translation.get_language_from_request(
            request, check_path=i18n_patterns_used)
        language_from_path = translation.get_language_from_path(
            request.path_info) #Get browser lang
        if not language_from_path and i18n_patterns_used and not prefixed_default_language:
            language = settings.LANGUAGE_CODE

        # if country and country == 'Italy':
        #     language = 'it'
        is_request_from_crawler = False
        if user_agent is None:
            logger.warning(f"User agent is None for session id: {custom_user_session_id}")
            is_request_from_crawler = True
        else:
            logger.info(f"Request is forwarded to check is HTTP_USER_AGENT: {user_agent} from crawler for {custom_user_session_id}")
            is_request_from_crawler = is_http_user_agent_from_crawler(user_agent)
            logger.info(f"Request is checked and HTTP_USER_AGENT: {user_agent} from crawler is {is_request_from_crawler} for {custom_user_session_id}")

        if not lang:
            if language == "it":
                lang = "it"
            else:
                logger.info(f"By default langugae is {language} and initial select lang url is called for {custom_user_session_id}")
                lang = "en"
                if is_request_from_crawler == False:
                    display_lang_popup = request.session.get('display_lang_popup', None)
                    if display_lang_popup is None:
                        request.session['display_lang_popup'] = "True"
                        request.session['reverse_url_from_setlang'] = request.build_absolute_uri()

        if not is_request_from_crawler:
            request.session['lang'] = lang

        if lang == 'it':
            language = 'it'
        else:
            language = 'en-us'
        logger.info(f"language code {lang} set by : {custom_user_session_id}")
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        if(request.LANGUAGE_CODE == "it"):
            request.TIME_ZONE = 'Europe/Rome'
            # timezone.activate(request.TIME_ZONE)
        else:
            request.TIME_ZONE = 'UTC'
        
        # if request.session.get('ctype', None):
            # ctype = request.GET.get('ctype', None)
            # request.session['ctype'] = ctype if ctype else 'general'

    def process_response(self, request, response):
        # try:
        #     if request.COOKIES.get("ip_address", None) == None:
        #         ip_address = get_client_ip(request)
        #         response.set_cookie("ip_address", ip_address, max_age=604800)
        #         # response.cookies['ip_address']['expires'] = datetime.today() + timedelta(days=7)
        #         logger.info(f"IP address does not exist in request cookies : {ip_address}")
        #     if request.COOKIES.get('country', None) == None:
        #         ip_address = request.COOKIES.get("ip_address", None)
        #         if ip_address == None:
        #             ip_address = get_client_ip(request)
        #             response.set_cookie("ip_address", ip_address, max_age=604800)
        #             logger.info(f"IP address does not exist in response cookies : {ip_address} and added in cookies")
        #         else:
        #             ip_address = request.COOKIES.get("ip_address")
        #         resp = get_location_by_ip(ip_address)
        #         if 'country' in resp:
        #             country = resp['country']
        #             response.set_cookie("country", country, max_age=604800)
        #             logger.info(f"Country does not exist in response cookies : {ip_address} and added in cookies")
        # except Exception as error:
        #     print(error)
        #     logger.error(f"Error in custom middleware : {error}")
        language = translation.get_language()
        language_from_path = translation.get_language_from_path(
            request.path_info)
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = is_language_prefix_patterns_used(
            urlconf)

        if (response.status_code == 404 and not language_from_path and
                i18n_patterns_used and prefixed_default_language):
            # Maybe the language code is missing in the URL? Try adding the
            # language prefix and redirecting to that URL.
            language_path = '/%s%s' % (language, request.path_info)
            path_valid = is_valid_path(language_path, urlconf)
            path_needs_slash = (
                not path_valid and (
                    settings.APPEND_SLASH and not language_path.endswith('/') and
                    is_valid_path('%s/' % language_path, urlconf)
                )
            )

            if path_valid or path_needs_slash:
                script_prefix = get_script_prefix()
                # Insert language after the script prefix and before the
                # rest of the URL
                language_url = request.get_full_path(force_append_slash=path_needs_slash).replace(
                    script_prefix,
                    '%s%s/' % (script_prefix, language),
                    1
                )
                return self.response_redirect_class(language_url)

        if not (i18n_patterns_used and language_from_path):
            patch_vary_headers(response, ('Accept-Language',))
        response.headers.setdefault('Content-Language', language)
        return response


class SetCookieMiddleware(MiddlewareMixin):
    def process_request(self, request):
        to_display_first_time_cookie_banner = request.session.get('to_display_first_time_cookie_banner', None)
        if to_display_first_time_cookie_banner is None:
            request.session['to_display_first_time_cookie_banner'] = "True"


# class SetLastVisitMiddleware():
#     def process_request(self, request):
#         user = request.GET.get('user',None)
#         print(user)
#         if(user):

#             if request.user.is_authenticated:
#                 # Update last visit time after request finished processing.
#                 local_tz = pytz.timezone(settings.TIME_ZONE)
#                 dt = local_tz.localize(datetime.datetime.now())
#                 models.Person.objects.filter(pk=request.user.pk).update(last_visit=dt)
#         return None

# class LastVisitMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if request.user.is_authenticated:
#             # Update last visit time after request finished processing.
#             local_tz = pytz.timezone(settings.TIME_ZONE)
#             dt = local_tz.localize(datetime.datetime.now())
#             print(dt)
#             user = models.Person.objects.filter(pk=request.user.pk).update(last_visit=dt)
#         response = self.get_response(request)
#         return response

