from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from .urls import urlpatterns
from userauth.models import Person


class StudentTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Person.objects.create_user(
            username='test_user', email='test_user@myfuturely.com', password='Abc@123456')

    def test_views(self):
        EXCLUDE_VIEWS = ['courses-overview', 'courses-available', 'module-steps', 'action-items', 'submit_answer','trail-plan-activate','account-settings','account-settings-counselor',
                         'post_detail', 'buy-course', 'add_todo', 'get_todo', 'update_todo', 'delete_todo', 'contact_tutor', 'courses-multiple', 'buy-plan', 'upgrade-plan','update_futurelab_form_status']
        # try:
        #     for single_url_pattern in urlpatterns:
        #         try:
        #             if single_url_pattern.name not in EXCLUDE_VIEWS:
        #                 #print(single_url_pattern.name)
        #                 request = self.factory.get(
        #                     reverse(single_url_pattern.name))
        #                 middleware = SessionMiddleware()
        #                 middleware.process_request(request)
        #                 request.LANGUAGE_CODE = 'it'
        #                 request.session.save()
        #                 request.user = self.user
        #                 # request.user = AnonymousUser()
                        
        #                 response = single_url_pattern.callback(request)
        #                 self.assertIn(response.status_code, [200, 302, 405])
        #         except Exception as ex:
        #             print("Error", ex)
        # except Exception as e:
        #     print("Error", e)
