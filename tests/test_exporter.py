import unittest
import csv
import test_utils
import os
from neatrader.preprocess import EtradeImporter, CsvExporter


class TestCsvExporter(unittest.TestCase):
    def test_to_csv(self):
        try:
            importer = EtradeImporter()
            exporter = CsvExporter('tests')
            tsla = test_utils.fetch_resource('2020-09-09/TSLA.json')
            chain = importer.from_json(tsla)
            file_name = exporter.to_csv(chain)

            with open(file_name, 'r') as f:
                rows = list(csv.reader(f))
                assert 2 == len(rows)
                assert '200909' == rows[1][0]
                assert '366.28' == rows[1][1]

            tsla = test_utils.fetch_resource('2020-09-10/TSLA.json')
            chain = importer.from_json(tsla)
            file_name = exporter.to_csv(chain)

            with open(file_name, 'r') as f:
                rows = list(csv.reader(f))
                assert 3 == len(rows)
                assert '200910' == rows[2][0]
                assert '371.34' == rows[2][1]
        finally:
            os.remove(file_name)
