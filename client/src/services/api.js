// API service functions

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export { apiBaseUrl }

export const transcribeMedia = async (file, token) => {
  const form = new FormData()
  form.append('file', file, file.name)

  const resp = await fetch(`${apiBaseUrl}/api/media/transcribe`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: form,
  })

  if (!resp.ok) {
    const maybeJson = await resp.json().catch(() => null)
    throw new Error(maybeJson?.detail || `Transcription failed (${resp.status})`)
  }

  const data = await resp.json()
  const id = data?.transcript_id || ''
  if (!id) throw new Error('Transcription succeeded but no transcript_id returned')
  return id
}

export const parseDocument = async (file, token) => {
  const form = new FormData()
  form.append('file', file, file.name)

  const resp = await fetch(`${apiBaseUrl}/api/documents/parse`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: form,
  })

  if (!resp.ok) {
    const maybeJson = await resp.json().catch(() => null)
    throw new Error(maybeJson?.detail || `Document parsing failed (${resp.status})`)
  }

  const data = await resp.json()
  const id = data?.document_id || ''
  if (!id) throw new Error('Document parsing succeeded but no document_id returned')
  return id
}

export const fetchUserProfile = async (token) => {
  const resp = await fetch(`${apiBaseUrl}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  
  if (!resp.ok) {
    throw new Error('Unauthorized')
  }
  
  return resp.json()
}

export const fetchConversations = async (token) => {
  const resp = await fetch(`${apiBaseUrl}/api/conversations`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) return []
  const data = await resp.json()
  return Array.isArray(data) ? data : []
}

export const fetchConversation = async (conversationId, token) => {
  const resp = await fetch(`${apiBaseUrl}/api/conversations/${conversationId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) {
    const maybeJson = await resp.json().catch(() => null)
    throw new Error(maybeJson?.detail || `Failed to load conversation (${resp.status})`)
  }
  return resp.json()
}

export const sendChatMessage = async (payload, token) => {
  const response = await fetch(`${apiBaseUrl}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const maybeJson = await response.json().catch(() => null)
    const detail = maybeJson?.detail || `Request failed (${response.status})`
    throw new Error(detail)
  }

  return response.json()
}

export const register = async (email, username, password) => {
  const resp = await fetch(`${apiBaseUrl}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password }),
  })
  if (!resp.ok) {
    const maybeJson = await resp.json().catch(() => null)
    throw new Error(maybeJson?.detail || `Signup failed (${resp.status})`)
  }
  return resp.json()
}

export const login = async (email, password) => {
  const form = new URLSearchParams()
  form.set('username', email)
  form.set('password', password)

  const tokenResp = await fetch(`${apiBaseUrl}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  })

  if (!tokenResp.ok) {
    const maybeJson = await tokenResp.json().catch(() => null)
    throw new Error(maybeJson?.detail || `Login failed (${tokenResp.status})`)
  }

  const tokenJson = await tokenResp.json()
  const token = tokenJson?.access_token || ''
  if (!token) throw new Error('Login succeeded but no token returned')
  return token
}
