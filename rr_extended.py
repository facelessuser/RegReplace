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
        """
        Return the unmodified template before expansion.
        """

        return self.__original

    def __escape_template(self, template):
        """
        Because the new backreferences are recognized by python
        we need to escape them so they come out okay.
        """

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
        """
        Add new backreferences, but not if they
        interfere with existing ones.
        """

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
        self.max_index = len(string) - 1
        self.index = 0
        self.current = None

    def __iter__(self):
        return self

    def next(self):
        """
        Iterate through characters of the string.
        Count \l, \L, \c, \C and \\ as a single char.
        """

        if self.index > self.max_index:
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


class BackReferencs(object):
    def __init__(self, match, template):
        self.template = template
        self.upper = False
        self.lower = False
        self.span = False
        self._expand_string(match)

    def next_group_boundary(self, index):
        """
        Return the next match group boundaries
        in relation to the index.  Return 'None'
        if there are no more boundaries.
        """

        bound = None
        for b in self.group_boundaries:
            if index < b[1]:
                bound = b
                break
        return bound

    def ignore_index(self, boundary, index):
        """
        If the index falls within the current group boundary,
        return that it should be ignored.
        """

        return boundary is not None and index >= boundary[0] and index < boundary[1]

    def out_of_boundary(self, boundary, index):
        """
        Return if the index has exceeded the right boundary.
        """

        return boundary is not None and index >= boundary[1]

    def span_upper(self, i):
        """
        Uppercase the next range of characters until end marker is found.
        Ignore \E if found in a group bondary.
        """

        try:
            boundary = self.next_group_boundary(i.index)
            index = i.index
            char = next(i)
            while char != "\\E" or self.ignore_index(boundary, index):
                self.result.append(char.upper())
                char = next(i)
                index = i.index
                if self.out_of_boundary(boundary, index):
                    boundary = self.next_group_boundary(i.index)
        except StopIteration:
            pass

    def span_lower(self, i):
        """
        Lowercase the next range of characters until end marker is found.
        Ignore \E if found in a group bondary.
        """

        try:
            boundary = self.next_group_boundary(i.index)
            index = i.index
            char = next(i)
            while char != "\\E" or self.ignore_index(boundary, index):
                self.result.append(char.lower())
                char = next(i)
                index = i.index
                if self.out_of_boundary(boundary, index):
                    boundary = self.next_group_boundary(i.index)
        except StopIteration:
            pass

    def single_lower(self, i):
        """
        Lowercase the next character.
        If none found, allow spanning to the next group.
        """

        try:
            t = next(i)
            if len(t) > 1:
                # Excaped char; just append.
                self.result.append(t)
            else:
                self.result.append(t.lower())
        except StopIteration:
            pass

    def single_upper(self, i):
        """
        Uppercase the next character.
        If none found, allow spanning to the next group.
        """

        try:
            t = next(i)
            if len(t) > 1:
                # Excaped char; just append.
                self.result.append(t)
            else:
                self.result.append(t.upper())
        except StopIteration:
            pass

    def _expand_string(self, match):
        """
        Using the template, expand the string.
        Keep track of the match group bondaries for later.
        """

        self.sep = match.string[:0]
        self.text = []
        self.result = []
        self.group_boundaries = []
        # Expand string
        char_index = 0
        for x in range(0, len(self.template.literals)):
            index = x
            l = self.template.literals[x]
            if l is None:
                g_index = self.template.get_group_index(index)
                l = match.group(g_index)
                start = char_index
                char_index += len(l)
                self.group_boundaries.append((start, char_index))
                self.text.append(l)
            else:
                start = char_index
                char_index += len(l)
                self.text.append(l)

    def expand_titles(self):
        """
        Walk the expanded template string and process
        the new added backreferences and apply the associated
        action.
        """

        # Handle backreferences
        i = Tokens(self.sep.join(self.text))
        for t in i:
            if t is None:
                break

            # Backreference has been found
            # This is for the neutral state
            # (currently applying no title cases)
            if len(t) > 1:
                c = t[1]
                if c == "\\":
                    self.result.append(t)
                elif c == "E":
                    self.result.append(t)
                elif c == "l":
                    self.single_lower(i)
                elif c == "L":
                    self.span_lower(i)
                elif c == "c":
                    self.single_upper(i)
                elif c == "C":
                    self.span_upper(i)
            else:
                self.result.append(t)
        return self.sep.join(self.result)


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
        return BackReferencs(m, template).expand_titles()
    except:
        print(str(traceback.format_exc()))
        return m.expand(template.get_base_template())
