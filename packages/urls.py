from django.conf.urls import url

from packages.views import GetAndSetPlans

urlpatterns = [
    url(r'^plans/$', GetAndSetPlans.as_view(), name='package-plans'),
]
