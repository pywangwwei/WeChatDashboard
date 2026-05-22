import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export function getOverview() {
  return api.get('/overview')
}

export function listGroups(params = {}) {
  return api.get('/groups', { params })
}

export function getGroupDetail(roomId) {
  return api.get(`/groups/${encodeURIComponent(roomId)}`)
}

export function listPersons(params = {}) {
  return api.get('/persons', { params })
}

export function getPersonDetail(userId) {
  return api.get(`/persons/${encodeURIComponent(userId)}`)
}

export function listMessages(params = {}) {
  return api.get('/messages', { params })
}

export function searchMessages(q) {
  return api.get('/search', { params: { q } })
}

export default api
