import {useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {ArrowUpRight,BookOpenCheck,CheckCircle2,ShieldAlert,Sparkles} from 'lucide-react'
import {api} from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const prompts=['What issue did the court decide?','Which provisions did the judgment apply?','Summarize the court’s reasoning.']
function CitationText({text,citations=[],evidence=[]}){
 const pattern=/\[([^\],]+),\s*p\.(\d+),\s*§([^\]]+)\]/g,parts=[];let cursor=0,match
 while((match=pattern.exec(text||''))){if(match.index>cursor)parts.push(text.slice(cursor,match.index));const citation=citations.find(item=>item.doc===match[1].trim()&&item.page===Number(match[2])&&item.section===match[3].trim());const source=evidence.find(item=>item.document_id===match[1].trim()&&item.page_number===Number(match[2]));parts.push(citation&&source?<Link key={match.index} className="citation-chip" to={`/documents/${source.document_id}?page=${source.page_number}&chunk=${encodeURIComponent(source.chunk_id)}`}>{match[0]}</Link>:match[0]);cursor=pattern.lastIndex}
 if(cursor<(text||'').length)parts.push(text.slice(cursor))
 return <>{parts.map((part,index)=>typeof part==='string'?<span key={`text-${index}`}>{part}</span>:part)}</>
}

export default function Ask(){
 const [params]=useSearchParams(),[question,setQuestion]=useState(params.get('q')||''),[court,setCourt]=useState(''),[category,setCategory]=useState(''),[answer,setAnswer]=useState(null),[loading,setLoading]=useState(false),[error,setError]=useState('')
 const submit=async event=>{event.preventDefault();if(!question.trim())return;setLoading(true);setError('');setAnswer(null);try{setAnswer(await api.ask({question:question.trim(),court:court||undefined,category:category||undefined}))}catch(e){setError(e.message)}finally{setLoading(false)}}
 return <section className="page-content">
  <PageHeader eyebrow="LEGAL RAG / CITATION-LED ANSWERS" title="Ask LegalMind" description="Ask across the indexed corpus. Each answer is grounded in retrieved judgment passages."/>
  <div className="research-safety"><ShieldAlert size={16}/><span><b>Research assistance, not legal advice.</b> Verify each cited passage in its source document before relying on it.</span></div>
  <div className="suggested-prompts">{prompts.map(prompt=><button key={prompt} className="suggested-prompt" onClick={()=>setQuestion(prompt)}>{prompt}</button>)}</div>
  <form className="ask-workspace" onSubmit={submit}><div className="ask-workspace-mark"><Sparkles size={17}/><span>LEGALMIND ASSISTANT</span></div><textarea value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask a question about a case, legal provision, or issue…" rows="4" aria-label="Question for LegalMind"/><div className="ask-workspace-footer"><label className="field"><span>Court filter</span><input value={court} onChange={e=>setCourt(e.target.value)} placeholder="Any court"/></label><label className="field"><span>Category filter</span><input value={category} onChange={e=>setCategory(e.target.value)} placeholder="Any category"/></label><span className="ask-source-note"><BookOpenCheck size={13}/> Answers cite indexed passages</span><button className="button button-primary" disabled={loading||!question.trim()}>{loading?'Researching…':<>Ask LegalMind <ArrowUpRight size={14}/></>}</button></div></form>
  {error&&<ErrorState message={error}/>}{loading&&<div className="answer-loading"><LoadingState message="Searching the corpus and checking supporting evidence…"/></div>}
  {answer&&!loading&&<div className="answer-layout"><article className="answer-card"><div className="answer-head"><div><span className="eyebrow">RESEARCH RESPONSE · {answer.query_type||'LEGAL QUESTION'}</span><h2>Answer</h2></div><span className="confidence"><CheckCircle2 size={13}/> {Math.round((answer.confidence||0)*100)}% confidence</span></div>{answer.insufficient_evidence&&<div className="insufficient"><ShieldAlert size={15}/><span><b>Insufficient evidence</b><small>The retrieved corpus does not provide enough support for a reliable answer. Broaden the search or review source documents.</small></span></div>}<div className="answer-text"><CitationText text={answer.answer} citations={answer.citations} evidence={answer.evidence}/></div><div className="answer-metrics"><span>Evidence coverage <b>{Math.round((answer.coverage||0)*100)}%</b></span><span>Response time <b>{answer.latency_ms??'—'} ms</b></span><span>Provider <b>{answer.provider||'—'}</b></span></div><p className="answer-disclaimer">{answer.disclaimer||'Not legal advice. Check each source passage and use professional judgment.'}</p></article>
   <aside className="evidence-panel"><div className="evidence-heading"><div><span className="eyebrow">SOURCE MATERIAL</span><h2>Evidence <span>{answer.evidence?.length||0}</span></h2></div><BookOpenCheck size={16}/></div>{answer.evidence?.length?answer.evidence.map(item=><article className="evidence-source" key={item.chunk_id}><div className="evidence-source-heading"><div><b>{item.case_title}</b><small>{item.page_number?`Page ${item.page_number}`:'Page unavailable'}{item.section_type?` · ${item.section_type}`:''}</small></div><span className="source-verified">SOURCE</span></div><p>{item.text}</p><div className="evidence-source-foot"><span>{item.citation}</span><Link to={`/documents/${item.document_id}?page=${item.page_number}&chunk=${encodeURIComponent(item.chunk_id)}`}>Open passage <ArrowUpRight size={12}/></Link></div></article>):<div className="empty-inline">No supporting passages were returned.</div>}</aside>
  </div>}
 </section>
}
