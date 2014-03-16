# -*- coding: UTF-8 -*-

from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
import url_encoder
import unicodedata

# DO NOT CHANGE THESE VALUES!!! (or the DB entries will be attributed wrongly...)
TEST_ANSWER_URL_SALT = 943
FOLDER_URL_SALT = 1238

class Test(models.Model):

    title = models.CharField(max_length=256)
    desc = models.TextField()
    created = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User)
    exercise = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    folder = models.ForeignKey('TestFolder', blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.title

    def get_url_key(self):
        return url_encoder.encode_url(self.id)

    @staticmethod
    def get_test_by_url(aUrl):
        return Test.objects.get(id=url_encoder.decode_url(aUrl));

    def editable_by(self, aUser):
        return (aUser.id == self.author.id)

class TestFolder(models.Model):
    
    title = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User)
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%d, %s' % (self.id, self.title)

    def get_url_key(self):
        return url_encoder.encode_url(self.id + FOLDER_URL_SALT)

    @staticmethod
    def get_folder_by_url(aUrl):
        return TestFolder.objects.get(id=(int(url_encoder.decode_url(aUrl)) - FOLDER_URL_SALT));

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

# Default test for new users
DEFAULT_TEST = {'title': u'Ukázkový test', 'desc': u'Popis ukázkového testu', 'exercise': True, 'deleted': False}

DEFAULT_QUESTION_1 = {'text': u'Auto se rovnoměrně rozjíždí a za dobu $$15 s$$ ujede dráhu $$112,5 m$$. S jak velkým zrychlením se rozjíždí?', 'multiple_answers': True, 'order': 1}
DEFAULT_RESPONSES_1 = [(u'0,1 $$m . s^{-2}$$', False), (u'0,5  $$m . s^{-2}$$', False), (u'0,75  $$m . s^{-2}$$', False), (u'1  $$m . s^{-2}$$', True)]

DEFAULT_QUESTION_2 = {'text': u'Řidič auta se rovnoměrně rozjíždí se zrychlením $$2,5 m.s^{-2}$$. Za jakou dobu dosáhne rychlost 90 km/h?', 'multiple_answers': True, 'order': 2}

DEFAULT_RESPONSES_2 = [(u'5 s', False), (u'10 s', True), (u'15 s', False), (u'20 s', False)]

DEFAULT_QUESTIONS = [DEFAULT_QUESTION_1, DEFAULT_QUESTION_2]
DEFAULT_RESPONSES = [DEFAULT_RESPONSES_1, DEFAULT_RESPONSES_2]

def create_default_test(sender, **kwargs):
    """
    Creates a default test for a new user
    """
    
    user = kwargs['instance']
    created = kwargs['created']
    if not created:
        return

    test = Test(author=user, title=DEFAULT_TEST['title'], desc=DEFAULT_TEST['desc'], exercise=DEFAULT_TEST['exercise'])
    test.save()
    # Add questions:

    for q_idx in xrange(0, len(DEFAULT_QUESTIONS)):
        question = Question(test=test, text=DEFAULT_QUESTIONS[q_idx]['text'], multiple_answers=DEFAULT_QUESTIONS[q_idx]['multiple_answers'], order=(q_idx+1))
        question.save()

        for r_idx in xrange(0, len(DEFAULT_RESPONSES[q_idx])):
            resp_data = DEFAULT_RESPONSES[q_idx][r_idx]
            response = QuestionResponse(question=question, text=resp_data[0], correct=resp_data[1], order=(r_idx+1))
            response.save()

signals.post_save.connect(create_default_test, sender=User, dispatch_uid='user_default_test_created')

