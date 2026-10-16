# OpenBrix customer service

Drafts replies to tlyfe customer service emails with Claude. It **never sends**: it reads new
emails (Outlook / Microsoft 365, or any IMAP mailbox), writes a reply into the Drafts folder, and a person checks and sends it.
Risky emails (complaints, deposit disputes, legal, data requests) get a `[NEEDS HUMAN: why]` line at the top.

## Files
- `responder.py`: the whole bot
- `knowledge.md`: facts Claude may use. **Fill in the TODOs and check the VERIFY lines first.**
- `examples/`: past emails and the replies sent (git-ignored, see `examples/README.md`)
- `test_responder.py`: offline check, `python test_responder.py`

## Setup
```
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...
```

### Outlook / Microsoft 365 (main route)
Microsoft has switched off password logins over IMAP, so this uses the Microsoft Graph API.
Someone with Microsoft 365 admin rights does this once (about 10 minutes):

1. Azure portal → **App registrations** → New registration → name it `tlyfe-cs-drafts`.
2. **API permissions** → Add → Microsoft Graph → *Application permissions* → `Mail.ReadWrite` → **Grant admin consent**.
3. **Certificates & secrets** → New client secret → copy the value.
4. **Restrict it to the support mailbox only.** Without this the app can read every mailbox in the company.
   In Exchange Online PowerShell:
   `New-ApplicationAccessPolicy -AppId <client id> -PolicyScopeGroupId support@yourdomain -AccessRight RestrictAccess -Description "CS bot"`

```
set GRAPH_TENANT_ID=<directory (tenant) id>
set GRAPH_CLIENT_ID=<application (client) id>
set GRAPH_CLIENT_SECRET=<secret value>
set GRAPH_MAILBOX=support@yourdomain
```
Drafts land in the mailbox's **Drafts** folder as threaded replies. Each email it handles gets the
Outlook category **AI Drafted** and stays unread.

### Any other mailbox (Gmail etc.) over IMAP
Used when `GRAPH_TENANT_ID` isn't set.
```
set IMAP_HOST=imap.gmail.com
set IMAP_USER=support@yourdomain
set IMAP_PASSWORD=<app password>
set IMAP_DRAFTS=[Gmail]/Drafts        (Outlook: Drafts)
```
Try one email without touching the inbox: `python responder.py some-email.eml`
Run for real: `python responder.py`.

### Running it every 15 minutes (Windows)
Task Scheduler doesn't see variables set with `set` in a terminal, so put them in a `run.bat` next to `responder.py`
(it's git-ignored because it holds secrets):
```
@echo off
set ANTHROPIC_API_KEY=sk-ant-...
set GRAPH_TENANT_ID=...
set GRAPH_CLIENT_ID=...
set GRAPH_CLIENT_SECRET=...
set GRAPH_MAILBOX=support@yourdomain
cd /d %~dp0
python responder.py >> log.txt 2>&1
```
Task Scheduler → Create Basic Task → Daily → action *Start a program* = `run.bat`. Then open the task's
Triggers tab → Edit → *Repeat task every 15 minutes* for *Indefinitely*. Also tick *Run whether user is logged on or not*.
Use a machine that stays on.

Model: Claude Sonnet 5.5 by default. Set `CS_MODEL=claude-opus-5-5` for harder emails, or `claude-haiku-5-5` for the cheapest option.

## Cost at 10 emails a day
Assumes about 11k input tokens per email (instructions + knowledge base + 25 example replies),
plus about 600 output tokens. The fixed part is prompt-cached, which helps when several emails arrive within 5 minutes.

| Model | Per email | Per month (300 emails) |
|---|---|---|
| Claude Opus 5.5 | $0.03-0.07 | about $10-21 |
| Claude Sonnet 5.5 (default) | $0.015-0.035 | about $5-11 |
| Claude Haiku 5.5 | under $0.005 | about $1 |

To compare, run the same 10-15 past emails through Sonnet and Opus and have the support team judge the drafts blind.
A Claude Team or Pro subscription doesn't cover this; it needs a Claude API key (console.anthropic.com) billed per use.

## Safety
- Draft-only by design. The email text is treated as untrusted input; nothing it says can make the bot send mail.
- Don't commit real customer emails: this repo is public.
