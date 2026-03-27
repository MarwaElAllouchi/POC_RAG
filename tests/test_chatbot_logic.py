from datetime import datetime

class FakeDoc:
    def __init__(self, metadata):
        self.metadata = metadata

def test_filter_valid_docs_by_date():
    docs = [
        FakeDoc({"start": "2026-02-25", "title": "Concert"}),
        FakeDoc({"start": "2026-02-20", "title": "Expo"})
    ]

    target_date = "2026-02-25"
    DATE_REF = datetime(2026, 2, 24)

    valid_docs = []
    for d in docs:
        event_date = d.metadata["start"]
        if event_date == target_date:
            valid_docs.append(d)

    assert len(valid_docs) == 1
    assert valid_docs[0].metadata["title"] == "Concert"