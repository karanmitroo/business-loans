import re

import pandas as pd

class ParseTable:

    def __init__(self, table_path):
        self.table = pd.read_csv(table_path, keep_default_na=False, dtype=str)
        self.condition_headers = {}
        self.action_headers = []
        self.set_headers()

    def set_headers(self):
        condition_headers_regex = re.compile('([\w\s]*\w)\s*\[([\w\s]*)\]')
        for each_column_name in self.table.columns.values:
            column_match = condition_headers_regex.match(each_column_name)
            if column_match is not None:
                self.condition_headers[column_match.group(1).lower()] = column_match.group(2).lower()
                self.table.rename(columns={each_column_name: column_match.group(1).lower()}, inplace=True)
            else:
                self.action_headers.append(each_column_name.lower())
                self.table.rename(columns={each_column_name: each_column_name.lower()}, inplace=True)


class EvalMethod:

    @staticmethod
    def equal(new_data, existing_data):
        if str(new_data) == 'NA' or str(existing_data) == 'NA':
            return str(new_data) == existing_data

        if '/' in existing_data:
            splitted_existing_data = list(map(lambda x: x.strip(), existing_data.split('/')))
            if str(new_data) in splitted_existing_data:
                return True
            return False

        # Try if values are integers then better to match converting to int.
        try:
            return int(float(new_data)) == int(float(existing_data))
        except ValueError:
            return str(new_data) == existing_data

    @staticmethod
    def range(new_data, existing_data):

        # Checking for 'NA' first as any the operands if NA will fail the eval function later.
        if str(new_data) == 'NA' or str(existing_data) == 'NA':
            return str(new_data) == existing_data

        # Case where input has a lower and upper value, comma separated.
        # Like: (193, 492)
        if '|' in existing_data:
            min_allowed, max_allowed = list(map(lambda x: float(x.strip()), existing_data.split('|')))
            return min_allowed <= float(new_data) <= max_allowed

        # When it only has one value with the operator before it or it can be NA to be matched equal.
        # Like: <234, >118, <=0.9. So it becomes return new_data < 234
        else:
            return eval(str(new_data) + existing_data)


class SequentialMatch:

    def __init__(self, parse_table_path, dict_condition):
        self.table_obj = ParseTable(parse_table_path)
        self.dict_condition = dict_condition
        self.eval_methods = EvalMethod()

    def get_action_for_condition(self):

        # This loop for all the conditional keys keeps on reducing the dataset by applying filter
        # over the dataframe columns. The eval methods are present in the the conditional headers dict
        # and their implementation in the class EvalMethods
        for key, value in self.dict_condition.items():

            self.table_obj.table = self.table_obj.table[
                self.table_obj.table[key].apply(lambda x: eval("self.eval_methods." +
                                                               self.table_obj.condition_headers[key] +
                                                               "(" + repr(value) + "," + repr(x) + ")"))
            ]

        # This will return a pandas dataframe, which can be played with when and where required.
        # Like somewhere it might be converted to list, while somewhere else can be a dict.
        return self.table_obj.table[self.table_obj.action_headers]
