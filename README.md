# Vita3K translations

Qt interface translations for [Vita3K](https://github.com/Vita3K/Vita3K), managed on
[Crowdin](https://crowdin.com/project/vita3k).

Translate on Crowdin, not here: the daily sync overwrites `translations/` with whatever the
project holds, so a hand-written change is lost at the next run.

## Layout

| Path | Contents |
| --- | --- |
| `template/vita3k_template.ts` | English source strings, generated from the emulator sources |
| `translations/vita3k_<tag>.ts` | One file per language, written by Crowdin |
| `qm/vita3k_<tag>.qm` | Compiled translations, published as a release |

## How it flows

1. **Emulator repository** — a push that touches the Qt interface runs `qt-ts.yml`, which runs
   `lupdate` and uploads `vita3k_template.ts` as a build artifact.
2. **`fetch-template.yml`** (Mondays, 01:00 UTC) — downloads that artifact, merges it into every
   language with `lupdate -no-obsolete`, and commits the result.
3. **`crowdin.yml`** (daily, 01:00 UTC) — uploads the template to Crowdin and commits the
   translations it downloads straight to `main`.
4. **`generate-qm.yml`** (daily, 02:00 UTC) — runs `lrelease`, commits the `.qm` files, and
   publishes `Vita3K-languages.zip` as a release when anything changed.
5. **Emulator build** — `.ci/common.sh` downloads that zip into the build's `qt_translations`
   directory, and every packaging step picks it up from there. A failed download only means a
   build without translations.

## Adding a language

Enable it on Crowdin and the sync creates the file on its own. The emulator only lists a language
that its `k_ui_languages` table knows, so a language new to Vita3K also needs an entry in
`vita3k/gui-qt/src/gui_language.cpp`. File names carry the tag that table uses, which is why
`crowdin.yml` maps Crowdin's `zh-CN` and `zh-TW` onto `zh_Hans` and `zh_Hant`.

## Setup

Repository secrets:

| Secret | Purpose |
| --- | --- |
| `CROWDIN_PROJECT_ID` | Crowdin project the sync talks to |
| `CROWDIN_PERSONAL_TOKEN` | Crowdin token with the manager or developer role and the `project`, `project.source` and `project.translation` scopes |
| `TEMPLATE_TOKEN` | Optional. Only needed if the default token cannot read the emulator repository's artifacts |

Repository variable `SOURCE_REPO` overrides the emulator repository the template comes from; it
defaults to `Vita3K/Vita3K`.
