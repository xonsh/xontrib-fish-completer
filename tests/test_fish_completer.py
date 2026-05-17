import pytest

from xonsh.parsers.completion_context import CommandArg, CommandContext


@pytest.fixture
def fish_completer(tmpdir, xession, load_xontrib, fake_process):
    """vox Alias function"""
    load_xontrib("fish_completer")
    xession.env.update(
        dict(
            XONSH_DATA_DIR=str(tmpdir),
            XONSH_SHOW_TRACEBACK=True,
        )
    )

    fake_process.register_subprocess(
        command=["fish", fake_process.any()],
        # completion for "git chec"
        stdout=b"""\
cherry-pick	Apply the change introduced by an existing commit
checkout	Checkout and switch to a branch""",
    )

    return fake_process


def test_fish_completer(fish_completer, check_completer):
    assert check_completer("git", prefix="chec") == {"checkout"}


@pytest.fixture
def loaded_xontrib(tmpdir, xession, load_xontrib):
    load_xontrib("fish_completer")
    xession.env.update(
        dict(
            XONSH_DATA_DIR=str(tmpdir),
            XONSH_SHOW_TRACEBACK=True,
        )
    )


def _run_fish_completer(ctx):
    """Invoke the registered fish completer directly with a CommandContext."""
    from xonsh.built_ins import XSH
    from xonsh.parsers.completion_context import CompletionContext

    completer = XSH.completers["fish"]
    result = completer(CompletionContext(command=ctx))
    if result is None:
        return [], None
    if isinstance(result, tuple):
        gen, extra = result
        return list(gen), extra
    return list(result), None


def test_fish_completer_passes_command_and_line_as_argv(
    loaded_xontrib, fake_process
):
    """fish must receive the command and line as separate argv entries, not
    interpolated into the script. Otherwise quotes / semicolons / backticks
    in the line break the generated fish script.
    """
    recorder = fake_process.register_subprocess(
        command=["fish", fake_process.any()],
        stdout=b"checkout\tCheckout and switch to a branch",
    )

    ctx = CommandContext(
        args=(CommandArg("git"),),
        arg_index=1,
        prefix="chec",
    )
    completions, _ = _run_fish_completer(ctx)

    assert {str(c) for c in completions} == {"checkout"}
    assert recorder.call_count() == 1

    args = list(recorder.calls[0].args)
    # fish is invoked as: fish -c <script> <command> <line>
    assert args[0] == "fish"
    assert args[1] == "-c"

    script = args[2]
    # script template references $argv — user input is never embedded
    assert "$argv" in script
    assert "chec" not in script
    assert "git" not in script

    # the actual values land as positional argv entries
    assert args[3] == "git"
    assert args[4].endswith("chec")


def test_fish_completer_survives_single_quote_in_line(
    loaded_xontrib, fake_process
):
    """Regression: a single quote in the line must not break the completer.

    The previous implementation built the fish script via
    ``f"complete -C '{line}'"``, so any single quote in the line broke
    fish's argument parsing and the completer silently returned nothing.
    """
    recorder = fake_process.register_subprocess(
        command=["fish", fake_process.any()],
        stdout=b"--amend\tAmend the previous commit",
    )

    # User typed:  git commit -m 'fix --
    # CommandContext for completing the trailing "--" prefix.
    ctx = CommandContext(
        args=(
            CommandArg("git"),
            CommandArg("commit"),
            CommandArg("-m"),
            CommandArg("fix", opening_quote="'"),
        ),
        arg_index=4,
        prefix="--",
    )
    completions, _ = _run_fish_completer(ctx)

    assert {str(c) for c in completions} == {"--amend"}

    args = list(recorder.calls[0].args)
    script = args[2]
    # the script must not contain user-provided characters at all
    assert "'" not in script
    # but the line passed via argv carries the quote verbatim
    assert "'fix" in args[4]


def test_fish_completer_skips_command_name_completion(
    loaded_xontrib, fake_process
):
    """When ``arg_index == 0`` the user is still typing the command name —
    ``complete_base`` owns that case. fish must not be invoked.

    This also guards against the ``text_before_cursor`` quirk where
    ``words_before_cursor`` is empty and the property returns a string
    with a stray leading space (e.g. ``" gi"``).
    """
    recorder = fake_process.register_subprocess(
        command=["fish", fake_process.any()],
        stdout=b"git\tThe git command",
    )

    ctx = CommandContext(
        args=(CommandArg("gi"),),
        arg_index=0,
        prefix="gi",
    )
    completions, _ = _run_fish_completer(ctx)

    assert completions == []
    assert recorder.call_count() == 0


def test_fish_completer_strips_quotes_from_command_name(
    loaded_xontrib, fake_process
):
    """The command name passed to ``complete --no-files`` must be the bare
    value, not the quoted ``raw_value``. Otherwise an invocation like
    ``"my cmd" --<TAB>`` would tell fish ``complete --no-files "my cmd"``,
    embedding the quotes into the command identifier.
    """
    recorder = fake_process.register_subprocess(
        command=["fish", fake_process.any()],
        stdout=b"--help\tShow help",
    )

    ctx = CommandContext(
        args=(CommandArg("my cmd", opening_quote='"', closing_quote='"'),),
        arg_index=1,
        prefix="--",
    )
    _run_fish_completer(ctx)

    args = list(recorder.calls[0].args)
    # argv[1] is the command name fish sees in `complete --no-files -- $argv[1]`
    assert args[3] == "my cmd"
    assert args[3] != '"my cmd"'


def test_fish_completer_placed_before_bash(xession, load_xontrib):
    """When bash is registered, fish must be inserted immediately before it."""
    from xonsh.built_ins import XSH

    noop = lambda *a, **kw: None
    XSH.completers.clear()
    XSH.completers["alias"] = noop
    XSH.completers["bash"] = noop
    XSH.completers["man"] = noop
    XSH.completers["path"] = noop

    load_xontrib("fish_completer")

    keys = list(XSH.completers.keys())
    assert keys.index("fish") < keys.index("bash")


def test_fish_completer_falls_back_to_man_without_bash(xession, load_xontrib):
    """Without bash (e.g. systems where it isn't on PATH), fish must anchor
    on the next available completer (man), not be appended to the end of
    the list past the exclusive ``path`` completer.
    """
    from xonsh.built_ins import XSH

    noop = lambda *a, **kw: None
    XSH.completers.clear()
    XSH.completers["alias"] = noop
    XSH.completers["man"] = noop
    XSH.completers["path"] = noop

    load_xontrib("fish_completer")

    keys = list(XSH.completers.keys())
    assert "fish" in keys
    assert keys.index("fish") < keys.index("man")
    assert keys.index("fish") < keys.index("path")


def test_fish_completer_falls_back_to_path_on_windows(xession, load_xontrib):
    """Windows scenario: bash and man are absent — anchor on ``path``.
    Without this fallback, ``add_one_completer`` would silently append fish
    after ``path`` and fish would never be reached.
    """
    from xonsh.built_ins import XSH

    noop = lambda *a, **kw: None
    XSH.completers.clear()
    XSH.completers["alias"] = noop
    XSH.completers["path"] = noop

    load_xontrib("fish_completer")

    keys = list(XSH.completers.keys())
    assert "fish" in keys
    assert keys.index("fish") < keys.index("path")


def test_fish_completer_survives_semicolon_in_line(loaded_xontrib, fake_process):
    """Regression: a ``;`` in the line must not be interpreted as a fish
    command separator. Previously ``complete -C 'git status; ls /tmp'`` ran
    a real ``ls`` inside fish.
    """
    recorder = fake_process.register_subprocess(
        command=["fish", fake_process.any()],
        stdout=b"--all\tShow all",
    )

    ctx = CommandContext(
        args=(CommandArg("git"), CommandArg("status;")),
        arg_index=2,
        prefix="--",
    )
    completions, _ = _run_fish_completer(ctx)

    assert {str(c) for c in completions} == {"--all"}
    args = list(recorder.calls[0].args)
    # the user-typed token is in argv, not interpolated into the script
    assert "status" not in args[2]
    assert "status;" in args[4]
