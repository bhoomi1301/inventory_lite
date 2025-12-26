import React, {useState} from 'react'
import API from '../api'

export default function Auth({onLogin}){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const submit = async (e)=>{
    e.preventDefault()
    setLoading(true)
    setMsg(null)
    const res = await API.postAuth('/auth/login/', {username, password})
    setLoading(false)
    if(res.status === 200 && res.body && res.body.access){
      localStorage.setItem('access', res.body.access)
      localStorage.setItem('refresh', res.body.refresh)
      setMsg('Logged in')
      onLogin && onLogin()
    } else if(res.body && res.body.detail){
      setMsg(res.body.detail)
    } else {
      setMsg('Login failed')
    }
  }

  return (
    <div className="card p-3">
      <h2>Login</h2>
      <form onSubmit={submit}>
        <div className="mb-2"><input className="form-control" placeholder="username" value={username} onChange={e=>setUsername(e.target.value)} /></div>
        <div className="mb-2"><input className="form-control" placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
        <button className="btn btn-primary" type="submit" disabled={loading}>{loading? 'Logging in...':'Login'}</button>
      </form>
      {msg && <div className="alert alert-info mt-2">{msg}</div>}
    </div>
  )
}