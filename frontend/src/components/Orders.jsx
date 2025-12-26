import React, { useEffect, useState } from 'react'
import API from '../api'

export default function Orders(){
  const [orders, setOrders] = useState([])
  const [refresh, setRefresh] = useState(0)
  const [msg, setMsg] = useState(null)
  useEffect(()=>{API.get('/orders/').then(setOrders)}, [refresh])

  const confirm = async (id) => {
    const res = await API.post(`/orders/${id}/confirm/`, {})
    if(res.status === 200){ setMsg({type:'success', text:'Order confirmed'}) }
    else {
      // Prefer server-provided detail and human-friendly item messages
      let text = res.body?.detail || JSON.stringify(res.body)
      if(res.body?.items){
        const msgs = res.body.items.map(i=> i.message || `${i.product || i.product_name}: ${i.requested} (available ${i.available})`)
        text = msgs.join('; ')
      }
      setMsg({type:'danger', text})
    }
    setRefresh(r=>r+1)
    setTimeout(()=>setMsg(null), 5000)
  }

  const cancel = async (id) => {
    const res = await API.post(`/orders/${id}/cancel/`, {})
    if(res.status === 200){ setMsg({type:'success', text:'Order cancelled'}) }
    else { setMsg({type:'danger', text: res.body?.detail || 'Cancel failed'}) }
    setRefresh(r=>r+1)
    setTimeout(()=>setMsg(null), 3000)
  }
  const deliver = async (id) => {
    const res = await API.post(`/orders/${id}/deliver/`, {})
    if(res.status === 200){ setMsg({type:'success', text:'Order delivered'}) } else { setMsg({type:'danger', text: JSON.stringify(res.body)}) }
    setRefresh(r=>r+1)
    setTimeout(()=>setMsg(null), 3000)
  }

  return (
    <div className="card p-3">
      <h2>Orders</h2>
      {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
      <table className="table table-sm">
        <thead><tr><th>Order #</th><th>Dealer</th><th>Status</th><th>Total</th><th>Actions</th></tr></thead>
        <tbody>
          {orders.map(o=> (
            <tr key={o.id}>
              <td>{o.order_number}</td>
              <td>{o.dealer}</td>
              <td>{o.status}</td>
              <td>{o.total_amount}</td>
              <td>
                {o.status === 'DRAFT' && <>
                  <button className="btn btn-sm btn-primary me-1" onClick={()=>confirm(o.id)}>Confirm</button>
                  <button className="btn btn-sm btn-danger me-1" onClick={()=>cancel(o.id)}>Cancel</button>
                </>}
                {o.status === 'CONFIRMED' && <button className="btn btn-sm btn-success" onClick={()=>deliver(o.id)}>Deliver</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}