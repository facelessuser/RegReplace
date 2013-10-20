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

####Input Sequencer order:
- ```mark=key,scope,style:replacements```

### Unmark Override
action = unmark

This action removes the highlights of a given ```key```.  Replacements can be ommitted with this command.

####Required Parameters:
- key = unique name of highlighted regions to clear

####Input Sequencer order:
- ```unmark=key:``` (replacements do not need to be defined)

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

## Regex Input Sequencer
If you haven't created a command yet, but you want to quickly run a sequence, you can search for ```Reg Replace: RegEx Input Sequencer``` in the command palette and launch an input panel where you can enter the name of replacements separated by commas and press enter.

If you only want to highlight the searches and not replace them, precede the sequence with ```?:```.  This will highlight the regions it can find to give you an idea of what regions will be targeted.  Afterwards, a panel will pop up allowing you to replace if you choose.

Also you can override the replace action with other actions like "fold" or "unfold" were the action precedes the sequence ```fold:```.  If you would like to highlight the selections only and then optionally perform the replace/action, you can precede the sequence like this ```?fold:```.

Some actions might have parameters.  In this case, you can follow the actions with an equal sign and the paramters separated by commas. ```mark=key,string,outline:```.  If some parameters are optional, you can leave them out: ```?mark=key,string``` or ```?mark=key,,outline:```.  The important thing is that the parameters are in the order outlined by the command.

If multiple sweeps are needed to find and replace all targets, you can use multi-pass using ```+:```. Multi-pass cannot be used with action overrides, but it can be used with highlighting searches ```?+:```.

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

# Version 1.7.0
- Add fold and unfold options for on_save
- Remove "highlgight": true option in favor of "action": "mark"  (also can use "fold" and "unfold")
- Allow each selection to be treated as its own buffer when applying regex
- Add option "regex_full_file_with_selections" to regex entire file and then pick matches from selection when using selections

# Version 1.6.1
- Auto highlight on save now uses same region label as find_only so it can be cleaned with the clean command and gets clean up with it

# Version 1.6
- Save under selection added (limits searches to selections if and only if selection exists)
- Cleanup "highlight on save regions" when performing other regex searches

# Version 1.5.2
- Do each on save replace sequence separate allowing multi_pass to be only applied to specific sequence.
- Add per on save sequence multi_pass key/value pair option

# Version 1.5.1
- Fix some small issues with highlight on save
- Merge highlight on save sequences and on save replacements under same object.  Specify highlight with the highlight key.

# Version 1.5
- Allow for highlighting on save
- Allow on save replacements to use multi_pass

# Version 1.4.2
- Fix regression with multi-pass

# Version 1.4.1
- With latest official beta, multiple unfold methods are no longer needed. Remove legacy methods and require latest official build.

# Version 1.4
- Allow on save regex sequences to define target files with regex as well as unix file name pattern matching
- Add example "remove_dangling_commas" replacement definition
- Add example on_save sequence using file regex pattern to remove dangling commas from sublime json files

# Version 1.3
- Add the ability to apply regex sequences right before a file save event.  Files are targeted with user defined file patterns

# Version 1.2.1
- Account for people still on the last offical beta since view.folded_regions() is not included in that release.  This method of unfold will be deprecated on new ST2 offical beta release.

# Version 1.2
- Added support for new API command view.unfold([regions]); old method is a fallback for official beta and will be deprecated on new ST2 official beta release

# Version 1.1
- Faster unfold when many regions to unfold

# Version 1.0
- Add "literal" param for scope search defines.
- Reduce code complexity

# Version 0.9
- Allow multipass on a scope region with regex with new "multi_pass_regex" parameter

# Version 0.8
- New "mark" and "unmark" actions
- Return error dialog showing regex issue
- Add support for scope search with regex find and replace in scope region
- Smarter folding of regex regions for "fold" action
- Small tweak to non-greedy algorithm
- Change default of optional replace parameter to "\\\\0"; do not delete by default, leave unchanged by default.
- Allow spaces in the "Regex Input Sequencer"

# Version 0.7
- Replace command examples now commented out by default
- RegReplace Commands and Settings now available via preference menu and command palette

# Version 0.6
- Add multi-pass sweeps
- Report bad actions

# Version 0.5
- Make replace an optional parameter defaulted to "" (empty string)
- Allow override actions to be used instead of replace: fold and unfold

# Version 0.4
- Add support for "literal" boolean parameter for literal find and replaces
- Allow the Regex Input Sequencer panel to highlight only by preceding the sequence with "?:"

# Version 0.3
- Allow option for highlighting find targets without replacing. Show prompt for replacing after highlighting.
- Add clear command to allow clearing of all highlights if for any reason view loses focus and highlights aren't cleared on cancel.

# Version 0.2
- "greedy" and "case" parameters are now optional and set to "true" by default

# Version 0.1
- Initial release
