import { Plus, LogOut } from 'lucide-react'

function Sidebar({ 
  darkMode, 
  sidebarOpen, 
  conversations, 
  onNewChat, 
  onSelectConversation, 
  user, 
  userAvatar, 
  avatarName,
  onLogout 
}) {
  return (
    <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 ${darkMode ? 'bg-neutral-900' : 'bg-white'} ${darkMode ? 'text-white' : 'text-gray-900'} flex flex-col overflow-hidden`}>
      <div className="w-64 flex flex-col h-full">
        {/* Logo */}
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg ${darkMode ? 'bg-white text-black' : 'bg-gray-900 text-white'}`}>
                PS
              </div>
              <span className="font-semibold text-lg">PanScience</span>
            </div>
          </div>
        </div>

        {/* Conversation History */}
        <div className="flex-1 overflow-y-auto p-4">
          <button className={`w-full mb-4 text-sm font-medium transition-colors flex items-center gap-2 ${darkMode ? 'text-white hover:text-gray-300' : 'text-gray-900 hover:text-gray-600'}`}>
            <Plus size={18} />
            <span onClick={onNewChat} role="button" tabIndex={0}>New Chat</span>
          </button>
          
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Recent Conversations</h3>
            {conversations.map(conv => (
              <button
                key={conv.id}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors group ${darkMode ? 'hover:bg-neutral-800' : 'hover:bg-gray-200'}`}
                onClick={() => onSelectConversation(conv.id)}
              >
                <div className="text-sm font-medium truncate">{conv.title}</div>
              </button>
            ))}
          </div>
        </div>

        {/* User Profile */}
        <div className="p-4">
          <button className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group ${darkMode ? 'hover:bg-neutral-800' : 'hover:bg-gray-200'}`}>
            <img
              src={userAvatar}
              alt={avatarName}
              className="w-10 h-10 rounded-full"
            />
            <div className="flex-1 text-left">
              <div className="text-sm font-medium">{user?.username || user?.email}</div>
              <div className="text-xs text-gray-500">Signed in</div>
            </div>
            <span
              className={`p-2 rounded-lg transition-colors ${darkMode ? 'text-gray-500 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
              onClick={onLogout}
              role="button"
              tabIndex={0}
              title="Logout"
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') onLogout()
              }}
            >
              <LogOut size={20} />
            </span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
