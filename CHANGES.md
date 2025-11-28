# RegReplace

## 3.9.0

-   **NEW**: Changes to support Python 3.13 on ST 4201+.

## 3.8.4

-   **FIX**: Fix support commands.

## 3.8.3

-   **FIX**: Ensure `typing` dependency for Python 3.3 host.

## 3.8.2

-   **FIX**: Fix bad links.

## 3.8.1

-   **NEW**: Update internal references to`backrefs` to prevent breakage with new version.

## 3.8.0

-   **NEW**: Add support for `regex` module's `REVERSE` flag.

## 3.7.2

-   **FIX**: Internal changes to support new backrefs 3.0.3.
-   **FIX**: Issue related to freezing due to changing tab to space setting on every region replace.  Now do it once for whole operation.

## 3.7.1

-   **FIX**: Internal changes to support new backrefs.

## 3.7.0

-   **NEW**: New experimental support for selection inputs for find patterns (#71).

## 3.6.0

-   **NEW**: Add support for optional format style replace templates. Learn more
    [here](https://facelessuser.github.io/backrefs/usage/#format-replacements).
-   **FIX**: Properly set default replace to group 0 by using `\g<0>` not `\0`.
-   **FIX**: Explain better some basic syntax differences between Re, Regex, and Backrefs with Re and Regex.

## 3.5.0

-   **NEW**: Document and quick start commands added to command palette.
-   **NEW**: Renamed some existing settings commands in the command palette and removed unnecessary commands.

## 3.4.0

-   **NEW**: Scope searches will now apply highlights and actions directly to the regex find regions opposed to the
    whole scope (#58).
-   **NEW**: Use new Sublime settings API for opening settings file.
-   **NEW**: Show error message when rule not found (#60).

## 3.3.0

-   **NEW**: Limit popups/phantoms to 3124+.
-   **NEW**: Use latest settings API when viewing settings.

## 3.2.1

-   **FIX**: Fix issue where scope search pattern could fail due to recompiling a compiled pattern.

## 3.2.0

-   **NEW**: Add support for regex regular expression module (!52).

## 3.1.0

-   **NEW**: Support Info and Changelog commands

## 3.0.1

-   **FIX**: Set test flag when running test command
-   **FIX**: Remove debug statement

## 3.0.0

-   **NEW**: Users can now edit regex (and other settings) in a python syntax  
    highlighted panel. You can even do multi-line regex with comments using Python  
    re's `(?x)` flag. All this will be converted properly into the JSON setting.  
    This makes it easier to edit regex as editing regex in JSON is cumbersome.  
    New command palette commands have been added to edit, add, or delete regex,  
    but you can still edit it in the traditional way. You can also run tests from  
    the the new regex edit panel. Read [documentation](http://facelessuser.github.io/RegReplace/usage/#a-better-way-to-create-regex-rules)
    to learn more.

-   **NEW**: Replacement rules have been changed slightly and have been moved  
    to a separate file: reg_replace_rules.sublime-settings. This is to allows  
    RegReplace to update the rules with out destroying all the comments in a  
    User's settings. A command found in  
    `Preferences`->`Package Settings`->`RegReplace`->`Convert` Rules to 3.0 will  
    convert existing rules to the new format and copy them to the new location.

-   **NEW**: on_save_sequences's option dotall has been deprecated (this option  
    specifically affected the file_regex option). This shouldn't affect anyone as  
    there is no reason to use dotall in a file pattern, but if this is needed,  
    you can (?s) to the regex. Legacy support still works but will be removed in  
    the next non-bugfix release.

-   **FIX**: Literal search and replace was still running replace through re,  
    now it is a real literal replace.
