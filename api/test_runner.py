import unittest
from django.test.runner import DiscoverRunner, TextTestResult

class NumberedTestResult(TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_counter = 0

    def startTest(self, test):
        self.test_counter += 1
        self.stream.write(f"Test {self.test_counter}: ")
        super().startTest(test)

class CustomTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failfast = False # Disable stopping on first failure

    def _make_result(self):
        return NumberedTestResult(self.stream, self.descriptions, self.verbosity)
