import React, { useEffect, useState, useRef } from 'react'
import api from '../../services/api'
import './console.css'

type Entry = { ts: string; cmd: string; ok: boolean; out?: string; err?: string }

export default function Console(){
  const [open, setOpen] = useState<boolean>(false)
  const [input, setInput] = useState<string>('')
  const [history, setHistory] = useState<Entry[]>(() => {
    try{ const s = window.localStorage.getItem('console_history'); return s? JSON.parse(s): [] }catch(e){ return [] }
  })
  const [histIdx, setHistIdx] = useState<number | null>(null)
  const bodyRef = useRef<HTMLDivElement | null>(null)

  useEffect(()=>{
    function onKey(e: KeyboardEvent){
      if(e.key === '`') { setOpen(o=>!o); e.preventDefault() }
      if(e.key === 'Escape') setOpen(false)
      if(open && (e.key === 'ArrowUp' || e.key === 'ArrowDown')){
        e.preventDefault()
        if(history.length===0) return
        if(histIdx===null) setHistIdx(history.length-1)
        else{
          const next = e.key === 'ArrowUp' ? Math.max(0, histIdx-1) : Math.min(history.length-1, histIdx+1)
          setHistIdx(next)
          setInput(history[next].cmd)
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return ()=> window.removeEventListener('keydown', onKey)
  },[open, history, histIdx])

  useEffect(()=>{ window.localStorage.setItem('console_history', JSON.stringify(history)) },[history])

  useEffect(()=>{ if(bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight },[history, open])

  async function runCommand(cmdline: string){
    const ts = new Date().toISOString().replace('T',' ').split('.')[0]
    const parts = cmdline.trim().split(/\s+/)
    const cmd = parts[0]
    // parse args as simple key=value pairs (basic)
    const args: any = {}
    parts.slice(1).forEach(p=>{
      const [k,v] = p.split('=')
      if(v===undefined) args[k] = true
      else if(/^[0-9]+$/.test(v)) args[k] = Number(v)
      else args[k] = v
    })
    // optimistic push at the end
    setHistory(h => [...h, { ts, cmd: cmdline, ok: false, out: '...' }])
    try{
      const r = await api.post('/cli/execute', { command: cmd, args })
      const data = r.data
      const out = data.output || JSON.stringify(data.data || data, null, 2)
      // replace last placeholder with actual result
      setHistory(h => {
        if (h.length === 0) return [{ ts, cmd: cmdline, ok: data.ok, out, err: data.error || '' }]
        const nh = [...h]
        nh[nh.length - 1] = { ts, cmd: cmdline, ok: data.ok, out, err: data.error || '' }
        return nh
      })
    }catch(err:any){
      const msg = err?.response?.data?.detail || err.message || String(err)
      setHistory(h => {
        if (h.length === 0) return [{ ts, cmd: cmdline, ok: false, out: '', err: String(msg) }]
        const nh = [...h]
        nh[nh.length - 1] = { ts, cmd: cmdline, ok: false, out: '', err: String(msg) }
        return nh
      })
    }
    setInput('')
    setHistIdx(null)
  }

  function clearHistory(){ setHistory([]) }

  async function showCommands(){
    try{
      const r = await api.get('/cli/commands')
      const list = r.data || []
      const ts = new Date().toISOString().replace('T',' ').split('.')[0]
      setHistory(h => [...h, { ts, cmd: 'commands', ok: true, out: JSON.stringify(list, null, 2) }])
    }catch(e){ console.error(e); alert('Failed to load commands') }
  }

  return (
    <div className={open? 'console-root':'console-collapsed'}>
      {open ? (
        <div className="console-dock" role="dialog" aria-label="command console">
          <div className="console-header">
            <div className="console-title">Console</div>
            <div style={{display:'flex',gap:8}}>
              <button className="console-small-btn" onClick={showCommands}>Commands</button>
              <button className="console-small-btn" onClick={clearHistory}>Clear</button>
              <button className="console-small-btn" onClick={()=>setOpen(false)}>Close</button>
            </div>
          </div>
          <div className="console-body" ref={bodyRef}>
            {history.map((h, i)=> (
              <div className="console-line" key={i}>
                <div style={{color:'#9ca3af',fontSize:12}}>{h.ts} — <span style={{fontWeight:700}}>{h.cmd}</span> {h.ok? <span style={{color:'#10b981'}}>OK</span>: <span style={{color:'#ef4444'}}>ERR</span>}</div>
                <pre style={{whiteSpace:'pre-wrap',margin:6}}>{h.err? h.err : h.out}</pre>
              </div>
            ))}
          </div>
          <div className="console-input">
            <input placeholder="run command (e.g. echo text='hello')" value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter'){ runCommand(input) } }} />
            <button onClick={()=>runCommand(input)}>Run</button>
          </div>
        </div>
      ) : (
        <div style={{display:'flex',justifyContent:'flex-end'}}>
          <button className="console-small-btn" onClick={()=>setOpen(true)}>Open Console (`)</button>
        </div>
      )}
    </div>
  )
}
