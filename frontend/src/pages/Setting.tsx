import React, { useEffect, useState } from 'react'
import './Setting.css'
import Menu from '../components/Menu'
import api from '../services/api'

export default function Setting(){
  const [easyberry, setEasyberry] = useState<string>('')
  const [polling, setPolling] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [savingEasy, setSavingEasy] = useState(false)
  const [savingPoll, setSavingPoll] = useState(false)

  useEffect(()=>{
    async function load(){
      setLoading(true)
      try{
        const r1 = await api.get('/settings/easyberry')
        const r2 = await api.get('/settings/polling')
        const e = r1.data
        const p = r2.data
        setEasyberry(JSON.stringify(e, null, 2))
        setPolling(JSON.stringify(p, null, 2))
      }catch(err){
        console.error(err)
        setEasyberry('{\n  "error": "could not load easyberry"\n}')
        setPolling('{\n  "error": "could not load polling"\n}')
      }finally{setLoading(false)}
    }
    load()
  },[])

  async function saveEasy(){
    setSavingEasy(true)
    try{
      const parsed = JSON.parse(easyberry)
      const res = await api.post('/settings/easyberry', parsed)
      if(!res || res.status >= 400) throw new Error('Save failed')
      alert('Easyberry config saved')
    }catch(err:any){
      alert('Error: '+(err.message||err))
    }finally{setSavingEasy(false)}
  }

  async function readEasy(){
    setSavingEasy(true)
    try{
      const r = await api.get('/settings/easyberry')
      setEasyberry(JSON.stringify(r.data, null, 2))
    }catch(err:any){
      alert('Error loading easyberry: '+(err.message||err))
    }finally{setSavingEasy(false)}
  }

  async function savePolling(){
    setSavingPoll(true)
    try{
      const parsed = JSON.parse(polling)
      const res = await api.post('/settings/polling', parsed)
      if(!res || res.status >= 400) throw new Error('Save failed')
      alert('Polling config saved')
    }catch(err:any){
      alert('Error: '+(err.message||err))
    }finally{setSavingPoll(false)}
  }

  async function readPolling(){
    setSavingPoll(true)
    try{
      const r = await api.get('/settings/polling')
      setPolling(JSON.stringify(r.data, null, 2))
    }catch(err:any){
      alert('Error loading polling: '+(err.message||err))
    }finally{setSavingPoll(false)}
  }

  return (
    <div>
      <Menu />
      <main className="setting-root">
        <h2>Settings</h2>
        <div className="setting-grid">
        <section className="json-card">
          <h3>Easyberry Config</h3>
          <div className="json-edit" role="region" aria-label="Easyberry JSON editor">
            <textarea value={easyberry} onChange={e=>setEasyberry(e.target.value)} spellCheck={false} />
          </div>
          <div className="card-actions">
            <button className="read-btn" onClick={readEasy} disabled={savingEasy || loading}>{savingEasy? 'Reading...':'Read File'}</button>
            <button className="save-btn" onClick={saveEasy} disabled={savingEasy || loading}>{savingEasy? 'Saving...':'Save Easyberry'}</button>
          </div>
        </section>

        <section className="json-card">
          <h3>Polling Config</h3>
          <div className="json-edit" role="region" aria-label="Polling JSON editor">
            <textarea value={polling} onChange={e=>setPolling(e.target.value)} spellCheck={false} />
          </div>
          <div className="card-actions">
            <button className="read-btn" onClick={readPolling} disabled={savingPoll || loading}>{savingPoll? 'Reading...':'Read File'}</button>
            <button className="save-btn" onClick={savePolling} disabled={savingPoll || loading}>{savingPoll? 'Saving...':'Save Polling'}</button>
          </div>
        </section>
        </div>
      </main>
    </div>
  )
}
