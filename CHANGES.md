# RegReplace 3.3.0

> Released May 27, 2017

- **NEW**: Limit popups/phantoms to 3124+.
- **NEW**: Use latest settings API when viewing settings.

# RegReplace 3.2.1

> Released Mar 5, 2017

- **FIX**: Fix issue where scope search pattern could fail due to recompiling a compiled pattern.

# RegReplace 3.2.0

> Released Dec 28, 2016

- **NEW**: Add support for regex regular expression module [#52](https://github.com/facelessuser/RegReplace/pull/52)

# RegReplace 3.1.0

> Released Nov 8, 2016

- **NEW**: Support Info and Changelog commands

# RegReplace 3.0.1

> Released Jun 17, 2016

- **FIX**: Set test flag when running test command
- **FIX**: Remove debug statement

# RegReplace 3.0.0

> Released Jun 16, 2016

- **NEW**: Users can now edit regex (and other settings) in a python syntax  
highlighted panel. You can even do multi-line regex with comments using Python  
re's `(?x)` flag. All this will be converted properly into the JSON setting.  
This makes it easier to edit regex as editing regex in JSON is cumbersome.  
New command palette commands have been added to edit, add, or delete regex,  
but you can still edit it in the traditional way. You can also run tests from  
the the new regex edit panel. Read [documentation](http://facelessuser.github.io/RegReplace/usage/#a-better-way-to-create-regex-rules) to learn more.

- **NEW**: Replacement rules have been changed slightly and have been moved  
to a separate file: reg_replace_rules.sublime-settings. This is to allows  
RegReplace to update the rules with out destroying all the comments in a  
User's settings. A command found in  
`Preferences`->`Package Settings`->`RegReplace`->`Convert` Rules to 3.0 will  
convert existing rules to the new format and copy them to the new location.

- **NEW**: on_save_sequences's option dotall has been deprecated (this option  
specifically affected the file_regex option). This shouldn't affect anyone as  
there is no reason to use dotall in a file pattern, but if this is needed,  
you can (?s) to the regex. Legacy support still works but will be removed in  
the next non-bugfix release.

- **FIX**: Literal search and replace was still running replace through re,  
now it is a real literal replace.
