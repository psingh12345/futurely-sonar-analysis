from lib2to3.pgen2 import driver
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
import html5lib
from .urls import urlpatterns
from .models import Person, Student, CountryDetails, School, ClassYear, Counselor
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.chrome.options import Options
from courses.models import OurPlans, step_status
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from payment.models import Coupon, Tax
from datetime import datetime, timedelta
from django.conf import settings
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import string, random, time, requests, pytz, json
from django.contrib.auth import authenticate, get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from userauth.userauthtestcase.userauth_test import UserTestCases, UserPaymentTestCases, CounselorTestCase
import logging
import os

# class UserAuthTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#         self.user = Person.objects.create_user(username='test_user', email='test_user@myfuturely.com', password='Abc@123456')

#     def test_views(self):
#         EXCLUDE_VIEWS = ['email_activate','password_reset', 'password_reset_confirm','get-school-by-name','get-school-cities-name','get-school-name-by-city','counselor_login','check_email','coupon-code-exists','logout','login','verify_email']
#         try:
#             for single_url_pattern in urlpatterns:
#                 if single_url_pattern.name not in EXCLUDE_VIEWS:
#                     request = self.factory.get(reverse(single_url_pattern.name))
#                     middleware = SessionMiddleware()
#                     middleware.process_request(request)
#                     request.LANGUAGE_CODE = 'it'
#                     request.session.save()
#                     request.user = self.user
#                     # request.user = AnonymousUser()

#                     response = single_url_pattern.callback(request)
#                     self.assertIn(response.status_code, [200, 302, 405])
#         except Exception as e:
#             print("Error", e)


class UserAuthTestWithSelenium(StaticLiveServerTestCase):
    fixtures = ['ourplan.json', 'course.json']

    def setUp(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument('--incognito')
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['goog:loggingPrefs'] = {'performance': 'ALL'} 
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options, desired_capabilities=capabilities)
        self.driver.maximize_window()
        self.client = Client(HTTP_USER_AGENT='Mozilla/5.0')
        self.factory = RequestFactory()
        print("SetUp called \n")
        return super(UserAuthTestWithSelenium, self).setUp()

    def tearDown(self):
        self.driver.quit()
        print("TearDown called \n")
        return super(UserAuthTestWithSelenium, self).tearDown()

    def test_a_login_and_registration_case(self):
        self.email = "dummy@gmail.com"
        self.password = "Test@1234"
        self.first_name = "test"
        self.last_name = "user"
        self.email_verified = False
        self.contact_number = str(random.randint(9000000000, 10000000000))
        self.how_know_us = "Instagram"
        self.gender = "Male"

        #User Registeration with exact values.
        # user_register = UserTestCases(client=self.client, live_server_url=self.live_server_url, driver=self.driver, email=self.email, password=self.password, first_name=self.first_name, last_name=self.last_name, contact_number=self.contact_number, gender=self.gender, assertTrue=self.assertTrue)
        UserTestCases.test_registration_with_correct_values(obj=self)
        time.sleep(1)
        UserTestCases.test_registration_with_invalid_email_id(obj=self)
        time.sleep(1)
        UserTestCases.test_registration_valid_coupon_code(obj=self)
        time.sleep(1)
        UserTestCases.test_registration_invalid_coupon_code(obj=self)
        time.sleep(1)
        UserTestCases.test_login_with_correct_credentials(obj=self)
        time.sleep(1)
        UserTestCases.test_login_with_wrong_cred(obj=self)
        time.sleep(1)
        UserTestCases.test_registration_email_already_exists(obj=self)
        time.sleep(1)
        UserTestCases.test_registration_are_you_fourteen_plus(obj=self)
        time.sleep(1)
        UserTestCases.test_reset_password(obj=self)
        UserTestCases.test_reset_password_with_wrong_email(obj=self)
    
    def test_b_counselor_login_and_registration_case(self):
        self.email = "dummycounselor@gmail.com"
        self.password = "Test@1234"
        self.first_name = "test"
        self.last_name = "user"
        self.email_verified = False
        self.contact_number = str(random.randint(9000000000, 10000000000))
        self.how_know_us = "Instagram"
        self.gender = "Male"
        #Counselor Registration
        CounselorTestCase.test_counselor_registration_with_correct_values(obj=self)
        time.sleep(1)
        CounselorTestCase.test_counselor_login(obj=self)
        time.sleep(1)
        CounselorTestCase.test_counselor_registration_with_email_already_exists(obj=self)
        time.sleep(1)
        # CounselorTestCase.test_counselor_login_with_wrong_email(obj=self)
        # time.sleep(1)
    
    def test_c_payment_with_coupon_code(self):
        self.email = "rohitkbti007@gmail.com"
        self.password = "Test@1234"
        self.first_name = "test"
        self.last_name = "user"
        self.email_verified = False
        self.contact_number = str(random.randint(9000000000, 10000000000))
        self.how_know_us = "Instagram"
        self.gender = "Male"
        self.coupon_code = "futu100"
        UserPaymentTestCases.test_user_payment_with_coupon_code(obj=self)
        time.sleep(1)