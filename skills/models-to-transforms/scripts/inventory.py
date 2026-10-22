#!/usr/bin/env python3
"""Inventory and classify every Metabase model, read-only.

Two data paths, one classifier:
  * API path (default): `mb` CLI calls only (search per database, card get, table get, dependency dependents), plus
    GETs through mb_rest.mjs for what the CLI lacks.
  * App-DB path (--app-db <database id>): SELECT-only SQL against the instance's own application database (PostgreSQL
    app DBs only) when it is connected to the instance as a data source. Faster, and it sees bookmarks, alerts,
    subscriptions, filter sources, actions, sandboxes and archived dependents that the API path can't count.

Outputs (in --out):
  models.csv        one row per model: class, proposed action, wave, target table, swap readiness, usage, dependents,
                    model-only features, freshness evidence, flags
  models.jsonl      the same plus column keys, FK columns, card refs and the raw dataset_query
  model_edges.csv   model -> upstream card edges, and the upstream models reached through saved questions
  failures.csv      models or calls that could not be read (the run exits 3 when this is non-empty, unless --allow-partial)
  summary.md        counts, swap readiness, and what this run could not see

Usage:
  python3 inventory.py --profile prod --out ./.scratch/model-migration/inventory [--app-db 12] [--include-archived]
                       [--db-ids 26,48] [--ids 1,2,3] [--max-models 50] [--workers 6] [--stale-days 180] [--extras]
                       [--no-deps] [--allow-partial]
  python3 inventory.py --profile prod --app-db 12 --sql q.sql      # run one guarded SELECT, print CSV (gate queries)
"""
import argparse, collections, concurrent.futures as cf, csv, datetime as dt, io, json, os, re, subprocess, sys, threading

csv.field_size_limit(sys.maxsize)

AUDIT_DB_ID = 13371337  # Metabase's built-in usage-analytics database; GET /api/database hides it
WRAPPER_OPS = {"fields", "order-by", "limit"}
IGNORED_KEYS = {"lib/type", "lib/options", "lib/stage-metadata", "source-metadata", "parameters", "lib/uuid",
                "source-table", "source-card", "source-query", "native", "template-tags"}
PARAM_TAG_TYPES = {"text", "number", "date", "dimension", "temporal-unit", "boolean"}
TRANSFORM_ENGINES = {"postgres", "mysql", "redshift", "snowflake", "bigquery-cloud-sdk", "clickhouse", "sqlserver"}
SQL_REJECT = re.compile(r"\b(join|where|group\s+by|having|union|intersect|except|with|distinct|over|window|qualify|pivot|"
                        r"lateral|final|sample|tablesample)\b", re.I)
IDENT = r'(?:"[^"]+"|`[^`]+`|\[[^\]]+\]|[A-Za-z_][\w$]*)'
REL = rf"{IDENT}(?:\s*\.\s*{IDENT}){{0,2}}"
SELECT_RE = re.compile(rf"^select\s+(?P<cols>.+?)\s+from\s+(?P<rel>{REL})(?:\s+(?:as\s+)?(?P<alias>[A-Za-z_]\w*))?"
                       rf"(?P<order>\s+order\s+by\s+.+?)?(?P<limit>\s+limit\s+\d+(?:\s+offset\s+\d+)?)?$", re.I | re.S)
CARD_SELECT_RE = re.compile(r"^select\s+\*\s+from\s+\{\{\s*#(\d+)[^}]*\}\}(?:\s+(?:as\s+)?[A-Za-z_]\w*)?$", re.I)
CARD_TAG_RE = re.compile(r"\{\{\s*#(\d+)")
ALIAS_KEYWORDS = {"order", "limit", "final", "sample", "tablesample", "for", "fetch", "offset", "at", "before", "where"}


# ----------------------------------------------------------------------------------------------- helpers
def strip_sql(sql):
    sql = re.sub(r"/\*.*?\*/", " ", sql or "", flags=re.S)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return re.sub(r"\s+", " ", sql).strip().rstrip(";").strip()


def guard_select(sql, name="query"):
    """Allow only one read-only SELECT/WITH statement."""
    s = re.sub(r"'(?:[^']|'')*'", "''", strip_sql(sql))          # drop string literals
    s = re.sub(r'"[^"]*"', '""', s)                                 # and quoted identifiers
    if not re.match(r"^(select|with)\b", s, re.I) or ";" in s:
        raise ValueError(f"{name}: only a single SELECT/WITH statement is allowed")
    if re.search(r"\b(insert|update|delete|merge|drop|alter|create|truncate|grant|revoke|copy|call|do|execute|set|lock|"
                 r"vacuum|analyze|refresh|listen|notify|into)\b|\bpg_(?!is_in_recovery\b)\w+\s*\(|\bset_config\s*\(|\blo_\w+\s*\(|\bdblink", s, re.I):
        raise ValueError(f"{name}: statement contains a write or side-effecting keyword")


class Mb:
    def __init__(self, profile, mb_bin="mb", tmp="."):
        self.profile, self.bin, self.tmp = profile, mb_bin, tmp
        self._n = 0
        self._lock = threading.Lock()

    def json(self, *args):
        cmd = [self.bin, *args, "--profile", self.profile, "--json", "--max-bytes", "0"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd)} -> exit {r.returncode}: {(r.stdout or r.stderr)[:500]}")
        return json.loads(r.stdout)

    def list_all(self, *args, page=1000):
        out, offset = [], 0
        while True:
            env = self.json(*args, "--limit", str(page), "--offset", str(offset))
            out.extend(env.get("data", []))
            if not env.get("has_more"):
                return out, env
            offset = env["next_offset"]

    def sql(self, db_id, sql, name):
        """Run one guarded read-only native query on db_id; rows as dicts (CSV export: no row cap, no cache)."""
        guard_select(sql, name)
        with self._lock:
            self._n += 1
            path = os.path.join(self.tmp, f"q_{name}_{self._n}.json")
        with open(path, "w") as f:
            json.dump({"lib/type": "mbql/query", "database": db_id,
                       "stages": [{"lib/type": "mbql.stage/native", "native": sql}]}, f)
        r = subprocess.run([self.bin, "query", "--file", path, "--export-format", "csv", "--profile", self.profile],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0 or r.stdout.lstrip().startswith("{\"ok\":false"):
            raise RuntimeError(f"SQL {name} failed: {(r.stdout or r.stderr)[:800]}")
        return list(csv.DictReader(io.StringIO(r.stdout, newline="")))


def rest_get(profile, path, log):
    """GET through mb_rest.mjs with the mb profile's credentials; None on any failure (callers treat None as unknown)."""
    helper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mb_rest.mjs")
    r = subprocess.run(["node", helper, "--profile", profile, "--log", log, "GET", path], capture_output=True, text=True, timeout=300)
    try:
        return json.loads(r.stdout).get("body") if r.returncode == 0 else None
    except ValueError:
        return None


def as_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def truthy(x):
    return x is True or str(x).lower() in ("true", "t", "1", "yes")


def parse_ts(x):
    if not x:
        return None
    m = re.match(r"(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d:\d\d)", str(x))
    return dt.datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}+00:00") if m else None


def loads(x):
    if isinstance(x, (dict, list)) or x is None:
        return x
    try:
        return json.loads(x)
    except (TypeError, ValueError):
        return None


def unquote(p):
    p = p.strip()
    return p[1:-1] if p[:1] in "\"`[" else p


# ----------------------------------------------------------------------------------------------- query parsing
def tags_list(tt):
    if isinstance(tt, dict):
        return [dict(v, name=k) if isinstance(v, dict) else {"name": k} for k, v in tt.items()]
    return [t for t in (tt or []) if isinstance(t, dict)]


def legacy_source(q):
    st = q.get("source-table")
    if isinstance(st, str) and st.startswith("card__"):
        return None, as_int(st[6:])
    return as_int(st), None


def normalize(dq):
    """Unify MBQL 5 and legacy dataset_query into a list of stages (innermost first)."""
    dq = loads(dq)
    if not isinstance(dq, dict):
        return {"fmt": "unknown", "stages": []}
    if "stages" in dq:
        stages = []
        for st in dq.get("stages") or []:
            if st.get("lib/type") == "mbql.stage/native" or "native" in st:
                stages.append({"kind": "native", "native": st.get("native") or "", "tags": tags_list(st.get("template-tags"))})
                continue
            joins = []
            for j in st.get("joins") or []:
                js = (j.get("stages") or [{}])[0]
                joins.append({"source_table": as_int(js.get("source-table")), "source_card": as_int(js.get("source-card"))})
            stages.append({"kind": "mbql", "source_table": as_int(st.get("source-table")), "source_card": as_int(st.get("source-card")),
                           "ops": {k for k in st if k not in IGNORED_KEYS and not k.endswith("-idents")} - {"joins"},
                           "joins": joins, "fields": st.get("fields") or []})
        return {"fmt": "mbql5", "stages": stages}
    if isinstance(dq.get("native"), dict):
        n = dq["native"]
        return {"fmt": "legacy", "stages": [{"kind": "native", "native": n.get("query") or "", "tags": tags_list(n.get("template-tags"))}]}
    chain, q = [], dq.get("query")
    while isinstance(q, dict):
        chain.append(q)
        q = q.get("source-query")
    stages = []
    for q in reversed(chain):
        if "native" in q and "source-table" not in q:
            stages.append({"kind": "native", "native": q.get("native") or "", "tags": tags_list(q.get("template-tags"))})
            continue
        t, c = legacy_source(q)
        joins = []
        for j in q.get("joins") or []:
            jt, jc = legacy_source(j)
            if isinstance(j.get("source-query"), dict):
                jt, jc = legacy_source(j["source-query"])
            joins.append({"source_table": jt, "source_card": jc})
        ops = {k for k in q if k not in IGNORED_KEYS and not k.endswith("-idents")} - {"joins"}
        stages.append({"kind": "mbql", "source_table": t, "source_card": c, "ops": ops, "joins": joins, "fields": q.get("fields") or []})
    return {"fmt": "legacy" if stages else "unknown", "stages": stages}


def all_card_refs(dq):
    """Every card a query reads: source-card, card__N, card template tags, {{#N}} outside SQL comments, at any depth."""
    refs = set()

    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "card" and "card-id" in x:
                refs.add(as_int(x["card-id"]))
            for k, v in x.items():
                if k == "source-card":
                    refs.add(as_int(v))
                elif k == "source-table" and isinstance(v, str) and v.startswith("card__"):
                    refs.add(as_int(v[6:]))
                elif k in ("native", "query") and isinstance(v, str):
                    refs.update(int(n) for n in CARD_TAG_RE.findall(strip_sql(v)))
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(loads(dq))
    refs.discard(None)
    return refs


def comment_only_card_tags(norm):
    out = set()
    for st in norm["stages"]:
        if st["kind"] == "native":
            live = {int(n) for n in CARD_TAG_RE.findall(strip_sql(st["native"]))}
            out |= {as_int(t.get("card-id")) for t in st["tags"] if t.get("type") == "card" and as_int(t.get("card-id")) not in live}
    out.discard(None)
    return out


def has_implicit_join_fields(st):
    return '"source-field"' in json.dumps(st.get("fields") or [])


def mbql_wrapper(norm):
    """True when the query is one MBQL stage with only fields/order-by/limit and no joins or implicit joins."""
    if len(norm["stages"]) != 1:
        return False
    st = norm["stages"][0]
    return st["kind"] == "mbql" and not st["joins"] and st["ops"] <= WRAPPER_OPS and not has_implicit_join_fields(st)


def parse_select_star(sql):
    """Return (relation parts, confidence, notes) for a native single-table wrapper, else None.
    Rejects joins, filters, grouping, CTEs, renames (`a AS b`), literals and expressions."""
    s = strip_sql(sql)
    if not s or "{{" in s:
        return None
    if SQL_REJECT.search(re.sub(r'"[^"]*"|`[^`]*`|\[[^\]]*\]', " x ", s)):
        return None
    m = SELECT_RE.match(s)
    if not m:
        return None
    alias = (m.group("alias") or "").lower()
    if alias in ALIAS_KEYWORDS:
        return None
    cols, notes, conf = m.group("cols").strip(), [], "high"
    rel_last = unquote(re.findall(IDENT, m.group("rel"))[-1]).lower()
    star = cols == "*" or re.fullmatch(rf"(?:{IDENT}\s*\.\s*)*\*", cols)
    if not star:
        if "(" in cols:
            return None
        for c in cols.split(","):
            c = c.strip()
            mm = re.fullmatch(rf"(?:{IDENT}\s*\.\s*){{0,3}}(?P<col>{IDENT})(?:\s+as\s+(?P<al>{IDENT}))?", c, re.I)
            if not mm or (not mm.group("col").startswith(('"', "`", "[")) and mm.group("col").lower() in ("true", "false", "null")):
                return None
            if mm.group("al"):
                a, col = mm.group("al"), mm.group("col")
                quoted = a[:1] in "\"`[" or col[:1] in "\"`["
                if (unquote(a) != unquote(col)) if quoted else (unquote(a).lower() != unquote(col).lower()):
                    return None  # a rename: the swap would lose the column name
        conf, notes = "medium", notes + ["column list"]
    elif cols != "*" and alias and not re.fullmatch(rf"{re.escape(alias)}\s*\.\s*\*", cols, re.I) and not cols.lower().startswith(rel_last):
        return None
    if m.group("order"):
        notes.append("ORDER BY dropped by a swap")
    if m.group("limit"):
        conf, notes = "medium", notes + ["LIMIT dropped by a swap: semantics change"]
    parts = [q for p in re.findall(IDENT, m.group("rel")) for q in (unquote(p).split(".") if p.startswith("`") else [unquote(p)])]
    return parts, conf, notes


def column_keys(result_metadata):
    rm = loads(result_metadata) or []
    keys, fks, flags = [], [], set()
    for c in rm:
        if not isinstance(c, dict):
            continue
        k = c.get("lib/desired-column-alias") or c.get("name")
        if not k:
            continue
        keys.append({"key": k, "display_name": c.get("display_name"), "semantic_type": c.get("semantic_type"),
                     "description": c.get("description"), "fk_target_field_id": c.get("fk_target_field_id")})
        if c.get("semantic_type") == "type/FK":
            fks.append({"key": k, "fk_target_field_id": c.get("fk_target_field_id")})
        if len(k.encode()) >= 60 or re.search(r"_[0-9a-f]{8}$", k):
            flags.add("long-or-truncated-column-keys")
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", k):
            flags.add("non-snake-column-keys")
        if "__via__" in k:
            flags.add("implicit-join-columns")
    return keys, fks, sorted(flags)


def precheck_target(m, fields_by_table):
    """Predict check-replace-source failures and user-visible metadata changes for a swap onto m's target table."""
    t = m.get("target_table_id")
    if not t or t not in fields_by_table:
        return
    fields = {f["name"]: f for f in fields_by_table[t] if truthy(f.get("active", True))}
    missing, fk_gaps, fk_mismatch, diffs = [], [], [], collections.Counter()
    for c in m.get("column_keys") or []:
        f = fields.get(c["key"])
        if f is None:
            missing.append(c["key"])
            continue
        if c.get("semantic_type") == "type/FK":
            if f.get("semantic_type") != "type/FK":
                fk_gaps.append(c["key"])
            elif c.get("fk_target_field_id") and as_int(f.get("fk_target_field_id")) != as_int(c.get("fk_target_field_id")):
                fk_mismatch.append(c["key"])
        for attr in ("display_name", "semantic_type", "description"):
            if c.get(attr) and c.get(attr) != f.get(attr):
                diffs[attr] += 1
    m["missing_on_target"], m["fk_gaps"], m["fk_mismatch"] = missing, fk_gaps, fk_mismatch
    m["n_missing_on_target"], m["n_fk_gaps"] = len(missing), len(fk_gaps) + len(fk_mismatch)
    m["metadata_diffs"] = ",".join(f"{k}:{v}" for k, v in sorted(diffs.items()))
    flags = set(m.get("flags") or [])
    if missing:
        flags.add(f"swap-check-fails: {len(missing)} model columns missing on the table")
    if fk_gaps or fk_mismatch:
        flags.add("needs FK metadata on the table before the swap")
    m["flags"] = sorted(flags)


# ----------------------------------------------------------------------------------------------- classification
def reachable_models(refs, cards_meta):
    """Models reached from refs, following saved questions (non-models) transitively."""
    out, stack, seen = set(), list(refs), set()
    while stack:
        r = stack.pop()
        if r in seen:
            continue
        seen.add(r)
        k = cards_meta.get(r) or {}
        if k.get("type") == "model":
            out.add(r)
        else:
            stack.extend(k.get("refs") or ())
    return out


def classify(m, tables, resolve_native, cards_meta, dbs):
    norm = normalize(m["dataset_query"])
    m["fmt"], m["n_stages"] = norm["fmt"], len(norm["stages"])
    st0 = norm["stages"][0] if norm["stages"] else {"kind": "unknown"}
    refs = all_card_refs(m["dataset_query"])
    m["card_refs"] = sorted(refs)
    m["upstream_models"] = sorted(reachable_models(refs, cards_meta))
    m["ops"] = ",".join(sorted(st0.get("ops") or [])) if st0.get("kind") == "mbql" else ""
    tags = [t for s in norm["stages"] if s["kind"] == "native" for t in s["tags"]]
    m["has_snippet"] = any(t.get("type") == "snippet" for t in tags)
    params = [t for t in tags if t.get("type") in PARAM_TAG_TYPES]
    m["has_params"] = bool(params)
    m["required_params_without_default"] = any(truthy(t.get("required")) and t.get("default") in (None, "", []) for t in params)
    notes, flags = [], set(m.get("column_flags") or [])
    if comment_only_card_tags(norm):
        flags.add("card-tag-only-in-comment (drop the stale tag before materializing)")
    target = None
    if refs:
        cls = "T6"
        kinds = {r: cards_meta.get(r) for r in refs}
        if any(k is None for k in kinds.values()):
            flags.add("upstream-card-missing")
        if any(k and k.get("unreadable") for k in kinds.values()):
            flags.add("upstream-card-unreadable")
        if any(k and truthy(k.get("archived")) for k in kinds.values()):
            flags.add("upstream-card-archived")
        if any(k and k.get("type") not in ("model", None) for k in kinds.values()):
            flags.add("reads-saved-question (inline it in the transform)")
        # wrapper of a single saved question that itself wraps one table -> swap straight to that table
        only = next(iter(refs)) if len(refs) == 1 else None
        up = kinds.get(only) if only else None
        native_wrap = st0.get("kind") == "native" and len(norm["stages"]) == 1 and CARD_SELECT_RE.match(strip_sql(st0.get("native")))
        if up and up.get("type") not in ("model", None) and up.get("wrapper_table") and (native_wrap or (
                mbql_wrapper(norm) and st0.get("source_card") == only)):
            target = up["wrapper_table"]
            notes.append(f"wraps saved question {only}, itself a wrapper of table {target}")
    elif st0.get("kind") == "native" and len(norm["stages"]) == 1:
        p = parse_select_star(st0.get("native") or "")
        table_tags = [t for t in st0["tags"] if t.get("type") == "table" and t.get("table-id")]
        if p is None and len(table_tags) == 1 and re.fullmatch(r"select \* from \{\{\s*\w+\s*\}\}", strip_sql(st0["native"]), re.I):
            p, target = ([], "high", []), as_int(table_tags[0]["table-id"])
        if p is None:  # derived SQL over a single transform output? suggest extending that transform
            mfrom = re.findall(rf"\bfrom\s+({REL})", strip_sql(st0.get("native") or ""), re.I)
            if len(set(x.lower() for x in mfrom)) == 1 and not re.search(r"\bjoin\b", strip_sql(st0.get("native") or ""), re.I):
                parts0 = [unquote(x) for x in re.findall(IDENT, mfrom[0])]
                t0, _ = resolve_native(m["database_id"], parts0)
                if t0 and (tables.get(t0) or {}).get("transform_id"):
                    flags.add(f"builds on transform {tables[t0]['transform_id']}'s output (consider extending that transform)")
        if p:
            parts, conf, pnotes = p
            if target is None:
                target, rnote = resolve_native(m["database_id"], parts)
                if rnote:
                    conf, pnotes = "low", pnotes + [rnote]
            notes += pnotes
            if any(n.startswith("LIMIT") for n in pnotes):
                flags.add("limit-wrapper")
            if target is None:
                cls, conf = "T2", "unresolved"
                flags.add("source-table-not-in-metabase-metadata")
            else:
                tb = tables.get(target, {})
                cls = "T3" if truthy(tb.get("is_upload")) else ("T7" if tb.get("transform_id") or truthy(tb.get("transform_target")) else "T2")
            m["native_parse_confidence"] = conf
        else:
            cls = "T5"
    elif st0.get("kind") == "native":
        cls = "T5"   # native stage wrapped by MBQL stages: derived
    elif st0.get("kind") == "mbql":
        tid = st0.get("source_table")
        tb = tables.get(tid, {})
        wrapper = mbql_wrapper(norm)
        if "limit" in st0["ops"] and wrapper:
            notes.append("LIMIT dropped by a swap: semantics change")
            flags.add("limit-wrapper")
        if "order-by" in st0["ops"] and wrapper:
            flags.add("order-by-wrapper (dependents lose the model's sort)")
        if not wrapper and tb.get("transform_id"):
            flags.add(f"builds on transform {tb.get('transform_id')}'s output (consider extending that transform)")
        if not wrapper and tb.get("coerced"):
            flags.add("source has coerced columns (" + ",".join(tb["coerced"][:5]) + "): cast them in the transform")
        if truthy(tb.get("is_upload")):
            cls, target = "T3", (tid if wrapper else None)
        elif wrapper and (tb.get("transform_id") or truthy(tb.get("transform_target"))):
            cls, target = "T7", tid
        elif wrapper:
            cls, target = "T1", tid
        else:
            cls = "T4"
    else:
        cls = "unknown"
    src = tables.get(target) if target else (tables.get(st0.get("source_table")) if st0.get("kind") == "mbql" else None)
    if src is not None and not truthy(src.get("active", True)):
        flags.add("source-table-inactive")
    if target:
        tb = tables.get(target, {})
        m.update(target_table_id=target, target_table=f"{tb.get('schema') or ''}.{tb.get('name') or ''}".strip("."),
                 target_published=truthy(tb.get("is_published")), target_collection_id=tb.get("collection_id"),
                 target_data_layer=tb.get("data_layer"))
    m["class"], m["notes"], m["flags"] = cls, "; ".join(notes), sorted(flags)
    db = dbs.get(m["database_id"]) or {}
    m["db_transforms_ok"], m["db_transforms_reason"] = db_transform_support(db)
    if target:
        pass  # swaps don't write to the warehouse
    elif m["db_transforms_ok"] and truthy(db.get("is_app_db")):
        m["flags"] = sorted(set(m["flags"]) | {"target db is this instance's own application database (confirm a dedicated schema once)"})
    elif m["db_transforms_ok"] and db.get("n_transforms") == 0:
        m["flags"] = sorted(set(m["flags"]) | {"no transform writes to this database yet (prove a writable schema first)"})
    return m


def db_transform_support(db):
    if not db:
        return False, "database unknown"
    if truthy(db.get("is_audit")) or db.get("id") == AUDIT_DB_ID:
        return False, "audit (usage analytics) database"
    if truthy(db.get("is_sample")):
        return False, "sample database"
    if db.get("router_user_attribute") or db.get("router_database_id") or truthy(db.get("has_router")):
        return False, "database routing"
    feats = db.get("features")
    if isinstance(feats, list):
        return ("transforms/table" in feats), ("ok" if "transforms/table" in feats else f"engine {db.get('engine')} lacks transforms/table")
    ok = db.get("engine") in TRANSFORM_ENGINES
    return ok, "ok (by engine)" if ok else f"engine {db.get('engine')} has no query transforms"


def propose(models, stale_days, now, extras_known):
    by_id = {m["id"]: m for m in models}

    def depth(mid, seen=()):
        m = by_id[mid]
        if "wave" in m:
            return m["wave"]
        ups = [r for r in m.get("upstream_models") or [] if r not in seen and r != mid]
        m["wave"] = 0 if not ups else 1 + max((depth(u, seen + (mid,)) if u in by_id else 0) for u in ups)
        return m["wave"]
    for mid in by_id:
        depth(mid)
    shared = collections.defaultdict(list)
    for m in models:
        if m.get("target_table_id"):
            shared[m["target_table_id"]].append(m["id"])
    for m in models:  # first pass: everything except T6 waiting on upstreams
        m["flags"] = set(m["flags"])
        if any(u not in by_id for u in m.get("upstream_models") or []):
            m["flags"].add("upstream-model-outside-this-run")
        used, created = parse_ts(m.get("last_used_at")), parse_ts(m.get("created_at"))
        m["days_since_used"] = (now - used).days if used else None
        age = (now - created).days if created else None
        stale = (m["days_since_used"] >= stale_days) if used else (age is None or age >= stale_days)
        if m.get("n_subscriptions") is None and m.get("n_dashcards") == 0:
            m["n_subscriptions"] = 0      # subscriptions only carry cards that sit on a dashboard
        if m.get("n_action_buttons") is None and m.get("n_actions_any_state") == 0:
            m["n_action_buttons"] = 0     # no actions, no action buttons
        direct = [m.get(k) for k in ("n_dashcards", "n_alerts", "n_subscriptions", "n_filter_sources", "n_sandboxes",
                                     "n_actions_any_state", "n_action_buttons")]
        unknown_direct = any(v is None for v in direct)
        unused = stale and int(m.get("n_dependents_active") or 0) == 0 and sum(int(v or 0) for v in direct) == 0
        if m.get("target_table_id") and len(shared[m["target_table_id"]]) > 1:
            m["flags"].add("shares-table-with:" + ",".join(str(x) for x in shared[m["target_table_id"]] if x != m["id"]))
        if int(m.get("n_sandboxes") or 0) > 0:
            m["flags"].add("used-as-sandbox-card (rebuild the policy before anything else)")
        if m.get("archived"):
            still_used = [k for k in ("n_action_buttons", "n_sandboxes", "n_filter_sources") if int(m.get(k) or 0) > 0]
            if int(m.get("n_dependents_active") or 0) > 0:
                m["action"] = "swap-archived-feeder: it still serves active content"
            elif still_used:
                m["action"] = f"review: archived, but still used by {', '.join(k[2:] for k in still_used)}"
            else:
                m["action"] = "purge-candidate: already archived, no active dependents" + ("" if not unknown_direct else " (direct-use counts incomplete: verify)")
        elif m.get("collection_type") == "instance-analytics":
            m["action"] = "exclude: Metabase-managed usage analytics"
        elif m["class"] == "unknown":
            m["action"] = "review: unparsed dataset_query"
        elif m["flags"] & {"source-table-inactive", "upstream-card-missing"}:
            m["action"] = "broken: archive or repair"
        elif "upstream-card-unreadable" in m["flags"]:
            m["action"] = "review: an upstream card could not be read"
        elif unused:
            m["action"] = "archive: unused" + (" (direct-use counts incomplete: verify)" if (unknown_direct or not extras_known) else "")
        elif m["class"] == "T6" and m["wave"] > 0 and not m.get("target_table_id"):
            m["action"] = None  # decided below, once upstream actions are known
        elif m.get("target_table_id") and "limit-wrapper" in m["flags"]:
            m["action"] = "review: LIMIT wrapper (a swap returns every row of the table)"
        elif m.get("target_table_id"):
            m["action"] = "swap-to-existing-table" + (" (via saved question)" if m["class"] == "T6" else "")
        elif m["class"] == "T2":
            m["action"] = "verify-source-table (sync it or fix the parse)"
        elif "used-as-sandbox-card (rebuild the policy before anything else)" in m["flags"]:
            m["action"] = "blocked: sandbox card (rebuild the policy first)"
        elif m["db_transforms_ok"]:
            m["action"] = "create-transform" + (" (inline the upstream saved question)" if m["class"] == "T6" else "")
            if m.get("required_params_without_default"):
                m["flags"].add("required-parameter-without-default (make optional before materializing)")
        else:
            m["action"] = f"blocked: {m['db_transforms_reason']}"
    changed = True
    while changed:  # archived chains: don't purge what an archived feeder still reads
        changed = False
        for m in models:
            if str(m.get("action")).startswith("swap-archived-feeder") or str(m.get("action")).startswith("wait:"):
                for u in m.get("upstream_models") or []:
                    um = by_id.get(u)
                    if um and um.get("archived") and str(um.get("action")).startswith("purge-candidate"):
                        um["action"] = f"wait: archived model {m['id']} built on it still serves live content"
                        changed = True
    for m in sorted(models, key=lambda x: x["wave"]):  # second pass: T6 waiting on upstream models
        if m["action"] is None:
            ups = [by_id.get(u) for u in m["upstream_models"]]
            dead = [u for u in m["upstream_models"] if u in by_id and str(by_id[u]["action"]).startswith(("exclude", "blocked", "broken", "purge"))]
            if dead:
                m["action"] = f"blocked: upstream model(s) {dead} will not be migrated"
            elif not m["db_transforms_ok"] and not all(u and str(u["action"]).startswith("swap") for u in ups):
                m["action"] = f"blocked: {m['db_transforms_reason']}"
            else:
                m["action"] = f"after-upstream: re-classify in wave {m['wave']}"
        m["flags"] = sorted(m["flags"])


# ----------------------------------------------------------------------------------------------- API path
def collect_api(mbc, args, failures):
    log = os.path.join(args.out, "rest-log.jsonl")
    dbs = {d["id"]: d for d in mbc.list_all("db", "list", "--fields", "id,name,engine,is_audit,is_sample,router_database_id,router_user_attribute")[0]}
    try:
        dbs[AUDIT_DB_ID] = mbc.json("db", "get", str(AUDIT_DB_ID), "--fields", "id,name,engine,is_audit,is_sample")
    except RuntimeError:
        pass
    capped = []
    if args.ids:
        model_ids = [as_int(x) for x in args.ids.split(",")]
    else:
        model_ids = []
        targets = [as_int(x) for x in args.db_ids.split(",")] if args.db_ids else sorted(dbs)
        for did in targets:
            for archived in ([False, True] if args.include_archived else [False]):
                extra = ["--archived"] if archived else []
                try:
                    rows, _ = mbc.list_all("search", "--models", "dataset", "--db-id", str(did), "--include-dashboard-questions",
                                           *extra, "--fields", "id,database_id")
                except RuntimeError as e:
                    failures.append({"what": f"search db {did}", "error": str(e)[:300]})
                    continue
                if len(rows) >= 1000:
                    capped.append(did)
                model_ids += [r["id"] for r in rows]
        if AUDIT_DB_ID in targets or not args.db_ids:  # search hides the analytics namespace
            try:
                rows, _ = mbc.list_all("card", "list", "--filter", "database", "--model-id", str(AUDIT_DB_ID), "--fields", "id,type,archived")
                model_ids += [r["id"] for r in rows if r.get("type") == "model" and (args.include_archived or not r.get("archived"))]
            except RuntimeError as e:
                failures.append({"what": "audit database models", "error": str(e)[:300]})
    model_ids = sorted(set(model_ids))[: args.max_models or None]
    fields = ("id,entity_id,name,description,type,archived,query_type,database_id,table_id,collection_id,collection,"
              "dataset_query,result_metadata,persisted,cache_ttl,public_uuid,enable_embedding,last_used_at,created_at,view_count,"
              "display,moderation_reviews,creator.email,dashboard_count,parameter_usage_count")

    def fetch(mid):
        c = mbc.json("card", "get", str(mid), "--fields", fields)
        if c.get("type") != "model":
            return c, None, {}
        cnt = collections.Counter()
        if args.no_deps:
            rows, _ = mbc.list_all("card", "list", "--filter", "using_model", "--model-id", str(mid), "--fields", "id,type")
            for d in rows:
                cnt[f"card:{d.get('type')}"] += 1
        else:
            try:
                deps = mbc.json("dependency", "dependents", "card", str(mid), "--include-personal-collections")
            except RuntimeError as e:
                if "response-shape" not in str(e):  # newer servers return kinds (e.g. "action") an older CLI rejects
                    raise
                body = rest_get(mbc.profile, f"/api/ee/dependencies/graph/dependents?id={mid}&type=card&include-personal-collections=true", log)
                if body is None:
                    raise
                deps = {"data": body}
            for d in deps.get("data", []):
                cnt[d["type"] if d["type"] != "card" else f"card:{(d.get('data') or {}).get('type')}"] += 1
        return c, cnt, (fetch_extras(mbc, mid, log) if args.extras else {})

    raw = {}
    with cf.ThreadPoolExecutor(args.workers) as ex:
        futs = {mid: ex.submit(fetch, mid) for mid in model_ids}
        for mid, fut in futs.items():
            try:
                c, cnt, extra = fut.result()
                if cnt is None:
                    failures.append({"what": f"card {mid}", "error": f"not a model (type {c.get('type')})"})
                    continue
                raw[mid] = (c, cnt, extra)
            except Exception as e:
                failures.append({"what": f"model {mid}", "error": str(e)[:300]})
    gtaps = rest_get(mbc.profile, "/api/mt/gtap", log) if args.extras else None
    sandbox_counts = collections.Counter(as_int(g.get("card_id")) for g in (gtaps or []) if isinstance(g, dict) and g.get("card_id"))
    for d in {c.get("database_id") for c, _, _ in raw.values()}:
        if d in dbs:
            try:
                dbs[d]["features"] = mbc.json("db", "get", str(d), "--fields", "features").get("features")
            except RuntimeError:
                pass
    coll_info, lock = {}, threading.Lock()

    def ancestors(coll):
        out = []
        for cid in [x for x in (coll.get("location") or "/").strip("/").split("/") if x]:
            with lock:
                if cid not in coll_info:
                    try:
                        coll_info[cid] = mbc.json("collection", "get", cid, "--fields", "name,personal_owner_id")
                    except RuntimeError:
                        coll_info[cid] = {"name": f"#{cid}"}
            out.append(coll_info[cid])
        return out

    models, src_tables, refs_needed = [], set(), set()
    for mid, (c, cnt, extra) in raw.items():
        keys, fks, cflags = column_keys(c.get("result_metadata"))
        coll = c.get("collection") or {}
        root = coll.get("id") == "root" or c.get("collection_id") is None
        anc = [] if root else ancestors(coll)
        verified = any(r.get("most_recent") and r.get("status") == "verified" for r in c.get("moderation_reviews") or [])
        m = {"id": mid, "entity_id": c.get("entity_id"), "name": c.get("name"), "description": c.get("description"),
             "archived": truthy(c.get("archived")), "database_id": c.get("database_id"), "query_type": c.get("query_type"),
             "dataset_query": c.get("dataset_query"), "collection_id": c.get("collection_id"),
             "collection_path": "(root)" if root else " / ".join([a.get("name") or "" for a in anc] + [coll.get("name") or ""]),
             "collection_type": None if root else coll.get("type"),
             "in_personal_collection": (not root) and (truthy(coll.get("is_personal")) or bool(coll.get("personal_owner_id"))
                                                       or any(a.get("personal_owner_id") for a in anc)),
             "collection_remote_synced": truthy(coll.get("is_remote_synced")), "creator_email": (c.get("creator") or {}).get("email"),
             "last_used_at": c.get("last_used_at"), "created_at": c.get("created_at"), "view_count": c.get("view_count"),
             "display": c.get("display"), "verified": verified, "persisted": truthy(c.get("persisted")), "cache_ttl": c.get("cache_ttl"),
             "is_public": bool(c.get("public_uuid")), "embedding": truthy(c.get("enable_embedding")),
             "n_dependents_active": sum(cnt.values()), "n_dependents_archived": None, "n_dep_questions": cnt["card:question"],
             "n_dep_models": cnt["card:model"], "n_dep_metrics": cnt["card:metric"], "n_dep_dashboards": cnt["dashboard"],
             "n_dep_transforms": cnt["transform"],
             "n_dep_other": sum(v for k, v in cnt.items() if k not in {"card:question", "card:model", "card:metric", "dashboard", "transform"}),
             "n_filter_sources": c.get("parameter_usage_count"), "n_dashcards": c.get("dashboard_count"),
             "n_sandboxes": (sandbox_counts.get(mid, 0) if gtaps is not None else None),
             "n_alerts": None, "n_subscriptions": None, "n_bookmarks": None, "n_actions_any_state": None, "n_action_buttons": None,
             "column_keys": keys, "fk_columns": fks, "column_flags": cflags, **extra}
        src_tables |= {st["source_table"] for st in normalize(c.get("dataset_query"))["stages"] if st["kind"] == "mbql" and st.get("source_table")}
        refs_needed |= all_card_refs(c.get("dataset_query"))
        models.append(m)

    tfields = "id,name,schema,db_id,active,is_upload,transform_id,transform_target,is_published,collection_id,data_layer,display_name"
    tables = {}

    def get_table(t):
        if t not in tables:
            try:
                tables[t] = mbc.json("table", "get", str(t), "--fields", tfields)
            except RuntimeError as e:
                failures.append({"what": f"table {t}", "error": str(e)[:200]})
        return tables.get(t)
    for t in src_tables:
        get_table(t)
    try:
        per_db = collections.Counter(as_int(((t.get("target") or {}).get("database")) or t.get("source_database_id"))
                                     for t in mbc.list_all("transform", "list", "--fields", "id,target,source_database_id")[0])
        for d in dbs:
            dbs[d]["n_transforms"] = per_db.get(d, 0)
    except RuntimeError as e:
        failures.append({"what": "transform list", "error": str(e)[:200]})
    for m in models:
        n = normalize(m["dataset_query"])
        t = n["stages"][0].get("source_table") if n["stages"] and n["stages"][0]["kind"] == "mbql" and not mbql_wrapper(n) else None
        if t and get_table(t) is not None and "coerced" not in tables[t]:
            try:
                fl = mbc.list_all("table", "fields", str(t), "--fields", "name,active,coercion_strategy")[0]
                tables[t]["coerced"] = [f["name"] for f in fl if f.get("coercion_strategy") and truthy(f.get("active", True))]
            except RuntimeError:
                tables[t]["coerced"] = []
    cards_meta = {m["id"]: {"type": "model", "archived": m["archived"]} for m in models}
    frontier = refs_needed - set(cards_meta)
    while frontier:  # follow saved questions transitively so models reached through them are found
        nxt = set()
        for r in sorted(frontier):
            try:
                k = mbc.json("card", "get", str(r), "--fields", "id,type,archived,database_id,dataset_query")
            except RuntimeError as e:
                cards_meta[r] = None if "404" in str(e) or "not found" in str(e).lower() else {"type": None, "unreadable": True}
                continue
            k["refs"] = sorted(all_card_refs(k.get("dataset_query")))
            n = normalize(k.get("dataset_query"))
            if k.get("type") != "model" and mbql_wrapper(n) and n["stages"][0].get("source_table"):
                k["wrapper_table"] = n["stages"][0]["source_table"]
                get_table(k["wrapper_table"])
            k.pop("dataset_query", None)
            cards_meta[r] = k
            nxt |= set(k["refs"])
        frontier = nxt - set(cards_meta)
    name_cache = {}

    def resolve_native(db_id, parts):
        key = (db_id, parts[-1].lower())
        if key not in name_cache:
            try:
                rows, _ = mbc.list_all("table", "list", "--db-id", str(db_id), "--term", parts[-1], "--fields", tfields)
            except RuntimeError:
                rows = []
            name_cache[key] = rows
        return pick_table(name_cache[key], parts, tables)

    for m in models:
        classify(m, tables, resolve_native, cards_meta, dbs)
    fields_by_table = {}
    for t in {m["target_table_id"] for m in models if m.get("target_table_id")}:
        try:
            fields_by_table[t] = mbc.list_all("table", "fields", str(t), "--fields",
                                              "id,name,active,semantic_type,fk_target_field_id,display_name,description")[0]
        except RuntimeError as e:
            failures.append({"what": f"fields of table {t}", "error": str(e)[:200]})
    for m in models:
        precheck_target(m, fields_by_table)
    if args.extras:
        policies = rest_get(mbc.profile, "/api/cache?model=root&model=database", log) or {}
        db_policy = {as_int(p.get("model_id")): json.dumps(p.get("strategy")) for p in policies.get("data", []) if p.get("model") == "database"}
        for m in models:
            m["db_cache_policy"] = db_policy.get(m["database_id"], "")
    caveats = ["API path: bookmarks, subscriptions and archived dependents are not counted; dependents are direct and active only",
               "`n_dashcards` is the card's dashboard_count (archived dashboards included); `n_filter_sources` is parameter_usage_count",
               "cache policies of the dashboards and questions that use each model are not collected (app-DB path does)"]
    if not args.extras:
        caveats.append("actions, action buttons, model indexes, cache configs, alerts and sandboxes not collected (use --extras)")
    if args.no_deps:
        caveats.append("--no-deps: dependents are cards found by `card list --filter using_model` (same database, unarchived) only")
    if capped:
        caveats.append(f"search returned 1000 models for databases {capped}: results may be capped; split by collection")
    return models, dbs, caveats, bool(args.extras) and gtaps is not None


def pick_table(cands, parts, tables):
    """Resolve [..schema, name] to one active table id; returns (id or None, note or None)."""
    name = parts[-1].lower()
    cands = [t for t in cands if (t.get("name") or "").lower() == name and truthy(t.get("active", True))]
    note = None
    if len(parts) >= 2:
        exact = [t for t in cands if (t.get("schema") or "").lower() == parts[-2].lower()]
        if not exact:
            exact = [t for t in cands if not t.get("schema")]  # MySQL / some ClickHouse tables have no schema in Metabase
            note = "matched a table with no schema in Metabase metadata" if exact else None
        cands = exact
    if len(cands) > 1:
        cands = [t for t in cands if (t.get("schema") or "").lower() in ("public", "dbo")]
        note = "ambiguous unqualified name: picked the public/dbo table"
    if len(cands) == 1:
        tables[as_int(cands[0]["id"])] = cands[0]
        return as_int(cands[0]["id"]), note
    return None, None


def fetch_extras(mbc, mid, log):
    out = {}
    acts = rest_get(mbc.profile, f"/api/action?model-id={mid}", log)
    arch = rest_get(mbc.profile, f"/api/action?model-id={mid}&archived=true", log)
    if acts is None or arch is None:
        out.update(n_actions=None, n_implicit_actions=None, n_actions_any_state=None)
    else:
        live = [a for a in acts if isinstance(a, dict)]
        out.update(n_actions=len(live), n_implicit_actions=sum(1 for a in live if a.get("type") == "implicit"),
                   n_actions_any_state=len({a.get("id") for a in live + [a for a in arch if isinstance(a, dict)]}))
    mi = rest_get(mbc.profile, f"/api/model-index?model_id={mid}", log)
    out["n_model_index"] = len(mi) if isinstance(mi, list) else None
    cache = rest_get(mbc.profile, f"/api/cache?model=question&id={mid}", log)
    rows = cache.get("data", []) if isinstance(cache, dict) else None
    out["cache_strategy"] = (json.dumps(rows[0].get("strategy")) if rows else "") if rows is not None else None
    try:
        out["n_alerts"] = len(mbc.json("card", "alerts", str(mid)).get("data", []))
    except RuntimeError:
        out["n_alerts"] = None
    return out


# ----------------------------------------------------------------------------------------------- app-DB path
def app_db_columns(mbc, db, tables):
    rows = mbc.sql(db, "select table_name, column_name from information_schema.columns where table_schema = current_schema() "
                       f"and table_name in ({','.join(repr(t) for t in tables)})", "probe")
    have = collections.defaultdict(set)
    for r in rows:
        have[r["table_name"]].add(r["column_name"])
    return have


def verify_app_db(mbc, db, sample_ids):
    """The connected app DB must be THIS instance's live primary: ids, names and entity ids match the API."""
    problems = []
    rows = {as_int(r["id"]): r for r in mbc.sql(db, f"select id, name, entity_id from report_card where id in ({','.join(map(str, sample_ids))})", "identity")}
    for i in sample_ids:
        try:
            c = mbc.json("card", "get", str(i), "--fields", "id,name,entity_id")
        except RuntimeError as e:
            problems.append(f"card {i} unreadable through the API: {str(e)[:100]}")
            continue
        r = rows.get(i)
        if not r or r["name"] != c.get("name") or r["entity_id"] != c.get("entity_id"):
            problems.append(f"card {i}: app DB says {r and (r['name'], r['entity_id'])}, API says {(c.get('name'), c.get('entity_id'))}")
    try:
        st = mbc.sql(db, "select pg_is_in_recovery() as replica, extract(epoch from now() - (select max(timestamp) from view_log)) as lag", "freshness")[0]
        if truthy(st.get("replica")):
            problems.append("the app DB connection points at a replica (pg_is_in_recovery): counts may lag")
        if st.get("lag") and float(st["lag"]) > 3600:
            problems.append(f"no view_log activity for {int(float(st['lag']))} s: is this a stale copy?")
    except (RuntimeError, ValueError):
        pass
    return problems


def collect_app_db(mbc, args, failures):
    db = args.app_db
    probe = ["report_card", "metabase_table", "metabase_table_user_settings", "metabase_field", "metabase_field_user_settings",
             "dependency", "card_bookmark", "notification_card", "pulse_card", "parameter_card", "sandboxes", "action",
             "model_index", "persisted_info", "cache_config", "moderation_review", "remote_sync_object", "metabot_prompt",
             "document", "transform", "report_dashboardcard", "report_dashboard", "dashboardcard_series", "collection",
             "metabase_database", "db_router", "segment", "measure", "view_log", "notification"]
    have = app_db_columns(mbc, db, probe)
    if "report_card" not in have:
        raise SystemExit(f"database {db} does not look like a Metabase application DB (no report_card)")
    where = "c.type = 'model'" + ("" if args.include_archived else " and not c.archived")
    if args.db_ids:
        where += f" and c.database_id in ({','.join(str(as_int(x)) for x in args.db_ids.split(','))})"
    if args.ids:
        where += f" and c.id in ({','.join(str(as_int(x)) for x in args.ids.split(','))})"
    models_rows, last = [], 0
    while True:  # keyset pages keep each request under the CLI's 30 s timeout
        b = mbc.sql(db, f"""
            select c.id, c.entity_id, c.name, c.description, c.archived, c.database_id, c.query_type, c.dataset_query, c.result_metadata,
                   c.collection_id, c.last_used_at, c.created_at, c.view_count, c.display, c.cache_ttl,
                   c.public_uuid is not null as is_public, c.enable_embedding, u.email as creator_email
            from report_card c left join core_user u on u.id = c.creator_id
            where {where} and c.id > {last} order by c.id limit 300""", "models")
        models_rows += b
        if len(b) < 300 or (args.max_models and len(models_rows) >= args.max_models):
            break
        last = as_int(b[-1]["id"])
    models_rows = models_rows[: args.max_models or None]
    ids = [as_int(r["id"]) for r in models_rows]
    if not ids:
        raise SystemExit("no models found")
    problems = verify_app_db(mbc, db, ids[:: max(1, len(ids) // 3)][:3])
    if problems:
        print("app DB identity/freshness problems:\n  " + "\n  ".join(problems), file=sys.stderr)
        if not args.allow_partial:
            raise SystemExit(3)
    idlist = ",".join(str(i) for i in ids)
    q = lambda name, sql: mbc.sql(db, sql, name)
    colls = {as_int(r["id"]): r for r in q("collections", "select id, name, location, type, personal_owner_id, "
                                         + ("is_remote_synced" if "is_remote_synced" in have["collection"] else "false as is_remote_synced")
                                         + " from collection")}
    dbs = {as_int(r["id"]): r for r in q("dbs", "select id, name, engine, is_audit, is_sample from metabase_database")}
    for r in dbs.values():
        r["id"] = as_int(r["id"])
    dbs.setdefault(db, {"id": db})["is_app_db"] = True
    if "db_router" in have:
        for r in q("routers", "select database_id from db_router"):
            if as_int(r["database_id"]) in dbs:
                dbs[as_int(r["database_id"])]["has_router"] = True
    for d in {as_int(r["database_id"]) for r in models_rows}:
        try:
            dbs[d]["features"] = mbc.json("db", "get", str(d), "--fields", "features").get("features")
        except (RuntimeError, KeyError):
            pass
    mt, u = have["metabase_table"], "metabase_table_user_settings" in have
    pub = "coalesce(u.is_published, t.is_published)" if u and "is_published" in mt else ("t.is_published" if "is_published" in mt else "false")
    coll = ("case when u.is_published is not null then u.collection_id else t.collection_id end" if u and "collection_id" in mt
            else ("t.collection_id" if "collection_id" in mt else "null"))
    layer = ("case when u.data_layer_set then u.data_layer else t.data_layer end" if u and "data_layer" in mt
             else ("t.data_layer" if "data_layer" in mt else "null"))
    tcols = ", ".join(f"t.{c}" if c in mt else f"null as {c}" for c in ("transform_id", "transform_target", "is_upload"))
    model_dbs = ",".join(str(d) for d in {as_int(r["database_id"]) for r in models_rows} if d is not None)
    tables = {}
    for r in q("tables", f"""
        select t.id, t.db_id, t.schema, t.name, t.active, {tcols}, {pub} as is_published, {coll} as collection_id, {layer} as data_layer
        from metabase_table t {"left join metabase_table_user_settings u on u.table_id = t.id" if u else ""}
        where t.db_id in ({model_dbs})"""):
        r["id"], r["transform_id"] = as_int(r["id"]), as_int(r.get("transform_id"))
        tables[r["id"]] = r

    if "transform" in have and "target_db_id" in have["transform"]:
        per_db = {as_int(r["db"]): as_int(r["n"]) for r in q("transforms_per_db", "select target_db_id db, count(*) n from transform group by 1")}
        for d in dbs:
            dbs[d]["n_transforms"] = per_db.get(d, 0)
    derived_src = set()
    for r in models_rows:
        n = normalize(r["dataset_query"])
        if n["stages"] and n["stages"][0]["kind"] == "mbql" and not mbql_wrapper(n) and n["stages"][0].get("source_table"):
            derived_src.add(n["stages"][0]["source_table"])
    if derived_src and "metabase_field" in have:
        fu = "metabase_field_user_settings" in have and "coercion_strategy" in have["metabase_field_user_settings"]
        for r in q("coerced", f"""
            select f.table_id, f.name from metabase_field f {"left join metabase_field_user_settings u on u.field_id = f.id" if fu else ""}
            where f.active and {"coalesce(u.coercion_strategy, f.coercion_strategy)" if fu else "f.coercion_strategy"} is not null
              and f.table_id in ({",".join(str(t) for t in sorted(derived_src))})"""):
            t = tables.get(as_int(r["table_id"]))
            if t is not None:
                t.setdefault("coerced", []).append(r["name"])
    counts = collections.defaultdict(dict)
    live_dash = "join report_dashboard d on d.id = dc.dashboard_id and not d.archived"
    feature_sql = {
        "n_dashcards": ("report_dashboardcard", f"select dc.card_id id, count(*) n from report_dashboardcard dc {live_dash} where dc.card_id in ({idlist}) group by 1"),
        "n_series": ("dashboardcard_series", f"select s.card_id id, count(*) n from dashboardcard_series s join report_dashboardcard dc on dc.id = s.dashboardcard_id {live_dash} where s.card_id in ({idlist}) group by 1"),
        "n_action_buttons": ("action", f"select a.model_id id, count(*) n from report_dashboardcard dc join action a on a.id = dc.action_id {live_dash} where a.model_id in ({idlist}) group by 1"),
        "n_bookmarks": ("card_bookmark", f"select card_id id, count(*) n from card_bookmark where card_id in ({idlist}) group by 1"),
        "n_alerts": ("notification_card", (f"select nc.card_id id, count(*) n from notification_card nc join notification n on n.payload_id = nc.id "
                                           f"and n.payload_type = 'notification/card' and n.active where nc.card_id in ({idlist}) group by 1")
                     if "notification" in have else f"select card_id id, count(*) n from notification_card where card_id in ({idlist}) group by 1"),
        "n_subscriptions": ("pulse_card", f"select card_id id, count(*) n from pulse_card where card_id in ({idlist}) group by 1"),
        "n_filter_sources": ("parameter_card", f"select card_id id, count(*) n from parameter_card where card_id in ({idlist}) group by 1"),
        "n_sandboxes": ("sandboxes", f"select card_id id, count(*) n from sandboxes where card_id in ({idlist}) group by 1"),
        "n_actions": ("action", f"select model_id id, count(*) n from action where not archived and model_id in ({idlist}) group by 1"),
        "n_actions_any_state": ("action", f"select model_id id, count(*) n from action where model_id in ({idlist}) group by 1"),
        "n_implicit_actions": ("action", f"select model_id id, count(*) n from action where not archived and type = 'implicit' and model_id in ({idlist}) group by 1"),
        "n_model_index": ("model_index", f"select model_id id, count(*) n from model_index where model_id in ({idlist}) group by 1"),
        "n_metabot_prompts": ("metabot_prompt", f"select card_id id, count(*) n from metabot_prompt where card_id in ({idlist}) group by 1"),
        "persisted": ("persisted_info", f"select card_id id, 1 n from persisted_info where active and card_id in ({idlist})"),
        "verified": ("moderation_review", "select moderated_item_id id, 1 n from moderation_review where moderated_item_type = 'card' "
                                          f"and most_recent and status = 'verified' and moderated_item_id in ({idlist})"),
        "card_remote_synced": ("remote_sync_object", f"select model_id id, 1 n from remote_sync_object where model_type = 'Card' "
                                                     f"and status <> 'removed' and model_id in ({idlist})"),
    }
    missing = []
    for k, (table, sql) in feature_sql.items():
        if table not in have:
            missing.append(k)
            continue
        for r in q(k, sql):
            counts[as_int(r["id"])][k] = as_int(r["n"])
    db_policy = {}
    if "cache_config" in have:
        for r in q("cache", f"select model_id id, strategy, config from cache_config where model = 'question' and model_id in ({idlist})"):
            counts[as_int(r["id"])]["cache_strategy"] = f"{r['strategy']} {r['config']}"
        for r in q("dbcache", "select model, model_id, strategy, config from cache_config where model in ('database', 'root')"):
            db_policy["root" if r["model"] == "root" else as_int(r["model_id"])] = f"{r['strategy']} {r['config']}"
    deps = collections.defaultdict(collections.Counter)
    if "dependency" in have and not args.no_deps:
        joins = {"card": "report_card", "dashboard": "report_dashboard", "document": "document", "transform": "transform",
                 "action": "action", "segment": "segment", "measure": "measure"}
        present = {k: t for k, t in joins.items() if t in have}
        lj = "\n".join(f"left join {t} e_{k} on dp.from_entity_type = '{k}' and e_{k}.id = dp.from_entity_id" for k, t in present.items())
        alive = " or ".join(f"e_{k}.id is not null" for k in present)
        arch = "coalesce(" + ", ".join(f"e_{k}.archived" for k, t in present.items() if "archived" in have[t]) + ", false)"
        for r in q("deps", f"""
            select dp.to_entity_id id, dp.from_entity_type t, coalesce(e_card.type, '') ct, {arch} as archived, count(*) n
            from dependency dp {lj}
            where dp.to_entity_type = 'card' and dp.to_entity_id in ({idlist})
              and ({alive} or dp.from_entity_type not in ({",".join(repr(k) for k in present)}))
            group by 1, 2, 3, 4"""):
            key = r["t"] if r["t"] != "card" else f"card:{r['ct']}"
            deps[as_int(r["id"])][("archived:" if truthy(r["archived"]) else "") + key] += as_int(r["n"])
        if "cache_config" in have:  # freshness evidence: cache policies of the questions and dashboards that use the model
            for r in q("consumer_cache", f"""
                select dp.to_entity_id id, cc.model, cc.strategy, cc.config, count(*) n
                from dependency dp join cache_config cc on cc.model_id = dp.from_entity_id
                 and ((dp.from_entity_type = 'card' and cc.model = 'question') or (dp.from_entity_type = 'dashboard' and cc.model = 'dashboard'))
                where dp.to_entity_type = 'card' and dp.to_entity_id in ({idlist}) group by 1, 2, 3, 4"""):
                counts[as_int(r["id"])].setdefault("consumer_cache", []).append(f"{r['model']}:{r['strategy']} {r['config']} x{r['n']}")
    else:  # no dependency graph (no `dependencies` feature): scan query text for references instead
        missing.append("dependency graph: dependents counted by scanning card query text")
        for r in q("textdeps", f"""
            select (x.m)[1]::int id, c.type ct, c.archived, count(distinct c.id) n
            from report_card c, lateral regexp_matches(c.dataset_query, '(?:"source-card": ?|card__|\\{{\\{{ *#)([0-9]+)', 'g') as x(m)
            where (x.m)[1]::int in ({idlist}) group by 1, 2, 3"""):
            deps[as_int(r["id"])][("archived:" if truthy(r["archived"]) else "") + f"card:{r['ct']}"] += as_int(r["n"])

    referenced, cards_meta = set(), {i: {"type": "model", "archived": False} for i in ids}
    for r in models_rows:
        referenced |= all_card_refs(r["dataset_query"])
        cards_meta[as_int(r["id"])]["archived"] = truthy(r.get("archived"))
    frontier = referenced - set(cards_meta)
    while frontier:  # follow saved questions transitively so models reached through them are found
        rows = q("refcards", f"select id, type, archived, database_id, dataset_query from report_card where id in ({','.join(map(str, sorted(frontier)))})")
        found = set()
        for r in rows:
            k = {"type": r["type"], "archived": truthy(r["archived"]), "refs": sorted(all_card_refs(r["dataset_query"]))}
            n = normalize(r["dataset_query"])
            if r["type"] != "model" and mbql_wrapper(n) and n["stages"][0].get("source_table"):
                k["wrapper_table"] = n["stages"][0]["source_table"]
            cards_meta[as_int(r["id"])] = k
            found.add(as_int(r["id"]))
        for missing_id in frontier - found:
            cards_meta[missing_id] = None
        frontier = {x for r in found for x in cards_meta[r]["refs"]} - set(cards_meta)

    by_name = collections.defaultdict(list)
    for t in tables.values():
        by_name[(as_int(t["db_id"]), (t.get("name") or "").lower())].append(t)

    def resolve_native(db_id, parts):
        return pick_table(by_name.get((db_id, parts[-1].lower()), []), parts, tables)

    def chain(cid):
        c = colls.get(cid)
        return [as_int(x) for x in ((c or {}).get("location") or "/").strip("/").split("/") if x] + [cid] if c else []

    models = []
    for r in models_rows:
        mid = as_int(r["id"])
        keys, fks, cflags = column_keys(r.get("result_metadata"))
        cid = as_int(r.get("collection_id"))
        c, d = counts.get(mid, {}), deps.get(mid, collections.Counter())
        active = {k: v for k, v in d.items() if not k.startswith("archived:")}
        m = {"id": mid, "entity_id": r["entity_id"], "name": r["name"], "description": r.get("description"),
             "archived": truthy(r.get("archived")), "database_id": as_int(r["database_id"]), "query_type": r["query_type"],
             "dataset_query": loads(r["dataset_query"]), "collection_id": cid,
             "collection_path": " / ".join((colls.get(i) or {}).get("name") or f"#{i}" for i in chain(cid)) or "(root)",
             "collection_type": (colls.get(cid) or {}).get("type"),
             "in_personal_collection": any((colls.get(i) or {}).get("personal_owner_id") for i in chain(cid)),
             "collection_remote_synced": truthy((colls.get(cid) or {}).get("is_remote_synced")),
             "card_remote_synced": bool(c.get("card_remote_synced")), "creator_email": r.get("creator_email"),
             "last_used_at": r.get("last_used_at"), "created_at": r.get("created_at"), "view_count": as_int(r.get("view_count")),
             "display": r.get("display"), "verified": bool(c.get("verified")), "persisted": bool(c.get("persisted")),
             "cache_ttl": r.get("cache_ttl"), "cache_strategy": c.get("cache_strategy", ""),
             "consumer_cache": "; ".join(c.get("consumer_cache", [])),
             "db_cache_policy": db_policy.get(as_int(r["database_id"]), db_policy.get("root", "")),
             "is_public": truthy(r.get("is_public")), "embedding": truthy(r.get("enable_embedding")),
             "n_dependents_active": sum(active.values()), "n_dependents_archived": sum(v for k, v in d.items() if k.startswith("archived:")),
             "n_dep_questions": active.get("card:question", 0), "n_dep_models": active.get("card:model", 0),
             "n_dep_metrics": active.get("card:metric", 0), "n_dep_dashboards": active.get("dashboard", 0),
             "n_dep_transforms": active.get("transform", 0),
             "n_dep_other": sum(v for k, v in active.items() if k not in {"card:question", "card:model", "card:metric", "dashboard", "transform"}),
             "column_keys": keys, "fk_columns": fks, "column_flags": cflags,
             **{k: (c.get(k, 0) if k not in missing else None) for k in
                ("n_dashcards", "n_series", "n_action_buttons", "n_bookmarks", "n_alerts", "n_subscriptions", "n_filter_sources",
                 "n_sandboxes", "n_actions", "n_actions_any_state", "n_implicit_actions", "n_model_index", "n_metabot_prompts")}}
        classify(m, tables, resolve_native, cards_meta, dbs)
        models.append(m)
    targets = sorted({m["target_table_id"] for m in models if m.get("target_table_id")})
    fields_by_table = collections.defaultdict(list)
    if targets:
        fus = "metabase_field_user_settings" in have
        st = "case when u.semantic_type_set then u.semantic_type else f.semantic_type end" if fus else "f.semantic_type"
        fk = "case when u.fk_target_field_id_set then u.fk_target_field_id else f.fk_target_field_id end" if fus else "f.fk_target_field_id"
        dn = "coalesce(u.display_name, f.display_name)" if fus else "f.display_name"
        de = "case when u.description_set then u.description else f.description end" if fus else "f.description"
        for r in q("target_fields", f"""
            select f.table_id, f.name, f.active, {st} as semantic_type, {fk} as fk_target_field_id, {dn} as display_name, {de} as description
            from metabase_field f {"left join metabase_field_user_settings u on u.field_id = f.id" if fus else ""}
            where f.table_id in ({",".join(str(t) for t in targets)})"""):
            fields_by_table[as_int(r["table_id"])].append(r)
    for m in models:
        precheck_target(m, fields_by_table)
    caveats = [f"app-DB path (database {db}, PostgreSQL); counts are live rows at query time"]
    if missing:
        caveats.append("not available on this version: " + ", ".join(missing))
    return models, dbs, caveats, not missing


# ----------------------------------------------------------------------------------------------- output
CSV_COLS = ["id", "entity_id", "name", "archived", "class", "action", "wave", "target_table_id", "target_table", "target_published",
            "target_collection_id", "target_data_layer", "n_missing_on_target", "n_fk_gaps", "metadata_diffs", "database_id",
            "db_transforms_ok", "db_transforms_reason", "query_type", "fmt", "n_stages", "ops", "card_refs", "upstream_models",
            "has_snippet", "has_params", "native_parse_confidence", "collection_id", "collection_path", "collection_type",
            "in_personal_collection", "collection_remote_synced", "card_remote_synced", "creator_email", "created_at",
            "last_used_at", "days_since_used", "view_count", "display", "verified", "persisted", "cache_ttl", "cache_strategy",
            "consumer_cache", "db_cache_policy", "is_public", "embedding", "n_dependents_active", "n_dependents_archived",
            "n_dep_questions", "n_dep_models", "n_dep_metrics", "n_dep_dashboards", "n_dep_transforms", "n_dep_other",
            "n_dashcards", "n_series", "n_filter_sources", "n_alerts", "n_subscriptions", "n_bookmarks", "n_actions",
            "n_actions_any_state", "n_implicit_actions", "n_action_buttons", "n_model_index", "n_sandboxes", "n_metabot_prompts",
            "flags", "notes"]


def write_outputs(models, dbs, caveats, failures, out):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "models.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for m in sorted(models, key=lambda x: x["id"]):
            row = dict(m)
            for k in ("card_refs", "upstream_models"):
                row[k] = " ".join(str(x) for x in m.get(k) or [])
            row["flags"] = "; ".join(m.get("flags") or [])
            w.writerow(row)
    with open(os.path.join(out, "models.jsonl"), "w") as f:
        for m in models:
            f.write(json.dumps(m, default=str) + "\n")
    with open(os.path.join(out, "failures.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["what", "error"])
        w.writeheader()
        w.writerows(failures)
    by_id = {m["id"]: m for m in models}
    with open(os.path.join(out, "model_edges.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model_id", "upstream_card_id", "kind", "upstream_in_this_run"])
        for m in models:
            for r in m.get("card_refs") or []:
                w.writerow([m["id"], r, "direct", r in by_id])
            for r in set(m.get("upstream_models") or []) - set(m.get("card_refs") or []):
                w.writerow([m["id"], r, "model via saved question", r in by_id])
    C = collections.Counter
    head = lambda a: str(a).split(":")[0].split(" (")[0]
    lines = [f"# Model inventory ({len(models)} models{', ' + str(len(failures)) + ' UNREADABLE' if failures else ''})", "",
             "## What this run could not see", ""]
    lines += [f"- {c}" for c in caveats]
    if failures:
        lines.append(f"- **{len(failures)} items could not be read** (see failures.csv): resolve them before classifying")
    lines += ["", "## By class", "", "| class | models |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(C(m["class"] for m in models).items())]
    lines += ["", "## By proposed action", "", "| action | models |", "|---|---|"] + [f"| {k} | {v} |" for k, v in C(head(m["action"]) for m in models).most_common()]
    lines += ["", "## By database", "", "| db | name | transforms | models | swap | transform | after-upstream | archive | blocked |", "|---|---|---|---|---|---|---|---|---|"]
    per_db = collections.defaultdict(list)
    for m in models:
        per_db[m["database_id"]].append(m)
    for d, ms in sorted(per_db.items(), key=lambda kv: -len(kv[1])):
        a = C(head(m["action"]) for m in ms)
        lines.append(f"| {d} | {(dbs.get(d) or {}).get('name')} | {ms[0]['db_transforms_reason']} | {len(ms)} | {a['swap-to-existing-table']} | "
                     f"{a['create-transform']} | {a['after-upstream']} | {a['archive']} | {a['blocked']} |")
    swaps = [m for m in models if str(m["action"]).startswith("swap")]
    lines += ["", "## Swap readiness (predicted `check-replace-source` outcome)", "",
              f"- {len(swaps)} models propose a swap onto an existing table",
              f"- {sum(1 for m in swaps if m.get('n_missing_on_target'))} would fail: model columns missing on the table (long/truncated names, stale metadata, implicit-join columns): decide per model",
              f"- {sum(1 for m in swaps if m.get('n_fk_gaps'))} need FK metadata added to the table first",
              f"- {sum(1 for m in swaps if m.get('metadata_diffs'))} have column metadata that differs from the table (display names, semantic types, descriptions change for dependents): promote or accept",
              f"- {sum(1 for m in swaps if not m.get('target_published'))} target tables are not published yet",
              f"- {sum(1 for m in models if 'limit-wrapper' in (m.get('flags') or []))} wrappers have a LIMIT (a swap would return every row): review"]
    lines += ["", "## Waves (model-on-model depth)", "", " · ".join(f"wave {k}: {v}" for k, v in sorted(C(m["wave"] for m in models).items()))]
    num = lambda m, k: int(m.get(k) or 0) > 0
    feat = [("verified", lambda m: m.get("verified")), ("persisted", lambda m: m.get("persisted")),
            ("cache policy on the model", lambda m: bool(m.get("cache_strategy")) or bool(m.get("cache_ttl"))),
            ("consumers with cache policies", lambda m: bool(m.get("consumer_cache"))),
            ("with actions (any state)", lambda m: num(m, "n_actions_any_state") or num(m, "n_actions")),
            ("with dashboard action buttons", lambda m: num(m, "n_action_buttons")), ("with model index", lambda m: num(m, "n_model_index")),
            ("bookmarked", lambda m: num(m, "n_bookmarks")), ("with alerts", lambda m: num(m, "n_alerts")),
            ("in subscriptions", lambda m: num(m, "n_subscriptions")), ("on dashboards directly", lambda m: num(m, "n_dashcards")),
            ("used as a chart series", lambda m: num(m, "n_series")), ("filter value source", lambda m: num(m, "n_filter_sources")),
            ("sandbox card", lambda m: num(m, "n_sandboxes")), ("public link or embedding", lambda m: m.get("is_public") or m.get("embedding")),
            ("in personal collections", lambda m: m.get("in_personal_collection")),
            ("remote-synced", lambda m: m.get("collection_remote_synced") or m.get("card_remote_synced")),
            ("already archived", lambda m: m.get("archived"))]
    lines += ["", "## Model-only features in use", "", "| feature | models |", "|---|---|"] + [f"| {n} | {sum(1 for m in models if f(m))} |" for n, f in feat]
    flagc = C(fl.split(":")[0].split(" (")[0] for m in models for fl in m.get("flags") or [])
    lines += ["", "## Flags", "", "| flag | models |", "|---|---|"] + [f"| {k} | {v} |" for k, v in flagc.most_common()]
    top = sorted(models, key=lambda m: -(m.get("n_dependents_active") or 0))[:25]
    lines += ["", "## Top 25 by active direct dependents", "", "| id | name | class | action | dependents | dashboards | views |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {m['id']} | {m['name']} | {m['class']} | {m['action']} | {m.get('n_dependents_active')} | {m.get('n_dep_dashboards')} | {m.get('view_count')} |" for m in top]
    with open(os.path.join(out, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", help="output directory (required unless --sql)")
    ap.add_argument("--app-db", type=int, help="database id of the instance's own (PostgreSQL) application DB, if connected")
    ap.add_argument("--sql", help="with --app-db: run this one guarded SELECT and print CSV, then exit")
    ap.add_argument("--include-archived", action="store_true", help="also inventory models already in the Trash")
    ap.add_argument("--db-ids", help="only models on these database ids")
    ap.add_argument("--ids", help="only these model ids")
    ap.add_argument("--max-models", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stale-days", type=int, default=180)
    ap.add_argument("--extras", action="store_true", help="API path: also fetch actions, model indexes, cache config, alerts, sandboxes")
    ap.add_argument("--no-deps", action="store_true", help="instance without the dependencies feature: count dependents from query text")
    ap.add_argument("--allow-partial", action="store_true", help="exit 0 even when some models could not be read")
    ap.add_argument("--mb", default="mb")
    args = ap.parse_args()
    if args.sql:
        if not args.app_db:
            ap.error("--sql needs --app-db")
        tmp = os.path.join(args.out or "./.scratch/model-migration", "tmp")
        os.makedirs(tmp, exist_ok=True)
        rows = Mb(args.profile, args.mb, tmp).sql(args.app_db, open(args.sql).read(), "adhoc")
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()) if rows else ["(no rows)"])
        w.writeheader()
        w.writerows(rows)
        return
    if not args.out:
        ap.error("--out is required")
    os.makedirs(os.path.join(args.out, "tmp"), exist_ok=True)
    mbc = Mb(args.profile, args.mb, os.path.join(args.out, "tmp"))
    failures = []
    models, dbs, caveats, complete = (collect_app_db if args.app_db else collect_api)(mbc, args, failures)
    propose(models, args.stale_days, dt.datetime.now(dt.timezone.utc), complete)
    write_outputs(models, dbs, caveats, failures, args.out)
    print(json.dumps({"models": len(models), "unreadable": len(failures), "out": os.path.abspath(args.out),
                      "classes": collections.Counter(m["class"] for m in models), "caveats": caveats}, default=str))
    if failures and not args.allow_partial:
        sys.exit(3)


if __name__ == "__main__":
    main()
