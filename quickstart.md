# Getting Started

RegReplace allows you to create find and replace rules and chain them together in one command. You can even setup  
sequences to execute on file save.  Out of the box, RegReplace does nothing as you have to setup the find and replace  
rules and commands you want to use first.

RegReplace also allows you to assign alternative actions to the replace.  For example, you could find and fold.  You  
could find and select.  You could even find and mark (highlight).  All of these are covered more in the [documentation](http://facelessuser.github.io/RegReplace/usage/#override-actions).

# Creating a Rule

This is a simple example of a find and replace rule to remove trailing spaces.

1. Press <kbd>ctrl</kbd> + <kbd>shift</kbd> + <kbd>p</kbd> (or <kbd>cmd</kbd> + <kbd>shift</kbd> + <kbd>p</kbd> on OSX)  
to bring up the command palette.

2. Type `RegReplace` to see all the RegReplace commands and select `RegReplace: Create New Regular Expression`.  You  
will be presented with an output panel.  In the output panel will be all the rule options.

3. In this example we will create a rule that looks for trailing spaces.  We will replace those trailing spaces with  
with an empty string to remove them.  We will need to set a command name, a find pattern, and a replace pattern;  
everything else will be left to the defaults in the template.  The panel template is using Python syntax.

    ```python
    """
    If you don't need a setting, just leave it as None.
    When the rule is parsed, the default will be used.
    Each variable is evaluated separately, so you cannot substitute variables in other variables.
    """

    # name (str): Rule name.  Required.
    name = "trailing_spaces"

    # find (str): Regular expression pattern or literal string.
    #    Use (?i) for case insensitive. Use (?s) for dotall.
    #    See https://docs.python.org/3.4/library/re.html for more info on regex flags.
    #    Required unless "scope" is defined.
    find = r'[\t ]+$'

    # replace (str - default=r'\0'): Replace pattern.
    replace = r''

    # literal (bool - default=False): Preform a non-regex, literal search and replace.
    literal = None

    # literal_ignorecase (bool - default=False): Ignore case when "literal" is true.
    literal_ignorecase = None

    # scope (str): Scope to search for and to apply optional regex to.
    #    Required unless "find" is defined.
    scope = None

    # scope_filter ([str] - default=[]): An array of scope qualifiers for the match.
    #    Only used when "scope" is not defined.
    #
    #    - Any instance of scope qualifies match: scope.name
    #    - Entire match of scope qualifies match: !scope.name
    #    - Any instance of scope disqualifies match: -scope.name
    #    - Entire match of scope disqualifies match: -!scope.name
    scope_filter = None

    # greedy (bool - default=True): Apply action to all instances (find all).
    #    Used when "find" is defined.
    greedy = None

    # greedy_scope (bool - default=True): Find all the scopes specified by "scope."
    greedy_scope = None

    # multi_pass (bool - default=False): Perform multiple sweeps on the scope region to find
    #    and replace all instances of the regex when regex cannot be formatted to find
    #    all instances. Since a replace can change a scope, this can be useful.
    multi_pass = None

    # plugin (str): Define replace plugin for more advanced replace logic.
    plugin = None

    # args (dict): Arguments for 'plugin'.
    args = None

    # ----------------------------------------------------------------------------------------
    # test: Here you can setup a test command.  This is not saved and is just used for this session.
    #     - replacements ([str]): A list of regex rules to sequence together.
    #     - find_only (bool): Highlight current find results and prompt for action.
    #     - action (str): Apply the given action (fold|unfold|mark|unmark|select).
    #       This overrides the default replace action.
    #     - options (dict): optional parameters for actions (see documentation for more info).
    #         - key (str): Unique name for highlighted region.
    #         - scope (str - default="invalid"): Scope name to use as teh color.
    #         - style (str - default="outline"): Highlight style (solid|underline|outline).
    #     - multi_pass (bool): Repeatedly sweep with sequence to find all instances.
    #     - no_selection (bool): Overrides the "selection_only" setting and forces no selections.
    #     - regex_full_file_with_selections (bool): Apply regex search to full file then apply
    #       action to results under selections.
    test = {
        "replacements": [],
        "find_only": True,
        "action": None,
        "options": {},
        "multi_pass": False,
        "no_selection": False,
        "regex_full_file_with_selections": False
    }
    '''
    ```

4. Press <kbd>ctrl</kbd> + <kbd>s</kbd> (or <kbd>cmd</kbd> + <kbd>s</kbd> in OSX) to save.  The rule will be added to  
`Packages/User/reg_replace_rules.sublime-settings`.  You can press <kbd>esc</kbd> to dismiss the panel.

Now, you can create a command with your new rule. In this example, we will add a rule that finds and highlights the  
results and prompts us whether we wish to replace them; this is accomplished via the the `find_only` option.  Open up  
`Packages/User/Default.sublime-commands` and add the following Rule. After you add the rule, the command should be  
available in the command palette.  See [Usage documentation](http://facelessuser.github.io/RegReplace/usage/) to see all the other parameters you can use.

```js
    // Remove Items
    {
        "caption": "Remove: Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["trailing_spaces"], "find_only": true}
    },
```

If you wish to always execute this command on save, you can add an `on_save` event.

1. Navigate via the menu to `Preferences->Packages->RegReplace->Settings - User` to bring up your general RegReplace  
user settings file.

2. Now we will enable `on_save` events and create an event that will execute on all files. The `on_save_sequences` is  
an array where you can setup multiple sequences that can run in different files.  See the [documentation](http://facelessuser.github.io/RegReplace/usage/#apply-regular-expressions-right-before-file-save-event) for more  
information on the all the available options.

    ```js
    {
        // If on_save is true, RegReplace will search through the file patterns listed below right before a file is saved,
        // if the file name matches a file pattern, the sequence will be applied before the file is saved.
        // RegReplace will apply all sequences that apply to a given file in the order they appear below.

        "on_save": true,

        // on_save replacements
        "on_save_sequences": [
            // Remove trailing spaces
            {
                "file_pattern": ["*"],
                "sequence": ["trailing_spaces"]
            }
        ]
    }
    ```

    Alternatively, you could highlight the options instead or replacing them:

    ```js
    {
        // If on_save is true, RegReplace will search through the file patterns listed below right before a file is saved,
        // if the file name matches a file pattern, the sequence will be applied before the file is saved.
        // RegReplace will apply all sequences that apply to a given file in the order they appear below.

        "on_save": true,

        // on_save replacements
        "on_save_sequences": [
            // Remove trailing spaces
            {
                "file_pattern": ["*"],
                "sequence": ["trailing_spaces"],
                "action": "mark"
            }
        ]
    }
    ```

# Regular Expression Enhancements

RegReplace adds a couple of couple of regular expression enhancements. Out of the box, RegReplace uses Python's [re](https://docs.python.org/3.3/library/re.html) regular expressions module.  If you wish to extend re with additional special back references,  
you can take a look at the [documentation](http://facelessuser.github.io/RegReplace/usage/#extended-back-references) to see how to enable them.

The Python re module is good, but if you prefer, you can use the [regex](https://pypi.python.org/pypi/regex)  
module which includes numerous enhancements.  You can also enable backrefs when using the regex module, but  
it will just add support fewer back references as regex implements more than re.

# I Need Help!

That's okay.  Bugs are sometimes introduced or discovered in existing code.  Sometimes the documentation isn't clear.  
Support can be found over on the [official repo](https://github.com/facelessuser/RegReplace/issues).  Make sure to first search the documentation and previous issues  
before opening a new issue.  And when creating a new issue, make sure to fill in the provided issue template.  Please  
be courteous and kind in your interactions.
