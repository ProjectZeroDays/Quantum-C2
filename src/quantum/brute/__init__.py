"""quantum.brute — crunch-style custom password list creation, honestly wired."""
from quantum.brute.crunch import (
    CRUNCH_NOTE,
    SYMBOLS,
    detect_crunch,
    estimate_count,
    estimate_size,
    expand_charset,
    generate,
    parse_pattern,
    write_wordlist,
)

__all__ = [
    "CRUNCH_NOTE",
    "SYMBOLS",
    "detect_crunch",
    "estimate_count",
    "estimate_size",
    "expand_charset",
    "generate",
    "parse_pattern",
    "write_wordlist",
]
