"""
Reg Replace
Licensed under MIT
Copyright (c) 2011 - 2012 Isaac Muse <isaacmuse@gmail.com>
"""

import sublime
import sublime_plugin
import re
from fnmatch import fnmatch

DEFAULT_SHOW_PANEL = False
DEFAULT_HIGHLIGHT_COLOR = 'invalid'
DEFAULT_HIGHLIGHT_STYLE = 'outline'
DEFAULT_MULTI_PASS_MAX_SWEEP = 100
MAX_UNFOLD_THRESHOLD = 1000
MODULE_NAME = 'RegReplace'


def underline(regions):
    # Convert to empty regions
    new_regions = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            new_regions.append(sublime.Region(start))
            start += 1
    return new_regions


class RegReplaceGlobal(object):
    bfr = None
    region = None

    @classmethod
    def clear(cls):
        cls.bfr = None
        cls.region = None


class RegReplaceApplyCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.replace(edit, RegReplaceGlobal.region, RegReplaceGlobal.bfr)


class RegReplaceInputCommand(sublime_plugin.WindowCommand):
    def run_sequence(self, value):
        find_only = False
        action = None
        multi_pass = False
        options = {}

        # Parse Input
        matches = re.match(r"(\?)?\s*([^\+][\w\W]*|\+?)\s*:\s*([\w\W]*)\s*", value)
        if matches != None:
            # Sequence
            value = matches.group(3)

            # Find Only?
            if matches.group(1) == '?':
                find_only = True

            # Multi-Pass?
            if matches.group(2) == '+':
                multi_pass = True

            # Action?
            elif matches.group(2) != '' and matches.group(2) != None:
                # Mark or unmark: parse options?
                params = re.match(
                    r"^(unmark|mark)\s*=\s*([\w\s\.\-]*)\s*(?:,\s*([\w\s\.\-]*)\s*)?(?:,\s*([\w\s\.\-]*))?\s*",
                    matches.group(2)
                )
                if params != None:
                    if params.group(2) != '' and params.group(2) != None:
                        # Mark options
                        if params.group(1) == 'mark':
                            options['key'] = params.group(2).strip()
                            if params.group(3) != '' and params.group(3) != None:
                                options['scope'] = params.group(3).strip()
                            if params.group(4) != '' and params.group(4) != None:
                                options['style'] = params.group(4).strip()
                            action = params.group(1)
                        # Unmark options
                        elif params.group(1) == 'unmark':
                            options['key'] = params.group(2)
                            action = params.group(1)
                else:
                    # All other actions
                    action = matches.group(2)

        # Parse returned regex sequence
        sequence = [x.strip() for x in value.split(',')]
        view = self.window.active_view()

        # Execute sequence
        if view != None:
            view.run_command(
                'reg_replace',
                {
                    'replacements': sequence,
                    'find_only': find_only,
                    'action': action,
                    'multi_pass': multi_pass,
                    'options': options
                }
            )

    def run(self):
        # Display RegReplace input panel for on the fly regex sequences
        self.window.show_input_panel(
            'Regex Sequence:',
            '',
            self.run_sequence,
            None,
            None
        )


class RegReplaceListenerCommand(sublime_plugin.EventListener):
    def find_replacements(self, view):
        match = False
        file_name = view.file_name()
        if file_name != None and rrsettings.get('on_save', False):
            replacements = rrsettings.get('on_save_sequences', [])
            scope = rrsettings.get('on_save_highlight_scope', None)
            style = rrsettings.get('on_save_highlight_style', None)
            self.options["key"] = MODULE_NAME
            if scope != None:
                self.options["scope"] = scope
            if style != None:
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
                            if not 'case' in item or not bool(item['case']):
                                flags |= re.IGNORECASE
                            if 'dotall' in item and bool(item['dotall']):
                                flags |= re.DOTALL
                            r = re.compile(regex, flags)
                            if r.match(file_name) != None:
                                found = True
                                self.select(item)
                                break
                        except:
                            pass
                match |= found
        return match

    def select(self, item):
        if "action" in item:
            if item['action'] == "fold":
                self.folds += item["sequence"]
            elif item['action'] == "unfold":
                self.unfolds += item["sequence"]
            elif item['action'] == "mark":
                self.highlights += item['sequence']
            else:
                sublime.error_message("action %s is not a valid action" % item["action"])
        elif "highlight" in item and bool(item['highlight']):
            sublime.message_dialog(
                "RegReplace:\n\"on_save_sequence\" setting option '\"highlight\": true' is deprecated!\nPlease use '\"action\": \"mark\"'."
            )
            self.highlights += item['sequence']
        else:
            self.replacements.append(
                {
                    "sequence": item['sequence'],
                    "multi_pass": True if "multi_pass" in item and bool(item['multi_pass']) else False
                }
            )

    def apply(self, view, replacements, options={}, multi_pass=False, action=None):
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
    handshake = None

    def forget_handshake(self):
        # Forget current view
        self.handshake = None
        self.clear_highlights(MODULE_NAME)

    def replace_prompt(self):
        # Ask if replacements are desired
        self.view.window().show_input_panel(
            'Replace targets / perform action? (yes | no):',
            'yes',
            self.run_replace,
            None,
            self.forget_handshake
        )

    def run_replace(self, answer):
        # Do we want to replace
        if answer.strip().lower() != 'yes':
            self.forget_handshake()
            return

        # See if we know this view
        window = sublime.active_window()
        view = window.active_view() if window != None else None
        if view != None:
            if self.handshake != None and self.handshake == view.id():
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

    def set_highlights(self, key, style, color):
        # Process highlight style
        highlight_style = 0
        if (self.find_only and self.selection_only) or style == 'underline':
            # Use underline if explicity requested,
            # or if doing a find only when under a selection only (only underline can be seen through a selection)
            self.target_regions = underline(self.target_regions)
            highlight_style = sublime.DRAW_EMPTY_AS_OVERWRITE
        elif style == 'outline':
            highlight_style = sublime.DRAW_OUTLINED

        # higlight all of the found regions
        self.view.erase_regions(key)
        self.view.add_regions(
            key,
            self.target_regions,
            color,
            "",
            highlight_style
        )

    def clear_highlights(self, key):
        # Clear all highlighted regions
        self.view.erase_regions(key)

    def ignore_ending_newlines(self, regions):
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
        sublime.status_message(text)

    def print_results_panel(self, text):
        # Get/create output panel
        window = self.view.window()
        view = window.get_output_panel('reg_replace_results')

        #Turn off stylings in panel
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

    def perform_action(self, action, options={}):
        status = True
        if action == 'fold':
            # Ignore newlines at the end of the region; newlines okay in the middle of region
            self.view.fold(self.ignore_ending_newlines(self.target_regions))
        elif action == 'unfold':
            try:
                # Unfold regions
                self.view.unfold(self.ignore_ending_newlines(self.target_regions))
            except:
                sublime.error_message("Cannot unfold! Please upgrade to the latest stable beta build to remove this error.")
        elif action == 'mark':
            # Mark targeted regions
            if 'key' in options:
                color = options['scope'].strip() if 'scope' in options else DEFAULT_HIGHLIGHT_COLOR
                style = options['style'].strip() if 'style' in options else DEFAULT_HIGHLIGHT_STYLE
                self.set_highlights(options['key'].strip(), style, color)
        elif action == 'unmark':
            # Unmark targeted regions
            if 'key' in options:
                self.clear_highlights(options['key'].strip())
        else:
            status = False
        return status

    def get_sel_point(self):
        # See if there is a cursor and get the first selections starting point
        sel = self.view.sel()
        pt = None if len(sel) == 0 else sel[0].begin()
        return pt

    def qualify_by_scope(self, region, pattern):
        for entry in pattern:
            # Is there something to qualify?
            if len(entry) > 0:
                # Initialize qualification parameters
                qualify = True
                pt = region.begin()
                end = region.end()

                # Disqualify if entirely of scope
                if entry.startswith('-!'):
                    entry = entry.lstrip('-!')
                    qualify = False
                    while pt < end:
                        if self.view.score_selector(pt, entry) == 0:
                            qualify = True
                            break
                        pt += 1
                # Disqualify if one or more instances of scope
                elif entry.startswith('-'):
                    entry = entry.lstrip('-')
                    while pt < end:
                        if self.view.score_selector(pt, entry):
                            qualify = False
                            break
                        pt += 1
                # Qualify if entirely of scope
                elif entry.startswith('!'):
                    entry = entry.lstrip('!')
                    while pt < end:
                        if self.view.score_selector(pt, entry) == 0:
                            qualify = False
                            break
                        pt += 1
                # Qualify if one or more instances of scope
                else:
                    qualify = False
                    while pt < end:
                        if self.view.score_selector(pt, entry):
                            qualify = True
                            break
                        pt += 1
                # If qualificatin of one fails, bail
                if qualify == False:
                    return qualify
        # Qualification completed successfully
        return True

    def greedy_replace(self, find, replace, regions, scope_filter):
        # Initialize replace
        replaced = 0
        count = len(regions) - 1

        # Step through all targets and qualify them for replacement
        for region in reversed(regions):
            # Does the scope qualify?
            qualify = self.qualify_by_scope(region, scope_filter) if scope_filter != None else True
            if qualify:
                replaced += 1
                if self.find_only or self.action != None:
                    # If "find only" or replace action is overridden, just track regions
                    self.target_regions.append(region)
                else:
                    # Apply replace
                    self.view.replace(self.edit, region, replace[count])
            count -= 1
        return replaced

    def non_greedy_replace(self, find, replace, regions, scope_filter):
        # Initialize replace
        replaced = 0
        last_region = len(regions) - 1
        selected_region = None
        selection_index = 0

        # See if there is a cursor and get the first selections starting point
        pt = self.get_sel_point()

        # Intialize with first qualifying region for wrapping and the case of no cursor in view
        count = 0
        for region in regions:
            # Does the scope qualify?
            qualify = self.qualify_by_scope(region, scope_filter) if scope_filter != None else True
            if qualify:
                # Update as new replacement candidate
                selected_region = region
                selection_index = count
                break
            else:
                count += 1

        # If regions were already swept till the end, skip calculation relative to cursor
        if selected_region != None and count < last_region and pt != None:
            # Try and find the first qualifying match contained withing the first selection or after
            reverse_count = last_region
            for region in reversed(regions):
                # Make sure we are not checking previously checked regions
                # And check if region contained after start of selection?
                if reverse_count >= count and region.end() - 1 >= pt:
                    # Does the scope qualify?
                    qualify = self.qualify_by_scope(region, scope_filter) if scope_filter != None else True
                    if qualify:
                        # Update as new replacement candidate
                        selected_region = region
                        selection_index = reverse_count
                    # Walk backwards through replace index
                    reverse_count -= 1
                else:
                    break

        # Did we find a suitable region?
        if selected_region != None:
            # Show Instance
            replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action != None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.append(selected_region)
            else:
                # Apply replace
                self.view.replace(self.edit, selected_region, replace[selection_index])
        return replaced

    def apply_scope_regex(self, string, re_find, replace, greedy_replace, multi):
        replaced = 0
        extraction = string
        if multi and not self.find_only and self.action == None:
            extraction, replaced = self.apply_multi_pass_scope_regex(string, extraction, re_find, replace, greedy_replace)
        else:
            if greedy_replace:
                extraction, replaced = re.subn(re_find, replace, string)
            else:
                extraction, replaced = re.subn(re_find, replace, string, 1)
        return extraction, replaced

    def apply_multi_pass_scope_regex(self, string, extraction, re_find, replace, greedy_replace):
        multi_replaced = 0
        count = 0
        total_replaced = 0
        while count < self.max_sweeps:
            count += 1
            if greedy_replace:
                extraction, multi_replaced = re.subn(re_find, replace, extraction)
            else:
                extraction, multi_replaced = re.subn(re_find, replace, extraction, 1)
            if multi_replaced == 0:
                break
            total_replaced += multi_replaced
        return extraction, total_replaced

    def greedy_scope_literal_replace(self, regions, find, replace, greedy_replace):
        total_replaced = 0
        for region in reversed(regions):
            extraction = self.view.substr(region)
            replaced = 0
            try:
                extraction.index(find)
                replaced = 1
                if greedy_replace:
                    extraction = extraction.replace(find, replace)
                else:
                    extraction = extraction.replace(find, replace, 1)
            except ValueError:
                pass
            if replaced > 0:
                total_replaced += 1
                if self.find_only or self.action != None:
                    self.target_regions.append(region)
                else:
                    self.view.replace(self.edit, region, extraction)
        return total_replaced

    def non_greedy_scope_literal_replace(self, regions, find, replace, greedy_replace):
        # Initialize replace
        total_replaced = 0
        replaced = 0
        last_region = len(regions) - 1
        selected_region = None
        selected_extraction = None

        # See if there is a cursor and get the first selections starting point
        pt = self.get_sel_point()

        # Intialize with first qualifying region for wrapping and the case of no cursor in view
        count = 0
        for region in regions:
            extraction = self.view.substr(region)
            replaced = 0
            try:
                extraction.index(find)
                replaced = 1
                if greedy_replace:
                    extraction = extraction.replace(find, replace)
                else:
                    extraction = extraction.replace(find, replace, 1)
            except ValueError:
                pass
            if replaced > 0:
                selected_region = region
                selected_extraction = extraction
                break
            else:
                count += 1

        # If regions were already swept till the end, skip calculation relative to cursor
        if selected_region != None and count < last_region and pt != None:
            # Try and find the first qualifying match contained withing the first selection or after
            reverse_count = last_region
            for region in reversed(regions):
                # Make sure we are not checking previously checked regions
                # And check if region contained after start of selection?
                if reverse_count >= count and region.end() - 1 >= pt:
                    extraction = self.view.substr(region)
                    replaced = 0
                    try:
                        extraction.index(find)
                        replaced = 1
                        if greedy_replace:
                            extraction = extraction.replace(find, replace)
                        else:
                            extraction = extraction.replace(find, replace, 1)
                    except ValueError:
                        pass
                    if replaced > 0:
                        selected_region = region
                        selected_extraction = extraction
                    reverse_count -= 1
                else:
                    break

        # Did we find a suitable region?
        if selected_region != None:
            # Show Instance
            total_replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action != None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.append(selected_region)
            else:
                # Apply replace
                self.view.replace(self.edit, selected_region, selected_extraction)
        return total_replaced

    def greedy_scope_replace(self, regions, re_find, replace, greedy_replace, multi):
        total_replaced = 0
        try:
            for region in reversed(regions):
                replaced = 0
                string = self.view.substr(region)
                extraction, replaced = self.apply_scope_regex(string, re_find, replace, greedy_replace, multi)
                if replaced > 0:
                    total_replaced += 1
                    if self.find_only or self.action != None:
                        self.target_regions.append(region)
                    else:
                        self.view.replace(self.edit, region, extraction)
        except Exception as err:
            sublime.error_message('REGEX ERROR: %s' % str(err))
            return total_replaced

        return total_replaced

    def non_greedy_scope_replace(self, regions, re_find, replace, greedy_replace, multi):
        # Initialize replace
        total_replaced = 0
        replaced = 0
        last_region = len(regions) - 1
        selected_region = None
        selected_extraction = None

        # See if there is a cursor and get the first selections starting point
        pt = self.get_sel_point()

        # Intialize with first qualifying region for wrapping and the case of no cursor in view
        count = 0
        try:
            for region in regions:
                string = self.view.substr(region)
                extraction, replaced = self.apply_scope_regex(string, re_find, replace, greedy_replace, multi)
                if replaced > 0:
                    selected_region = region
                    selected_extraction = extraction
                    break
                else:
                    count += 1
        except Exception as err:
            sublime.error_message('REGEX ERROR: %s' % str(err))
            return total_replaced

        try:
            # If regions were already swept till the end, skip calculation relative to cursor
            if selected_region != None and count < last_region and pt != None:
                # Try and find the first qualifying match contained withing the first selection or after
                reverse_count = last_region
                for region in reversed(regions):
                    # Make sure we are not checking previously checked regions
                    # And check if region contained after start of selection?
                    if reverse_count >= count and region.end() - 1 >= pt:
                        string = self.view.substr(region)
                        extraction, replaced = self.apply_scope_regex(string, re_find, replace, greedy_replace, multi)
                        if replaced > 0:
                            selected_region = region
                            selected_extraction = extraction
                        reverse_count -= 1
                    else:
                        break
        except Exception as err:
            sublime.error_message('REGEX ERROR: %s' % str(err))
            return total_replaced

        # Did we find a suitable region?
        if selected_region != None:
            # Show Instance
            total_replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action != None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.append(selected_region)
            else:
                # Apply replace
                self.view.replace(self.edit, selected_region, selected_extraction)
        return total_replaced

    def select_scope_regions(self, regions, greedy_scope):
        if greedy_scope:
            # Greedy scope; return all scopes
            replaced = len(regions)
            self.target_regions = regions
        else:
            # Non-greedy scope; return first valid scope
            # If cannot find first valid scope after cursor
            number_regions = len(regions)
            selected_region = None
            first_region = 0
            last_region = number_regions - 1
            pt = self.get_sel_point()

            # Find first scope
            if number_regions > 0:
                selected_region = regions[0]

            # Walk backwards seeing which scope is valid
            # Quit if you reach the already selected first scope
            if selected_region != None and last_region > first_region and pt != None:
                reverse_count = last_region
                for region in reversed(regions):
                    if reverse_count >= first_region and region.end() - 1 >= pt:
                        selected_region = region
                        reverse_count -= 1
                    else:
                        break

            # Store the scope if we found one
            if selected_region != None:
                replaced += 1
                self.view.show(selected_region.begin())
                self.target_regions = [selected_region]

        return replaced

    def scope_apply(self, pattern):
        # Initialize replacement variables
        replaced = 0
        regions = []

        # Grab pattern definitions
        scope = pattern['scope']
        find = pattern['find'] if 'find' in pattern else None
        replace = pattern['replace'] if 'replace' in pattern else '\\0'
        greedy_scope = bool(pattern['greedy_scope']) if 'greedy_scope' in pattern else True
        greedy_replace = bool(pattern['greedy_replace']) if 'greedy_replace' in pattern else True
        case = bool(pattern['case']) if 'case' in pattern else True
        multi = bool(pattern['multi_pass_regex']) if 'multi_pass_regex' in pattern else False
        literal = bool(pattern['literal']) if 'literal' in pattern else False
        dotall = bool(pattern['dotall']) if 'dotall' in pattern else False

        if scope == None or scope == '':
            return replace

        if self.selection_only:
            sels = self.view.sel()
            sel_start = []
            sel_size = []
            for s in sels:
                sel_start.append(s.begin())
                sel_size.append(s.size())

        regions = self.view.find_by_selector(scope)

        if self.selection_only:
            regions = self.filter_by_selection(regions)

        # Find supplied?
        if find != None:
            # Compile regex: Ignore case flag?
            if not literal:
                try:
                    flags = 0
                    if not case:
                        flags |= re.IGNORECASE
                    if dotall:
                        flags |= re.DOTALL
                    re_find = re.compile(find, flags)
                except Exception as err:
                    sublime.error_message('REGEX ERROR: %s' % str(err))
                    return replaced

                #Greedy Scope?
                if greedy_scope:
                    replaced = self.greedy_scope_replace(regions, re_find, replace, greedy_replace, multi)
                else:
                    replaced = self.non_greedy_scope_replace(regions, re_find, replace, greedy_replace, multi)
            else:
                if greedy_scope:
                    replaced = self.greedy_scope_literal_replace(regions, find, replace, greedy_replace)
                else:
                    replaced = self.non_greedy_scope_literal_replace(regions, find, replace, greedy_replace)
        else:
            replaced = self.select_scope_regions(regions, greedy_scope)

        if self.selection_only:
            new_sels = []
            count = 0
            offset = 0
            for s in sels:
                r = sublime.Region(sel_start[count] + offset, s.end())
                new_sels.append(r)
                offset += r.size() - sel_size[count]
                count += 1
            sels.clear()
            sels.add_all(new_sels)

        return replaced

    def apply(self, pattern):
        # Initialize replacement variables
        regions = []
        flags = 0
        replaced = 0

        # Grab pattern definitions
        find = pattern['find']
        replace = pattern['replace'] if 'replace' in pattern else '\\0'
        literal = bool(pattern['literal']) if 'literal' in pattern else False
        dotall = bool(pattern['dotall']) if 'dotall' in pattern else False
        greedy = bool(pattern['greedy']) if 'greedy' in pattern else True
        case = bool(pattern['case']) if 'case' in pattern else True
        scope_filter = pattern['scope_filter'] if 'scope_filter' in pattern else []

        # Ignore Case?
        if not case:
            flags |= re.IGNORECASE
        if dotall:
            flags |= re.DOTALL

        if self.selection_only:
            sels = self.view.sel()
            sel_start = []
            sel_size = []
            for s in sels:
                sel_start.append(s.begin())
                sel_size.append(s.size())

        # Find and format replacements
        extractions = []
        try:
            # regions = self.view.find_all(find, flags, replace, extractions)
            if self.selection_only and not self.full_file:
                for sel in sels:
                    regions += self.regex_findall(find, flags, replace, extractions, literal, sel)
            else:
                regions = self.regex_findall(find, flags, replace, extractions, literal)
        except Exception as err:
            sublime.error_message('REGEX ERROR: %s' % str(err))
            return replaced

        if self.selection_only and self.full_file:
            regions, extractions = self.filter_by_selection(regions, extractions)

        # Where there any regions found?
        if len(regions) > 0:
            # Greedy or non-greedy search? Get replaced instances.
            if greedy:
                replaced = self.greedy_replace(find, extractions, regions, scope_filter)
            else:
                replaced = self.non_greedy_replace(find, extractions, regions, scope_filter)

        if self.selection_only:
            new_sels = []
            count = 0
            offset = 0
            for s in sels:
                r = sublime.Region(sel_start[count] + offset, s.end())
                new_sels.append(r)
                offset += r.size() - sel_size[count]
                count += 1
            sels.clear()
            sels.add_all(new_sels)

        return replaced

    def regex_findall(self, find, flags, replace, extractions, literal=False, sel=None):
        regions = []
        offset = 0
        if sel is not None:
            offset = sel.begin()
            bfr = self.view.substr(sublime.Region(offset, sel.end()))
        else:
            bfr = self.view.substr(sublime.Region(0, self.view.size()))
        flags |= re.MULTILINE
        if literal:
            find = re.escape(find)
        for m in re.compile(find, flags).finditer(bfr):
            regions.append(sublime.Region(offset + m.start(0), offset + m.end(0)))
            extractions.append(m.expand(replace))
        return regions

    def find_and_replace(self):
        replace_list = rrsettings.get('replacements', {})
        result_template = '%s: %d regions;\n' if self.panel_display else '%s: %d regions; '
        results = ''

        # Walk the sequence
        # Multi-pass only if requested and will be occuring
        if self.multi_pass and not self.find_only and self.action == None:
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
                        # Search within a specific scope or search and qualify with scopes
                        if 'scope' in pattern:
                            current_replacements += self.scope_apply(pattern)
                        else:
                            current_replacements += self.apply(pattern)
                total_replacements += current_replacements

                # No more regions found?
                if current_replacements == 0:
                    break
            # Record total regions found
            results += 'Regions Found: %d regions;' % total_replacements
        else:
            for replacement in self.replacements:
                # Is replacement available in the list?
                if replacement in replace_list:
                    pattern = replace_list[replacement]
                    # Search within a specific scope or search and qualify with scopes
                    if 'scope' in pattern:
                        results += result_template % (replacement, self.scope_apply(pattern))
                    else:
                        results += result_template % (replacement, self.apply(pattern))
        return results

    def filter_by_selection(self, regions, extractions=None):
        new_regions = []
        new_extractions = []
        idx = 0
        sels = self.view.sel()
        for region in regions:
            for sel in sels:
                if region.begin() >= sel.begin() and region.end() <= sel.end():
                    new_regions.append(region)
                    if extractions != None:
                        new_extractions.append(extractions[idx])
                        break
            idx += 1
        if extractions == None:
            return new_regions
        else:
            return new_regions, new_extractions

    def is_selection_available(self):
        available = False
        for sel in self.view.sel():
            if sel.size() > 0:
                available = True
                break
        return available

    def run(
        self, edit, replacements=[],
        find_only=False, clear=False, action=None,
        multi_pass=False, no_selection=False, regex_full_file_with_selections=False,
        options={}
    ):
        self.find_only = bool(find_only)
        self.action = action.strip() if action != None else action
        self.target_regions = []
        self.replacements = replacements
        self.full_file = bool(regex_full_file_with_selections)
        self.multi_pass = bool(multi_pass)
        self.options = options
        self.selection_only = True if not no_selection and rrsettings.get('selection_only', False) and self.is_selection_available() else False
        self.max_sweeps = rrsettings.get('multi_pass_max_sweeps', DEFAULT_MULTI_PASS_MAX_SWEEP)
        self.panel_display = rrsettings.get('results_in_panel', DEFAULT_SHOW_PANEL)
        self.edit = edit

        # Clear regions and exit
        if clear:
            self.clear_highlights(MODULE_NAME)
            return
        elif action == 'unmark' and 'key' in options:
            self.perform_action(action, options)

        # Establish new run
        self.handshake = self.view.id()

        # Is the sequence empty?
        if len(replacements) > 0:
            # Find targets and replace if applicable
            results = self.find_and_replace()

            # Higlight regions
            if self.find_only:
                style = rrsettings.get('find_highlight_style', DEFAULT_HIGHLIGHT_STYLE)
                color = rrsettings.get('find_highlight_color', DEFAULT_HIGHLIGHT_COLOR)
                self.set_highlights(MODULE_NAME, style, color)
                self.replace_prompt()
            else:
                self.clear_highlights(MODULE_NAME)
                # Perform action
                if action != None:
                    if not self.perform_action(action, options):
                        results = 'Error: Bad Action!'

                # Report results
                if self.panel_display:
                    self.print_results_panel(results)
                else:
                    self.print_results_status_bar(results)

def plugin_loaded():
    global rrsettings
    rrsettings = sublime.load_settings('reg_replace.sublime-settings')
