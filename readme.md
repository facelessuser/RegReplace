# About
Reg Replace is a plugin for Sublime Text 2 that allows the creating of commands consisting of sequences of find and replace instructions.

# Installation
- Use Package Control to install
- Or you can download or clone directly and drop into your Sublime Text 2 packages directory (plugin folder must be named RegReplace)

# Usage
## Create Find and Replace Sequences
To use, replacements must be defined in the reg_replace.sublime-settings file.

There are two kinds of definitions.  The first uses regex to find regions, and then you can use scopes to qualify the regions before applying the replace.

```
    // Required parameters:
    //     find:    Regex description of what you would like to target.
    //
    // Optional parameters:
    //     replace:      description of what you would like to replace target with.
    //                   Variables are okay for non-literal searches and are done by escaping
    //                   the selection number \\1 etc.  Default value is "" (empty string)
    //     literal:      Boolean setting to define whether the find and replace is literal or not.
    //                   Default is false.
    //     greedy:       Boolean setting to define whether search is greedy or not. Default is true.
    //     case:         Boolean defining case sensitivity.  True equals sensitive. Defualt is true.
    //     dotall:       Boolean defining whether to use dotall flag in regex (include \n etc. when using dot).
    //                   Default is False
    //     scope_filter: an array of scope qualifiers for the match.
    //                       - Any instance of scope qualifies match: scope.name
    //                       - Entire match of scope qualifies match: !scope.name
    //                       - Any instance of scope disqualifies match: -scope.name
    //                       - Entire match of scope disqualifies match: -!scope.name
```

```javascript
    {
        "replacements": {
            "html5_remove_deprecated_type_attr": {
                "find": "(<(style|script)[^>]*)\\stype=(\"|')text/(css|javascript)(\"|')([^>]*>)",
                "replace": "\\1\\6",
                "greedy": true,
                "case": false
            },
```

The second kind of definition allows you to search for a scope type and then apply regex to the regions to filter the matches and make replaces.

```
    // Required parameters:
    //     scope:    scope you would like to target
    //
    // Optional parameters:
    //     find:            regex description that is to be applied to the scope
    //                      to qualify.  Also can be used to find and replace
    //                      within the found scope.  Default is None.
    //     replace:         description of what you would like to replace within the scope.
    //                      Default value is "\\0".
    //     literal:         Boolean setting to define whether the find and replace is literal or not.
    //                      Default is false.
    //     greedy_replace:  Boolean setting to define whether regex search is greedy or not. Default is true.
    //     greedy_scope:    Boolean setting to define whether scope search is greedy or not. Default is true.
    //     case:            Boolean setting to define whether regex search is case sensitive. Default is true.
    //     dotall:          Boolean defining whether to use dotall flag in regex (include \n etc. when using dot).
    //                      Default is False
    //     multi_pass_regex:Boolean setting to define whether there will be multiple sweeps on the scope region
    //                      region to find and replace all instances of the regex, when regex cannot be formatted
    //                      to find all instances in a greedy fashion.  Default is false.
```

```javascript
    {
            "replacements": {
                "remove_comments": {
                    "scope": "comment",
                    "find" : "(([^\\n\\r]*)(\\r\\n|\\n))*([^\\n\\r]+)",
                    "replace": "",
                    "greedy_replace": true
                }
```

Once you have replacements defined, there are a number of ways you can run a sequence.  One way is to create a command in the command palette by editing/creating a Default.sublime-commands in your User folder and adding your command.  RegReplace comes with its own Default.sublime-commands file and includes some examples showing simple replacement commands and an example showing the chaining of multiple replacements.

```javascript
    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["remove_trailing_spaces"]}
    },
```

Chained replacements in one command

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

## View Without Replacing
If you would simply like to view what the sequence would find without replacing, you can construct a command to highlight targets without replacing them (each pass could affect the end result, but this just shows all passes without predicting replaces).

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
If instead of replacing you would like to do something else, you can override the action. Actions are defined in commands by setting the ```action``` parameter.  Some actions may require additional parameters be set in the ```options``` parameter.  See examples below.

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

### Fold Override
action = fold

This action folds the given find target.  This action has no parameters.

### Unfold Override
action = unfold

This action unfolds the all regions that match the given find target.  This action has no parameters

### Mark Override
action = mark

This action highlights the regions of the given find target.

####Required Parameters:
- key = unique name for highlighted regions

####Optional Parameters:
- scope = scope name to use as the color. Default is ```invalid```
- style = highlight style (solid|underline|outline). Default is ```outline```.

### Unmark Override
action = unmark

This action removes the highlights of a given ```key```.  Replacements can be ommitted with this command.

####Required Parameters:
- key = unique name of highlighted regions to clear

## Multi-Pass
Sometimes a regular expression cannot be made to find all instances in one pass.  In this case, you can use the multi-pass option.

Multi-pass cannot be paired with override actions (it will be ignored), but it can be paired with ```find_only```.  Multi-pass will sweep the file repeatedly until all instances are found and replaced.  To protect against poorly constructed mult-pass regex looping forever, there is a default max sweep threshold that will cause the sequence to kick out if it is reached.  This threshold can be tweaked in the settings file.

```javascript
    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["example"], "multi_pass": true}
    },
```

## Replace Only Under Selection(s)
Sometimes you only want to search under selections.  This can be done by enabling the ```selection_only``` setting in the settings file.  By enabling this setting, regex targets will be limited to the current selection if and only if a selection exists.  Auto replace/highlight on save events ignore this setting.  If you have a command that you wish to ignore this setting, just set the ```no_selection``` argument to ```true```.  Highlight style will be forced to underline under selections if ```find_only``` is set to ensure they will show up.

```javascript
    // Ignore "selection_only" setting
    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["example"], "multi_pass": true, "no_selection": true}
    },
```

## Use Regex on Entire File Buffer when Using Selections
Sometimes you might have a regex chain that lends itself better to performing the regex on the entire file buffer and then pick the matches under the selections opposed the default behaviour of applying the regex directly to the selection buffer.  To do this, you can use the option ```regex_full_file_with_selections```.

```javascript
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

## Apply Regex Right Before File Save Event
If you want to automatically apply a sequence right before a file saves, you can define sequences in the reg_replace.sublime-settings file.  Each "on save" sequence will be applied to the files you sepcify by file patterns or file regex.  Also, you must have ```on_save``` set to ```true```.  You can also just highlight, fold, or unfold by regex by adding the ```"action": "mark"``` key/value pair (options are mark, fold, and unfold). Both types can be used at the same time. Actions are performed after replacements.


Example:

```
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
        // - file_pattern: an array of file patterns that must match for the sequence to be applied
        // - sequence: an array of replacement definitions to be applied on saving the file
        // - multi_pass: perform multiple passes on file to catch all regex instances
        {
            "file_regex": [".*\\.sublime-(settings|commands|menu|keymap|mousemap|theme|build|project|completions|commands)"],
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

# Source Code
https://github.com/facelessuser/RegReplace/zipball/master

# License

Reg Replace is released under the MIT license.

Copyright (c) 2011 - 2012 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
