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
import ast
import textwrap

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

        okay = False
        if key == 'reg_replace_panel_save' and view.settings().get('reg_replace.edit_view', False):
            okay = True
        elif key == 'reg_replace_panel_test' and view.settings().get('reg_replace.edit_view', False):
            okay = True
        return okay


class RegReplacePanelInsertCommand(sublime_plugin.TextCommand):
    """Command to insert text into panel."""

    def run(self, edit, text):
        """Insert text into panel."""

        self.view.replace(edit, sublime.Region(0, self.view.size()), text)


class ConvertPythonSrc2Obj(object):
    """Convert the python source to a RegReplace object."""

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
            count = 0
            for v in value.values:
                if not self.eval_value(v):
                    okay = False
                    break
                count += 1
        return okay

    def eval_list(self, value):
        """Evaluate the list to see if it is safe to execute."""

        okay = True
        count = 0
        for v in value.elts:
            if not self.eval_value(v):
                okay = False
                break
            count += 1
        return okay

    def convert(self, text):
        """
        Convert the source to an object.

        Test object will be compiled separately.
        """

        obj = {}
        test = {}
        try:
            # Examine the python code to ensure it it is safe to evaluate.
            # We will evalute each statement and see if it is safe.
            # None and numbers are ignored unless it is in the arg dictionary.
            # All the top level variables are either string, bool, list of strings, or dict.
            code = ast.parse(text)
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
                        elif name == 'test' and class_name == 'Dict':
                            if self.eval_dict(snippet.value):
                                test = compile_expr(snippet.value)
        except Exception as e:
            error('Could not read rule settings!\n\n%s' % str(e))
            return None, None
        return obj, test


class RegReplaceShowEditPanel(sublime_plugin.WindowCommand):
    """Show the existing regex panel."""

    def run(self):
        """Execute the command to show the panel."""

        self.window.run_command("show_panel", {"panel": "output.reg_replace"})


class RegReplacePanelTestCommand(sublime_plugin.TextCommand):
    """Handle the panel find shortcut."""

    test_keys = (
        'find_only',
        'multi_pass',
        'no_selection',
        'regex_full_file_with_selections',
        'replacements',
        'action',
        'options'
    )
    test_subkeys = ('key', 'scope', 'style')
    test_bool_keys = ('find_only', 'multi_pass', 'no_selection', 'regex_full_file_with_selections')

    def process_test_cmd(self, test):
        """Process the test command."""

        remove = []
        okay = True
        for k, v in test.items():
            if k not in self.test_keys:
                remove.append(k)
            elif (
                k == 'replacements' and
                not isinstance(v, list) or
                not all(isinstance(x, str) for x in test['replacements'])
            ):
                error('You need to specify valid replacements in your sequence for testing!')
                okay = False
                break
            elif k in self.test_bool_keys:
                if v is None:
                    remove.append(k)
                elif not isinstance(v, bool):
                    error('"%s" must be a boolean value!')
                    okay = False
                    break
            elif k == 'action':
                if v is None:
                    remove.append(k)
                elif not isinstance(v, str):
                    error('"action" must be a string!')
                    okay = False
                    break
            elif k == 'options':
                if v is None:
                    remove.append(k)
                elif not isinstance(v, dict):
                    error('"options" must be a dict!')
                    okay = False
                    break
                else:
                    for k1, v1 in v.items():
                        if k1 not in self.test_subkeys:
                            remove.append((k, k1))
                        elif not isinstance(v1, str):
                            error('"%s" must be a string!' % k1)
                            okay = False
                            break

        if okay:
            # Remove any items set to None or invalid keys
            for r in remove:
                if isinstance(r, tuple):
                    del test[r[0]][r[1]]
                else:
                    del test[r]
        return okay

    def run(self, edit):
        """Parse the regex panel, and if okay, run the test entry in the active view."""

        obj, test = ConvertPythonSrc2Obj().convert(self.view.substr(sublime.Region(0, self.view.size())))

        # Something went wrong.
        if test is None or obj is None:
            return

        # Ensure test command is valid.
        if not self.process_test_cmd(test):
            return

        # Copy all regex rules that are to be included in the test sequence
        test_rules = {}
        rules = sublime.load_settings('reg_replace_rules.sublime-settings').get('replacements', {})
        for x in test['replacements']:
            if x in rules:
                test_rules[x] = rules[x]

        # Ensure the bare minimum items are in the current test rule
        # and ensure the regex (if any) compiles.
        # If all is well, execute the command.
        if not obj.get('name'):
            error('A valid name must be provided!')
        elif obj.get('scope') is None and obj.get('find') is None:
            error('A valid find pattern or scope must be provided!')
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
                test_rules[obj['name']] = obj
                settings = sublime.load_settings('reg_replace_test.sublime-settings')
                settings.set('format', '3.0')
                settings.set('replacements', test_rules)
                window = sublime.active_window()
                if window is not None:
                    view = window.active_view()
                    if view is not None:
                        test["use_test_buffer"] = True
                        view.run_command('reg_replace', test)
            except Exception as e:
                error('Regex compile failed!\n\n%s' % str(e))


class RegReplacePanelSaveCommand(sublime_plugin.TextCommand):
    """Handle the panel save shortcut."""

    def is_existing_name(self, name):
        """Confirm if name already exists and if user is okay with overwritting an existing name."""

        original_name = self.view.settings().get('regreplace.name', None)
        rules = sublime.load_settings('reg_replace_rules.sublime-settings').get('replacements', {})
        msg = "The name '%s' already exists in the replacment list.  Do you want to replace existing rule?" % name
        return not (name == original_name or name not in rules or sublime.ok_cancel_dialog(msg))

    def run(self, edit):
        """Parse the regex panel, and if okay, insert/replace entry in settings."""

        obj = ConvertPythonSrc2Obj().convert(self.view.substr(sublime.Region(0, self.view.size())))[0]

        if obj is None:
            return
        if not obj.get('name'):
            error('A valid name must be provided!')
        elif obj.get('scope') is None and obj.get('find') is None:
            error('A valid find pattern or scope must be provided!')
        elif not self.is_existing_name(obj['name']):
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
                settings = sublime.load_settings('reg_replace_rules.sublime-settings')
                rules = settings.get('replacements', {})
                rules[obj['name']] = obj
                settings.set('replacements', rules)
                sublime.save_settings('reg_replace_rules.sublime-settings')
                self.view.settings().set('regreplace.name', obj['name'])
            except Exception as e:
                error('Regex compile failed!\n\n%s' % str(e))


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

    def edit_rule(self, value, new=False):
        """Parse rule and format as Python code and insert into panel."""

        if value >= 0 or new:
            if new:
                name = None
                rule = {}
            else:
                name = self.keys[value]
                rule = self.rules[value]
            text = '"""\nIf you don\'t need a setting, just leave it as None.\n'
            text += 'When the rule is parsed, the default will be used.\n'
            text += 'Each variable is evaluated separately, so you cannot substitute variables '
            text += 'in other variables.\n"""\n'
            text += '\n# name (str): Rule name.  Required.\n'
            text += self.format_string('name', name)
            text += '\n# find (str): Regular expression pattern or literal string.\n'
            text += '#    Use (?i) for case insensitive. Use (?s) for dotall.\n'
            text += '#    See https://docs.python.org/3.4/library/re.html for more info on regex flags.\n'
            text += '#    Required unless "scope" is defined.\n'
            text += self.format_regex_string('find', rule.get('find'))
            text += '\n# replace (str - default=r\'\\0\'): Replace pattern.\n'
            text += self.format_regex_string('replace', rule.get('replace'))
            text += '\n# literal (bool - default=False): Preform a non-regex, literal search and replace.\n'
            text += self.format_bool('literal', rule.get('literal'))
            text += '\n# literal_ignorecase (bool - default=False): Ignore case when "literal" is true.\n'
            text += self.format_bool('literal_ignorecase', rule.get('literal_ignorecase'))
            text += '\n# scope (str): Scope to search for and to apply optional regex to.\n'
            text += '#    Required unless "find" is defined.\n'
            text += self.format_string('scope', rule.get('scope'))
            text += '\n# scope_filter ([str] - default=[]): An array of scope qualifiers for the match.\n'
            text += '#    Only used when "scope" is not defined.\n'
            text += '#\n'
            text += '#    - Any instance of scope qualifies match: scope.name\n'
            text += '#    - Entire match of scope qualifies match: !scope.name\n'
            text += '#    - Any instance of scope disqualifies match: -scope.name\n'
            text += '#    - Entire match of scope disqualifies match: -!scope.name\n'
            text += self.format_array('scope_filter', rule.get('scope_filter'))
            text += '\n# greedy (bool - default=True): Apply action to all instances (find all).\n'
            text += '#    Used when "find" is defined.\n'
            text += self.format_bool('greedy', rule.get('greedy'))
            text += '\n# greedy_scope (bool - default=True): Find all the scopes specified by "scope."\n'
            text += self.format_bool('greedy_scope', rule.get('greedy_scope'))
            text += '\n# multi_pass (bool - default=False): Perform multiple sweeps on the scope region to find\n'
            text += '#    and replace all instances of the regex when regex cannot be formatted to find\n'
            text += '#    all instances. Since a replace can change a scope, this can be useful.\n'
            text += self.format_bool('multi_pass', rule.get('multi_pass'))
            text += '\n# plugin (str): Define replace plugin for more advanced replace logic.\n'
            text += self.format_string('plugin', rule.get('plugin'))
            text += '\n# args (dict): Arguments for \'plugin\'.\n'
            text += self.format_dict('args', rule.get('args'))
            text += '\n# ----------------------------------------------------------------------------------------\n'
            text += '# test: Here you can setup a test command.  This is not saved and is just used for this session.\n'
            text += '#     - replacements ([str]): A list of regex rules to sequence together.\n'
            text += '#     - find_only (bool): Highlight current find results and prompt for action.\n'
            text += '#     - action (str): Apply the given action (fold|unfold|mark|unmark|select).\n'
            text += '#       This overrides the default replace action.\n'
            text += '#     - options (dict): optional parameters for actions (see documentation for more info).\n'
            text += '#         - key (str): Unique name for highlighted region.\n'
            text += '#         - scope (str - default="invalid"): Scope name to use as the color.\n'
            text += '#         - style (str - default="outline"): Highlight style (solid|underline|outline).\n'
            text += '#     - multi_pass (bool): Repeatedly sweep with sequence to find all instances.\n'
            text += '#     - no_selection (bool): Overrides the "selection_only" setting and forces no selections.\n'
            text += '#     - regex_full_file_with_selections (bool): Apply regex search to full file then apply\n'
            text += '#       action to results under selections.\n'
            text += textwrap.dedent(
                """\
                test = {
                    "replacements": [%s],
                    "find_only": True,
                    "action": None,
                    "options": {},
                    "multi_pass": False,
                    "no_selection": False,
                    "regex_full_file_with_selections": False
                }
                """ % (self.simple_format_string(name) if name is not None else '')
            )

            replace_view = self.window.create_output_panel('reg_replace')
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
            replace_view.settings().set('line_numbers', True)
            replace_view.settings().set('reg_replace.edit_view', True)
            replace_view.settings().set('bracket_highlighter.bracket_string_escape_mode', 'regex')
            replace_view.settings().set('regreplace.name', name)
            replace_view.sel().clear()
            replace_view.sel().add(sublime.Region(0, 0))
            self.window.run_command("show_panel", {"panel": "output.reg_replace"})
            sublime.set_timeout(lambda w=self.window, v=replace_view: w.focus_view(v), 100)

    def run(self, new=False):
        """Read regex from file and place in panel for editing."""

        if new:
            self.edit_rule(-1, new=True)
        else:
            self.keys = []
            self.rules = []
            rules = sublime.load_settings('reg_replace_rules.sublime-settings').get('replacements', {})
            for name, rule in sorted(rules.items()):
                self.keys.append(name)
                self.rules.append(rule)
            if len(self.keys):
                self.window.show_quick_panel(
                    self.keys,
                    self.edit_rule
                )


class RegReplaceDeleteRegexCommand(sublime_plugin.WindowCommand):
    """Delete a regular expression rule."""

    def delete_rule(self, value):
        """Delete the specified rule."""

        if value >= 0:
            if sublime.ok_cancel_dialog('Are you sure you want to delete the rule: \'%s\'?' % self.keys[value]):
                del self.regex_rules[self.keys[value]]
                sublime.load_settings('reg_replace_rules.sublime-settings').set('replacements', self.regex_rules)
                sublime.save_settings('reg_replace_rules.sublime-settings')

    def run(self):
        """Show a quick panel and let the user select which expression to delete."""

        self.keys = []
        self.regex_rules = sublime.load_settings('reg_replace_rules.sublime-settings').get('replacements', {})
        for name in sorted(self.regex_rules.keys()):
            self.keys.append(name)
        if len(self.keys):
            self.window.show_quick_panel(
                self.keys,
                self.delete_rule
            )
