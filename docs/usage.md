!!! warning "Regular Expression Engine"
    Remember that the regular expression engine that is used is Python's [re][re], not Sublime's internal regular expression engine.  If enabling `extended_back_references`, additional syntax is added which is covered in the [backrefs documentation][backrefs].

    To enable such features as case insensitivity or dotall, see [re's documentation](https://docs.python.org/3.4/library/re.html).

## Create Find and Replace Sequences
To use, replacements must be defined in the `reg_replace_rules.sublime-settings` file.

There are two types of rules that can be created: scope rules (with optional scope qualifiers) or scope searches that apply regular expressions to the targeted scopes.  We will call these **regex** and **scope regex** rules respectively.

**Regex** rules use regular expressions to find regions, and then you can use scopes to qualify the regions before applying the replace.  These rules can use the following options:

```js
    /*
    ###### Regex with optional scope qualifiers. ######
    - find (required)
    - replace
    - literal
    - literal_ignorecase
    - greedy
    - scope_filter
    - plugin
    - args
    */

    {
        "replacements": {
            "html5_remove_deprecated_type_attr": {
                "find": "(?i)(<(style|script)[^>]*)\\stype=(\"|')text/(css|javascript)(\"|')([^>]*>)",
                "replace": "\\1\\6",
                "greedy": true
            },
```

The second kind of rule is the **scope regex** which allows you to search for a scope type and then apply regular expression to the regions to filter the matches and make replacements.

```js
    /*
    ###### Scope search with regular expression applied to scope region. ######
    - scope (required)
    - find
    - replace
    - literal
    - literal_ignorecase
    - greedy
    - greedy_scope
    - multi_pass
    - plugn
    - args
    */

    {
            "replacements": {
                "remove_comments": {
                    "scope": "comment",
                    "find" : "(([^\\n\\r]*)(\\r\\n|\\n))*([^\\n\\r]+)",
                    "replace": "",
                    "greedy": true,
                    "greedy_scope": true
                }
```

A description of all the options is found below:

```
    name:               (str): Rule name.  Required.

    find:               (str): Regular expression pattern or literal string.
                        Use (?i) for case insensitive. Use (?s) for dotall.
                        See https://docs.python.org/3.4/library/re.html for more info on regex flags.
                        Required unless "scope" is defined.

    replace:            (str - default=r'\0'): Replace pattern.

    literal:            (bool - default=False): Preform a non-regex, literal search and replace.

    literal_ignorecase: (bool - default=False): Ignore case when "literal" is true.

    scope:              (str): Scope to search for and to apply optional regex to.
                        Required unless "find" is defined.

    scope_filter:       ([str] - default=[]): An array of scope qualifiers for the match.
                        Only used when "scope" is not defined.

                        - Any instance of scope qualifies match: scope.name
                        - Entire match of scope qualifies match: !scope.name
                        - Any instance of scope disqualifies match: -scope.name
                        - Entire match of scope disqualifies match: -!scope.name

    greedy:             (bool - default=True): Apply action to all instances (find all).
                        Used when "find" is defined.

    greedy_scope:       (bool - default=True): Find all the scopes specified by "scope."

    multi_pass:         (bool - default=False): Perform multiple sweeps on the scope region to find
                        and replace all instances of the regex when regex cannot be formatted to find
                        all instances.  Since a replace can change a scope, this can be useful.

    plugin:             (str): Define replace plugin for more advanced replace logic.
                        Only used for regex replaces and replace.

    args:               (dict): Arguments for 'plugin'.
                        Only used for regex replaces and replace.
```

Once you have replacements defined, there are a number of ways you can run a sequence.  One way is to create a command in the command palette by editing/creating a `Default.sublime-commands` in your `User` folder and then adding your command(s).

Basic replacement command:

```javascript
    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["remove_trailing_spaces"]}
    },
```

Chained replacements in one command:

```javascript
    {
        "caption": "Reg Replace: Remove HTML Comments and Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["remove_html_comments", "remove_trailing_spaces"]}
    }
```

You can also bind a replacement command to a shortcut.

```javascript
    {
        "keys": ["ctrl+shift+t"],
        "command": "reg_replace",
        "args": {"replacements": ["remove_trailing_spaces"]}
    }
```

## A Better Way To Create Regex Rules
Recently a new feature was added that allows the editing of the regular expression rules to be done in a Python syntax highlighted panel.  This allows for a less cumbersome editing experience.  Users can even split their regular expressions on multiple lines and add comments which will all be preserved for the next time the rule is viewed.

While in the edit panel, you can press <kbd>ctrl</kbd> + <kbd>s</kbd> on Windows/Linux (or <kbd>super</kbd> + <kbd>s</kbd> on OSX) and the rule will be saved back to the settings file.  On save, the regex is compiled to test if it is valid; if it fails, you should be alerted and the save will be canceled.

To edit, insert, or delete rules, you can use the following command palette commands:

- RegReplace: Edit Regular Expression Rule
- RegReplace: Create New Regular Expression Rule
- RegReplace: Delete Regular Expression Rule

![edit panel](imgs/edit_panel.png)

You can also test the regular expression from the edit panel.  At the bottom of the panel, you should see the `test` variable which will allow you to configure a sequence to run from the panel.  Once configured, you can press <kbd>ctrl</kbd> + <kbd>f</kbd> on Windows/Linux (or <kbd>super</kbd> + <kbd>f</kbd> on OSX) to execute.  Keep in mind, you can run the current rule sequenced together with others in the test configuration to test how it plays with other rules.  `test` is not saved with the other settings, but is only good for the current session.

```python
# ----------------------------------------------------------------------------------------
# test: Here you can setup a test command.  This is not saved and is just used for this session.
#     - replacements ([str]): A list of regex rules to sequence together.
#     - find_only (bool): Highlight current find results and prompt for action.
#     - action (str): Apply the given action (fold|unfold|mark|unmark|select).
#       This overrides the default replace action.
#     - options (dict): optional parameters for actions (see documentation for more info).
#         - key (str): Unique name for highlighted region.
#         - scope (str - default="invalid"): Scope name to use as the color.
#         - style (str - default="outline"): Highlight style (solid|underline|outline).
#     - multi_pass (bool): Repeatedly sweep with sequence to find all instances.
#     - no_selection (bool): Overrides the "selection_only" setting and forces no selections.
#     - regex_full_file_with_selections (bool): Apply regex search to full file then apply
#       action to results under selections.
```

![test variable](imgs/test.png)

Depending on how the test command was configured, it may cause the panel to close, or you might accidentally close it by pressing <kbd>esc</kbd> or running some other command.  When closed, the currently opened rule is not lost and can be brought back by running the command palette command `RegReplace: Show Edit Panel` (the command will only work if the panel has been opened at least once).  You can also use the panel icon in the bottom left hand corner of the Sublime Text window (only on later versions of Sublime Text 3).

## View Without Replacing
If you would simply like to view what the sequence would find without replacing, you can construct a command to highlight targets without replacing them (each pass could affect the end result, but this just shows all passes without predicting the replacements).

Just add the "find_only" argument and set it to true.

```javascript
    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["remove_trailing_spaces"], "find_only": true}
    },
```

A prompt will appear allowing you to replace the highlighted regions.  Regions will be cleared on cancel.

If for any reason the highlights do not get cleared, you can simply run the "RegReplace: Clear Highlights" command from the command palette.

Highlight color and style can be changed in the settings file.

## Override Actions
If instead of replacing you would like to do something else, you can override the action. Actions are defined in commands by setting the `action` parameter.  Some actions may require additional parameters be set in the `options` parameter.  See examples below.

```javascript
    {
        "caption": "Reg Replace: Fold HTML Comments",
        "command": "reg_replace",
        "args": {"replacements": ["remove_html_comments"], "action": "fold"}
    },
    {
        "caption": "Reg Replace: Unfold HTML Comments",
        "command": "reg_replace",
        "args": {"replacements": ["remove_html_comments"], "action": "unfold"}
    },
    {
        "caption": "Reg Replace: Mark Example",
        "command": "reg_replace",
        "args": {
            "replacements": ["example"],
            "action": "mark",
            "options": {"key": "name", "scope": "invalid", "style": "underline"}
        }
    },
    {
        "caption": "Reg Replace: Unmark Example",
        "command": "reg_replace",
        "args": {
            "action": "unmark",
            "options": {"key": "name"}
        }
    },
```

###Supported override actions:
- fold
- unfold
- mark
- unmark
- select

### Fold Override
```js
"action": "fold"
```

This action folds the given find target.  This action has no parameters.

### Unfold Override
```js
"action": "unfold"
```

This action unfolds the all regions that match the given find target.  This action has no parameters

### Mark Override
```js
"action": "mark"
```

This action highlights the regions of the given find target.

#### Mark Options
Action options are specified with the `options` key.

#####Required Parameters:
```js
"options": {"key": "name"}
```

Unique name for highlighted regions.

####Optional Parameters:
```js
"options": {"scope": "invalid"}
```

Scope name to use as the color. Default is `invalid`.

```js
"options": {"style": "outline"}
```

Highlight style (solid|underline|outline). Default is `outline`.

### Unmark Override
```js
"action": "unmark"
```

This action removes the highlights of a given `key`.  Replacements can be omitted with this command.

#### Unmark Options
Action options are specified with the `options` key.

#####Required Parameters:
```js
"options": {"key": "name"}
```

unique name of highlighted regions to clear

### Select Override
```js
"action": "select"
```

This action selects the regions of the given find target.

## Multi-Pass
Sometimes a regular expression cannot be made to find all instances in one pass.  In this case, you can use the multi-pass option.  This option will cause the entire sequence to repeatedly executed until all instances are found and replaced.  To protect against a poorly constructed multi-pass regular expression looping forever, there is a default max sweep threshold that will cause the sequence to kick out if it is reached.  This threshold can be tweaked in the settings file.

Multi-pass is used in replaces and cannot be paired with override actions (it will be ignored), but it can be paired with `find_only` as `find_only` allows you to initiate a replace.

```js
    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["example"], "multi_pass": true}
    },
```

## Replace Only Under Selection(s)
Sometimes you only want to search under selections.  This can be done by enabling the `selection_only` setting in the settings file.  By enabling this setting, regular expression targets will be limited to the current selection if and only if a selection exists.  Auto replace/highlight on save events ignore this setting.  If you have a command that you wish to ignore this setting, just set the `no_selection` argument to `true`.  Highlight style will be forced to underline selections if `find_only` is set to ensure they will show up.

```js
    // Ignore "selection_only" setting
    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["example"], "multi_pass": true, "no_selection": true}
    },
```

## Use Regular Expressions on Entire File Buffer when Using Selections
When `selection_only` is enabled, you might have a regular expression chain that lends itself better to performing the regular expression on the entire file buffer and then pick the matches under the selections as opposed to the default behavior of applying the regular expression directly to the selection buffer.  To do this, you can use the option `regex_full_file_with_selections`.

```js
    {
        "caption": "Remove: All Comments",
        "command": "reg_replace",
        "args": {
            "replacements": [
                "remove_comments", "remove_trailing_spaces",
                "remove_excessive_newlines", "ensure_newline_at_file_end"
            ],
            "find_only": true,
            "regex_full_file_with_selections": true
        }
    },
```

## Apply Regular Expressions Right Before File Save Event
If you want to automatically apply a sequence right before a file saves, you can define sequences in the `reg_replace.sublime-settings` file.  Each "on save" sequence will be applied to the files you specify by file patterns or file regular expression.  Also, you must have `on_save` set to `true`.  You can also just highlight, fold, or unfold by regular expression by adding the `"action": "mark"` key/value pair (supported options are `mark`, `fold`, and `unfold`). Both types can be used at the same time. Actions are performed after replacements.


Example:

```js
    // If on_save is true, RegReplace will search through the file patterns listed below right before a file is saved,
    // if the file name matches a file pattern, the sequence will be applied before the file is saved.
    // RegReplace will apply all sequences that apply to a given file in the order they appear below.
    "on_save": true,

    // Highlight visual settings
    "on_save_highlight_scope": "invalid",
    "on_save_highlight_style": "outline",

    "on_save_sequences": [
        // An example on_save event that removes dangling commas from json files
        // - file_regex: an array of regex strings that must match the file for the sequence to be applied
        // - case: regex case sensitivity (true|false) false is default (this setting is optional)
        //   See https://docs.python.org/3.4/library/re.html for more information on Python's re.
        // - file_pattern: an array of file patterns that must match for the sequence to be applied
        // - sequence: an array of replacement definitions to be applied on saving the file
        // - multi_pass: perform multiple passes on file to catch all regex instances
        {
            "file_regex": ["(?i).*\\.sublime-(settings|commands|menu|keymap|mousemap|theme|build|project|completions|commands)"],
            "file_pattern": ["*.json"],
            "sequence": ["remove_json_dangling_commas"]
        },
        // An example on_save_sequence that targets all files and highlights trailing spaces
        // - file_pattern: an array of file patterns that must match for the sequence to be applied
        // - sequence: an array of replacement definitions to be applied on saving the file
        // - action: (mark|fold|unfold) instead of replace
        {
            "file_pattern": ["*"],
            "sequence": ["remove_trailing_spaces"],
            "action": "mark"
        }
    ],
```

## Custom Replace Plugins
There are times that a simple regular expression and replace is not enough.  Since RegReplace uses Python's re regular expression engine, we can use python code to intercept the replace and do more complex things via a plugin.  Because this uses Python's re, this will only be applied when doing regular expression searches (not literal searches).

In this example we are going to search for dates with the form YYYYMMDD and increment them by one day.

Below is the regular expression rule; notice we have defined a plugin to replace.  Plugins are defined as if you were importing a module in python.  So in this example, we are loading it from the `User` package. You do not need an `__init__.py` file in `rr_modules` folder; it is recommended to not use one as Sublime shouldn't bother loading these files as RegReplace will load them when needed.

```js
"date_up": {
    "find": "(?P<year>\\d{4})(?P<month>\\d{2})(?P<day>\\d{2})",
    "plugin": "User.rr_modules.date_up"
    // "args": {"some_plugin_arguments": "if_desired"}  <== optional plugin arguments
}
```

Next we can define the command that will utilize the regex rule:

```js
    {
        "caption": "Replace: Date Up",
        "command": "reg_replace",
        "args": {"replacements": ["date_up"], "find_only": true}
    },
```

Lastly, we can provide the plugin.  RegReplace will load the plugin and look for a function called `replace`.  `replace` takes a python re match object, and any arguments you want to feed it.  Arguments are defined in the regular expression rule as shown above.

```python
SHORT_MONTH = 30
LONG_MONTH = 31
FEB_MONTH = 28
FEB_LEAP_MONTH = 29

JAN = 1
FEB = 2
MAR = 3
APR = 4
MAY = 5
JUN = 6
JUL = 7
AUG = 8
SEP = 9
OCT = 10
NOV = 11
DEC = 12


def is_leap_year(year):
    return ((year % 4 == 0) and (year % 100 != 0)) or (year % 400 == 0)


def days_in_months(month, year):
    days = LONG_MONTH
    if month == FEB:
        days = FEB_LEAP_MONTH if is_leap_year(year) else FEB_MONTH
    elif month in [SEP, APR, JUN, NOV]:
        days = SHORT_MONTH
    return days


def increment_by_day(day, month, year):
    mdays = days_in_months(month, year)
    if day == mdays:
        day = 1
        if month == DEC:
            month = JAN
            year += 1
        else:
            month += 1
    else:
        day += 1

    return day, month, year


def replace(m):
    g = m.groupdict()
    year = int(g["year"].lstrip("0"))
    month = int(g["month"].lstrip("0"))
    day = int(g["day"].lstrip("0"))

    day, month, year = increment_by_day(day, month, year)

    return "%04d%02d%02d" % (year, month, day)
```

Here is some text to test the example on:

```
# Test 1: 20140228
# Test 2: 20141231
# Test 3: 20140101
```

RegReplace comes with a very simple example you can test with found at `/Packages/RegReplace/rr_modules/example.py`.  Imported with `RegReplace.rr_modules.example`.

## Regex Module

By default, RegReplace uses Python's [re][re] module.  But if you prefer the  
more advanced [regex][regex] regular expression module, you can enable it with the  
following setting:

```js
    // Use the regex module for regular expression.
    // https://pypi.python.org/pypi/regex
    "use_regex_module": true,
```

To select whether to use Version 0 or Version 1 of the regex module, simply change the following setting:

```js
    // When "use_regex_module" is enabled, select which version of the regex module to use (0 or 1).
    // See documentation to understand the differences: https://pypi.python.org/pypi/regex.
    "regex_module_version": 0,
```

## Extended Back References
RegReplace uses a special wrapper around Python's re library called backrefs.  Backrefs was written specifically for RegReplace and adds various additional backrefs that are known to some regular expression engines, but not to Python's re.  Backrefs adds: `\p`, `\P`, `\u`, `\U`, `\l`, `\L`, `\Q` or `\E` (though `\u` and `\U` are replaced with `\c` and `\C`).  It even  
adds some of the Posix style classes such as `[:ascii:]` etc.

Backrefs also works with the regex module, but it enables a smaller portion of back references as the regex module implements a few of the back references already (in one form or the other).  For instance, there was no need to add  
Unicode properties as it was already available. And since you can already use Unicode and/or Posix properties to do  
uppercase and lowercase character classes in search patterns, and regex already reserves `\L`, it wasn't worth the  
extra work to try and add equivalents for `\c`, `\C`, '\l' and `\L` to the search back references.

You can enable extended back references in the settings file:

```js
    // Use extended back references
    "extended_back_references": true
```

When enabled, you can apply the back references to your search and/or replace patterns as you would other back references:

```js
    "test_case": {
        "find": "([a-z])(?P<somegroup>[a-z]*)((?:_[a-z]+)+)",
        "replace": "\\c\\1\\L\\g<somegroup>\\E\\C\\g<3>\\E",
        "greedy": true
    }
```

You can read more about the backrefs' features in the [backrefs documentation][backrefs].

### Getting the Latest Backrefs
It is not always clear when Package Control updates dependencies.  So to force dependency updates, you can run Package Control's `Satisfy Dependencies` command which will update to the latest release.

### Using Backrefs in RegReplace Plugin
You can import backrefs into a RegReplace plugin:

```python
from backrefs as bre
```

Or use bregex for the regex module with backrefs:

```python
from backrefs as bregex
```

Backrefs does provide a wrapper for all of re's normal functions such as `match`, `sub`, etc., but is recommended to pre-compile your search patterns **and** your replace patterns for the best performance; especially if you plan on reusing the same pattern multiple times.  As re does cache a certain amount of the non-compiled calls you will be spared from some of the performance hit, but backrefs does not cache the pre-processing of search and replace patterns.

To use pre-compiled functions, you compile the search pattern with `compile_search`.  If you want to take advantage of replace backrefs, you need to compile the replace pattern as well.  Notice the compiled pattern is fed into the replace pattern; you can feed the replace compiler the string representation of the search pattern as well, but the compiled pattern will be faster and is the recommended way.

```python
pattern = bre.compile_search(r'somepattern', flags)
replace = bre.compile_replace(pattern, r'\1 some replace pattern')
```

Then you can use the complied search pattern and replace

```python
text = pattern.sub(replace, r'sometext')
```

or

```python
m = pattern.match(r'sometext')
if m:
    text = replace(m)  # similar to m.expand(template)
```

To use the non-compiled search/replace functions, you call them just them as you would in re; the names are the same.  Methods like `sub` and `subn` will compile the replace pattern on the fly if given a string.

```python
for m in bre.finditer(r'somepattern', 'some text', bre.UNICODE | bre.DOTALL):
    # do something
```

If you want to replace without compiling, you can use the `expand` method.

```python
m = bre.match(r'sometext')
if m:
    text = bre.expand(m, r'replace pattern')
```
