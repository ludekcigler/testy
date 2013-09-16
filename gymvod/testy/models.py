# -*- coding: UTF-8 -*-

from django.db import models
from django.contrib.auth.models import User
import url_encoder
import unicodedata

TEST_ANSWER_URL_SALT = 943

class Test(models.Model):

    title = models.CharField(max_length=256)
    desc = models.TextField()
    created = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User)
    exercise = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % self.title

    def get_url_key(self):
        return url_encoder.encode_url(self.id)

    @staticmethod
    def get_test_by_url(aUrl):
        return Test.objects.get(id=url_encoder.decode_url(aUrl));

class Question(models.Model):
    
    text = models.TextField()
    image = models.ImageField(upload_to='uploads', blank = True)
    multiple_answers = models.BooleanField()
    test = models.ForeignKey('Test')
    order = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return u"%s: %s" % (self.test, self.text)

    def num_correct_answers(self):
        return len(self.questionresponse_set.filter(correct=True))

    class Meta:
        ordering = ['order']

class QuestionResponse(models.Model):
    
    text = models.CharField(max_length=256)
    correct = models.BooleanField()
    question = models.ForeignKey('Question')
    order = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return u"%s: %s) %s%s" % (self.question.test, self.question.id, self.text, u" ✓" if self.correct else u" ✗")

    class Meta:
        ordering = ['order']

class TestAnswer(models.Model):

    test = models.ForeignKey('Test')
    date = models.DateTimeField(auto_now=True)
    score = models.FloatField()
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    email = models.CharField(max_length=50)

    def __unicode__(self):
        return u"%s, %s %s, %s" % (self.test, self.first_name, self.last_name, self.date)

    def get_score(self):
        """
        Calculate the score on-the-fly for the moment, what if we need to change it?
        """
        total_points = sum([q.get_points() for q in self.questionanswer_set.all()])
        return float(total_points)/len(self.test.question_set.all())

    def get_url_key(self):
        return url_encoder.encode_url(self.id + TEST_ANSWER_URL_SALT)

    @staticmethod
    def get_testanswer_by_url(aUrl):
        return TestAnswer.objects.get(id=(int(url_encoder.decode_url(aUrl)) - TEST_ANSWER_URL_SALT));

class QuestionAnswer(models.Model):

    test_answer = models.ForeignKey('TestAnswer')
    question = models.ForeignKey('Question')
    responses = models.ManyToManyField('QuestionResponse')

    def __unicode__(self):
        return u"%s %s" % (self.test_answer, self.id)

    def num_correct_answers(self):
        # Calculate the number of points
        return len(self.responses.filter(correct=True))

    def get_points(self):
        return self.num_correct_answers()/self.question.num_correct_answers()

