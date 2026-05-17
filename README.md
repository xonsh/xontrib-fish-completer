<p align="center">
Populate rich completions using fish, taking precedence over the default bash based completer in xonsh shell. The bash completer remains registered and is used as a fallback when fish has no completion for the command.
</p>

<p align="center">
If you like the idea click ⭐ on the repo and <a href="https://twitter.com/intent/tweet?text=Nice%20xontrib%20for%20the%20xonsh%20shell!&url=https://github.com/xonsh/xontrib-fish-completer" target="_blank">tweet</a>.
</p>


## Installation

First of all install [fish shell](https://github.com/fish-shell/fish-shell#getting-fish).

To install the xontrib use xpip:

```bash
xpip install xontrib-fish-completer
# or: xpip install -U git+https://github.com/xonsh/xontrib-fish-completer
```

## Usage

```bash
xontrib load fish_completer
ls -<Tab>
```

## Credits

This package was created with [xontrib template](https://github.com/xonsh/xontrib-template).
