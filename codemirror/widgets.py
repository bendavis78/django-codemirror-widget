# -*- coding: utf-8 -*-
#
# Created:    2010/09/09
# Author:         alisue
#
import json, re
from itertools import chain
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

# set default settings
CODEMIRROR_PATH = getattr(settings, 'CODEMIRROR_PATH', 'codemirror')
if CODEMIRROR_PATH.endswith('/'):
    CODEMIRROR_PATH = CODEMIRROR_PATH[:-1]
CODEMIRROR_MODE = getattr(settings, 'CODEMIRROR_MODE', 'javascript')
CODEMIRROR_THEME = getattr(settings, 'CODEMIRROR_THEME', 'default')
CODEMIRROR_CONFIG = getattr(settings, 'CODEMIRROR_CONFIG', { 'lineNumbers': True })
CODEMIRROR_JS_VAR_FORMAT = getattr(settings, 'CODEMIRROR_JS_VAR_FORMAT', None)

THEME_CSS_FILENAME_RE = re.compile(r'[\w-]+')

def isstring(obj):
    try:
        return isinstance(obj, basestring)
    except NameError:
        return isinstance(obj, str)

class CodeMirrorTextarea(forms.Textarea):
    u"""Textarea widget render with `CodeMirror`

    CodeMirror:
        http://codemirror.net/
    """
    
    @property
    def media(self):
        mode_name = self.mode_name
        return forms.Media(css = {
                'all': ("%s/lib/codemirror.css" % CODEMIRROR_PATH,) +
                    tuple("%s/theme/%s.css" % (CODEMIRROR_PATH, theme_css_filename)
                        for theme_css_filename in self.theme_css),
            },
            js = (
                "%s/lib/codemirror.js" % CODEMIRROR_PATH,
                "%s/mode/%s/%s.js" % (CODEMIRROR_PATH, mode_name, mode_name),
            ) + tuple(
                "%s/mode/%s/%s.js" % (CODEMIRROR_PATH, dependency, dependency)
                    for dependency in self.dependencies)
            )
    
    def __init__(self, attrs=None, mode=None, theme=None, config=None, dependencies=(), js_var_format=None, **kwargs):
        u"""Constructor of CodeMirrorTextarea

        Attribute:
            path          - CodeMirror directory URI (DEFAULT = settings.CODEMIRROR_PATH)
            mode          - Name of language or a modal configuration object as described in CodeMirror docs.
                            Used to autoload an appropriate language plugin js file according to filename conventions.
                            (DEFAULT = settings.CODEMIRROR_MODE)
            theme         - Name of theme. Also autoloads theme plugin css according to filename conventions.
                            (DEFAULT = settings.CODEMIRROR_THEME)
            config        - The rest of the options passed into CodeMirror as a python map.
                            (updated from settings.CODEMIRROR_CONFIG)
            dependencies  - Some modes depend on others, you can pass extra modes dependencies with this argument.
                            For example for mode="htmlmixed", you must pass dependencies=("xml", "javascript", "css").
            js_var_format - A format string interpolated with the form field name to name a global JS variable that will
                            hold the CodeMirror editor object. For example with js_var_format="%s_editor" and a field
                            named "code", the JS variable name would be "code_editor". If None is passed, no global
                            variable is created (DEFAULT = settings.CODEMIRROR_JS_VAR_FORMAT)

        Example:
            *-------------------------------*
            + static
              + codemirror
                + lib
                  - codemirror.js
                  - codemirror.css
                + mode
                  + python
                    - python.js
                + theme
                  + cobalt.css
            *-------------------------------*
            CODEMIRROR_PATH = "codemirror"

            codemirror = CodeMirrorTextarea(mode="python", theme="cobalt", config={ 'fixedGutter': True })
            document = forms.TextField(widget=codemirror)
        """
        super(CodeMirrorTextarea, self).__init__(attrs=attrs, **kwargs)
        
        mode = mode or CODEMIRROR_MODE
        if isstring(mode):
            mode = { 'name': mode }
        self.mode_name = mode['name']
        self.dependencies = dependencies
        self.js_var_format = js_var_format or CODEMIRROR_JS_VAR_FORMAT
        
        theme = theme or CODEMIRROR_THEME
        theme_css_filename = THEME_CSS_FILENAME_RE.search(theme).group(0)
        if theme_css_filename == 'default':
            self.theme_css = []
        else:
            self.theme_css = [theme_css_filename]
        
        config = config or {}
        self.option_json = json.dumps(dict(chain(
            CODEMIRROR_CONFIG.items(),
            config.items(),
            [('mode', mode), ('theme', theme)])))
    
    def render(self, name, value, attrs=None):
        u"""Render CodeMirrorTextarea"""
        if self.js_var_format is not None:
            js_var_bit = 'var %s = ' % (self.js_var_format % name)
        else:
            js_var_bit = ''
        output = [super(CodeMirrorTextarea, self).render(name, value, attrs),
            '<script type="text/javascript">%sCodeMirror.fromTextArea(document.getElementById(%s), %s);</script>' %
                (js_var_bit, '"id_%s"' % name, self.option_json)]
        return mark_safe('\n'.join(output))

