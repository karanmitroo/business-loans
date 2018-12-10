import os
import uuid
import ast
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import AnonData, CompanyData, UserData
from users.sequential_decision_table import SequentialMatch


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
        email = request.data.get('email')

        # Check if any other user with the same username or email does NOT already exists.
        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            # If the user already exists, then ask them to login rather registering.
            return Response({
                "status" : "nok",
                "response" : "User Already Exists"
            })

        # Else register and signin the user.
        user_obj = User.objects.create(username=username)
        user_obj.email = email
        user_obj.set_password(password)
        user_obj.save()

        # Authenticate the user and log them in.
        authenticated_user = authenticate(request, username=username, password=password)
        login(request, authenticated_user)

        # Also create the other models required further.
        cls.create_userdata(authenticated_user)

        # Add any anonymous data to this actual users data
        cls.add_anon_data_to_userdata(request.data.get('uuid'), user_obj)

        return Response("Thanks for logging in")


    @classmethod
    def create_userdata(cls, user_obj):
        """ To create a userdata object as and when a new user registers to the platform. """
        user_data_obj, _ = UserData.objects.get_or_create(user=user_obj)
        user_data_obj.session_data['current_state'] = 'eligibility_check'
        user_data_obj.save()

    @classmethod
    def add_anon_data_to_userdata(cls, identifier, user_obj):
        """ To fetch anonymous data from AnonData model and save it for any actual user """

        anon_data = AnonData.objects.get(identifier=identifier)

        # Saving the fetched anonymous data to data of a known user.
        _ = CompanyData.objects.create(
            business=user_obj,
            revenue=anon_data.data['revenue'],
            amount_requested=anon_data.data['amount_requested'],
            date_of_registration=timezone.datetime(
                year=int(anon_data.data['year_of_registration']),
                month=1,
                day=1)
            )

        # Since anonymous data has been saved, there is no use of keeping it the anonymous table.
        anon_data.delete()


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
            user_data_obj = UserData.objects.get(user=user_obj)

            # Login the user and send the current state where the user is present.
            return Response({
                "status" : "ok",
                "current_state" : user_data_obj.session_data['current_state']
            })

        return Response({
            "status" : "nok",
            "response" : "Wrong Username/ Password. Please Try again."
        })


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
    def post(cls, request):
        """
        Will be called to check eligibility for a company before getting them registering
        to the platform.
        """
        request_data = request.data

        # We have got a lot of data here but do NOT know who the user is.
        # So currently saving the data as Anonymous data and sending a uuid token
        # to the frontend which will be retrieved at time of registering.
        # Matching this uuid will get us the user for which the data was collected.
        uuid_generated = uuid.uuid4()
        anon_data = {
            "year_of_registration" : request_data.get('year_of_registration'),
            "revenue" : request_data.get('revenue'),
            "amount_requested": request_data.get('amount')
        }

        anon_data_obj = AnonData.objects.create(identifier=uuid_generated, data=anon_data)

        # Checking the eligibility of the user, depending on the params used in the method below.
        sequential_match_obj = SequentialMatch(os.path.join(
            settings.BASE_DIR, 'utils', 'Decision_Table_one.csv'), {
                "age" : timezone.now().year - int(request_data.get('year_of_registration')),
                "revenue" : request_data.get('revenue'),
                "amount requested": request_data.get('amount')
            })

        # This is a pandas dataframe object and can be played with however required.
        sequential_result = sequential_match_obj.get_action_for_condition()

        # Using eval here to convert the text boolean value to python boolean values.
        # The result we get here will be 'True' or 'False'. eval converts to
        eligibility_status = ast.literal_eval(
            list(sequential_result.to_dict()['status'].values())[0])

        # If eligible then simply send the generated uuid.
        if eligibility_status:

            return Response({
                "status" : "ok",
                "uuid" : uuid_generated
            })

        # If not eligible then decline and save the status to anonymous data.
        anon_data_obj.data['status'] = 'declined'
        anon_data_obj.save()

        return Response({
            "status" : "declined",
        })
