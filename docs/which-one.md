# `which-one`: installed package provenance

The zsh function lives in `~/.zsh_functions`. Load it in an existing shell:

```zsh
source ~/.zsh_functions
which-one impala
which-one Hyprland
which-one codex
which-one LocalSend
```

Pass one command name, executable path, package name, or Flatpak application ID.
Python 3 is required; unavailable package managers are skipped.

The helper checks only DNF/RPM (including COPR repositories), Homebrew formulae
and casks, Flatpak applications, and Nix. It does not check language package
managers such as Cargo, npm, or pip.

- Lists all external executables in PATH order and resolves symlinks. Reports
  shell aliases/functions/builtins separately without executing the target.
- Checks RPM ownership of both symlinks and their targets. Uses cached DNF
  metadata for the recorded installation repository, marking COPR repositories.
- Checks Homebrew names and resolved Cellar/Caskroom paths, so executable names
  need not equal formula names (for example, `rg` and `ripgrep`).
- Shows Flatpak origins and installations. Exact IDs/display names are matches;
  matching only the final ID component is labeled a candidate.
- Identifies Nix-store executables and searches the default profile, including
  legacy `nix-env` profiles. Other profiles, development shells, and NixOS system
  generations are not exhaustively searched.

Installed-name matches do not necessarily own the active executable. Missing
records do not prove a manual download. Queries do not install packages or
refresh repository metadata; Homebrew automatic updates/analytics are disabled.

Regression checks:

```sh
zsh -n .zsh_functions
python3 tests/test_which_one.py
```
