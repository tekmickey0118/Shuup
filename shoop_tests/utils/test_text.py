# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.utils.text import snake_case, kebab_case, camel_case, flatten, space_case, identifierify


def test_casers():
    text = u"What is Love? Baby Don't Hurt Me"
    assert snake_case(text) == "what_is_love?_baby_don't_hurt_me"
    assert kebab_case(text) == "what-is-love?-baby-don't-hurt-me"
    assert camel_case(text) == "WhatIsLove?BabyDon'THurtMe"
    assert identifierify(snake_case(text)) == "what_is_love_baby_dont_hurt_me"
    assert identifierify(kebab_case(text), "-") == "what-is-love-baby-dont-hurt-me"
    assert identifierify(camel_case(text)) == "WhatIsLoveBabyDonTHurtMe"
    assert space_case("some_identifier") == "some identifier"


def test_flatten():
    text = "Whät is Löve? Bäby Don't Hurt Me"
    assert flatten(text) == "what-is-love?-baby-don't-hurt-me"
    assert flatten(text, "/") == "what/is/love?/baby/don't/hurt/me"
