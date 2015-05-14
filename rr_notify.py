"""
Reg Replace.

Licensed under MIT
Copyright (c) 2011 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except:
    class Notify:

        """Notify fallback."""

        @classmethod
        def is_ready(cls):
            """Return false to effectively disable SubNotify."""

            return False


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
