from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (AgentProfile, PaymentsTracker,
                     NewsUpdate, Notifications, ForexRate)

from django.utils.translation import gettext_lazy as _


class UserAdminConfig(UserAdmin):
    model = AgentProfile
    search_fields = ('email', 'agent_name', 'first_name',
                     'business_name', 'commission', 'phone')
    list_filter = ('agent_name', 'email', 'first_name',
                   'last_name', 'business_name',
                   'phone', 'commission', 'is_active', 'is_staff')
    ordering = ('-date_joined',)
    list_display = ('id', 'agent_name', 'email', 'commission', 'first_name', 'last_name',
                    'business_name', 'phone', 'is_active', 'image',)

    fieldsets = (
        (None, {"fields": ("agent_name", "password")}),
        (_("Personal info"), {
         "fields": ("first_name", "last_name", "email", "image",)}),
        ('Business info', {'fields': ('business_name', 'commission', 'description',
         'phone', "region", "zone", "woreda", "street",)}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),

    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("agent_name", "password1", "password2"),
            },
        ),
    )


admin.site.register(AgentProfile, UserAdminConfig)
admin.site.register(PaymentsTracker)
admin.site.register(NewsUpdate)
admin.site.register(Notifications)
admin.site.register(ForexRate)
