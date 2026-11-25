# Manual stance annotations

Two stratified samples were annotated by hand and used to train and evaluate the stance classifier in notebook 06.

| File | Items | How the sample was drawn |
|---|---|---|
| `x_annotations.csv` | 376 X posts | stratified by keyword group (A/B/C) and account type (news media, large accounts > 500k followers, small accounts), plus 80 replies/quotes so that interaction posts are represented |
| `reddit_annotations.csv` | 507 Reddit items | two random draws from the relevant threads (150 submissions, 360 comments; at most 14 items per subreddit in the second draw; bots, deleted authors, removed texts and items shorter than 30 characters excluded); comments were labelled with their thread title and parent comment visible |

## Stance (towards the CJP-led Jantar Mantar protest)

* **PRO** – supports the protest, the CJP, its leaders or its demands (Pradhan's resignation, exam accountability); criticises the government's or police's handling in favour of the protesters; announces participation.
* **ANTI** – opposes, mocks or delegitimises the protest or the CJP (drama, picnic, "B-team of AAP", paid/foreign-funded, low turnout, hypocrisy), defends the government or police, or wants the protest stopped.
* **NEUTRAL** – news reporting and factual updates without an evaluative stance, questions, fact-checks, off-topic items, and mixed or unclear positions. Posts that merely quote a CJP statement in a news style are NEUTRAL even when posted by a supporter account.

The label describes the **text**, not the account. User-level stance is obtained later by averaging the stance of all items a user posted.

## Hostile (binary)

1 when the text contains personal insults, slurs, dehumanising terms, threats, endorsement of violence, or explicit accusations of treason, terrorism links or paid protest aimed at a person or group on either side. Mockery alone (circus, clown, picnic, drama) is **not** hostile.

## Columns

`n` running number · `id` post or comment id · `author` · `grp` keyword group (X) / `kind` submission or comment (Reddit) · `subreddit` · `text` · `stance` · `hostile`.
