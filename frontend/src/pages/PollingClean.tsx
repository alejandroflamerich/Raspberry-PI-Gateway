import React, { useEffect, useRef, useState } from 'react'
import Menu from '../components/Menu'
import api from '../services/api'
import './Slaves.css'

type PacketLine = {
  ts: string
  poller_id: string
  direction: 'req' | 'resp'
  data: string | null
  note?: string
  status?: string | null
}

export default function Slaves(){
  const [lines, setLines] = useState<PacketLine[]>([])
  const linesRef = useRef<PacketLine[]>(lines)
  const [loading, setLoading] = useState(true)
  const [deviceNames, setDeviceNames] = useState<Record<string,string>>({})
  const [devicesList, setDevicesList] = useState<any[]>([])
  const [pollerNames, setPollerNames] = useState<Record<string,string>>({})
  const [running, setRunning] = useState<boolean>(false)
  const intervalRef = useRef<number | null>(null)
  const userStarted = useRef<boolean>(false)
  const statusIntervalRef = useRef<number | null>(null)
  const bodyRef = useRef<HTMLDivElement | null>(null)
  const lastLoadId = useRef<number>(0)

  function normalizePollerId(raw:any){
    const s = String(raw || '').trim()
    // remove leading numeric prefix like "1-" if present
    return s.replace(/^\d+-/, '')
  }

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

  useEffect(()=>{ linesRef.current = lines }, [lines])

  // persist/restore lines across navigation to keep UI state immediate
  useEffect(()=>{
    try{
      const raw = window.sessionStorage.getItem('polling_lines_v1')
      if(raw){ const arr = JSON.parse(raw) as PacketLine[]; if(Array.isArray(arr) && arr.length>0) setLines(arr) }
    }catch(e){ }
    return ()=>{
      try{ window.sessionStorage.setItem('polling_lines_v1', JSON.stringify(linesRef.current.slice(-200))) }catch(e){}
    }
  }, [])

  useEffect(()=>{
    const reqId = { current: 0 }

    async function fetchPacketsOnce(){
      const my = ++reqId.current
      if(linesRef.current.length === 0) setLoading(true)
      try{
        console.debug('[PollingClean] fetchPacketsOnce start', my)
        const r = await api.get('/debug/packets')
        const items = r.data.packets || []
        const out: PacketLine[] = []
        items.forEach((it: any) => {
          if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status})
          if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
        })
        out.sort((a,b) => a.ts.localeCompare(b.ts))
        if(my === reqId.current){ setLines(out.slice()); console.debug('[PollingClean] fetchPacketsOnce setLines', out.length, 'req', my) }
      }catch(err){ console.error('[PollingClean] fetch error', err) }finally{ setLoading(false) }
    }

    function startLocalLoop(){ if(intervalRef.current) return; fetchPacketsOnce(); intervalRef.current = window.setInterval(fetchPacketsOnce, 2000) }
    function stopLocalLoop(){ if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null } }

    // initial fetch and start local loop so returning to the page resumes live updates
    fetchPacketsOnce()

    // load device names from polling config for display (poller id -> device.id)
    ;(async ()=>{
      try{
        const cfg = await api.get('/settings/polling')
        const data = cfg.data || {}
        const devices = Array.isArray(data.devices) ? data.devices : []
        const map: Record<string,string> = {}
        const pmap: Record<string,string> = {}
        devices.forEach((dev:any)=>{
          const devId = dev.id || dev.name || dev.label || String(dev.host || '')
          const pollers = Array.isArray(dev.pollers) ? dev.pollers : []
          pollers.forEach((p: any)=>{
            const pid = p && (p.id || (p.id === 0 ? 0 : undefined))
            const pidKey = pid !== undefined && pid !== null ? String(pid).trim() : undefined
            if(pidKey !== undefined && pidKey !== null){ map[pidKey] = String(devId) }
            const pname = p && (p.name || p.label || p.id)
            if(pidKey !== undefined && pidKey !== null && pname !== undefined && pname !== null){ pmap[pidKey] = String(pname).trim() }
          })
        })
        setDevicesList(devices)
        setDeviceNames(map)
        setPollerNames(pmap)
                try{ (window as any).__polling_devices = { map, devices }; console.debug('[PollingClean] device map', map) }catch(e){}
      }catch(e){ /* ignore */ }
    })()

    api.get('/debug/polling/status').then(r=>{
      const isRunning = Boolean(r.data.running)
      setRunning(isRunning)
      // always start the local refresh loop when mounting so UI updates resume
      startLocalLoop()
    }).catch(()=>{ startLocalLoop() })

    statusIntervalRef.current = window.setInterval(async ()=>{
      try{
        const r = await api.get('/debug/polling/status')
        const isRunning = Boolean(r.data.running)
        setRunning(isRunning)
        if(isRunning){ if(!intervalRef.current && !userStarted.current) startLocalLoop() }
        else { if(!userStarted.current && intervalRef.current){ stopLocalLoop() } }
      }catch(e){ }
    }, 2000)

    return ()=>{ stopLocalLoop(); if(statusIntervalRef.current){ clearInterval(statusIntervalRef.current); statusIntervalRef.current = null } }
  },[])

  useEffect(()=>{ console.debug('[PollingClean] lines updated', lines.length); if(bodyRef.current){ try{ bodyRef.current.scrollTop = bodyRef.current.scrollHeight }catch(e){}} },[lines])

  // expose current state for debugging from browser console
  useEffect(()=>{
    try{
      ;(window as any).__polling_state = { linesCount: lines.length, loading, running, lastLoadId: lastLoadId.current }
      console.debug('[PollingClean] exposed state', (window as any).__polling_state)
    }catch(e){}
  },[lines, loading, running])

  async function toggleRunning(){
    try{
      if(running){
        await api.post('/debug/polling/stop')
        setRunning(false); userStarted.current = false
        try{ window.localStorage.removeItem('modbus_user_started') }catch(e){}
        if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null }
        const r = await api.get('/debug/packets')
        const items = r.data.packets || []
        const out: PacketLine[] = []
        items.forEach((it: any) => {
          if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, poller_id: it.poller_id||'-', direction:'req', data: it.request, note: it.note, status: it.status})
          if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, poller_id: it.poller_id||'-', direction:'resp', data: it.response, note: it.note, status: it.status})
        })
        out.sort((a,b)=>a.ts.localeCompare(b.ts))
        setLines(out.slice())
      }else{
        try{ window.localStorage.setItem('modbus_user_started','1') }catch(e){}
        await api.post('/debug/polling/start')
        setRunning(true); userStarted.current = true
        if(!intervalRef.current){
          const r = await api.get('/debug/packets')
          const items = r.data.packets || []
          const out: PacketLine[] = []
          items.forEach((it: any) => {
            if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, poller_id: it.poller_id||'-', direction:'req', data: it.request, note: it.note, status: it.status})
            if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, poller_id: it.poller_id||'-', direction:'resp', data: it.response, note: it.note, status: it.status})
          })
          out.sort((a,b)=>a.ts.localeCompare(b.ts))
          setLines(out.slice())
          intervalRef.current = window.setInterval(async ()=>{
            try{
              const rr = await api.get('/debug/packets')
              const itms = rr.data.packets||[]
              const out2: PacketLine[] = []
              itms.forEach((it:any)=>{
                if(it.request && !isStartedPayload(it.request)) out2.push({ts:it.ts,poller_id:it.poller_id||'-',direction:'req',data:it.request,note:it.note,status:it.status})
                if(it.response && !isStartedPayload(it.response)) out2.push({ts:it.ts,poller_id:it.poller_id||'-',direction:'resp',data:it.response,note:it.note,status:it.status})
              })
              out2.sort((a,b)=>a.ts.localeCompare(b.ts))
              setLines(out2.slice())
            }catch(e){ console.error(e) }
          }, 2000)
        }
      }
    }catch(err){ console.error(err); alert('Failed to toggle polling') }
  }

  async function clearConsole(){ try{ await api.post('/debug/packets/clear'); setLines([]) }catch(err){ console.error(err); alert('Failed to clear console') } }

  return (
    <div>
      <Menu />
      <main className="sc-polling-root">
        <h2>Slaves</h2>
        <div style={{marginBottom:8}}>
          <strong>Debug:</strong> Lines = {lines.length} {loading? '(loading)':''}
        </div>
        <div className="sc-log-actions">
          <button className={`sc-toggle-btn ${running? 'on':''}`} onClick={toggleRunning}>{running? 'Stop Polling':'Start Polling'}</button>
          <button className="sc-clear-btn" onClick={clearConsole}>Clear</button>
        </div>
        <div className="sc-log-wrapper">
          <div className="sc-packet-header">
            <div>Time</div>
            <div>Device</div>
            <div>Poller</div>
            <div>Status</div>
            <div>Data</div>
          </div>

            <div className="sc-log-container" ref={bodyRef}>
          {loading && lines.length===0 && <div className="sc-loading">Loading...</div>}
          {!loading && lines.length===0 && <div className="sc-empty">No packets yet</div>}

          <ul className="sc-packet-list">
            {lines.map((l, idx)=> (
              <li key={idx} className={`sc-packet-line ${l.direction==='req'?'req':'resp'}`}>
                <div className="sc-pl-time">{l.ts}</div>
                <div className="sc-pl-device">{(()=>{
                    const lid = normalizePollerId(l.poller_id)
                    if(deviceNames[lid]) return deviceNames[lid]
                    for(const d of devicesList){
                      const pls = Array.isArray(d.pollers) ? d.pollers : []
                      if(pls.find((pp:any)=>{
                        const pid = String(pp.id || '').trim()
                        return pid === lid || pid.replace(/^\d+-/, '') === lid
                      })) return d.id || d.name || d.label || '-'
                    }
                    return '-'
                  })()}</div>
                <div className="sc-pl-poller">{pollerNames[String(l.poller_id)] || l.poller_id || '-'}</div>
                <div className="sc-pl-status-cell">{l.status ? <span className={`sc-pl-status ${l.status==='OK'?'ok':'err'}`}>{l.status}</span> : ''}</div>
                <div className="sc-pl-data">{l.data || '-'}</div>
              </li>
            ))}
          </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
