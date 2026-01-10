Output artifacts/vhs/rocs-validate-help.gif

Set Shell "bash"
Set FontSize 18
Set Width 1400
Set Height 900

Require "uv"
Require "python"

Type "uv run python -m rocs_cli validate --help"
Enter
Sleep 1s
