import React, { useEffect, useState } from 'react'
import API from '../api'

export default function CreateOrder(){
  const [products, setProducts] = useState([])
  const [dealers, setDealers] = useState([])
  const [dealer, setDealer] = useState(null)
  const [items, setItems] = useState([])
  const [errors, setErrors] = useState(null)
  useEffect(()=>{API.get('/products/').then(setProducts); API.get('/dealers/').then(setDealers)}, [])

  const addLine = ()=> setItems([...items, {product: products[0]?.id || null, quantity:1}])
  const updateLine = (idx, field, value) => {
    const copy = [...items]; copy[idx][field] = value; setItems(copy)
  }
  const removeLine = (idx) => { setItems(items.filter((_,i)=>i!==idx)) }

  const validate = ()=>{
    const errs = []
    if(!dealer) errs.push('Select a dealer')
    if(items.length === 0) errs.push('Add at least one item')
    items.forEach((it, idx)=>{
      if(!it.product) errs.push(`Line ${idx+1}: select a product`)
      if(!it.quantity || Number(it.quantity) < 1) errs.push(`Line ${idx+1}: quantity must be at least 1`)
    })
    return errs
  }

  const submit = async ()=>{
    const errs = validate()
    if(errs.length){ setErrors(errs); return }
    const body = {dealer, items: items.map(i=>({product: i.product, quantity: Number(i.quantity)}))}
    const res = await API.post('/orders/', body)
    if(res.status === 201) { alert('Order created'); setItems([]); setErrors(null) } else { setErrors([res.body?.detail || 'Order creation failed']) }
  }

  return (
    <div className="card p-3">
      <h2>Create Order</h2>
      {errors && <div className="alert alert-danger"><ul>{errors.map((e,i)=><li key={i}>{e}</li>)}</ul></div>}
      <div className="mb-2">
        <label>Dealer: </label>
        <select className="form-select" onChange={e=>setDealer(Number(e.target.value))} value={dealer||''}>
          <option value="">--select--</option>
          {dealers.map(d=> <option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
        </select>
      </div>
      <div>
        <h3>Items</h3>
        <button className="btn btn-secondary mb-2" onClick={addLine}>Add Item</button>
        {items.map((it, idx)=> (
          <div key={idx} className="line">
            <select className="form-select" style={{width: '60%'}} value={it.product} onChange={e=>updateLine(idx, 'product', Number(e.target.value))}>
              {products.map(p=> <option key={p.id} value={p.id}>{p.name} ({p.sku}) - Stock: {p.stock}</option>)}
            </select>
            <input className="form-control" style={{width: '100px'}} type="number" value={it.quantity} min={1} onChange={e=>updateLine(idx, 'quantity', e.target.value)} />
            <button className="btn btn-danger" onClick={()=>removeLine(idx)}>Remove</button>
          </div>
        ))}
      </div>
      <div className="mt-3">
        <button className="btn btn-primary" onClick={submit}>Create Draft Order</button>
      </div>
    </div>
  )
}