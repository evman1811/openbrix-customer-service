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
print("ok")
