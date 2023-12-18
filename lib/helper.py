import requests
import json
from django.db.models import Q
from django.conf import settings
import datetime
import pytz
from web_analytics.models import CustomEvent, EVENT_NAMES
from payment.models import Coupon, Tax
from courses.models import OurPlans
import logging
from django.contrib.auth import get_user_model

PERSON = get_user_model()

from lib.custom_logging import CustomLoggerAdapter


adapter = logging.getLogger('watchtower')
logger = CustomLoggerAdapter(adapter, {})

logger_console_adapter = logging.getLogger('console')
logger_console = CustomLoggerAdapter(logger_console_adapter, {})


LIST_OF_CRAWLERS = ['twitterbot','siteauditbot','tpradstxtcrawler','pinterestbot','coccocbot','googlebot','bingbot','slurp', 'duckduckbot', 'baiduspider', 'yandexbot', 'sogou','exabot','facebot','facebookexternalhit', 'ia_archiver','elb-healthchecker','apis-google','adsbot','mediapartners-google','feedfetcher-google','google-read-aloud','duplexweb-google','googleweblight','storebot-google', 'googleimageproxy','mj12bot','megaindex','ahrefsbot','semrushbot','dotbot','jobboersebot','petalbot','msnbot','seoscanners','seokicks-robot','blexbot','seznambot','bubing','voilabot','mail.ru_bot','adscanner']

LIST_OF_DEVICE = ['android', 'iphone', 'mobile']

def get_location_by_ip(ip_address):
    """Analytics data by Object type"""
    try:
        request_url = "http://ip-api.com/json/{}".format(ip_address)
        response = requests.get(request_url)
        json_response = response.json()
        return json_response
    except Exception as error:
        raise Exception({"get_location_by_ip: ": str(error)})


def get_client_ip(request):
    ip = ""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_http_user_agent_from_crawler(user_agent):
    user_agent = user_agent.lower()
    if any(substring in user_agent for substring in LIST_OF_CRAWLERS):
        return True
    else:
        return False

def is_http_user_agent_from_mobile(user_agent):
    user_agent = user_agent.lower()
    if any(substring in user_agent for substring in LIST_OF_DEVICE):
        return True
    else:
        return False

def create_custom_event(request, event_id=None, custom_user_session_id=None, meta_data={}):
    try:
        if event_id:
            user_agent = request.META.get('HTTP_USER_AGENT', None)
            page_url = request.get_full_path()
            ip_address = get_client_ip(request)
            meta_data['influencer'] = request.session.get('INFLUENCER', '') # This is being set in custom_locale.py 
            
            if not custom_user_session_id:
                custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
            event_name = ""
            for e_name in EVENT_NAMES:
                if e_name[0] == event_id:
                    event_name = e_name[1]
            if user_agent != "ELB-HealthChecker/2.0" or user_agent != None:
                if request.user.id:
                    person = request.user
                    CustomEvent.objects.create(person=person, event_id=event_id, event_name=event_name, user_agent=user_agent, page_url=page_url, ip_address=ip_address, custom_user_session_id=custom_user_session_id, meta_data=meta_data)
                    logger.info(f"Custom event '{event_name}' cretaed successfully by : {request.user.username}")
                else:
                    CustomEvent.objects.create(event_id=event_id, event_name=event_name, user_agent=user_agent, page_url=page_url, ip_address=ip_address, custom_user_session_id=custom_user_session_id, meta_data=meta_data)
                    logger.info(f"Custom event '{event_name}' cretaed successfully by : {custom_user_session_id}")
    except Exception as e:
        if(request.user.id):
            user_name = request.user.username
            logger.error(f"Error('{e}') to create event, and username is : {user_name}")
        else:
            custom_user_session_id = request.session.get('CUSTOM_USER_SESSION_ID', '')
            logger.error(f"Error('{e}') to create event, and session id  : {custom_user_session_id}")
        


def calculate_discount_parameters(request, coupon_code=None):
    """if user have applied coupon code then call this function and calculate discount parameters with coupon code"""
    # coupon_code = None # pass any coupon_code here and it will apply the default discount automatically
    coupon_obj = None
    discount = 0
    student = getattr(request.user, 'student', None)
    result = {}
    try:
        plan_id = request.session.get('plan_id', None)
        try:
            our_plan_obj = OurPlans.plansManager.lang_code(request.LANGUAGE_CODE).get(id=plan_id)
        except:
            our_plan_obj = None
        if our_plan_obj and our_plan_obj.plan_name == "Community":
            result['discount'] = discount
        elif coupon_code:
            if our_plan_obj.plan_name == "Premium":
                coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"), Q(discount_type="Percentage"))
            elif our_plan_obj.plan_name == "Elite":
                coupon_obj = Coupon.active_objects.get(Q(code__iexact=coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"), Q(discount_type="Percentage"))
            # coupon_obj = Coupon.active_objects.get(code=coupon_code)
            if coupon_obj:
                discount_type = coupon_obj.discount_type
                discount = float(coupon_obj.discount_value)
                result['discount'] = discount
                result['name'] = coupon_obj.name
                result['code'] = coupon_obj.code
                if 'percent' in discount_type.lower():
                    result['is_discount_percent'] = True
                else:
                    result['is_discount_percent'] = False
                result['is_futurelab_or_company_discount_applied'] = False
        elif student and student.discount_coupon_code:
            local_tz = pytz.timezone(settings.TIME_ZONE)
            dt_now = local_tz.localize(datetime.datetime.now())
            try:
                if our_plan_obj.plan_name == "Premium":
                    coupon_obj = Coupon.objects.get(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(code__iexact=student.discount_coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"), Q(discount_type="Percentage"))
                    #coupon_obj = Coupon.futurelab_company_objects.get(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(code__iexact=student.discount_coupon_code), Q(plan_type="Premium") | Q(plan_type="Master"))
                elif our_plan_obj.plan_name == "Elite":
                    coupon_obj = Coupon.objects.get(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(code__iexact=student.discount_coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"), Q(discount_type="Percentage"))
                    #coupon_obj = Coupon.futurelab_company_objects.get(Q(start_date__lte= dt_now), Q(end_date__gte= dt_now), Q(code__iexact=student.discount_coupon_code), Q(plan_type="Elite") | Q(plan_type="Master"))
            except:
                print("Coupon Object not found")
            if coupon_obj:
                discount_type = coupon_obj.discount_type
                discount = float(coupon_obj.discount_value)
                result['discount'] = discount
                result['name'] = coupon_obj.name
                result['code'] = coupon_obj.code
                if 'percent' in discount_type.lower():
                    result['is_discount_percent'] = True
                else:
                    result['is_discount_percent'] = False
                    
                if discount > 0:
                    result['is_futurelab_or_company_discount_applied'] = True
            else:
                result['is_futurelab_or_company_coupon_expired_or_inactive'] = True
                result['code'] = student.discount_coupon_code
        else:
            result['coupon_found'] = False
    except Exception as error:
        result['coupon_found'] = False
    finally:
        return result

def calculate_tax_and_price(request,total):
    all_taxes=None
    tax_result = {}
    try:
        if request.LANGUAGE_CODE == 'en-us':
            all_taxes = Tax.objects.filter(tax_country='USA', is_active=True)
        elif request.LANGUAGE_CODE == 'it':
            all_taxes = Tax.objects.filter(tax_country='Italy', is_active=True)
        if all_taxes.count()>0:
            print(f"In tax {all_taxes.count()}")
            tax_result['tax_isactive'] = True
            tax_result['all_taxes']=all_taxes
            amount_tax = 0
            for tax in all_taxes:
                amount_tax = amount_tax + tax.cal_tax_amount(total)
                
            tax_result["amount_after_tax"] = round(total + amount_tax, 2)
            tax_result["total_tax_amount"] = amount_tax
        else:
            print(f"No tax {all_taxes.count()}")
            tax_result['tax_isactive'] = False
            tax_result['all_taxes']=all_taxes
            tax_result["amount_after_tax"] = total
            tax_result["total_tax_amount"] = 0

    except Exception as error:
        print(error)
        tax_result['tax_isactive'] = False
        tax_result["amount_after_tax"] = total
        tax_result["total_tax_amount"] = 0
    finally:
        return tax_result

def calculate_discount_and_final_price(total, discount_value, is_discount_percentage):
    if is_discount_percentage:
        final_discount = total * discount_value/100
        final_discount = round(final_discount, 2)
        return final_discount, round(total - final_discount,2)
    else:
        return discount_value, round(total - discount_value,2)





def create_custom_event_for_celery_task(id, ip_address, user_agent, influencer, page_url, custom_user_session_id, event_id=None, meta_data={}):
    try:
        person = PERSON.objects.filter(id=id).first()
        if event_id:
            meta_data['influencer'] = influencer
            
            if not custom_user_session_id:
                custom_user_session_id = custom_user_session_id
            event_name = ""
            for e_name in EVENT_NAMES:
                if e_name[0] == event_id:
                    event_name = e_name[1]
            if user_agent != "ELB-HealthChecker/2.0" or user_agent != None:
                if person:
                    CustomEvent.objects.create(person=person, event_id=event_id, event_name=event_name, user_agent=user_agent, page_url=page_url, ip_address=ip_address, custom_user_session_id=custom_user_session_id, meta_data=meta_data)
                    logger.info(f"Custom event '{event_name}' cretaed successfully by : {person.username}")
                else:
                    CustomEvent.objects.create(event_id=event_id, event_name=event_name, user_agent=user_agent, page_url=page_url, ip_address=ip_address, custom_user_session_id=custom_user_session_id, meta_data=meta_data)
                    logger.info(f"Custom event '{event_name}' cretaed successfully by : {custom_user_session_id}")
    except Exception as e:
        if(person):
            logger.error(f"Error('{e}') to create event at create_custom_event_for_celery_task , and username is : {person.username}")
        else:
            custom_user_session_id = custom_user_session_id
            logger.error(f"Error('{e}') to create event at create_custom_event_for_celery_task, and session id  : {custom_user_session_id}")
        
