import React, { useEffect } from 'react'

export default function Toast({ message, variant='info', duration=2000, onClose }){
  useEffect(()=>{
    if(!message) return
    const t = setTimeout(()=>{ onClose && onClose() }, duration)
    return ()=>clearTimeout(t)
  }, [message])

  if(!message) return null

  const bg = {
    info: 'bg-info text-dark',
    success: 'bg-success text-white',
    warning: 'bg-warning text-dark',
    danger: 'bg-danger text-white'
  }[variant] || 'bg-info text-dark'

  return (
    <div style={{position:'fixed', top:20, right:20, zIndex:9999}}>
      <div className={`toast show ${bg}`} role="alert" aria-live="assertive" aria-atomic="true" style={{minWidth:200}}>
        <div className="toast-body">
          {message}
        </div>
      </div>
    </div>
  )
}
