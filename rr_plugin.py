import sublime
import imp
import sys
import traceback
from os.path import join, normpath
import re


def sublime_format_path(pth):
    m = re.match(r"^([A-Za-z]{1}):(?:/|\\)(.*)", pth)
    if sublime.platform() == "windows" and m != None:
        pth = m.group(1) + "/" + m.group(2)
    return pth.replace("\\", "/")


class Plugin(object):
    loaded = []

    @classmethod
    def purge(cls):
        loaded = []

    @classmethod
    def get_module(cls, module_name, path_name):
        module = None
        try:
            module = sys.modules[module_name]
        except:
            module = cls.load_module(module_name, path_name)

    @classmethod
    def load_module(cls, module_name, path_name):
        module = imp.new_module(module_name)
        sys.modules[module_name] = module
        exec(
            compile(
                sublime.load_resource(sublime_format_path(path_name)),
                module_name,
                'exec'
            ),
            sys.modules[module_name].__dict__
        )
        return module

    @classmethod
    def load(cls, module_name, loaded=None):
        if module_name.startswith("rr_modules."):
            path_name = join("Packages", "RegReplace", normpath(module_name.replace('.', '/')))
        else:
            path_name = join("Packages", normpath(module_name.replace('.', '/')))
        path_name += ".py"
        module = None
        if module_name in cls.loaded:
            module = cls.get_module(module_name, path_name)
        else:
            module = cls.load_module(module_name, path_name)
        return module

    @classmethod
    def load_from(cls, module_name, attribute):
        return getattr(cls.load_module(module_name), attribute)
