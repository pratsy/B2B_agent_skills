# Alternative recorder for docs/assets/demo.gif using VHS (https://github.com/charmbracelet/vhs).
# The checked-in GIF is made without VHS:
#   python scripts/render_demo_gif.py --record docs/assets/demo-session.txt
#   python scripts/render_demo_gif.py docs/assets/demo-session.txt -o docs/assets/demo.gif
#
#
#   brew install vhs
#   pip install -e .            # puts b2b-skills on PATH
#   vhs docs/assets/demo.tape
#
# Runs a real model through the Claude Code CLI (your Claude login or
# subscription), so no API key is needed. Re-record when skills change.

Output docs/assets/demo.gif
Require b2b-skills
Require jq

Set Shell zsh
Set FontSize 15
Set Width 1200
Set Height 760
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms

Hide
Type "export PS1='$ ' && clear" Enter
Show

Type "# 48 B2B revenue skills. Here: MEDDPICC deal risk, scored on evidence quality" Enter
Sleep 1s
Type "b2b-skills list | head -5" Enter
Sleep 2s
Type "jq .pillar_evidence.economic_buyer examples/fixtures/deal_risk_input.json" Enter
Sleep 3s
Type "b2b-skills run deal-risk-assessor -i examples/fixtures/deal_risk_input.json --provider claude-code" Enter
Wait+Screen@180s /priority_action/
Sleep 7s
Type "# Schema-validated JSON. Same skill runs in Claude Code, over MCP, and via HTTP." Enter
Sleep 3s
