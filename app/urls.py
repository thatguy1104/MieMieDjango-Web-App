from django.urls import path, include
from django.conf.urls.static import static  # new
from django.conf import settings  # new
from django.conf.urls import url
from app import views
from django.contrib.staticfiles.views import serve
from django.views.decorators.cache import cache_control

urlpatterns = [
    path('', views.app, name='app'),
    path('join', views.join, name='join'),
    path('sdg', views.sdg, name='sdg'),
    path('svm_universal', views.universal_SVM, name='universal_SVM'),
    path('iheVisualisation', views.iheVisualisation, name='iheVisualisation'),
    path('sdgVisualisation', views.sdgVisualisation, name='sdgVisualisation'),
    path('module/<str:pk>', views.module, name='module'),
    path('publication/<str:pk>', views.publication, name='publication'),
    path('exportMod', views.export_modules_csv, name='export_modules_csv'),
    path('exportPub', views.export_publications_csv,name='export_publications_csv'),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL,
#                           view=cache_control(no_cache=True, must_revalidate=True)(serve))
