import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import './Menu.css'

type MenuItem = 'dashboard' | 'easyberry' | 'slaves' | 'setting' | 'logout'

export default function Menu({ onSelect }:{ onSelect?: (m:MenuItem)=>void }){
  const [active, setActive] = useState<MenuItem>('dashboard')
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(()=>{
    // derive active tab from location pathname so UI reflects route changes
    const p = location.pathname || ''
    if(p.startsWith('/easyberry')) setActive('easyberry')
    else if(p.startsWith('/slaves')) setActive('slaves')
    else if(p.startsWith('/setting')) setActive('setting')
    else if(p.startsWith('/login')) setActive('logout')
    else setActive('dashboard')
  }, [location.pathname])

  function handleClick(item: MenuItem){
    setActive(item)
    if(onSelect) onSelect(item)
    // navigate to route when clicked
    if(item === 'dashboard') navigate('/dashboard')
    if(item === 'easyberry') navigate('/easyberry')
    if(item === 'slaves') navigate('/slaves')
    if(item === 'setting') navigate('/setting')
    if(item === 'logout') navigate('/login')
  }

  return (
    <aside className="app-sidebar" role="navigation" aria-label="Main menu">
      <div className="sidebar-top">
        <div className="sidebar-brand">Easyberry</div>
        <div className="sidebar-items">
          <button className={`sidebar-btn ${active==='dashboard'?'active':''}`} onClick={()=>handleClick('dashboard')}>Dashboard</button>
          <button className={`sidebar-btn ${active==='easyberry'?'active':''}`} onClick={()=>handleClick('easyberry')}>Easyberry</button>
          <button className={`sidebar-btn ${active==='slaves'?'active':''}`} onClick={()=>handleClick('slaves')}>Slaves</button>
          <button className={`sidebar-btn ${active==='setting'?'active':''}`} onClick={()=>handleClick('setting')}>Setting</button>
        </div>
      </div>
      <div className="sidebar-footer">
        <button className={`sidebar-btn logout ${active==='logout'?'active':''}`} onClick={()=>handleClick('logout')}>Logout</button>
      </div>
    </aside>
  )
}

