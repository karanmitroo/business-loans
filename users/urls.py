from django.conf.urls import url
from users.views import Register, Login
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    url(r'^register/$', Register.as_view(), name='register-user'),
    url(r'^login/$', Login.as_view(), name='login-user')
]
