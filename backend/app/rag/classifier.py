from enum import Enum

class QueryType(str, Enum):
    PROVISION_LOOKUP = 'provision_lookup'
    FACTUAL = 'factual'
    REASONING = 'reasoning'
    COMPARISON = 'comparison'
    SUMMARY = 'summary'


def classify_query(query: str) -> QueryType:
    q = query.lower().strip()
    if any(x in q for x in ['compare', 'difference', 'similarities', 'versus', ' vs ', 'both cases']):
        return QueryType.COMPARISON
    if any(x in q for x in ['summarize', 'summary', 'brief this case', 'overview', 'key points']):
        return QueryType.SUMMARY
    if any(x in q for x in ['why did', 'why was', 'reasoning', 'reason', 'held that', 'because', 'rationale']):
        return QueryType.REASONING
    if any(x in q for x in ['section ', 'article ', 'ipc', 'crpc', 'cpc', 'act ', 'provision', 'under section', 'under article']):
        return QueryType.PROVISION_LOOKUP
    return QueryType.FACTUAL
