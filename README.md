# tutor

My personal tutor: one teacher, one learner, many sessions. It layers Matt Pocock's [`teach`](https://github.com/mattpocock/skills/tree/main/skills/productivity/teach) method onto storage that any agent can reach, so a topic can move between Claude Code, Claude, Muse, Grok or any other app and pick up where the last session stopped.

## Start a session from any app

Paste this, naming the topic:

> You're my tutor. Read https://github.com/hienqn/tutor, starting with SKILL.md, then my Notion page Tutor / Start here, and continue CS 168.

The app needs to read and write my Notion. Everything else (forms, artifacts, local files, running code) is optional, and [SKILL.md](SKILL.md) says what to do without it.

In Claude Code on my Mac this folder is `~/.claude/skills/tutor`, so `/tutor`, `/tutor review` and `/tutor <topic>` work directly.

## What lives where

| Place | Holds |
| --- | --- |
| This repo | The rules and the code: [SKILL.md](SKILL.md) (the session), [NOTION-LAYOUT.md](NOTION-LAYOUT.md) (where things go, with tested `ntn` commands), [COURSE.md](COURSE.md) (taking a university course in), [extract.py](extract.py) (any download to text), [templates/](templates/) and [examples/](examples/) |
| Notion | My data: topics, missions, lessons, cards, records, glossaries, each topic's Handoff, and the `Start here` page with the ids |
| My Mac | Course downloads and their text, past exams that may not be shared, project solutions. None of it goes in this repo |
| The vault | Topics that draw on anything Zillow-internal, in Markdown, never in Notion |

## Editing

Change the rules here and nowhere else; every app reads this copy. Keep em dashes out of the prose.
