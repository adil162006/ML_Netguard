import { lazy, Suspense } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { Activity, ArrowUpRight, ChartNoAxesCombined, CircleHelp, LayoutDashboard, Shield, ShieldAlert } from 'lucide-react'
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'))
const TrafficAnalysis = lazy(() => import('./pages/TrafficAnalysis.jsx'))
const ModelPerformance = lazy(() => import('./pages/ModelPerformance.jsx'))
const About = lazy(() => import('./pages/About.jsx'))

const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/analysis', label: 'Traffic Analysis', icon: Activity },
  { to: '/performance', label: 'Model Performance', icon: ChartNoAxesCombined },
  { to: '/about', label: 'About NetGuard', icon: CircleHelp },
]
export function PageHeader({ eyebrow, title, description, action }) { return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div> }
export function ErrorNotice({ error }) { return error ? <div className="notice error"><ShieldAlert size={18}/><span>{error.message}. Start the API and ensure training has completed.</span></div> : null }
export default function App() {
 return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-icon"><Shield size={21}/></div><div><b>NETGUARD</b><span>THREAT INTELLIGENCE</span></div></div><div className="nav-label">WORKSPACE</div><nav>{links.map(({to,label,icon:Icon,end})=><NavLink key={to} to={to} end={end} className={({isActive})=>`nav-link ${isActive?'active':''}`}><Icon size={18}/><span>{label}</span>{label==='Overview'&&<ArrowUpRight className="nav-arrow" size={14}/>}</NavLink>)}</nav><div className="sidebar-bottom"><div className="side-status"><span className="pulse-dot"/> Local analysis engine</div><div className="side-foot">UNSW-NB15 · Binary classifier<br/>Research demonstration</div></div></aside><main className="main-area"><header className="topbar"><div className="mobile-brand"><Shield size={18}/> NETGUARD</div><div className="breadcrumb">SECURITY OPERATIONS <span>/</span> CLASSIFICATION</div><div className="top-right"><span className="env-pill"><i/> LOCAL ENVIRONMENT</span><div className="avatar">NG</div></div></header><section className="content"><Suspense fallback={<div className="panel loading-state">Loading workspace…</div>}><Routes><Route path="/" element={<Dashboard/>}/><Route path="/analysis" element={<TrafficAnalysis/>}/><Route path="/performance" element={<ModelPerformance/>}/><Route path="/about" element={<About/>}/></Routes></Suspense></section><footer className="footer"><span>NETGUARD CLASSIFICATION SYSTEM</span><span>Submitted records only · No live packet capture</span></footer></main></div>
}
