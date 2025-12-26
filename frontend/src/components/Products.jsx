import React, { useEffect, useState } from 'react'
import API from '../api'

export default function Products(){
  const [products, setProducts] = useState([])
  useEffect(()=>{API.get('/products/').then(setProducts)}, [])
  return (
    <div className="card p-3">
      <h2>Products</h2>
      <table className="table table-striped">
        <thead><tr><th>SKU</th><th>Name</th><th>Price</th><th>Stock</th></tr></thead>
        <tbody>
          {products.map(p => (
            <tr key={p.id}>
              <td>{p.sku}</td>
              <td>{p.name}</td>
              <td>{p.price}</td>
              <td>{p.stock}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}