const TOKEN_KEY = 'access_token'
const EMAIL_KEY = 'user_email'

const normalizeToken = (rawToken) => {
  if (!rawToken || typeof rawToken !== 'string') return null
  const trimmed = rawToken.trim()
  if (!trimmed || trimmed === 'null' || trimmed === 'undefined') return null
  if (trimmed.startsWith('"') && trimmed.endsWith('"') && trimmed.length >= 2) {
    return trimmed.slice(1, -1)
  }
  return trimmed
}

export const getAccessToken = () => normalizeToken(localStorage.getItem(TOKEN_KEY))

export const setAccessToken = (token) => {
  const normalized = normalizeToken(token)
  if (!normalized) {
    localStorage.removeItem(TOKEN_KEY)
    return null
  }
  localStorage.setItem(TOKEN_KEY, normalized)
  return normalized
}

export const clearAuthSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(EMAIL_KEY)
}

