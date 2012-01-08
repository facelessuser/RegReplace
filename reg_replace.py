import sublime
import sublime_plugin

rrsettings = hv_settings = sublime.load_settings('reg_replace.sublime-settings')


class RegReplaceCommand(sublime_plugin.TextCommand):
    def apply(self, pattern):
        find = pattern['find']
        replace = pattern['replace']
        greedy = bool(pattern['greedy'])
        case = bool(pattern['case'])
        regions = []
        flags = 0

        # Ignore Case?
        if not case:
            flags |= sublime.IGNORECASE

        # Find and format replacements
        extractions = []
        regions = self.view.find_all(find, flags, replace, extractions)
        count = len(extractions) - 1
        # Greedy or non-greedy search?
        if greedy:
            for region in reversed(regions):
                self.view.replace(self.edit, region, extractions[count])
                count -= 1
        else:
            # Todo: work from cursor forward
            if len(regions) > 0:
                self.view.replace(self.edit, regions[0], extractions[0])

    def run(self, edit, replacements=[]):
        # Is the sequence empty?
        if len(replacements) > 0:
            replace_list = rrsettings.get('replacements')
            self.edit = edit

            # Walk the sequence
            for replacement in replacements:
                # Is replacement available in the list?
                if replacement in replace_list:
                    self.apply(replace_list[replacement])
