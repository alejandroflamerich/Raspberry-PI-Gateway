import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../store/authStore'

export default function ProtectedRoute({ children }: { children: JSX.Element }){
  const token = useAuth(state => state.token)
  if(!token) return <Navigate to="/login" replace />
  return children
}
