"""thefuturely URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import copy

from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler403, url
from django.views.static import serve

# Add internationalization paths here
urlpatterns = [
    # Add italian URLs here
    path('it/',include("website.urls")),
    path('it/',include("userauth.urls")),
    path('it/',include("student.urls")),
    path('it/',include("payment.urls")),
    path('it/',include("courses.urls")),
    path('it/',include("counselor.urls")),
    path('it/',include("futurely_admin.urls")),
    path('it/',include("unipegaso.urls")),
    path('it/',include("landing_website.urls")),
    path('it/',include("new_userauth.urls")),
    path('it/',include("ifoa.urls")),
    path('it/',include("quiz_app.urls")),


    # Add English URLs here
    path('en/',include("website.urls")),
    path('en/',include("userauth.urls")),
    path('en/',include("student.urls")),
    path('en/',include("payment.urls")),
    path('en/',include("courses.urls")),
    path('en/',include("counselor.urls")),
    path('en/',include("futurely_admin.urls")),
    path('en/',include("unipegaso.urls")),
    path('en/',include("landing_website.urls")),
    path('en/',include("new_userauth.urls")),
    path('en/',include("ifoa.urls")),
    path('en/',include("quiz_app.urls")),

]

urlpatterns += [
    path('admin/', admin.site.urls, name='admin'),
    path('', include("userauth.urls")),
    path('',include("student.urls")),
    path('',include("payment.urls")),
    path('',include("website.urls")),
    path('',include("courses.urls")),
    path('counselor/',include("counselor.urls")),
    path('futurely_admin/',include("futurely_admin.urls")),
    path('', include("unipegaso.urls")),
    url(r'^download/(?P<path>.*)$',serve,{'document_root':settings.MEDIA_ROOT}),
    path('',include("landing_website.urls")),
    path('',include("new_userauth.urls")),
    path('',include("ifoa.urls")),
    path('',include("quiz_app.urls")),

]

handler404 = "website.views.page_not_found_404_view"

if settings.DEBUG:
    #urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         url(r'^__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns
