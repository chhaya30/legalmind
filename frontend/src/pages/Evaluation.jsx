import {useEffect,useState} from 'react'
import {Activity,ArrowDownToLine,ClipboardCheck,FileJson,FileSpreadsheet,Play,ShieldCheck} from 'lucide-react'
import {api} from '../services/api'
import PageHeader from '../components/PageHeader'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'

const labels={'precision@k':'Precision@K','recall@k':'Recall@K','mrr':'MRR','ndcg@k':'NDCG@K','citation_accuracy':'Citation accuracy','faithfulness':'Faithfulness','answer_relevance':'Answer relevance','latency_ms':'Latency','failure_rate':'Failure rate'}
function download(blob,filename){const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=filename;anchor.click();URL.revokeObjectURL(url)}

export default function Evaluation(){
 const [rows,setRows]=useState([]),[role,setRole]=useState(null),[username,setUsername]=useState('evaluator'),[password,setPassword]=useState(''),[runId,setRunId]=useState(''),[busy,setBusy]=useState(''),[error,setError]=useState(''),[notice,setNotice]=useState('')
 const loadResults=async id=>{const result=await api.evaluationResults(id||undefined);setRows(result);if(id)setRunId(id);return result}
 useEffect(()=>{api.me().then(async session=>{if(session.authenticated){setRole(session.role);try{await loadResults()}catch(e){setError(e.message)}}}).catch(()=>{})},[])
 const signIn=async event=>{event.preventDefault();setError('');try{const session=await api.login(username,password);setRole(session.role);setPassword('');await loadResults()}catch(e){setError(e.message)}}
 const run=async()=>{setBusy('run');setError('');setNotice('');try{const result=await api.evaluationRun();setRunId(result.run_id);await loadResults(result.run_id);setNotice(`Evaluation run completed · ${result.run_id}`)}catch(e){setError(e.message)}finally{setBusy('')}}
 const exportData=async format=>{setBusy(format);setError('');setNotice('');try{const blob=await api.evaluationExport(format);download(blob,`legalmind-evaluation.${format}`);setNotice(`${format.toUpperCase()} export downloaded.`)}catch(e){setError(e.message)}finally{setBusy('')}}
 const grouped=Object.groupBy?Object.groupBy(rows,row=>row.metric):rows.reduce((result,row)=>{(result[row.metric]??=[]).push(row);return result},{})
 const metrics=Object.entries(grouped).map(([name,items])=>({name,label:labels[name.toLowerCase()]||name.replaceAll('_',' '),count:items.length,value:items.reduce((sum,item)=>sum+Number(item.value||0),0)/items.length}))
 const order=['precision@k','recall@k','mrr','ndcg@k','citation_accuracy','faithfulness','answer_relevance','latency_ms','failure_rate']
 metrics.sort((a,b)=>{const ai=order.indexOf(a.name.toLowerCase()),bi=order.indexOf(b.name.toLowerCase());return(ai<0?99:ai)-(bi<0?99:bi)})
 return <section className="page-content"><PageHeader eyebrow="QUALITY / EVALUATION" title="Evaluation" description="Run the held-out benchmark and inspect retrieval, citation, and answer-quality metrics."/>
  {!role?<form className="access-form" onSubmit={signIn}><div className="card-heading"><span className="eyebrow">PROTECTED BENCHMARK</span><h2><ShieldCheck size={17}/> Evaluator or admin access</h2><p>Benchmark runs and stored results are protected by the backend session.</p></div><div className="form-grid"><label>Username<input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username"/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></label><button className="button button-primary" disabled={!password}>Sign in</button></div></form>:<><div className="evaluation-access"><div><span className="eyebrow">BENCHMARK CONTROL</span><b className="evaluation-role"><ShieldCheck size={13}/> {role} session verified</b></div><span className="evaluation-run-meta">{runId?`RUN ${runId}`:'Latest saved results'}</span><div className="evaluation-actions"><button className="button button-primary" onClick={run} disabled={!!busy}><Play size={13}/>{busy==='run'?'Running benchmark…':'Run evaluation'}</button><button className="button button-secondary" onClick={()=>loadResults()} disabled={!!busy}><Activity size={13}/>Refresh</button><button className="button button-quiet" onClick={()=>exportData('json')} disabled={!!busy}><FileJson size={13}/>{busy==='json'?'Preparing…':'JSON'}</button><button className="button button-quiet" onClick={()=>exportData('csv')} disabled={!!busy}><FileSpreadsheet size={13}/>{busy==='csv'?'Preparing…':'CSV'}</button></div></div>
   {error&&<ErrorState message={error}/>} {notice&&<div className="inline-success" role="status">{notice}</div>}
   {busy==='run'&&<LoadingState message="Running retrieval and answer evaluations…"/>}
   <section className="panel-card evaluation-results"><div className="card-topline"><div><span className="eyebrow">BENCHMARK OUTPUT</span><h2>Metric results</h2><p>{rows.length?`${rows.length} stored metric observations`:'Results from the selected evaluation run'}</p></div><ClipboardCheck size={15}/></div>{metrics.length?<div className="eval-grid">{metrics.map(item=><article className="eval-card" key={item.name}><b>{item.label}</b><strong>{item.value.toFixed(item.name==='latency_ms'?0:3)}{item.name==='failure_rate'?'%':''}</strong><span>{item.count} observation{item.count===1?'':'s'}</span></article>)}</div>:!busy&&<div className="empty-state"><span className="empty-icon"><Activity size={20}/></span><h2>No evaluation results yet</h2><p>Run the benchmark to create persisted metrics from the configured held-out cases.</p></div>}</section>
   <div className="evaluation-footnote"><span><ArrowDownToLine size={13}/> Exports include the backend’s stored result rows.</span><span>Benchmark relevance labels are maintained in the evaluation dataset.</span></div>
  </>}
 </section>
}
