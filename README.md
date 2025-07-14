# PDF and YouTube Video Query API with Azure OpenAI

A FastAPI application that allows users to upload PDF documents and YouTube videos, then query them using Azure OpenAI for intelligent question-answering.

## Features

- **PDF Processing**: Upload and query multiple PDF documents
- **YouTube Integration**: Process YouTube video transcripts (with cloud deployment fallbacks)
- **Smart Search**: Intelligent search strategies across different content types
- **Azure OpenAI**: Powered by Azure OpenAI for accurate question answering
- **Vector Storage**: Uses Qdrant for efficient semantic search
- **RESTful API**: Clean, documented API endpoints

## Prerequisites

- Python 3.8+
- Azure OpenAI account and deployment
- Qdrant cloud account (or local instance)

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Update your `.env` file with your actual credentials:

```env
SHREYA_NAME="Your Name"

# Qdrant Configuration
QDRANT_KEY = "your-qdrant-api-key"

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = "your-azure-openai-api-key"
AZURE_OPENAI_ENDPOINT = "https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME = "your-gpt-deployment-name"
AZURE_OPENAI_API_VERSION = "2025-01-01-preview"
```

### 3. Run the Application

```bash
# Start the server
uvicorn app.main:app --reload

# The API will be available at:
# - Main API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
# - Alternative docs: http://localhost:8000/redoc
```

### 4. Test the Application

```bash
# Run the test script
python test_api.py
```

## Azure OpenAI Setup

### Getting Your Credentials

1. **Azure OpenAI API Key**:

   - Go to your Azure OpenAI resource in Azure Portal
   - Navigate to "Keys and Endpoint"
   - Copy one of the API keys

2. **Azure OpenAI Endpoint**:

   - In the same "Keys and Endpoint" section
   - Copy the Endpoint URL (should end with `.openai.azure.com/`)

3. **Deployment Name**:

   - Go to "Model deployments" in your Azure OpenAI resource
   - Copy the deployment name (not the model name)

4. **API Version**:
   - Use `2025-01-01-preview` (latest stable version)
   - Check Azure OpenAI documentation for newer versions

## API Endpoints

### Health & Testing

- `GET /` - Health check
- `GET /test-azure-openai` - Test Azure OpenAI connectivity
- `GET /youtube-status` - Check YouTube API accessibility

### PDF Management

- `POST /upload-pdf/` - Upload PDF documents
- `GET /documents/` - List uploaded documents
- `POST /query/` - Query all documents
- `POST /query-document/` - Query specific document
- `POST /smart-query/` - Intelligent query with strategy

### YouTube Management

- `POST /upload-youtube/` - Upload YouTube video transcript
- `GET /videos/` - List uploaded videos
- `POST /query-youtube/` - Query specific video

### Smart Querying

- `POST /smart-query-all/` - Query across PDFs, videos, or both
- `GET /content-summary/` - Get content summary

## Usage Examples

### Upload a PDF

```bash
curl -X POST "http://localhost:8000/upload-pdf/" \
  -F "files=@document.pdf"
```

### Query Documents

```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?", "k": 3}'
```

### Upload YouTube Video

```bash
curl -X POST "http://localhost:8000/upload-youtube/" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "manual_transcript": "Optional manual transcript text"
  }'
```

## Cloud Deployment Considerations

### YouTube Transcript Limitations

- Cloud providers (Azure/AWS/GCP) IPs may be blocked by YouTube
- Solution: Use manual transcript input for cloud deployments
- The API provides fallback mechanisms and clear error messages

### Environment Variables in Production

- Store sensitive keys in Azure Key Vault or similar
- Use environment-specific configuration files
- Never commit actual API keys to version control

## Development

### Project Structure

```
askpdfAzDep/
├── app/
│   ├── main.py              # Main FastAPI application
│   └── qdrant_utils.py      # Vector database utilities
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── test_api.py             # API test script
└── README.md               # This file
```

### Key Technologies

- **FastAPI**: Modern, fast web framework
- **Azure OpenAI**: Large language model API
- **Qdrant**: Vector database for semantic search
- **PyMuPDF**: PDF text extraction
- **youtube-transcript-api**: YouTube transcript retrieval
- **LangChain**: Text processing and chunking

### Debugging

Use VS Code with the following `launch.json` configuration:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

## Migration Notes

This project has been migrated from Google Gemini to Azure OpenAI:

### ✅ Completed Changes

- Replaced `google-generativeai` with `openai` library
- Updated all API calls to use Azure OpenAI client
- Modified environment configuration
- Enhanced error handling
- Improved code structure and documentation

### Benefits of Azure OpenAI

- Better enterprise integration
- Consistent performance in cloud environments
- Enhanced security and compliance
- More predictable pricing

## Troubleshooting

### Common Issues

1. **Azure OpenAI Connection Failed**

   - Check your API key and endpoint
   - Verify deployment name is correct
   - Ensure API version is supported

2. **YouTube Transcript Blocked**

   - Use manual transcript input
   - Check `/youtube-status` endpoint
   - Consider proxy solutions for production

3. **PDF Upload Failed**

   - Ensure PDF has extractable text
   - Check file size limits
   - Verify file permissions

4. **Qdrant Connection Issues**
   - Check your Qdrant API key
   - Verify network connectivity
   - Ensure proper authentication

### Getting Help

- Check the interactive documentation at `/docs`
- Run the test script to identify issues
- Check server logs for detailed error messages
- Verify environment variables are correctly set

## License

This project is for educational and development purposes.
