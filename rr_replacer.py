"""
Reg Replace.

Licensed under MIT
Copyright (c) 2011 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
from RegReplace.rr_plugin import Plugin
from backrefs import bre, bregex
import re
import regex
import backrefs
import traceback
import string
from RegReplace.rr_notify import error

FORMAT_REPLACE = backrefs.version_info >= (2, 1, 0)


class RegexInputFormatter(string.Formatter):
    """Regex input formatter."""

    def __init__(self, engine):
        """Initialize."""

        self._engine = engine
        self.implicit = -1
        self.explicit = False
        super(RegexInputFormatter, self).__init__()

    def convert_field(self, value, conversion):
        """Convert to escaped format."""

        if conversion is not None and conversion == 'e':
            return self._engine.escape(value)
        return super(RegexInputFormatter, self).convert_field(value, conversion)

    def get_value(self, key, args, kwargs):
        """Get value."""

        if key == '':
            if not self.explicit:
                self.implicit += 1
                key = self.implicit
            else:
                raise ValueError("Cannot change from explicit index to implicit!")
        elif self.implicit >= 0:
            raise ValueError("Cannot change from implict to explicit indexing!")
        return super(RegexInputFormatter, self).get_value(key, args, kwargs)


class ScopeRepl(object):
    """
    Replace object for scopes.

    Call on_replace event if there is a plugin to run.
    """

    def __init__(self, has_plugin, replace, expand, replace_event):
        """Initialize."""

        self.has_plugin = has_plugin
        self.replace = replace
        self.expand = expand
        self.replace_event = replace_event

    def repl(self, m):
        """Apply replace."""

        return self.replace_event(m) if self.has_plugin else self.expand(m, self.replace)


class FindReplace(object):
    """Find and replace using regex."""

    def __init__(self, view, edit, find_only, full_file, selection_only, max_sweeps, action):
        """Initialize find replace object."""

        Plugin.purge()
        self.view = view
        self.edit = edit
        self.find_only = find_only
        self.full_file = full_file
        self.selection_only = selection_only
        self.max_sweeps = max_sweeps
        self.action = action
        self.target_regions = []
        self.plugin = None
        settings = sublime.load_settings('reg_replace.sublime-settings')
        self.extend = bool(settings.get("extended_back_references", False))
        self.use_regex = bool(settings.get('use_regex_module', False)) and bregex.REGEX_SUPPORT
        self.sel_input_max_size = int(settings.get('selection_input_max_size', 256))
        self.sel_input_max_count = int(settings.get('selection_input_max_count', 10))
        self.use_format = (self.extend or self.use_regex) and FORMAT_REPLACE
        if self.use_regex:
            regex_version = int(settings.get('regex_module_version', 0))
            if regex_version > 1:
                regex_version = 0
            self.regex_version_flag = bregex.VERSION1 if regex_version else bregex.VERSION0
        else:
            self.regex_version_flag = 0
        self.extend_module = bregex if self.use_regex else bre
        self.normal_module = regex if self.use_regex else re

    def view_replace(self, region, replacement):
        """
        Replace in the view.

        Account for tab settings that can interfere with the replace.
        """

        tabs_to_spaces = self.view.settings().get('translate_tabs_to_spaces', False)
        if tabs_to_spaces:
            self.view.settings().set('translate_tabs_to_spaces', False)
        self.view.replace(self.edit, region, replacement)
        if tabs_to_spaces:
            self.view.settings().set('translate_tabs_to_spaces', True)

    def close(self):
        """Clean up for the object.  Mainly clean up the tracked loaded plugins."""

        Plugin.purge()

    def on_replace(self, m):
        """Run the associated plugin on the replace event."""

        try:
            module = Plugin.load(self.plugin)
            text = module.replace(m, **self.plugin_args)
        except Exception:
            text = m.group(0)
            print(str(traceback.format_exc()))
        return text

    def filter_by_selection(self, regions, extractions=None):
        """Filter results by what is included in selected region."""

        new_regions = []
        new_extractions = []
        idx = 0
        sels = self.view.sel()
        for region in regions:
            for sel in sels:
                if region.begin() >= sel.begin() and region.end() <= sel.end():
                    new_regions.append(region)
                    if extractions is not None:
                        new_extractions.append(extractions[idx])
                        break
            idx += 1
        return (new_regions, new_extractions) if extractions is not None else (new_regions, None)

    def get_sel_point(self):
        """See if there is a cursor and get the first selections starting point."""

        sel = self.view.sel()
        pt = None if len(sel) == 0 else sel[0].begin()
        return pt

    def qualify_by_scope(self, region, pattern):
        """Qualify the match with scopes."""

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
                if qualify is False:
                    return qualify
        # Qualification completed successfully
        return True

    def greedy_replace(self, replace, regions, scope_filter):
        """Perform a greedy replace."""

        # Initialize replace
        replaced = 0
        count = len(regions) - 1

        # Step through all targets and qualify them for replacement
        for region in reversed(regions):
            # Does the scope qualify?
            qualify = self.qualify_by_scope(region, scope_filter) if scope_filter is not None else True
            if qualify:
                replaced += 1
                if self.find_only or self.action is not None:
                    # If "find only" or replace action is overridden, just track regions
                    self.target_regions.append(region)
                else:
                    # Apply replace
                    self.view_replace(region, replace[count])
            count -= 1
        return replaced

    def non_greedy_replace(self, replace, regions, scope_filter):
        """Perform a non-greedy replace."""

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
            qualify = self.qualify_by_scope(region, scope_filter) if scope_filter is not None else True
            if qualify:
                # Update as new replacement candidate
                selected_region = region
                selection_index = count
                break
            else:
                count += 1

        # If regions were already swept till the end, skip calculation relative to cursor
        if selected_region is not None and count < last_region and pt is not None:
            # Try and find the first qualifying match contained withing the first selection or after
            reverse_count = last_region
            for region in reversed(regions):
                # Make sure we are not checking previously checked regions
                # And check if region contained after start of selection?
                if reverse_count >= count and region.end() - 1 >= pt:
                    # Does the scope qualify?
                    qualify = self.qualify_by_scope(region, scope_filter) if scope_filter is not None else True
                    if qualify:
                        # Update as new replacement candidate
                        selected_region = region
                        selection_index = reverse_count
                    # Walk backwards through replace index
                    reverse_count -= 1
                else:
                    break

        # Did we find a suitable region?
        if selected_region is not None:
            # Show Instance
            replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action is not None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.append(selected_region)
            else:
                # Apply replace
                self.view_replace(selected_region, replace[selection_index])
        return replaced

    def expand(self, m, replace):
        """Apply replace."""

        if self.extend:
            return self.template(m)
        elif self.format:
            return m.expandf(replace)
        else:
            return m.expand(replace)

    def regex_findall(self, find, flags, replace, extractions, literal=False, sel=None):
        """Findall with regex."""

        regions = []
        offset = 0
        if sel is not None:
            offset = sel.begin()
            bfr = self.view.substr(sublime.Region(offset, sel.end()))
        else:
            bfr = self.view.substr(sublime.Region(0, self.view.size()))
        if self.extend:
            flags |= self.extend_module.MULTILINE
        else:
            flags |= self.normal_module.MULTILINE
        if literal:
            find = self.normal_module.escape(find)
        if self.extend and not literal:
            pattern = self.extend_module.compile_search(find, flags | self.regex_version_flag)
            if not self.plugin:
                self.template = self.extend_module.compile_replace(
                    pattern, replace, (self.extend_module.FORMAT if self.format else 0)
                )
        else:
            pattern = self.normal_module.compile(find, flags | self.regex_version_flag)
        for m in pattern.finditer(bfr):
            regions.append(sublime.Region(offset + m.start(0), offset + m.end(0)))
            if literal:
                extractions.append(replace)
            elif self.plugin is not None:
                extractions.append(self.on_replace(m))
            else:
                extractions.append(self.expand(m, replace))
        return regions

    def apply(self, pattern):
        """Normal find and replace."""

        # Initialize replacement variables
        regions = []
        flags = 0
        replaced = 0

        # Grab pattern definitions
        find = pattern['find']
        replace = pattern.get('replace', r'\g<0>')
        selection_inputs = pattern.get('selection_inputs', False)
        greedy = bool(pattern.get('greedy', True))
        scope_filter = pattern.get('scope_filter', [])
        self.format = bool(pattern.get('format_replace', False)) and self.use_format
        self.plugin = pattern.get("plugin", None)
        self.plugin_args = pattern.get("args", {})
        literal = pattern.get('literal', False)
        literal_ignorecase = literal and bool(pattern.get('literal_ignorecase', False))

        # Ignore Case?
        if literal_ignorecase:
            if self.extend:
                flags |= self.extend_module.IGNORECASE
            else:
                flags |= self.normal_module.IGNORECASE

        find, sels, sel_start, sel_size, errors = self.process_selections(
            find, self.selection_only, selection_inputs, literal
        )
        if errors:
            return replace

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
            print(str(traceback.format_exc()))
            error('REGEX ERROR: %s' % str(err))
            return replaced

        if self.selection_only and self.full_file:
            regions, extractions = self.filter_by_selection(regions, extractions)

        # Where there any regions found?
        if len(regions) > 0:
            # Greedy or non-greedy search? Get replaced instances.
            if greedy:
                replaced = self.greedy_replace(extractions, regions, scope_filter)
            else:
                replaced = self.non_greedy_replace(extractions, regions, scope_filter)

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

    def apply_scope_regex(self, string, pattern, replace, greedy_replace, multi, start, sub_regions):
        """Apply regex on a scope."""

        replaced = 0
        extraction = string

        scope_repl = ScopeRepl(self.plugin, replace, self.expand, self.on_replace)
        if self.extend and not self.plugin:
            self.template = self.extend_module.compile_replace(
                pattern, replace, (self.extend_module.FORMAT if self.format else 0)
            )
        if multi and not self.find_only and self.action is None:
            extraction, replaced = self.apply_multi_pass_scope_regex(
                pattern, extraction, scope_repl.repl, greedy_replace
            )
        elif self.find_only or self.action is not None:
            for m in pattern.finditer(string):
                sub_regions.append(sublime.Region(start + m.start(0), start + m.end(0)))
                replaced += 1
                if not greedy_replace:
                    break
        elif self.use_regex and not self.extend and self.format:
            if greedy_replace:
                extraction, replaced = pattern.subfn(scope_repl.repl, string)
            else:
                extraction, replaced = pattern.subfn(scope_repl.repl, string, 1)
        else:
            if greedy_replace:
                extraction, replaced = pattern.subn(scope_repl.repl, string)
            else:
                extraction, replaced = pattern.subn(scope_repl.repl, string, 1)
        return extraction, replaced

    def apply_multi_pass_scope_regex(self, pattern, extraction, repl, greedy_replace):
        """Use a multi-pass scope regex."""

        multi_replaced = 0
        count = 0
        total_replaced = 0
        while count < self.max_sweeps:
            count += 1
            if self.use_regex and not self.extend and self.format:
                if greedy_replace:
                    extraction, multi_replaced = pattern.subfn(repl, extraction)
                else:
                    extraction, multi_replaced = pattern.subfn(repl, extraction, 1)
            else:
                if greedy_replace:
                    extraction, multi_replaced = pattern.subn(repl, extraction)
                else:
                    extraction, multi_replaced = pattern.subn(repl, extraction, 1)
            if multi_replaced == 0:
                break
            total_replaced += multi_replaced
        return extraction, total_replaced

    def greedy_scope_literal_replace(self, regions, find, replace, greedy_replace):
        """Greedy literal scope replace."""

        total_replaced = 0
        for region in reversed(regions):
            sub_regions = []
            start = region.begin()
            extraction = self.view.substr(region)
            if self.find_only or self.action is not None:
                replace_count = 0
                for m in find.finditer(extraction):
                    sub_regions.append(sublime.Region(start + m.start(0), start + m.end(0)))
                    replace_count += 1
                    if not greedy_replace:
                        break
            else:
                if greedy_replace:
                    extraction, replace_count = find.subn(replace, extraction)
                    sub_regions = [region]
                else:
                    extraction, replace_count = find.subn(replace, extraction, count=1)
                    sub_regions = [region]

            if replace_count > 0:
                total_replaced += 1
                if self.find_only or self.action is not None:
                    self.target_regions.extend(sub_regions)
                else:
                    self.view_replace(region, extraction)
        return total_replaced

    def non_greedy_scope_literal_replace(self, regions, find, replace, greedy_replace):
        """Non greedy literal scope replace."""

        # Initialize replace
        total_replaced = 0
        last_region = len(regions) - 1
        selected_region = None
        selected_sub_regions = None
        selected_extraction = None

        # See if there is a cursor and get the first selections starting point
        pt = self.get_sel_point()

        # Intialize with first qualifying region for wrapping and the case of no cursor in view
        count = 0
        for region in regions:
            sub_regions = []
            start = region.begin()
            extraction = self.view.substr(region)
            if self.find_only or self.action is not None:
                replace_count = 0
                for m in find.finditer(extraction):
                    sub_regions.append(sublime.Region(start + m.start(0), start + m.end(0)))
                    replace_count += 1
                    if not greedy_replace:
                        break
            else:
                if self.use_regex and not self.extend and self.format:
                    if greedy_replace:
                        extraction, replace_count = find.subfn(replace, extraction)
                    else:
                        extraction, replace_count = find.subfn(replace, extraction, count=1)
                else:
                    if greedy_replace:
                        extraction, replace_count = find.subn(replace, extraction)
                    else:
                        extraction, replace_count = find.subn(replace, extraction, count=1)

            if replace_count > 0:
                selected_region = region
                selected_sub_regions = sub_regions
                selected_extraction = extraction
                break
            else:
                count += 1

        # If regions were already swept till the end, skip calculation relative to cursor
        if selected_region is not None and count < last_region and pt is not None:
            # Try and find the first qualifying match contained withing the first selection or after
            reverse_count = last_region
            for region in reversed(regions):
                sub_regions = []
                start = region.begin()
                # Make sure we are not checking previously checked regions
                # And check if region contained after start of selection?
                if reverse_count >= count and region.end() - 1 >= pt:
                    extraction = self.view.substr(region)
                    replace_count
                    if self.find_only or self.action is not None:
                        for m in find.finditer(extraction):
                            sub_regions.append(sublime.Region(start + m.start(0), start + m.end(0)))
                            replace_count += 1
                            if not greedy_replace:
                                break
                    else:
                        if self.use_regex and not self.extend and self.format:
                            if greedy_replace:
                                extraction, replace_count = find.subfn(replace, extraction)
                            else:
                                extraction, replace_count = find.subfn(replace, extraction, count=1)
                        else:
                            if greedy_replace:
                                extraction, replace_count = find.subn(replace, extraction)
                            else:
                                extraction, replace_count = find.subn(replace, extraction, count=1)

                    if replace_count > 0:
                        selected_region = region
                        selected_sub_regions = sub_regions
                        selected_extraction = extraction
                    reverse_count -= 1
                else:
                    break

        # Did we find a suitable region?
        if selected_region is not None:
            # Show Instance
            total_replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action is not None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.extend(selected_sub_regions)
            else:
                # Apply replace
                self.view_replace(selected_region, selected_extraction)
        return total_replaced

    def greedy_scope_replace(self, regions, re_find, replace, greedy_replace, multi):
        """Greedy scope replace."""

        total_replaced = 0
        try:
            for region in reversed(regions):
                sub_regions = []
                replaced = 0
                string = self.view.substr(region)
                extraction, replaced = self.apply_scope_regex(
                    string, re_find, replace, greedy_replace, multi, region.begin(), sub_regions
                )
                if replaced > 0:
                    total_replaced += 1
                    if self.find_only or self.action is not None:
                        self.target_regions.extend(sub_regions)
                    else:
                        self.view_replace(region, extraction)
        except Exception as err:
            print(str(traceback.format_exc()))
            error('REGEX ERROR: %s' % str(err))
            return total_replaced

        return total_replaced

    def non_greedy_scope_replace(self, regions, re_find, replace, greedy_replace, multi):
        """Non greedy scope replace."""

        # Initialize replace
        total_replaced = 0
        replaced = 0
        last_region = len(regions) - 1
        selected_region = None
        selected_sub_regions = None
        selected_extraction = None

        # See if there is a cursor and get the first selections starting point
        pt = self.get_sel_point()

        # Intialize with first qualifying region for wrapping and the case of no cursor in view
        count = 0
        try:
            for region in regions:
                sub_regions = []
                string = self.view.substr(region)
                extraction, replaced = self.apply_scope_regex(
                    string, re_find, replace, greedy_replace, multi, region.begin(), sub_regions
                )
                if replaced > 0:
                    selected_region = region
                    selected_sub_regions = sub_regions
                    selected_extraction = extraction
                    break
                else:
                    count += 1
        except Exception as err:
            print(str(traceback.format_exc()))
            error('REGEX ERROR: %s' % str(err))
            return total_replaced

        try:
            # If regions were already swept till the end, skip calculation relative to cursor
            if selected_region is not None and count < last_region and pt is not None:
                # Try and find the first qualifying match contained withing the first selection or after
                reverse_count = last_region
                for region in reversed(regions):
                    sub_regions = []
                    # Make sure we are not checking previously checked regions
                    # And check if region contained after start of selection?
                    if reverse_count >= count and region.end() - 1 >= pt:
                        string = self.view.substr(region)
                        extraction, replaced = self.apply_scope_regex(
                            string, re_find, replace, greedy_replace, multi, region.begin(), sub_regions
                        )
                        if replaced > 0:
                            selected_region = region
                            selected_sub_regions = sub_regions
                            selected_extraction = extraction
                        reverse_count -= 1
                    else:
                        break
        except Exception as err:
            print(str(traceback.format_exc()))
            error('REGEX ERROR: %s' % str(err))
            return total_replaced

        # Did we find a suitable region?
        if selected_region is not None:
            # Show Instance
            total_replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action is not None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.extend(selected_sub_regions)
            else:
                # Apply replace
                self.view_replace(selected_region, selected_extraction)
        return total_replaced

    def select_scope_regions(self, regions, greedy_scope):
        """Select scope region."""

        if greedy_scope:
            # Greedy scope; return all scopes
            replaced = len(regions)
            self.target_regions += regions
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
            if selected_region is not None and last_region > first_region and pt is not None:
                reverse_count = last_region
                for region in reversed(regions):
                    if reverse_count >= first_region and region.end() - 1 >= pt:
                        selected_region = region
                        reverse_count -= 1
                    else:
                        break

            # Store the scope if we found one
            if selected_region is not None:
                replaced += 1
                self.view.show(selected_region.begin())
                self.target_regions += [selected_region]

        return replaced

    def process_selections(self, orig_find, selection_only, selection_inputs, literal):
        """Process selections if necessary."""

        sel_start = []
        sel_size = []
        find = orig_find
        errors = False
        sels = self.view.sel()

        if selection_only and selection_inputs:
            error("Cannot use 'selection_inputs' with global option 'selection_only'!")
            errors = True
        elif selection_only:
            sel_start = []
            sel_size = []
            for s in sels:
                sel_start.append(s.begin())
                sel_size.append(s.size())
        elif selection_inputs:
            try:
                sel_inputs = []
                count = 0
                for s in sels:
                    assert s.size() <= self.sel_input_max_size, "Exceeded max selection size"
                    engine = self.normal_module
                    if not literal and self.extend:
                        engine = self.extend_module
                    sel_inputs.append(self.view.substr(s))
                    count += 1
                    assert count <= self.sel_input_max_count
                find = RegexInputFormatter(engine).format(orig_find, *sel_inputs, sel=sel_inputs)
            except Exception:
                print(str(traceback.format_exc()))
                error('Failed to process selection inputs.')
                errors = True
        return find, sels, sel_start, sel_size, errors

    def scope_apply(self, pattern):
        """Find and replace based on scope."""

        # Initialize replacement variables
        replaced = 0
        regions = []

        # Grab pattern definitions
        scope = pattern['scope']
        find = pattern.get('find')
        replace = pattern.get('replace', r'\g<0>')
        selection_inputs = pattern.get('selection_inputs', False)
        greedy_scope = bool(pattern.get('greedy_scope', True))
        greedy_replace = bool(pattern.get('greedy', True))
        literal = pattern.get('literal', False)
        literal_ignorecase = literal and bool(pattern.get('literal_ignorecase', False))
        multi = bool(pattern.get('multi_pass', False))
        self.format = bool(pattern.get('format_replace', False)) and self.use_format
        self.plugin = pattern.get("plugin", None)
        self.plugin_args = pattern.get("args", {})

        if scope is None or scope == '':
            return replace

        find, sels, sel_start, sel_size, errors = self.process_selections(
            find, self.selection_only, selection_inputs, literal
        )
        if errors:
            return replace

        regions = self.view.find_by_selector(scope)

        if self.selection_only:
            regions = self.filter_by_selection(regions)[0]

        # Find supplied?
        if find is not None:
            if not literal:
                try:
                    if self.extend:
                        re_find = self.extend_module.compile_search(find, self.regex_version_flag)
                    else:
                        re_find = self.normal_module.compile(find, self.regex_version_flag)
                except Exception as err:
                    print(str(traceback.format_exc()))
                    error('REGEX ERROR: %s' % str(err))
                    return replaced

                # Greedy Scope?
                if greedy_scope:
                    replaced = self.greedy_scope_replace(regions, re_find, replace, greedy_replace, multi)
                else:
                    replaced = self.non_greedy_scope_replace(regions, re_find, replace, greedy_replace, multi)
            else:
                try:
                    re_find = self.normal_module.compile(
                        self.normal_module.escape(find),
                        (self.normal_module.I if literal_ignorecase else 0) | self.regex_version_flag
                    )
                except Exception as err:
                    print(str(traceback.format_exc()))
                    error('REGEX ERROR: %s' % str(err))
                    return replaced

                if greedy_scope:
                    replaced = self.greedy_scope_literal_replace(regions, re_find, replace, greedy_replace)
                else:
                    replaced = self.non_greedy_scope_literal_replace(regions, re_find, replace, greedy_replace)
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

    def search(self, pattern, scope=False):
        """Search with the given patter."""

        return self.scope_apply(pattern) if scope else self.apply(pattern)
