import os

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import CompanyData, UserData
from users.sequential_decision_table import SequentialMatch
from users.utils import COMPANY_DATA_QUESTIONS_MAPPING
from utils.questions import QUESTIONS_FOR_ELIGIBILITY


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


class UserForm(APIView):
    """ Returns a set of questions to be asked on the frontend depending on which phase
    of the application user is currently at. """

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @classmethod
    def get(cls, request):
        """ This will be called when questions has to be asked to a user. """
        # Get the phase no for which the questions has to be shown.
        phase_no = request.query_params.get('phase_no', None)

        # If a phase no is given, then return the questions and related data for that phase no.
        if phase_no is not None:
            return Response(QUESTIONS_FOR_ELIGIBILITY.get(phase_no, None))

        # If phase no not given then return as bad request.
        return Response("Bad Request")

class Eligibility(APIView):
    """ To check if a user is eligibile or not for the loan """

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @classmethod
    def get(cls, request):
        """
        Will be called to check eligibility for a company before getting them registering
        to the platform.
        """
        query_params = request.query_params

        # Getting the business_model object here to add data to it and then check for eligibility.
        company_data_obj = CompanyData.objects.get(business=request.user)

        # Dynamically saving data to the company_data object using the setattr method.
        # NOTE: the attribute name is fetched from the query params and for that attrbute
        # the model attribute name is fetched using a dict and the data is saved to that attribute.
        for key, value in query_params.items():
            setattr(company_data_obj, COMPANY_DATA_QUESTIONS_MAPPING[key], value)

        # Now the data saving part is complete. Have to check for eligibility next.
        company_data_obj.save()


        sequential_match_obj = SequentialMatch(os.path.join(settings.BASE_DIR, 'utils',
                                                            'Decision_Table_one.csv'), query_params)

        # This is a pandas dataframe object and can be played with however required.
        sequential_result = sequential_match_obj.get_action_for_condition()
        eligibility_status = sequential_result.to_dict['status'].values()[0]

        if eligibility_status == 'TRUE':
            return Response("Done")
        else:
            return Response("Rejected")
