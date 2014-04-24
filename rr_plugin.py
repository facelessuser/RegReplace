import imp
import sys
import traceback


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
