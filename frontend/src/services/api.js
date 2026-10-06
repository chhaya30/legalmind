const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001/api/v1'
const protectedHeaders = () => ({})
async function request(path, options={}) {
  const res = await fetch(`${API}${path}`, {...options, credentials:'include'})
  const data = await res.json().catch(()=>({message:'Unexpected server response'}))
  if (!res.ok) {
    const detail = data?.detail?.message || data?.message || 'Request failed'
    throw new Error(detail)
  }
  return data
}
export const api = {
  health:()=>request('/health'),
  login:(username,password)=>request('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})}),
  logout:()=>request('/auth/logout',{method:'POST'}),
  me:()=>request('/auth/me'),
  listDocuments:(params={})=>{const query=new URLSearchParams({page:String(params.page||1),page_size:String(params.page_size||20),sort:params.sort||'created_at_desc'});if(params.q)query.set('q',params.q);if(params.status)query.set('status',params.status);if(params.category)query.set('category',params.category);return request(`/documents?${query}`)},
  getDocument:(id)=>request(`/documents/${id}`),
  getPage:(id,page)=>request(`/documents/${id}/pages/${page}`),
  getChunk:(id)=>request(`/chunks/${id}`),
  upload:async(file,onProgress)=>{
    const xhr = new XMLHttpRequest()
    return new Promise((resolve,reject)=>{
      xhr.open('POST',`${API}/documents/upload`); xhr.withCredentials=true
      xhr.responseType='json'
      xhr.upload.onprogress=e=>{ if(e.lengthComputable) onProgress?.(Math.round(e.loaded/e.total*100)) }
      xhr.onload=()=>xhr.status>=200&&xhr.status<300?resolve(xhr.response):reject(new Error(xhr.response?.message || xhr.response?.detail?.message || 'Upload failed'))
      xhr.onerror=()=>reject(new Error('Network error'))
      const form=new FormData(); form.append('file',file); xhr.send(form)
    })
  },
  remove:(id)=>request(`/documents/${id}`,{method:'DELETE'}),
  search:(body)=>request('/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
  ask:(body)=>request('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
  similar:(id,body={})=>request(`/similar/${id}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
  issues:(id)=>request(`/documents/${id}/issues`),
  timeline:(id)=>request(`/documents/${id}/timeline`),
  compare:(body)=>request('/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),
  analytics:(params={})=>{const query=new URLSearchParams();if(params.date_from)query.set('date_from',params.date_from);if(params.date_to)query.set('date_to',params.date_to);return request(`/analytics${query.size?`?${query}`:''}`,{headers:protectedHeaders()})},
  nlpModel:()=>request('/nlp/model'),
  metrics:()=>request('/metrics'),
  evaluationRun:()=>request('/evaluation/run',{method:'POST',headers:protectedHeaders()}),
  evaluationResults:(runId)=>request(`/evaluation/results${runId?`?run_id=${runId}`:''}`,{headers:protectedHeaders()}),
  evaluationExport:async(fmt)=>{const r=await fetch(`${API}/evaluation/export?fmt=${fmt}`,{headers:protectedHeaders(),credentials:'include'});if(!r.ok){const data=await r.json().catch(()=>({}));throw new Error(data.message||'Export failed')}return r.blob()}

}
