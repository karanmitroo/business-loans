from django.conf.urls import url

from users.views import Eligibility, Login, Register

urlpatterns = [
    url(r'^register/$', Register.as_view(), name='register-user'),
    url(r'^login/$', Login.as_view(), name='login-user'),
    url(r'^eligibility/$', Eligibility.as_view(), name='user-eligibility')
]
