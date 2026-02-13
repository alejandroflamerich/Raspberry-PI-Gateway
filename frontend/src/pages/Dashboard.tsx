import React, { useEffect, useState } from 'react'
import api from '../services/api'
import Menu from '../components/Menu'
import DataFlow from '../components/DataFlow'
import './Dashboard.css'

export default function Dashboard(){
  const [health, setHealth] = useState<string>('loading')
  const [points, setPoints] = useState<any[]>([])
  const [db, setDb] = useState<any>({pollers: [], mbid_index: {}})
  const [search, setSearch] = useState<string>('')
  const [sortBy, setSortBy] = useState<string>('mbid')
  const [sortDir, setSortDir] = useState<'asc'|'desc'>('asc')

  useEffect(()=>{
    api.get('/health').then(r=>setHealth(r.data.status)).catch(()=>setHealth('error'))
    api.get('/points/').then(r=>setPoints(r.data)).catch(()=>setPoints([]))

    let mounted = true
    async function loadDb(){
      try{
        const r = await api.get('/debug/database')
        if(!mounted) return
        setDb(r.data)
      }catch(e){ if(mounted) setDb({pollers: [], mbid_index: {}}) }
    }

    // initial load
    loadDb()
    // refresh periodically
    const iid = window.setInterval(loadDb, 2000)
    return ()=>{ mounted=false; clearInterval(iid) }
  }, [])

  // build rows from db
  const rows: any[] = []
  for(const p of (db.pollers || [])){
    for(const t of (p.things||[])){
      rows.push({
        thing: t.name || t.label || `thing-${t.mbid}`,
        mbid: String(t.mbid),
        value: t.value,
        updated_at: t.updated_at || null,
      })
    }
  }

  // apply search filter
  const q = (search || '').trim().toLowerCase()
  let filtered = rows
  if(q){
    filtered = rows.filter(r => (
      String(r.thing || '').toLowerCase().includes(q) ||
      String(r.mbid || '').toLowerCase().includes(q) ||
      String(r.value ?? '').toLowerCase().includes(q)
    ))
  }

  // sort
  filtered.sort((a,b)=>{
    const key = sortBy || 'mbid'
    const va = a[key] ?? ''
    const vb = b[key] ?? ''
    if(typeof va === 'number' && typeof vb === 'number'){
      return sortDir === 'asc' ? va - vb : vb - va
    }
    const sa = String(va).localeCompare(String(vb), undefined, {numeric: true})
    return sortDir === 'asc' ? sa : -sa
  })

  function toggleSort(key: string){
    if(sortBy === key){
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    }else{
      setSortBy(key)
      setSortDir('asc')
    }
  }

  return (
    <div>
      <Menu />
      <main className="dashboard-root">
        <DataFlow />
        <h1>Dashboard</h1>
        <div className="health">Backend health: {health}</div>

        <section className="db-section">
          <h2>Things</h2>
          <div className="table-wrap">
            <table className="things-table">
              <thead>
                <tr>
                  <th>Thing</th>
                  <th>MBID</th>
                  <th>Value</th>
                  <th>Last Update</th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const rows: any[] = []
                  // db.pollers is an array of poller objects with `things` lists
                  for(const p of (db.pollers || [])){
                    for(const t of (p.things||[])){
                      rows.push({
                        thing: t.name || t.label || `thing-${t.mbid}`,
                        mbid: String(t.mbid),
                        value: t.value,
                        updated_at: t.updated_at || null,
                      })
                    }
                  }
                  if(rows.length===0){
                    return (<tr><td colSpan={4} className="empty">No things configured</td></tr>)
                  }
                  return rows.map((r, i) => (
                    <tr key={r.mbid + '-' + i}>
                      <td>{r.thing}</td>
                      <td>{r.mbid}</td>
                      <td className="mono">{String(r.value ?? '-')}</td>
                      <td>{r.updated_at ? formatTs(r.updated_at) : '-'}</td>
                    </tr>
                  ))
                })()}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  )
}

function pad(n:number){ return String(n).padStart(2,'0') }
function formatTs(ts:number){
  // ts is epoch seconds; format as YYYY-mm-dd HH:MM:SS
  try{
    const d = new Date(Number(ts)*1000)
    const Y = d.getFullYear()
    const M = pad(d.getMonth()+1)
    const D = pad(d.getDate())
    const hh = pad(d.getHours())
    const mm = pad(d.getMinutes())
    const ss = pad(d.getSeconds())
    return `${Y}-${M}-${D} ${hh}:${mm}:${ss}`
  }catch(e){ return String(ts) }
}
