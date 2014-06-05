import re

CAPS_REFS = r"""
(?P<escape>(?<!\\)(?:(?:[\\]{2})*)\\)          # Make sure the escape char isn't escaped
(?:
    u (?P<upper_case>.)                      | # upercase character
    U (?P<upper_case_range>.*?)(?P=escape)E  | # uppercase range
    l (?P<lower_case>.)                      | # lowercase character
    L (?P<lower_case_range>.*?)(?P=escape)E    # lowercase range
)
"""

CAPS_REF_SEARCH = re.compile(CAPS_REFS, re.MULTILINE | re.VERBOSE)


def repl(m):
    text = ""
    if m.group("lower_case"):
        text = m.group("lower_case").lower()
    elif m.group("lower_case_range"):
        text = m.group("lower_case_range").lower()
    elif m.group("upper_case"):
        text = m.group("upper_case").upper()
    elif m.group("upper_case_range"):
        text = m.group("upper_case_range").upper()
    else:
        # This shouldn't ever happen
        print('Expansion identification failed!')
    return text


def run(text):
    text = CAPS_REF_SEARCH.sub(repl, text)
    return text
