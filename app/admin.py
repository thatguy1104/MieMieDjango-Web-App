from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Module)
admin.site.register(Publication)

admin.site.register(BubbleAct)
admin.site.register(ApproachAct)
admin.site.register(SpecialtyAct)
admin.site.register(ColorAct)
admin.site.register(UserProfileAct)
