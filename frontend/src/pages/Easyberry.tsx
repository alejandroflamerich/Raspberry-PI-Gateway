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
  const [settingsInfo, setSettingsInfo] = useState<{url?:string, username?:string, password?:string, context?:string, authPath?:string, token?:string}>({})
  const [showToken, setShowToken] = useState(false)
  const intervalRef = useRef<number | null>(null)
  const bodyRef = useRef<HTMLDivElement | null>(null)

  function isStartedPayload(raw: any){
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
        if(mounted) setLines(prev => {
          const map = new Map<string, Exchange>()
          ;[...prev, ...out].forEach(it => {
            const key = JSON.stringify([it.ts, it.direction, it.endpoint, it.note, it.body])
            map.set(key, it)
          })
          const merged = Array.from(map.values())
          merged.sort((a,b)=> a.ts.localeCompare(b.ts))
          return merged.slice(-200)
        })
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
          authPath: settings.authPath || 'auth',
          token: settings.token || ''
        })
      }catch(e){ console.error('failed loading settings', e) }
    }

    load()
    loadSettings()

    // if user previously started Easyberry polling from the UI, ensure backend is started
    try{
      const prev = window.localStorage.getItem('easyberry_user_started')
      if(prev){
        // try to (re)start backend polling but do not block UI
        (async ()=>{
          try{ await api.post('/easyberry/start'); setRunning(true) }catch(e){ /* ignore: backend may already be running or fail */ }
        })()
      }
    }catch(e){}

    return ()=>{ mounted=false; if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null } }
  },[])

  async function doLogin(){
    try{
      // Use settings already loaded in state when possible
      const st = settingsInfo || {}
      const base = (st.url || '').replace(/\/+$/,'')
      const context = (st.context || '').replace(/^\/+|\/+$/g, '')
      const authPath = st.authPath || 'auth'
      let url = ''
      // if authPath is already an absolute URL, use it as-is; otherwise build from base/context/authPath
      if (/^https?:\/\//i.test(authPath)) {
        url = authPath
      } else {
        url = [base, context, authPath].filter(Boolean).join('/')
      }
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
        // exclude start-related messages so we don't show the 'started' noise immediately after login
        await fetchEasyberryPackets({ excludeNotes: ['start response','start error','started','start'] })
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
        try{ await fetchEasyberryPackets({ excludeNotes: ['start response','start error','started','start'] }) }catch(_e){ /* ignore */ }
      }
    }catch(e){ console.error('Login failed', e); pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: '-', body: String(e), note: 'login exception' }) }
  }

  async function fetchEasyberryPackets(options?: { excludeNotes?: string[] }){
    try{
      const rr = await api.get('/debug/easyberry')
      const items = rr.data.easyberry || []
      const out: Exchange[] = []
      const exclude = (options && options.excludeNotes) || []
      items.forEach((it:any)=>{
        const note: string = (it.note || '')
        const skip = exclude.length > 0 && exclude.some(ex => note.includes(ex))
        if(skip) return
        if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, direction:'req', endpoint: it.endpoint, body: it.request, content_type: it.content_type, note: it.note})
        if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, direction:'resp', endpoint: it.endpoint, body: it.response, content_type: it.content_type, note: it.note})
      })
      // merge fetched items with existing lines (preserve recent local entries)
      setLines(prev => {
        const map = new Map<string, Exchange>()
        ;[...prev, ...out].forEach(it => {
          const key = JSON.stringify([it.ts, it.direction, it.endpoint, it.note, it.body])
          map.set(key, it)
        })
        const merged = Array.from(map.values())
        merged.sort((a,b)=> a.ts.localeCompare(b.ts))
        return merged.slice(-200)
      })
    }catch(e){ console.error('failed fetching easyberry packets', e) }
  }

  async function startEasyberryPolling(){
    try{
      // Optimistically mark running so UI updates immediately
      setRunning(true)
      // remember user explicitly started polling so it persists across pages
      try{ window.localStorage.setItem('easyberry_user_started','1') }catch(e){}

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

      // send current database values once via backend, then start polling
      try{
        const sendResp = await api.post('/easyberry/send')
        if(!isStartedPayload(sendResp.data)) pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: JSON.stringify(sendResp.data, null, 2), note: 'send response' })
      }catch(err:any){
        // revert optimistic UI state
        setRunning(false)
        console.error('Failed to send payload', err)
        const resp = err?.response
        const bodyStr = resp && resp.data ? (typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data, null, 2)) : String(err)
        pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: bodyStr, note: 'send error' })
        return
      }

      // start backend polling
      try{
        const r = await api.post('/easyberry/start')
        if(!isStartedPayload(r.data)) pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: JSON.stringify(r.data, null, 2), note: 'start response' })
      }catch(err:any){
        // revert optimistic UI state
        setRunning(false)
        console.error('Failed to start polling', err)
        const resp = err?.response
        const bodyStr = resp && resp.data ? (typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data, null, 2)) : String(err)
        pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: url, body: bodyStr, note: 'start error' })
        try{ window.localStorage.removeItem('easyberry_user_started') }catch(e){}
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
              if(it.request && !isStartedPayload(it.request)) out.push({ts: it.ts, direction:'req', endpoint: it.endpoint, body: it.request, content_type: it.content_type, note: it.note})
              if(it.response && !isStartedPayload(it.response)) out.push({ts: it.ts, direction:'resp', endpoint: it.endpoint, body: it.response, content_type: it.content_type, note: it.note})
            })
            setLines(prev => {
              const map = new Map<string, Exchange>()
              ;[...prev, ...out].forEach(it => {
                const key = JSON.stringify([it.ts, it.direction, it.endpoint, it.note, it.body])
                map.set(key, it)
              })
              const merged = Array.from(map.values())
              merged.sort((a,b)=> a.ts.localeCompare(b.ts))
              return merged.slice(-200)
            })
          }catch(e){ console.error(e) }
        }, 2000)
      }
    }catch(e){ console.error(e); pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: '-', body: String(e), note: 'start exception' }) }
  }

  async function stopEasyberryPolling(){
    try{ await api.post('/easyberry/stop'); setRunning(false); try{ window.localStorage.removeItem('easyberry_user_started') }catch(e){}; if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null } }catch(e){ console.error(e); pushLine({ ts: new Date().toISOString().replace('T',' ').split('.')[0], direction: 'resp', endpoint: '-', body: String(e), note: 'stop exception' }) }
  }

  function pushLine(entry: Exchange){
    setLines(prev => [...prev, entry].slice(-200))
  }

  // auto-scroll to bottom when lines change
  useEffect(()=>{
    try{ if(bodyRef.current){ bodyRef.current.scrollTop = bodyRef.current.scrollHeight } }catch(e){ }
  },[lines])

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
            <button className="clear-btn" onClick={async ()=>{
              try{ await api.post('/debug/easyberry/clear'); setLines([]) }catch(e){ console.error(e); alert('Failed to clear console') }
            }}>Clear</button>
          </div>
          
        </div>

        <div className="log-container" ref={bodyRef}>
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
