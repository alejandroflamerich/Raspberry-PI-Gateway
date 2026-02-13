import React, { useEffect, useRef, useState } from 'react'
import Menu from '../components/Menu'
import api from '../services/api'
import './Easyberry.css'

type Exchange = {
  id?: string
  _uid?: string
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
  const runningRef = useRef<boolean>(running)
  const uidCounterRef = useRef<number>(0)
  function genUid(){ uidCounterRef.current += 1; return `uid-${Date.now()}-${uidCounterRef.current}-${Math.floor(Math.random()*1000)}` }
  function getKey(l: Exchange){
    const fallback = JSON.stringify([l.ts, l.direction, l.endpoint, l.note, l.body])
    return l.id || l._uid || fallback
  }
  function localTimestamp(){
    const d = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }

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
          if(it.request) out.push({id: it.id, ts: it.ts, direction: 'req', endpoint: it.endpoint || '-', body: it.request, content_type: it.content_type, note: it.note})
          if(it.response) out.push({id: it.id, ts: it.ts, direction: 'resp', endpoint: it.endpoint || '-', body: it.response, content_type: it.content_type, note: it.note})
        })
        if(mounted) setLines(prev => {
          const map = new Map<string, Exchange>()
          // keep previous entries first, then overwrite with new ones by id or _uid
          prev.forEach(it => map.set(getKey(it), it))
          out.forEach(it => map.set(getKey(it), it))
          const merged = Array.from(map.values())
          merged.sort((a,b)=> a.ts.localeCompare(b.ts))
          const sliced = merged.slice(-200)
          // ensure synthetic stable ids for entries without server-provided id
          sliced.forEach(it => { if(!it.id && !it._uid) it._uid = genUid() })
          return sliced
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
      const ts = localTimestamp()
      console.info(`${ts} - LOGIN -> url=${url} - payload=`, masked)

      // show request in page log
      pushLine({ ts, direction: 'req', endpoint: url, body: JSON.stringify(payload, null, 2), note: 'login request' })

      // trigger backend login and display server-provided details if it fails
      try{
        const r = await api.post('/easyberry/login')
        // show server response in page log (backend response)
        pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: url, body: JSON.stringify(r.data, null, 2), note: 'login response (backend)' })
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
          pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: url, body: bodyStr, note: `login error ${resp.status} (backend)` })
        }else{
          console.error('Login failed', err)
          pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: url, body: String(err), note: 'login exception' })
        }
        // also fetch easyberry exchanges so the actual server reply is shown if present
        try{ await fetchEasyberryPackets({ excludeNotes: ['start response','start error','started','start'] }) }catch(_e){ /* ignore */ }
      }
    }catch(e){ console.error('Login failed', e); pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: '-', body: String(e), note: 'login exception' }) }
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
        if(it.request && !isStartedPayload(it.request)) out.push({id: it.id, ts: it.ts, direction:'req', endpoint: it.endpoint, body: it.request, content_type: it.content_type, note: it.note})
        if(it.response && !isStartedPayload(it.response)) out.push({id: it.id, ts: it.ts, direction:'resp', endpoint: it.endpoint, body: it.response, content_type: it.content_type, note: it.note})
      })
      try{ console.debug('[Easyberry] fetched', out.length, 'items from /debug/easyberry', out.slice(-3)) }catch(e){}
      // NOTE: temporarily skip deduplication/merge to verify items are received
      try{ console.debug('[Easyberry] merging fetched items by id', out.length, 'items') }catch(e){}
      setLines(prev => {
        const map = new Map<string, Exchange>()
        prev.forEach(it => map.set(getKey(it), it))
        out.forEach(it => map.set(getKey(it), it))
        const merged = Array.from(map.values())
        merged.sort((a,b)=> a.ts.localeCompare(b.ts))
        const sliced = merged.slice(-200)
        sliced.forEach(it => { if(!it.id && !it._uid) it._uid = genUid() })
        try{ console.debug('[Easyberry] merged lines ->', sliced.length, 'last3', sliced.slice(-3)) }catch(e){}
        return sliced
      })
    }catch(e){ console.error('failed fetching easyberry packets', e) }
  }

  async function startEasyberryPolling(){
    try{
      // Optimistically mark running so UI updates immediately
      setRunning(true)
      runningRef.current = true
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
      const ts = localTimestamp()
      console.info(`${ts} - SENDING -> url=${url} - payload=`, payload)
      // show the put payload in the page log as a request
      pushLine({ ts, direction: 'req', endpoint: url, body: JSON.stringify(payload, null, 2), note: 'put payload' })

      // send current database values once via backend, then start polling
      try{
        const sendResp = await api.post('/easyberry/send')
        if(!isStartedPayload(sendResp.data)) pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: url, body: JSON.stringify(sendResp.data, null, 2), note: 'send response' })
      }catch(err:any){
        // revert optimistic UI state
        setRunning(false)
        console.error('Failed to send payload', err)
        const resp = err?.response
        const bodyStr = resp && resp.data ? (typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data, null, 2)) : String(err)
        pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: url, body: bodyStr, note: 'send error' })
        return
      }

      // start backend polling
      try{
        const r = await api.post('/easyberry/start')
        try{ console.debug('[Easyberry] start response', r.data) }catch(e){}
        // always push server response for debugging
        pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: url, body: JSON.stringify(r.data, null, 2), note: 'start response' })
        // if server indicates it didn't start, revert optimistic UI state
        const started = !!(r.data && (r.data.started === true || (typeof r.data === 'object' && r.data.started)) )
        if(!started){
          setRunning(false)
          try{ window.localStorage.removeItem('easyberry_user_started') }catch(e){}
          return
        }
      }catch(err:any){
        // revert optimistic UI state
        setRunning(false)
        console.error('Failed to start polling', err)
        const resp = err?.response
        const bodyStr = resp && resp.data ? (typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data, null, 2)) : String(err)
        pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: url, body: bodyStr, note: 'start error' })
        try{ window.localStorage.removeItem('easyberry_user_started') }catch(e){}
        return
      }

      // start refreshing exchanges while running
      if(!intervalRef.current){
        console.debug('[Easyberry] starting interval fetch for easyberry packets')
        intervalRef.current = window.setInterval(async ()=>{
          try{
            console.debug('[Easyberry] interval tick - fetching /debug/easyberry')
            const rr = await api.get('/debug/easyberry')
            const items = rr.data.easyberry || []
            console.debug('[Easyberry] interval fetched', items.length)
            const out: Exchange[] = []
            items.forEach((it:any)=>{
              if(it.request && !isStartedPayload(it.request)) out.push({id: it.id, ts: it.ts, direction:'req', endpoint: it.endpoint, body: it.request, content_type: it.content_type, note: it.note})
              if(it.response && !isStartedPayload(it.response)) out.push({id: it.id, ts: it.ts, direction:'resp', endpoint: it.endpoint, body: it.response, content_type: it.content_type, note: it.note})
            })
            console.debug('[Easyberry] interval built out items', out.length, 'from', items.length)
            // Merge by packet id to avoid duplicates
            setLines(prev => {
              const map = new Map<string, Exchange>()
              prev.forEach(it => map.set(getKey(it), it))
              out.forEach(it => map.set(getKey(it), it))
              const merged = Array.from(map.values())
              merged.sort((a,b)=> a.ts.localeCompare(b.ts))
              const sliced = merged.slice(-200)
              sliced.forEach(it => { if(!it.id && !it._uid) it._uid = genUid() })
              try{ console.debug('[Easyberry] interval merged lines ->', sliced.length, 'last3', sliced.slice(-3)) }catch(e){}
              return sliced
            })
          }catch(e){ console.error('[Easyberry] interval tick error', e) }
        }, 2000)
      }
    }catch(e){ console.error(e); pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: '-', body: String(e), note: 'start exception' }) }
  }

  async function stopEasyberryPolling(){
    try{
      await api.post('/easyberry/stop')
      setRunning(false)
      runningRef.current = false
      try{ window.localStorage.removeItem('easyberry_user_started') }catch(e){}
      if(intervalRef.current){
        console.debug('[Easyberry] clearing interval on stop')
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }catch(e){ console.error(e); pushLine({ ts: localTimestamp(), direction: 'resp', endpoint: '-', body: String(e), note: 'stop exception' }) }
  }

  function pushLine(entry: Exchange){
    try{ console.debug('[Easyberry] pushLine', entry) }catch(e){}
    setLines(prev => {
      if(!entry.id && !entry._uid) entry._uid = genUid()
      const next = [...prev, entry].slice(-200)
      try{
        ;(window as any).__easyberry_lines = next
        ;(window as any).__easyberry_state = { linesCount: next.length, loading, running: runningRef.current || Boolean(intervalRef.current) }
        console.debug('[Easyberry] exposed immediate state', (window as any).__easyberry_state)
      }catch(e){}
      return next
    })
  }

  // auto-scroll to bottom when lines change
  useEffect(()=>{
    try{ if(bodyRef.current){ bodyRef.current.scrollTop = bodyRef.current.scrollHeight } }catch(e){ }
  },[lines])

  // debug: log how many .eb-packet-line elements are present in the DOM after render
  useEffect(()=>{
    try{ console.debug('[Easyberry] DOM .eb-packet-line count after render ->', document.querySelectorAll('.eb-packet-line').length) }catch(e){}
  },[lines])

  // extra debug: when DOM count doesn't match state length, print mapping of ids
  useEffect(()=>{
    try{
      const dom = Array.from(document.querySelectorAll('.eb-packet-line')) as HTMLElement[]
      const domIds = dom.map(n => n.getAttribute('data-eb-id') || n.textContent || '(no-id)')
      if(dom.length !== lines.length){
        try{ console.warn('[Easyberry] MISMATCH: state.lines=', lines.length, 'DOM.nodes=', dom.length) }catch(e){}
        try{ console.debug('[Easyberry] state ids (last 20)=', (window as any).__easyberry_lines?.slice(-20).map((x:any)=> x.id || JSON.stringify([x.ts,x.direction]).slice(0,40))) }catch(e){}
        try{ console.debug('[Easyberry] dom data-eb-id (last 40)=', domIds.slice(-40)) }catch(e){}
      }
    }catch(e){}
  },[lines])

  // expose current lines/state for easier debugging in browser console
  useEffect(()=>{
    try{
      (window as any).__easyberry_lines = lines
      (window as any).__easyberry_state = { linesCount: lines.length, loading, running }
      console.debug('[Easyberry] exposed state', (window as any).__easyberry_state, 'last5', lines.slice(-5))
    }catch(e){}
  },[lines, loading, running])

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
      <main className="eb-easyberry-root">
        <h2>Easyberry Exchanges</h2>
        <div style={{marginBottom:8}}>
          <strong>Debug:</strong> Lines = {lines.length} {loading? '(loading)':''}
        </div>
        <div className="eb-top-actions">
          <div className="eb-left-actions">
            <button className="eb-auth-btn" onClick={doLogin}>App Login</button>
            
            <button className={`eb-toggle-btn ${running? 'on':''}`} onClick={()=>{ running? stopEasyberryPolling(): startEasyberryPolling() }}>{running? 'Stop Polling':'Start Easyberry Polling'}</button>
            <button className="eb-clear-btn" onClick={async ()=>{
              try{ await api.post('/debug/easyberry/clear'); setLines([]) }catch(e){ console.error(e); alert('Failed to clear console') }
            }}>Clear</button>
          </div>
          
        </div>

        <div className="eb-log-wrapper">
          <div className="eb-packet-header">
            <div>Time</div>
            <div>Endpoint</div>
            <div>Data</div>
          </div>

          <div className="eb-log-container" ref={bodyRef}>
            {loading && <div className="eb-loading">Loading...</div>}
            {!loading && lines.length===0 && <div className="eb-empty">No exchanges yet</div>}
            <ul className="eb-packet-list">
              {lines.map((l)=>{
                const key = getKey(l)
                return (
                  <li key={key} data-eb-id={key} className={`eb-packet-line ${l.direction}`}>
                    <div className="eb-pl-time">{l.ts}</div>
                    <div className="eb-pl-device">{l.endpoint} {l.content_type ? <span style={{marginLeft:8, color:'#666', fontSize:12}}>[{l.content_type}]</span> : null}</div>
                    <div className="eb-pl-data">{renderBody(l)}</div>
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
