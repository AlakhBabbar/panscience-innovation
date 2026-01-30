import { MessageSquare, FileAudio, FileVideo, FileText, Image as ImageIcon } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function ChatArea({ darkMode, messages, user, isSending, isTranscribing, isParsing, messagesEndRef }) {
  return (
    <div 
      className="absolute inset-0 overflow-y-auto scrollbar-custom"
      style={{
        scrollbarWidth: 'thin',
        scrollbarColor: darkMode ? '#525252 #171717' : '#d1d5db #f9fafb'
      }}
    >
      <div className="pt-16 sm:pt-20 pb-40 sm:pb-48">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] sm:min-h-[calc(100vh-13rem)]">
            <div className="text-center max-w-2xl mx-auto px-4">
              <div className={`w-12 h-12 sm:w-16 sm:h-16 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6 ${darkMode ? 'bg-neutral-900' : 'bg-gray-100'}`}>
                <MessageSquare size={24} className={`${darkMode ? 'text-white' : 'text-gray-900'} sm:w-8 sm:h-8`} />
              </div>
              <h2 className={`text-2xl sm:text-3xl font-bold mb-2 sm:mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Welcome back, {user?.username.split(' ')[0]}!
              </h2>
              <p className={`text-base sm:text-lg ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                How can I assist you today? Start a conversation by typing your question below.
              </p>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6 px-3 sm:px-6">
            {messages.map(message => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-[70%] px-3 sm:px-4 py-2.5 sm:py-3 rounded-2xl ${
                    message.sender === 'user'
                      ? darkMode ? 'bg-neutral-800 text-white' : 'bg-gray-100 text-gray-900'
                      : darkMode ? 'bg-neutral-900 text-white border border-neutral-800' : 'bg-white text-gray-900 border border-gray-200'
                  }`}
                >
                  {Array.isArray(message.attachments) && message.attachments.length > 0 && (
                    <div className="mb-2 flex flex-wrap gap-2">
                      {message.attachments.map((a, idx) => {
                        const kind = a?.kind || 'document'
                        const name = a?.name || 'attachment'
                        const previewUrl = a?.previewUrl || null
                        return (
                          <div
                            key={`${name}-${idx}`}
                            className={`flex items-center gap-2 rounded-xl border px-2 py-2 ${
                              message.sender === 'user'
                                ? darkMode
                                  ? 'border-neutral-700 bg-neutral-700/40'
                                  : 'border-gray-300 bg-white'
                                : darkMode
                                  ? 'border-neutral-800 bg-neutral-950'
                                  : 'border-gray-300 bg-gray-100'
                            }`}
                            title={name}
                          >
                            {kind === 'image' && previewUrl ? (
                              <img src={previewUrl} alt={name} className="w-10 h-10 rounded-lg object-cover" />
                            ) : (
                              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                                message.sender === 'user'
                                  ? darkMode ? 'bg-neutral-700' : 'bg-gray-200'
                                  : darkMode ? 'bg-neutral-900' : 'bg-gray-200'
                              }`}>
                                {kind === 'audio' ? (
                                  <FileAudio size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                                ) : kind === 'video' ? (
                                  <FileVideo size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                                ) : kind === 'image' ? (
                                  <ImageIcon size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                                ) : (
                                  <FileText size={20} className={darkMode ? 'text-gray-300' : 'text-gray-700'} />
                                )}
                              </div>
                            )}
                            <div className="min-w-0">
                              <div className={`text-xs font-medium truncate max-w-55 ${darkMode ? (message.sender === 'user' ? 'text-white' : 'text-gray-200') : (message.sender === 'user' ? 'text-gray-900' : 'text-gray-800')}`}>
                                {name}
                              </div>
                              <div className={`text-[11px] ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{kind}</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {message.sender === 'assistant' ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                        em: ({ children }) => <em className="italic">{children}</em>,
                        ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 my-2">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1 my-2">{children}</ol>,
                        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                        h1: ({ children }) => <h1 className="text-xl font-semibold mt-2 mb-2">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-semibold mt-2 mb-2">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-base font-semibold mt-2 mb-2">{children}</h3>,
                        blockquote: ({ children }) => (
                          <blockquote className={`border-l-4 pl-3 my-2 ${darkMode ? 'border-neutral-700 text-gray-200' : 'border-gray-300 text-gray-700'}`}>
                            {children}
                          </blockquote>
                        ),
                        code: ({ inline, children }) =>
                          inline ? (
                            <code className={`px-1 py-0.5 rounded ${darkMode ? 'bg-neutral-800' : 'bg-gray-200'}`}>{children}</code>
                          ) : (
                            <code className="block whitespace-pre-wrap">{children}</code>
                          ),
                        pre: ({ children }) => (
                          <pre className={`my-2 p-3 rounded-lg overflow-x-auto text-sm ${darkMode ? 'bg-neutral-950 border border-neutral-800' : 'bg-white border border-gray-200'}`}>
                            {children}
                          </pre>
                        ),
                        a: ({ href, children }) => (
                          <a
                            href={href}
                            target="_blank"
                            rel="noreferrer"
                            className={`${darkMode ? 'text-blue-300' : 'text-blue-700'} underline`}
                          >
                            {children}
                          </a>
                        ),
                      }}
                    >
                      {message.text}
                    </ReactMarkdown>
                  ) : (
                    message.text
                  )}
                </div>
              </div>
            ))}

            {isSending && (
              <div className="flex justify-start">
                <div
                  className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                    darkMode
                      ? 'bg-neutral-900 text-white border border-neutral-800'
                      : 'bg-gray-100 text-black border border-gray-200'
                  }`}
                >
                  {isTranscribing ? 'Transcribing file…' : isParsing ? 'Parsing document…' : 'Thinking…'}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatArea
