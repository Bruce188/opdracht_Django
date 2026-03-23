from django import forms


class CalculationForm(forms.Form):
    principal = forms.FloatField(label='Principal Amount (P)', min_value=0)
    interest_rate = forms.FloatField(label='Annual Interest Rate (%)', min_value=0)
    years = forms.IntegerField(label='Number of Years (n)', min_value=1)
