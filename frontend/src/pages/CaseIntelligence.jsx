import {useEffect,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {ArrowUpRight,BookOpen,CalendarDays,FileSearch,Scale,UsersRound} from 'lucide-react'
import {api} from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const config={
 similar:{eyebrow:'CASE INTELLIGENCE / 01',title:'Similar cases',description:'Find judgments with related language, authorities, and legal issues.',icon:Scale},
 issues:{eyebrow:'CASE INTELLIGENCE / 02',title:'Issues & arguments',description:'Review extracted issues, parties, provisions, and their source pages.',icon:UsersRound},
 timeline:{eyebrow:'CASE INTELLIGENCE / 03',title:'Case timeline',description:'Follow dated events in their source-page order.',icon:CalendarDays},
}
const ENTITY_LABELS=['PARTY','PERSON','ACT','STATUTE','LEGAL_SECTION','PROVISION']

export default function CaseIntelligence({kind}){
 const [params,setParams]=useSearchParams()
 const selected=params.get('document')||''
 const [documents,setDocuments]=useState([]),[document,setDocument]=useState(null),[data,setData]=useState([]),[loading,setLoading]=useState(false),[error,setError]=useState('')
 const current=config[kind],Icon=current.icon

 useEffect(()=>{
  api.listDocuments({page_size:100,...(kind==='similar'?{status:'ready'}:{})}).then(setDocuments).catch(e=>setError(e.message))
 },[kind])

 useEffect(()=>{
  if(!selected){setDocument(null);setData([]);return}
  let active=true
  setLoading(true);setError('')
  const detail=api.getDocument(selected)
  const request=kind==='similar'?api.similar(selected,{top_k:10}):kind==='issues'?api.issues(selected):api.timeline(selected)
  Promise.all([detail,request]).then(([doc,result])=>{
   if(!active)return
   setDocument(doc)
   setData(kind==='similar'?result.results||[]:kind==='issues'?result.issues||[]:result.events||[])
  }).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)})
  return()=>{active=false}
 },[selected,kind])

 const setDocumentId=id=>setParams(id?{document:id}:{})
 return <section className="page-content">
  <PageHeader eyebrow={current.eyebrow} title={current.title} description={current.description} action={{to:'/documents',label:'Browse documents'}}/>
  <div className="tool-toolbar">
   <label className="select-field"><span>Source document</span><select value={selected} onChange={e=>setDocumentId(e.target.value)}><option value="">Choose a document</option>{documents.map(doc=><option value={doc.id} key={doc.id}>{doc.title||doc.filename}</option>)}</select></label>
   {document&&<Link className="button button-quiet" to={`/documents/${document.id}`}><BookOpen size={15}/> Open source</Link>}
  </div>
  {error&&<ErrorState message={error}/>}
  {!selected&&!error&&<div className="empty-state"><span className="empty-icon"><Icon size={22}/></span><h2>Select a judgment</h2><p>Choose a document to inspect real extracted case intelligence.</p></div>}
  {loading&&<LoadingState message={`Loading ${current.title.toLowerCase()}…`}/>}
  {document&&!loading&&<>
   <div className="source-strip"><div className="source-monogram"><FileSearch size={18}/></div><div><span className="eyebrow">SOURCE JUDGMENT</span><b>{document.title||document.filename}</b><small>{document.court||'Court not detected'}{document.case_number?` · ${document.case_number}`:''}</small></div><span className="source-pages">{document.page_count||0} pages</span></div>
   {kind==='similar'&&<div className="intelligence-list">
    {data.length?data.map((item,index)=><article className="intelligence-card similar-card" key={item.document_id}>
     <div className="rank-number">{String(index+1).padStart(2,'0')}</div><div className="intelligence-main">
      <div className="intelligence-card-head"><div><span className="eyebrow">{item.court||'COURT UNAVAILABLE'} · {item.category||'UNCLASSIFIED'}</span><h2>{item.title}</h2></div><strong className="score-dial">{Math.round(item.similarity_score*100)}<small>%</small></strong></div>
      <div className="overlap-metrics"><span>Semantic <b>{Math.round(item.semantic_score*100)}%</b></span><span>Entity overlap <b>{Math.round(item.entity_overlap*100)}%</b></span></div>
      <div className="reason-list">{item.why_similar.map(reason=><span key={reason}><Scale size={13}/>{reason}</span>)}</div>
      <div className="similar-page-refs"><Link to={`/documents/${document.id}?page=${item.target_page_number||1}`}>Source judgment · p.{item.target_page_number??'—'}</Link><Link to={`/documents/${item.document_id}?page=${item.source_page_number||1}`}>Related judgment · p.{item.source_page_number??'—'}</Link></div>
      <Link className="text-link" to={`/documents/${item.document_id}`}><BookOpen size={14}/> Open similar case <ArrowUpRight size={14}/></Link>
     </div>
    </article>):<div className="empty-state"><h2>No similar judgments found</h2><p>There are no other ready documents to compare against this judgment.</p></div>}
   </div>}
   {kind==='issues'&&<div className="intelligence-grid new-intelligence-grid">
    <article className="panel-card"><div className="card-heading"><span className="eyebrow">EXTRACTED FROM THE JUDGMENT</span><h2>Issues for determination <span>{data.length}</span></h2></div>
     {data.length?data.map((item,index)=><div className="issue-record" key={`${item.section_id}-${index}`}><span className="issue-index">{String(index+1).padStart(2,'0')}</span><div><p>{item.issue}</p><div className="source-line"><span>{item.section_id?'Judgment issue':'Question detected'}</span><span>Confidence {Math.round((item.confidence||0)*100)}%</span>{item.page_number&&<Link to={`/documents/${document.id}?page=${item.page_number}`}>Page {item.page_number} <ArrowUpRight size={12}/></Link>}</div></div></div>):<div className="empty-inline">No issue statements were detected in this document.</div>}
    </article>
    <article className="panel-card"><div className="card-heading"><span className="eyebrow">STRUCTURED AUTHORITIES</span><h2>Parties & provisions</h2></div>
     {document.entities.filter(entity=>ENTITY_LABELS.includes(entity.label)).length?document.entities.filter(entity=>ENTITY_LABELS.includes(entity.label)).map(entity=><div className="entity-record" key={entity.id}><span className="entity-kind">{entity.label.replace('_',' ')}</span><b>{entity.text}</b><span className="entity-detail">{Math.round(entity.confidence*100)}% confidence {entity.page_number&&`· p.${entity.page_number}`}</span></div>):<div className="empty-inline">No party or provision entities were extracted.</div>}
     <div className="card-subheading">Detected sections</div>
     {document.sections.length?document.sections.map(section=><Link className="section-record" key={section.id} to={`/documents/${document.id}?page=${section.page_number||1}`}><span>{section.section_type}</span><small>p.{section.page_number||'—'} · {Math.round(section.confidence*100)}%</small></Link>):<div className="empty-inline">No labeled sections found.</div>}
     <div className="card-subheading">Section text and reasoning</div>
     {document.sections.filter(section=>['FACTS','LAW','REASONING','JUDGMENT','ARGUMENTS'].includes(section.section_type)).map(section=><details className="reasoning-section" key={`text-${section.id}`}><summary>{section.section_type}<span>p.{section.page_number||'—'} · {Math.round(section.confidence*100)}%</span></summary><p>{section.text}</p><Link to={`/documents/${document.id}?page=${section.page_number||1}`}>Open source passage <ArrowUpRight size={12}/></Link></details>)}
    </article>
   </div>}
   {kind==='timeline'&&<div className="timeline-panel">
    {data.length?data.map((event,index)=><article className="timeline-record" key={`${event.source_page_id}-${index}`}><div className="timeline-rail"><span/><i/></div><div className="timeline-copy"><div className="timeline-record-head"><time>{event.date}</time><span>{event.date_text}</span></div><p>{event.event}</p><Link to={`/documents/${document.id}?page=${event.page_number}`}><BookOpen size={14}/> Source page {event.page_number} <ArrowUpRight size={13}/></Link></div></article>):<div className="empty-state"><h2>No dated events extracted</h2><p>This judgment contains no dates recognized by the current timeline extractor.</p></div>}
   </div>}
  </>}
 </section>
}
