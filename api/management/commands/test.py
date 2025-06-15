from django.core.management.base import BaseCommand
import sys
import pytest

class Command(BaseCommand):
    help = 'Runs tests using pytest instead of Django\'s default test runner'

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        # Convert Django's test command arguments to pytest arguments
        pytest_args = list(args)
        
        if not pytest_args:
            # If no specific test paths are provided, run all tests
            pytest_args = ['api/tests', 'api_v2/tests']

        # Add -v for more verbose output by default
        if '-v' not in pytest_args:
            pytest_args.insert(0, '-v')

        # Run pytest with the collected arguments
        sys.exit(pytest.main(pytest_args)) 