from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse
from userauth.models import Person, Student, CountryDetails, School, ClassYear, Counselor
from datetime import datetime, timedelta
from payment.models import Coupon
from selenium.webdriver.support.ui import WebDriverWait, Select
from django.conf import settings
import string, random, time, requests, pytz, json
from selenium.webdriver.common.action_chains import ActionChains
import time
from django.core import mail
from bs4 import BeautifulSoup


def student_regitration_form_first_stage(obj):
    if obj is not None:
        obj.driver.find_element_by_name('first_name').send_keys("Test")
        obj.driver.find_element_by_name('last_name').send_keys("user")
        gender_element = obj.driver.find_element_by_id('id_gender')
        gender_dropdown = Select(gender_element)
        gender_dropdown.select_by_value("Male")
        fourteen_plus = obj.driver.find_element_by_id("id_are_you_fourteen_plus")
        fourteen_plus_dropdown = Select(fourteen_plus)
        fourteen_plus_dropdown.select_by_value("Yes")
        obj.driver.find_element_by_name("email").send_keys(obj.email)
        obj.driver.find_element_by_name("password").send_keys(obj.password)
        obj.driver.find_element_by_name("contact_number").send_keys("4512457845")
        know_element = obj.driver.find_element_by_id("id_how_know_us")
        element_know_us = Select(know_element)
        element_know_us.select_by_value("Google")
        time.sleep(5)
        obj.driver.find_element_by_xpath('//*[@id="btn_next"]').click()
        return True
    else:
        return False

def student_registration_form_second_stage(obj):
    if obj is not None:
        obj.driver.find_element_by_id('select2-id-school-region-container').click()
        obj.driver.find_element_by_class_name('select2-search__field').send_keys("Test Regionnnn")
        obj.driver.find_element_by_id('select2-id-school-region-results').click()
        time.sleep(5)
        obj.driver.find_element_by_id('select2-id-school-city-container').click()
        obj.driver.find_element_by_class_name('select2-search__field').send_keys("Test School City")
        obj.driver.find_element_by_id('select2-id-school-city-results').click()
        time.sleep(5)
        obj.driver.find_element_by_id('select2-id-school-name-container').click()
        obj.driver.find_element_by_class_name('select2-search__field').send_keys('Test Schoolll')
        obj.driver.find_element_by_id('select2-id-school-name-results').click()
        time.sleep(5)
        class_year_ele = obj.driver.find_element_by_id('id-class-year')
        class_year_ele_option = Select(class_year_ele)
        class_year_ele_option.select_by_index(0)
        time.sleep(5)
        checkbox_ele = obj.driver.find_element_by_css_selector("input.form-check-input")
        obj.driver.execute_script("arguments[0].click();", checkbox_ele)
        obj.driver.find_element_by_id("btn-submit").click()
        return True
    else:
        return False

def check_invalid_email(obj):
    if obj is not None:
        obj.driver.find_element_by_name('first_name').send_keys("Test")
        obj.driver.find_element_by_name('last_name').send_keys("user")
        gender_element = obj.driver.find_element_by_id('id_gender')
        gender_dropdown = Select(gender_element)
        gender_dropdown.select_by_value("Male")
        fourteen_plus = obj.driver.find_element_by_id("id_are_you_fourteen_plus")
        fourteen_plus_dropdown = Select(fourteen_plus)
        fourteen_plus_dropdown.select_by_value("Yes")
        obj.driver.find_element_by_name("email").send_keys("invalidEmailID@in")
        obj.driver.find_element_by_name("password").send_keys(obj.password)
        obj.driver.find_element_by_name("contact_number").send_keys("4512457845")
        know_element = obj.driver.find_element_by_id("id_how_know_us")
        element_know_us = Select(know_element)
        element_know_us.select_by_value("Google")
        time.sleep(5)
        obj.driver.find_element_by_xpath('//*[@id="btn_next"]').click()
        return True
    else:
        return False

class UserTestCases:

    def test_registration_with_correct_values(obj):
        print('============== Start Test Registration ====================')
        sch_created = create_school_details(obj)
        obj.assertTrue(sch_created)
        create_coupon_code(obj)
        obj.driver.get(obj.live_server_url + reverse('register') + "?lang=en")
        delay_fun()
        first_stage_response = student_regitration_form_first_stage(obj)
        obj.assertTrue(first_stage_response)
        delay_fun()
        print('============== Test registration first stage is OK ====================')
        print('============== Test registration stage 2 start ====================')
        second_stage_response = student_registration_form_second_stage(obj)
        obj.assertTrue(second_stage_response)
        delay_fun()
        plans = obj.driver.find_elements_by_class_name("btn-buy-btn")
        obj.driver.execute_script("arguments[0].click();", plans[0])
        print('---------------------------------logs-----------------------------------')
        logs = obj.driver.get_log('performance')
        for log in logs:
            if log['message']:
                d = json.loads(log['message'])
                if d['message'].get('method') == "Network.responseReceived":
                    print(d['message']['params']['response']['status'])
        obj.assertTrue(obj.driver.page_source.__contains__('Logout'))
        print('============== Test Registration is OK ====================')

    def test_registration_with_invalid_email_id(obj):
        print('============== Start Test Registration start with invalid email ID ====================')
        obj.driver.get(obj.live_server_url + reverse('logout') + "?lang=en")
        delay_fun()
        obj.driver.get(obj.live_server_url + reverse('register') + "?lang=en")
        delay_fun()
        first_stage_response = check_invalid_email(obj)
        obj.assertTrue(first_stage_response)
        delay_fun()
        obj.assertTrue(obj.driver.page_source.__contains__('Enter a valid email address.'))
        print('============== Start Test Registration is Ok with invalid email ID ====================')

    def test_registration_valid_coupon_code(obj):
        user_obj = Person.objects.filter(username=obj.email).first()
        user_obj.delete()
        print('============== Start Test Registration with valid coupon code ====================')
        obj.driver.get(obj.live_server_url + reverse('register') + "?lang=en")
        delay_fun()
        first_stage_response = student_regitration_form_first_stage(obj)
        obj.assertTrue(first_stage_response)
        delay_fun()
        print('============== Test registration first stage is OK ====================')
        print('============== Test registration stage 2 started ====================')
        obj.driver.find_element_by_id('id_discount_coupon_code').send_keys("futu50")
        delay_fun()
        second_stage_response = student_registration_form_second_stage(obj)
        obj.assertTrue(second_stage_response)
        delay_fun()
        plans = obj.driver.find_elements_by_class_name("btn-buy-btn")
        obj.driver.execute_script("arguments[0].click();", plans[0])
        logs = obj.driver.get_log('performance')
        for log in logs:
            if log['message']:
                d = json.loads(log['message'])
                if d['message'].get('method') == "Network.responseReceived":
                    print(d['message']['params']['response']['status'])
        obj.assertTrue(obj.driver.page_source.__contains__('Logout'))
        print('============== Test Registration with valid coupon code is OK ====================')

    def test_registration_invalid_coupon_code(obj):
        user_obj = Person.objects.filter(username=obj.email).first()
        user_obj.delete()
        is_registered = False
        obj.driver.get(obj.live_server_url + reverse('register') + "?lang=en")
        delay_fun()
        first_stage_response = student_regitration_form_first_stage(obj)
        obj.assertTrue(first_stage_response)
        delay_fun()
        print('============== Test registration first stage is OK ====================')
        print('============== Test registration stage 2 started ====================')
        obj.driver.find_element_by_id('id_discount_coupon_code').send_keys("NONECOUCPONCODE")
        delay_fun()
        # obj.assertTrue(obj.driver.page_source.__contains__('Invalid discount code'))
        second_stage_response = student_registration_form_second_stage(obj)
        obj.assertTrue(second_stage_response)
        delay_fun()
        plans = obj.driver.find_elements_by_class_name("btn-buy-btn")
        obj.driver.execute_script("arguments[0].click();", plans[0])
        print('---------------------------------logs-----------------------------------')
        logs = obj.driver.get_log('performance')
        for log in logs:
                if log['message']:
                    d = json.loads(log['message'])
                    if d['message'].get('method') == "Network.responseReceived":
                        print(d['message']['params']['response']['status'])
        obj.assertTrue(obj.driver.page_source.__contains__('Logout'))
        print('============== Test Registration with valid coupon code is OK ====================')


    def test_login_with_correct_credentials(obj):
        Person = get_user_model()
        obj.user = authenticate(username=obj.email, password=obj.password)
        if obj.user is not None:
            obj.user = Person.objects.get(username=obj.email)
            obj.login = obj.client.login(username=obj.email, password=obj.password)
            obj.driver.get(obj.live_server_url + reverse('logout') + "?lang=en")
            delay_fun()
            obj.driver.get(obj.live_server_url + reverse('login') + "?lang=en")
            delay_fun()
            obj.assertTrue(obj.driver.page_source.__contains__('Sign in to Futurely'))
            login_reponse = login_form(obj)
            obj.assertTrue(login_reponse)
            delay_fun()
            obj.assertTrue(obj.driver.page_source.__contains__('Logout'))
            print('============== Test Login OK ====================')

    def test_login_with_wrong_cred(obj):
        print('============== Test Login with wrong credentials ====================')
        obj.driver.get(obj.live_server_url + reverse('logout') + "?lang=en")
        delay_fun()
        obj.driver.get(obj.live_server_url + reverse('login') + "?lang=en")
        delay_fun()
        obj.assertTrue(obj.driver.page_source.__contains__('Sign in to Futurely'))
        email = obj.driver.find_element_by_name("username")
        email.send_keys("testwithwrong@gmail.com")
        password = obj.driver.find_element_by_name("password")
        password.send_keys(obj.password)
        obj.driver.find_element_by_class_name('sign-btn').click() # login-button
        obj.assertTrue(obj.driver.page_source.__contains__('Login failed: Invalid username or password'))
        delay_fun()
        print('============== Test Login wrong credential is OK ====================')
    
    def test_registration_email_already_exists(obj):
        print('============== Start Test Registration with valid coupon code ====================')
        obj.driver.get(obj.live_server_url + reverse('register') + "?lang=en")
        delay_fun()
        first_stage_response = student_regitration_form_first_stage(obj)
        obj.assertTrue(first_stage_response)
        delay_fun()
        obj.assertTrue(obj.driver.page_source.__contains__('The email already exists in the system'))

    def test_registration_are_you_fourteen_plus(obj):
        obj.driver.get(obj.live_server_url + reverse('register') + "?lang=en")
        delay_fun()
        obj.driver.find_element_by_name('first_name').send_keys("Test")
        obj.driver.find_element_by_name('last_name').send_keys("user")
        gender_element = obj.driver.find_element_by_id('id_gender')
        gender_dropdown = Select(gender_element)
        gender_dropdown.select_by_value("Male")
        fourteen_plus = obj.driver.find_element_by_id("id_are_you_fourteen_plus")
        fourteen_plus_dropdown = Select(fourteen_plus)
        fourteen_plus_dropdown.select_by_value("No")
        delay_fun()
        obj.assertTrue(obj.driver.page_source.__contains__('Our program is intended only for high school students who are 14 and above. Soon, we will add our experience for everyone. Please check back in some time.'))

    def test_reset_password(obj):
        response = obj.client.get(reverse('password_reset') + "?lang=en")
        obj.assertEqual(response.status_code, 200)
        response = obj.client.post(reverse('password_reset') + "?lang=en", {'email':obj.email})
        obj.assertEqual(response.status_code, 302)
        obj.assertEqual(mail.outbox[3].subject, 'Password reset requested')
        msg = mail.outbox[3]
        # print(msg.body)
        email_html = BeautifulSoup(msg.body,'html.parser')#make email_html that is parse-able by bs
        link=email_html.a['href']        
        url=link.split("/")
        uid=url[4]
        token=url[5]
        response = obj.client.get(reverse('password_reset_confirm', kwargs={'uidb64':uid, 'token':token})+ "?lang=en")
        obj.assertEqual(response.status_code, 302)
        obj.new_password='Test@1234'
        password_page_response = obj.client.post(response.url,{'new_password1':obj.new_password,'new_password2':obj.new_password})
        obj.assertEqual(password_page_response.status_code, 302)
        obj.user = authenticate(username=obj.email, password=obj.new_password)
        obj.assertIsNotNone(obj.user)
        print('============== Test Reset Password is OK ====================')

    def test_reset_password_with_wrong_email(obj):
        response = obj.client.get(reverse('password_reset') + "?lang=en")
        obj.assertEqual(response.status_code, 200)
        response = obj.client.post(reverse('password_reset') + "?lang=en", {'email':"wrongemail@gmail.com"})
        obj.assertEqual(response.status_code, 200)


class CounselorTestCase:

    def test_counselor_registration_with_correct_values(obj):
        print('============== Start Test Counselor Registration ====================')
        create_school_details(obj)
        obj.driver.get(obj.live_server_url + reverse('counselor_registration')+"?lang=en")
        delay_fun()
        current_url = user_authenticated(obj)
        print(current_url)
        obj.assertTrue(obj.driver.page_source.__contains__("Counselor Sign up for Futurely"))
        form_resp = counselor_regitration_form(obj)
        obj.assertTrue(form_resp)
        delay_fun()
        obj.assertEqual(len(mail.outbox), 1)
        obj.assertEqual(mail.outbox[0].subject, 'Futurely - Verify your email address')
        msg = mail.outbox[0]
        # print(msg.body)
        email_verify_link = BeautifulSoup(msg.body,'html.parser')
        link = email_verify_link.a['href']
        print(link)
        email_url = link.replace("https://", "http://") # we need to remove this code for production
        obj.driver.get(email_url)
        delay_fun()
        counselor = Counselor.objects.all()
        counselor_obj = counselor.first()
        counselor_obj.is_verified_by_futurely = True
        counselor_obj.save()
        print("============== The Email varification completed Ok ==================")
        obj.driver.get(obj.live_server_url + reverse("counselor-dashboard") + "?lang=en")
        print('============== Test Counselor Registration is Ok ====================')

    def test_counselor_registration_with_email_already_exists(obj):
        print("====== Test Start email already exist for Counselor =======")
        obj.driver.get(obj.live_server_url + reverse('logout'))
        delay_fun()
        obj.driver.get(obj.live_server_url + reverse('counselor_registration')+"?lang=en")
        delay_fun()
        obj.assertTrue(obj.driver.page_source.__contains__("Counselor Sign up for Futurely"))
        form_resp = counselor_regitration_form(obj)
        obj.assertTrue(form_resp)
        delay_fun()
        obj.assertTrue(obj.driver.page_source.__contains__("The email already exists in the system"))
        print("====== Test email already exist is Ok for Counselor =======")

    def test_counselor_login(obj):
        print('============== Start Test Counselor Login ====================')
        obj.driver.get(obj.live_server_url + reverse('logout'))
        delay_fun()
        obj.driver.get(obj.live_server_url + reverse('counselor_login') + "?lang=en")
        delay_fun()
        response = login_form(obj)
        obj.assertTrue(response)
        # obj.driver.find_element_by_name("username").send_keys(obj.email)
        # obj.driver.find_element_by_name("password").send_keys(obj.password)
        # delay_fun()
        # submit_btn = obj.driver.find_element_by_css_selector("button.sign-btn-next")
        # obj.driver.execute_script("arguments[0].click();", submit_btn)
        print("============= Counselor Login Successfully ===================")
        delay_fun()
        obj.assertTrue(obj.driver.page_source.__contains__("Student Records"))
        obj.user = authenticate(username=obj.email, password=obj.password)
        obj.assertIsNotNone(obj.user)

    # def test_counselor_login_with_wrong_email(obj):
    #     print('======= Start Test Counselor Login with wrong Email ID =======')
    #     obj.driver.get(obj.live_server_url + reverse('logout'))
    #     delay_fun()
    #     obj.driver.get(obj.live_server_url + reverse('counselor_login') + "?lang=en")
    #     delay_fun()
    #     response = login_form(obj)
    #     obj.assertTrue(response)
    #     # obj.driver.find_element_by_name("username").send_keys("wrongemail@gmail.com")
    #     # obj.driver.find_element_by_name("password").send_keys(obj.password)
    #     # delay_fun()
    #     # submit_btn = obj.driver.find_element_by_css_selector("button.sign-btn-next")
    #     # obj.driver.execute_script("arguments[0].click();", submit_btn)
    #     print("====== Counselor Login Successfully =======")
    #     delay_fun()
    #     obj.assertTrue(obj.driver.page_source.__contains__("Login failed: Invalid username or password"))


class UserPaymentTestCases:

    def test_user_payment_with_coupon_code(obj=None):
        PERSON = get_user_model()
        user_obj = PERSON.objects.filter(username=obj.email).first()
        create_coupon_code(obj)
        # Student.objects.create(person=user_obj, are_you_fourteen_plus="Yes")
        obj.driver.get(obj.live_server_url + reverse('logout'))
        delay_fun()
        obj.user = authenticate(username=obj.email, password=obj.password)
        if obj.user is not None:
            obj.driver.get(obj.live_server_url + reverse('login'))
            login_form(obj)
            delay_fun()
            elite_plan(obj)
            delay_fun()
            apply_coupon_code(obj)
            delay_fun()
            print('============== Test User Payment is OK ====================')
        else:
            print('============== Test User Payment is Not OK ====================')


def counselor_regitration_form(obj=None):
    if obj is not None:
        obj.driver.find_element_by_name('first_name').send_keys(obj.first_name)
        obj.driver.find_element_by_name('last_name').send_keys(obj.last_name)
        obj.driver.find_element_by_name('email').send_keys(obj.email)
        gender_element = obj.driver.find_element_by_id('id_gender')
        gender_drop = Select(gender_element)
        gender_drop.select_by_value("Male")
        delay_fun()
        obj.driver.find_element_by_name("password").send_keys(obj.password)
        obj.driver.find_element_by_id("id_contact_number").send_keys("1245124545")
        know_element = obj.driver.find_element_by_id("id_how_know_us")
        element_know_us = Select(know_element)
        element_know_us.select_by_value("Google")
        delay_fun()
        obj.driver.find_element_by_id('select2-id-school-region-container').click()
        obj.driver.find_element_by_class_name('select2-search__field').send_keys("Test Regionnnn")
        obj.driver.find_element_by_id('select2-id-school-region-results').click()
        delay_fun()
        obj.driver.find_element_by_id('select2-id-school-city-container').click()
        obj.driver.find_element_by_class_name('select2-search__field').send_keys("Test School City")
        obj.driver.find_element_by_class_name("select2-results__options").click()
        delay_fun()
        school_name_container = obj.driver.find_element_by_id('select2-id-school-name-container')
        action = ActionChains(obj.driver)
        action.click(on_element = school_name_container)
        action.perform()
        delay_fun()
        obj.driver.find_element_by_class_name('select2-search__field').send_keys('Test Schoolll')
        obj.driver.find_element_by_id('select2-id-school-name-results').click()
        delay_fun()
        submit_btn = obj.driver.find_element_by_css_selector("button.sign-btn-next")
        obj.driver.execute_script("arguments[0].click();", submit_btn)
        return True
    else:
        return False

def login_form(obj=None):
    if obj is not None:
        email = obj.driver.find_element_by_name("username")
        email.send_keys(obj.email)
        password = obj.driver.find_element_by_name("password")
        password.send_keys(obj.password)
        obj.driver.find_element_by_class_name('sign-btn').click() # login-button
        return True
    else:
        return  False

def delay_fun():
    time_of_second = random.randint(8,10)
    time.sleep(time_of_second)

def register_form(obj=None):
    pass

def apply_coupon_code(obj=None):
    if obj is not None:
        obj.driver.find_element_by_name('discount').send_keys("test100")
        time.sleep(2)
        obj.driver.find_element_by_id('apply-dis-btn').click()
        time.sleep(7)
        obj.driver.find_element_by_xpath('//*[@id="OrderSummaryForm"]/div[2]/input').click()
        time.sleep(7)
        return True
    else:
        return False

def premium_plan(obj=None):
    pass

def elite_plan(obj=None):
    if obj is not None:
        elite_plan_button = obj.driver.find_elements_by_class_name("btn-buy-btn")
        obj.driver.execute_script("arguments[0].click();", elite_plan_button[2])  
        return True
    else:
        return False

def create_coupon_code(obj=None):
    ### Bulk create Coupon code ###
    if obj is not None:
        a = datetime.now() + timedelta(2)
        time_zone = pytz.timezone(settings.TIME_ZONE)
        date_time = time_zone.localize(a)
        Coupon.objects.bulk_create([
            Coupon(code="test100", name="General discount", discount_type="Percentage", plan_type="Master", end_date=date_time, is_active=True, discount_value=100.0),
            Coupon(code="demo001", name="Future lab discount", discount_type="Percentage", end_date=date_time, is_active=True, discount_value=20.0),
            Coupon(code="futurely100", name="Future lab discount", discount_type="Percentage", end_date=date_time, is_active=True, discount_value=100.0),
        ])
        return True
    else:
        return False

def create_school_details(obj):
    if obj is not None:
        # Create country details data.
        CountryDetails.objects.bulk_create([
            CountryDetails(region="Test Regionnnn", city='Test School City', country="USA"),
            CountryDetails(region="VENETO", city='BELLUNO', country="USA"),
            CountryDetails(region="Test 1", city='Test 1 School City', country="USA"),
        ])
        # Create school Data.
        School.objects.bulk_create([
            School(name="Test Schoolll", region="Test Regionnnn", city="Test School City", type="Test School Typeeee", country="USA", is_verified=True),
            School(name="Test 1 Schoolll", region="Test 1 Regionnnn", city="Test 1 School City", type="Test 1 School Typeeee", country="USA", is_verified=True),
            ])

        # Create classYears data.
        ClassYear.objects.bulk_create([
            ClassYear(name="1st year", country="USA"),
            ClassYear(name="2nd year", country="USA"),
            ClassYear(name="3rd year", country="USA"),
        ])
        return True
    else:
        return False

def user_authenticated(obj=None):
    if obj is not None:
        current_path = obj.driver.current_url
        if "/counselor-registration/" in current_path:
            print("Counselor url for Registration")
            print(current_path)
            return current_path
        elif "/login/" in current_path:
            print("Student Login URL")
            print(current_path)
            return current_path
        elif "/register/" in current_path:
            print("Student registration URL")
            print(current_path)
            return current_path
        elif "/counselor-login/" in current_path:
            print("Counselor Login URL")
            print(current_path)
            return current_path
        else:
            return ""
    else:
        print("Error")
        return ""