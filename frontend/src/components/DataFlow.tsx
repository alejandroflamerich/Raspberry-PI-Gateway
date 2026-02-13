import React, { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import './DataFlow.css'

import easyberryImg from '../assets/easyberry.png'
import raspberryImg from '../assets/raspberry.webp'
import slavesImg from '../assets/slaves.png'

export default function DataFlow(){
  const [easyberryActive, setEasyberryActive] = useState(false)
  const [slavesActive, setSlavesActive] = useState(false)
  const topLeftRef = useRef<SVGPathElement | null>(null)
  const bottomLeftRef = useRef<SVGPathElement | null>(null)
  const topRightRef = useRef<SVGPathElement | null>(null)
  const bottomRightRef = useRef<SVGPathElement | null>(null)
  const topOffset = useRef(0)
  const bottomOffset = useRef(0)

  useEffect(()=>{
    let mounted = true
    async function check(){
      try{
        const r1 = await api.get('/debug/polling/status')
        if(!mounted) return
        setSlavesActive(Boolean(r1.data.running))
      }catch(e){ if(mounted) setSlavesActive(false) }

      try{
        const r2 = await api.get('/easyberry/status')
        if(!mounted) return
        // backend returns { running: boolean }
        setEasyberryActive(Boolean(r2.data && r2.data.running))
      }catch(e){ if(mounted) setEasyberryActive(false) }
    }
    check()
    const iid = window.setInterval(check, 2000)
    return ()=>{ mounted=false; clearInterval(iid) }
  }, [])

  // JS-driven RAF animation disabled to prefer CSS animations (was causing conflicts)
  // useDataFlowAnimation({ topLeftRef, bottomLeftRef, topRightRef, bottomRightRef, easyberryActive, slavesActive })

  return (
    <div className="dataflow-root" role="region" aria-label="Data flow">
      <div className="nodes">
        <div className="node">
          <img src={easyberryImg} alt="Easyberry" />
          <div className="label">Easyberry</div>
        </div>
        <div className="node">
          <img src={raspberryImg} alt="Raspberry" />
          <div className="label">Raspberry</div>
        </div>
        <div className="node">
          <img src={slavesImg} alt="Slaves" />
          <div className="label">Slaves</div>
        </div>
      </div>

      <svg className="connectors" viewBox="0 0 600 100" preserveAspectRatio="none" aria-hidden>
        <defs>
          <linearGradient id="dataflow-g1" x1="0%" x2="100%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
        </defs>
        {/* Left: Easyberry -> Raspberry (two parallel lines) */}
        <path ref={topLeftRef} className={`line left top ${easyberryActive? 'active':''}`} d="M100 46 L300 46" stroke="#10b981" strokeOpacity="1" strokeWidth="3.5" fill="none" strokeLinecap="round" />
        <path ref={bottomLeftRef} className={`line left bottom ${easyberryActive? 'active':''}`} d="M100 54 L300 54" stroke="#0b1220" strokeWidth="2.5" fill="none" strokeLinecap="round" />
        {/* Right: Raspberry -> Slaves (two parallel lines) */}
        <path ref={topRightRef} className={`line right top ${slavesActive? 'active':''}`} d="M300 46 L500 46" stroke="#10b981" strokeOpacity="1" strokeWidth="3.5" fill="none" strokeLinecap="round" />
        <path ref={bottomRightRef} className={`line right bottom ${slavesActive? 'active':''}`} d="M300 54 L500 54" stroke="#0b1220" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      </svg>
    </div>
  )
}

// animate stroke dash offset with requestAnimationFrame for reliable SVG motion
function useDataFlowAnimation(opts: {
  topLeftRef: React.RefObject<SVGPathElement>
  bottomLeftRef: React.RefObject<SVGPathElement>
  topRightRef: React.RefObject<SVGPathElement>
  bottomRightRef: React.RefObject<SVGPathElement>
  easyberryActive: boolean
  slavesActive: boolean
}){
  const { topLeftRef, bottomLeftRef, topRightRef, bottomRightRef, easyberryActive, slavesActive } = opts
  useEffect(()=>{
    let raf = 0
    let last = performance.now()
    let offTop = 0
    let offBottom = 0
    const topSpeed = 60 // px per second
    const bottomSpeed = 40 // px per second

    const loop = (t: number)=>{
      const dt = (t - last) / 1000
      last = t
      if(easyberryActive){ offTop -= topSpeed * dt; offBottom += bottomSpeed * dt }
      if(slavesActive){ offTop -= topSpeed * dt; offBottom += bottomSpeed * dt }

      if(topLeftRef.current) topLeftRef.current.style.strokeDashoffset = `${offTop}px`
      if(topRightRef.current) topRightRef.current.style.strokeDashoffset = `${offTop}px`
      if(bottomLeftRef.current) bottomLeftRef.current.style.strokeDashoffset = `${offBottom}px`
      if(bottomRightRef.current) bottomRightRef.current.style.strokeDashoffset = `${offBottom}px`

      raf = requestAnimationFrame(loop)
    }

    raf = requestAnimationFrame(loop)
    return ()=> cancelAnimationFrame(raf)
  }, [easyberryActive, slavesActive, topLeftRef, bottomLeftRef, topRightRef, bottomRightRef])
}

// attach the animation hook inside the component via side-effect
// (we export default component above; React will call hooks only inside component scope)
