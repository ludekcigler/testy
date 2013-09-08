# -*- coding: utf-8 -*-
import datetime
import decorator
import time
import urllib

from django.core.exceptions import ObjectDoesNotExist
from django.core import urlresolvers
from django import http 
from django.template import loader, Context, RequestContext
from django.views.decorators.cache import cache_control, never_cache
import django.contrib.auth
import django.shortcuts

import testy.models
import testy.forms

ERROR_TEST_NOT_FOUND_TITLE = u'Test nenalezen'
ERROR_TEST_NOT_FOUND_DESC = u'Bohužel Vámi zadaná adresa neodpovídá žádnému testu v databázi.'
ERROR_TEST_NOT_FOUND_TITLE = u'Řešení nenalezeno'
ERROR_TEST_NOT_FOUND_DESC = u'Bohužel Vámi zadaná adresa neodpovídá žádnému řešení v databázi.'
ERROR_TEST_FORM_MISSING_DATA = u'Prosím, zadejte vaše osobní údaje.'
ERROR_BAD_LOGIN = u'Zadali jste špatné uživatelské jméno nebo heslo.'

@decorator.decorator
def login_required(view, *args, **kwargs):
    if kwargs.has_key('request'):
        request = kwargs['request']
    else:
        request = args[0]

    continue_url = urllib.quote(request.META['PATH_INFO'])
    if not request.user or not request.user.is_authenticated():
        return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.user_login') + ('?continue=%s' % continue_url))
    else:
        return view(*args, **kwargs)

@login_required
def index(request):
    return test_display_all(request)

@login_required
def user_logout(request):
    # Logout the user
    django.contrib.auth.logout(request)
    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.user_login'))

def user_login(request):
    # Display the login form or login the user in case it has been successful
    context = {}
    if request.POST.has_key('username') and request.POST.has_key('password'):
        username = request.POST['username']
        password = request.POST['password']
        # Try to authenticate the user
        user = django.contrib.auth.authenticate(username=username, password=password)
    
        if user is not None and user.is_active:
            django.contrib.auth.login(request, user)
            if request.POST.has_key('continue'):
                return http.HttpResponseRedirect(request.POST['continue'])
            else:
               return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.index'))
        else:
            context['error_message'] = ERROR_BAD_LOGIN

    t = loader.get_template('testy/login.html')
    if request.GET.has_key('continue'):
        context['continue_url'] = request.GET['continue']

    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))

@never_cache
@login_required
def test_display_all(request):
    # Display all tests created by a particular user
    tests = testy.models.Test.objects.filter(author=request.user, deleted=False)

    context = {'tests': tests}
    t = loader.get_template('testy/seznam_testu.html')
    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))

def test_display(request, test_url):
    # Display the form to submit solve a single test specified by the URL
    
    # Find the test object by URL
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    template = loader.get_template('testy/test.html')
    context = {'test': test}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

def test_display_bis(request, test_url):
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    template = loader.get_template('testy/test_bis.html')
    form = testy.forms.TestForm(test=test)
    c = RequestContext(request, {'test': test, 'test_form': form})
    return http.HttpResponse(template.render(c))
    

@login_required
def test_edit(request, test_url, error=None):
    # Display a form to edit the test
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    template = loader.get_template('testy/test_form.html')
    context = {'test': test, 'error': error, 'title': 'Upravit test'}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

@login_required
def test_delete(request, test_url):
    # Move the test to trash
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    test.deleted = True
    test.save()

    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.index'))

@login_required
def test_edit_submit(request, test_url):
    # Submit the edited test, then redirect to list of all tests
    
    # How to update the test:
    # - edit the corresponding test object
    # - delete all questions and corresponding responses, restore them from the form again

    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    test.title = request.POST['title']
    test.desc = request.POST['desc']
    test.exercise = True if request.POST.get("test_type") == "exercise" else False
    test.save()
    
    numQuestions = int(request.POST['num_questions'])
    # List of questions which remained after editing
    questionsRemaining = []
    for q_idx in xrange(1, numQuestions+1):
        v = request.POST['q%d_id' % q_idx]
        if len(v) > 0:
            questionsRemaining.append(int(v))

    delete_old_solutions = False
    # Remove the questions which have been removed
    for q in test.question_set.all():
        if not q.id in questionsRemaining:
            q.delete()
            delete_old_solutions = True

    # Remove old solutions to this test (they don't make sense now that we have changed the questions
    # (Only if the set of questions changed)

    delete_old_solutions = questions_add(request, test) or delete_old_solutions

    if delete_old_solutions:
        for ta in test.testanswer_set.all():
            ta.delete()

    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.index'))

@login_required
def test_add(request):
    # Display an empty form for a new test

    error = None
    template = loader.get_template('testy/test_form_add.html')
    context = {'error': error, 'title': 'Přidat test'}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

@login_required
def test_add_submit(request):
    # Create a new test and redirect to the list of all tests
    test = testy.models.Test(author=request.user)
    test.title = request.POST['title']
    test.desc = request.POST['desc']
    test.exercise = True if request.POST.get("test_type") == "exercise" else False
    test.save()

    questions_add(request, test)

    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.index'))

def questions_add(request, test):
    # Returns true if the test has changed. How do we know? There are new questions or responses
    test_changed = False

    numQuestions = int(request.POST['num_questions'])
    
    for q_idx in xrange(1, numQuestions+1):
        id = request.POST['q%d_id' % q_idx]
        numResponses = int(request.POST['q%d_num_responses' % q_idx])
        if id:
            # Update question with a given ID
            q = testy.models.Question.objects.get(id=id)
            q.text = request.POST['q%d' % q_idx]
            if request.POST.get('q%d-deleteimage' % q_idx, False):
                q.image = None
            elif request.FILES.has_key('q%d-image' % q_idx):
                q.image = request.FILES['q%d-image' % q_idx]

            q.multiple_answers = request.POST.get('q%d-multiplechoice' % q_idx, False)
            q.order = q_idx
            # Remove the question responses which are not present in the current set
            responsesRemaining = []
            for r_idx in xrange(1, numResponses+1):
                v = request.POST['q%d-r%d_id' % (q_idx, r_idx)]
                if len(v) > 0:
                    responsesRemaining.append(int(v))
            for r in q.questionresponse_set.all():
                if not r.id in responsesRemaining:
                    r.delete()
                    test_changed = True
            q.save()
        else:
            test_changed = True
            # Create a new question and attach it to the test
            q = testy.models.Question(test=test, text=request.POST['q%d' % q_idx], multiple_answers=request.POST.get('q%d-multiplechoice' % q_idx, False), order=q_idx)
            if request.FILES.has_key('q%d-image' % q_idx):
                q.image = request.FILES['q%d-image' % q_idx]
            q.save()

        # Load all the responses from the form
        for r_idx in xrange(1, numResponses+1):
            r_id = request.POST['q%d-r%d_id' % (q_idx, r_idx)]
            if r_id:
                r = testy.models.QuestionResponse.objects.get(id=r_id)
            else:
                test_changed = True
                r = testy.models.QuestionResponse(question=q)

            r.text = request.POST['q%d-r%d' % (q_idx, r_idx)]
            r.order = r_idx
            if q.multiple_answers:
                r.correct = request.POST.get('q%d-r%d-correct' % (q_idx, r_idx), False)
            else:
                if int(request.POST.get('q%d-correct' % q_idx, 1)) == r_idx:
                    r.correct = True
                else:
                    r.correct = False

            r.save()
            q.questionresponse_set.add(r)

    return test_changed

def solution_submit(request, test_url):
    # Submit a single solution to a test given by test_url
    # If the test is an exercise, display the corrected test straight away.
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    # Check if the personal info is there, if not reject. Otherwise, save this.
    check_fields = ['first_name', 'last_name', 'email']
    for f in check_fields:
        if not request.POST.has_key(f):
            # TODO: Display the sumitted solution instead (maybe we should use Django forms?)
            return test_display(request, test_url, error=ERROR_TEST_FORM_MISSING_DATA)

    # Create a new TestAnswer object and save
    test_answer = testy.models.TestAnswer(test=test, score=0.0, first_name=request.POST['first_name'], last_name=request.POST['last_name'], email=request.POST['email'])
    test_answer.save()
    num_questions = len(test.question_set.all())
    
    for q_idx, q in enumerate(test.question_set.all()):
        # Create a new questionAnswer object, and save the responses there
        q_answer = testy.models.QuestionAnswer(test_answer=test_answer, question=q)
        q_answer.save()

        if q.multiple_answers:
            selected_responses = [r for r_idx, r in enumerate(q.questionresponse_set.all()) if request.POST.get("q%d-r%d" % (q_idx+1, r_idx+1), False)]
        else:
            if request.POST.has_key("q%s" % (q_idx+1)):
                selected_responses = [q.questionresponse_set.all()[int(request.POST.get("q%s" % (q_idx+1), 1))-1]]
            else:
                selected_responses = []

        for r in selected_responses:
            q_answer.responses.add(r)

        q_answer.save()

    if test.exercise:
        return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.solution_display', args=(test_url, test_answer.id)))
    else:
        t = loader.get_template('testy/test_pisemka_odeslan.html')
        c = RequestContext(request, {})
        return http.HttpResponse(t.render(c))

@login_required
def solution_display(request, test_url, solution_id):
    # Display the corrected solution
    try:
        test = testy.models.Test.get_test_by_url(test_url)
        solution = testy.models.TestAnswer.objects.get(id=solution_id)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, SOLUTION_NOT_FOUND_TITLE, SOLUTION_NOT_FOUND_DESC))

    template = loader.get_template('testy/vyhodnoceni.html')
    context = {'test_answer': solution}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

@never_cache
@login_required
def solution_delete(request, test_url, solution_id):
    ta = testy.models.TestAnswer(id=solution_id)

    ta.delete()

    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.solution_display_all', args=(test_url,)))


@never_cache
@login_required
def solution_display_all(request, test_url):
    # Display all solutions for a given test
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    template = loader.get_template('testy/seznam_reseni.html')
    context = {'test': test}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

def error_display(request, error_title, error_desc):
    c = RequestContext(request, {'error_desc': error_desc, 'error_title': error_title})
    t = loader.get_template('testy/error.html')
    return t.render(c)

