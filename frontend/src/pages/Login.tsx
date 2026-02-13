import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/auth'
import api from '../services/api'
import './Login.css'

export default function Login(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent){
    e.preventDefault()
    setError(null)
    setLoading(true)
    const ok = await login(username, password)
    setLoading(false)
    if(ok) navigate('/dashboard')
    else setError('Login failed — check username and password')
  }

  async function forgot(){
    if(!confirm('This will reset configuration and remove stored credentials. Continue?')) return
    try{
      await api.post('/auth/forgot')
      alert('Configuration reset. Please login again with a new password.')
      setUsername('')
      setPassword('')
    }catch(e){
      alert('Failed to reset configuration')
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <header className="login-header">
          <h1>Easyberry</h1>
          <p className="muted">Sign in to your dashboard</p>
        </header>

        <form className="login-form" onSubmit={submit}>
          <label className="field">
            <span className="label">Username</span>
            <input
              className="input"
              value={username}
              onChange={e=>setUsername(e.target.value)}
              autoComplete="username"
            />
          </label>

          <label className="field">
            <span className="label">Password</span>
            <input
              className="input"
              type="password"
              value={password}
              onChange={e=>setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>

          {error && <div className="error">{error}</div>}

          <div className="actions">
            <button className="btn" type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
          </div>
          <div className="forgot-link">
            <button type="button" className="forgot-link-btn" onClick={forgot}>Forgot password</button>
          </div>
        </form>

        <footer className="login-footer">
          <small className="muted">Developed for Easyberry — use a strong password</small>
        </footer>
      </div>
    </div>
  )
}

