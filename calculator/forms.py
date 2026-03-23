from django import forms


class CalculationForm(forms.Form):
    principal = forms.FloatField(label='Principal Amount (P)', min_value=0.01, max_value=1_000_000_000)
    interest_rate = forms.FloatField(label='Annual Interest Rate (%)', min_value=0, max_value=1000)
    years = forms.IntegerField(label='Number of Years (n)', min_value=1, max_value=100)
