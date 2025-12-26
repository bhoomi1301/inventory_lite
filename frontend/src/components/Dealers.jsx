import React, {useEffect, useState} from 'react'
import API from '../api'

export default function Dealers(){
  const [dealers, setDealers] = useState([])
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [err, setErr] = useState(null)
  useEffect(()=>{API.get('/dealers/').then(setDealers)}, [])
  const create = async ()=>{
    setErr(null)
    if(!name || !code) { setErr('Name and Code are required'); return }
    const res = await API.post('/dealers/', {name, code})
    if(res.status === 201){ setDealers(d=>[...d, res.body]); setName(''); setCode('') } else { setErr(res.body?.detail || JSON.stringify(res.body)) }
  }
  return (
    <div className="card p-3">
      <h2>Dealers</h2>
      {err && <div className="alert alert-danger">{err}</div>}
      <div className="d-flex gap-2 mb-2">
        <input className="form-control" placeholder="name" value={name} onChange={e=>setName(e.target.value)} />
        <input className="form-control" placeholder="code" value={code} onChange={e=>setCode(e.target.value)} />
        <button className="btn btn-primary" onClick={create}>Create</button>
      </div>
      <ul className="list-group">
        {dealers.map(d=> <li className="list-group-item" key={d.id}>{d.name} ({d.code})</li>)}
      </ul>
    </div>
  )
}