# -*- coding: utf-8 -*-
"""
    flaskbb.utils.markup
    ~~~~~~~~~~~~~~~~~~~~

    A module for all markup related stuff like markdown and emojis.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import re

from flask import url_for

import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound


_re_emoji = re.compile(r':([a-z0-9\+\-_]+):', re.I)
_re_user = re.compile(r'@(\w+)', re.I)
_re_youtube = re.compile(
    r'^((https?)://)?((www.)?youtube\.com/watch\?v=|youtu\.be/)' +
    r'([A-Za-z0-9_-]{11})\s*$'
)

# base directory of flaskbb - used to collect the emojis
_basedir = os.path.join(os.path.abspath(os.path.dirname(
                        os.path.dirname(__file__))))


def collect_emojis():
    """Returns a dictionary containing all emojis with their
    name and filename. If the folder doesn't exist it returns a empty
    dictionary.
    """
    emojis = dict()
    full_path = os.path.join(_basedir, "static", "emoji")
    # return an empty dictionary if the path doesn't exist
    if not os.path.exists(full_path):
        return emojis

    for emoji in os.listdir(full_path):
        name, ending = emoji.split(".")
        if ending in ["png", "gif", "jpg", "jpeg"]:
            emojis[name] = emoji

    return emojis

EMOJIS = collect_emojis()


class FlaskBBRenderer(mistune.Renderer):
    """Markdown with some syntetic sugar such as @user gets linked to the
    user's profile and emoji support.
    """
    def __init__(self, **kwargs):
        super(FlaskBBRenderer, self).__init__(**kwargs)

    def paragraph(self, text):
        """Rendering paragraph tags. Like ``<p>`` with emoji support."""

        def emojify(match):
            value = match.group(1)

            if value in EMOJIS:
                filename = url_for(
                    "static",
                    filename="emoji/{}".format(EMOJIS[value])
                )

                emoji = "<img class='{css}' alt='{alt}' src='{src}' />".format(
                    css="emoji", alt=value,
                    src=filename
                )
                return emoji
            return match.group(0)

        def userify(match):
            value = match.group(1)
            user = "<a href='{url}'>@{user}</a>".format(
                url=url_for("user.profile", username=value, _external=False),
                user=value
            )
            return user

        text = _re_emoji.sub(emojify, text)
        text = _re_user.sub(userify, text)

        return '<p>%s</p>\n' % text.strip(' ')

    def block_code(self, code, lang):
        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                lexer = None
        else:
            lexer = None
        if not lexer:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)

    def autolink(self, link, is_email=False):
        if is_email:
            match = None
        else:
            match = _re_youtube.match(link)
        if match:
            return (
                '<span class="embed-responsive embed-responsive-16by9">' +
                '<iframe src="https://www.youtube-nocookie.com/embed/' +
                match.group(5) +
                '?rel=0" allowfullscreen></iframe>' +
                '</span>'
            )
        else:
            return super().autolink(link, is_email)


renderer = FlaskBBRenderer(escape=True, hard_wrap=True)
markdown = mistune.Markdown(renderer=renderer)
