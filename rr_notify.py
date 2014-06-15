import sublime
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except:
    class Notify:
        @classmethod
        def is_ready(cls):
            return False


def notify(msg):
    settings = sublime.load_settings("reg_replace.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RegReplace", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    settings = sublime.load_settings("reg_replace.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RegReplace", "msg": msg, "level": "error"})
    else:
        sublime.error_message("RegReplace:\n%s" % msg)
