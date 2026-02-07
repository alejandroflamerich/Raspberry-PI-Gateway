import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from '../pages/Login'
import Dashboard from '../pages/Dashboard'
import Setting from '../pages/Setting'
import Polling from '../pages/Polling'
import Easyberry from '../pages/Easyberry'
import ProtectedRoute from '../components/ProtectedRoute'

export default function Router() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
      />
      
      <Route
        path="/setting"
        element={<ProtectedRoute><Setting /></ProtectedRoute>}
      />
      <Route
        path="/polling"
        element={<ProtectedRoute><Polling /></ProtectedRoute>}
      />
      <Route
        path="/easyberry"
        element={<ProtectedRoute><Easyberry /></ProtectedRoute>}
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
