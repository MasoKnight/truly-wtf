# truly.wtf

A tiny markdown-powered blog. Write posts in markdown, run one script, push to GitHub.

## How it fits together

```
content/
  home.md            <- the homepage text (above the post list)
  posts/
    web-pen-testing.md
    talk-notes.md
    reading.md
templates/
  base.html          <- page shell (header, footer, <head>) — shared by every page
  home.html          <- layout for the homepage
  post.html          <- layout for a single post
static/
  style.css          <- the entire look of the site, one file
build.py             <- reads content/, writes docs/
docs/                <- generated output — this is what gets published, don't hand-edit it
```

You should only ever need to touch things inside `content/` for day-to-day writing.
`templates/`, `static/style.css`, and `build.py` are there when you want to change how
the site looks or behaves.

## Writing a new post

1. Create a new file in `content/posts/`, named like:

   ```
   content/posts/2026-09-15-some-slug.md
   ```

   The `YYYY-MM-DD-` prefix controls sorting (newest first on the homepage) and gets
   stripped from the URL, so that file publishes at `truly.wtf/posts/some-slug/`.
   You can skip the date prefix if you don't care about ordering — undated posts just
   sort to the bottom, alphabetically.

2. Add frontmatter at the top, then write the post in markdown below it:

   ```markdown
   ---
   title: Some Slug
   description: One line for search engines / previews, optional.
   ---

   Whatever you want, in normal markdown. Headings, **bold**, `code`,
   [links](https://example.com), lists, all of it.
   ```

   (The `date:` field is optional if you used the filename prefix — either works.)

3. Build the site:

   ```bash
   python3 build.py
   ```

   This regenerates everything in `docs/` from scratch. It will print a list of every
   post it built.

4. Commit and push:

   ```bash
   git add .
   git commit -m "Add post: some slug"
   git push
   ```

That's it — GitHub Pages picks up `docs/` and Cloudflare serves it at truly.wtf.

## Editing an existing post

Just edit the `.md` file in `content/posts/`, run `python3 build.py` again, commit,
push.

## Changing the look

Everything visual lives in `static/style.css`. It's one plain CSS file with comments,
no build tooling, no preprocessor. Change a color or font, re-run `build.py`, done.

The page structure (header, footer, homepage layout, post layout) lives in
`templates/*.html`, using `{{placeholder}}` markers that `build.py` fills in.

Site-wide text (the title "Truly WTF?!", the tagline, the footer line) is set at the
top of `build.py` under "Site-wide settings".

## One-time setup notes

- `build.py` writes a `CNAME` file into `docs/` containing `truly.wtf`, so make sure
  your repo's GitHub Pages setting has the source set to the `docs/` folder (or move
  its contents to wherever your Pages source currently points, if that's different).
- Requires the `markdown` Python package: `pip install markdown` (already installed
  in the environment this was built in).

## A note on what got migrated

Your old `index.html` and `Web_Pen_Testing.html` had real, personal content in them —
that's now in `content/home.md` and `content/posts/web-pen-testing.md`, wording kept
as-is (typos and all — they're yours to fix whenever you like).

`Talk_Notes.html` and `reading.html` still had the original unedited template text in
them (the CSS Zen Garden boilerplate), not actual notes, so instead of publishing that
placeholder text I created `content/posts/talk-notes.md` and `content/posts/reading.md`
as empty stubs with just the links you were planning to take notes on. Fill them in
whenever you're ready.
