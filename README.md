# Vita3K translations

Interface translations for [Vita3K](https://github.com/Vita3K/Vita3K), managed on
[Crowdin](https://crowdin.com/project/vita3k).

Translate on Crowdin, not here: the daily sync overwrites this repository with whatever the
project holds, so a hand-written change is lost at the next run.

## Layout

| Path | Contents |
| --- | --- |
| `template/vita3k_template.ts` | English source strings of the Qt interface, generated from the emulator sources |
| `translations/vita3k_<tag>.ts` | One Qt file per language, written by Crowdin |
| `qm/vita3k_<tag>.qm` | Compiled Qt translations, published as a release |
| `android/strings.xml` | English source strings of the Android interface, copied from the emulator repository |
| `android/values-<code>/strings.xml` | One Android resource file per language, written by Crowdin. Crowdin always writes a region (`values-de-rDE`); `scripts/pack_android_strings.py` drops it in the release where Android needs the bare language |

## How it flows

1. **Emulator repository** — a push that touches the Qt interface runs `qt-ts.yml`, which runs
   `lupdate` and uploads `vita3k_template.ts` as a build artifact. The Android strings need no
   build step; they are a plain file in that repository.
2. **`fetch-sources.yml`** (Mondays, 01:00 UTC) — downloads that artifact and the current
   `strings.xml`, merges the template into every Qt language with `lupdate -no-obsolete`, and
   commits the result.
3. **`crowdin.yml`** (daily, 01:00 UTC) — uploads both sources to Crowdin and commits the
   translations it downloads straight to `main`.
4. **`generate-qm.yml`** — runs `lrelease`, commits the `.qm` files, screens the incoming
   strings with Gemini, and publishes `vita3k-languages.zip` and `vita3k-android-strings.zip`
   as a release. The sync calls it directly, because a push made with `GITHUB_TOKEN` raises no
   push event.
5. **Emulator build** — `.ci/common.sh` unpacks the Qt archive into the build's
   `qt_translations` directory and the Android archive into `android/app/src/main/res`, where
   every packaging step already looks. A failed download only means a build without
   translations.

## Review

Every import is screened by `scripts/review_translations.py` before it is published: it asks
Gemini to flag abuse, spam, vandalism, obvious mistranslation, and placeholders a translation
breaks, and writes what it finds to the run summary. It reads only what the import changed.
Run `generate-qm.yml` by hand with **Review every translated string** to screen everything.

The review needs a `GEMINI_API_KEY` secret. Without one the run still publishes, and the
summary says the review did not happen.

## Adding a language

Enable it on Crowdin and the sync creates the files on its own. Android picks a language up
from the resource directory alone, but the Qt interface only lists a language its
`k_ui_languages` table knows, so a language new to Vita3K also needs an entry in
`vita3k/gui-qt/src/gui_language.cpp`. Qt file names carry the tag that table uses, which is why
`crowdin.yml` maps Crowdin's `zh-CN` and `zh-TW` onto `zh_Hans` and `zh_Hant`.

## Setup

Repository secrets:

| Secret | Purpose |
| --- | --- |
| `CROWDIN_PROJECT_ID` | Crowdin project the sync talks to |
| `CROWDIN_PERSONAL_TOKEN` | Crowdin token with the manager or developer role and the `project`, `project.source` and `project.translation` scopes |
| `GEMINI_API_KEY` | Key the review uses |
| `TEMPLATE_TOKEN` | Optional. Only needed if the default token cannot read the emulator repository's artifacts |

Repository variables `SOURCE_REPO` and `SOURCE_BRANCH` override where the sources come from;
they default to `Vita3K/Vita3K` and `master`.
