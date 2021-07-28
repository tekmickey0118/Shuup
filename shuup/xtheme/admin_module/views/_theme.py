# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import URLActionButton, get_default_edit_toolbar
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.admin.views.wizard import TemplatedWizardFormDef, WizardPane
from shuup.core import cache
from shuup.utils.django_compat import reverse
from shuup.utils.importing import cached_load
from shuup.xtheme._theme import get_theme_by_identifier, get_theme_cache_key, set_current_theme
from shuup.xtheme.forms import AdminThemeForm, FontForm
from shuup.xtheme.models import ThemeSettings, AdminThemeSettings, Font


class ActivationForm(forms.Form):
    """
    A very simple form for activating a theme.
    """

    activate = forms.CharField(label=_("activate"))
    selected_style = forms.CharField(required=False, widget=forms.HiddenInput())


class ThemeWizardPane(WizardPane):
    identifier = "theme"
    icon = "xtheme/theme.png"
    title = _("Theme")
    text = _("Choose a theme for your shop")

    def valid(self):
        from shuup.admin.utils.permissions import has_permission

        return has_permission(self.request.user, "telemetry")

    def visible(self):
        return ThemeSettings.objects.filter(active=False, shop=self.object).count() == 0

    def get_form_defs(self):
        shop = self.object
        context = cached_load("SHUUP_XTHEME_ADMIN_THEME_CONTEXT")(shop)
        context.update({"shop": shop})

        current_theme_class = context["current_theme"] or context["theme_classes"][0]
        current_theme_settings = ThemeSettings.objects.get_or_create(
            shop=shop, theme_identifier=current_theme_class.identifier
        )[0]
        context["active_stylesheet"] = current_theme_settings.data.get("settings", {}).get("stylesheet", None)

        return [
            TemplatedWizardFormDef(
                template_name="shuup/xtheme/admin/wizard.jinja",
                name="theme",
                form_class=ActivationForm,
                context=context,
            )
        ]

    def form_valid(self, form):
        identifier = form["theme"].cleaned_data["activate"]
        data = {"settings": {"stylesheet": form["theme"].cleaned_data["selected_style"]}}
        theme_settings, created = ThemeSettings.objects.get_or_create(
            theme_identifier=identifier, shop=get_shop(self.request)
        )
        if created:
            theme_settings.data = data
            theme_settings.save()
        else:
            theme_settings.update_settings(data["settings"])

        set_current_theme(identifier, self.object)
        cache.bump_version(get_theme_cache_key(get_shop(self.request)))


class ThemeConfigView(FormView):
    """
    A view for listing and activating themes.
    """

    template_name = "shuup/xtheme/admin/config.jinja"
    form_class = ActivationForm

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigView, self).get_context_data(**kwargs)
        shop = get_shop(self.request)
        context.update(cached_load("SHUUP_XTHEME_ADMIN_THEME_CONTEXT")(shop))
        return context

    def form_valid(self, form):
        identifier = form.cleaned_data["activate"]
        set_current_theme(identifier, get_shop(self.request))
        messages.success(self.request, _("Theme activated."))
        return HttpResponseRedirect(self.request.path)


class ThemeConfigDetailView(CreateOrUpdateView):
    """
    A view for configuring a single theme.
    """

    model = ThemeSettings
    template_name = "shuup/xtheme/admin/config_detail.jinja"
    form_class = forms.Form
    context_object_name = "theme_settings"
    add_form_errors_as_messages = True

    def get_object(self, queryset=None):
        return ThemeSettings.objects.get_or_create(
            theme_identifier=self.kwargs["theme_identifier"], shop=get_shop(self.request)
        )[0]

    def get_theme(self):
        """
        Get the theme object to configure.

        :return: Theme object.
        :rtype: shuup.xtheme.Theme
        """
        return get_theme_by_identifier(identifier=self.kwargs["theme_identifier"], shop=get_shop(self.request))

    def get_context_data(self, **kwargs):
        context = super(ThemeConfigDetailView, self).get_context_data(**kwargs)
        shop = get_shop(self.request)
        theme = self.get_theme()
        context["theme"] = theme
        context["guide"] = None

        if theme.guide_template:
            template = loader.get_template(theme.guide_template)
            context["guide"] = template.render({}, request=self.request)

        context["active_stylesheet"] = self.object.data.get("settings", {}).get("stylesheet", None)
        context["shop"] = shop
        return context

    def get_form(self, form_class=None):
        return self.get_theme().get_configuration_form(form_kwargs=self.get_form_kwargs())

    def get_success_url(self):
        return reverse("shuup_admin:xtheme.config_detail", kwargs={"theme_identifier": self.object.theme_identifier})

    def save_form(self, form):
        super(ThemeConfigDetailView, self).save_form(form)
        cache.bump_version(get_theme_cache_key(get_shop(self.request)))

    def get_toolbar(self):
        toolbar = get_default_edit_toolbar(self, self.get_save_form_id(), with_split_save=False)
        toolbar.append(
            URLActionButton(
                text=_("Custom CSS/JS"),
                icon="fa fa-magic",
                url=reverse("shuup_admin:xtheme_snippet.list"),
                extra_css_class="btn-info",
            )
        )
        return toolbar


class ThemeGuideTemplateView(TemplateView):
    template_name = None

    def dispatch(self, request, *args, **kwargs):
        theme = get_theme_by_identifier(kwargs["theme_identifier"], shop=get_shop(self.request))
        self.template_name = theme.guide_template
        return super(ThemeGuideTemplateView, self).dispatch(request, *args, **kwargs)


class FontEditView(CreateOrUpdateView):
    model = Font
    form_class = FontForm
    template_name = "shuup/xtheme/admin/font_create.jinja"
    context_object_name = "admin_font"

    def get_queryset(self):
        return Font.objects.filter(shop=get_shop(self.request))

    def get_form_kwargs(self):
        kwargs = super(FontEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(FontEditView, self).form_valid(form)


def AdminThemeConfigDetailView(request):
    """
    A view for editing the admin base theme.
    """

    context ={}
  
    current_theme = AdminThemeSettings.objects.get_or_create(shop=get_shop(request))

    if current_theme[0]:
        form = AdminThemeForm(request.POST or None, instance=current_theme[0])
    else:
        form = AdminThemeForm(request.POST or None)
      
    # check if form data is valid
    if form.is_valid() and request.method == 'POST':
        # save the form data to model
        form.save()
  
    context['form']= form
    return render(request, "shuup/xtheme/admin/admin_config_detail.jinja", context)
