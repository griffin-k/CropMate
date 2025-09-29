# Virtual Agronomist Setup Guide

## Overview
The Virtual Agronomist feature integrates with Groq API to provide AI-powered agricultural advice using Llama models.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install groq
```

### 2. Get Groq API Key
1. Visit [Groq Console](https://console.groq.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the API key

### 3. Set Environment Variable
Add your Groq API key to your environment:

**For macOS/Linux:**
```bash
export GROQ_API_KEY="your-groq-api-key-here"
```

**For Windows:**
```cmd
set GROQ_API_KEY=your-groq-api-key-here
```

**Or create a .env file in your project root:**
```
GROQ_API_KEY=your-groq-api-key-here
```

### 4. Features
The Virtual Agronomist can help with:
- ✅ Crop planning & rotation advice
- ✅ Pest and disease identification
- ✅ Soil health recommendations  
- ✅ Irrigation management tips
- ✅ Fertilizer recommendations
- ✅ Weather-based farming advice
- ✅ Sustainable farming practices

### 5. Usage
1. Navigate to the Agronomist page in CropMate
2. Ask questions using natural language
3. Use quick suggestion buttons for common queries
4. Get real-time AI responses powered by Llama models

### 6. API Details
- **Model**: llama-3.1-8b-instant
- **Temperature**: 0.7 (balanced creativity/accuracy)
- **Max Tokens**: 500 (concise responses)
- **System Prompt**: Specialized for agricultural expertise

### 7. Error Handling
- Network connectivity issues are handled gracefully
- API rate limits are managed
- Fallback responses for service unavailability
- User-friendly error messages

### 8. Security
- API key stored as environment variable
- CSRF protection for form submissions
- User authentication required
- Input sanitization

## Testing
To test the integration:
1. Set your GROQ_API_KEY
2. Start the Django server
3. Navigate to /agronomist/
4. Ask: "What crops should I plant this season?"
5. Verify AI response appears

## Troubleshooting
- Ensure API key is correctly set
- Check network connectivity
- Verify Groq service status
- Review Django logs for errors