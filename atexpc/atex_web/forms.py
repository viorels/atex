# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model
from django.core.validators import validate_email
from django.forms.widgets import (TextInput, PasswordInput, HiddenInput, 
    CheckboxInput, RadioSelect, Select, Textarea)
from haystack.forms import FacetedSearchForm

# ROCNPField, ROPhoneNumberField, ROCIFField, ROIBANField, ROCountyField, ROCountySelect
from localflavor.ro import forms as roforms

SORT_CHOICES = (
    ('pret_asc', ' - pret crescator - '),
    ('pret_desc', ' - pret descrescator - '),
    ('vanzari_desc', ' - cele mai vandute - '))

PER_PAGE_CHOICES = tuple((choice, str(choice)) for choice in (20, 40, 60))

def search_form_factory(search_in_choices, advanced=False):
    SEARCH_IN_CHOICES = (("", "- Toate Categoriile -"),) + search_in_choices

    class SearchForm(FacetedSearchForm):
        q = forms.CharField(
            widget=TextInput(attrs={"type": "search",
                                    "class": "search delegate_filter",
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
        login_type = forms.ChoiceField(
            widget=RadioSelect(),
            choices=(('new', 'Sunt client nou'),
                     ('password', 'Am deja parola'),
                     ('nopassword', 'Nu știu parola')))
        username = forms.EmailField(
            widget=TextInput(attrs={"type": "email",
                                    "class": "input_cos"}))
        password = forms.CharField(
            widget=PasswordInput(attrs={"id": "masked_password",
                                        "class": "input_cos"}))

        def clean(self):
            email = self.cleaned_data.get('username')

            user_exists = get_user_model().objects.get_or_none(email=email)
            if not user_exists:
                # self.cleaned_data['login_type'] = 'new'
                raise forms.ValidationError('Nu am găsit contul dar poți creea unul')

            return super(LoginForm, self).clean()

    class SignupForm(LoginForm):
        first_name = forms.CharField(
            label="Prenume",
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "prenume"}))
        last_name = forms.CharField(
            label="Nume",
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

        def clean(self):
            email = self.cleaned_data.get('username')

            user_exists = get_user_model().objects.get_or_none(email=email)
            if user_exists:
                # self.cleaned_data['login_type'] = 'password'
                raise forms.ValidationError('Ai deja un cont, '
                    'incearcă parola sau reseteaz-o')

            if not self._errors:
                user_info = {'email': email,
                             'first_name': self.cleaned_data.get('first_name'),
                             'last_name': self.cleaned_data.get('last_name')}
                ancora_user_id = api.users.create_or_update_user(**user_info)
                user_info['ancora_id'] = ancora_user_id
                user_info['password'] = self.cleaned_data.get('password')
                user = get_user_model().objects.create_user(**user_info)
            return super(SignupForm, self).clean()

    if is_signup:
        return SignupForm
    else:
        return LoginForm


def order_form_factory(form_type, user, customers=[], addresses=[], delivery=False):
    """ Return a personalized order form based on type of client
        e.g. f = "Persoana fizica", j = "... juridica"
        If he wants delivery he must also fill in the delivery_address """

    customer_choices = [(c['customer_id'], c['name']) for c in customers] + \
                       [(0, 'Persoană/firmă nouă')]
    default_customer = customers[-1]['customer_id'] if customers else 0

    unique_addresses = dict((a['address'], a) for a in addresses).values()
    address_choices = [(a['address_id'], a['address']) for a in unique_addresses] + \
                      [(-1, 'Adresa de facturare'), (0, 'Adresă nouă')]
    address_default = -1

    delivery_default = 'yes' if delivery else 'no'

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
                                    "placeholder": "telefon"}),
            initial=user.phone)
        customer = forms.TypedChoiceField(
            widget=Select(attrs={"class": "input_cos"}),
            choices=customer_choices,
            initial=default_customer,
            coerce=int,
            required=True)
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
                     ('yes', 'Selectați adresa de livrare')),
            initial=delivery_default)
        delivery_address_id = forms.TypedChoiceField(
            widget=Select(attrs={"class": "input_cos"}),
            choices=address_choices,
            initial=address_default,
            coerce=int)
        delivery_city = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "localitatea"}),
            required=False)
        delivery_county = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "judetul"}),
            required=False)
        delivery_address = forms.CharField(
            widget=Textarea(attrs={"class": "input_cos",
                                   "placeholder": "adresa (cod postal, strada, nr, bloc, scara, etaj, apartament)"}),
            required=False)
        notes = forms.CharField(
            widget=Textarea(attrs={"class": "input_cos",
                                   "placeholder": "observatii ..."}),
            initial='',
            required=False)

        def clean(self):
            cleaned_data = super(BaseOrderForm, self).clean()

            if cleaned_data.get('delivery') == 'yes':
                delivery_address_id = cleaned_data.get("delivery_address_id")
                customer_id = cleaned_data.get("customer")

                # if user selected "same address as in invoice"
                if delivery_address_id == -1:
                    cleaned_data['delivery_county'] = cleaned_data.get('county')
                    cleaned_data['delivery_city'] = cleaned_data.get('city')
                    cleaned_data['delivery_address'] = cleaned_data.get('address')
                elif delivery_address_id > 0:
                    matched_addresses = [a for a in addresses
                                         if a['address_id'] == delivery_address_id]
                    if matched_addresses:
                        cleaned_data['delivery_county'] = matched_addresses[0]['county']
                        cleaned_data['delivery_city'] = matched_addresses[0]['city']
                        cleaned_data['delivery_address'] = matched_addresses[0]['address']

                # check if address id belongs to this customer or we need to create a new address
                def delivery_is_address(delivery, other):
                    return all(delivery.get("delivery_" + field).lower() == other.get(field).lower()
                               for field in ('address', 'city', 'county'))
                matched_addresses = [a for a in addresses
                                     if a['customer_id'] == customer_id
                                     and delivery_is_address(cleaned_data, a)]
                if matched_addresses:
                    delivery_address_id = matched_addresses[0]['address_id']
                else:
                    delivery_address_id = 0

                cleaned_data['delivery_address_id'] = delivery_address_id

            # Always return the full collection of cleaned data.
            return cleaned_data

    class PersonOrderForm(BaseOrderForm):
        cnp = roforms.ROCNPField(
            max_length=None, min_length=None,
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "CNP"}))

    class CompanyInfo(forms.Form):
        company = forms.CharField(
            widget=TextInput(attrs={"class": "input_cos",
                                    "placeholder": "Nume firma"}))
        vat = forms.BooleanField(
            widget=CheckboxInput(attrs={"class": "checkbox"}),
            initial=False,
            required=False)
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
