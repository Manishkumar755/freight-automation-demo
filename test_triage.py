from types import SimpleNamespace

from email_triage import SAFE_FALLBACK_DRAFT, draft_contains_price, triage


class FakeClient:
    def __init__(self, text):
        self.messages = self
        self._text = text

    def create(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


def test_price_detector():
    assert draft_contains_price("The rate is USD 4.20 per kg")
    assert draft_contains_price("It will cost $300")
    assert draft_contains_price("Around 3.10 per kg")
    assert not draft_contains_price("Thank you, we will review your request.")


def test_price_in_draft_is_blocked():
    out = '{"category":"quote_request","urgency":"medium","summary":"rate ask","draft_reply":"The rate is USD 4.20 per kg."}'
    r = triage("s", "b", client=FakeClient(out))
    assert r["status"] == "blocked_price_in_draft"
    assert r["draft_reply"] == SAFE_FALLBACK_DRAFT
    assert r["human_review"] is True


def test_routing_and_safe_defaults():
    out = '{"category":"unknown_thing","urgency":"extreme","summary":"x","draft_reply":"Thanks, we will check."}'
    r = triage("s", "b", client=FakeClient(out))
    assert r["category"] == "other" and r["urgency"] == "high"
    assert r["routed_to"] == "ops-manager@example.com"
