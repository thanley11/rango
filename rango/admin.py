from django.contrib import admin
from django.core.urlresolvers import reverse
from rango.models import Category, Page, UserProfile

class PageAdmin(admin.ModelAdmin):

    list_display = ("category","title","url","views")
    
admin.site.register(Category)
admin.site.register(Page, PageAdmin)
admin.site.register(UserProfile)

