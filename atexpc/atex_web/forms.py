# -*- coding: utf-8 -*-

from django import forms
from django.forms.widgets import (TextInput, PasswordInput, HiddenInput, 
    CheckboxInput, RadioSelect, Select, Textarea)

SORT_CHOICES = (
    ('pret_asc', ' - pret crescator - '),
    ('pret_desc', ' - pret descrescator - '),
    ('vanzari_desc', ' - cele mai vandute - '))

PER_PAGE_CHOICES = tuple((choice, str(choice)) for choice in (20, 40, 60))

def search_form_factory(search_in_choices, advanced=False):
    SEARCH_IN_CHOICES = (("", "- Toate Categoriile -"),) + search_in_choices

    class SearchForm(forms.Form):
        cuvinte = forms.CharField(
            widget=TextInput(attrs={"class": "search delegate_filter",
                                    "title": "Caută produsul dorit ..."}),
            initial='',
            required=False)
        cauta_in = forms.TypedChoiceField(
            widget=Select(attrs={"class": "categorii delegate_filter",
                                 "title": "Selectează categoria în care cauţi"}),
            choices=SEARCH_IN_CHOICES,
            coerce=int,
            required=False)

    class AdvancedSearchForm(SearchForm):
        categorie = forms.IntegerField(
            widget=HiddenInput(), required=False)
        ordine = forms.ChoiceField(
            widget=Select(attrs={"class": "delegate_filter submit"}),
            choices=SORT_CHOICES,
            initial='pret_asc',
            required=False)
        pe_pagina = forms.TypedChoiceField(
            widget=Select(attrs={"class": "delegate_filter submit"}),
            choices=PER_PAGE_CHOICES,
            coerce=int,
            initial=20,
            required=False)
        stoc = forms.BooleanField(
            widget=CheckboxInput(attrs={"class": "checkbox delegate_filter submit"}),
            initial="",
            required=False)
        pagina = forms.IntegerField(initial=1, required=False)
        pret_min = forms.IntegerField(initial='', required=False)
        pret_max = forms.IntegerField(initial='', required=False)

    return AdvancedSearchForm if advanced else SearchForm


class OrderForm(forms.Form):
    # logintype
    user = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "email"}),
        required=True)
    password = forms.CharField(
        widget=PasswordInput(attrs={"class": "input_cos",
                                    "title": "parola"}),
        required=False)

    surname = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "nume"}),
        required=False)
    firstname = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "prenume"}),
        required=False)
    email = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "adresa email"}),
        required=False)
    phone = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "telefon"}),
        required=False)
    password1 = forms.CharField(
        widget=PasswordInput(attrs={"class": "input_cos",
                                "title": "parola"}),
        required=False)
    password2 = forms.CharField(
        widget=PasswordInput(attrs={"class": "input_cos",
                                "title": "repeta parola"}),
        required=False)
    usertype = forms.ChoiceField(
            widget=RadioSelect(),
            choices=(('f', 'Persoana fizica'), ('j', 'Persoana juridica')),
            initial='',
            required=False)
    city = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "localitatea"}),
        required=False)
    county = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "judetul"}),
        required=False)
    address = forms.CharField(
        widget=Textarea(attrs={"class": "input_cos",
                               "title": "adresa (cod postal, strada, nr, bloc, scara, etaj, apartament)"}),
        required=False)