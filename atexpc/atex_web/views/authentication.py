from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import FormView

from atexpc.atex_web.views.base import HybridGenericView, JSONResponseMixin
from atexpc.atex_web.utils import FrozenDict
from atexpc.atex_web.forms import user_form_factory


class LoginBase(FormView, HybridGenericView):
    template_name = "login.html"
    breadcrumbs = [FrozenDict(name="Login/Register",
                              url=reverse_lazy('login'))]
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super(LoginBase, self).get_context_data(**kwargs)
        signup_form = user_form_factory(True, self.api)
        context['signup_form'] = signup_form(data=self.request.POST or None)
        if 'form' not in context:   # show full unbound form on first view
            context['form'] = signup_form()
        return context

    def get_form_class(self):
        is_signup = 'signup' in self.request.POST
        return user_form_factory(is_signup, self.api)

    def form_valid(self, form):
        login(self.request, form.get_user())
        logger.info('Login %s', self.request.user.email)
        return super(LoginBase, self).form_valid(form)


class GetEmails(JSONResponseMixin, ListView):
    """ List user emails that begin with the specified username, e.g. username@anydomain.com """
    
    context_object_name = 'emails'
    json_exclude = ('object_list', 'view', 'paginator', 'page_obj', 'is_paginated')

    def get_queryset(self):
        username_filter = self.kwargs.get('username') + '@'
        users_beginning_with = get_user_model().objects.filter(email__startswith=username_filter)
        emails = [user.email for user in users_beginning_with]
        return emails
