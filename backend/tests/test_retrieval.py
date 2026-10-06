from app.retrieval.engine import _tokens, rrf_fuse
from types import SimpleNamespace

def make_item(cid, kw=0.0, sem=0.0):
    chunk=SimpleNamespace(id=cid, text=f"passage {cid}")
    return {"chunk":chunk,"document":SimpleNamespace(id="doc-"+cid),"page":SimpleNamespace(id="page-"+cid),"section":None,"keyword_score":kw,"semantic_score":sem}

def test_exact_legal_tokens():
    assert _tokens("Section 302 IPC") == ["section", "302", "ipc"]

def test_rrf_fuses_two_rankings():
    kw=[make_item("a",1),make_item("b",.5)]
    sem=[make_item("b",.9),make_item("c",.8)]
    out=rrf_fuse(kw,sem,3)
    ids=[x["chunk"].id for x in out]
    assert ids[0] in {"a","b"}
    assert set(ids)=={"a","b","c"}

def test_rrf_preserves_provenance():
    out=rrf_fuse([make_item("x",1)],[],1)
    assert out[0]["document"].id=="doc-x"
