# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import forms as auth_forms, authenticate
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

def user_form_factory(logintype, api):
    is_signup = logintype == 'new'

    class LoginForm(auth_forms.AuthenticationForm):
        logintype = forms.ChoiceField(
            widget=RadioSelect(),
            choices=(('new', 'Client nou'), ('old', 'Client vechi')),
            initial='',
            required=True)
        username = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "email"}),
            required=not is_signup)
        password = forms.CharField(
            widget=PasswordInput(attrs={"class": "input_cos",
                                        "title": "parola"}),
            required=not is_signup)

    class SignupForm(LoginForm):
        first_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "prenume"}),
            required=True)
        last_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "nume"}),
            required=True)
        usertype = forms.ChoiceField(
                widget=RadioSelect(),
                choices=(('f', 'Persoana fizica'), ('j', 'Persoana juridica')),
                initial='',
                required=True)
        terms = forms.BooleanField( # Am citit si sunt de acord cu Termenii & Conditii de utilizare
            widget=CheckboxInput(),
            initial="",
            required=True)
        newsletter = forms.BooleanField( # Doresc sa fiu informat, prin email, despre produsele ATEX
            widget=CheckboxInput(),
            initial="",
            required=True)

        def clean(self):
            cleaned_data = super(SignupForm, self).clean()
            email = cleaned_data['username']
            password = cleaned_data['password']
            first_name = cleaned_data['first_name']
            last_name = cleaned_data['last_name']
            result = api.users.create_user(email=email,
                                           first_name=first_name,
                                           last_name=last_name,
                                           password=password,
                                           usertype='F')
            user = authenticate(email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            self.user_cache = user

        def get_user(self):
            return self.user_cache


    if is_signup:
        return SignupForm
    else:
        return LoginForm


class DeliveryAddressForm(forms.Form):
    phone = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "telefon"}),
        required=True)
    city = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "localitatea"}),
        required=True)
    county = forms.CharField(
        widget=TextInput(attrs={"class": "input_cos",
                                "title": "judetul"}),
        required=True)
    address = forms.CharField(
        widget=Textarea(attrs={"class": "input_cos",
                               "title": "adresa (cod postal, strada, nr, bloc, scara, etaj, apartament)"}),
        required=True)
