from django.conf.urls import url

from packages.views import GetAndSetPlans

urlpatterns = [
    url(r'^choose-package/$', GetAndSetPlans.as_view(), name='choose-package'),
]
