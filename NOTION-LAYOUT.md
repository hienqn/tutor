# Notion layout

Where a Notion topic lives, how upstream's workspace files map onto Notion, and the `ntn` commands that read and write it.

## Root

A private page titled `Tutor`, holding two databases:

- **Topics**: one row per Notion topic. Properties: Name (title), Status (select: Active, Paused, Done, Moved), Started (date). Each row's page is that topic's workspace.
- **Review**: every card, from every topic. Properties: Prompt (title), Answer (rich_text), Topic (relation to Topics), Lesson (url), Interval (number), Last result (select: correct, partial, wrong), Last drilled (date), Created (created_time), and Due, a formula: `if(empty(prop("Last drilled")), dateAdd(prop("Created"), 1, "days"), dateAdd(prop("Last drilled"), prop("Interval"), "days"))`. A card is due when Due is today or earlier.
- **Start here**: a page beside the two databases for any agent arriving fresh. It links this repo, says how to begin, and lists the ids (below).

## Topic page

| Upstream | Notion, inside the topic's row page |
| --- | --- |
| `MISSION.md` | A `Mission` heading at the top of the page body, with MISSION-FORMAT's sections |
| (none) | Child page `Handoff`: the last session's date and app, what it covered, the next lesson, cards due and when, open threads. Rewritten whole at every close with `ntn pages edit` |
| `NOTES.md` | Child page `Notes`, which also records whether I've opted out of communities |
| `GLOSSARY.md` | Database `Glossary`, whose description is GLOSSARY-FORMAT's topic line. Properties: Term (title), Definition (rich_text), Avoid (rich_text), Group (select), Note (rich_text, for a flagged ambiguity) |
| `RESOURCES.md` | Database `Resources`: Title (title), URL (url), Group (select: Knowledge, Wisdom, Gap), Use for (rich_text) |
| `learning-records/` | Database `Learning Records`: Title (title), No. (number), Status (select: active, superseded), Superseded by (number), Evidence (rich_text); the record itself is the row's page body |
| `lessons/` | Database `Lessons`, which is also the progress map: Title (title, `0001 <name>`), No. (number), Status (select: Planned, Current, Done), Unit (multi_select), Sources (rich_text, Course Map Keys). Each lesson is its row's page body |
| `reference/` | Child page `Reference`, one sub-page per reference doc |
| Course map (course topics, [COURSE.md](COURSE.md)) | Database `Course Map`: Title (title), Key (rich_text), Kind (select: Reading, Slides, Video, Worksheet, Solution, Homework, Project, Exam, Exam solution, Paper, Tool, Service), Access (select: public, gated, announced, moved), Unit (multi_select), Date (date), URL (url), Local (rich_text), Related (rich_text), Covers (rich_text), License (rich_text), Lesson (rich_text), Posted (date), Note (rich_text) |

## ntn recipes

An app with its own Notion connector does the same operations with its tools; the layout above is what matters. On my Mac, `ntn` keeps my session in the macOS keychain, so commands carry no token. Every recipe below was run against Notion API version 2026-03-11. Three rules hold for every call:

- End each `ntn` command with `< /dev/null`. `ntn` reads a request body from stdin whenever stdin is not a terminal, so a call left on an open pipe waits forever.
- Pass bodies as one single-quoted argument (`--data '<json>'`, `--content '<markdown>'`). zsh expands `a[b]=c` field syntax as a glob.
- Page bodies are Notion's enhanced Markdown, and a leading `# Heading` becomes the page title.

| Job | Command |
| --- | --- |
| Check the session | `ntn doctor < /dev/null` |
| Find a page by title | `ntn api v1/search --data '{"query":"<title>","filter":{"property":"object","value":"page"}}' < /dev/null` |
| Read a page's properties | `ntn api v1/pages/<page-id> < /dev/null` |
| Read a page's body | `ntn pages get <page-id> < /dev/null` (front matter holds the title; children appear as `<page url="...">` and `<database url="...">` tags) |
| List a page's children | `ntn api v1/blocks/<page-id>/children < /dev/null` (`child_page` and `child_database` blocks carry ids and titles) |
| Create a child page | `ntn pages create --parent page:<page-id> --content '<markdown>' < /dev/null` (prints the new page id) |
| Rewrite a page's body | `ntn pages edit <page-id> --content '<markdown>' < /dev/null`. It replaces the whole body and refuses to drop a child page or database: read the body first and keep every `<page>` and `<database>` tag in what you write back |
| Insert blocks after a block | `ntn api v1/blocks/<page-id>/children -X PATCH --data '{"children":[<blocks>],"position":{"type":"after_block","after_block":{"id":"<block-id>"}}}' < /dev/null`. Safer than a whole-body rewrite for one addition; `after` is refused on this API version |
| Create a database | `ntn api v1/databases --data '{"parent":{"type":"page_id","page_id":"<id>"},"title":[<text>],"is_inline":true,"initial_data_source":{"properties":{<schema>}}}' < /dev/null` (the response's `data_sources[0].id` is the data source) |
| Add a row | `ntn api v1/pages --data '{"parent":{"type":"data_source_id","data_source_id":"<id>"},"properties":{<values>},"markdown":"<body>"}' < /dev/null` |
| Update a row | `ntn api v1/pages/<page-id> -X PATCH --data '{"properties":{<values>}}' < /dev/null` |
| Query rows (due cards) | `ntn api v1/data_sources/<id>/query --data '{"filter":{"property":"Due","formula":{"date":{"on_or_before":"<YYYY-MM-DD>"}}},"page_size":100}' < /dev/null` (Due is a formula, so the filter nests under `formula`), repeating with `"start_cursor":"<next_cursor>"` while `has_more` is true. This endpoint returns named properties; `ntn datasources query` prints unlabeled columns |
| Trash a page or row | `ntn pages trash <page-id> --yes < /dev/null` |

Schema shapes: `{"title":{}}`, `{"rich_text":{}}`, `{"number":{"format":"number"}}`, `{"select":{"options":[{"name":"..."}]}}`, `{"multi_select":{"options":[]}}`, `{"date":{}}`, `{"url":{}}`, `{"relation":{"data_source_id":"<id>","type":"single_property","single_property":{}}}`. Value shapes: title and rich_text `[{"type":"text","text":{"content":"..."}}]`, select `{"name":"..."}`, multi_select `[{"name":"..."}]`, number `2`, date `{"start":"YYYY-MM-DD"}`, url `"https://..."`, relation `[{"id":"<page-id>"}]`.

## Ids

This file is public, so it holds no ids. They are on the `Start here` page under the root: find the root with the search recipe (query `Tutor`), list its children, and read `Start here`. Each topic page's own databases are found from its row in Topics.
