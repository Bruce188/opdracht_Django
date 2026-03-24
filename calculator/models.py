from django.db import models


class Calculation(models.Model):
    principal = models.FloatField()
    interest_rate = models.FloatField()
    years = models.IntegerField()
    future_value = models.FloatField()
    total_interest = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"P={self.principal:g}, r={self.interest_rate:g}%, n={self.years} → A={self.future_value:g}"
