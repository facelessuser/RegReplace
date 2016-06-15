"""
Reg Replace.

Licensed under MIT
Copyright (c) 2011 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
import re
from backrefs import bre
from RegReplace.rr_notify import error
import copy
import ast

USE_ST_SYNTAX = int(sublime.version()) >= 3092
ST_LANGUAGES = ('.sublime-syntax', '.tmLanguage') if USE_ST_SYNTAX else ('.tmLanguage',)


def ast_class(cl):
    """Get the ast_class name."""

    return cl.__class__.__name__


def compile_expr(exp):
    """Compile the expression."""

    return eval(compile(ast.Expression(exp), '(none)', 'eval'))


class RegReplaceEventListener(sublime_plugin.EventListener):
    """Listen for save event in regreplace edit panel."""

    def on_query_context(self, view, key, operator, operand, match_all):
        """Check if save shortcut occured in output panel for regreplace."""

        return key == 'reg_replace_panel_save' and view.settings().get('reg_replace_edit_view', False)


class RegReplacePanelInsertCommand(sublime_plugin.TextCommand):
    """Command to insert text into panel."""

    def run(self, edit, text):
        """Insert text into panel."""

        self.view.replace(edit, sublime.Region(0, self.view.size()), text)


class RegReplacePanelSaveCommand(sublime_plugin.TextCommand):
    """Handle the panel save shortcut."""

    string_keys = ('find', 'replace', 'scope', 'plugin', 'name')

    bool_keys = ('greedy', 'greedy_scope', 'multi_pass', 'literal', 'literal_ignorecase]')

    allowed_keys = (
        'literal',
        'literal_ignorecase',
        'find',
        'replace',
        'greedy',
        'greedy_scope',
        'multi_pass',
        'scope',
        'scope_filter',
        'plugin',
        'args',
        'name'
    )

    def eval_value(self, v):
        """Evaluate the value io see if it is safe to execute."""
        okay = False
        if ast_class(v) == 'Dict':
            # dict
            if self.eval_dict(v):
                okay = True
        elif ast_class(v) == 'List':
            # list
            if self.eval_list(v):
                okay = True
        elif ast_class(v) == 'Str':
            # string
            okay = True
        elif ast_class(v) == 'Name' and v.id in ('True', 'False', 'None'):
            # boleans or None
            okay = True
        elif ast_class(v) == 'Num':
            # numbers
            okay = True
        elif ast_class(v) == 'UnaryOp' and ast_class(v.op) == 'USub' and ast_class(v.operand) == 'Num':
            # negative numbers
            okay = True
        return okay

    def eval_dict(self, value):
        """Evaluate the dictionary to see if it is safe to execute."""

        okay = True
        if all(ast_class(k) == 'Str' for k in value.keys):
            for v in value.values:
                if not self.eval_value(v):
                    okay = False
                    break
        return okay

    def eval_list(self, value):
        """Evaluate the list to see if it is safe to execute."""

        okay = True
        for v in value.elts:
            if not self.eval_value(v):
                okay = False
                break
        return okay

    def run(self, edit):
        """Parse the regex panel, and if okay, insert/replace entry in settings."""

        try:
            # Examine the python code to ensure it it is safe to evaluate.
            # We will evalute each statement and see if it is safe.
            # None and numbers are ignored unless it is in the arg dictionary.
            # All the top level variables are either string, bool, list of strings, or dict.
            code = ast.parse(self.view.substr(sublime.Region(0, self.view.size())))
            obj = {}
            for snippet in code.body:
                if ast_class(snippet) == 'Assign' and len(snippet.targets) == 1:
                    target = snippet.targets[0]
                    if ast_class(target) == 'Name':
                        name = target.id
                        class_name = ast_class(snippet.value)
                        if name in self.string_keys and class_name == 'Str':
                            obj[name] = compile_expr(snippet.value)
                        elif name in self.bool_keys and class_name == 'Name' and snippet.value.id in ('True', 'False'):
                            obj[name] = compile_expr(snippet.value)
                        elif name == 'scope_filter' and class_name == 'List':
                            if all(ast_class(l) == 'Str' for l in snippet.value.elts):
                                obj[name] = compile_expr(snippet.value)
                        elif name == 'args' and class_name == 'Dict':
                            if self.eval_dict(snippet.value):
                                obj[name] = compile_expr(snippet.value)
        except Exception as e:
            error('Could not read rule settings!\n\n%s' % str(e))
            return

        if obj.get('name') is None:
            error('A valid name must be provided!')
        elif obj.get('scope') is None and obj.get('find') is None:
            error('A valid find pattern must be provided!')
        else:
            try:
                if obj.get('find') is not None:
                    if obj.get('literal', False):
                        flags = 0
                        pattern = re.escape(obj['find'])
                        if obj.get('literal_ignorecase', False):
                            flags = re.I
                        re.compile(pattern, flags)
                    else:
                        extend = sublime.load_settings(
                            'reg_replace.sublime-settings'
                        ).get('extended_back_references', False)
                        if extend:
                            bre.compile_search(obj['find'])
                        else:
                            re.compile(obj['find'])
                settings = sublime.load_settings('reg_replace_expressions.sublime-settings')
                expressions = settings.get('replacements', {})
                expressions[obj['name']] = obj
                settings.set('replacements', expressions)
                sublime.save_settings('reg_replace_expressions.sublime-settings')
            except Exception as e:
                error('Regex compile failed!\n\n%s' % str(e))


class RegReplaceConvertRulesCommand(sublime_plugin.ApplicationCommand):
    """Convert rules to new version."""

    def run(self):
        """Convert old style rules to new style rules."""

        old = sublime.load_settings('reg_replace.sublime-settings').get('replacements', {})
        settings = sublime.load_settings('reg_replace_expressions.sublime-settings')
        new = settings.get('replacements', {})
        for k, v in old.items():
            obj = {
                "find": None,
                "literal": None,
                "literal_ignorecase": None,
                "replace": None,
                "greedy": None,
                "greedy_scope": None,
                "multi_pass": None,
                "scope": None,
                "scope_filter": None,
                "plugin": None
            }
            if v.get('literal', False):
                obj['literal'] = True
                if v.get('case', True) is False:
                    obj['literal_ignorecase'] = True
                obj['find'] = v.get('find')
            else:
                prefix = ''
                if v.get('case', True) is False:
                    prefix == 'i'
                if v.get('dotall', False):
                    prefix == 's'
                if prefix:
                    prefix = "(?%s)" % prefix
                if 'find' in obj:
                    obj['find'] = prefix + v['find'].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

            obj['replace'] = v.get('replace', None)
            if 'greedy' in v:
                obj['greedy'] = v['greedy']
            elif 'greedy_replace' in v:
                obj['greedy'] = v['greedy_replace']
            obj['greedy_scope'] = v.get('greedy_scope', None)
            obj['multi_pass'] = v.get('multi_pass_regex', None)
            obj['scope'] = v.get('scope', None)
            obj['scope_filter'] = v.get('scope_filter', None)
            obj['plugin'] = v.get('plugin', None)
            obj['args'] = v.get('args', None)

            remove = []
            for k1, v1 in obj.items():
                if v1 is None:
                    remove.append(k1)
            for k1 in remove:
                del obj[k1]

            new[k] = obj
        settings.set('replacements', new)
        sublime.save_settings('reg_replace_expressions.sublime-settings')


class RegReplaceEditRegexCommand(sublime_plugin.WindowCommand):
    """Class to edit regex in settings file."""

    def needs_escape(self, string, target_char, quote_count=1):
        """Check if regex string needs escaping."""

        skip = False
        count = 0
        needs_escape = False
        for c in string:
            if skip:
                skip = False
                continue
            if c == '\\':
                skip = True
            elif c == target_char:
                count += 1
                if count == quote_count:
                    needs_escape = True
                    break
            else:
                count = 0
        return needs_escape

    def fix_escape(self, string, target_char, quote_count=1):
        """Escape regex to fit in quoted string."""

        skip = False
        count = 0
        fixed = []
        for c in string():
            if skip:
                fixed.append(c)
                continue
            if c == '\\':
                skip = True
                fixed.append(c)
            elif c == target_char:
                count += 1
                if count == quote_count:
                    fixed.append('\\')
                    fixed.append(c)
                    count = 0
                else:
                    fixed.append(c)
            else:
                count = 0
                fixed.append(c)
        return ''.join(fixed)

    def format_string(self, name, value):
        """Format string."""

        if value is not None and isinstance(value, str):
            string = '%s = %s\n' % (name, self.simple_format_string(value))
        else:
            string = '%s = None\n' % name
        return string

    def format_regex_string(self, name, value):
        """Format triple quoted strings."""

        if value is not None and isinstance(value, str):
            string = '%s = %s\n' % (name, self.simple_format_string(value, force_raw=True))
        else:
            string = '%s = None\n' % name
        return string

    def simple_format_string(self, value, force_raw=False):
        """Format string without key."""

        m = re.search(r'((\n)|\r|\n|\t|\\)', value)
        newlines = False
        raw = ''
        if m:
            if m.group(2):
                newlines = True
            raw = 'r'
        if force_raw and not raw:
            raw = 'r'

        single = self.needs_escape(value, '\'')
        double = self.needs_escape(value, '"')
        tsingle = self.needs_escape(value, '\'', quote_count=3)
        tdouble = self.needs_escape(value, '"', quote_count=3)
        if not double and not newlines:
            string = '%s"%s"' % (raw, value)
        elif not single and not newlines:
            string = '%s\'%s\'' % (raw, value)
        elif not tdouble:
            string = '%s"""%s"""' % (raw, value)
        elif not tsingle:
            string = '%s\'\'\'%s\'\'\'' % (raw, value)
        elif not newlines:
            string = '%s"%s"' % (raw, self.fix_escape(value, '"'))
        else:
            string = '%s"""%s"""' % (raw, self.fix_escape(value, '"', quote_count=3))
        return string

    def format_array(self, name, value):
        """Format an array strings."""

        if value is not None and isinstance(value, list):
            array = '%s = [\n%s]\n' % (name, self.parse_array(value, 1))
        else:
            array = '%s = None\n' % name
        return array

    def format_bool(self, name, value):
        """Format a boolean."""

        if value is not None and isinstance(value, bool):
            boolean = '%s = %s\n' % (name, str(value))
        else:
            boolean = '%s = None\n' % name
        return boolean

    def parse_array(self, value, indent):
        """Parse array."""

        array = ''
        for v in value:
            if v is None:
                array += '%(indent)sNone,\n' % {
                    'indent': '    ' * indent
                }
            elif isinstance(v, str):
                array += '%(indent)s%(content)s,\n' % {
                    'indent': '    ' * indent,
                    'content': self.simple_format_string(v)
                }
            elif isinstance(v, (int, float)):
                array += '%(indent)s%(content)s,\n' % {
                    'indent': '    ' * indent,
                    'content': v.__repr__()
                }
            elif isinstance(v, list):
                array += '%(indent)s[\n%(content)s%(indent)s],\n' % {
                    'indent': '    ' * indent,
                    'content': self.parse_array(v, indent + 1)
                }
            elif isinstance(v, dict):
                array += '%(indent)s{\n%(content)s%(indent)s},\n' % {
                    'indent': '    ' * indent,
                    'content': self.parse_dict(v, indent + 1)
                }
        return array

    def parse_dict(self, value, indent):
        """Parse dictionary."""

        dictionary = ''
        for k, v in value.items():
            if v is None:
                dictionary += '%(indent)s%(name)s: None,\n' % {
                    'name': self.simple_format_string(k),
                    'indent': '    ' * indent
                }
            elif isinstance(v, str):
                dictionary += '%(indent)s%(name)s: %(content)s,\n' % {
                    'name': self.simple_format_string(k),
                    'indent': '    ' * indent,
                    'content': self.simple_format_string(v)
                }
            elif isinstance(v, (int, float)):
                dictionary += '%(indent)s%(name)s: %(content)s,\n' % {
                    'name': self.simple_format_string(k),
                    'indent': '    ' * indent,
                    'content': v.__repr__()
                }
            elif isinstance(v, list):
                dictionary += '%(indent)s%(name)s: [\n%(content)s%(indent)s],\n' % {
                    'name': self.simple_format_string(k),
                    'indent': '    ' * indent,
                    'content': self.parse_array(v, indent + 1)
                }
            elif isinstance(v, dict):
                dictionary += '%(indent)s%(name)s: {\n%(content)s%(indent)s},\n' % {
                    'name': self.simple_format_string(k),
                    'indent': '    ' * indent,
                    'content': self.parse_dict(v, indent + 1)
                }
        return dictionary

    def format_dict(self, name, value):
        """Format dictionary."""

        if value is not None and isinstance(value, dict):
            if len(value):
                dictionary = '%(name)s = {\n%(content)s}\n' % {
                    'name': name,
                    'content': self.parse_dict(value, 1)
                }
            else:
                dictionary = '%s%s = {}\n' % name
        else:
            dictionary = '%s = None\n' % name
        return dictionary

    def edit_rule(self, value):
        """Parse rule and format as Python code and insert into panel."""

        if value >= 0:
            name = self.keys[value]
            rule = self.rules[value]
            text = '# If you don\'t need a setting, just leave it as None.\n'
            text += '# When the rule is parsed, the default will be used.\n'
            text += '\n# name (str): Rule name.  Required.\n'
            text += self.format_string('name', name)
            text += '\n# find (str): Regular expression pattern or literal string.\n'
            text += '#             Required unless "scope" is defined.\n'
            text += self.format_regex_string('find', rule.get('find'))
            text += '\n# replace (str = default=r\'\\0\'): Replace pattern.\n'
            text += self.format_regex_string('replace', rule.get('replace'))
            text += '\n# literal (bool - default=False): Preform a non-regex, literal search and replace.\n'
            text += self.format_bool('literal', rule.get('literal'))
            text += '\n# literal_ignorecase (bool - default=False): Ignore case when "literal" is true.\n'
            text += self.format_bool('literal_ignorecase', rule.get('literal_ignorecase'))
            text += '\n# scope (str): Scope to search for and to apply optional regex to.\n'
            text += '#              Required unless "find" is defined.\n'
            text += self.format_string('scope', rule.get('scope'))
            text += '\n# scope_filter ([str] = default=[]): An array of scope qualifiers for the match.\n'
            text += '#                                    Only used when "scope" is not defined.\n'
            text += self.format_array('scope_filter', rule.get('scope_filter'))
            text += '\n# greedy (bool - default=True): Apply action to all instances (find all).\n'
            text += '#                               Used when "find" is defined.\n'
            text += self.format_bool('greedy', rule.get('greedy'))
            text += '\n# greedy_scope (bool - default=True): Find all the scopes specified by "scope."\n'
            text += self.format_bool('greedy_scope', rule.get('greedy_scope'))
            text += '\n# multi_pass (bool - default=False): Perform multiple sweeps on the scope region to find\n'
            text += '#             and replace all instances of the regex when regex cannot be formatted to find\n'
            text += '#             all instances.\n'
            text += self.format_bool('multi_pass', rule.get('multi_pass'))
            text += '\n# plugin (str): Define replace plugin for more advanced replace logic.\n'
            text += self.format_string('plugin', rule.get('plugin'))
            text += '\n# args (dict): Arguments for \'plugin\'.\n'
            text += self.format_dict('args', rule.get('args'))

            replace_view = self.window.create_output_panel('reg_replace', unlisted=True)
            replace_view.run_command('reg_replace_panel_insert', {'text': text})
            for ext in ST_LANGUAGES:
                highlighter = sublime.load_settings(
                    'reg_replace.sublime-settings'
                ).get('python_highlighter', 'Python/Python')
                highlighter = 'Packages/' + highlighter + ext
                try:
                    sublime.load_resource(highlighter)
                    replace_view.set_syntax_file(highlighter)
                    break
                except Exception:
                    pass
            replace_view.settings().set('gutter', True)
            replace_view.settings().set('line_numbers', False)
            replace_view.settings().set('reg_replace_edit_view', True)
            replace_view.settings().set('bracket_highlighter.widget_okay', True)
            replace_view.settings().set('bracket_highlighter.bracket_string_escape_mode', 'regex')
            self.window.run_command("show_panel", {"panel": "output.reg_replace"})
            sublime.set_timeout(lambda w=self.window, v=replace_view: w.focus_view(v), 100)

    def run(self):
        """Read regex from file and place in panel for editing."""

        self.keys = []
        self.rules = []
        expressions = sublime.load_settings('reg_replace_expressions.sublime-settings').get('replacements', {})
        for name, rule in expressions.items():
            self.keys.append(name)
            self.rules.append(rule)
        if len(self.keys):
            self.window.show_quick_panel(
                self.keys,
                self.edit_rule
            )
