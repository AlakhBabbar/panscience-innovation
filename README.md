# PanScience AI Chat Assistant

A full-stack intelligent chat application with advanced features including audio/video transcription, document parsing, and conversation management powered by Google's Gemini AI.

## Overview

This project is a comprehensive chat application that combines modern web technologies with AI capabilities. Users can have conversations with an AI assistant, upload various types of files (audio, video, documents), and receive intelligent responses based on the content. The application maintains conversation history and supports timestamped queries for media files.

## Features

### Core Functionality

- **AI-Powered Chat**: Integration with Google Gemini 2.5 Flash for intelligent conversational responses
- **User Authentication**: Secure JWT-based authentication with login/signup functionality
- **Conversation Management**: Persistent conversation history stored in MongoDB
- **Dark/Light Theme**: Toggle between dark and light modes with preference persistence

### Advanced Features

#### 1. Audio/Video Transcription
- Upload audio and video files for automatic transcription
- Powered by Deepgram API for accurate speech-to-text conversion
- Timestamped transcription enables precise queries (e.g., "what was discussed at 01:20-02:10")
- Supports time window extraction from natural language prompts

#### 2. Document Parsing
- Upload and parse multiple document formats:
  - PDF documents
  - Microsoft Word (.doc, .docx)
  - Excel spreadsheets (.xls, .xlsx)
  - JSON files
- Automatic content extraction and analysis
- Ask questions about uploaded documents

#### 3. Multi-Modal Attachments
- Support for images, audio, video, and documents
- Image preview in chat interface
- File type detection and appropriate icon display
- Multiple file uploads in a single message

#### 4. Conversation History
- All conversations are persisted to MongoDB
- Recent conversations list in sidebar
- Load previous conversations with full message history
- AI receives conversation context for coherent responses

#### 5. Responsive UI
- Modern, minimalist design with Tailwind CSS
- Custom scrollbar styling
- Floating input box with backdrop blur
- Markdown rendering for AI responses (headers, lists, code blocks, links, etc.)
- Auto-scroll to latest messages
- Loading states for transcription and document parsing

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async driver)
- **AI Model**: Google Gemini 2.5 Flash Lite (via LangChain)
- **Authentication**: JWT tokens with OAuth2 password flow
- **Transcription**: Deepgram API
- **Document Processing**: 
  - pypdf (PDF parsing)
  - python-docx (Word documents)
  - openpyxl (Excel files)
  - pandas (data processing)

### Frontend
- **Framework**: React 18 with Vite
- **Routing**: React Router v6 with protected routes
- **Styling**: Tailwind CSS
- **Markdown**: react-markdown with remark-gfm
- **Icons**: Lucide React
- **HTTP Client**: Fetch API

## Project Structure

```
panscience-assessment/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── services/
│   │   ├── chat_service.py    # Gemini AI integration
│   │   ├── document_service.py # Document parsing logic
│   │   └── document_store.py   # MongoDB document operations
│   └── README.md
│
├── client/
│   ├── src/
│   │   ├── App.jsx            # React Router setup
│   │   ├── App.css            # Global styles, custom scrollbar
│   │   ├── pages/
│   │   │   ├── LoginSignup.jsx # Authentication page
│   │   │   └── Home.jsx        # Main chat interface
│   │   ├── components/
│   │   │   ├── Sidebar.jsx     # Conversation list & user profile
│   │   │   ├── Header.jsx      # Top navigation bar
│   │   │   ├── ChatArea.jsx    # Message display area
│   │   │   └── ChatInput.jsx   # Input box with attachments
│   │   ├── services/
│   │   │   └── api.js          # API communication layer
│   │   └── utils/
│   │       └── helpers.js      # Utility functions
│   ├── package.json
│   └── FRONTEND_STRUCTURE.md
│
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB Atlas account (or local MongoDB)
- Google AI API key (for Gemini)
- Deepgram API key (for transcription)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with required environment variables:
```env
MONGODB_URI=your_mongodb_connection_string
GOOGLE_AI_API_KEY=your_google_ai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
JWT_SECRET=your_jwt_secret_key
```

4. Start the FastAPI server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the client directory:
```bash
cd client
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file (optional, defaults to localhost:8000):
```env
VITE_API_BASE_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/token` - Login and get JWT token
- `GET /auth/me` - Get current user profile

### Chat
- `POST /api/chat` - Send message and get AI response
- `GET /api/conversations` - List user's conversations
- `GET /api/conversations/{id}` - Get specific conversation with messages

### Media & Documents
- `POST /api/media/transcribe` - Upload and transcribe audio/video
- `POST /api/documents/parse` - Upload and parse document
- `GET /api/documents` - List parsed documents
- `GET /api/documents/{id}` - Get document content

## Usage

### Basic Chat
1. Register or login with your credentials
2. Type your message in the input box
3. Press Enter or click the send button
4. Receive AI-generated responses

### Audio/Video Transcription
1. Click the attachment button (paperclip icon)
2. Select an audio or video file
3. The file will be automatically transcribed
4. Ask questions about specific time ranges: "what was said between 01:20 and 02:30"

### Document Analysis
1. Click the attachment button
2. Select a PDF, Word, Excel, or JSON file
3. The document will be parsed automatically
4. Ask questions about the document content

### Managing Conversations
- Click "New Chat" to start a fresh conversation
- Previous conversations appear in the sidebar
- Click any conversation to load its full history

### Theme Switching
- Click the sun/moon icon in the header to toggle between dark and light modes
- Theme preference is saved automatically

## Authentication Flow

1. Unauthenticated users are redirected to `/login`
2. After successful login, users are redirected to `/home`
3. Protected routes check for valid JWT token
4. Token is stored in localStorage
5. Expired/invalid tokens trigger automatic logout and redirect to login

## Key Implementation Details

### Conversation History in AI Responses
- Backend passes up to 40 recent messages to the LLM
- Maintains context across multiple user interactions
- Differentiates between transcript-based and general prompts

### Timestamp Extraction
- Natural language parsing for time ranges ("from 1:20 to 2:30", "between 01:20-02:10")
- Supports both mm:ss and hh:mm:ss formats
- Automatic window creation for single timestamp mentions

### Component Architecture
- Separation of concerns with pages and reusable components
- Centralized API service layer
- Utility functions for common operations
- Protected and public route wrappers

## Development Notes

### Code Organization
The frontend was recently reorganized from a monolithic 995-line App.jsx into:
- Two route-level pages (LoginSignup, Home)
- Four reusable UI components (Sidebar, Header, ChatArea, ChatInput)
- Centralized API service layer
- Utility functions module

This structure improves maintainability, reusability, and enables easier testing and collaboration.

### Custom Features
- Custom scrollbar styling matching the theme
- Auto-scroll on new messages
- Floating input box with backdrop blur
- Markdown rendering with syntax highlighting
- File preview with type-specific icons
- Loading indicators for async operations

## Future Enhancements

Potential areas for expansion:
- Voice input/output
- Real-time collaboration
- Message search functionality
- File download from chat
- Message editing and deletion
- Conversation sharing
- Export chat history
- Custom AI model selection

## License

This project is part of a technical assessment for PanScience.
