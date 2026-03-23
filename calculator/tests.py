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


class CalculationModelTests(TestCase):
    def test_model_str(self):
        """Calculation.__str__ returns expected format."""
        calc = Calculation.objects.create(
            principal=1000,
            interest_rate=5,
            years=10,
            future_value=1628.89,
            total_interest=628.89,
        )
        expected = "P=1000, r=5%, n=10 → A=1628.89"
        self.assertEqual(str(calc), expected)
