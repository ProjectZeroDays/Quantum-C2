"""quantum.brute.crunch — crunch-compatible custom password list creation.

Mirrors the Kali `crunch <min> <max> [charset] [-t pattern] [-o wordlist.txt]`
semantics operators already know:

* charset placeholders inside ``-t`` patterns: ``@`` lowercase, ``,`` uppercase,
  ``%`` digits, ``^`` symbols; any other char is literal (backslash escapes a
  literal placeholder, e.g. ``\\@``). Pattern classes are FIXED (full a-z /
  A-Z / 0-9 / symbols) exactly like real crunch — a custom charset only
  applies to non-pattern mode.
* no charset and no pattern  ->  ascii lowercase (crunch's default).
* ordering is rightmost-slot-fastest (odometer), identical to crunch output.

Backend selection is honest (see CRUNCH_NOTE): when the real ``crunch``
binary is installed on THIS host it is used as a passthrough
(``backend="system"`` or ``"auto"``); otherwise the pure-Python generator
with identical ordering produces the list. Nothing is ever bundled or faked.

Combinatorial explosion is guarded: estimate_*() give exact counts/sizes up
front, and write_wordlist() refuses jobs over `cap` entries unless
allow_huge=True (with the estimate quoted back so the operator can narrow
the job instead of filling a disk by accident).
"""
from __future__ import annotations

import itertools
import os
import shutil
import string
import subprocess

CRUNCH_NOTE = (
    "crunch output semantics (lengths, charset classes, @ , % ^ pattern "
    "placeholders, odometer ordering). Uses the system `crunch` binary when "
    "installed on this host, else an identical pure-Python generator. "
    "crunch is NOT bundled (Kali tool, GPLv2) — install it for the system "
    "backend, or use the embedded generator."
)

LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits
# crunch's symbol class (documented exactly — string.punctuation).
SYMBOLS = string.punctuation

PLACEHOLDERS = {"@": LOWER, ",": UPPER, "%": DIGITS, "^": SYMBOLS}

DEFAULT_CAP = 100_000_000


def detect_crunch():
    """Path to the system `crunch` binary on THIS host, or None."""
    return shutil.which("crunch")


def expand_charset(spec):
    """Literal charset string -> deduplicated chars, order preserved.

    The spec is literal (like crunch's charset argument); placeholders are
    NOT expanded here — they only have meaning inside -t patterns.
    """
    if not spec:
        raise ValueError("charset must not be empty")
    seen = set()
    out = []
    for ch in spec:
        if ch not in seen:
            seen.add(ch)
            out.append(ch)
    return "".join(out)


def charset_from_file(path, name=None):
    """Minimal charset.lst support: `name = chars` lines (+ `#` comments).

    With `name`, returns that entry; without, the file must hold exactly one
    entry. Raises ValueError listing available names on mismatch.
    """
    entries = {}
    order = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                entry_name, chars = line.split("=", 1)
                entry_name = entry_name.strip()
                chars = chars.strip()
            else:
                entry_name, chars = f"line{len(order) + 1}", line
            if entry_name and chars and entry_name not in entries:
                entries[entry_name] = chars
                order.append(entry_name)
    if name is not None:
        if name not in entries:
            raise ValueError(
                f"charset {name!r} not in {path} (available: {', '.join(order) or 'none'})"
            )
        return entries[name]
    if len(entries) != 1:
        raise ValueError(
            f"{path} holds {len(entries)} charsets — pick one by name "
            f"(available: {', '.join(order) or 'none'})"
        )
    return entries[order[0]]


def parse_pattern(pattern):
    """Pattern -> list of ("lit", char) / ("class", placeholder) slots.

    Backslash escapes the next char into a literal. Raises ValueError on a
    trailing backslash or an empty pattern.
    """
    if not pattern:
        raise ValueError("pattern must not be empty")
    slots = []
    escaped = False
    for ch in pattern:
        if escaped:
            slots.append(("lit", ch))
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch in PLACEHOLDERS:
            slots.append(("class", ch))
        else:
            slots.append(("lit", ch))
    if escaped:
        raise ValueError("pattern ends with a dangling backslash")
    return slots


def _check_lengths(min_len, max_len):
    if not isinstance(min_len, int) or not isinstance(max_len, int):
        raise ValueError("min/max lengths must be integers")
    if min_len < 1:
        raise ValueError(f"min length must be >= 1 (got {min_len})")
    if max_len < min_len:
        raise ValueError(f"max length {max_len} < min length {min_len}")


def estimate_count(min_len, max_len, charset=None, pattern=None):
    """Exact entry count for the job (no generation performed)."""
    _check_lengths(min_len, max_len)
    if pattern is not None:
        slots = parse_pattern(pattern)
        if not (min_len == max_len == len(slots)):
            raise ValueError(
                f"with -t, min ({min_len}) and max ({max_len}) must both equal "
                f"the pattern length ({len(slots)})"
            )
        total = 1
        for kind, val in slots:
            total *= len(PLACEHOLDERS[val]) if kind == "class" else 1
        return total
    chars = expand_charset(charset if charset is not None else LOWER)
    base = len(chars)
    return sum(base ** length for length in range(min_len, max_len + 1))


def estimate_size(min_len, max_len, charset=None, pattern=None):
    """Exact {"entries": n, "bytes": b} including one newline per entry."""
    _check_lengths(min_len, max_len)
    if pattern is not None:
        slots = parse_pattern(pattern)
        if not (min_len == max_len == len(slots)):
            raise ValueError(
                f"with -t, min ({min_len}) and max ({max_len}) must both equal "
                f"the pattern length ({len(slots)})"
            )
        entries = estimate_count(min_len, max_len, pattern=pattern)
        return {"entries": entries, "bytes": entries * (len(slots) + 1)}
    chars = expand_charset(charset if charset is not None else LOWER)
    base = len(chars)
    entries = 0
    size = 0
    for length in range(min_len, max_len + 1):
        count = base ** length
        entries += count
        size += count * (length + 1)
    return {"entries": entries, "bytes": size}


def _slot_alphabets(pattern):
    return [
        PLACEHOLDERS[val] if kind == "class" else val
        for kind, val in parse_pattern(pattern)
    ]


def generate(min_len, max_len, charset=None, pattern=None,
             resume_from=None, limit=None):
    """Lazy odometer-ordered candidate generator (rightmost slot fastest).

    resume_from skips every entry sorting before it (crunch -s semantics);
    limit caps yielded entries (crunch -c). Both compose: skip first, then
    cap — matching `crunch ... -s START -c N`.
    """
    _check_lengths(min_len, max_len)
    if limit is not None and limit < 0:
        raise ValueError("limit must be >= 0")
    if pattern is not None:
        slots = parse_pattern(pattern)
        if not (min_len == max_len == len(slots)):
            raise ValueError(
                f"with -t, min ({min_len}) and max ({max_len}) must both equal "
                f"the pattern length ({len(slots)})"
            )
        alphabets = _slot_alphabets(pattern)
        combos = ("".join(p) for p in itertools.product(*alphabets))
    else:
        chars = expand_charset(charset if charset is not None else LOWER)

        def combos():
            for length in range(min_len, max_len + 1):
                for prod in itertools.product(chars, repeat=length):
                    yield "".join(prod)

        combos = combos()
    yielded = 0
    for entry in combos:
        if resume_from is not None and entry < resume_from:
            continue
        if limit is not None and yielded >= limit:
            return
        yield entry
        yielded += 1


def _system_argv(min_len, max_len, charset, pattern, path,
                 resume_from, limit):
    argv = ["crunch", str(min_len), str(max_len)]
    if pattern is not None:
        # pattern classes are fixed in crunch — a custom charset is ignored
        # with -t, so it is deliberately not forwarded.
        argv += ["-t", pattern]
    elif charset is not None:
        argv.append(charset)
    if resume_from is not None:
        argv += ["-s", resume_from]
    if limit is not None:
        argv += ["-c", str(limit)]
    argv += ["-o", path]
    return argv


def write_wordlist(path, min_len, max_len, charset=None, pattern=None,
                   backend="auto", resume_from=None, limit=None,
                   cap=DEFAULT_CAP, allow_huge=False, progress=None):
    """Generate the wordlist file; returns {"path","entries","bytes","backend"}.

    backend: "auto" (system crunch if installed, else embedded), "system"
    (error when missing), "embedded" (always pure-Python). progress, when
    given, is called with cumulative entries every 100k (embedded) or once
    at completion (system backend — documented, no fake granularity).
    """
    est = estimate_size(min_len, max_len, charset=charset, pattern=pattern)
    if est["entries"] > cap and not allow_huge:
        raise ValueError(
            f"job would emit {est['entries']:,} entries "
            f"(~{est['bytes'] / 1e9:.1f} GB) — over the {cap:,} cap. Narrow "
            "min/max, shrink the charset/pattern, or pass allow_huge=True."
        )
    use_system = (
        backend == "system"
        or (backend == "auto" and detect_crunch() is not None)
    )
    if backend not in ("auto", "system", "embedded"):
        raise ValueError(f"unknown backend {backend!r} (auto|system|embedded)")
    if backend == "system" and detect_crunch() is None:
        raise ValueError("backend='system' but no `crunch` binary is installed")
    if use_system:
        argv = _system_argv(min_len, max_len, charset, pattern, path,
                            resume_from, limit)
        proc = subprocess.run(argv, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"crunch failed: {proc.stderr.strip() or proc.stdout.strip()}")
        entries = sum(1 for _ in open(path, encoding="utf-8", errors="replace"))
        size = os.path.getsize(path)
        if progress is not None:
            progress(entries)
        return {"path": path, "entries": entries,
                "bytes": size, "backend": "system"}
    count = 0
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for entry in generate(min_len, max_len, charset=charset,
                              pattern=pattern, resume_from=resume_from,
                              limit=limit):
            fh.write(entry + "\n")
            count += 1
            if progress is not None and count % 100_000 == 0:
                progress(count)
    if progress is not None:
        progress(count)
    return {"path": path, "entries": count,
            "bytes": os.path.getsize(path), "backend": "embedded"}
