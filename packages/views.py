import os
import numpy as np

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

        print("HERE")
        response_data = {}
        response_data["amount"] = package_data[0].amount
        response_data["user_id"] = package_data[0].user_id
        print("response rates",response_data)

        response_data["locked"] = Packages.objects.filter(user=user_obj, selected=True).exists()

        print("Here")

        print(response_data)
        amount = response_data["amount"]*100000
        response_data["packages"] = []
        for each_data in package_data:
            package_field = {}
            rate_field = int(each_data.rate)*1.0/1200.0
            months = each_data.tenure_years*12
            emi_amount = round(-1*np.pmt(rate_field, months, amount))
            package_field["years"] = each_data.tenure_years
            package_field["rate"] = each_data.rate
            package_field["emi"] = emi_amount
            package_field["selected"] = each_data.selected
            package_field["id"] = each_data.id
            response_data["packages"].append(package_field)

        return Response(response_data)



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


        return Response({"status":"ok",
                         "selected_package_id":request_data.get('id')})
