import React, { useState } from 'react'
import Products from './components/Products'
import Orders from './components/Orders'
import CreateOrder from './components/CreateOrder'
import Auth from './components/Auth'
import Dealers from './components/Dealers'
import AdminInventory from './components/AdminInventory'
import Toast from './components/Toast'
import API from './api'

export default function App(){
  const [view, setView] = useState('products')
  const [loggedIn, setLoggedIn] = useState(Boolean(localStorage.getItem('access')))
  const [autoRefId, setAutoRefId] = useState(null)
  const [user, setUser] = useState(null)
  const [alert, setAlert] = useState(null)
  const [toast, setToast] = useState(null)

  React.useEffect(()=>{
    // on app load, if we have token try to fetch user info
    const init = async ()=>{
      if(localStorage.getItem('access')){
        const me = await API.getMe()
        if(me){
          setLoggedIn(true); setUser(me)
          if(me.is_staff){
            setToast({message:'Redirecting to Admin...', variant:'info'})
            setTimeout(()=>{ setView('admin'); setToast(null) }, 700)
          }
        }
        else { setLoggedIn(false); setUser(null) }
      }
    }
    init()
  }, [])

  // start/stop auto refresh and clear user on logout
  React.useEffect(()=>{
    if(loggedIn){
      const id = API.startAutoRefresh(()=>{ setLoggedIn(false); setUser(null); setAlert({type:'warning', text:'Session expired'}) })
      setAutoRefId(id)
    } else if(autoRefId){
      clearInterval(autoRefId)
      setAutoRefId(null)
    }
  }, [loggedIn])



  return (
    <div className="container mt-3">
      <header className="d-flex justify-content-between align-items-center mb-3">
        <h1>Vikmo</h1>
        <nav>
          <button className="btn btn-outline-primary me-2" onClick={()=>setView('products')}>Products</button>
          <button className="btn btn-outline-primary me-2" onClick={()=>setView('orders')}>Orders</button>
          <button className="btn btn-outline-primary me-2" onClick={()=>setView('create')}>Create Order</button>
          <button className="btn btn-outline-primary me-2" onClick={()=>setView('dealers')}>Dealers</button>
          {user && user.is_staff && <button className="btn btn-outline-secondary me-2" onClick={()=>setView('admin')}>Admin</button>} 
          {!loggedIn ? <button className="btn btn-success" onClick={()=>setView('login')}>Login</button> : <>
            <span className="me-2">{user ? `Hi, ${user.username}` : ''}</span>
            <button className="btn btn-danger" onClick={()=>{localStorage.removeItem('access'); localStorage.removeItem('refresh'); setLoggedIn(false); setUser(null)}}>Logout</button>
          </>}
        </nav>
      </header>
      {toast && <Toast message={toast.message} variant={toast.variant} onClose={()=>setToast(null)} />}
      <main>
        {alert && <div className={`alert alert-${alert.type} mb-2`}>{alert.text}</div>}
        {view === 'products' && <Products />}
        {view === 'orders' && <Orders />}
        {view === 'create' && <CreateOrder />}
        {view === 'dealers' && <Dealers />}
        {view === 'admin' && <AdminInventory />}
        {view === 'login' && <Auth onLogin={async ()=>{
            const me = await API.getMe();
            if(me){
              setLoggedIn(true);
              setUser(me);
              setAlert({type:'success', text:'Logged in'});
              setTimeout(()=>setAlert(null),2000);
              if(me.is_staff){
                setToast({message:'Redirecting to Admin...', variant:'info'});
                setTimeout(()=>{ setView('admin'); setToast(null) }, 700)
              } else {
                setView('products');
              }
            } else {
              setAlert({type:'danger', text:'Login failed'});
              setTimeout(()=>setAlert(null),2000);
            }
          }} />}
      </main>
    </div>
  )
}