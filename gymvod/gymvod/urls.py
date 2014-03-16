# -*- coding: UTF-8 -*-
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from rest_framework import routers
import testy.api.views
import testy.simple.views

router = routers.DefaultRouter()
router.register(r'users', testy.api.views.UserViewSet)
router.register(r'groups', testy.api.views.GroupViewSet)
router.register(r'tests', testy.api.views.TestViewSet)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'gymvod.views.home', name='home'),
    # url(r'^gymvod/', include('gymvod.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    #url(r'^api/', include(router.urls)),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Simple HTML app
    #url(r'^testy/s/$', 'testy.simple.views.index'),
    #url(r'^testy/s/users/$', 'testy.simple.views.list_all_users'),
    #url(r'^testy/s/users/(?P<aUserName>\w{1,})/', 'testy.simple.views.user_details'),
    #url(r'^testy/s/students/$', 'testy.simple.views.list_students'),

    # Testy URLs
    url(r'^$', 'testy.views.index'),
    url(r'^testy/$', 'testy.views.index'),
    url(r'^testy/profil/$', 'testy.views.user_profile_edit'),
    url(r'^testy/profil/upravit/$', 'testy.views.user_profile_edit_submit'),
    url(r'^testy/login/$', 'testy.views.user_login'),
    url(r'^testy/logout/$', 'testy.views.user_logout'),
    url(r'^testy/novy/$', 'testy.views.test_add'),
    url(r'^testy/novy/odeslat/$', 'testy.views.test_add_submit'),
    url(r'^testy/nova-slozka/$', 'testy.views.folder_add'),
    url(r'^testy/nova-slozka/odeslat/$', 'testy.views.folder_add_submit'),
    url(r'^testy/slozka/(?P<folder_url>\w+)/$', 'testy.views.folder_display'),
    url(r'^testy/slozka/(?P<folder_url>\w+)/upravit/$', 'testy.views.folder_edit'),
    url(r'^testy/slozka/(?P<folder_url>\w+)/odeslat/$', 'testy.views.folder_edit_submit'),
    url(r'^testy/slozka/(?P<folder_url>\w+)/smazat/$', 'testy.views.folder_delete'),

    url(r'^test/(?P<test_url>\w+)/$', 'testy.views.test_display'),
    url(r'^test/(?P<test_url>\w+)/bis/$', 'testy.views.test_display_bis'),
    url(r'^test/(?P<test_url>\w+)/upravit/$', 'testy.views.test_edit'),
    url(r'^test/(?P<test_url>\w+)/smazat/$', 'testy.views.test_delete'),
    url(r'^test/(?P<test_url>\w+)/odeslat/$', 'testy.views.test_edit_submit'),
    url(r'^test/(?P<test_url>\w+)/odeslat_reseni/$', 'testy.views.solution_submit'),
    url(r'^test/(?P<test_url>\w+)/reseni/$', 'testy.views.solution_display_all'),
    url(r'^test/(?P<test_url>\w+)/reseni/(?P<solution_url>\w+)/$', 'testy.views.solution_display'),
    url(r'^test/(?P<test_url>\w+)/reseni/(?P<solution_url>\w+)/smazat/$', 'testy.views.solution_delete'),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

