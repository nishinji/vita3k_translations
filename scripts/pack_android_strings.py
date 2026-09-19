from __future__ import annotations

import argparse
from pathlib import Path
import re
import zipfile

VALUES_PREFIX = "values-"

# <string>/<item> bodies only, so the <string-array> and <plurals> wrappers do not match.
BODY = re.compile(r"(<(string|item)(?![\w-])[^>]*>)(.*?)(</\2>)", re.DOTALL)
TAG = re.compile(r"<[^>]*>")
APOSTROPHE = re.compile(r"&apos;|&#0*39;|'")


def escape_apostrophes(text: str) -> tuple[str, int]:
    """Give every unescaped apostrophe in a text run the backslash Android wants."""
    escaped = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal escaped
        backslashes = 0
        index = match.start() - 1
        while index >= 0 and text[index] == "\\":
            backslashes += 1
            index -= 1
        if backslashes % 2 == 1:
            return match.group(0)
        escaped += 1
        return "\\'"

    return APOSTROPHE.sub(replace, text), escaped


def escape_body(body: str) -> tuple[str, int]:
    stripped = body.strip()
    if len(stripped) >= 2 and stripped.startswith('"') and stripped.endswith('"'):
        # a fully quoted value keeps its apostrophes literally
        return body, 0

    pieces: list[str] = []
    escaped = 0
    position = 0
    for tag in TAG.finditer(body):
        text, count = escape_apostrophes(body[position:tag.start()])
        pieces.extend((text, tag.group(0)))
        escaped += count
        position = tag.end()
    text, count = escape_apostrophes(body[position:])
    pieces.append(text)

    return "".join(pieces), escaped + count


def android_strings(path: Path) -> tuple[bytes, int]:
    """Read one translated file and hand back what Android can actually compile.

    Crowdin writes an apostrophe as the XML entity &apos;. That is correct XML, but once
    the parser has decoded it aapt2 sees a bare ' inside a string resource that is not
    wrapped in double quotes and refuses to compile the resource, which fails the
    emulator's mergeResources with a rather opaque "Can not extract resource from ..."
    message. Translators cannot be expected to add Android's own escape on top of the
    XML one, so add it here rather than shipping an archive that does not build.
    """
    source = path.read_text(encoding="utf-8")
    escaped = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal escaped
        body, count = escape_body(match.group(3))
        escaped += count
        return match.group(1) + body + match.group(4)

    return BODY.sub(replace, source).encode("utf-8"), escaped


def qualifier_for(language: str, variants: dict[str, list[str]], qualifier: str) -> str:
    # Android falls back from de-AT to values-de but never to values-de-rDE, so the region is
    # kept only where the language has more than one variant. English keeps it too, because
    # values/ already holds English and values-en would take US devices with it.
    if language == "en" or len(variants[language]) > 1:
        return qualifier

    return language


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--res-dir", default=str(Path(__file__).resolve().parents[1] / "android"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    res_dir = Path(args.res_dir)
    sources = sorted(path for path in res_dir.glob(f"{VALUES_PREFIX}*/strings.xml"))
    if not sources:
        raise RuntimeError(f"No {VALUES_PREFIX}*/strings.xml under {res_dir}")

    variants: dict[str, list[str]] = {}
    for path in sources:
        qualifier = path.parent.name[len(VALUES_PREFIX):]
        variants.setdefault(qualifier.split("-r")[0], []).append(qualifier)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sources:
            qualifier = path.parent.name[len(VALUES_PREFIX):]
            language = qualifier.split("-r")[0]
            target = qualifier_for(language, variants, qualifier)
            strings, escaped = android_strings(path)
            archive.writestr(f"{VALUES_PREFIX}{target}/strings.xml", strings)
            note = f" ({escaped} apostrophe(s) escaped)" if escaped else ""
            print(f"{path.parent.name} -> {VALUES_PREFIX}{target}{note}")


if __name__ == "__main__":
    main()
