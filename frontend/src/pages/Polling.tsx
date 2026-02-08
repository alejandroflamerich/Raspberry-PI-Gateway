
import React, { useEffect, useRef, useState } from 'react'
import Menu from '../components/Menu'
import api from '../services/api'
import './Polling.css'

type PacketLine = {
  ts: string
  poller_id: string
  direction: 'req' | 'resp'
  data: string | null
  note?: string
  status?: string | null
}

export default function Polling(){
  const [lines, setLines] = useState<PacketLine[]>([])
  const linesRef = useRef<PacketLine[]>(lines)
  const bodyRef = useRef<HTMLDivElement | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState<boolean>(false)
  const intervalRef = useRef<number | null>(null)
  const userStarted = useRef<boolean>(false)
  const statusIntervalRef = useRef<number | null>(null)
  const lastLoadId = useRef<number>(0)

  // keep a ref in sync to avoid stale closures inside async loops
  useEffect(()=>{ linesRef.current = lines }, [lines])

  // restore previous lines from sessionStorage when remounting, so UI shows history immediately
  useEffect(()=>{
    try{
      const raw = window.sessionStorage.getItem('polling_lines_v1')
      if(raw){ const arr = JSON.parse(raw) as PacketLine[]; if(Array.isArray(arr) && arr.length>0) setLines(arr) }
    }catch(e){ /* ignore parse errors */ }
    return ()=>{
      try{ window.sessionStorage.setItem('polling_lines_v1', JSON.stringify(linesRef.current.slice(-200))) }catch(e){}
    }
  }, [])

  function isStartedPayload(raw:any){
    if(raw === null || raw === undefined) return false
    if(typeof raw === 'object') return raw.started === true
    if(typeof raw === 'string'){
      const s = raw.trim()
      try{ const o = JSON.parse(s); return o && o.started === true }catch(e){}
      return s.indexOf('"started": true') !== -1 || s.indexOf("'started': true") !== -1
    }
    return false
  }

  useEffect(()=>{
    const req = { current: 0 }

    async function fetchPacketsOnce(){
      const my = ++req.current
      if(linesRef.current.length === 0) setLoading(true)
      try{
        console.debug('[Polling] fetchPacketsOnce start', my)
        const r = await api.get('/debug/packets')
        const items = r.data.packets || []
        const out: PacketLine[] = []
        items.forEach((it: any) => {
          if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status})
          if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
        })
        out.sort((a,b)=>a.ts.localeCompare(b.ts))
        if(my === req.current){ setLines(out.slice()); console.debug('[Polling] fetchPacketsOnce setLines', out.length, 'req', my) }
      }catch(err){ console.error('[Polling] fetch error', err) }finally{ setLoading(false) }
    }

    function startLocalLoop(){ if(intervalRef.current) return; fetchPacketsOnce(); intervalRef.current = window.setInterval(fetchPacketsOnce, 2000) }
    function stopLocalLoop(){ if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null } }

    // initial fetch and always start local loop so returning to page resumes live updates
    fetchPacketsOnce()

    api.get('/debug/polling/status').then(r=>{
      const isRunning = Boolean(r.data.running)
      setRunning(isRunning)
      startLocalLoop()
    }).catch(()=>{ startLocalLoop() })

    // if user previously started modbus polling from the UI, ensure backend is started
    try{
      const prev = window.localStorage.getItem('modbus_user_started')
      if(prev){
        (async ()=>{
          try{ await api.post('/debug/polling/start'); setRunning(true); userStarted.current = true; startLocalLoop() }catch(e){ /* ignore */ }
        })()
      }
    }catch(e){}

    // poll backend status every 2s and if backend becomes active start loop
    statusIntervalRef.current = window.setInterval(async ()=>{
      try{
        const r = await api.get('/debug/polling/status')
        const isRunning = Boolean(r.data.running)
        setRunning(isRunning)
        if(isRunning){ if(!intervalRef.current && !userStarted.current) startLocalLoop() }
        else { if(!userStarted.current && intervalRef.current){ stopLocalLoop() } }
      }catch(e){ /* ignore status poll errors */ }
    }, 2000)

    return ()=>{ stopLocalLoop(); if(statusIntervalRef.current){ clearInterval(statusIntervalRef.current); statusIntervalRef.current = null } }
  },[])

  async function toggleRunning(){
    try{
      if(running){
        // user pressed Stop: stop backend and stop local loop
        await api.post('/debug/polling/stop')
        setRunning(false)
        userStarted.current = false
        try{ window.localStorage.removeItem('modbus_user_started') }catch(e){}
        // stop interval
        if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null }
        // refresh once
        const r = await api.get('/debug/packets')
        const items = r.data.packets || []
        const out: PacketLine[] = []
          function isStartedPayload(raw:any){
            if(raw === null || raw === undefined) return false
            if(typeof raw === 'object') return raw.started === true
            if(typeof raw === 'string'){
              const s = raw.trim()
              try{ const o = JSON.parse(s); return o && o.started === true }catch(e){}
              return s.indexOf('"started": true') !== -1 || s.indexOf("'started': true") !== -1
            }
            return false
          }
        items.forEach((it: any) => {
              if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status}); 
            if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
        })
        out.sort((a,b)=>a.ts.localeCompare(b.ts))
        setLines(out.slice())
      }else{
        // user pressed Start: optimistically mark running immediately,
        // remember user intent and call backend to start polling and begin local loop.
        setRunning(true)
        userStarted.current = true
        try{ window.localStorage.setItem('modbus_user_started','1') }catch(e){}
        try{
          await api.post('/debug/polling/start')
        }catch(err){
          // revert optimistic state on failure
          setRunning(false)
          userStarted.current = false
          try{ window.localStorage.removeItem('modbus_user_started') }catch(e){}
          throw err
        }
        // start loop
        if(!intervalRef.current){
          // immediate fetch and then interval
          const r = await api.get('/debug/packets')
          const items = r.data.packets || []
          const out: PacketLine[] = []
          items.forEach((it: any) => {
            if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status})
            if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
          })
          out.sort((a,b)=>a.ts.localeCompare(b.ts))
          setLines(out.slice())
          intervalRef.current = window.setInterval(async ()=>{
            try{
              const rr = await api.get('/debug/packets')
              const itms = rr.data.packets || []
              const out2: PacketLine[] = []
              itms.forEach((it: any) => {
                if(it.request && !isStartedPayload(it.request)) out2.push({ts: it.ts, poller_id: it.poller_id||'-', direction:'req', data: it.request, note: it.note, status: it.status})
                if(it.response && !isStartedPayload(it.response)) out2.push({ts: it.ts, poller_id: it.poller_id||'-', direction:'resp', data: it.response, note: it.note, status: it.status})
              })
              out2.sort((a,b)=>a.ts.localeCompare(b.ts))
              setLines(out2.slice())
            }catch(e){ console.error(e) }
          }, 2000)
        }
      }
    }catch(err){
      console.error(err)
      alert('Failed to toggle polling')
    }
  }

  async function clearConsole(){
    try{
      await api.post('/debug/packets/clear')
      setLines([])
    }catch(err){
      console.error(err)
      alert('Failed to clear console')
    }
  }

  return (
    <div>
      <Menu />
      <main className="polling-root">
        <h2>Polling Packet Log</h2>
        <div className="log-actions">
          <button className={`toggle-btn ${running? 'on':''}`} onClick={toggleRunning}>{running? 'Stop Polling':'Start Polling'}</button>
          <button className="clear-btn" onClick={clearConsole}>Clear</button>
        </div>
        <div className="log-container">
          {loading && lines.length===0 && <div className="loading">Loading...</div>}
          {!loading && lines.length===0 && <div className="empty">No packets yet</div>}
          <ul className="packet-list">
            {lines.map((l, idx)=> (
              <li key={idx} className={`packet-line ${l.direction==='req'?'req':'resp'}`}>
                <div className="pl-time">{l.ts}</div>
                <div className="pl-device">{l.poller_id} {l.status && <span className={`pl-status ${l.status==='OK'?'ok':'err'}`}>{l.status}</span>}</div>
                <div className="pl-data">{l.data || '-'}</div>
              </li>
            ))}
          </ul>
        </div>
      </main>
    </div>
  )
}
