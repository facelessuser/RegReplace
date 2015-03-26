import sublime
import re
import rr_extended
import traceback
from rr_plugin import Plugin


class FindReplace(object):
    def __init__(self, view, edit, find_only, full_file, selection_only, max_sweeps, action):
        """
        Initialize find replace object
        """

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

    def view_replace(self, region, replacement):
        tabs_to_spaces = self.view.settings().get('translate_tabs_to_spaces', False)
        if tabs_to_spaces:
            self.view.settings().set('translate_tabs_to_spaces', False)
        self.view.replace(self.edit, region, replacement)
        if tabs_to_spaces:
            self.view.settings().set('translate_tabs_to_spaces', True)
    
    def close(self):
        """
        Clean up for the object.  Mainly clean up the tracked loaded plugins.
        """

        Plugin.purge()

    def on_replace(self, m):
        """
        Run the associated plugin on the replace event
        """

        try:
            module = Plugin.load(self.plugin)
            text = module.replace(m, **self.plugin_args)
        except:
            text = m.group(0)
            print(str(traceback.format_exc()))
        return text

    def filter_by_selection(self, regions, extractions=None):
        """
        Filter results by what is included in selected region
        """

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
        if extractions is None:
            return new_regions
        else:
            return new_regions, new_extractions

    def get_sel_point(self):
        """
        See if there is a cursor and get the first selections starting point
        """

        sel = self.view.sel()
        pt = None if len(sel) == 0 else sel[0].begin()
        return pt

    def qualify_by_scope(self, region, pattern):
        """
        Qualify the match with scopes.
        """

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

    def greedy_replace(self, find, replace, regions, scope_filter):
        """
        Perform a greedy replace
        """

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

    def non_greedy_replace(self, find, replace, regions, scope_filter):
        """
        Perform a non-greedy replace
        """

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
        if self.extend:
            return rr_extended.replace(m, self.template)
        else:
            return m.expand(replace)

    def regex_findall(self, find, flags, replace, extractions, literal=False, sel=None):
        """
        Findall with regex
        """

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
        pattern = re.compile(find, flags)
        if self.extend:
            self.template = rr_extended.ReplaceTemplate(pattern, replace)
        for m in pattern.finditer(bfr):
            regions.append(sublime.Region(offset + m.start(0), offset + m.end(0)))
            if self.plugin is not None:
                extractions.append(self.on_replace(m))
            else:
                extractions.append(self.expand(m, replace))
        return regions

    def apply(self, pattern):
        """
        Normal find and replace
        """

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
        self.plugin = pattern.get("plugin", None)
        self.plugin_args = pattern.get("args", {})

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
            print(str(traceback.format_exc()))
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
            map(lambda x: self.view.sel().add(x), new_sels)

        return replaced

    def apply_scope_regex(self, string, re_find, replace, greedy_replace, multi):
        """
        Apply regex on a scope
        """

        replaced = 0
        extraction = string
        if self.plugin is None:
            repl = lambda m, replace=replace: self.expand(m, replace)
        else:
            repl = self.on_replace
        pattern = re.compile(re_find)
        if self.extend:
            self.template = rr_extended.ReplaceTemplate(pattern, replace)
        if multi and not self.find_only and self.action is None:
            extraction, replaced = self.apply_multi_pass_scope_regex(pattern, string, extraction, repl, greedy_replace)
        else:
            if greedy_replace:
                extraction, replaced = pattern.subn(repl, string)
            else:
                extraction, replaced = pattern.subn(repl, string, 1)
        return extraction, replaced

    def apply_multi_pass_scope_regex(self, pattern, string, extraction, repl, greedy_replace):
        """
        Use a multi-pass scope regex
        """

        multi_replaced = 0
        count = 0
        total_replaced = 0
        while count < self.max_sweeps:
            count += 1
            if greedy_replace:
                extraction, multi_replaced = pattern.subn(repl, extraction)
            else:
                extraction, multi_replaced = pattern.subn(repl, extraction, 1)
            if multi_replaced == 0:
                break
            total_replaced += multi_replaced
        return extraction, total_replaced

    def greedy_scope_literal_replace(self, regions, find, replace, greedy_replace):
        """
        Greedy literal scope replace
        """

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
                if self.find_only or self.action is not None:
                    self.target_regions.append(region)
                else:
                    self.view_replace(region, extraction)
        return total_replaced

    def non_greedy_scope_literal_replace(self, regions, find, replace, greedy_replace):
        """
        Non greedy literal scope replace
        """

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
        if selected_region is not None and count < last_region and pt is not None:
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
        if selected_region is not None:
            # Show Instance
            total_replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action is not None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.append(selected_region)
            else:
                # Apply replace
                self.view_replace(selected_region, selected_extraction)
        return total_replaced

    def greedy_scope_replace(self, regions, re_find, replace, greedy_replace, multi):
        """
        Greedy scope replace
        """

        total_replaced = 0
        try:
            for region in reversed(regions):
                replaced = 0
                string = self.view.substr(region)
                extraction, replaced = self.apply_scope_regex(string, re_find, replace, greedy_replace, multi)
                if replaced > 0:
                    total_replaced += 1
                    if self.find_only or self.action is not None:
                        self.target_regions.append(region)
                    else:
                        self.view_replace(region, extraction)
        except Exception as err:
            print(str(traceback.format_exc()))
            sublime.error_message('REGEX ERROR: %s' % str(err))
            return total_replaced

        return total_replaced

    def non_greedy_scope_replace(self, regions, re_find, replace, greedy_replace, multi):
        """
        Non greedy scope replace
        """

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
            print(str(traceback.format_exc()))
            sublime.error_message('REGEX ERROR: %s' % str(err))
            return total_replaced

        try:
            # If regions were already swept till the end, skip calculation relative to cursor
            if selected_region is not None and count < last_region and pt is not None:
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
            print(str(traceback.format_exc()))
            sublime.error_message('REGEX ERROR: %s' % str(err))
            return total_replaced

        # Did we find a suitable region?
        if selected_region is not None:
            # Show Instance
            total_replaced += 1
            self.view.show(selected_region.begin())
            if self.find_only or self.action is not None:
                # If "find only" or replace action is overridden, just track regions
                self.target_regions.append(selected_region)
            else:
                # Apply replace
                self.view_replace(selected_region, selected_extraction)
        return total_replaced

    def select_scope_regions(self, regions, greedy_scope):
        """
        Select scope region
        """

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

    def scope_apply(self, pattern):
        """
        Find and replace based on scope
        """

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
        self.plugin = pattern.get("plugin", None)
        self.plugin_args = pattern.get("args", {})

        if scope is None or scope == '':
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
        if find is not None:
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
                    print(str(traceback.format_exc()))
                    sublime.error_message('REGEX ERROR: %s' % str(err))
                    return replaced

                # Greedy Scope?
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
            map(lambda x: self.view.sel().add(x), new_sels)

        return replaced

    def search(self, pattern, scope=False):
        return self.scope_apply(pattern) if scope else self.apply(pattern)
