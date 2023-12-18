from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from .urls import urlpatterns


class WebsiteTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_views(self):
        EXCLUDE_VIEWS = ['lets-talk-send-message','index']
        # try:
        #     for single_url_pattern in urlpatterns:
        #         if single_url_pattern.name not in EXCLUDE_VIEWS:
        #             request = self.factory.get(reverse(single_url_pattern.name))
        #             middleware = SessionMiddleware()
        #             middleware.process_request(request)
        #             request.LANGUAGE_CODE = 'it'
        #             request.session.save()
        #             request.user = AnonymousUser()
        #             response = single_url_pattern.callback(request)
        #             self.assertIn(response.status_code, [200, 302, 405])
        # except Exception as e:
        #     print("Error", e)
