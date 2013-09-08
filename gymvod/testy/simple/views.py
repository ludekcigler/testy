# -*- coding: UTF-8 -*-

from django import http 
from django.contrib.auth.models import User
from django.template import loader, Context, RequestContext
from django.shortcuts import get_object_or_404, render

def list_all_users(request):
    return list_users(request, User.objects.all(), u'Všichni uživatelé')

def list_students(request):
    return list_users(request, User.objects.filter(groups__name = 'Students'), u'Studenti')

def list_users(request, aUserList, aTitle):
    data = {'users': aUserList, 'title': aTitle}
    t = loader.get_template('testy/simple/list_users.html')
    c = RequestContext(request, data)
    return http.HttpResponse(t.render(c))
    

def user_details(request, aUserName):
    u = get_object_or_404(User, username=aUserName)
    t = loader.get_template('testy/simple/user_details.html')
    data = {'user': u}
    c = RequestContext(request, data)
    return http.HttpResponse(t.render(c))        
