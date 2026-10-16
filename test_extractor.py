from types import SimpleNamespace

from doc_extractor import extract, parse_json, validate


class FakeClient:
    def __init__(self, text):
        self.messages = self
        self._text = text

    def create(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


GOOD = """{"document_type":"commercial invoice","shipper":"A","consignee":"B",
"description":"cotton","gross_weight_kg":186.5,"container_number":null,"confidence":0.95,"missing_fields":[]}"""


def test_good_output_passes():
    r = extract("doc", client=FakeClient(GOOD))
    assert r["needs_review"] is False
    assert r["data"]["gross_weight_kg"] == 186.5


def test_low_confidence_goes_to_review():
    r = extract("doc", client=FakeClient(GOOD.replace("0.95", "0.5")))
    assert r["needs_review"] is True


def test_missing_required_field_goes_to_review():
    r = extract("doc", client=FakeClient(GOOD.replace('"shipper":"A"', '"shipper":null')))
    assert "shipper" in r["missing_fields"] and r["needs_review"] is True


def test_bad_json_is_flagged_not_crashed():
    r = extract("doc", client=FakeClient("Sure! Here you go: {broken"))
    assert r["needs_review"] is True and r["data"] is None


def test_markdown_fences_are_stripped():
    assert parse_json("```json\n{\"a\": 1}\n```") == {"a": 1}


def test_container_format_checked():
    v = validate({"document_type": "x", "shipper": "a", "consignee": "b", "description": "d",
                  "gross_weight_kg": 1, "confidence": 0.9, "container_number": "ABC123"})
    assert any("container" in p for p in v["problems"])
