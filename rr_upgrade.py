"""
Reg Replace.

Licensed under MIT
Copyright (c) 2011 - 2016 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin


class RegReplaceConvertRulesCommand(sublime_plugin.ApplicationCommand):
    """Convert rules to new version."""

    def run(self):
        """Convert old style rules to new style rules."""

        old = sublime.load_settings('reg_replace.sublime-settings').get('replacements', {})
        settings = sublime.load_settings('reg_replace_rules.sublime-settings')
        new = settings.get('replacements', {})
        for k, v in old.items():
            obj = {
                "find": None,
                "literal": None,
                "literal_ignorecase": None,
                "replace": None,
                "greedy": None,
                "greedy_scope": None,
                "multi_pass": None,
                "scope": None,
                "scope_filter": None,
                "plugin": None
            }
            if v.get('literal', False):
                obj['literal'] = True
                if v.get('case', True) is False:
                    obj['literal_ignorecase'] = True
                obj['find'] = v.get('find')
            else:
                prefix = ''
                if v.get('case', True) is False:
                    prefix == 'i'
                if v.get('dotall', False):
                    prefix == 's'
                if prefix:
                    prefix = "(?%s)" % prefix
                if 'find' in obj:
                    obj['find'] = prefix + v['find'].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

            obj['replace'] = v.get('replace', None)
            if 'greedy' in v:
                obj['greedy'] = v['greedy']
            elif 'greedy_replace' in v:
                obj['greedy'] = v['greedy_replace']
            obj['greedy_scope'] = v.get('greedy_scope', None)
            obj['multi_pass'] = v.get('multi_pass_regex', None)
            obj['scope'] = v.get('scope', None)
            obj['scope_filter'] = v.get('scope_filter', None)
            obj['plugin'] = v.get('plugin', None)
            obj['args'] = v.get('args', None)

            remove = []
            for k1, v1 in obj.items():
                if v1 is None:
                    remove.append(k1)
            for k1 in remove:
                del obj[k1]

            new[k] = obj
        settings.set('format', '3.0')
        settings.set('replacements', new)
        sublime.save_settings('reg_replace_rules.sublime-settings')
        sublime.message_dialog(
            'RegReplace rule conversion complete!\n\n'
            'Your new converted rules should be found in \'reg_replace_rules.sublime-settings\'.\n\n'
            'Double check your regex to ensure everything is fine, and then you can '
            'remove \'replacements\' from your \'reg_replace.sublime-settings\' file.'
        )
