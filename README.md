# Medical Price Comparator

A medical analysis price comparator for Romania with AI integration for OCR and price comparison across multiple healthcare providers.

## Features

- AI-powered OCR for reading doctor recommendations
- Price comparison across multiple providers (Regina Maria, Medlife, etc.)
- Admin import tools for CSV data
- Simple HTML/JS frontend interface
- FastAPI backend with MongoDB
- Docker containerization

## Project Structure

```
medical_price_comparator/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── models/      # MongoDB models
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Business logic
│   │   └── main.py      # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # HTML/JS frontend
│   ├── static/
│   ├── templates/
│   └── index.html
├── docker-compose.yml   # Docker configuration
└── README.md
```

## Getting Started

1. Clone the repository
2. Run with Docker: `docker-compose up`
3. Access the application at `http://localhost:8000`

## Development

- Backend: FastAPI with MongoDB
- Frontend: Vanilla HTML/JS
- AI Integration: LangFun for OCR and analysis
- Database: MongoDB with efficient indexing