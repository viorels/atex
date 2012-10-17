from django import forms
from django.forms.widgets import Select

SORT_CHOICES = (
    ('pret_asc', ' - pret crescator - '),
    ('pret_desc', ' - pret descrescator - '),
    ('vanzari_desc', ' - cele mai vandute - '))

PER_PAGE_CHOICES = ((str(choice),)*2 for choice in (20, 40, 60))

class SearchForm(forms.Form):
    ordine = forms.ChoiceField(
        widget=Select(attrs={'class': 'filter submit'}),
        choices=SORT_CHOICES)
    pe_pagina = forms.ChoiceField(
        widget=Select(attrs={'class': 'filter submit'}),
        choices=PER_PAGE_CHOICES)
