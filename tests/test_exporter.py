import unittest
import csv
import test_utils
import os
from neatrader.preprocess import EtradeImporter, CsvExporter


class TestCsvExporter(unittest.TestCase):
    def test_to_csv(self):
        tsla = test_utils.fetch_resource('2020-09-09/TSLA.json')
        chain = EtradeImporter().from_json(tsla)
        file_name = CsvExporter().to_csv([chain])

        with open(file_name, 'r') as f:
            for row in csv.reader(f):
                assert '200909' == row[0]
                assert '366.28' == row[1]

        os.remove(file_name)