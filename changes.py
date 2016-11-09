"""Changelog."""
import sublime
import sublime_plugin
import webbrowser

CSS = '''
html { {{'.background'|css}} }
div.reg-replace { padding: 0; margin: 0; {{'.background'|css}} }
.reg-replace h1, .reg-replace h2, .reg-replace h3,
.reg-replace h4, .reg-replace h5, .reg-replace h6 {
    {{'.string'|css}}
}
.reg-replace blockquote { {{'.comment'|css}} }
.reg-replace a { text-decoration: none; }
'''


class RegReplaceChangesCommand(sublime_plugin.WindowCommand):
    """Changelog command."""

    def run(self):
        """Show the changelog in a new view."""
        try:
            import mdpopups
            has_phantom_support = (mdpopups.version() >= (1, 10, 0)) and (int(sublime.version()) >= 3118)
        except Exception:
            has_phantom_support = False

        text = sublime.load_resource('Packages/RegReplace/CHANGES.md')
        view = self.window.new_file()
        view.set_name('RegReplace - Changelog')
        view.settings().set('gutter', False)
        if has_phantom_support:
            mdpopups.add_phantom(
                view,
                'changelog',
                sublime.Region(0),
                text,
                sublime.LAYOUT_INLINE,
                wrapper_class="reg-replace",
                css=CSS,
                on_navigate=self.on_navigate
            )
        else:
            view.run_command('insert', {"characters": text})
        view.set_read_only(True)
        view.set_scratch(True)

    def on_navigate(self, href):
        """Open links."""
        webbrowser.open_new_tab(href)
