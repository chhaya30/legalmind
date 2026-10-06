from pydantic import BaseModel, Field

class SimilarRequest(BaseModel):
    top_k:int=Field(5,ge=1,le=20)

class CompareRequest(BaseModel):
    document_a_id:str
    document_b_id:str

class SimilarCase(BaseModel):
    document_id:str; title:str; court:str|None=None; category:str|None=None; similarity_score:float; semantic_score:float; entity_overlap:float; why_similar:list[str]

class CompareCaseRequest(BaseModel):
    document_a_id:str
    document_b_id:str
