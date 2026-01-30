# Frontend Code Organization

## Overview
The frontend code has been reorganized from a monolithic 995-line `App.jsx` file into a well-structured React application using React Router for navigation and proper component separation.

## Folder Structure

```
client/src/
├── App.jsx                    # Main app with React Router setup
├── App.css                    # Global styles and custom scrollbar
├── main.jsx                   # Entry point
├── index.css                  # Base styles
├── pages/                     # Route-level components
│   ├── LoginSignup.jsx        # Authentication page
│   └── Home.jsx               # Main chat interface
├── components/                # Reusable UI components
│   ├── Sidebar.jsx            # Conversation list and user profile
│   ├── Header.jsx             # Top navigation bar
│   ├── ChatArea.jsx           # Message display area
│   └── ChatInput.jsx          # Input box with attachments
├── services/                  # API communication layer
│   └── api.js                 # All API calls to backend
└── utils/                     # Utility functions
    └── helpers.js             # Helper functions for attachments and timestamps
```

## Key Features

### 1. React Router Setup
- **Route Protection**: `ProtectedRoute` component checks for auth token
- **Smart Redirects**: Root path (`/`) automatically redirects based on login status
- **Routes**:
  - `/` → Redirects to `/home` if logged in, otherwise `/login`
  - `/login` → Login/Signup page
  - `/home` → Main chat interface (protected)

### 2. Component Separation

#### App.jsx (45 lines)
- React Router configuration
- Protected route wrapper
- Dark mode state management
- Clean and minimal

#### Pages
- **LoginSignup.jsx**: Handles user authentication
  - Login and signup tabs
  - Form validation
  - Redirects to `/home` on success using `useNavigate`
  
- **Home.jsx**: Main chat interface
  - All chat logic and state management
  - Manages conversations, messages, attachments
  - Coordinates between child components

#### Components
- **Sidebar.jsx**: Left sidebar
  - Logo and branding
  - New chat button
  - Conversation list
  - User profile with logout

- **Header.jsx**: Top navigation
  - Sidebar toggle
  - Title
  - Theme toggle (dark/light mode)

- **ChatArea.jsx**: Message display
  - Empty state with welcome message
  - Message bubbles (user/assistant)
  - Markdown rendering for AI responses
  - Attachment previews
  - Loading indicators

- **ChatInput.jsx**: Input box
  - Text input field
  - File attachment button
  - Attachment preview chips with remove
  - Transcript/document status display
  - Send button with validation

#### Services
- **api.js**: Centralized API communication
  - `transcribeMedia(file)` - Upload and transcribe audio/video
  - `parseDocument(file)` - Parse PDF, Word, Excel, JSON
  - `fetchUserProfile()` - Get current user info
  - `fetchConversations()` - Get conversation list
  - `fetchConversation(id)` - Get specific conversation
  - `sendChatMessage(payload)` - Send message to AI
  - `register(email, username, password)` - User registration
  - `login(email, password)` - User login
  - `apiBaseUrl` constant

#### Utils
- **helpers.js**: Utility functions
  - `getAttachmentKind(mimetype, filename)` - Determine file type
  - `makeAttachmentId()` - Generate unique attachment ID
  - `parseTimestampToSeconds(timestamp)` - Convert HH:MM:SS to seconds
  - `extractTimeWindowFromPrompt(text)` - Extract time ranges from prompt

## Authentication Flow

1. User visits `/` (root)
2. App checks `localStorage.getItem('auth_token')`
3. If token exists → Redirect to `/home`
4. If no token → Redirect to `/login`
5. After successful login → Navigate to `/home`
6. Protected routes check token before rendering

## Benefits of New Structure

1. **Maintainability**: Each component has a single responsibility
2. **Reusability**: Components can be used in different contexts
3. **Testability**: Isolated components are easier to test
4. **Scalability**: Easy to add new pages and components
5. **Collaboration**: Multiple developers can work on different files
6. **Code Navigation**: Clear file organization makes finding code easier
7. **Type Safety**: Easier to add TypeScript later if needed

## Migration Notes

- All functionality from the original App.jsx has been preserved
- No features were lost in the reorganization
- API calls are centralized in `services/api.js`
- Utility functions moved to `utils/helpers.js`
- Custom scrollbar CSS remains in `App.css`
- Dark mode state is managed at the App level and passed down

## Running the Application

```bash
cd client
npm install
npm run dev
```

The app will open at `http://localhost:5173` and automatically redirect based on authentication status.
