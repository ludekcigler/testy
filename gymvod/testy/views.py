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
ERROR_FOLDER_NOT_FOUND_TITLE = u'Složka nenalezena'
ERROR_FOLDER_NOT_FOUND_DESC = u'Bohužel Vámi zadaná adresa neodpovídá žádné složce v databázi.'
ERROR_SOLUTION_NOT_FOUND_TITLE = u'Řešení nenalezeno'
ERROR_SOLUTION_NOT_FOUND_DESC = u'Bohužel Vámi zadaná adresa neodpovídá žádnému řešení v databázi.'
ERROR_TEST_FORM_MISSING_DATA = u'Prosím, zadejte vaše osobní údaje.'
ERROR_BAD_LOGIN = u'Zadali jste špatné uživatelské jméno nebo heslo.'
ERROR_TEST_NOT_EDITABLE_BY_USER_TITLE = u'Nedostatečné oprávnění'
ERROR_TEST_NOT_EDITABLE_BY_USER_DESC = u'K úpravě tohoto testu nemáte oprávnění. Test může upravovat jenom jeho autor.'
ERROR_USER_PROFILE_NOT_EDITABLE_TITLE = u'Přístup zakázán'
ERROR_USER_PROFILE_NOT_EDITABLE_DESC = u'Nemůžete upravovat cizí profil.'
ERROR_USER_PROFILE_NOT_FOUND_TITLE = u'Uživatel nenalezen'
ERROR_USER_PROFILE_NOT_FOUND_DESC = u'Vámi hledaný uživatel v systému neexistuje'
ERROR_PASSWORDS_DONT_MATCH_TITLE = u'Hesla nesouhlasí'
ERROR_PASSWORDS_DONT_MATCH_DESC = u'Vámi zadaná hesla nesouhlasí. Stiskněte tlačítko prohlížeče "Zpět" a dbejte na to, abyste zadali do obou políček stejné heslo.'

ERROR_USER_DOES_NOT_EXIST_TITLE = u'Uživatelské jméno neexistuje'
ERROR_USER_DOES_NOT_EXIST_DESC = u'Uživatel, kterému chcete test zkopírovat, neexistuje.'

ERROR_USER_DOES_NOT_EXIST_TITLE = u'Uživatelské jméno neexistuje'
ERROR_USER_DOES_NOT_EXIST_DESC = u'Uživatel, kterému chcete test zkopírovat, neexistuje.'
ERROR_FOLDER_NOT_FOUND_TITLE = u'Složka nebyla nalezena'
ERROR_FOLDER_NOT_FOUND_DESC = u'Složka kterou chcete zkopírovat neexistuje.'

ERROR_FOLDER_NOT_EDITABLE_BY_USER_TITLE = u'Přístup zakázán'
ERROR_FOLDER_NOT_EDITABLE_BY_USER_DESC = u'Nemáte právo kopírovat tuto složku.'

ERROR_TEST_DELETED_TITLE = u'Test byl smazán'
ERROR_TEST_DELETED_DESC = u'Omlouváme se, tento test byl smazán a už jej není možno vyplnit.'

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
    tests = testy.models.Test.objects.filter(author=request.user, deleted=False, folder=None)
    folders = testy.models.TestFolder.objects.filter(author=request.user, deleted=False)

    context = {'tests': tests,
        'folders': folders,
        'page_title': (u'Testy'),
        'page_header': (u'Seznam testů'),
        }
    t = loader.get_template('testy/seznam_testu.html')
    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))

def test_display(request, test_url, error=None):
    # Display the form to submit solve a single test specified by the URL

    # Find the test object by URL
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    if test.deleted:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_DELETED_TITLE, ERROR_TEST_DELETED_DESC))

    template = loader.get_template('testy/test.html')
    context = {'test': test, 'error': error}
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

    # Check if the test can be edited by the user
    if not test.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_TEST_NOT_EDITABLE_BY_USER_TITLE, ERROR_TEST_NOT_EDITABLE_BY_USER_DESC))

    folders = testy.models.TestFolder.objects.filter(author=request.user, deleted=False)

    template = loader.get_template('testy/test_form.html')
    context = {'test': test, 'error': error, 'title': 'Upravit test', 'folders': folders}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

@never_cache
@login_required
def test_delete(request, test_url):
    # Move the test to trash
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    if not test.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_TEST_NOT_EDITABLE_BY_USER_TITLE, ERROR_TEST_NOT_EDITABLE_BY_USER_DESC))

    test.deleted = True
    test.folder = None
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

    if not test.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_TEST_NOT_EDITABLE_BY_USER_TITLE, ERROR_TEST_NOT_EDITABLE_BY_USER_DESC))

    try:
        folder_id = request.POST['folder']
        folder = None
        if folder_id != '':
            folder = testy.models.TestFolder.objects.get(author=request.user, id=int(folder_id))

        test.folder = folder
    except ObjectDoesNotExist:
        pass

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

    folders = testy.models.TestFolder.objects.filter(author=request.user, deleted=False)

    error = None
    template = loader.get_template('testy/test_form_add.html')
    context = {'error': error, 'title': 'Přidat test', 'folders': folders}
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
            for r in q.questionresponse_set.order_by('order'):
                if not r.id in responsesRemaining:
                    r.delete()
                    test_changed = True
            q.save()
        else:
            test_changed = True
            # Create a new question and attach it to the test
            q = testy.models.Question( \
                test=test, text=request.POST['q%d' % q_idx], \
                multiple_answers=request.POST.get('q%d-multiplechoice' % q_idx, False), \
                order=q_idx)
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

    for q_idx, q in enumerate(test.question_set.order_by('order')):
        # Create a new questionAnswer object, and save the responses there
        q_answer = testy.models.QuestionAnswer(test_answer=test_answer, question=q)
        q_answer.save()

        if q.multiple_answers:
            selected_responses = [r for r_idx, r in enumerate(q.questionresponse_set.order_by('order')) if request.POST.get("q%d-r%d" % (q_idx+1, r_idx+1), False)]
        else:
            if request.POST.has_key("q%s" % (q_idx+1)):
                selected_responses = [q.questionresponse_set.order_by('order')[int(request.POST.get("q%s" % (q_idx+1), 1))-1]]
            else:
                selected_responses = []

        for r in selected_responses:
            q_answer.responses.add(r)

        q_answer.save()

    if test.exercise:
        return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.solution_display', args=(test_url, test_answer.get_url_key())))
    else:
        t = loader.get_template('testy/test_pisemka_odeslan.html')
        c = RequestContext(request, {})
        return http.HttpResponse(t.render(c))

def solution_display(request, test_url, solution_url):
    # Display the corrected solution
    try:
        test = testy.models.Test.get_test_by_url(test_url)
        solution = testy.models.TestAnswer.get_testanswer_by_url(solution_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_SOLUTION_NOT_FOUND_TITLE, ERROR_SOLUTION_NOT_FOUND_DESC))

    template = loader.get_template('testy/vyhodnoceni.html')
    context = {'test_answer': solution}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

@never_cache
@login_required
def solution_delete(request, test_url, solution_url):
    try:
        solution = testy.models.TestAnswer.get_testanswer_by_url(solution_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_SOLUTION_NOT_FOUND_TITLE, ERROR_SOLUTION_NOT_FOUND_DESC))

    solution.delete()

    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.solution_display_all', args=(test_url,)))


@never_cache
@login_required
def solution_display_all(request, test_url):
    # Display all solutions for a given test
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))
    if not test.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_TEST_NOT_EDITABLE_BY_USER_TITLE, ERROR_TEST_NOT_EDITABLE_BY_USER_DESC))

    template = loader.get_template('testy/seznam_reseni.html')
    context = {'test': test}
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

def error_display(request, error_title, error_desc):
    c = RequestContext(request, {'error_desc': error_desc, 'error_title': error_title})
    t = loader.get_template('testy/error.html')
    return t.render(c)

@login_required
def user_profile_edit(request):
    c = RequestContext(request, {})
    t = loader.get_template('testy/user_profile.html')
    return http.HttpResponse(t.render(c))

@login_required
def user_profile_edit_submit(request):
    firstname = request.POST['firstname']
    lastname = request.POST['lastname']
    email = request.POST['email']

    password = request.POST['password']
    password2 = request.POST['password2']

    # Check if the username corresponds to request.user
    request.user.first_name = firstname
    request.user.last_name = lastname
    request.user.email = email
    request.user.save()

    if password and password2 and password == password2:
        # Change the password
        request.user.set_password(password)
        request.user.save()
    elif (password or password2) and not password == password2:
        # Display a message that the two passwords don't match
        return http.HttpResponse(error_display(request, ERROR_PASSWORDS_DONT_MATCH_TITLE, ERROR_PASSWORDS_DONT_MATCH_DESC))

    continue_url = request.POST['continue_url']
    if continue_url:
        return http.HttpResponseRedirect(continue_url)
    else:
        return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.index'))



@login_required
def folder_add(request):
    error = None
    template = loader.get_template('testy/folder_form.html')
    context = {'error': error, \
        'title': 'Přidat složku', \
        'tests': testy.models.Test.objects.filter(author=request.user, deleted=False), \
        'folder': {'title': u'Název složky'}, \
        'form_action': urlresolvers.reverse('testy.views.folder_add_submit') \
    }
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

@login_required
def folder_add_submit(request):
    folder = testy.models.TestFolder(author=request.user)
    return folder_edit_from_request(request, folder)

@login_required
def folder_display(request, folder_url):
    try:
        folder = testy.models.TestFolder.get_folder_by_url(request, folder_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_FOLDER_NOT_FOUND_TITLE, ERROR_FOLDER_NOT_FOUND_DESC))

    context = {'tests': folder.test_set.all(),
        'folders': testy.models.TestFolder.objects.none(),
        'page_title': (u'%s - Testy' % folder.title),
        'page_header': (u'%s - Seznam testů' % folder.title),
        }
    t = loader.get_template('testy/seznam_testu.html')
    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))

@login_required
def folder_edit(request, folder_url):
    try:
        folder = testy.models.TestFolder.get_folder_by_url(request, folder_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_FOLDER_NOT_FOUND_TITLE, ERROR_FOLDER_NOT_FOUND_DESC))
    pass

    template = loader.get_template('testy/folder_form.html')
    context = { \
        'title': 'Upravit složku', \
        'tests': testy.models.Test.objects.filter(author=request.user, deleted=False), \
        'folder': folder, \
        'form_action': urlresolvers.reverse('testy.views.folder_edit_submit', kwargs={'folder_url': folder_url}) \
    }
    c = RequestContext(request, context)
    return http.HttpResponse(template.render(c))

@login_required
def folder_edit_submit(request, folder_url):
    try:
        folder = testy.models.TestFolder.get_folder_by_url(request, folder_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_FOLDER_NOT_FOUND_TITLE, ERROR_FOLDER_NOT_FOUND_DESC))
    pass

    return folder_edit_from_request(request, folder)

@login_required
def folder_delete(request, folder_url):
    # Remove the folder associations from the tests in that folder? The tests become un-associated again? Yes.
    try:
        folder = testy.models.TestFolder.get_folder_by_url(request, folder_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_FOLDER_NOT_FOUND_TITLE, ERROR_FOLDER_NOT_FOUND_DESC))

    for t in folder.test_set.all():
        t.folder = None
        t.save()

    folder.delete()
    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.index'))

def folder_edit_from_request(request, folder):
    folder.title = request.POST['title']
    folder.save()

    # TODO: Add code to update the selected tests with the folder
    tests_add_to_folder(request, folder)

    return http.HttpResponseRedirect(urlresolvers.reverse('testy.views.index'))

def tests_add_to_folder(request, folder):
    for t in testy.models.Test.objects.filter(author=request.user, deleted=False):
        selected = request.POST.get('t%d' % t.id, False)
        if selected:
            t.folder = folder
        elif t.folder == folder:
            t.folder = None
        t.save()

@login_required
def test_clone(request, test_url):
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    if not test.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_TEST_NOT_EDITABLE_BY_USER_TITLE, ERROR_TEST_NOT_EDITABLE_BY_USER_DESC))

    all_users = django.contrib.auth.models.User.objects.all()

    context = {'all_users': all_users, 'test': test}
    t = loader.get_template('testy/test_kopirovat.html')
    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))

@login_required
def folder_clone(request, folder_url):
    try:
        folder = testy.models.TestFolder.get_folder_by_url(request, folder_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_FOLDER_NOT_FOUND_TITLE, ERROR_FOLDER_NOT_FOUND_DESC))

    if not folder.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_FOLDER_NOT_EDITABLE_BY_USER_TITLE, ERROR_FOLDER_NOT_EDITABLE_BY_USER_DESC))

    all_users = django.contrib.auth.models.User.objects.all()

    context = {'all_users': all_users, 'folder': folder}
    t = loader.get_template('testy/slozka_kopirovat.html')
    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))
    

@login_required
def test_clone_submit(request, test_url):
    try:
        test = testy.models.Test.get_test_by_url(test_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_TEST_NOT_FOUND_TITLE, ERROR_TEST_NOT_FOUND_DESC))

    if not test.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_TEST_NOT_EDITABLE_BY_USER_TITLE, ERROR_TEST_NOT_EDITABLE_BY_USER_DESC))

    try:
      new_user = django.contrib.auth.models.User.objects.get(id=request.POST['new_user_id'])
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_USER_DOES_NOT_EXIST_TITLE, ERROR_USER_DOES_NOT_EXIST_DESC))

    clone_test_to_user(test, new_user, new_title=request.POST['test_name'])
    context = {'test': test, 'new_user': new_user}
    t = loader.get_template('testy/test_zkopirovan.html')
    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))

@login_required
def folder_clone_submit(request, folder_url):
    try:
        folder = testy.models.TestFolder.get_folder_by_url(request, folder_url)
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_FOLDER_NOT_FOUND_TITLE, ERROR_FOLDER_NOT_FOUND_DESC))

    if not folder.editable_by(request.user):
        return http.HttpResponseForbidden(error_display(request, ERROR_FOLDER_NOT_EDITABLE_BY_USER_TITLE, ERROR_FOLDER_NOT_EDITABLE_BY_USER_DESC))

    try:
      new_user = django.contrib.auth.models.User.objects.get(id=request.POST['new_user_id'])
    except ObjectDoesNotExist:
        return http.HttpResponseNotFound(error_display(request, ERROR_USER_DOES_NOT_EXIST_TITLE, ERROR_USER_DOES_NOT_EXIST_DESC))

    clone_folder_to_user(folder, new_user, new_title=request.POST['folder_name'])
    context = {'folder': folder, 'new_user': new_user}
    t = loader.get_template('testy/slozka_zkopirovana.html')
    c = RequestContext(request, context)
    return http.HttpResponse(t.render(c))

def clone_folder_to_user(folder, user, new_title=None):
    new_folder = testy.models.TestFolder(author=user, title=(new_title or folder.title))
    new_folder.save()

    for test in folder.test_set.all():
        clone_test_to_user(test, user, new_folder)

def clone_test_to_user(test, new_user, folder=None, new_title=None):
    new_test = testy.models.Test(author=new_user, title=(new_title or test.title), desc=test.desc, exercise=test.exercise, folder=folder)

    new_test.save()

    clone_test_questions(test, new_test)

def clone_test_questions(test, new_test):
    for question in test.question_set.all():
        new_question = testy.models.Question(test=new_test, text=question.text, image=question.image, multiple_answers=question.multiple_answers, order=question.order)
        new_question.save()
  
        clone_test_question_responses(question, new_question)

def clone_test_question_responses(question, new_question):
    for response in question.questionresponse_set.all():
        new_response = testy.models.QuestionResponse(question=new_question, text=response.text, correct=response.correct, order=response.order)
        new_response.save()
