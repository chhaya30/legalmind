import {useEffect,useState} from 'react'
import {ArrowDownToLine,FileJson,FileSpreadsheet,LockKeyhole,ShieldCheck} from 'lucide-react'
import {api} from '../services/api'
import PageHeader from '../components/PageHeader'
import ErrorState from '../components/ErrorState'

export default function Exports(){
 const [role,setRole]=useState(null),[username,setUsername]=useState('evaluator'),[password,setPassword]=useState(''),[busy,setBusy]=useState(''),[error,setError]=useState(''),[message,setMessage]=useState('')
 useEffect(()=>{api.me().then(session=>setRole(session.role||null)).catch(()=>setRole(null))},[])
 const signIn=async event=>{event.preventDefault();setError('');try{const session=await api.login(username,password);setRole(session.role);setPassword('')}catch(e){setError(e.message)}}
 const download=async format=>{setBusy(format);setError('');setMessage('');try{const blob=await api.evaluationExport(format);const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download=`legalmind-evaluation.${format}`;anchor.click();URL.revokeObjectURL(url);setMessage(`${format.toUpperCase()} evaluation export downloaded.`)}catch(e){setError(e.message)}finally{setBusy('')}}
 return <section className="page-content"><PageHeader eyebrow="DATA / EXPORTS" title="Exports" description="Download evaluation results from the protected LegalMind API."/>
  <div className="export-intro"><span className="export-lock"><ShieldCheck size={20}/></span><div><b>Protected evaluation data</b><p>Exports use your authenticated admin or evaluator session. Credentials stay in the server-side session cookie.</p></div></div>
  {!role?<form className="access-form" onSubmit={signIn}><div className="card-heading"><span className="eyebrow">AUTHENTICATION REQUIRED</span><h2><LockKeyhole size={18}/> Sign in to export</h2></div><div className="form-grid"><label>Username<input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username"/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></label><button className="button button-primary" disabled={!password}>Continue</button></div></form>:<div className="export-grid"><article className="export-card"><span className="export-format-icon json"><FileJson size={22}/></span><span className="eyebrow">STRUCTURED DATA</span><h2>JSON results</h2><p>Evaluation observations with run IDs, metric values, latency, and case details.</p><button className="button button-primary" disabled={!!busy} onClick={()=>download('json')}><ArrowDownToLine size={15}/>{busy==='json'?'Preparing…':'Download JSON'}</button></article><article className="export-card"><span className="export-format-icon csv"><FileSpreadsheet size={22}/></span><span className="eyebrow">SPREADSHEET DATA</span><h2>CSV results</h2><p>Tabular evaluation output suitable for spreadsheet review and analysis.</p><button className="button button-primary" disabled={!!busy} onClick={()=>download('csv')}><ArrowDownToLine size={15}/>{busy==='csv'?'Preparing…':'Download CSV'}</button></article></div>}
  {error&&<ErrorState message={error}/>} {message&&<div className="inline-success" role="status">{message}</div>}
 </section>
}
