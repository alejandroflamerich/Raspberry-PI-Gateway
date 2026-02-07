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
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState<boolean>(false)
  const intervalRef = useRef<number | null>(null)
  const userStarted = useRef<boolean>(false)
  const statusIntervalRef = useRef<number | null>(null)

  useEffect(()=>{
    let mounted = true

    async function load(){
      setLoading(true)
      try{
        const r = await api.get('/debug/packets')
        const items = r.data.packets || []
        const out: PacketLine[] = []
        items.forEach((it: any) => {
          if(it.request) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status})
          if(it.response) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
        })
        if(mounted) setLines(out.reverse())
      }catch(err){
        console.error(err)
      }finally{ if(mounted) setLoading(false) }
    }

    function startLoop(){
      if(intervalRef.current) return
      // immediate fetch
      load()
      // poll every 2s
      intervalRef.current = window.setInterval(load, 2000)
    }

    function stopLoop(){
      if(intervalRef.current){
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    // if backend polling already active, begin user-controlled loop
    api.get('/debug/polling/status').then(r=>{
      const isRunning = Boolean(r.data.running)
      setRunning(isRunning)
      if(isRunning){
        // started externally; begin auto-refresh (but mark userStarted false)
        userStarted.current = false
        startLoop()
      }else{
        // load once to show current state
        load()
      }
    }).catch(()=>{ load() })

    // poll backend status every 2s and if backend becomes active start loop
    statusIntervalRef.current = window.setInterval(async ()=>{
      try{
        const r = await api.get('/debug/polling/status')
        const isRunning = Boolean(r.data.running)
        setRunning(isRunning)
        if(isRunning){
          // if user hasn't explicitly started/stopped, start automatic loop
          if(!intervalRef.current && !userStarted.current){
            startLoop()
          }
        }else{
          // if backend is stopped and user didn't start locally, stop loop
          if(!userStarted.current){
            if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null }
          }
        }
      }catch(e){ /* ignore status poll errors */ }
    }, 2000)

    return ()=>{ mounted=false; stopLoop(); if(statusIntervalRef.current){ clearInterval(statusIntervalRef.current); statusIntervalRef.current = null } }
  },[])

  async function toggleRunning(){
    try{
      if(running){
        // user pressed Stop: stop backend and stop local loop
        await api.post('/debug/polling/stop')
        setRunning(false)
        userStarted.current = false
        // stop interval
        if(intervalRef.current){ clearInterval(intervalRef.current); intervalRef.current = null }
        // refresh once
        const r = await api.get('/debug/packets')
        const items = r.data.packets || []
        const out: PacketLine[] = []
        items.forEach((it: any) => {
          if(it.request) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status})
          if(it.response) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
        })
        setLines(out.reverse())
      }else{
        // user pressed Start: start backend and begin local loop (stop only when user presses Stop)
        await api.post('/debug/polling/start')
        setRunning(true)
        userStarted.current = true
        // start loop
        if(!intervalRef.current){
          // immediate fetch and then interval
          const r = await api.get('/debug/packets')
          const items = r.data.packets || []
          const out: PacketLine[] = []
          items.forEach((it: any) => {
            if(it.request) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status})
            if(it.response) out.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
          })
          setLines(out.reverse())
          intervalRef.current = window.setInterval(async ()=>{
            try{
              const rr = await api.get('/debug/packets')
              const itms = rr.data.packets || []
              const out2: PacketLine[] = []
              itms.forEach((it: any) => {
                if(it.request) out2.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'req', data: it.request, note: it.note, status: it.status})
                if(it.response) out2.push({ts: it.ts, poller_id: it.poller_id || '-', direction: 'resp', data: it.response, note: it.note, status: it.status})
              })
              setLines(out2.reverse())
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
          {loading && <div className="loading">Loading...</div>}
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
