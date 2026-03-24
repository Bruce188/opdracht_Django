import importlib
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.urls import reverse

from .forms import CalculationForm
from .models import Calculation


class CalculatorViewTests(TestCase):
    def test_get_calculate_page(self):
        """GET / returns 200, uses correct template, contains a CalculationForm, result is None."""
        response = self.client.get(reverse('calculate'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculator/calculate.html')
        self.assertIsInstance(response.context['form'], CalculationForm)
        self.assertIsNone(response.context['result'])

    def test_valid_post_computes_correctly(self):
        """POST with P=1000, r=5, n=10 returns correct future_value and total_interest."""
        response = self.client.post(reverse('calculate'), {
            'principal': 1000,
            'interest_rate': 5,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        result = response.context['result']
        self.assertIsNotNone(result)
        self.assertEqual(result['future_value'], 1628.89)
        self.assertEqual(result['total_interest'], 628.89)

    def test_valid_post_saves_to_db(self):
        """POST valid data creates exactly one Calculation record with correct fields."""
        self.client.post(reverse('calculate'), {
            'principal': 1000,
            'interest_rate': 5,
            'years': 10,
        })
        self.assertEqual(Calculation.objects.count(), 1)
        calc = Calculation.objects.first()
        self.assertEqual(calc.principal, 1000)
        self.assertEqual(calc.interest_rate, 5)
        self.assertEqual(calc.years, 10)
        self.assertEqual(calc.future_value, 1628.89)
        self.assertEqual(calc.total_interest, 628.89)

    def test_zero_interest_rate(self):
        """POST with r=0 returns A=P and I=0."""
        response = self.client.post(reverse('calculate'), {
            'principal': 1000,
            'interest_rate': 0,
            'years': 5,
        })
        result = response.context['result']
        self.assertEqual(result['future_value'], 1000.00)
        self.assertEqual(result['total_interest'], 0.00)

    def test_single_year(self):
        """POST with P=100, r=10, n=1 returns A=110.00 and I=10.00."""
        response = self.client.post(reverse('calculate'), {
            'principal': 100,
            'interest_rate': 10,
            'years': 1,
        })
        result = response.context['result']
        self.assertEqual(result['future_value'], 110.00)
        self.assertEqual(result['total_interest'], 10.00)

    def test_invalid_negative_principal(self):
        """POST with negative principal shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': -100,
            'interest_rate': 5,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_invalid_zero_years(self):
        """POST with years=0 shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': 1000,
            'interest_rate': 5,
            'years': 0,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_invalid_missing_fields(self):
        """POST with empty body shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_invalid_exceeds_max_values(self):
        """POST with principal exceeding max_value shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': 2_000_000_000,
            'interest_rate': 5,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

        # Also test years exceeding max_value
        response = self.client.post(reverse('calculate'), {
            'principal': 1000,
            'interest_rate': 5,
            'years': 200,
        })
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_invalid_interest_rate_exceeds_max(self):
        """POST with interest_rate=1001 shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': 1000,
            'interest_rate': 1001,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_invalid_negative_interest_rate(self):
        """POST with interest_rate=-1 shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': 1000,
            'interest_rate': -1,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('interest_rate', response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_invalid_post_result_is_none(self):
        """POST with invalid data keeps result as None in context."""
        response = self.client.post(reverse('calculate'), {
            'principal': -100,
            'interest_rate': 5,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['result'])

    def test_principal_min_boundary_accepted(self):
        """POST with principal=0.01 (min boundary) succeeds."""
        response = self.client.post(reverse('calculate'), {
            'principal': 0.01,
            'interest_rate': 5,
            'years': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].errors)
        self.assertIsNotNone(response.context['result'])
        self.assertEqual(Calculation.objects.count(), 1)

    def test_principal_zero_rejected(self):
        """POST with principal=0.00 shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': 0.00,
            'interest_rate': 5,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_invalid_non_numeric_input(self):
        """POST with non-numeric principal shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': 'abc',
            'interest_rate': 5,
            'years': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)

    def test_isfinite_guard(self):
        """Overflow guard rejects non-finite results with error, no DB record."""
        with patch('calculator.views.math') as mock_math:
            mock_math.isfinite.return_value = False
            response = self.client.post(reverse('calculate'), {
                'principal': 1000,
                'interest_rate': 5,
                'years': 10,
            })
        self.assertIsNone(response.context['result'])
        self.assertIn(
            'The result is too large to compute.',
            response.context['form'].non_field_errors(),
        )
        self.assertEqual(Calculation.objects.count(), 0)

    def test_overflow_with_real_inputs(self):
        """Real computation producing inf triggers the overflow guard (no math mock)."""
        # Form max_value constraints prevent inputs large enough to overflow,
        # so we bypass form validation while letting the real computation in the
        # view (including math.isfinite) run with extreme values.
        extreme_data = {
            'principal': 1e250,
            'interest_rate': 1000,
            'years': 100,
        }

        def fake_is_valid(form_self):
            form_self.cleaned_data = extreme_data
            return True

        with patch.object(CalculationForm, 'is_valid', fake_is_valid):
            response = self.client.post(reverse('calculate'), {
                'principal': 1000,
                'interest_rate': 5,
                'years': 1,
            })
        self.assertIsNone(response.context['result'])
        self.assertIn(
            'The result is too large to compute.',
            response.context['form'].non_field_errors(),
        )
        self.assertEqual(Calculation.objects.count(), 0)

    def test_form_accepts_max_boundaries(self):
        """Form accepts exact max boundary values."""
        form = CalculationForm(data={
            'principal': 1_000_000_000,
            'interest_rate': 1000,
            'years': 100,
        })
        self.assertTrue(form.is_valid())

    def test_principal_below_min_boundary_rejected(self):
        """POST with principal=0.005 (below min_value=0.01) shows form errors, no DB record."""
        response = self.client.post(reverse('calculate'), {
            'principal': 0.005,
            'interest_rate': 5,
            'years': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Calculation.objects.count(), 0)


class CalculationModelTests(TestCase):
    def test_model_str(self):
        """Calculation.__str__ returns expected format after DB round-trip."""
        calc = Calculation.objects.create(
            principal=1000,
            interest_rate=5,
            years=10,
            future_value=1628.89,
            total_interest=628.89,
        )
        # Re-fetch from DB to test with float representation
        calc = Calculation.objects.get(pk=calc.pk)
        expected = "P=1000, r=5%, n=10 → A=1628.89"
        self.assertEqual(str(calc), expected)

    def test_model_str_trailing_zeros(self):
        """Calculation.__str__ with :g format strips trailing zeros."""
        calc = Calculation.objects.create(
            principal=1000.10,
            interest_rate=5.00,
            years=10,
            future_value=1629.00,
            total_interest=628.90,
        )
        calc = Calculation.objects.get(pk=calc.pk)
        expected = "P=1000.1, r=5%, n=10 → A=1629"
        self.assertEqual(str(calc), expected)

    def test_model_str_scientific_notation(self):
        """Calculation.__str__ uses scientific notation for extreme values via :g format."""
        calc = Calculation.objects.create(
            principal=1e16,
            interest_rate=100,
            years=50,
            future_value=1e31,
            total_interest=1e31,
        )
        calc = Calculation.objects.get(pk=calc.pk)
        result = str(calc)
        self.assertIn('e+', result.lower())


class SettingsTests(TestCase):
    def _reload_settings(self):
        """Reload config.settings with load_dotenv disabled to isolate env vars."""
        import config.settings as settings_module
        with patch('dotenv.load_dotenv'):
            importlib.reload(settings_module)
        return settings_module

    def _restore_settings(self):
        """Restore config.settings to its original state."""
        import config.settings as settings_module
        importlib.reload(settings_module)

    def test_secret_key_missing_in_production_raises(self):
        """Missing DJANGO_SECRET_KEY with DEBUG=False raises ImproperlyConfigured."""
        env = {
            k: v for k, v in __import__('os').environ.items()
            if k not in ('DJANGO_SECRET_KEY', 'DJANGO_DEBUG')
        }
        env['DJANGO_DEBUG'] = 'False'
        with patch.dict('os.environ', env, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                self._reload_settings()
        self._restore_settings()

    def test_debug_env_parsing(self):
        """DEBUG setting correctly parses various env values."""
        cases = {
            'True': True,
            '1': True,
            'true': True,
            'False': False,
            '0': False,
            'false': False,
        }
        for env_val, expected in cases.items():
            with self.subTest(env_val=env_val):
                with patch.dict('os.environ', {'DJANGO_DEBUG': env_val}):
                    settings_module = self._reload_settings()
                    self.assertEqual(settings_module.DEBUG, expected)
        # Test absent (defaults to False)
        env_no_debug = {
            k: v for k, v in __import__('os').environ.items()
            if k != 'DJANGO_DEBUG'
        }
        with patch.dict('os.environ', env_no_debug, clear=True):
            settings_module = self._reload_settings()
            self.assertFalse(settings_module.DEBUG)
        self._restore_settings()

    def test_allowed_hosts_parsing(self):
        """ALLOWED_HOSTS correctly splits, strips, and filters empty values."""
        cases = [
            ('host1,,host2', ['host1', 'host2']),
            ('', []),
            (' host1 , host2 ', ['host1', 'host2']),
            ('single', ['single']),
        ]
        for env_val, expected in cases:
            with self.subTest(env_val=env_val):
                with patch.dict('os.environ', {'DJANGO_ALLOWED_HOSTS': env_val}):
                    settings_module = self._reload_settings()
                    self.assertEqual(settings_module.ALLOWED_HOSTS, expected)
        self._restore_settings()
