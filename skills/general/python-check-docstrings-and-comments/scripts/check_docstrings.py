"""
Compare the parameter and return sections of Python docstrings with the
code. Reads Google (Args:), NumPy (Parameters / -----) and reST (:param x:)
styles. Read-only: prints one finding per line, file:line: message.

Usage:
    python check_docstrings.py [--ignore client,request] <file or dir>...
    python check_docstrings.py --self-test
"""

import ast
import re
import sys
from pathlib import Path

GOOGLE_HEADER = re.compile(
    r"^(\s*)(Args|Arguments|Parameters|Keyword Args|Keyword Arguments):\s*$"
)
GOOGLE_ENTRY = r"^{indent}(\*{{0,2}}\w+)\s*(\([^)]*\))?\s*:"
NUMPY_HEADER = re.compile(r"^(\s*)(Parameters|Other Parameters)\s*$")
NUMPY_ENTRY = r"^{indent}(\*{{0,2}}\w+)\s*(:|$)"
REST_PARAM = re.compile(r":param\s+(?:[^:]*\s)?\*{0,2}(\w+)\s*:")
RETURNS = re.compile(
    r"^\s*(Returns?:|Returns\s*\n\s*-{3,}|:returns?:|:rtype:)", re.M
)


def section_lines(lines, start, indent):
    """
    Lines of the section that starts after line `start`: they are blank or
    more indented than the header.
    """
    for line in lines[start + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= len(indent):
            break
        yield line


def documented_params(docstring):
    """
    Return the parameter names of the docstring, or None when the docstring
    has no parameter section.
    """
    lines = docstring.expandtabs().splitlines()
    names = set()
    found = False
    for index, line in enumerate(lines):
        google = GOOGLE_HEADER.match(line)
        numpy = NUMPY_HEADER.match(line)
        if google:
            found = True
            body = [l for l in section_lines(lines, index, google.group(1))]
            entry_indent = min(
                (len(l) - len(l.lstrip()) for l in body if l.strip()),
                default=0,
            )
            pattern = re.compile(GOOGLE_ENTRY.format(indent=" " * entry_indent))
            names |= {
                m.group(1).lstrip("*") for l in body if (m := pattern.match(l))
            }
        elif (
            numpy
            and index + 1 < len(lines)
            and set(lines[index + 1].strip()) == {"-"}
        ):
            found = True
            indent = numpy.group(1)
            pattern = re.compile(NUMPY_ENTRY.format(indent=re.escape(indent)))
            for l in lines[index + 2 :]:
                if l.strip() and not l.startswith(indent):
                    break
                if re.match(r"^\s*-{3,}\s*$", l):
                    break
                m = pattern.match(l)
                if m and not l[len(indent) :].startswith(" "):
                    names.add(m.group(1).lstrip("*"))
            # The header of the next section was read as a name.
            names -= {"Returns", "Yields", "Raises", "Examples", "Notes"}
    rest = {m.group(1) for m in REST_PARAM.finditer(docstring)}
    if rest:
        found = True
        names |= rest
    return names if found else None


def signature_params(function):
    args = function.args
    every = args.posonlyargs + args.args + args.kwonlyargs
    names = [a.arg for a in every]
    if args.vararg:
        names.append(args.vararg.arg)
    if args.kwarg:
        names.append(args.kwarg.arg)
    return [n for n in names if n not in ("self", "cls")]


def own_nodes(function):
    """
    Nodes of the function body, without the nested functions and classes.
    """
    stack = list(function.body)
    while stack:
        node = stack.pop()
        yield node
        for child in ast.iter_child_nodes(node):
            if not isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                stack.append(child)


def is_stub(function):
    body = function.body[1:] if ast.get_docstring(function) else function.body
    return all(
        isinstance(node, ast.Pass)
        or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
        or isinstance(node, ast.Raise)
        for node in body
    )


def check_function(function, ignore=frozenset()):
    docstring = ast.get_docstring(function)
    if not docstring:
        return []
    findings = []
    signature = signature_params(function)
    documented = documented_params(docstring)
    if documented is not None:
        for name in sorted(documented - set(signature)):
            findings.append(f"documents `{name}`, not in the signature")
        for name in signature:
            if name not in documented and name not in ignore:
                findings.append(f"does not document `{name}`")
    if RETURNS.search(docstring) and not is_stub(function):
        nodes = list(own_nodes(function))
        returns_value = any(
            isinstance(n, ast.Return) and n.value is not None for n in nodes
        )
        yields = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in nodes)
        if not returns_value and not yields:
            findings.append("has a Returns section, returns nothing")
    return findings


def check_source(source, filename="<string>", ignore=frozenset()):
    tree = ast.parse(source, filename)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for message in check_function(node, ignore):
                findings.append(f"{filename}:{node.lineno}: {node.name} {message}")
    return findings


def python_files(paths):
    for path in map(Path, paths):
        if path.is_dir():
            yield from sorted(
                p for p in path.rglob("*.py") if ".venv" not in p.parts
            )
        else:
            yield path


def self_test():
    source = '''
def google(a, b=1):
    """
    Do a thing.

    Args:
        a (str): First.
        c (int): Removed long ago.
            Continuation line, not a name.

    Returns:
        str: Never returned.
    """
    print(a, b)


def numpy(x, *args):
    """
    Parameters
    ----------
    x : int
        The value.
    args : tuple
        More.

    Returns
    -------
    int
    """
    return x


def rest(item, client=None):
    """
    :param item: The item.
    :param str other: Gone.
    """


def no_section(value):
    """
    A docstring without a parameter section is not checked.
    """


def abstract(value):
    """
    Args:
        value: The value.

    Returns:
        int: Implemented by subclasses.
    """
    raise NotImplementedError


def generator(items):
    """
    Args:
        items: The items.

    Returns:
        iterator: The items.
    """
    yield from items
'''
    found = check_source(source, "t.py")
    ignored = check_source(source, "t.py", ignore={"b", "client"})
    assert not any("document `b`" in f for f in ignored), ignored
    assert not any("document `client`" in f for f in ignored), ignored
    expected = [
        "t.py:2: google documents `c`, not in the signature",
        "t.py:2: google does not document `b`",
        "t.py:2: google has a Returns section, returns nothing",
        "t.py:33: rest documents `other`, not in the signature",
        "t.py:33: rest does not document `client`",
    ]
    assert sorted(found) == sorted(expected), "\n".join(found)
    print("self-test ok")


def main(argv):
    if argv == ["--self-test"]:
        self_test()
        return 0
    ignore = set()
    if argv[:1] == ["--ignore"] and len(argv) > 1:
        ignore = set(argv[1].split(","))
        argv = argv[2:]
    if not argv:
        print(__doc__.strip())
        return 2
    findings = []
    for path in python_files(argv):
        try:
            findings += check_source(
                path.read_text(encoding="utf-8"), str(path), ignore
            )
        except SyntaxError as error:
            print(f"{path}: cannot parse: {error}", file=sys.stderr)
    print("\n".join(findings) if findings else "no finding")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
