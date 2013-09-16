# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model
from django.core.validators import validate_email
from django.forms.widgets import (TextInput, PasswordInput, HiddenInput, 
    CheckboxInput, RadioSelect, Select, Textarea)

# ROCNPField, ROPhoneNumberField, ROCIFField, ROIBANField, ROCountyField, ROCountySelect
from localflavor.ro import forms as roforms

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
                                    "placeholder": "Caută produsul dorit ..."}),
            initial='',
            required=False)
        cauta_in = forms.TypedChoiceField(
            widget=Select(attrs={"class": "categorii delegate_filter",
                                 "placeholder": "Selectează categoria în care cauţi"}),
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
                                    "placeholder": "prenume"}))
        last_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "nume de familie"}))
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


def order_form_factory(form_type, user, delivery=False):
    """ Return a personalized order form based on type of client
        e.g. f = "Persoana fizica", j = "... juridica"
        If he wants delivery he must also fill in the delivery_address """

    delivery_default = 'same' if delivery else 'no'
    delivery_required = False

    class BaseOrderForm(forms.Form):
        customer_type = forms.ChoiceField(
            widget=RadioSelect(),
            choices=(('f', 'Persoana fizica'), ('j', 'Persoana juridica'), ('o', 'ONG')),
            initial='f')
        username = forms.EmailField(
            widget=TextInput(attrs={"class": "input_cos"}),
            initial=user.email)
        first_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "prenume"}),
            initial=user.first_name)
        last_name = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "nume de familie"}),
            initial=user.last_name)
        phone = roforms.ROPhoneNumberField(
            max_length=None, min_length=None,
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "telefon"}))
        city = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "localitatea"}))
        county = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "judetul"}))
        address = forms.CharField(
            widget=Textarea(attrs={"class": "input_cos",
                                   "placeholder": "adresa (cod postal, strada, nr, bloc, scara, etaj, apartament)"}))
        delivery = forms.ChoiceField(
            widget=RadioSelect(),
            choices=(('no', 'Ridic de la sediul Atex Computer'),
                     ('same', 'La adresa de facturare'),
                     ('other', 'La alta adresa')),
            initial=delivery_default)
        delivery_city = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "localitatea"}),
            required=delivery_required)
        delivery_county = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "judetul"}),
            required=delivery_required)
        delivery_address = forms.CharField(
            widget=Textarea(attrs={"class": "input_cos",
                                   "placeholder": "adresa (cod postal, strada, nr, bloc, scara, etaj, apartament)"}),
            required=delivery_required)
        notes = forms.CharField(
            widget=Textarea(attrs={"class": "input_cos",
                                   "placeholder": "observatii ..."}),
            initial='',
            required=False)

    class PersonOrderForm(BaseOrderForm):
        cnp = roforms.ROCNPField(
            max_length=None, min_length=None,
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "CNP"}))

    class CompanyInfo(forms.Form):
        company = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "Nume firma"}))
        bank = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "Banca"}))
        bank_account = roforms.ROIBANField(
            max_length=None, min_length=None,
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "Cont bana (IBAN)"}))

    class CompanyOrderForm(BaseOrderForm, CompanyInfo):
        cui = roforms.ROCIFField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "Cod unic (CUI)"}))
        vat = forms.BooleanField(
            widget=CheckboxInput(attrs={"class": "checkbox"}),
            initial=False,
            required=False)
        regcom = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "Cod înregistrare (Reg. Com.)"}))

    class ONGOrderForm(BaseOrderForm, CompanyInfo):
        cif = roforms.ROCIFField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "Cod de identificare fiscală (CIF)"}))

    form_types = {'f': PersonOrderForm,
                  'j': CompanyOrderForm,
                  'o': ONGOrderForm}
    return form_types.get(form_type, BaseOrderForm)
