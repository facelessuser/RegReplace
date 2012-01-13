# About
Reg Replace is a plugin for Sublime Text 2 that allows the creating of commands consisting of sequences of find and replace instructions.

# Installation 
- You can download or clone directly and drop into your Sublime Text 2 packages directory (plugin folder must be named RegReplace)

# Usage
To use, replacements must be defined in the reg_replace.sublime-settings file.

    // Required parameters:
    //     find:    Regex description of what you would like to target.
    //     replace: description of what you would like to replace target with.
    //              Variables are okay and are done by escaping the selection number \\1 etc.
    // Optional parameters:
    //     greedy:       Boolean setting to define whether search is greedy or not. Default is true.
    //     case:         Boolean defining case sensitivity.  True equals sensitive. Defualt is true.
    //     scope_filter: an array of scope qualifiers for the match.
    //                       - Any instance of scope qualifies match: scope.name
    //                       - Entire match of scope qualifies match: !scope.name
    //                       - Any instance of scope disqualifies match: -scope.name
    //                       - Entire match of scope disqualifies match: -!scope.name
    {
        "replacements": {
            // Example replacements
            "html5_remove_deprecated_type_attr": {
                "find": "(<(style|script)[^>]*)\\stype=(\"|')text/(css|javascript)(\"|')([^>]*>)",
                "replace": "\\1\\6",
                "greedy": true,
                "case": false
            },

Once you have replacements defined, there are a number of ways you can run a sequence.  One way is to create a command in the command palette by editing/creating a Default.sublime-commands in your User folder and adding your command.  RegReplace comes with its own Default.sublime-commands file and includes some examples showing simple replacement commands and an example showing the chaining of multiple replacements.

    {
        "caption": "Reg Replace: Remove Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["remove_trailing_spaces"]}
    },
    // Chained replacements in one command
    {
        "caption": "Reg Replace: Remove HTML Comments and Trailing Spaces",
        "command": "reg_replace",
        "args": {"replacements": ["remove_html_comments", "remove_trailing_spaces"]}
    }

You can also bind a replacement command to a shortcut.

    {
        "keys": ["ctrl+shift+t"],
        "command": "reg_replace",
        "args": {"replacements": ["remove_trailing_spaces"]}
    }

If you haven't created a command yet, but you want to quickly run a sequence, you can search for ```Reg Replace: RegEx Input Sequencer``` in the command palette and launch an input panel where you can enter the name of replacements separated by commas and press enter.

# Source Code
https://github.com/facelessuser/RegReplace/zipball/master

# License

Reg Replace is released under the MIT license.

Copyright (c) 2011 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#Version 0.2
- "greedy" and "case" parameters are now optional and set to "true" by default

#Version 0.1
- Initial release
