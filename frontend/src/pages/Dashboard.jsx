import {useEffect,useState} from 'react'
import {Link,useNavigate} from 'react-router-dom'
import {Activity,ArrowRight,ArrowUpRight,Clock3,FileSearch,Files,GitCompareArrows,ListChecks,Search,ShieldAlert,Sparkles,Upload,Workflow} from 'lucide-react'
import {api} from '../services/api'
import QuickUpload from '../components/QuickUpload'
import StatusBadge from '../components/StatusBadge'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const actions=[
 ['/ask',Sparkles,'Ask LegalMind','Evidence-grounded research'],
 ['/search',Search,'Search documents','Keyword, semantic, hybrid'],
 ['/similar',GitCompareArrows,'Similar cases','Related judgments'],
 ['/issues',ListChecks,'Extract issues','Issues and provisions'],
 ['/timeline',Clock3,'Build a timeline','Dated case events'],
 ['/compare',Workflow,'Compare documents','Align legal reasoning'],
]
const greeting=()=>{const hour=new Date().getHours();return hour<12?'Good morning':hour<18?'Good afternoon':'Good evening'}

export default function Dashboard(){
 const navigate=useNavigate(),[documents,setDocuments]=useState([]),[metrics,setMetrics]=useState(null),[analytics,setAnalytics]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[question,setQuestion]=useState('')
 const load=async(includeProtectedAnalytics=false)=>{setError('');try{const [docRows,counters]=await Promise.all([api.listDocuments({page_size:8}),api.metrics()]);setDocuments(docRows);setMetrics(counters);if(includeProtectedAnalytics){try{const session=await api.me();if(session.authenticated)setAnalytics(await api.analytics())}catch{setAnalytics(null)}}}catch(e){setError(e.message)}finally{setLoading(false)}}
 useEffect(()=>{load(true);const timer=setInterval(()=>load(false),30000);return()=>clearInterval(timer)},[])
 const ask=e=>{e.preventDefault();if(question.trim())navigate(`/ask?q=${encodeURIComponent(question.trim())}`)}
 const activity=analytics?.search_activity||[],maxActivity=Math.max(1,...activity.map(row=>row.count))
 const values=[
  ['Corpus documents',metrics?.documents_total??'—',Files,'Across this workspace',''],
  ['Ready to research',metrics?.documents_ready??'—',FileSearch,'Indexed and available','positive'],
  ['Processing',metrics?.documents_processing??'—',Workflow,'Ingestion pipeline',''],
  ['Failed jobs',metrics?.documents_failed??'—',ShieldAlert,'Needs review','alert'],
  ['Searches',metrics?.search_events??'—',Search,'Retrieval events',''],
 ]
 return <section className="page-content dashboard-page">
  <div className="dashboard-welcome"><section className="welcome-main"><span className="eyebrow">Legal document intelligence</span><h2>{greeting()}. Let’s review the record.</h2><p>Search judgments, inspect the cited passage, and keep every conclusion anchored to its source.</p><div className="welcome-actions"><Link className="button button-primary" to="/upload"><Upload size={14}/> Add a judgment</Link><Link className="button button-quiet" to="/documents">Open corpus <ArrowRight size={14}/></Link></div></section><QuickUpload/></div>
  <div className="metric-grid">{values.map(([label,value,Icon,detail,tone])=><article className={`metric-card ${tone}`} key={label}><div className="metric-card-head"><span>{label}</span><span className="metric-icon"><Icon size={14}/></span></div><strong>{value}</strong><small>{detail}</small></article>)}</div>
  {error&&<ErrorState message={error} onRetry={load}/>}
  <div className="dashboard-grid"><section className="panel-card quick-actions-card"><div className="card-topline"><div><span className="eyebrow">SHORTCUTS</span><h2>Research tools</h2></div><span className="muted">Choose an analysis</span></div><div className="quick-action-grid">{actions.map(([to,Icon,title,description])=><Link className="quick-action" to={to} key={to} aria-label={title==='Ask LegalMind'?'Open assistant research workspace':undefined}><span className="quick-action-icon"><Icon size={15}/></span><span><b>{title}</b><small>{description}</small></span></Link>)}</div></section>
   <section className="panel-card assistant-preview"><div><div className="assistant-heading"><span className="assistant-glyph"><Sparkles size={16}/></span><span><b>LegalMind assistant</b><small>Document-grounded research</small></span></div><p>Ask a question across your indexed corpus. Answers include the supporting passages and page citations.</p></div><form className="assistant-form" onSubmit={ask}><input aria-label="Ask LegalMind a question" value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask about a provision or holding…"/><button className="assistant-send" aria-label="Send question" disabled={!question.trim()}><ArrowUpRight size={15}/></button></form><Link className="text-link assistant-open" to="/ask">Open research workspace <ArrowRight size={13}/></Link></section>
  </div>
  <div className="dashboard-bottom"><section className="panel-card recent-card"><div className="card-topline"><div><span className="eyebrow">YOUR CORPUS</span><h2>Recent documents</h2><p>Latest documents from the live database</p></div><Link to="/documents">View all <ArrowUpRight size={13}/></Link></div>{loading&&!documents.length?<LoadingState message="Loading corpus…"/>:error&&!documents.length?null:documents.length?<div className="document-list">{documents.slice(0,6).map(doc=><Link className="document-row" key={doc.id} to={`/documents/${doc.id}`}><span className="file-mark">PDF</span><span className="document-copy"><b>{doc.title||doc.filename}</b><small>{doc.case_number||doc.court||'Court not detected'}{doc.category?` · ${doc.category}`:''}</small></span><StatusBadge status={doc.status}/></Link>)}</div>:<div className="empty-inline">No documents yet. Upload a judgment to start the corpus.</div>}</section>
   <div className="dashboard-side-stack"><section className="panel-card analytics-preview"><div className="card-topline"><div><span className="eyebrow">ACTIVITY</span><h2>Search overview</h2></div><Link to="/analytics">Analytics <ArrowUpRight size={13}/></Link></div>{analytics?<div className="analytics-preview-body">{activity.length?<><div className="activity-bars" aria-label="Searches by date">{activity.slice(-14).map((row,index)=><span className="activity-bar" key={`${row.date}-${index}`} style={{'--bar-height':`${Math.max(6,Math.round(row.count/maxActivity*100))}%`}} title={`${row.date}: ${row.count} searches`}/>)}</div><div className="activity-labels"><span>{activity.at(-14)?.date||activity[0]?.date}</span><span>{activity.at(-1)?.date}</span></div></>:<div className="chart-empty">No search activity recorded for this period.</div>}</div>:<div className="locked-analytics"><ShieldAlert size={15}/><span>Sign in to view protected analytics.</span><Link to="/analytics">Open analytics</Link></div>}</section>
    <section className="panel-card queries-card"><div className="card-topline"><div><span className="eyebrow">RETRIEVAL</span><h2>Top search queries</h2></div><Activity size={14}/></div>{analytics?.top_queries?.length?analytics.top_queries.slice(0,4).map((item,index)=><div className="query-row" key={`${item.query}-${index}`}><span className="query-index">0{index+1}</span><span className="query-text" title={item.query}>{item.query}</span><span className="query-count">{item.count}</span></div>):<div className="locked-analytics"><span>{analytics?'Search queries will appear after searches are recorded.':'Available to an authenticated evaluator or admin.'}</span>{!analytics&&<Link to="/analytics">Sign in</Link>}</div>}</section></div>
  </div>
 </section>
}
