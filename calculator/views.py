import math

from django.shortcuts import render

from .forms import CalculationForm
from .models import Calculation


def calculate(request):
    result = None

    if request.method == 'POST':
        form = CalculationForm(request.POST)
        if form.is_valid():
            principal = form.cleaned_data['principal']
            interest_rate = form.cleaned_data['interest_rate']
            years = form.cleaned_data['years']

            raw = principal * (1 + interest_rate / 100) ** years

            if not math.isfinite(raw):
                form.add_error(None, 'The result is too large to compute.')
            else:
                future_value = round(raw, 2)
                total_interest = round(future_value - principal, 2)

                Calculation.objects.create(
                    principal=principal,
                    interest_rate=interest_rate,
                    years=years,
                    future_value=future_value,
                    total_interest=total_interest,
                )

                result = {
                    'future_value': future_value,
                    'total_interest': total_interest,
                }
    else:
        form = CalculationForm()

    return render(request, 'calculator/calculate.html', {
        'form': form,
        'result': result,
    })
