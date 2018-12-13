import os


import uuid
from random import randint, choice
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

from packages.utils import create_package_data


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
        password = request.data.get('password')
        email = request.data.get('email')
        username = request.data.get('username')

        # Check if any other user with the same username or email does NOT already exists.
        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            # If the user already exists, then ask them to login rather registering.
            return Response({
                "status" : "nok",
                "response" : "This username/ email is already registered with the system. Kindly login to proceed further with your application."
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
        user_data_obj, _ = UserData.objects.get_or_create(user=user_obj)
        cls.create_userdata(user_data_obj)

        # Add any anonymous data to this actual users data
        cls.add_anon_data_to_userdata(request.data.get('uuid'), user_obj)

        return Response({
            "status" : "ok",
            "user" : {
                "status" : "ok",
                "username" : user_obj.username,
                "current_state" : user_data_obj.session_data.get('current_state')
            }
        })


    @classmethod
    def create_userdata(cls, user_data_obj):
        """ To create a userdata object as and when a new user registers to the platform. """
        user_data_obj.session_data['current_state'] = 'indepth_details'
        user_data_obj.save()

    @classmethod
    def add_anon_data_to_userdata(cls, identifier, user_obj):
        """ To fetch anonymous data from AnonData model and save it for any actual user """

        anon_data = AnonData.objects.get(identifier=identifier)

        # Save username from the previously fetched company name
        user_obj.first_name = anon_data.data['company_name']
        user_obj.save()

        # Saving the fetched anonymous data to data of a known user.
        _ = CompanyData.objects.create(
            business=user_obj,
            revenue=anon_data.data['revenue'],
            amount_requested=anon_data.data['amount_requested'],
            date_of_registration=timezone.datetime(
                year=int(anon_data.data['year_of_registration'].split('-')[0]),
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


class Eligibility(APIView):
    """ To check if a user is eligibile or not for the loan """

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)



    @classmethod
    def get(cls, request):
        """ This will help get the details of the user that were used for eligibility check
        in case he comes back """

        request_data = request.data
        company_data_obj = CompanyData.objects.get(business=user_obj)

        company_data = {}
        company_data["year_of_registration"] = company_data_obj.year_of_registration
        company_data["revenue"] = company_data_obj.revenue
        company_data["amount_requested"] = company_data_obj.amount_requested
        company_data["company_name"] = company_data_obj.company_name


        return Response(("Business Details", company_data))






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
            "year_of_registration" : request_data.get('dateOfRegistration'),
            "revenue" : request_data.get('revenue'),
            "amount_requested": request_data.get('amountRequested'),
            "company_name": request_data.get('companyName')
        }

        anon_data_obj = AnonData.objects.create(identifier=uuid_generated, data=anon_data)

        # Checking the eligibility of the user, depending on the params used in the method below.
        sequential_match_obj = SequentialMatch(os.path.join(
            settings.BASE_DIR, 'utils', 'eligibility_decision_table.csv'), {
                "age" : timezone.now().year - int(request_data.get('dateOfRegistration').split('-')[0]),
                "revenue" : request_data.get('revenue'),
                "amount requested": request_data.get('amountRequested')
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
                "uuid" : uuid_generated,
                "next_state" : "register"
            })

        # If not eligible then decline and save the status to anonymous data.
        anon_data_obj.data['status'] = 'declined'
        anon_data_obj.save()

        return Response({
            "status" : "nok",
            "next_state" : "declined"
        })

class GetUser(APIView):
    """ To send the user data if the user is logged in """

    @classmethod
    def get(cls, request):
        """ Will be called whenever the current status of a user (if logged in)
        has to be known """
        if request.user.is_authenticated:
            user_obj = request.user
            user_data_obj = UserData.objects.get(user=user_obj)

            data = {
                "status" : "ok",
                "username" : user_obj.username,
                "current_state" : user_data_obj.session_data.get('current_state')
            }

            return Response(data)

        return Response({
            "status" : "nok"
        })


class GetIndepthDetails(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @classmethod
    def post(cls, request):
        """
        Will be called to check get additional details of customer
        which will be used to calculate a eligibility_point
        which will in turn be sent to the packages module to
        find which paackages (rate & years) can be given
        to the customer.
        """

        #Creating the user object and getting the request data
        user_obj = request.user
        request_data = request.data
        print ("Came here")
        #Extracting more data points regarding the user.
        indepth_data = {
            "tax_reg_no" : request_data.get('taxRegNo'),
            "sector" : request_data.get('sector'),
            "address": request_data.get('location')
        }

        print (indepth_data, user_obj)
        #Updating the compant data object with the newly avaialable data points
        company_data_obj = CompanyData.objects.get(business=user_obj)
        company_data_obj.tax_reg_no = indepth_data["tax_reg_no"]
        company_data_obj.sector = indepth_data["sector"]
        company_data_obj.address = indepth_data["address"]
        company_data_obj.save()

        print ("Saved company data")
        LOCATION = ["Urban", "Semi-Urban", "Rural"]

        #To be replaced with an api call that will send the tax registration number and
        #get the cibil score in return
        cibil = randint(1,10)

        #To be replaced with an api call that will send the location details
        #and get whether it is in a urban, semi-urban or rural neighbourhood in return
        location_option = choice(LOCATION)

        print ("things choosen")


        # Getting the eligibility_point of the user, using on the params used in the method below.
        sequential_match_obj = SequentialMatch(os.path.join(
            settings.BASE_DIR, 'utils', 'score_decision_table.csv'), {
                "cibil rank" : cibil,
                "sector" : request_data.get('sector'),
                "location": location_option,
            })

        # This is a pandas dataframe object and can be played with however required.
        sequential_result = sequential_match_obj.get_action_for_condition()

        # Using eval to ge the eligibility point here
        eligibility_point = eval(list(sequential_result.to_dict()['score'].values())[0])

        #Saving the eligibility point in the misc_data attribute of the company
        company_data_obj.misc_data["eligibility_point"] = eligibility_point
        company_data_obj.save()



        #Call the function that will calculate and create the package data based on loan eligibility
        user_data_obj = UserData.objects.get(user=user_obj)
        if eligibility_point != 0:

            user_data_obj.session_data['current_state'] = 'choose_package'
            user_data_obj.save()
            create_package_data(company_data_obj)
            return Response(
                {"status" : "ok",
                 "user" : {
                     "status" : "ok",
                     "username" : user_obj.username,
                     "current_state" : user_data_obj.session_data.get('current_state')
                 }})
        print ("Going to else to send response")
        # If the user is declined then send status as "nok"
        # user_data_obj.session_data['current_state'] = 'declined'
        # user_data_obj.save()
        return Response({
            "status" : "nok",
            "user" : {
                "status" : "ok",
                "username" : user_obj.username,
                "current_state" : user_data_obj.session_data.get('current_state')
            }
        })



    @classmethod
    def get(cls, request):
        """
        Will be called to get saved additional details of customer
        which have been used to calculate a eligibility_point
        """

        user_obj = request.user

        indepth_data = {}

        company_data_obj = CompanyData.objects.get(business=user_obj)

        if (company_data_obj.tax_reg_no != '' and
                company_data_obj.sector != '' and
                company_data_obj.address != ''):
            indepth_data["tax_reg_no"] = company_data_obj.tax_reg_no
            indepth_data["sector"] = company_data_obj.sector
            indepth_data["address"] = company_data_obj.address
            indepth_data["locked"] = True

        else:
            indepth_data["locked"] = False

        return Response(indepth_data)
