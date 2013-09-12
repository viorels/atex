# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model
from django.core.validators import validate_email
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


def user_form_factory(is_signup, api):
    class LoginForm(auth_forms.AuthenticationForm):
        username = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos"}))
        password = forms.CharField(
            widget=PasswordInput(attrs={"id": "masked_password",
                                        "class": "input_cos"}))

    class SignupForm(LoginForm):
        first_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "prenume"}))
        last_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "nume de familie"}))
        terms = forms.BooleanField( # Am citit si sunt de acord cu Termenii & Conditii de utilizare
            widget=CheckboxInput(attrs={"id": "terms_checkbox",
                                        "class": "checkbox"}),
            initial=True)
        newsletter = forms.BooleanField( # Doresc sa fiu informat, prin email, despre produsele ATEX
            widget=CheckboxInput(attrs={"id": "newsletter_checkbox",
                                        "class": "checkbox"}),
            initial=False,
            required=False)

        def clean_username(self):
            email = self.cleaned_data['username']
            validate_email(email)
            return email

        def clean(self):
            if (not self._errors):
                user_info = {'email': self.cleaned_data.get('username'),
                             'first_name': self.cleaned_data.get('first_name'),
                             'last_name': self.cleaned_data.get('last_name')}
                ancora_user_id = api.users.create_or_update_user(**user_info)
                user_info['ancora_id'] = ancora_user_id
                user_info['password'] = self.cleaned_data.get('password')
                user = get_user_model().objects.create_user(**user_info)
            return super(SignupForm, self).clean()

        def get_user(self):
            return self.user_cache

    if is_signup:
        return SignupForm
    else:
        return LoginForm


def order_form_factory(form_type):
    class BaseOrderForm(forms.Form):
        customer_type = forms.ChoiceField(
            widget=RadioSelect(),
            choices=(('f', 'Persoana fizica'), ('j', 'Persoana juridica'), ('o', 'ONG')),
            initial='f')
        first_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "prenume"}))
        last_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "nume de familie"}))
        phone = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "telefon"}))
        city = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "localitatea"}))
        county = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "judetul"}))
        address = forms.CharField(
            widget=Textarea(attrs={"class": "input_cos",
                                   "title": "adresa (cod postal, strada, nr, bloc, scara, etaj, apartament)"}))
        delivery = forms.ChoiceField(
            widget=RadioSelect(),
            choices=(('no', 'Ridicare de la sediul Atex'), 
                     ('same', 'Adresa de facturare'),
                     ('other', 'Alta adresa')))
        delivery_city = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "localitatea"}),
            required=False)
        delivery_county = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "judetul"}),
            required=False)
        delivery_address = forms.CharField(
            widget=Textarea(attrs={"class": "input_cos",
                                   "title": "adresa (cod postal, strada, nr, bloc, scara, etaj, apartament)"}),
            required=False)

    class PersonOrderForm(BaseOrderForm):
        cnp = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "CNP"}))

    class CompanyInfo(forms.Form):
        company = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "Nume firma"}))
        bank = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "Banca"}))
        bank_account = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "Cont bana (IBAN)"}))

    class CompanyOrderForm(BaseOrderForm, CompanyInfo):
        cui = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "Cod unic (CUI)"}))
        regcom = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "Cod înregistrare (Reg. Com.)"}))
        vat = forms.BooleanField(
            widget=CheckboxInput(attrs={"class": "checkbox"}),
            initial=False,
            required=False)

    class ONGOrderForm(BaseOrderForm, CompanyInfo):
        cif = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "title": "Cod de identificare fiscală (CIF)"}))

    form_types = {'f': PersonOrderForm,
                  'j': CompanyOrderForm,
                  'o': ONGOrderForm}
    return form_types[form_type]
