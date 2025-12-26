import React, {useEffect, useState} from 'react'
import API from '../api'

export default function AdminInventory(){
  const [inventory, setInventory] = useState([])
  const [change, setChange] = useState(0)
  const [note, setNote] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(()=>{
    let mounted = true
    const fetchInv = async ()=>{
      setLoading(true)
      setError(null)
      try{
        const data = await API.get('/inventory/')
        // API.get returns parsed JSON or null; handle unauthorized/empty cases
        if(mounted){
          if(!data){
            setError('Unauthorized: please login as an admin')
            setInventory([])
          } else if(Array.isArray(data)){
            setInventory(data)
          } else {
            setError('Error fetching inventory')
            setInventory([])
          }
        }
      }catch(e){ if(mounted) setError('Error fetching inventory') }
      finally{ if(mounted) setLoading(false) }
    }
    fetchInv()
    return ()=>{ mounted = false }
  }, [])

  const adjust = async (productId)=>{
    const inv = inventory.find(i=>i.product_id === productId)
    if(!inv) return
    setMsg(null)
    const res = await API.put(`/inventory/${inv.id}/adjust/`, {change: Number(change), note})
    if(res.status === 200){
      setMsg({type:'success', text:'Inventory adjusted'})
      // refresh
      try{ const r = await fetch('/api/inventory/'); if(r.status===200){ const d = await r.json(); setInventory(Array.isArray(d)?d:[]) } }
      catch(e){ /* ignore */ }
    } else if(res.status === 401 || res.status === 403){
      setMsg({type:'danger', text: 'Unauthorized: you need admin privileges'})
    } else {
      setMsg({type:'danger', text: JSON.stringify(res.body)})
    }
    setTimeout(()=>setMsg(null), 3000)
  }

  return (
    <div className="card p-3">
      <h2>Admin Inventory</h2>
      {error && <div className="alert alert-warning">{error}</div>}
      {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
      {loading ? <div>Loading...</div> : (
        <>
          <div className="d-flex gap-2 mb-2">
            <input className="form-control" type="number" value={change} onChange={e=>setChange(e.target.value)} />
            <input className="form-control" placeholder="note" value={note} onChange={e=>setNote(e.target.value)} />
          </div>
          <table className="table table-sm">
            <thead><tr><th>SKU</th><th>Qty</th><th>Action</th></tr></thead>
            <tbody>
              {(inventory || []).map(i=> (
                <tr key={i.product_id}><td>{i.sku}</td><td>{i.quantity}</td><td><button className="btn btn-sm btn-primary" onClick={()=>adjust(i.product_id)}>Adjust</button></td></tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}