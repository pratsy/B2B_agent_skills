# Demo workspace inputs

Inputs for the demo GIF (`scripts/render_demo_gif.py --record`) and a quick way to try the playbooks on realistic data:

```bash
b2b-skills init try-it --yes && cd try-it
cp ../examples/demo/{answers.txt,homepage.txt} .
b2b-skills checkup northwind.example --text homepage.txt --answers answers.txt --provider claude-code
b2b-skills checkup --docs ../examples/demo/docs --no-questions --provider claude-code   # from documents alone
cp ../examples/demo/company.md . && cp ../examples/demo/icp.json gtm/ && cp ../examples/demo/{win-loss-and-homepage.md,leads.csv} .
b2b-skills playbook fix-my-message --notes win-loss-and-homepage.md --provider claude-code
b2b-skills playbook score-list --csv leads.csv
```

`docs/` holds the documents a founder would already have: a HubSpot-style deal export (31 closed, 8 open), a lead sheet with lead sources, and notes from a customer call.

The company ("Northwind Forecasting") and all people and accounts are fictional.
