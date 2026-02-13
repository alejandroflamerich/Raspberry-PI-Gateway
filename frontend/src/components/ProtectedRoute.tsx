import React, { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/authStore'
import api from '../services/api'

export default function ProtectedRoute({ children }: { children: JSX.Element }){
  const token = useAuth(state => state.token)
  const setToken = useAuth(state => state.setToken)
  const [verifying, setVerifying] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    let mounted = true
    async function verify(){
      if(!token) return
      setVerifying(true)
      try{
        await api.get('/auth/me')
      }catch(e:any){
        // token invalid or server error -> clear and redirect
        setToken(null)
        if(mounted) navigate('/login', { replace: true })
      }finally{
        if(mounted) setVerifying(false)
      }
    }
    verify()
    return () => { mounted = false }
  }, [token, setToken, navigate])

  if(!token) return <Navigate to="/login" replace />
  if(verifying) return null
  return children
}
