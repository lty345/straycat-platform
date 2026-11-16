import client from './client'

export function postEvent(payload) {
  return client.post('/api/v1/events', payload)
}