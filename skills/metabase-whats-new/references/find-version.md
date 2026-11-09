# How to find your Metabase version

Walk the user through these in order. Stop as soon as they find it.

## The fastest way (works for most people)

1. In Metabase, click the **gear icon** (⚙️) in the top-right corner.
2. Click **About Metabase**.
3. A small window pops up showing the version — something like `v0.52.6` or `v1.52.6`.

That's it. Have them read the whole string to you.

## If they can't see the gear icon

They might be in an embedded view or on a limited account. Try:

1. Open any Metabase URL in the browser (e.g., the dashboard they're looking at).
2. Add `/api/session/properties` to the end of the base URL. For example: `https://mycompany.metabase.com/api/session/properties`.
3. Press Enter. A big block of JSON loads. Search for `"version"` — the value next to `tag` is the version, like `v0.52.6`.

## If they're an admin

Admins can also see it in **Admin settings → Settings → General**.

## How to read what they tell you

The version string looks like `v0.XX.Y` or `v1.XX.Y`:

- **`v0.` prefix** → **OSS** (Open Source, self-hosted, free). Example: `v0.52.6` is OSS running version 52.
- **`v1.` prefix** → **Paid plan** (Starter, Pro, Cloud, or Enterprise). Example: `v1.52.6` is a paid plan running version 52.
- **`XX`** → the major version. This is the number that matters most for features — `52` means Metabase 52.
- **`Y`** → the patch number. Rarely matters for feature discussions.

If their version prefix is anything other than `0.` or `1.` (very old builds), say so plainly and point them to [the full releases page](https://www.metabase.com/releases).

Once you have both the major version and OSS/paid, go back to Step 2 of the main skill flow.
