import os


import uuid
from random import randint, choice
import ast
from django.shortcuts import render
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
from packages.models import Packages
from packages.utils import create_package_data

# Create your views here.

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """ Hackable method to bypass csrf check while getting a post request """
    def enforce_csrf(self, request):
        return


class GetAndSetPlans(APIView):
    """ Returns a set of plans for the given business entity
    that has rates, and years for given loan amount """


    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @classmethod
    def get(cls, request):
        """ This will be called when user goes to the final view plans page. """

        user_obj = request.user

        company_data_obj = CompanyData.objects.get(business=user_obj)
        package_data = Packages.objects.filter(user=company_data_obj.business)

        response_data = {}
        response_data["rates"] = {}

        for each_data in package_data:
            response_data["rates"][each_data.tenure_months] = each_data.rate
        response_data["amount"] = package_data[0].amount
        response_data["user_id"] = package_data[0].user_id
        response_data["id"] = package_data[0].id
        # response_data["amount"] = package_data.amount

        return Response(("Worked", response_data))



    @classmethod
    def post(cls, request):
        """ This will be called when user goes to the final view plans page. """

        user_obj = request.user
        request_data = request.data

        # Packages.object.filter(user=user_obj).update(selected=False)
        Packages.objects.filter(user=user_obj).update(selected=False)

        package_data = Packages.objects.get(user=user_obj, id=request_data.get('id'))
        package_data.selected = True
        package_data.save()




        return Response("Saved package")
