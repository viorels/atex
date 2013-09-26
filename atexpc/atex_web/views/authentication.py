from django.conf import settings
from django.contrib.auth import get_user_model, login, REDIRECT_FIELD_NAME
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

from password_reset.views import Recover

from atexpc.atex_web.views.base import HybridGenericView, JSONResponseMixin
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
        return user_form_factory(self.is_signup, self.api)

    def form_valid(self, form):
        login(self.request, form.get_user())
        logger.info('Login %s', self.request.user.email)
        return super(LoginBase, self).form_valid(form)

    def form_invalid(self, form):
        logger.info('Login invalid %s', self.login_type)
        if self.login_type == 'nopassword':
            logger.info('Reset password')

            return RecoverPassword.as_view()(self.request)
            # email = form.cleaned_data['username']
            # user = get_user_model().objects.get_or_none(email=email)
            # if user:
                # password_reset function does not allow changing unusable passwords
                # if not user.has_usable_password():
                #     random_password = get_user_model().objects.make_random_password()
                #     user.set_password(random_password)
                #     user.save()

                # self.request.POST = self.request.POST.copy()
                # self.request.POST['email'] = email
                # return password_reset(request=self.request,
                #                       template_name=self.template_name)
        return super(LoginBase, self).form_invalid(form)

    def get_success_url(self):
        redirect_to = self.request.REQUEST.get(REDIRECT_FIELD_NAME, '')
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = settings.LOGIN_REDIRECT_URL
        return redirect_to

    def get_context_data(self, **kwargs):
        context = super(LoginBase, self).get_context_data(**kwargs)
        signup_form = user_form_factory(is_signup=True, api=self.api)
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


class RecoverPassword(Recover, HybridGenericView):
    template_name = LoginBase.template_name
    search_fields = ['username', 'email']


@receiver(user_logged_out)
def log_out_handler(sender, **kwargs):
     pass   # "do your custom stuff here"
