import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import ChatArea from '../components/ChatArea'
import ChatInput from '../components/ChatInput'
import { 
  transcribeMedia, 
  parseDocument, 
  fetchUserProfile, 
  fetchConversations, 
  fetchConversation, 
  sendChatMessage 
} from '../services/api'
import { 
  getAttachmentKind, 
  makeAttachmentId, 
  extractTimeWindowFromPrompt 
} from '../utils/helpers'

function Home({ darkMode, setDarkMode }) {
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [me, setMe] = useState(null)
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState('')
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [sendError, setSendError] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isParsing, setIsParsing] = useState(false)
  const [activeTranscriptId, setActiveTranscriptId] = useState('')
  const [activeDocumentId, setActiveDocumentId] = useState('')
  const [attachments, setAttachments] = useState([])
  
  const messagesEndRef = useRef(null)
  const token = localStorage.getItem('auth_token')

  // User avatar
  const avatarName = me?.username || me?.email || 'U'
  const userAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(avatarName)}&background=random&size=128`

  // Fetch user profile
  useEffect(() => {
    if (!token) return
    let cancelled = false

    fetchUserProfile(token)
      .then((data) => {
        if (!cancelled) setMe(data)
      })
      .catch(() => {
        if (!cancelled) {
          localStorage.removeItem('auth_token')
          navigate('/login', { replace: true })
        }
      })

    return () => {
      cancelled = true
    }
  }, [token])

  // Fetch conversations
  const refreshConversations = async () => {
    if (!token) return
    try {
      const data = await fetchConversations(token)
      setConversations(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to fetch conversations:', err)
    }
  }

  useEffect(() => {
    if (!token) {
      setConversations([])
      return
    }
    refreshConversations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  // Autoscroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

  // Load a specific conversation
  const loadConversation = async (conversationId) => {
    if (!token) return
    try {
      const data = await fetchConversation(conversationId, token)
      const msgs = Array.isArray(data?.messages) ? data.messages : []
      setActiveConversationId(String(conversationId))
      setMessages(
        msgs.map((m, idx) => ({
          id: Date.now() + idx,
          text: m.text,
          sender: m.sender,
          attachments: m.attachments || null,
        }))
      )
    } catch (err) {
      setSendError(err.message)
    }
  }

  // Start a new chat
  const startNewChat = () => {
    setActiveConversationId('')
    setMessages([])
    setSendError('')
    clearAttachments()
    setActiveTranscriptId('')
    setActiveDocumentId('')
  }

  const handleNewChat = () => {
    startNewChat()
    if (window.innerWidth < 1024) setSidebarOpen(false)
  }

  // Logout
  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login', { replace: true })
  }

  // Attachment handling
  const clearAttachments = () => {
    for (const a of attachments) {
      if (a?.previewUrl) URL.revokeObjectURL(a.previewUrl)
    }
    setAttachments([])
  }

  const removeAttachment = (attachmentId) => {
    setAttachments((prev) => {
      const removed = prev.find((a) => a.id === attachmentId)
      if (removed?.previewUrl) URL.revokeObjectURL(removed.previewUrl)
      return prev.filter((a) => a.id !== attachmentId)
    })
  }

  const addFilesAsAttachments = (files) => {
    const newAttachments = []
    for (const file of files) {
      const kind = getAttachmentKind(file)
      const id = makeAttachmentId(file)
      let previewUrl = null

      if (kind === 'image') {
        previewUrl = URL.createObjectURL(file)
      }

      newAttachments.push({ id, file, kind, previewUrl })
    }
    setAttachments((prev) => [...prev, ...newAttachments])
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files && files.length > 0) addFilesAsAttachments(files)
    e.target.value = ''
  }

  // Transcribe attachment
  const transcribeAttachment = async (file) => {
    try {
      const transcriptId = await transcribeMedia(file, token)
      return transcriptId
    } catch (err) {
      throw new Error('Transcription failed: ' + err.message)
    }
  }

  // Parse document
  const parseDocumentFile = async (file) => {
    try {
      const documentId = await parseDocument(file, token)
      return documentId
    } catch (err) {
      throw new Error('Document parsing failed: ' + err.message)
    }
  }

  // Handle message send
  const handleSendMessage = async (e) => {
    e.preventDefault()
    const text = inputValue.trim()
    if (!text || isSending) return
    if (!token) {
      setSendError('Please login first.')
      return
    }

    setSendError('')
    setIsSending(true)

    const currentAttachments = attachments
    const attachmentMeta = currentAttachments.map((a) => ({
      name: a.file?.name || 'attachment',
      kind: a.kind,
      mimetype: a.file?.type || '',
      previewUrl: a.previewUrl || null,
    }))

    const userMessage = { id: Date.now(), text, sender: 'user', attachments: attachmentMeta }
    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setAttachments([])

    const mediaAttachment = currentAttachments.find((a) => a.kind === 'audio' || a.kind === 'video')
    const documentAttachment = currentAttachments.find((a) => a.kind === 'document')

    try {
      const payload = { message: text }
      if (activeConversationId) payload.conversation_id = activeConversationId

      if (attachmentMeta.length > 0) {
        payload.attachments = attachmentMeta.map(({ name, kind, mimetype }) => ({ name, kind, mimetype }))
      }

      let transcriptIdToUse = activeTranscriptId
      let documentIdToUse = activeDocumentId

      if (mediaAttachment?.file) {
        setIsTranscribing(true)
        transcriptIdToUse = await transcribeAttachment(mediaAttachment.file)
        setActiveTranscriptId(transcriptIdToUse)
        setIsTranscribing(false)
      }

      if (documentAttachment?.file) {
        setIsParsing(true)
        documentIdToUse = await parseDocumentFile(documentAttachment.file)
        setActiveDocumentId(documentIdToUse)
        setIsParsing(false)
      }

      if (transcriptIdToUse) {
        payload.transcript_id = transcriptIdToUse
        const window = extractTimeWindowFromPrompt(text)
        if (window?.start !== undefined) payload.start_time = window.start
        if (window?.end !== undefined) payload.end_time = window.end
      }

      if (documentIdToUse) {
        payload.document_id = documentIdToUse
      }

      const data = await sendChatMessage(payload, token)
      const assistantText = data?.message ?? ''
      const conversationId = data?.conversation_id
      if (conversationId) setActiveConversationId(String(conversationId))
      const assistantMessage = { id: Date.now() + 1, text: assistantText, sender: 'assistant' }
      setMessages((prev) => [...prev, assistantMessage])
      await refreshConversations()
    } catch (err) {
      setIsTranscribing(false)
      setIsParsing(false)
      setSendError(err instanceof Error ? err.message : 'Failed to send message')
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          text: 'Sorry — I could not complete that request. Check you are logged in and the backend is running.',
          sender: 'assistant',
        },
      ])
    } finally {
      setIsSending(false)
    }
  }

  const handleClearActiveContext = () => {
    setActiveTranscriptId('')
    setActiveDocumentId('')
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      for (const a of attachments) {
        if (a?.previewUrl) URL.revokeObjectURL(a.previewUrl)
      }
      for (const msg of messages) {
        if (!Array.isArray(msg?.attachments)) continue
        for (const a of msg.attachments) {
          if (a?.previewUrl) URL.revokeObjectURL(a.previewUrl)
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className={`flex h-screen ${darkMode ? 'bg-neutral-950' : 'bg-gray-50'}`}>
      <Sidebar
        darkMode={darkMode}
        sidebarOpen={sidebarOpen}        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}        conversations={conversations}
        onNewChat={handleNewChat}
        onSelectConversation={loadConversation}
        user={me}
        userAvatar={userAvatar}
        avatarName={avatarName}
        onLogout={handleLogout}
      />

      <div className="flex-1 flex flex-col relative">
        <Header
          darkMode={darkMode}
          onToggleDarkMode={() => setDarkMode(!darkMode)}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />

        <ChatArea
          darkMode={darkMode}
          messages={messages}
          user={me}
          isSending={isSending}
          isTranscribing={isTranscribing}
          isParsing={isParsing}
          messagesEndRef={messagesEndRef}
        />

        <ChatInput
          darkMode={darkMode}
          inputValue={inputValue}
          setInputValue={setInputValue}
          onSubmit={handleSendMessage}
          attachments={attachments}
          onAttach={handleFileSelect}
          onRemoveAttachment={removeAttachment}
          isSending={isSending}
          isTranscribing={isTranscribing}
          isParsing={isParsing}
          activeTranscriptId={activeTranscriptId}
          activeDocumentId={activeDocumentId}
          onClearActiveContext={handleClearActiveContext}
          sendError={sendError}
        />
      </div>
    </div>
  )
}

export default Home
