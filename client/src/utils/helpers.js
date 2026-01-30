// Utility functions for file attachments and transcription

export const getAttachmentKind = (file) => {
  const t = String(file?.type || '')
  if (t.startsWith('image/')) return 'image'
  if (t.startsWith('video/')) return 'video'
  if (t.startsWith('audio/')) return 'audio'
  return 'document'
}

export const makeAttachmentId = (file) => {
  return `${file.name}:${file.size}:${file.lastModified}:${Math.random().toString(16).slice(2)}`
}

export const parseTimestampToSeconds = (ts) => {
  const v = String(ts || '').trim()
  if (!v) return null
  const parts = v.split(':').map((p) => p.trim())
  if (parts.some((p) => p === '' || !/^[0-9]+$/.test(p))) return null
  const nums = parts.map((p) => Number(p))
  if (nums.some((n) => !Number.isFinite(n))) return null

  // support mm:ss and hh:mm:ss
  if (nums.length === 2) return nums[0] * 60 + nums[1]
  if (nums.length === 3) return nums[0] * 3600 + nums[1] * 60 + nums[2]
  return null
}

export const extractTimeWindowFromPrompt = (text) => {
  const t = String(text || '')
  if (!t.trim()) return null

  // Match hh:mm:ss OR mm:ss
  const re = /\b\d{1,2}:\d{2}(?::\d{2})?\b/g
  const matches = []
  let m
  while ((m = re.exec(t)) !== null) {
    const sec = parseTimestampToSeconds(m[0])
    if (sec === null) continue
    matches.push({ raw: m[0], sec, index: m.index })
    if (matches.length >= 4) break
  }

  if (matches.length === 0) return null

  if (matches.length >= 2) {
    const a = matches[0]
    const b = matches[1]
    const between = t.slice(a.index + a.raw.length, b.index).toLowerCase()
    if (between.includes('-') || between.includes('to') || between.includes('and') || between.includes('until')) {
      return { start: Math.min(a.sec, b.sec), end: Math.max(a.sec, b.sec) }
    }
  }

  // Single timestamp => small around-window
  const center = matches[0].sec
  return { start: Math.max(0, center - 20), end: center + 20 }
}
