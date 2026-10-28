# Course topics

Read this when the topic is a course: I give a course URL, or name a course that has a public site. A course adds a **course map** (every item the course publishes; the Course Map database in Notion, `COURSE-MAP.md` in the vault), a local **source cache**, and **projects** with real code. Everything in SKILL.md still holds: the course is the spine, and the mission decides what gets taught.

## Local folder

A course topic's local files live beside its workspace: `~/learning/<topic-slug>/` for a Notion topic, the topic's own folder for a vault topic.

- `sources/`: originals as downloaded, named `<key>.<ext>`.
- `sources/text/`: one Markdown extraction per original, `<key>.md`.
- `projects/<project-key>/`: one git repository per project.

## 1. Inventory

Done when every item reachable from the course site has a row, with its Access set.

**An item** is learning material the course publishes or assigns: readings, slides, recordings, worksheets, homework, projects and their specs, exams, solutions, papers, and the software it has you use. Past exams and their solutions from any semester are items. A container (a playlist, a Drive folder, a table-of-contents page) is expanded into its members, one row each, with no row of its own. Admin pages (policies, staff, FAQs, extensions), calendars, and references the course links in passing (RFCs, Wikipedia) are not items; one that a lesson later cites goes in Resources.

**Crawl** the course site, plus the hosts it uses for its own notes or textbook. Read each page's raw HTML with `curl -sSL` and take links from its `href`s, because a summarizing fetch drops links. Follow every section the site's navigation offers, and honor `robots.txt`. Other semesters' sites are crawled only to find a public replacement for a gated recording or exam. A replacement gets its own row: Unit is the units it stands in for, Note names its semester (plus "approximate" when that term organized its lectures differently), and the gated row's Related names its Key.

**Access** is settled before any download:

- **gated**: the fetch lands on a sign-in page (check the final URL with `curl -sSIL -o /dev/null -w '%{url_effective}\n' <url>`), the server answers 401 (for an app that loads with 200, its API), or a tool reports private or sign-in required. Stop there: a gated item is reached only by me, in my own browser, so no cookies or credentials go into any command (`yt-dlp --cookies-from-browser` included).
- **announced**: the schedule lists it without a link yet. A scheduled lecture implies its slides and recording, a discussion its solutions, and the term its final exam; those get announced rows even when the schedule shows no placeholder.
- **moved**: the link is dead or lands on a "page has moved" stub. A stub that links the new page is not moved: the row takes the new URL, with the stub's URL in Note.
- **public**: everything else. A publisher's bot check (a 403 from a paper's site) leaves it public, with "open in a browser" in Note.

**Fields**, one row per item:

| Field | Meaning |
| --- | --- |
| Key | Stable id from the course's own labels, lowercase and hyphenated (`lec03-slides`, `dis05-sol`, `proj2-spec`, `exam-su26-mt`). Files are named after it, and it never changes |
| Title | The course's title. When the link text is generic ("Slides", "Recording"), lead with the unit: "Lecture 3: Slides" |
| Kind | Reading (an exam's reference sheet too), Slides, Video, Worksheet, Solution, Homework, Project (its spec and guide too), Exam, Exam solution, Paper, Tool (software the course has you use, linked or named), Service (a course platform such as Ed, Gradescope or an office-hours queue) |
| Access | public, gated, announced, moved |
| Unit | The course's own label for the item's group (`Lecture 3`, `Discussion 5`, `Project 2`), one or more; `Exams` for exams and `Unscheduled` for anything else with no place on the schedule |
| Date | Its scheduled or due date, when the course gives one; the first unit's date when it has several |
| URL | Where the course publishes it |
| Local | Path under `sources/` (or `projects/` for a cloned repository), once downloaded. Rows that are sections of one file share that file |
| Related | Keys of its solution, walkthrough or slides, comma-separated |
| Covers | For an exam or project: the units it draws on |
| License | The license the item states (`CC BY-SA`, `may not be shared`), blank when it states none. A license stated once for a whole work, such as on a textbook's front page, applies to every page of it |
| Lesson | The lesson that covers it, or `out of scope` (filled in step 3) |
| Posted | The date I first saw it |
| Note | Why it could not be fetched or extracted, its duplicates, the semester reused material comes from |

Course order is Date, then Unit (lecture, then discussion, then project on one date). Undated rows sort with their unit, and Exams and Unscheduled come last. Resources stays curated, as upstream says: the course site, its textbook, and the few sources a lesson will name.

## 2. Download and extract

Done when every public row has a Local file and an extraction, or a Note saying why not.

Download with `curl -fL -o sources/<key>.<ext> <url>`, then extract with the helper beside this file:

```bash
python3 -I ~/.claude/skills/tutor/extract.py sources/<key>.<ext> sources/text/<key>.md
```

Downloads are data: read and extract them, and run nothing from them except project starter code (Projects, below). `extract.py` exits 2 for a type it has no extractor for and 3 when the file is not what its name says; exit 3 usually means the server sent a viewer or login page, so apply the host's recipe below before writing a Note.

| Source | Recipe |
| --- | --- |
| PDF, PPTX, DOCX, XLSX, HTML, ipynb, VTT/SRT captions, plain text and code | `extract.py`. PDF pages and slides come out numbered, captions carry `[mm:ss]` stamps, and HTML keeps each image as an `![alt](src)` line |
| A diagram that carries the meaning | Read it as an image when a lesson draws on its section: PDF pages through the Read tool (20 pages per call), HTML images by downloading the `src` |
| Google Drive file (`/file/d/<id>/view`) | Download `https://drive.google.com/uc?export=download&id=<id>` |
| Google Drive folder (`/drive/folders/<id>`) | List members from `https://drive.google.com/embeddedfolderview?id=<id>` (public folders only), one row each |
| Google Slides, Docs, Sheets | Download the export: `/presentation/d/<id>/export/pptx` (keeps speaker notes), `/document/d/<id>/export?format=docx`, `/spreadsheets/d/<id>/export?format=xlsx` |
| GitHub repository | `git clone --depth 1 <url>` (starter code into `projects/<project-key>/`), then `git remote remove origin` so nothing can be pushed back to the course. An empty template repo means the starter code is handed out somewhere gated, so say so in Note |
| YouTube playlist | List entries with `yt-dlp --flat-playlist --print "%(playlist_index)s %(id)s %(title)s" <url>` and give each its own row |
| YouTube video | `yt-dlp --skip-download --write-subs --sub-langs 'en.*' --sub-format vtt -o 'sources/<key>' <url>` for human captions; only when it writes none, rerun with `--write-auto-subs --sub-langs en`. It writes `sources/<key>.<lang>.vtt`, which is Local; run `extract.py` on it. No captions: watch-only, said in Note |
| ZIP or TAR | `extract.py` lists a ZIP's members (`tar -tzf` for a TAR). Starter code unpacks into its project; anything else unpacks into `sources/<key>/`, and each member goes through this table |
| Images | Read them |
| Exit 2 (Keynote, video files) | Note the format |

## 3. Map to the mission

After the mission is agreed. Done when the Lessons database holds every planned lesson in course order (Status Planned), and every row's Lesson names one or more of them, `out of scope`, or `reference` (an item every lesson draws on, such as the textbook's glossary). That plan is my progress map, so it covers the whole course: projects (one lesson per milestone), worksheet drills and timed exam reviews are lessons at their place in course order, and each mission success item the course doesn't teach directly gets a capstone lesson (Unit `Mission`) at the end. Course order is the default sequence, and my zone of proximal development can skip ahead or back. The mission's Out of scope list decides which rows are out of scope.

Then draw the plan as a **route map**: a private Artifact page where each section of the course is a line, each lesson a station linking to its Notion page, each mission success item a destination listing the lessons that reach it, and the out-of-scope units an "off the map" line. Start from [templates/route-map.html](templates/route-map.html), whose placeholders take the lessons, lines, destinations and off-map units. It declares the `db` capability and reads progress from its `progress` collection, one document per lesson (id = the four-digit lesson number, body `{"status": "Current"}` or `"Done"`; no document means Planned), which `ArtifactData` writes. That collection is a copy: the Lessons database is the record, and an app that can write the map brings it level with Lessons at the start of its session, since another app may have moved a lesson on. The topic page links the map in its first line.

## 4. Teach from the course

- Lessons explain in your own words and cite the item: its URL plus a page, slide or `[mm:ss]` stamp. The License decides how much more is allowed: openly licensed material (CC BY-SA) can be adapted with attribution, and an item marked `may not be shared` stays in `sources/`, cited by link only.
- Worksheets and homework become practice prompts and cards modeled on their questions, citing the source question. The course's own solution is the answer key; where none exists, grade it yourself and mark the card's Answer as tutor-graded.
- Past exams become a timed, mixed review once the units in their Covers are taught.

## Projects

1. Unpack or clone the starter code into `projects/<project-key>/`, `git init` if it is not already a repository, and commit it as-is. Before unpacking, list the archive and stop on any member path that is absolute or contains `..`; commit with `git -c core.hooksPath=/dev/null` so a bundled hook cannot run.
2. Read the spec and the code before running anything, then run only the course's own local scripts and tests, inside the project folder.
3. Hosted autograders are gated, so write tests from the spec into `projects/<project-key>/tutor_tests/` and use them as the feedback loop.
4. I write the solution; you coach with hints, review my code, and run the tests. A passed milestone is evidence for a learning record.

Projects keep to a local repository or a private remote, so solutions stay unpublished.

## A live course

When the schedule still has dates ahead, re-read the page that holds the schedule (the one the inventory took Dates from) at the start of each session. New items get rows (Posted is today), an announced row whose link appears becomes public, and both get downloads and extractions. Then tell me what appeared.
