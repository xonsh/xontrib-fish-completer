"""Populate rich completions using fish and remove the default bash based completer."""
from xonsh.completers import completer
from xonsh.completers.tools import complete_from_sub_proc, contextual_command_completer
from xonsh.parsers.completion_context import CommandContext


_FISH_SCRIPT = "complete --no-files -- $argv[1]; complete -C -- $argv[2]"


@contextual_command_completer
def fish_proc_completer(ctx: CommandContext):
    # only complete command arguments; the command name itself is handled by
    # ``complete_base``. Bailing out here also avoids ``text_before_cursor``
    # returning a string with a stray leading space when ``arg_index == 0``.
    if ctx.arg_index < 1:
        return

    return (
        complete_from_sub_proc(
            "fish",
            "-c",
            _FISH_SCRIPT,
            ctx.args[0].value,
            ctx.text_before_cursor,
        ),
        False,
    )


def _load_xontrib_(**_):
    completer.add_one_completer("fish", fish_proc_completer, "<bash")
