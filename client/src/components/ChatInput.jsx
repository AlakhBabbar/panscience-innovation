import { useRef } from 'react'
import { Paperclip, Send, X, FileAudio, FileVideo, FileText, Image as ImageIcon } from 'lucide-react'

function ChatInput({ 
  darkMode, 
  inputValue, 
  setInputValue,
  onSubmit, 
  attachments, 
  onAttach, 
  onRemoveAttachment,
  isSending, 
  isTranscribing,
  isParsing,
  activeTranscriptId,
  activeDocumentId,
  onClearActiveContext,
  sendError
}) {
  const fileInputRef = useRef(null)

  const handleFileAttachment = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="absolute bottom-3 sm:bottom-6 left-1/2 -translate-x-1/2 z-20 w-full max-w-3xl px-3 sm:px-6">
      <form onSubmit={onSubmit} className={`${darkMode ? 'bg-neutral-900/95 backdrop-blur-md' : 'bg-white/95 backdrop-blur-md'} rounded-xl sm:rounded-2xl shadow-2xl border ${darkMode ? 'border-neutral-800' : 'border-gray-200'}`}>
        {sendError && (
          <div
            className={`mx-4 mt-4 mb-2 text-sm ${darkMode ? 'text-red-300' : 'text-red-700'}`}
            role="alert"
          >
            {sendError}
          </div>
        )}
        
        <div className={`p-3 transition-colors ${darkMode ? 'focus-within:bg-neutral-800/50' : 'focus-within:bg-gray-50'}`}>
          {(isTranscribing || isParsing || activeTranscriptId || activeDocumentId) && (
            <div className={`px-2 pt-2 ${attachments.length > 0 ? 'pb-1' : 'pb-2'}`}>
              <div className="flex items-center gap-2">
                <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  {isTranscribing
                    ? 'Transcribing audio/video with timestamps…'
                    : isParsing
                    ? 'Parsing document…'
                    : activeTranscriptId
                    ? 'Transcript ready (timestamped). Ask using timestamps in your prompt (e.g., 01:20-02:10).'
                    : activeDocumentId
                    ? 'Document parsed and ready. Ask questions about the document.'
                    : null}
                </div>

                {(activeTranscriptId || activeDocumentId) && !isTranscribing && !isParsing && (
                  <button
                    type="button"
                    onClick={onClearActiveContext}
                    className={`ml-auto text-xs px-2 py-1 rounded-lg transition-colors ${
                      darkMode ? 'text-gray-400 hover:text-white hover:bg-neutral-800' : 'text-gray-600 hover:text-black hover:bg-gray-100'
                    }`}
                    title="Clear transcript/document"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          )}

          {attachments.length > 0 && (
            <div className="px-2 pt-2 pb-1">
              <div className="flex flex-wrap gap-2">
                {attachments.map((a) => (
                  <div
                    key={a.id}
                    className={`flex items-center gap-2 rounded-xl border px-2 py-2 max-w-full ${darkMode ? 'border-neutral-700 bg-neutral-800' : 'border-gray-300 bg-white shadow-sm'}`}
                    title={a.file.name}
                  >
                    {a.kind === 'image' && a.previewUrl ? (
                      <img
                        src={a.previewUrl}
                        alt={a.file.name}
                        className="w-10 h-10 rounded-lg object-cover"
                      />
                    ) : (
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${darkMode ? 'bg-neutral-900' : 'bg-gray-100'}`}>
                        {a.kind === 'audio' ? (
                          <FileAudio size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                        ) : a.kind === 'video' ? (
                          <FileVideo size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                        ) : a.kind === 'image' ? (
                          <ImageIcon size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                        ) : (
                          <FileText size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                        )}
                      </div>
                    )}

                    <div className="min-w-0">
                      <div className={`text-xs font-medium truncate max-w-55 ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                        {a.file.name}
                      </div>
                      <div className={`text-[11px] ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                        {a.kind}
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => onRemoveAttachment(a.id)}
                      className={`p-1 rounded-lg transition-colors ${darkMode ? 'text-gray-400 hover:text-white hover:bg-neutral-800' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'}`}
                      title="Remove attachment"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-end gap-2 sm:gap-3">
            {/* Attachment Button */}
            <button
              type="button"
              onClick={handleFileAttachment}
              className={`p-2 rounded-lg transition-colors ${darkMode ? 'text-gray-400 hover:text-white hover:bg-neutral-800' : 'text-gray-600 hover:text-black hover:bg-gray-100'}`}
              title="Attach files"
            >
              <Paperclip size={20} className="sm:w-6 sm:h-6" />
            </button>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,video/*,audio/*,.pdf"
              onChange={onAttach}
              className="hidden"
            />

            {/* Text Input */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={isTranscribing ? 'Transcribing file…' : isParsing ? 'Parsing document…' : isSending ? 'Sending…' : 'Type your message here...'}
              className={`flex-1 px-2 sm:px-3 py-2 bg-transparent outline-none text-sm sm:text-base ${darkMode ? 'text-white placeholder-gray-500' : 'text-gray-900 placeholder-gray-500'}`}
            />

            {/* Send Button */}
            <button
              type="submit"
              disabled={!inputValue.trim() || isSending || isTranscribing || isParsing}
              className={`p-2 rounded-lg transition-colors ${
                inputValue.trim() && !isSending && !isTranscribing && !isParsing
                  ? darkMode ? 'bg-white text-black hover:bg-gray-200' : 'bg-gray-900 text-white hover:bg-gray-800'
                  : darkMode ? 'bg-neutral-800 text-gray-600 cursor-not-allowed' : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Send size={20} className="sm:w-6 sm:h-6" />
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}

export default ChatInput
