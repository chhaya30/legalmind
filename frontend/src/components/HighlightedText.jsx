function escapeRegExp(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
export default function HighlightedText({text,terms=[]}){
 const unique=[...new Set(terms.filter(Boolean))].sort((a,b)=>b.length-a.length)
 if(!unique.length)return <>{text}</>
 const re=new RegExp(`(${unique.map(escapeRegExp).join('|')})`,'gi')
 return <>{text.split(re).map((part,i)=>unique.some(t=>t.toLowerCase()===part.toLowerCase())?<mark key={i}>{part}</mark>:part)}</>
}
