const getToken = () => localStorage.getItem('access')
const getRefresh = () => localStorage.getItem('refresh')

async function tryRefresh() {
  const refresh = getRefresh()
  if(!refresh) return false
  try{
    const resp = await fetch('/api/auth/refresh/', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({refresh})
    })
    if(resp.status === 200){
      const data = await resp.json()
      localStorage.setItem('access', data.access)
      return true
    }
  }catch(e){ }
  // refresh failed
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
  return false
}

const API = {
  get: async (path) => {
    const headers = getToken() ? {'Authorization': `Bearer ${getToken()}`} : {}
    let resp = await fetch(`/api${path}`, {headers})
    if(resp.status === 401){
      const ok = await tryRefresh()
      if(ok){
        const headers2 = {'Authorization': `Bearer ${getToken()}`}
        resp = await fetch(`/api${path}`, {headers: headers2})
      }
    }
    return resp.json().catch(()=>null)
  },
  post: async (path, body) => {
    const headers = {'Content-Type':'application/json'}
    if(getToken()) headers['Authorization'] = `Bearer ${getToken()}`
    let resp = await fetch(`/api${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    })
    if(resp.status === 401){
      const ok = await tryRefresh()
      if(ok){
        headers['Authorization'] = `Bearer ${getToken()}`
        resp = await fetch(`/api${path}`, {method:'POST', headers, body: JSON.stringify(body)})
      }
    }
    return {status: resp.status, body: await resp.json().catch(()=>null)}
  },
  put: async (path, body) => {
    const headers = {'Content-Type':'application/json'}
    if(getToken()) headers['Authorization'] = `Bearer ${getToken()}`
    let resp = await fetch(`/api${path}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body)
    })
    if(resp.status === 401){
      const ok = await tryRefresh()
      if(ok){
        headers['Authorization'] = `Bearer ${getToken()}`
        resp = await fetch(`/api${path}`, {method:'PUT', headers, body: JSON.stringify(body)})
      }
    }
    return {status: resp.status, body: await resp.json().catch(()=>null)}
  },

  // Helper to update orders: prevents sending `status` in payload (server rejects status changes via update)
  putOrder: async function(id, body) {
    if('status' in body){
      return {status: 400, body: {detail: 'Order status cannot be changed via update; use confirm or deliver endpoints'}}
    }
    return this.put(`/orders/${id}/`, body)
  },
  postAuth: async (path, body) => {
    const resp = await fetch(`/api${path}`, {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
    })
    return {status: resp.status, body: await resp.json().catch(()=>null)}
  },
  getMe: async ()=> {
    const resp = await fetch('/api/auth/me/', {headers: getToken()?{'Authorization':`Bearer ${getToken()}`}:{}})
    if(resp.status === 401){
      const ok = await tryRefresh()
      if(ok){
        return fetch('/api/auth/me/', {headers: {'Authorization': `Bearer ${getToken()}`}}).then(r=>r.json()).catch(()=>null)
      }
      return null
    }
    return resp.json().catch(()=>null)
  },
  tryRefresh,
  startAutoRefresh: (logoutCb) => {
    // refresh every 4 minutes
    const id = setInterval(async ()=>{
      const ok = await tryRefresh()
      if(!ok && typeof logoutCb === 'function'){
        logoutCb()
        clearInterval(id)
      }
    }, 4*60*1000)
    return id
  }
}

export default API