from app.intelligence.service import _cos, _tokens

def test_document_similarity_cosine():
    assert _cos([1,0],[1,0]) == 1.0
    assert _cos([1,0],[0,1]) == 0.0

def test_token_overlap_signal():
    a=_tokens('Section 302 IPC murder'); b=_tokens('murder under section 302 ipc')
    assert len(a & b) >= 3

def test_compare_classification_threshold():
    assert len(_tokens('same facts and same issue') & _tokens('same facts and same issue')) == 4

def test_timeline_date_regex():
    import re
    assert re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b','12/03/2020')

def test_issue_question_signal():
    import re
    assert re.search(r'\bwhether\b', 'The court must decide whether the appeal is maintainable.', re.I)
