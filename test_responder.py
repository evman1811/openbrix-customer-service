"""Offline check of email parsing and draft building (no API call). Run: python test_responder.py"""
import email
from email.policy import default

from responder import body_text, build_draft

raw = b"""From: Jo Tenant <jo@example.com>
To: support@tlyfe.co.uk
Subject: Can't verify my ID
Message-ID: <abc@example.com>
Content-Type: text/plain

The app keeps rejecting my passport photo.
"""
msg = email.message_from_bytes(raw, policy=default)
assert "passport photo" in body_text(msg)

d = build_draft(msg, {"needs_human": False, "reason": "", "reply": "Hi Jo, ..."}, "support@tlyfe.co.uk")
assert d["To"] == "Jo Tenant <jo@example.com>"
assert d["Subject"] == "Re: Can't verify my ID"
assert d["In-Reply-To"] == "<abc@example.com>"
assert d.get_content().startswith("Hi Jo")

d = build_draft(msg, {"needs_human": True, "reason": "complaint", "reply": "Hi Jo"}, "support@tlyfe.co.uk")
assert d.get_content().startswith("[NEEDS HUMAN: complaint]")

# Outlook loop with a fake Graph + fake Claude: drafts new mail once, skips already-drafted mail
import os
import responder

os.environ["GRAPH_MAILBOX"] = "support@tlyfe.co.uk"
inbox = [
    {"id": "1", "subject": "Login help", "from": {"emailAddress": {"address": "a@x.com"}},
     "body": {"content": "can't log in"}, "categories": []},
    {"id": "2", "subject": "Old", "from": {"emailAddress": {"address": "b@x.com"}},
     "body": {"content": "hi"}, "categories": ["AI Drafted"]},
]
calls = []
def fake_graph(token, method, path, body=None):
    calls.append((method, path, body))
    return {"value": inbox} if method == "GET" else {}
responder.draft_reply = lambda c, s, subj, b: {"category": "account_login", "needs_human": True,
                                                "reason": "unsure", "reply": "Hi", "usage": {}}
responder.run_graph(None, call=fake_graph)
assert calls[1] == ("POST", "/users/support@tlyfe.co.uk/messages/1/createReply",
                    {"comment": "[NEEDS HUMAN: unsure]\n\nHi"})
assert calls[2] == ("PATCH", "/users/support@tlyfe.co.uk/messages/1", {"categories": ["AI Drafted"]})
assert len(calls) == 3  # message 2 skipped
print("ok")
