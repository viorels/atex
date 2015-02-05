from django.conf import settings
from django.contrib.auth import get_user_model, login, authenticate, REDIRECT_FIELD_NAME
from django.contrib.auth.signals import user_logged_out
from django.core.urlresolvers import reverse_lazy
from django.dispatch import receiver
from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _

from password_reset.views import Recover, RecoverDone, Reset, ResetDone

from atexpc.atex_web.views.base import BaseView, HybridGenericView, JSONResponseMixin
from atexpc.atex_web.utils import FrozenDict
from atexpc.atex_web.forms import user_form_factory

import logging
logger = logging.getLogger(__name__)


class LoginBase(FormView, HybridGenericView):
    template_name = "login.html"
    breadcrumbs = [FrozenDict(name=_('Sign up') + '/' + _('Log in'),
                              url=reverse_lazy('login'))]

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        self.login_type = self.request.POST.get('login_type')
        self.is_signup = self.login_type == 'new'
        return super(LoginBase, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        return user_form_factory(self.is_signup, self.request.api)

    def form_valid(self, form):
        login(self.request, form.get_user())
        logger.info('Login %s', self.request.user.email)
        return super(LoginBase, self).form_valid(form)

    def form_invalid(self, form):
        logger.info('Login invalid %s', self.login_type)
        if self.login_type == 'nopassword':
            email = form.cleaned_data.get('username')
            logger.info('Reset password for %s', email)
            return RecoverPasswordView.as_view()(self.request)

        return super(LoginBase, self).form_invalid(form)

    def get_success_url(self):
        redirect_to = self.request.REQUEST.get(REDIRECT_FIELD_NAME, '')
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = settings.LOGIN_REDIRECT_URL
        return redirect_to

    def get_context_data(self, **kwargs):
        context = super(LoginBase, self).get_context_data(**kwargs)
        signup_form = user_form_factory(is_signup=True, api=self.request.api)
        context['signup_form'] = signup_form(data=self.request.POST or None)
        if 'form' not in context:   # show full unbound form on first view
            context['form'] = signup_form()
        return context


class GetEmails(JSONResponseMixin, ListView):
    """ List user emails that begin with the specified username, e.g. username@anydomain.com """

    context_object_name = 'emails'
    json_exclude = ('object_list', 'view', 'paginator', 'page_obj', 'is_paginated')

    def get_queryset(self):
        username_filter = self.kwargs.get('username') + '@'
        users_beginning_with = get_user_model().objects.filter(email__startswith=username_filter)
        emails = [user.email for user in users_beginning_with]
        return emails


class RecoverPasswordView(Recover, BaseView):
    template_name = LoginBase.template_name     # 'password_reset/recovery_form.html'
    email_subject_template_name = 'password/recovery_email_subject.txt'
    email_template_name = 'password/recovery_email.txt'
    search_fields = ['email']

    def get_form_kwargs(self):
        kwargs = super(RecoverPasswordView, self).get_form_kwargs()
        kwargs['data'] = self.request.POST.copy()
        kwargs['data']['username_or_email'] = kwargs['data'].get('username')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RecoverPasswordView, self).get_context_data(**kwargs)
        
        context['reset_form'] = context['form']

        signup_form = user_form_factory(is_signup=True, api=self.request.api)
        context['signup_form'] = signup_form(data=self.request.POST or None)
        context['form'] = signup_form()
        
        return context

class RecoverPasswordDoneView(RecoverDone, BaseView):
    template_name = 'password/reset_sent.html'


class ResetPasswordView(Reset, BaseView):
    template_name = 'password/reset.html'

    def get_context_data(self, **kwargs):
        context = super(ResetPasswordView, self).get_context_data(**kwargs)

        # TODO: move this patch to a base class
        # this is needed because TemplateView.get overrites ProcessFormView.get
        if self.request.method == 'GET':
            context['form'] = self.get_form(self.get_form_class())

        return context

    def form_valid(self, form):
        valid = super(ResetPasswordView, self).form_valid(form)
        user = authenticate(email=form.user.email, password=form.cleaned_data['password1'])
        if user is not None:
            login(self.request, user)
            logger.info('Login %s', self.request.user.email)
        return valid

class ResetPasswordDoneView(ResetDone, BaseView):
    template_name = 'password/recovery_done.html'


@receiver(user_logged_out)
def log_out_handler(sender, **kwargs):
     pass   # "do your custom stuff here"
