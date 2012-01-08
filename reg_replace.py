import sublime
import sublime_plugin

rrsettings = hv_settings = sublime.load_settings('reg_replace.sublime-settings')


class RegReplaceMenuCommand(sublime_plugin.WindowCommand):
    def replace(self, value):
        if value != -1:
            command = self.names[value]
            self.window.run_command("reg_replace", {'reg_command': command})

    def run(self):
        commands = rrsettings.get('commands')
        self.names = []
        for command in commands:
            self.names.append(command)
        if len(self.names) > 0:
            self.window.show_quick_panel(self.names, self.replace)


class RegReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, reg_command=None):
        view = self.view

        # Did we get a reg command sequence name?
        if reg_command != None:
            commands = rrsettings.get('commands')

            # Does reg command sequence exist?
            if reg_command in commands:
                reg_pattern = commands[reg_command]

                # Walk through sequence
                for pattern in reg_pattern:
                    find = pattern['find']
                    replace = pattern['replace']
                    greedy = bool(pattern['greedy'])
                    case = bool(pattern['case'])
                    regions = []
                    flags = 0

                    # Ignore Case?
                    if not case:
                        flags |= sublime.IGNORECASE

                    # Greedy or non-greedy search?
                    if greedy:
                        regions = view.find_all(find, flags)
                    else:
                        # Todo: work from cursor forward
                        region = view.find(find, 0, flags)
                        if region != None:
                            regions = [region]

                    # Replace and account for offset after replace
                    for region in reversed(regions):
                        view.replace(edit, region, replace)
