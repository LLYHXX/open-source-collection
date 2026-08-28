"""Forms pipeline: extract_forms into scan context."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from utils.parser import ResponseParser


class FakeResp:
    def __init__(self, text):
        self.text = text
        self.headers = {}


def test_extract_forms_includes_enctype():
    html = '''
    <form action="/login" method="POST" enctype="multipart/form-data">
      <input name="user" type="text"/>
      <input name="pass" type="password"/>
    </form>
    '''
    forms = ResponseParser(FakeResp(html)).extract_forms()
    assert len(forms) == 1
    assert forms[0]["method"] == "POST"
    assert "multipart" in forms[0].get("enctype", "").lower()
    names = {i["name"] for i in forms[0]["inputs"]}
    assert "user" in names and "pass" in names


def test_forms_feed_injection_surfaces():
    from core.injection_surfaces import extract_surfaces, Surface

    forms = [
        {
            "action": "/login",
            "method": "POST",
            "enctype": "application/x-www-form-urlencoded",
            "inputs": [{"name": "user", "type": "text", "value": ""}],
        }
    ]
    s = extract_surfaces("https://x.com/login", {"forms": forms})
    assert any(n == "user" for n, _ in s[Surface.FORM_POST])
