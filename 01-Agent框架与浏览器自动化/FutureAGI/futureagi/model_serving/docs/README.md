# Model Serving API - Bruno Collection 📡

This Bruno collection provides comprehensive API documentation and testing for the Model Serving API. Bruno is a fast, open-source API client that stores collections as files in your repository.

## 📋 Collection Overview

The collection includes endpoints for:

### 🔧 **Core Endpoints**
- **Root Endpoint** - Service information and status
- **Health Check** - Service health and monitoring
- **API Documentation** - Interactive Swagger UI

### 🧠 **Embedding Endpoints**
- **Text Embeddings** - Generate text embeddings with batch support
- **Image Embeddings** - Process images for visual similarity search
- **Audio Embeddings** - Extract features from audio files
- **Image-Text Embeddings** - Multimodal embeddings for cross-modal search

### 📊 **Model Management**
- **List Available Models** - Get information about all available models

## 🚀 Quick Start

### Prerequisites

1. **Install Bruno**: Download from [usebruno.com](https://www.usebruno.com/)
2. **Start Model Serving**: Ensure the model serving API is running
   ```bash
   cd model_serving
   make serve  # or uv run serve --reload
   ```

### Using the Collection

1. **Open Bruno** and import this collection
2. **Select Environment**:
   - `Development` - Local development server (localhost:8080)
   - `Docker` - Docker container (localhost:8080)
   - `Production` - Production server (update URL as needed)
3. **Run Requests** - Click on any endpoint and hit "Send"

## 🌍 Environments

### Development
```
base_url: http://localhost:8080
api_version: v1
```

### Docker
```
base_url: http://localhost:8080
api_version: v1
```

### Production
```
base_url: https://your-model-serving-domain.com
api_version: v1
```

## 📁 Collection Structure

```
bruno/
├── bruno.json                           # Collection configuration
├── README.md                           # This documentation
├── core/                               # Core API endpoints
│   ├── Root Endpoint.bru              # GET /
│   ├── Health Check.bru               # GET /health
│   └── API Documentation.bru          # GET /docs
├── embeddings/                        # Embedding endpoints
│   ├── Text Embeddings.bru           # POST /model/v1/embed
│   ├── Image Embeddings.bru          # POST /model/v1/embed/image
│   ├── Audio Embeddings.bru          # POST /model/v1/embed/audio
│   └── Image-Text Embeddings.bru     # POST /model/v1/embed/image-text
└── models/                           # Model management
    └── List Available Models.bru     # GET /model/v1/models
```

## 🧪 Testing Features

Each endpoint includes:

- **📖 Comprehensive Documentation** - Detailed descriptions, parameters, and examples
- **🔍 Automated Tests** - Response validation and error checking
- **💡 Examples** - Real request/response examples
- **⚡ Performance Tests** - Response time validation

### Test Coverage

- ✅ Status code validation
- ✅ Response structure validation
- ✅ Data type checking
- ✅ Business logic validation
- ✅ Performance benchmarks

## 🛠️ Usage Examples

### 1. Basic Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### 2. Text Embeddings (Single)

```http
POST /model/v1/embed
Content-Type: application/json

{
  "text": "Hello world",
  "input_type": "text"
}
```

### 3. Text Embeddings (Batch)

```http
POST /model/v1/embed
Content-Type: application/json

{
  "text": [
    "First sentence for embedding",
    "Second sentence for comparison",
    "Third sentence for analysis"
  ],
  "input_type": "text"
}
```

### 4. Image Embeddings

```http
POST /model/v1/embed/image
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAQABAAD...",
  "input_type": "image"
}
```

### 5. Cross-Modal Search

```http
POST /model/v1/embed/image-text
Content-Type: application/json

{
  "text": "A red sports car on a city street",
  "input_type": "image-text"
}
```

## 🔧 Environment Configuration

### Switching Environments

1. Click on the environment dropdown in Bruno
2. Select the appropriate environment:
   - **Development** - For local development
   - **Docker** - For Docker container testing
   - **Production** - For production testing

### Custom Environment Variables

You can add custom environment variables:

```json
{
  "name": "Custom",
  "variables": [
    {
      "name": "base_url",
      "value": "http://custom-host:8080",
      "enabled": true,
      "secret": false
    },
    {
      "name": "api_key",
      "value": "your-api-key",
      "enabled": true,
      "secret": true
    }
  ]
}
```

## 📊 Response Examples

### Successful Text Embedding

```json
{
  "embeddings": [
    [0.1234, -0.5678, 0.9012, ...]
  ]
}
```

### Model Information

```json
{
  "models": {
    "text_embedding": {
      "name": "sentence-transformers/all-MiniLM-L6-v2",
      "type": "text",
      "status": "loaded",
      "dimensions": 384
    }
  },
  "server_info": {
    "total_models": 4,
    "loaded_models": 3,
    "memory_usage": "2.1GB"
  }
}
```

### Error Response

```json
{
  "detail": "Validation error: text field is required",
  "status_code": 422
}
```

## 🚨 Error Handling

The collection includes comprehensive error testing:

### Common Error Codes

- `400 Bad Request` - Invalid input format
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Model or server errors
- `503 Service Unavailable` - Service not ready

### Error Testing

Each endpoint tests various error scenarios:
- Missing required fields
- Invalid data types
- Malformed requests
- Server errors

## 🎯 Best Practices

### 1. **Environment Management**
- Use Development for local testing
- Use Docker for container validation
- Use Production with care

### 2. **Request Optimization**
- Use batch processing for multiple texts
- Compress images before encoding
- Keep audio files under recommended limits

### 3. **Response Handling**
- Always check status codes
- Validate response structure
- Handle errors gracefully

### 4. **Performance Testing**
- Monitor response times
- Test with various input sizes
- Check memory usage patterns

## 🔍 Debugging

### Common Issues

1. **Connection Refused**
   - Ensure the model serving API is running
   - Check the correct port (default: 8080)
   - Verify the base_url in your environment

2. **Model Not Loaded**
   - Check `/model/v1/models` for model status
   - Wait for models to load on first startup
   - Check server logs for loading errors

3. **Invalid Base64**
   - Ensure proper base64 encoding
   - Include data URI prefix for images/audio
   - Check for encoding corruption

4. **Timeout Errors**
   - Large files may take longer to process
   - Increase timeout in Bruno settings
   - Consider reducing input size

### Debugging Steps

1. **Test Health First**: Always start with `/health`
2. **Check Models**: Use `/model/v1/models` to verify model status
3. **Start Simple**: Test with minimal inputs first
4. **Check Logs**: Monitor server logs for detailed errors

## 📈 Performance Benchmarks

Expected response times (approximate):

- **Health Check**: < 50ms
- **Text Embeddings**: 100-500ms (depends on text length)
- **Image Embeddings**: 200-1000ms (depends on image size)
- **Audio Embeddings**: 500-2000ms (depends on audio length)
- **Model List**: < 100ms

## 🤝 Contributing

To add new endpoints or improve existing ones:

1. Create new `.bru` files in appropriate folders
2. Follow the existing format and documentation style
3. Include comprehensive tests and examples
4. Update this README with new endpoints

## 📚 Additional Resources

- **Bruno Documentation**: https://docs.usebruno.com/
- **Model Serving API**: See the main README.md in the project root
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **OpenAPI Specification**: Available at `/docs` endpoint

---

**Happy API Testing! 🚀**

*This collection provides everything you need to explore, test, and integrate with the Model Serving API.*
