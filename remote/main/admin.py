from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# Register your models here.
from .models import PnetModel


class PnetModelInline(admin.StackedInline):
    model = PnetModel
    can_delete = False
    verbose_name_plural = 'Pnet'


class UserAdmin(BaseUserAdmin):
    inlines = (PnetModelInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
