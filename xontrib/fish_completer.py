"""Populate rich completions using fish, taking precedence over the default bash based completer."""

from xonsh.built_ins import XSH
from xonsh.completers import completer
from xonsh.completers.tools import (
    RichCompletion,
    complete_from_sub_proc,
    contextual_command_completer,
)
from xonsh.parsers.completion_context import CommandContext

_FISH_SCRIPT = "complete --no-files -- $argv[1]; complete -C -- $argv[2]"

# Descriptions fish emits as placeholders for PATH commands without real
# completion metadata. They're not informative and just clutter the UI.
_NOISE_DESCRIPTIONS = frozenset({"command link"})


def _denoise(completions):
    for comp in completions:
        if isinstance(comp, RichCompletion) and comp.description in _NOISE_DESCRIPTIONS:
            yield comp.replace(description="")
        else:
            yield comp


@contextual_command_completer
def fish_proc_completer(ctx: CommandContext):
    # only complete command arguments; the command name itself is handled by
    # ``complete_base``. Bailing out here also avoids ``text_before_cursor``
    # returning a string with a stray leading space when ``arg_index == 0``.
    if ctx.arg_index < 1:
        return

    return (
        _denoise(
            complete_from_sub_proc(
                "fish",
                "-c",
                _FISH_SCRIPT,
                ctx.args[0].value,
                ctx.text_before_cursor,
            )
        ),
        False,
    )


def _load_xontrib_(**_):
    # Anchor fish before the first arg-completing completer that is actually
    # registered. ``bash`` is the preferred neighbour, but on Windows and on
    # systems without bash it isn't registered at all — falling through to
    # ``man`` and finally ``path`` keeps fish ahead of the exclusive ``path``
    # completer; otherwise ``add_one_completer`` would silently append fish
    # to the end of the list and it would never be reached.
    for anchor in ("bash", "man", "path"):
        if anchor in XSH.completers:
            completer.add_one_completer("fish", fish_proc_completer, f"<{anchor}")
            return


def _unload_xontrib_(*_, **__):
    XSH.completers.pop("fish", None)
