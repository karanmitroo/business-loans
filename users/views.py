from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)

from rest_framework.views import APIView
from rest_framework.response import Response

from users.models import UserData


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """ Hackable method to bypass csrf check while getting a post request """
    def enforce_csrf(self, request):
        return


class Register(APIView):
    """ To register a user on to the platform """

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @classmethod
    def post(cls, request):
        """ Will be called when a user tries to register to the platform """
        username = request.data.get('username')
        password = request.data.get('password')

        # Check if any other user with the same username does NOT already exists.
        if User.objects.filter(username=username).exists():
            # If the user already exists, then ask them to login rather registering.
            return Response("User Already exists")

        # Else register and signin the user.
        user_obj = User.objects.create(username=username)
        user_obj.set_password(password)
        user_obj.save()

        # Authenticate the user and log them in.
        authenticated_user = authenticate(request, username=username, password=password)
        login(request, authenticated_user)

        # Also create the other models required further.
        cls.create_userdata(authenticated_user)
        return Response("Thanks for logging in")


    @classmethod
    def create_userdata(cls, user_obj):
        """ To create a userdata object as and when a new user registers to the platform. """
        UserData.objects.get_or_create(user=user_obj)


class Login(APIView):
    """ To login a user on the platform """

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @classmethod
    def post(cls, request):
        """ Will be called when a user tries to login to the platform """
        username = request.data.get('username')
        password = request.data.get('password')

        user_obj = authenticate(request, username=username, password=password)

        # If user_obj found, means username and password are correct, then log in the user.
        if user_obj is not None:
            login(request, user_obj)
            return Response("Logged In")

        return Response("Sorry, Incorrect username/ password entered.")



class Eligibility(APIView):
    """ To check if a user is eligibile or not for the loan """

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @classmethod
    def get(cls, request):
        """
        Will be called to check eligibility for a company before getting them registering
        to the platform.
        """
        return Response("Done")
