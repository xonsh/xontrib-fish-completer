"""Populate rich completions using fish and remove the default bash based completer."""
from xonsh.completers import completer
from xonsh.completers.tools import complete_from_sub_proc, contextual_command_completer
from xonsh.parsers.completion_context import CommandContext


_FISH_SCRIPT = "complete --no-files -- $argv[1]; complete -C -- $argv[2]"


@contextual_command_completer
def fish_proc_completer(ctx: CommandContext):
    if not ctx.args:
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
