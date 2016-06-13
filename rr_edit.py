"""
Reg Replace.

Licensed under MIT
Copyright (c) 2011 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
import re
import json
from backrefs import bre
from RegReplace.rr_notify import error

USE_ST_SYNTAX = int(sublime.version()) >= 3092
ST_LANGUAGES = ('.sublime-syntax', '.tmLanguage') if USE_ST_SYNTAX else ('.tmLanguage',)

REGEX_LINE = re.compile(
    r'''(?x)
    ("find"\s*:\s*)
    "
    ((?:\\.|[^"])*)
    "
    '''
)

EDIT_LINE = re.compile(
    r'''(?xs)
    ^\s*find\s*=\s*(r?
        "{3}(?:\\.|"{1,2}(?!")|[^"])*?"{3} |
        '{3}(?:\\.|'{1,2}(?!')|[^'])*?'{3} |
        '(?:\\.|[^'])*' |
        "(?:\\.|[^"])*"
    )
    \s*$
    '''
)


def find_regex_region(view):
    """Get the `"find": "regex"` regions and locate the one the cursor is in."""

    match = None
    line_region = None
    sel = view.sel()
    # Make sure there is just one selection
    if len(sel) == 1:
        # We only care if the cursor is not selecting multiple chars
        selection = sel[0]
        if selection.size() == 0:
            # Find all instances of regex entries on the line,
            # but only consider it found if the cursor is within
            # region of an instance.
            region = view.line(selection)
            line = view.substr(region)
            for m in REGEX_LINE.finditer(line):
                start_pt = region.begin() + m.start(0)
                end_pt = region.begin() + m.end(0)
                if start_pt <= selection.begin() < end_pt:
                    match = m
                    line_region = region
                    break
    return match, line_region


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


class RegReplaceSettingsInsertCommand(sublime_plugin.TextCommand):
    """Class to write regex back to settings file."""

    def run(self, edit, text, start, end):
        """Write modified regex back to settings file."""

        self.view.replace(edit, sublime.Region(start, end), text)


class RegReplacePanelSaveCommand(sublime_plugin.TextCommand):
    """Handle the panel save shortcut."""

    def run(self, edit):
        """Search the active view to see if the cursor is in a find regex."""

        text = self.view.substr(sublime.Region(0, self.view.size()))
        m = EDIT_LINE.match(text)
        find = None
        if m:
            obj = {"find": eval(m.group(1))}
            settings = sublime.load_settings('reg_replace.sublime-settings')
            extend = bool(settings.get("extended_back_references", False))
            try:
                if extend:
                    bre.compile_search(obj['find'])
                else:
                    re.compile(obj['find'])
                find = json.dumps(obj)[9:-1]
                self.save_to_settings(find)
            except Exception as e:
                error('Regex compile failed!\n\n%s' % str(e))

    def save_to_settings(self, find):
        """Save modified regex to the settings file."""

        view = None
        window = sublime.active_window()
        if window is not None:
            view = window.active_view()
        m, line_region = find_regex_region(view)
        if m:
            start = line_region.begin() + m.start(2) - 1
            end = line_region.begin() + m.end(2) + 1
            view.run_command(
                'reg_replace_settings_insert',
                {
                    'text': find,
                    'start': start,
                    'end': end
                }
            )


class RegReplaceEditRegexCommand(sublime_plugin.TextCommand):
    """Class to edit regex in settings file."""

    def needs_escape(self, string, target_char, fix=False):
        """Check if regex string needs escaping."""

        skip = False
        count = 0
        needs_escape = False
        for c in string:
            if skip:
                continue
            if c == '\\':
                skip = True
            elif c == target_char:
                count += 1
                if count == 3:
                    needs_escape = True
                    break
            else:
                count = 0
        return needs_escape

    def fix_escape(self, string, target_char):
        """Escape regex to fit in triple quoted string."""

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
                if count == 3:
                    fixed.append('\\')
                    fixed.append(c)
                    count = 0
                else:
                    fixed.append(c)
            else:
                count = 0
                fixed.append(c)
        return ''.join(fixed)

    def run(self, edit):
        """Read regex from file and place in panel for editing."""

        m = find_regex_region(self.view)[0]
        if m:
            regex = json.loads('{"find": "%s"}' % m.group(2))
            single = self.needs_escape(regex['find'], '\'')
            double = self.needs_escape(regex['find'], '"')
            if not double:
                edit_regex = r'find = r"""%s"""' % regex['find']
            elif not single:
                edit_regex = r'find = r\'\'\'%s\'\'\'' % regex['find']
            else:
                edit_regex = r'find = r"""%s"""' % self.fix_escape(regex['find'], '"')
            window = self.view.window()
            if window is not None:
                replace_view = window.create_output_panel('reg_replace', unlisted=True)
                replace_view.run_command('reg_replace_panel_insert', {'text': edit_regex})
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
                replace_view.settings().set('reg_replace_edit_view', True)
                replace_view.settings().set('bracket_highlighter.widget_okay', True)
                replace_view.settings().set('bracket_highlighter.bracket_string_escape_mode', 'regex')
                window.run_command("show_panel", {"panel": "output.reg_replace"})
