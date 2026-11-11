"""
Cross-repo contract audit: zou routes and events against kitsu, gazu and
the developer documentation.

Run from the zou repo root, with the sibling repos next to it:

    SECRET_KEY=audit DB_DATABASE=zoudb-test CACHE_TYPE=simple \
        ~/.virtualenvs/zou/bin/python \
        ~/.claude/skills/contract-audit/scripts/contract_audit.py [out_dir]

Builds the zou app to read its real url_map (no request is made, the
database is not queried).
"""

import ast
import datetime
import json
import os
import re
import sys
from collections import defaultdict

WORKSPACE = os.path.dirname(os.getcwd())
KITSU = os.path.join(WORKSPACE, "kitsu", "src")
GAZU = os.path.join(WORKSPACE, "gazu", "gazu")
DOCS = os.path.join(WORKSPACE, "kitsu-developer-documentation", "docs")

KITSU_METHODS = {
    "get": "GET",
    "pget": "GET",
    "post": "POST",
    "ppost": "POST",
    "put": "PUT",
    "pput": "PUT",
    "del": "DELETE",
    "pdel": "DELETE",
    "patch": "PATCH",
    "ppatch": "PATCH",
}
PLACEHOLDER = "\x00"
EVENT_NAME = r"[a-z][a-z0-9-]*:[a-z][a-z0-9-]*"


def walk(root, extensions, skip=("node_modules", ".vitepress", "dist")):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for filename in filenames:
            if filename.endswith(extensions):
                path = os.path.join(dirpath, filename)
                yield path, open(path, encoding="utf-8").read()


def line_of(text, index):
    return text.count("\n", 0, index) + 1


# Zou side
# ---------------------------------------------------------------------------


def zou_routes_and_crud_events(app):
    routes = []
    crud_events = set()
    for rule in app.url_map.iter_rules():
        methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
        routes.append((re.sub(r"<[^>]+>", PLACEHOLDER, rule.rule), methods))
        view = app.view_functions.get(rule.endpoint)
        view_class = getattr(view, "view_class", None)
        if view_class is None or "crud" not in view_class.__module__:
            continue
        try:
            model = view_class().model
        except Exception:
            continue
        name = model.__tablename__.replace("_", "-")
        for action in ("new", "update", "delete"):
            crud_events.add(f"{name}:{action}")
    return routes, crud_events


def zou_emitted_events():
    """
    First argument of every events.emit call: literal names, and f-string
    patterns with each {} as a wildcard.
    """
    exact, patterns = defaultdict(list), defaultdict(list)
    for path, text in walk("zou/app", (".py",)):
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "emit"
                and node.args
            ):
                continue
            arg = node.args[0]
            where = f"{path}:{node.lineno}"
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                exact[arg.value.lower()].append(where)
            elif isinstance(arg, ast.JoinedStr):
                pattern = "".join(
                    re.escape(v.value) if isinstance(v, ast.Constant) else ".+"
                    for v in arg.values
                )
                patterns[pattern].append(where)
    return exact, patterns


# Consumer side
# ---------------------------------------------------------------------------


def normalize_js_path(raw):
    path = re.sub(r"\$\{[^}]*\}", PLACEHOLDER, raw)
    path = path.split("?")[0]
    return path.removeprefix("/api")


def kitsu_paths():
    """
    Every /api/... literal of kitsu/src with its HTTP method when the call
    site shows it.
    """
    found = []
    literal = re.compile(r"([`'\"])(/api/[^`'\"\s]*)\1")
    call = re.compile(r"client\.(\w+)\(\s*$")
    for path, text in walk(KITSU, (".js", ".vue")):
        for match in literal.finditer(text):
            before = text[max(0, match.start() - 40) : match.start()]
            method_match = call.search(before)
            method = None
            if method_match:
                method = KITSU_METHODS.get(method_match.group(1))
            after = text[match.end() : match.end() + 3].lstrip()
            # A literal completed by concatenation, or a placeholder holding
            # several segments (`${episodePath}task-types`), is checked as
            # dynamic only.
            glued = re.search(r"\$\{[^}]*\}[A-Za-z]", match.group(2))
            dynamic = after.startswith("+") or bool(glued)
            found.append(
                {
                    "path": normalize_js_path(match.group(2)),
                    "raw": match.group(2),
                    "method": method,
                    "dynamic": dynamic,
                    "where": f"{os.path.relpath(path, WORKSPACE)}:"
                    f"{line_of(text, match.start())}",
                }
            )
    return found


def doc_paths():
    found = []
    pattern = re.compile(
        r"(?<![\w/-])(?:(GET|POST|PUT|DELETE|PATCH)\s+)?(?:/api)?"
        r"(/(?:data|actions|auth|pictures|movies|export|import|config)"
        r"/[^\s`\"')\]<>|,]*)"
    )
    for path, text in walk(DOCS, (".md",)):
        for match in pattern.finditer(text):
            raw = match.group(2).rstrip(".:;")
            normalized = re.sub(r":[a-z_]+|\{[^}]*\}|<[^>]*>", PLACEHOLDER, raw)
            found.append(
                {
                    "path": normalized.split("?")[0],
                    "raw": raw,
                    "method": match.group(1),
                    "where": f"{os.path.relpath(path, WORKSPACE)}:"
                    f"{line_of(text, match.start())}",
                }
            )
    return found


GAZU_HELPERS = {
    # name: (prefix, number of path arguments joined with "/")
    "fetch_all": ("data/", 1),
    "fetch_first": ("data/", 1),
    "fetch_one": ("data/", 2),
    "create": ("data/", 1),
    "update": ("data/", 2),
    "get": ("", 1),
    "post": ("", 1),
    "put": ("", 1),
    "delete": ("", 1),
    "upload": ("", 1),
    "download": ("", 1),
}


def gazu_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            v.value if isinstance(v, ast.Constant) else PLACEHOLDER
            for v in node.values
        )
    return PLACEHOLDER


def gazu_paths():
    """
    Paths gazu requests, read from the calls to its client helpers, with
    the data/ prefix fetch_*, create and update add themselves. Used only
    to tell which zou routes have a consumer.
    """
    found = []
    for path, text in walk(GAZU, (".py",)):
        tree = ast.parse(text)
        # gazu often builds the path first: path = f"user/..."; then
        # fetch_all(path). Remember those local string assignments.
        bound = {}
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, (ast.Constant, ast.JoinedStr))
            ):
                value = gazu_string(node.value)
                if value != PLACEHOLDER:
                    bound.setdefault(node.targets[0].id, set()).add(value)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(
                func, "id", None
            )
            if name not in GAZU_HELPERS or not node.args:
                continue
            prefix, count = GAZU_HELPERS[name]
            first = node.args[0]
            if isinstance(first, ast.Name) and first.id in bound:
                heads = bound[first.id]
            else:
                heads = {gazu_string(first)}
            rest = [gazu_string(a) for a in node.args[1:count]]
            for head in heads:
                if head == PLACEHOLDER:
                    continue
                joined = prefix + "/".join([head, *rest])
                found.append({"path": "/" + joined.split("?")[0]})
    return found


def kitsu_listened_events():
    """
    socket.on('x:y', ...) calls and keys of socketEvents = { 'x:y': ... }
    objects.
    """
    found = defaultdict(list)
    on_call = re.compile(
        rf"socket\.on\(\s*['\"]({EVENT_NAME})['\"]", re.I
    )
    key = re.compile(rf"^\s*['\"]({EVENT_NAME})['\"]\s*[:(]", re.M)
    for path, text in walk(KITSU, (".js", ".vue")):
        where = os.path.relpath(path, WORKSPACE)
        for match in on_call.finditer(text):
            found[match.group(1)].append(
                f"{where}:{line_of(text, match.start())}"
            )
        if "socketEvents" not in text and "sockets" not in text:
            continue
        for match in key.finditer(text):
            found[match.group(1)].append(
                f"{where}:{line_of(text, match.start())}"
            )
    return found


# Matching
# ---------------------------------------------------------------------------


def segment_match(consumer, route):
    if consumer == route:
        return True
    if consumer == PLACEHOLDER or route == PLACEHOLDER:
        return True
    if PLACEHOLDER in consumer or PLACEHOLDER in route:
        a = re.escape(consumer).replace(re.escape(PLACEHOLDER), ".+")
        b = re.escape(route).replace(re.escape(PLACEHOLDER), ".+")
        sample_a = consumer.replace(PLACEHOLDER, "x")
        sample_b = route.replace(PLACEHOLDER, "x")
        return bool(
            re.fullmatch(b, sample_a) or re.fullmatch(a, sample_b)
        )
    return False


def matching_routes(path, routes):
    segments = path.rstrip("/").split("/")
    matches = []
    for route, methods in routes:
        route_segments = route.rstrip("/").split("/")
        if len(route_segments) != len(segments):
            continue
        if all(map(segment_match, segments, route_segments)):
            matches.append((route, methods))
    return matches


def check_paths(found, routes):
    missing, wrong_method, dynamic = [], [], []
    used = set()
    for item in found:
        path = item["path"]
        if item.get("dynamic") or path.endswith("/"):
            dynamic.append(item)
            continue
        matches = matching_routes(path, routes)
        if not matches:
            missing.append(item)
            continue
        for route, _ in matches:
            used.add(route)
        if item.get("method") and not any(
            item["method"] in methods for _, methods in matches
        ):
            item["allowed"] = sorted({m for _, ms in matches for m in ms})
            wrong_method.append(item)
    return missing, wrong_method, dynamic, used


def is_emitted(name, exact, patterns, crud_events):
    if name in exact or name in crud_events:
        return True
    # A fully dynamic name (f"{a}:{b}") would match anything.
    return any(re.fullmatch(p, name) for p in patterns if p != ".+:.+")


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else ".audit"
    from zou.app import create_app

    app = create_app()
    routes, crud_events = zou_routes_and_crud_events(app)
    exact, patterns = zou_emitted_events()

    kitsu = kitsu_paths()
    docs = doc_paths()
    gazu = gazu_paths()
    k_missing, k_method, k_dynamic, k_used = check_paths(kitsu, routes)
    d_missing, d_method, _, _ = check_paths(docs, routes)
    _, _, _, g_used = check_paths(gazu, routes)

    unused = sorted(
        route.replace(PLACEHOLDER, "<>")
        for route, _ in routes
        if route not in k_used
        and route not in g_used
        and not route.startswith(
            (
                "/static",
                "/apidocs",
                "/flasgger",
                "/docs",
                "/openapi",
                "/oauth2-redirect",
                # Installed plugins vary from one machine to the next.
                "/plugins/",
            )
        )
    )

    listened = kitsu_listened_events()
    zou_source = "\n".join(text for _, text in walk("zou/app", (".py",)))
    never_emitted = {}
    for name, where in sorted(listened.items()):
        if is_emitted(name, exact, patterns, crud_events):
            continue
        # Room events are relayed by the event stream, not events.emit.
        if f'"{name}"' in zou_source or f"'{name}'" in zou_source:
            continue
        never_emitted[name] = where
    all_emitted = set(exact) | crud_events
    not_listened = sorted(n for n in all_emitted if n not in listened)

    def show(item):
        method = f"{item['method']} " if item.get("method") else ""
        allowed = (
            f" (zou allows {', '.join(item['allowed'])})"
            if "allowed" in item
            else ""
        )
        return f"- `{method}{item['raw']}`{allowed}: {item['where']}"

    stamp = datetime.date.today().isoformat()
    lines = [
        f"# Cross-repo contract audit, {stamp}",
        "",
        f"{len(routes)} zou rules, {len(kitsu)} kitsu paths, "
        f"{len(gazu)} gazu paths, {len(docs)} doc paths, "
        f"{len(all_emitted)} zou events ({len(crud_events)} from CRUD), "
        f"{len(listened)} kitsu listeners.",
        "",
        f"## Kitsu calls a route zou does not have ({len(k_missing)})",
        "",
        *map(show, k_missing),
        "",
        f"## Kitsu uses a method the zou route refuses ({len(k_method)})",
        "",
        *map(show, k_method),
        "",
        f"## Kitsu listens to an event zou never emits ({len(never_emitted)})",
        "",
        *(
            f"- `{name}`: {', '.join(where)}"
            for name, where in never_emitted.items()
        ),
        "",
        f"## Docs mention a route zou does not have ({len(d_missing)})",
        "",
        *map(show, d_missing),
        "",
        f"## Docs show a method the zou route refuses ({len(d_method)})",
        "",
        *map(show, d_method),
        "",
        f"## Zou routes with no kitsu or gazu caller ({len(unused)})",
        "",
        "Candidates for removal or for a gazu wrapper; plugins and external "
        "scripts may still use them.",
        "",
        *(f"- `{route}`" for route in unused),
        "",
        f"## Zou events kitsu does not listen to ({len(not_listened)})",
        "",
        "Informational: gazu users and plugins may listen to them.",
        "",
        *(f"- `{name}`" for name in not_listened),
        "",
        f"## Kitsu paths built dynamically, unchecked ({len(k_dynamic)})",
        "",
        *map(show, k_dynamic),
    ]
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"contract-{stamp}")
    with open(f"{base}.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(f"{base}.json", "w") as f:
        json.dump(
            {
                "kitsu_missing": k_missing,
                "kitsu_wrong_method": k_method,
                "kitsu_never_emitted": never_emitted,
                "docs_missing": d_missing,
                "docs_wrong_method": d_method,
                "unused_routes": unused,
                "events_not_listened": not_listened,
                "kitsu_dynamic": k_dynamic,
            },
            f,
            indent=2,
        )
    print(f"Report: {base}.md")
    for line in lines:
        if line.startswith("## "):
            print(line[3:])


if __name__ == "__main__":
    main()
