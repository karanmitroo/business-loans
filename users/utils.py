
# Since the questions sent to the frontend are dynamic, we are here mapping the questions to
# the model attributes that they belong to.

COMPANY_DATA_QUESTIONS_MAPPING = {
    "age": "date_of_registration",
    "amount requested": "amount_requested",
    "revenue": "revenue",
    "pan": "tax_reg_no",
    "sector": "sector",
    "pin": "address"
    }
