Output artifacts/vhs/rocs-version.gif

Set Shell "bash"
Set FontSize 20
Set Width 1200
Set Height 520

Require "uv"
Require "python"

Type "uv run python -m rocs_cli version"
Enter
Sleep 750ms
