import React, { useEffect, useRef, useState } from 'react'
import Menu from '../components/Menu'
import api from '../services/api'
import './Easyberry.css'

type Exchange = {
  ts: string
  direction: 'req' | 'resp'
  endpoint?: string
  body: string | null
  content_type?: string
  note?: string
}

export default function Easyberry(){
  const [lines, setLines] = useState<Exchange[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [settingsInfo, setSettingsInfo] = useState<{url?:string, username?:string, password?:string, context?:string, authPath?:string}>({})
  const intervalRef = useRef<number | null>(null)

  useEffect(()=>{
    let mounted = true
    async function load(){
      setLoading(true)
      try{
        const r = await api.get('/debug/easyberry')
        const items = r.data.easyberry || []
        const out: Exchange[] = []
        // Map to columns: ts, endpoint, request/response
        items.forEach((it: any)=>{
          if(it.request) out.push({ts: it.ts, direction: 'req', endpoint: it.endpoint || '-', body: it.request, content_type: it.content_type, note: it.note})
          if(it.response) out.push({ts: it.ts, direction: 'resp', endpoint: it.endpoint || '-', body: it.response, content_type: it.content_type, note: it.note})
        })
        if(mounted) setLines(out.reverse())
      }catch(err){ console.error(err) }
      finally{ if(mounted) setLoading(false) }
    }

    async function loadSettings(){
      try{
        const s = await api.get('/settings/easyberry')
        const settings = (s.data && s.data.settings) || {}
        setSettingsInfo({
          url: settings.url || '',
          username: settings.username || '',
          password: settings.password || '',
          context: settings.context || '',
          authPath: settings.authPath || 'auth'
        })
      }catch(e){ console.error('failed loading settings', e) }
    }

    load()
    loadSettings()

    return ()=>{ mounted=false; if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null } }
  },[])

  async function doLogin(){
    try{
      // Use settings already loaded in state when possible
      const st = settingsInfo || {}
      const base = (st.url || '').replace(/\/+$/,'')
      const context = (st.context || '').replace(/^\/+|\/+$/g, '')
      const authPath = st.authPath || 'auth'
      const url = [base, context, authPath].filter(Boolean).join('/')
      const payload = { username: st.username || '', password: st.password || '' }
      const masked = { username: payload.username, password: '***' }
      const ts = new Date().toISOString().replace('T',' ').split('.')[0]
      console.info(`${ts} - LOGIN -> url=${url} - payload=`, masked)

      // show request in page log
      pushLine({ ts, direction: 'req', endpoint: url, body: JSON.stringify(payload, null, 2), note: 'login request' })

      // trigger backend login and display server-provided details if it fails
      try{
        const r = await api.post('/easyberry/login')
        // show server response in page log (backend response)
        pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: JSON.stringify(r.data, null, 2), note: 'login response (backend)' })
        // refresh settings in case token persisted or fields changed
        try{ const s2 = await api.get('/settings/easyberry'); setSettingsInfo((s2.data && s2.data.settings) || {} ) }catch(_){ }
        // fetch and display any easyberry server exchanges that just occurred
        await fetchEasyberryPackets()
      }catch(err:any){
        // Log whatever the server returned so the user can inspect URL/payload and also show it on the page
        const resp = err?.response
        if(resp){
          console.error('Server response status:', resp.status)
          console.error('Server response body:', resp.data)
          const bodyStr = resp.data ? (typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data, null, 2)) : String(resp)
          pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: bodyStr, note: `login error ${resp.status} (backend)` })
        }else{
          console.error('Login failed', err)
          pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: String(err), note: 'login exception' })
        }
        // also fetch easyberry exchanges so the actual server reply is shown if present
        try{ await fetchEasyberryPackets() }catch(_e){ /* ignore */ }
      }
    }catch(e){ console.error('Login failed', e); pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: '-', body: String(e), note: 'login exception' }) }
  }

  async function fetchEasyberryPackets(){
    try{
      const rr = await api.get('/debug/easyberry')
      const items = rr.data.easyberry || []
      const out: Exchange[] = []
      items.forEach((it:any)=>{
        if(it.request) out.push({ts: it.ts, direction:'req', endpoint: it.endpoint, body: it.request, content_type: it.content_type, note: it.note})
        if(it.response) out.push({ts: it.ts, direction:'resp', endpoint: it.endpoint, body: it.response, content_type: it.content_type, note: it.note})
      })
      // prepend the fetched exchanges so they appear at top
      setLines(prev => [...out.reverse(), ...prev].slice(0,200))
    }catch(e){ console.error('failed fetching easyberry packets', e) }
  }

  async function startEasyberryPolling(){
    try{
      // Build payload from current database for display
      const db = await api.get('/debug/database')
      const pollers = (db.data && db.data.pollers) || []
      const things: Record<string, {value: string}> = {}
      pollers.forEach((p: any)=>{
        (p.things || []).forEach((t: any)=>{
          const name = t.name || t.id || t.mbid
          const val = t.value
          things[name] = { value: val === undefined || val === null ? '' : String(val) }
        })
      })

      // build target URL from settings
      const s = await api.get('/settings/easyberry')
      const settings = (s.data && s.data.settings) || {}
      const base = (settings.url || '').replace(/\/+$/,'')
      const context = (settings.context || '').replace(/^\/+|\/+$/g, '')
      const url = [base, context].filter(Boolean).join('/')

      const payload = { op: 'put', things }
      const ts = new Date().toISOString().replace('T',' ').split('.')[0]
      console.info(`${ts} - SENDING -> url=${url} - payload=`, payload)
      // show the put payload in the page log as a request
      pushLine({ ts, direction: 'req', endpoint: url, body: JSON.stringify(payload, null, 2), note: 'put payload' })

      // start backend polling
      try{
        const r = await api.post('/easyberry/start')
        setRunning(true)
        pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: JSON.stringify(r.data, null, 2), note: 'start response' })
      }catch(err:any){
        console.error('Failed to start polling', err)
        const resp = err?.response
        const bodyStr = resp && resp.data ? (typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data, null, 2)) : String(err)
        pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: bodyStr, note: 'start error' })
        return
      }

      // start refreshing exchanges while running
      if(!intervalRef.current){
        intervalRef.current = window.setInterval(async ()=>{
          try{
            const rr = await api.get('/debug/easyberry')
            const items = rr.data.easyberry || []
            const out: Exchange[] = []
            items.forEach((it:any)=>{
              if(it.request) out.push({ts: it.ts, direction:'req', endpoint: it.endpoint, body: it.request, content_type: it.content_type, note: it.note})
              if(it.response) out.push({ts: it.ts, direction:'resp', endpoint: it.endpoint, body: it.response, content_type: it.content_type, note: it.note})
            })
            setLines(out.reverse())
          }catch(e){ console.error(e) }
        }, 2000)
      }
    }catch(e){ console.error(e); pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: '-', body: String(e), note: 'start exception' }) }
  }

  async function stopEasyberryPolling(){
    try{ await api.post('/easyberry/stop'); setRunning(false); if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null } }catch(e){ console.error(e); pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: '-', body: String(e), note: 'stop exception' }) }
  }

  function pushLine(entry: Exchange){
    setLines(prev => [entry, ...prev].slice(0, 200))
  }

  function renderBody(l: Exchange){
    const raw = l.body || ''
    const ctype = (l.content_type || '').toLowerCase()
    // prefer content-type when available
    if(ctype.includes('application/json')){
      try{
        const obj = JSON.parse(raw)
        return <pre>{JSON.stringify(obj, null, 2)}</pre>
      }catch(e){
        return <pre>{raw}</pre>
      }
    }
    // try to detect JSON even without content-type
    try{
      if(raw && (raw.trim().startsWith('{') || raw.trim().startsWith('['))){
        const obj = JSON.parse(raw)
        return <pre>{JSON.stringify(obj, null, 2)}</pre>
      }
    }catch(e){ /* fallthrough */ }
    // if HTML, label it but show as text
    if(ctype.includes('html') || raw.trim().startsWith('<')){
      return <pre>{raw}</pre>
    }
    return <pre>{raw}</pre>
  }

  return (
    <div>
      <Menu />
      <main className="easyberry-root">
        <h2>Easyberry Exchanges</h2>
        <div className="eb-top-actions">
          <div className="left-actions">
            <button className="auth-btn" onClick={doLogin}>App Login</button>
            <button className={`toggle-btn ${running? 'on':''}`} onClick={()=>{ running? stopEasyberryPolling(): startEasyberryPolling() }}>{running? 'Stop Polling':'Start Easyberry Polling'}</button>
          </div>
          
        </div>

        <div className="log-container">
          {loading && <div className="loading">Loading...</div>}
          {!loading && lines.length===0 && <div className="empty">No exchanges yet</div>}
          <ul className="packet-list">
            {lines.map((l, idx)=> (
              <li key={idx} className={`packet-line ${l.direction}`}>
                <div className="pl-time">{l.ts}</div>
                <div className="pl-device">{l.endpoint} {l.content_type ? <span style={{marginLeft:8, color:'#666', fontSize:12}}>[{l.content_type}]</span> : null}</div>
                <div className="pl-data">{renderBody(l)}</div>
              </li>
            ))}
          </ul>
        </div>
      </main>
    </div>
  )
}
