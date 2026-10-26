
import regex

# Unicode script names, spelled as the `regex` module expects them.
JAPANESE_SCRIPTS: tuple[str, ...] = ('Hiragana', 'Katakana')
INDIAN_SCRIPTS: tuple[str, ...] = (
    'Devanagari',
    'Bengali',
    'Gurmukhi',
    'Gujarati',
    'Oriya',
    'Tamil',
    'Telugu',
    'Kannada',
    'Malayalam',
    'Ol_Chiki',
    'Meetei_Mayek',
)

# Letters minus the Latin, Common and Inherited scripts. Common and Inherited
# letters (for example mathematical alphanumeric symbols) belong to no particular
# script, so they must not make a string non-Latin. The set subtraction needs the
# regex.V1 flag.
_NON_LATIN_LETTER_PATTERN = (
    r'[\p{L}--\p{Script=Latin}--\p{Script=Common}--\p{Script=Inherited}]'
)

# Restricts script names to what a Unicode script name can contain, so that a name
# can never alter the structure of the pattern it is inserted in.
_SCRIPT_NAME_PATTERN = r'[A-Za-z0-9_ -]+'

def _scriptProperty(name: str) -> str:
    """Build the `regex` expression matching the characters of one Unicode script.

    Args:
        name: Name of the Unicode script.

    Returns:
        The property expression to insert in a character class.

    Raises:
        ValueError: If `name` is not a known Unicode script.
    """
    if not regex.fullmatch(_SCRIPT_NAME_PATTERN, name):
        raise ValueError(f'Unknown Unicode script: {name!r}.')

    expression = f'\\p{{Script={name}}}'
    try:
        regex.compile(expression)
    except regex.error as err:
        raise ValueError(f'Unknown Unicode script: {name!r}.') from err

    return expression


def containsScriptChar(s: str, *scripts: str) -> bool:
    """Check whether a string contains a character of at least one Unicode script.

    This is the building block of the `contains<Script>Char` helpers. Use it
    directly to test a script that has no dedicated helper. The script names are
    those of the `regex` module (the Unicode `Script` property, for example
    `'Cyrillic'` or `'Ol_Chiki'`) and are matched without regard to case.

    Args:
        s: String to scan.
        *scripts: Names of the Unicode scripts to look for. At least one is required.

    Returns:
        True if `s` contains at least one character of any of the given scripts,
        False otherwise.

    Raises:
        ValueError: If no script name is given, or if a name is not a known Unicode
            script.

    Example:
        >>> containsScriptChar('abc', 'Latin')
        True
        >>> containsScriptChar('abc', 'Greek', 'Cyrillic')
        False
    """
    if not scripts:
        raise ValueError('At least one script name is required.')

    pattern = '[' + ''.join(_scriptProperty(name) for name in scripts) + ']'
    return regex.search(pattern, s) is not None


def isNotLatin(s: str) -> bool:
    """Check whether a string contains a letter that is not written in Latin script.

    Only letters are considered. Digits (even those of another script, such as the
    Arabic-Indic digits), spaces, punctuation, symbols, emoji and combining marks
    are not letters, so they never make a string non-Latin: `'Hello, 123!'` is Latin
    and a string without any letter gives False. Letters of no particular script
    (for example mathematical alphanumeric symbols) are ignored as well. A string is
    flagged as soon as one letter of any other script is present, so mixed text such
    as Latin followed by Cyrillic gives True.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one letter that belongs to a script other
        than Latin, False otherwise (including for an empty string).
    """
    return regex.search(_NON_LATIN_LETTER_PATTERN, s, flags=regex.V1) is not None


def containsLatinChar(s: str) -> bool:
    """Check whether a string contains a Latin character.

    Covers the Latin script as a whole (basic letters, accented letters and the extended
    blocks), the script of English, French, Vietnamese and many other languages. Digits,
    spaces and punctuation belong to no script and never match.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Latin character, False otherwise.
    """
    return containsScriptChar(s, 'Latin')


def containsGreekChar(s: str) -> bool:
    """Check whether a string contains a Greek character.

    Covers modern (monotonic) and polytonic Greek letters.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Greek character, False otherwise.
    """
    return containsScriptChar(s, 'Greek')


def containsCyrillicChar(s: str) -> bool:
    """Check whether a string contains a Cyrillic character.

    Script of Russian, Ukrainian, Bulgarian, Serbian and many other languages.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Cyrillic character, False otherwise.
    """
    return containsScriptChar(s, 'Cyrillic')


def containsArmenianChar(s: str) -> bool:
    """Check whether a string contains an Armenian character.

    Script of the Armenian language.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Armenian character, False otherwise.
    """
    return containsScriptChar(s, 'Armenian')


def containsGeorgianChar(s: str) -> bool:
    """Check whether a string contains a Georgian character.

    Script of the Georgian language.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Georgian character, False otherwise.
    """
    return containsScriptChar(s, 'Georgian')


def containsHebrewChar(s: str) -> bool:
    """Check whether a string contains a Hebrew character.

    Script of Hebrew and Yiddish.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Hebrew character, False otherwise.
    """
    return containsScriptChar(s, 'Hebrew')


def containsArabicChar(s: str) -> bool:
    """Check whether a string contains an Arabic character.

    Script of Arabic, Persian, Urdu and many other languages. The Arabic-Indic digits
    match, but the Arabic comma belongs to no script and does not.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Arabic character, False otherwise.
    """
    return containsScriptChar(s, 'Arabic')


def containsIndianChar(s: str) -> bool:
    """Check whether a string contains an Indian-script character.

    Checks the main scripts of India: Devanagari (Hindi, Marathi, Sanskrit), Bengali,
    Gurmukhi (Punjabi), Gujarati, Oriya (Odia), Tamil, Telugu, Kannada, Malayalam,
    Ol Chiki (Santali) and Meetei Mayek (Meitei). Arabic (used for Urdu) is not
    included, see `containsArabicChar`. The danda punctuation marks belong to no
    script and do not match. Use `containsScriptChar` for any other script of the
    Indian subcontinent.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Indian-script character, False otherwise.
    """
    return containsScriptChar(s, *INDIAN_SCRIPTS)


def containsThaiChar(s: str) -> bool:
    """Check whether a string contains a Thai character.

    Script of the Thai language. The baht currency sign belongs to no script and does
    not match.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Thai character, False otherwise.
    """
    return containsScriptChar(s, 'Thai')


def containsKhmerChar(s: str) -> bool:
    """Check whether a string contains a Khmer character.

    Script of the Khmer language.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Khmer character, False otherwise.
    """
    return containsScriptChar(s, 'Khmer')


def containsLaoChar(s: str) -> bool:
    """Check whether a string contains a Lao character.

    Script of the Lao language.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Lao character, False otherwise.
    """
    return containsScriptChar(s, 'Lao')


def containsMyanmarChar(s: str) -> bool:
    """Check whether a string contains a Myanmar character.

    Script of Burmese and several other languages of Myanmar.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Myanmar character, False otherwise.
    """
    return containsScriptChar(s, 'Myanmar')


def containsTibetanChar(s: str) -> bool:
    """Check whether a string contains a Tibetan character.

    Script of Tibetan and Dzongkha.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Tibetan character, False otherwise.
    """
    return containsScriptChar(s, 'Tibetan')


def containsSinhalaChar(s: str) -> bool:
    """Check whether a string contains a Sinhala character.

    Script of the Sinhala language.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Sinhala character, False otherwise.
    """
    return containsScriptChar(s, 'Sinhala')


def containsEthiopicChar(s: str) -> bool:
    """Check whether a string contains an Ethiopic character.

    Script of Amharic, Tigrinya and other languages of the Horn of Africa.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Ethiopic character, False otherwise.
    """
    return containsScriptChar(s, 'Ethiopic')


def containsMongolianChar(s: str) -> bool:
    """Check whether a string contains a Mongolian character.

    Covers the traditional Mongolian script. Mongolian written in Cyrillic is detected
    by `containsCyrillicChar`.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Mongolian character, False otherwise.
    """
    return containsScriptChar(s, 'Mongolian')


def containsKoreanChar(s: str) -> bool:
    """Check whether a string contains a Korean (Hangul) character.

    Detects Hangul only. Hanja (Chinese characters used in Korean text) are not
    detected, see `containsChineseChar`.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Korean (Hangul) character, False otherwise.
    """
    return containsScriptChar(s, 'Hangul')


def containsJapaneseChar(s: str) -> bool:
    """Check whether a string contains a Japanese (kana) character.

    Detects kana only (Hiragana and Katakana). Kanji are Han characters shared with
    Chinese, so they cannot tell Japanese from Chinese and are not detected, see
    `containsChineseChar`. The prolonged sound mark and the middle dot belong to no
    script and do not match.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Japanese (kana) character, False otherwise.
    """
    return containsScriptChar(s, *JAPANESE_SCRIPTS)

def containsChineseChar(s: str) -> bool:
    """Check whether a string contains a Chinese (Han) character.

    Covers the whole Unicode Han script: the CJK Unified Ideographs and all their
    extensions, the compatibility ideographs, the CJK radicals and a few ideographic
    marks such as the iteration mark U+3005. Han ideographs are shared with Japanese
    kanji and Korean hanja, so this cannot tell Chinese from those languages. CJK
    punctuation belongs to no script and does not match.

    Args:
        s: String to scan.

    Returns:
        True if `s` contains at least one Han character, False otherwise.
    """
    return containsScriptChar(s, 'Han')
