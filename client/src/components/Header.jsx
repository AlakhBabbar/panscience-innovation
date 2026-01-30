import { Menu, Sun, Moon } from 'lucide-react'

function Header({ darkMode, onToggleDarkMode, onToggleSidebar }) {
  return (
    <div className={`absolute top-0 left-0 right-0 z-10 ${darkMode ? 'bg-neutral-950/95 backdrop-blur-sm' : 'bg-white/95 backdrop-blur-sm'} px-6 py-4 flex items-center justify-between border-b ${darkMode ? 'border-neutral-800' : 'border-gray-200'}`}>
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-neutral-900' : 'hover:bg-gray-100'}`}
        >
          <Menu size={24} className={darkMode ? 'text-white' : 'text-gray-600'} />
        </button>
        <h1 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Chat Assistant</h1>
      </div>
      <button
        onClick={onToggleDarkMode}
        className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-neutral-900' : 'hover:bg-gray-100'}`}
        title="Toggle theme"
      >
        {darkMode ? <Sun size={20} className="text-white" /> : <Moon size={20} className="text-gray-600" />}
      </button>
    </div>
  )
}

export default Header
