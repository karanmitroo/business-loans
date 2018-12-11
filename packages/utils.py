import os

from django.conf import settings
from users.sequential_decision_table import SequentialMatch
from packages.models import Packages

def create_package_data(company_data_obj):

    #create a dictionary called interest_rates_dict to store years and rates
    #in a key : value format
    interest_rates_dict = dict()


    #Creating the sequential_match_obj using the third decision table
    sequential_match_obj = SequentialMatch(os.path.join(
        settings.BASE_DIR, 'utils', 'package_decision_table.csv'), {
            "score" : company_data_obj.misc_data['eligibility_point']})

    # This is a pandas dataframe object and can be played with however required.
    sequential_result = sequential_match_obj.get_action_for_condition()


    #Fill up the values for the dictionary that is to have the rates and years
    for year, rate in sequential_result.to_dict().items():
        interest_rates_dict[int(year)] = float(list(rate.values())[0])

    #Delete packages for the business in case it already exists
    Packages.objects.filter(user=company_data_obj.business).delete()

    #Push computed package details of the company in the package table
    for years, rate in interest_rates_dict.items():
        if rate != "NA":
            _ = Packages.objects.create(amount=int(company_data_obj.amount_requested),
                                        tenure_months=int(years), rate=float(rate),
                                        selected=False,
                                        user=company_data_obj.business)

    return "Eligible for Loan"
