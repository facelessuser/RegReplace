import sublime
import sublime_plugin
import re


class RegReplaceInputCommand(sublime_plugin.WindowCommand):
    def run_sequence(self, value):
        """
        Run the sequence
        """

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
        """
        Display RegReplace input panel for on the fly regex sequences
        """

        self.window.show_input_panel(
            'Regex Sequence:',
            '',
            self.run_sequence,
            None,
            None
        )
