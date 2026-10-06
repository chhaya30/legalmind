import {useRef,useState} from 'react'
import {useNavigate} from 'react-router-dom'
import {ArrowUpToLine,FileText,LoaderCircle,UploadCloud} from 'lucide-react'
import {api} from '../services/api'

export default function QuickUpload(){
 const input=useRef(null),navigate=useNavigate(),[file,setFile]=useState(null),[progress,setProgress]=useState(0),[busy,setBusy]=useState(false),[error,setError]=useState(''),[dragging,setDragging]=useState(false)
 const choose=selected=>{const candidate=selected?.[0];if(!candidate)return;setError('');if(candidate.type!=='application/pdf'&&!candidate.name.toLowerCase().endsWith('.pdf')){setFile(null);setError('Select a PDF document.');return}setFile(candidate);setProgress(0)}
 const upload=async()=>{if(!file)return;setBusy(true);setError('');try{const result=await api.upload(file,setProgress);navigate(`/documents/${result.id}`)}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <section className={`quick-upload${dragging?' is-dragging':''}`} onDragOver={e=>{e.preventDefault();setDragging(true)}} onDragLeave={()=>setDragging(false)} onDrop={e=>{e.preventDefault();setDragging(false);choose(e.dataTransfer.files)}}>
  <div className="quick-upload-head"><span className="upload-glyph"><UploadCloud size={18}/></span><div><b>Upload judgment</b><small>Secure PDF ingestion</small></div></div>
  <button className="quick-upload-drop" onClick={()=>input.current?.click()}><span className="file-drop-icon">{file?<FileText size={18}/>:<ArrowUpToLine size={18}/>}</span><span><b>{file?file.name:'Drop a PDF or browse'}</b><small>{file?`${(file.size/1024/1024).toFixed(2)} MB · ready to process`:'PDF · max 15 MB'}</small></span></button>
  <input ref={input} type="file" accept="application/pdf,.pdf" hidden onChange={e=>choose(e.target.files)}/>
  {progress>0&&<div className="upload-progress"><span style={{width:`${progress}%`}}/></div>}
  {error&&<p className="quick-upload-error" role="alert">{error}</p>}
  {file?<div className="quick-upload-actions"><button className="button button-quiet button-small" onClick={()=>{setFile(null);setProgress(0)}} disabled={busy}>Remove</button><button className="button button-primary button-small" onClick={upload} disabled={busy}>{busy?<><LoaderCircle className="spin-icon" size={13}/>Uploading {progress}%</>:'Start processing'}</button></div>:<button className="button button-quiet button-small quick-browse" onClick={()=>input.current?.click()}>Choose file</button>}
 </section>
}
