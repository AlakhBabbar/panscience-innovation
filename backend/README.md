# PanScience Backend API

FastAPI backend for the PanScience chat application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env`:

- Copy `.env.example` to `.env`
- Fill in at least:
	- `MONGODB_URI` (MongoDB Atlas connection string)
	- `MONGODB_DB`
	- `JWT_SECRET_KEY`
	- `GOOGLE_API_KEY`

5. Run the server:
```bash
uvicorn main:app --reload
```

Or simply:
```bash
python main.py
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/conversations` - Get all conversations
- `GET /api/conversations/{id}` - Get specific conversation
- `POST /api/chat` - Send chat message
- `POST /api/conversations` - Create new conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `POST /api/upload` - Upload files

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

The server runs on `http://localhost:8000` by default with auto-reload enabled.
