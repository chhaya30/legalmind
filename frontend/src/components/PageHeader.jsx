import {Link} from 'react-router-dom'
import {ArrowUpRight} from 'lucide-react'

export default function PageHeader({eyebrow,title,description,action}){
 return <div className="page-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action&&<Link className="button button-primary" to={action.to}>{action.label}<ArrowUpRight size={15}/></Link>}</div>
}
