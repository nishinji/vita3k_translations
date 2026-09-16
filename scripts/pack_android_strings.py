from __future__ import annotations

import argparse
from pathlib import Path
import zipfile

VALUES_PREFIX = "values-"


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
            archive.write(path, f"{VALUES_PREFIX}{target}/strings.xml")
            print(f"{path.parent.name} -> {VALUES_PREFIX}{target}")


if __name__ == "__main__":
    main()
