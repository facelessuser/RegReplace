"""
Reg Replace.

Licensed under MIT
Copyright (c) 2011 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
import re
from fnmatch import fnmatch
from RegReplace.rr_replacer import FindReplace
from RegReplace.rr_notify import error, deprecated, DEPRECATED_DOTALL


DEFAULT_SHOW_PANEL = False
DEFAULT_HIGHLIGHT_COLOR = 'invalid'
DEFAULT_HIGHLIGHT_STYLE = 'outline'
DEFAULT_MULTI_PASS_MAX_SWEEP = 100
MODULE_NAME = 'RegReplace'

rrsettings = {}
rrsettingsrules = {}


def underline(regions):
    """Convert to empty regions."""

    new_regions = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            new_regions.append(sublime.Region(start))
            start += 1
    return new_regions


class RegReplaceGlobal(object):
    """Global object to aid in replacing text in a view."""

    bfr = None
    region = None

    @classmethod
    def clear(cls):
        """Clear buffer and region."""

        cls.bfr = None
        cls.region = None


class RegReplaceApplyCommand(sublime_plugin.TextCommand):
    """Command to replace text in a view."""

    def run(self, edit):
        """Workaround replace text with info from `RegReplaceGlobal`."""

        self.view.replace(edit, RegReplaceGlobal.region, RegReplaceGlobal.bfr)


class RegReplaceListenerCommand(sublime_plugin.EventListener):
    """Event listener command."""

    def find_replacements(self, view):
        """Retrieve on save replacement rules."""

        match = False
        file_name = view.file_name()
        if file_name is not None and rrsettings.get('on_save', False):
            replacements = rrsettings.get('on_save_sequences', [])
            scope = rrsettings.get('on_save_highlight_scope', None)
            style = rrsettings.get('on_save_highlight_style', None)
            self.options["key"] = MODULE_NAME
            if scope is not None:
                self.options["scope"] = scope
            if style is not None:
                self.options["style"] = style
            for item in replacements:
                found = False
                if 'file_pattern' in item:
                    for pattern in item['file_pattern']:
                        if fnmatch(file_name, pattern):
                            found = True
                            self.select(item)
                            break
                if not found and 'file_regex' in item:
                    for regex in item['file_regex']:
                        try:
                            flags = 0
                            if 'case' not in item or not bool(item['case']):
                                flags |= re.IGNORECASE
                            if 'dotall' in item and bool(item['dotall']):
                                deprecated(DEPRECATED_DOTALL)
                                flags |= re.DOTALL
                            r = re.compile(regex, flags)
                            if r.match(file_name) is not None:
                                found = True
                                self.select(item)
                                break
                        except Exception:
                            pass
                match |= found
        return match

    def select(self, item):
        """Select action to perform."""

        if "action" in item:
            if item['action'] == "fold":
                self.folds += item["sequence"]
            elif item['action'] == "unfold":
                self.unfolds += item["sequence"]
            elif item['action'] == "mark":
                self.highlights += item['sequence']
            else:
                error("action %s is not a valid action" % item["action"])
        elif "highlight" in item and bool(item['highlight']):
            sublime.message_dialog(
                "RegReplace:\n\"on_save_sequence\" setting option '\"highlight\": true' is deprecated!"
                "\nPlease use '\"action\": \"mark\"'."
            )
            self.highlights += item['sequence']
        else:
            self.replacements.append(
                {
                    "sequence": item['sequence'],
                    "multi_pass": True if "multi_pass" in item and bool(item['multi_pass']) else False
                }
            )

    def apply(self, view, replacements, options=None, multi_pass=False, action=None):
        """Run the actual RegReplace command."""

        if options is None:
            options = {}

        view.run_command(
            'reg_replace',
            {
                "replacements": replacements,
                'action': action,
                'options': options,
                'multi_pass': multi_pass,
                'no_selection': True
            }
        )

    def on_pre_save(self, view):
        """Perform searches and specified action on file save."""

        self.replacements = []
        self.highlights = []
        self.folds = []
        self.unfolds = []
        self.multi_pass = False
        self.options = {}
        if self.find_replacements(view):
            for replacements in self.replacements:
                self.apply(view, replacements['sequence'], multi_pass=replacements["multi_pass"])

            if len(self.highlights) > 0:
                self.apply(view, self.highlights, action="mark", options=self.options)

            if len(self.folds) > 0:
                self.apply(view, self.folds, action="fold")

            if len(self.unfolds) > 0:
                self.apply(view, self.unfolds, action="unfold")


class RegReplaceCommand(sublime_plugin.TextCommand):
    """RegReplace command."""

    handshake = None

    def forget_handshake(self):
        """Forget current view."""

        self.handshake = None
        self.clear_highlights(MODULE_NAME)
        self.replace_obj.close()

    def replace_prompt(self):
        """Prompt the user to see if they wish to replace the highlighted selections."""

        # Ask if replacements are desired
        self.handshake = self.view.id()
        self.view.window().show_input_panel(
            'Replace targets / perform action? (yes | no):',
            'yes',
            self.run_replace,
            None,
            self.forget_handshake
        )

    def run_replace(self, answer):
        """
        Initiate a find with replace.

        Used to initiate replacing when a find is executed with a replace prompt.
        """

        # Do we want to replace
        if answer.strip().lower() != 'yes':
            self.forget_handshake()
            return

        # See if we know this view
        window = sublime.active_window()
        view = window.active_view() if window is not None else None
        if view is not None:
            if self.handshake is not None and self.handshake == view.id():
                self.forget_handshake()
                # re-run command to actually replace targets
                view.run_command(
                    'reg_replace',
                    {
                        'replacements': self.replacements,
                        'action': self.action,
                        'multi_pass': self.multi_pass,
                        'regex_full_file_with_selections': self.full_file,
                        'options': self.options
                    }
                )
        else:
            self.forget_handshake()

    def clear_regions(self):
        """Clear highlighted regions specified."""

        cleared = False
        # Clear regions and exit
        if self.clear:
            self.clear_highlights(MODULE_NAME)
            self.replace_obj.close()
            cleared = True
        elif self.action == 'unmark' and 'key' in self.options:
            self.perform_action()
            self.replace_obj.close()
            cleared = True
        return cleared

    def set_highlights(self, key, style, color):
        """Mark regions with specified highlight options."""

        # Process highlight style
        highlight_style = 0
        if (self.find_only and self.selection_only) or style == 'underline':
            # Use underline if explicitly requested,
            # or if doing a find only when under a selection only (only underline can be seen through a selection)
            self.replace_obj.target_regions = underline(self.replace_obj.target_regions)
            highlight_style = sublime.DRAW_EMPTY_AS_OVERWRITE
        elif style == 'outline':
            highlight_style = sublime.DRAW_OUTLINED

        # highlight all of the found regions
        self.view.erase_regions(key)
        self.view.add_regions(
            key,
            self.replace_obj.target_regions,
            color,
            "",
            highlight_style
        )

    def clear_highlights(self, key):
        """Clear all highlighted regions of given key."""

        self.view.erase_regions(key)

    def is_selection_available(self):
        """See if there are selections in document."""

        available = False
        for sel in self.view.sel():
            if sel.size() > 0:
                available = True
                break
        return available

    def ignore_ending_newlines(self, regions):
        """Ignore newlines at the end of the region; newlines okay in the middle of region."""

        new_regions = []
        for region in regions:
            offset = 0
            size = region.size()
            if size > offset and self.view.substr(region.end() - 1) == '\n':
                offset += 1
            if size > offset and self.view.substr(region.end() - offset - 1) == '\r':
                offset += 1
            new_regions.append(sublime.Region(region.begin(), region.end() - offset))
        return new_regions

    def print_results_status_bar(self, text):
        """Print results to the status bar."""

        sublime.status_message(text)

    def print_results_panel(self, text):
        """Print find results to an output panel."""

        # Get/create output panel
        window = self.view.window()
        view = window.get_output_panel('reg_replace_results')

        # Turn off styles in panel
        view.settings().set('draw_white_space', 'none')
        view.settings().set('draw_indent_guides', False)
        view.settings().set('gutter', 'none')
        view.settings().set('line_numbers', False)
        view.set_syntax_file('Packages/Text/Plain text.tmLanguage')

        # Show Results in read only panel and clear selection in panel
        window.run_command('show_panel', {'panel': 'output.reg_replace_results'})
        view.set_read_only(False)
        RegReplaceGlobal.bfr = 'RegReplace Results\n\n' + text
        RegReplaceGlobal.region = sublime.Region(0, view.size())
        view.run_command("reg_replace_apply")
        RegReplaceGlobal.clear()
        view.set_read_only(True)
        view.sel().clear()

    def perform_action(self):
        """Perform action on targeted text."""

        status = True
        if self.action == 'fold':
            # Fold regions
            self.view.fold(self.ignore_ending_newlines(self.replace_obj.target_regions))
        elif self.action == 'unfold':
            # Unfold regions
            try:
                self.view.unfold(self.ignore_ending_newlines(self.replace_obj.target_regions))
            except Exception:
                error("Cannot unfold! Please upgrade to the latest stable beta build to remove this error.")
        elif self.action == 'mark':
            # Mark targeted regions
            if 'key' in self.options:
                color = self.options['scope'].strip() if 'scope' in self.options else DEFAULT_HIGHLIGHT_COLOR
                style = self.options['style'].strip() if 'style' in self.options else DEFAULT_HIGHLIGHT_STYLE
                self.set_highlights(self.options['key'].strip(), style, color)
        elif self.action == 'unmark':
            # Unmark targeted regions
            if 'key' in self.options:
                self.clear_highlights(self.options['key'].strip())
        elif self.action == 'select':
            self.view.sel().clear()
            self.view.sel().add_all(self.replace_obj.target_regions)
        else:
            # Not a valid action
            status = False
        return status

    def find_and_replace(self):
        """
        Walk the sequence finding the targeted regions in the text.

        If allowed, replacements will be done as well.
        """

        if self.use_test_buffer:
            replace_list = sublime.load_settings('reg_replace_test.sublime-settings').get('replacements', {})
        else:
            replace_list = rrsettingsrules.get('replacements', {})
        result_template = '%s: %d regions;\n' if self.panel_display else '%s: %d regions; '
        results = ''

        # Walk the sequence
        # Multi-pass only if requested and will be occurring
        if self.multi_pass and not self.find_only and self.action is None:
            # Multi-pass initialization
            current_replacements = 0
            total_replacements = 0
            count = 0

            # Sweep file until all instances are found
            # Avoid infinite loop and break out if sweep threshold is met
            while count < self.max_sweeps:
                count += 1
                current_replacements = 0

                for replacement in self.replacements:
                    # Is replacement available in the list?
                    if replacement in replace_list:
                        pattern = replace_list[replacement]
                        current_replacements += self.replace_obj.search(pattern, 'scope' in pattern)
                total_replacements += current_replacements

                # No more regions found?
                if current_replacements == 0:
                    break
            # Record total regions found
            results += 'Regions Found: %d regions;' % total_replacements
        else:
            not_found = []
            for replacement in self.replacements:
                # Is replacement available in the list?
                if replacement in replace_list:
                    pattern = replace_list[replacement]
                    results += result_template % (replacement, self.replace_obj.search(pattern, 'scope' in pattern))
                else:
                    not_found.append(replacement)
            if not_found:
                error("%d rules not found! See console." % len(not_found))
                print('\n'.join(['RegReplace: "%s" not found!' % r for r in not_found]))
        return results

    def start_sequence(self):
        """Run the replace sequence."""

        # Find targets and replace if applicable
        results = self.find_and_replace()

        if self.find_only:
            # Highlight regions
            style = rrsettings.get('find_highlight_style', DEFAULT_HIGHLIGHT_STYLE)
            color = rrsettings.get('find_highlight_color', DEFAULT_HIGHLIGHT_COLOR)
            self.set_highlights(MODULE_NAME, style, color)
            self.replace_prompt()
        else:
            self.clear_highlights(MODULE_NAME)
            # Perform action
            if self.action is not None:
                if not self.perform_action():
                    results = 'Error: %s - Bad Action!' % self.action

            # Report results
            if self.panel_display:
                self.print_results_panel(results)
            else:
                self.print_results_status_bar(results)
            self.replace_obj.close()

    def run(
        self, edit, replacements=None,
        find_only=False, clear=False, action=None,
        multi_pass=False, no_selection=False, regex_full_file_with_selections=False,
        options=None, use_test_buffer=False
    ):
        """Kick off sequence."""

        if replacements is None:
            replacements = []
        if options is None:
            options = {}

        self.use_test_buffer = bool(use_test_buffer)
        self.find_only = bool(find_only)
        self.action = action.strip() if action is not None else action
        self.full_file = bool(regex_full_file_with_selections)
        if not no_selection and rrsettings.get('selection_only', False) and self.is_selection_available():
            self.selection_only = True
        else:
            self.selection_only = False
        self.max_sweeps = rrsettings.get('multi_pass_max_sweeps', DEFAULT_MULTI_PASS_MAX_SWEEP)
        self.replacements = replacements
        self.multi_pass = bool(multi_pass)
        self.panel_display = rrsettings.get('results_in_panel', DEFAULT_SHOW_PANEL)
        self.options = options
        self.clear = clear

        self.replace_obj = FindReplace(
            self.view,
            edit,
            self.find_only,
            self.full_file,
            self.selection_only,
            self.max_sweeps,
            self.action
        )

        # Clear regions and exit; no need to run sequences
        if self.clear_regions():
            self.replace_obj.close()
            return

        # Is the sequence empty?
        if len(self.replacements) > 0:
            self.start_sequence()
        else:
            self.replace_obj.close()


def plugin_loaded():
    """Setup plugin."""

    global rrsettings
    global rrsettingsrules
    rrsettings = sublime.load_settings('reg_replace.sublime-settings')
    rrsettingsrules = sublime.load_settings('reg_replace_rules.sublime-settings')
