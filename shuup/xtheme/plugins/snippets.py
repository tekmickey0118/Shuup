# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.xtheme import Plugin, resources
from shuup.xtheme.resources import add_resource, InlineMarkupResource


class SnippetsPlugin(Plugin):
    """
    Simple plugin class for including snippets and resources on the page, mostly for simple integrations.
    """
    identifier = "snippets"
    name = _("Snippets")
    fields = [
        ("in_place", forms.CharField(label=_("In-Place Snippet"), widget=forms.Textarea, required=False)),
        ("head_end", forms.CharField(label=_("Resource snippet for end of head"), widget=forms.Textarea,
                                     required=False)),
        ("body_start", forms.CharField(label=_("Resource snippet for beginning of body"), widget=forms.Textarea,
                                       required=False)),
        ("body_end", forms.CharField(label=_("Resource for end of body"), widget=forms.Textarea, required=False)),
    ]

    def render(self, context):
        for location, __ in self.fields:
            if location in resources.KNOWN_LOCATIONS:
                resource = self.config.get(location, "")
                add_resource(context, location, InlineMarkupResource(resource))
        return self.config.get("in_place", "")
