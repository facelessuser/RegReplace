def replace(m, **kwargs):
    text = "Here are your groups: "
    for group in m.groups():
        if group is not None:
            text += "(%s)" % group
    return text
