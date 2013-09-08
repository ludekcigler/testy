# -*- coding: UTF-8 -*-
from django import forms

class QuestionForm(forms.Form):
    # Display question

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        super(QuestionForm, self).__init__(*args, **kwargs)

        choices = []
        for r in question.questionresponse_set.order_by('order').all():
            choices.append(r.text)

        if question.multiple_answers:
            responses = forms.CheckboxSelectMultiple(choices=choices)
        else:
            responses = forms.RadioSelect(choices=choices)

class TestForm(forms.Form):
    # Form to display test to students
    def __init__(self, *args, **kwargs):
        test = kwargs.pop('test')
        super(TestForm, self).__init__(*args, **kwargs)

        for q_idx, q in enumerate(test.question_set.order_by('order').all()):
            #self.fields['question_%d' % q_idx] = QuestionForm(question=q, *args, **kwargs)
            pass

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.CharField(max_length=50)

class ResponseEditForm(forms.Form):
    # Display a form to edit response
    correct = ""

class TestEditForm(forms.Form):
    # Edit form
    pass

class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)

