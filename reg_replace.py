'''
Reg Replace
Licensed under MIT
Copyright (c) 2011 Isaac Muse <isaacmuse@gmail.com>
'''

import sublime
import sublime_plugin

DEFAULT_SHOW_PANEL = False
DEFAULT_HIGHLIGHT_COLOR = "invalid"
DEFAULT_HIGHLIGHT_STYLE = "outline"
rrsettings = sublime.load_settings('reg_replace.sublime-settings')


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


class RegReplaceInputCommand(sublime_plugin.WindowCommand):
    def run_sequence(self, value):
        # Parse returned regex sequence
        sequence = [x.strip() for x in value.split(',')]
        view = self.window.active_view()

        # Execute sequence
        if view != None:
            view.run_command('reg_replace', {'replacements': sequence})

    def run(self):
        # Display RegReplace input panel for on the fly regex sequences
        self.window.show_input_panel(
            "Regex Sequence:",
            "",
            self.run_sequence,
            None,
            None
        )


class RegReplaceCommand(sublime_plugin.TextCommand):
    handshake = None

    def forget_handshake(self):
        # Forget current view
        self.handshake = None
        self.clear_highlights()

    def replace_prompt(self):
        # Ask if replacements are desired
        self.view.window().show_input_panel(
            "Replace targets? (yes | no):",
            "yes",
            self.run_replace,
            None,
            self.forget_handshake
        )

    def run_replace(self, answer):
        # Do we want to replace
        if answer.strip().lower() != "yes":
            self.forget_handshake()
            return

        # See if we know this view
        window = sublime.active_window()
        view = window.active_view() if window != None else None
        if view != None:
            if self.handshake != None and self.handshake == view.id():
                self.forget_handshake()
                # re-run command to actually replace targets
                view.run_command('reg_replace', {'replacements': self.replacements})
        else:
            self.forget_handshake()

    def set_highlights(self):
        # Process highlight style
        style = rrsettings.get("find_highlight_style", DEFAULT_HIGHLIGHT_STYLE)
        highlight_style = 0
        if style == "outline":
            highlight_style = sublime.DRAW_OUTLINED
        elif style == "underline":
            self.highlight_regions = underline(self.highlight_regions)
            highlight_style = sublime.DRAW_EMPTY_AS_OVERWRITE

        # higlight all of the found regions
        self.view.erase_regions('RegReplace')
        self.view.add_regions(
            'RegReplace',
            self.highlight_regions,
            rrsettings.get('find_highlight_color', DEFAULT_HIGHLIGHT_COLOR),
            highlight_style
        )

    def clear_highlights(self):
        # Clear all highlighted regions
        self.view.erase_regions('RegReplace')

    def print_results_status_bar(self, text):
        sublime.status_message(text)

    def print_results_panel(self, text):
        # Get/create output panel
        window = self.view.window()
        view = window.get_output_panel('reg_replace_results')

        #Turn off stylings in panel
        view.settings().set("draw_white_space", "none")
        view.settings().set("draw_indent_guides", False)
        view.settings().set("gutter", "none")
        view.settings().set("line_numbers", False)

        # Show Results in read only panel and clear selection in panel
        window.run_command("show_panel", {"panel": "output.reg_replace_results"})
        view.set_read_only(False)
        edit = view.begin_edit()
        view.replace(edit, sublime.Region(0, view.size()), "RegReplace Results\n\n" + text)
        view.end_edit(edit)
        view.set_read_only(True)
        view.sel().clear()

    def qualify_by_scope(self, region, pattern):
        for entry in pattern:
            # Is there something to qualify?
            if len(entry) > 0:
                # Initialize qualification parameters
                qualify = True
                pt = region.begin()
                end = region.end()

                # Disqualify if entirely of scope
                if entry.startswith("-!"):
                    entry = entry.lstrip("-!")
                    qualify = False
                    while pt < end:
                        if self.view.score_selector(pt, entry) == 0:
                            qualify = True
                            break
                        pt += 1
                # Disqualify if one or more instances of scope
                elif entry.startswith("-"):
                    entry = entry.lstrip("-")
                    while pt < end:
                        if self.view.score_selector(pt, entry):
                            qualify = False
                            break
                        pt += 1
                # Qualify if entirely of scope
                elif entry.startswith("!"):
                    entry = entry.lstrip("!")
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
                if self.find_only:
                    # If "find only", just track regions
                    self.highlight_regions.append(region)
                else:
                    # Apply replace
                    self.view.replace(self.edit, region, replace[count])
            count -= 1
        return replaced

    def non_greedy_replace(self, find, replace, regions, scope_filter):
        # Initialize replace
        replaced = 0
        last_region = count = len(regions) - 1
        selected_region = None
        selection_index = 0

        # See if there is a cursor and get the first selections starting point
        sel = self.view.sel()
        if len(sel) == 0:
            pt = None
        else:
            pt = sel[0].begin()

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
                if reverse_count > count and region.end() - 1 >= pt:
                    # Does the scope qualify?
                    qualify = self.qualify_by_scope(region, scope_filter) if scope_filter != None else True
                    if qualify:
                        # Update as new replacement candidate
                        selected_region = region
                        selection_index = reverse_count
                    else:
                        # Walk backwards through replace index
                        reverse_count -= 1
                else:
                    break

        # Did we find a suitable region?
        if selected_region != None:
            # Show Instance
            replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only:
                # If "find only", just track regions
                self.highlight_regions.append(selected_region)
            else:
                # Apply replace
                self.view.replace(self.edit, selected_region, replace[selection_index])
        return replaced

    def apply(self, pattern):
        # Initialize replacement variables
        regions = []
        flags = 0
        replaced = 0

        # Grab pattern definitions
        find = pattern['find']
        replace = pattern['replace']
        greedy = bool(pattern['greedy']) if 'greedy' in pattern else True
        case = bool(pattern['case']) if 'case' in pattern else True
        scope_filter = pattern['scope_filter'] if 'scope_filter' in pattern else []

        # Ignore Case?
        if not case:
            flags |= sublime.IGNORECASE

        # Find and format replacements
        extractions = []
        regions = self.view.find_all(find, flags, replace, extractions)

        # Where there any regions found?
        if len(regions) > 0:
            # Greedy or non-greedy search? Get replaced instances.
            if greedy:
                replaced = self.greedy_replace(find, extractions, regions, scope_filter)
            else:
                replaced = self.non_greedy_replace(find, extractions, regions, scope_filter)
        return replaced

    def run(self, edit, replacements=[], find_only=False, clear=False):
        self.find_only = find_only
        self.highlight_regions = []
        self.replacements = replacements

        # Clear regions and exit
        if clear:
            self.clear_highlights()
            return

        # Establish new run
        self.handshake = self.view.id()

        # Is the sequence empty?
        if len(replacements) > 0:
            replace_list = rrsettings.get('replacements', {})
            panel_display = rrsettings.get("results_in_panel", DEFAULT_SHOW_PANEL)
            result_template = "%s: %d regions;\n" if panel_display else "%s: %d regions; "
            self.edit = edit
            results = ""

            # Walk the sequence
            for replacement in replacements:
                # Is replacement available in the list?
                if replacement in replace_list:
                    results += result_template % (replacement, self.apply(replace_list[replacement]))

            # Higlight regions
            if self.find_only:
                self.set_highlights()
                self.replace_prompt()
            else:
                # Report results
                if panel_display:
                    self.print_results_panel(results)
                else:
                    self.print_results_status_bar(results)
