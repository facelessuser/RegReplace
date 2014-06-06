import sre_parse
import traceback

CAP_TOKEN = set("lLcCE")
DEF_BACK_REF = set("abfnrtvAbBdDsSwWZuxg")


class ReplaceTemplate(object):
    def __init__(self, pattern, template):
        self.__original = template
        self.__back_ref = set()
        self.__add_back_references(CAP_TOKEN)
        self.__template = self.__escape_template(template)
        self.groups, self.literals = sre_parse.parse_template(self.__template, pattern)

    def get_base_template(self):
        return self.__original

    def __escape_template(self, template):
        new_template = []
        slash_count = 0
        for c in template:
            if c == "\\":
                slash_count += 1
            elif c in self.__back_ref:
                if slash_count != 0 and (slash_count % 2) == 0:
                    new_template.append("\\")
                slash_count = 0
            else:
                slash_count = 0
            new_template.append(c)
        return "".join(new_template)

    def __add_back_references(self, args):
        for arg in args:
            if isinstance(arg, str) and len(arg) == 1:
                if arg not in DEF_BACK_REF and arg not in self.__back_ref:
                    self.__back_ref.add(arg)

    def get_group_index(self, index):
        """
        Find and return the appropriate group index
        """

        g_index = None
        for group in self.groups:
            if group[0] == index:
                g_index = group[1]
                break
        return g_index


class Tokens(object):
    def __init__(self, string):
        self.string = string
        self.last = len(string) - 1
        self.index = 0
        self.current = None

    def __iter__(self):
        return self

    def __next__(self):
        """
        Iterate through characters of the string.
        Count \l, \L, \c, \C and \\ as a single char.
        """

        if self.index > self.last:
            raise StopIteration

        char = self.string[self.index]
        if char == "\\":
            try:
                c = self.string[self.index + 1]
                if c in CAP_TOKEN:
                    char += c
                elif c == "\\":
                    try:
                        ref = self.string[self.index + 2]
                        if ref in CAP_TOKEN:
                            self.index += 1
                        else:
                            char += c
                    except:
                        char += c
                        pass
            except:
                pass

        self.index += len(char)
        self.current = char
        return self.current


class TitleCase(object):
    def __init__(self, match, template):
        self.template = template
        self.upper = False
        self.lower = False
        self.span = False
        self.match = match
        self.text = []

    def group_entry(self):
        """
        Insert the correct group into the next slot.
        If we are currently adjusting case, make the appropriate,
        alteration for the group.  Allow adjustments to span past
        the current group if needed.
        """

        g_index = self.template.get_group_index(self.index)
        if g_index is not None:
            if self.upper:
                # Upper case adjustment
                if self.span:
                    # Span
                    self.text.append(self.match.group(g_index).upper())
                else:
                    # Single char
                    g_str = self.match.group(g_index)
                    if len(g_str):
                        # No character to adjust
                        self.text.append(g_str[0].upper() + g_str[1:])
                        self.upper = False
            elif self.lower:
                # Lower case adjustment
                if self.span:
                    # Single char
                    self.text.append(self.match.group(g_index).lower())
                else:
                    g_str = self.match.group(g_index)
                    if len(g_str):
                        # No character to adjust
                        self.text.append(g_str[0].lower() + g_str[1:])
                        self.lower = False
            else:
                # Copy the entire group
                self.text.append(self.match.group(g_index))

    def span_upper(self, i, new_entry, c=None):
        """
        Uppercase the next range of characters until end marker is found.
        Allow spanning past the current group if needed.
        """

        try:
            if c is None:
                c = next(i)
            while c != "\\E":
                new_entry.append(c.upper())
                c = next(i)
            self.upper = False
            self.span = False
        except StopIteration:
            self.upper = True
            self.span = True

    def span_lower(self, i, new_entry, c=None):
        """
        Lowercase the next range of characters until end marker is found.
        Allow spanning past the current group if needed.
        """

        try:
            if c is None:
                c = next(i)
            while c != "\\E":
                new_entry.append(c.lower())
                c = next(i)
            self.lower = False
            self.span = False
        except StopIteration:
            self.lower = True
            self.span = True

    def single_lower(self, i, new_entry):
        """
        Lowercase the next character.
        If none found, allow spanning to the next group.
        """

        try:
            t = next(i)
            if len(t) > 1:
                new_entry.append(t)
            else:
                new_entry.append(t.lower())
            self.lower = False
        except StopIteration:
            self.lower = True

    def single_upper(self, i, new_entry):
        """
        Lowercase the next character.
        If none found, allow spanning to the next group.
        """

        try:
            t = next(i)
            if len(t) > 1:
                new_entry.append(t)
            else:
                new_entry.append(t.upper())
            self.upper = False
        except StopIteration:
            self.upper = True

    def string_entry(self, entry):
        """
        Parse the string entry and find title case backreferences.
        Make necessary adjustments if needed.
        """

        new_entry = []
        i = Tokens(entry)
        for t in i:
            if t is None:
                break
            if len(t) > 1 and not self.upper and not self.lower:
                # Backreference has been found
                # This is for the neutral state
                # (currently applying no title cases)
                c = t[1]
                if c == "\\":
                    new_entry.append(t)
                elif c == "E":
                    new_entry.append(t)
                elif c == "l":
                    self.single_lower(i, new_entry)
                elif c == "L":
                    self.span_lower(i, new_entry)
                elif c == "c":
                    self.single_upper(i, new_entry)
                elif c == "C":
                    self.span_upper(i, new_entry)
            else:
                # This is for normal characters or when in
                # the active state (currently applying title case)
                if self.upper:
                    if self.span:
                        self.span_upper(i, new_entry, t)
                    else:
                        self.single_upper(i, new_entry)
                elif self.lower:
                    if self.span:
                        self.span_lower(i, new_entry, t)
                    else:
                        self.single_lower(i, new_entry)
                else:
                    new_entry.append(t)

            # Add the newly formatted string
            if len(new_entry):
                self.text.append("".join(new_entry))
                new_entry = []

    def expand_titles(self):
        """
        Parse the template and construct the expanded
        string with appropriate title cases.
        """

        for x in range(0, len(self.template.literals)):
            self.index = x
            entry = self.template.literals[x]
            if entry is None:
                # Empty slot, find the group that
                # should fill this spot
                self.group_entry()
            else:
                # Parse the literal string
                # and search for upper and lower
                # case backreferences.
                # Apply title case if needed.
                self.string_entry(entry)
        return "".join(self.text)


def replace(m, template):
    """
    Replace event.  Using the template, scan for (\c | \C.*?\E | \l | \L.*?\E).
    (c|C) are capital/upper case. (l|L) is lower case.
    \c and \l are applied to the next character.  While \C and \L are applied to
    all characters until either the end of the string is found, or the end marker \E
    is found.  Actual group content is not scanned for markers.
    """

    assert isinstance(template, ReplaceTemplate), "Not a valid template!"

    try:
        return TitleCase(m, template).expand_titles()
    except:
        print(str(traceback.format_exc()))
        return sre_parse.expand_template(template.get_base_template(), m)
