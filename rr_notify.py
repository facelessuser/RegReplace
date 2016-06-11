"""
Reg Replace.

Licensed under MIT
Copyright (c) 2011 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except Exception:
    class Notify(object):
        """Notify fallback."""

        @classmethod
        def is_ready(cls):
            """Return false to effectively disable SubNotify."""

            return False

DEPRECATED_CASE = '''\
"case" setting is deprecated and will be removed in a future release.
Please consider using "(?i)" for case insensitive searches.
'''

DEPRECATED_DOTALL = '''\
"dotall" setting is deprecated and will be removed in a future release.
Please consider using "(?s)" for case insensitive searches.
'''


def notify(msg):
    """Notify msg."""

    settings = sublime.load_settings("reg_replace.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RegReplace", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    """Error msg."""

    settings = sublime.load_settings("reg_replace.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RegReplace", "msg": msg, "level": "error"})
    else:
        sublime.error_message("RegReplace:\n%s" % msg)


def deprecated(msg):
    """Deprecation warning."""

    print('RegReplace: DEPRECATED - %s' % msg)
