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

USE_ST_SYNTAX = int(sublime.version()) >= 3092
ST_LANGUAGES = ('.sublime-syntax', '.tmLanguage') if USE_ST_SYNTAX else ('.tmLanguage',)
EDIT_LINE = re.compile(
    r'''(?mxs)
    ^\s*([a-zA-Z\d_]+)\s*=\s*
    (
        (None) |
        (True|False) |
        (\[(?:\s*(?:'(?:\\.|[^'])*'|"(?:\\.|[^"])*")\s*,?\s*)*\]) |
        (r?
            "{3}(?:\\.|"{1,2}(?!")|[^"])*?"{3} |
            '{3}(?:\\.|'{1,2}(?!')|[^'])*?'{3} |
            '(?:\\.|[^'])*' |
            "(?:\\.|[^"])*" |
        )
    )
    \s*$
    '''
)


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

    string_keys = ('find', 'replace', 'scope', 'plugin')

    bool_keys = ('greedy', 'greedy_scope', 'multi_pass')

    valid_search_types = ('regex', 'literal', 'literal_no_case')

    allowed_keys = (
        'search_type',
        'find',
        'replace',
        'greedy',
        'greedy_scope',
        'multi_pass',
        'scope',
        'scope_filter',
        'plugin',
        'name'
    )

    def run(self, edit):
        """Parse the regex panel, and if okay, insert/replace entry in settings."""

        text = self.view.substr(sublime.Region(0, self.view.size()))

        self.view.size()
        pt = 0
        end = self.view.size() - 1
        obj = {}
        name = None
        while pt < end:
            m = EDIT_LINE.search(text, pt)
            if m:
                if m.group(1) in self.allowed_keys and m.group(3) is None:
                    if m.group(1) == 'name' and m.group(6):
                        name = eval(m.group(6))
                    elif (
                        (m.group(1) in self.string_keys and m.group(6)) or
                        (m.group(1) in self.bool_keys and m.group(4)) or
                        (m.group(1) == 'scope_filter' and m.group(5))
                    ):
                        obj[m.group(1)] = eval(m.group(2))
                    elif m.group(1) == 'search_type' and m.group(6):
                        search_type = eval(m.group(2))
                        if search_type in self.valid_search_types:
                            obj[m.group(1)] = search_type
                pt = m.end(0)
            else:
                break

        if name is None:
            error('A valid name must be provided!')
        elif obj.get('search_type') is None:
            error('A valid search type must be provided!')
        elif obj.get('scope') is None and obj.get('find') is None:
            error('A valid find pattern must be provided!')
        else:
            try:
                if obj.get('find') is not None:
                    if obj['search_type'] in ('literal', 'literal_no_case'):
                        flags = 0
                        find = re.escape(obj['find'])
                        if obj['search_type'] == 'literal_no_case':
                            flags = re.I
                        re.compile(find, flags)
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
                expressions[name] = obj
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
                "search_type": None,
                "find": None,
                "replace": None,
                "greedy": None,
                "greedy_scope": None,
                "multi_pass": None,
                "scope": None,
                "scope_filter": None,
                "plugin": None
            }
            if 'literal' in v:
                if 'case' in v and v['case'] is False:
                    obj['search_type'] = 'literal_no_case'
                else:
                    obj['search_type'] = 'literal'
                obj['find'] = v.get('find')
            else:
                obj['search_type'] = 'regex'
                prefix = ''
                if 'case' in v and v['case'] is False:
                    prefix == 'i'
                if 'dotall' in v and v['dotall']:
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
            text = '# name: rule name\n'
            text += self.format_string('name', name)
            text += '\n# search_type: search type\n'
            text += self.format_string('search_type', rule.get('search_type'))
            text += '\n# find: regular expression pattern or literal string\n'
            text += self.format_regex_string('find', rule.get('find'))
            text += '\n# replace: replace pattern\n'
            text += self.format_regex_string('replace', rule.get('replace'))
            text += '\n# scope: scope to search for (scope_regex)\n'
            text += self.format_string('scope', rule.get('scope'))
            text += '\n# scope_filter: an array of scope qualifiers for the match (regex)\n'
            text += self.format_array('scope_filter', rule.get('scope_filter'))
            text += '\n# greedy: apply action to all instances or first\n'
            text += self.format_bool('greedy', rule.get('greedy'))
            text += '\n# greedy_scope: apply search to all instances of scope (scope_regex)\n'
            text += self.format_bool('greedy_scope', rule.get('greedy_scope'))
            text += '\n# multi_pass: perform multiple sweeps on the scope region to find and\n'
            text += '#             replace all instances of the regex (scope_regex)\n'
            text += self.format_bool('multi_pass', rule.get('multi_pass'))
            text += '\n# plugin: define replace plugin for more advanced replace logic\n'
            text += self.format_string('plugin', rule.get('plugin'))
            text += '\n# args: arguments for \'plugin\'\n'
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
