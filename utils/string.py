import re

def stringWithSpaceAroundsCase(string: str) -> list[str]:
    return [
        ' ' + string,
        string + ' ',
        ' ' + string + ' '
    ]

def generateKeyVariants(value: str) -> list[str]:
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", value).split()
    
    if len(words) == 1:
        word = words[0]
        return [
            word.lower(),
            word.capitalize(),
            word.upper()
        ]

    return [
        "".join(words),
        "".join(words).lower(),
        "".join(words).upper(),
        " ".join(words),
        " ".join(w.capitalize() for w in words),
        " ".join(words).lower(),
        " ".join(words).upper(),
        "_".join(words),
        "_".join(w.capitalize() for w in words),
        "_".join(words).lower(),
        "_".join(words).upper(),
    ]