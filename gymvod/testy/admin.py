# -*- coding: UTF-8 -*-
from django.contrib import admin
import testy.models

admin.site.register(testy.models.Test)
admin.site.register(testy.models.TestFolder)
#admin.site.register(testy.models.Question)
#admin.site.register(testy.models.QuestionResponse)
admin.site.register(testy.models.TestAnswer)
admin.site.register(testy.models.QuestionAnswer)

class QuestionResponseInline(admin.StackedInline):
    model = testy.models.QuestionResponse
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionResponseInline]

admin.site.register(testy.models.Question, QuestionAdmin)
