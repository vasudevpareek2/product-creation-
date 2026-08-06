# Product Creation Web App

Full-stack web application for automating Thrillophilia product creation workflow with AI-powered content generation.

## Quick Start

### Get a Free AI API Key (Recommended)
1. Visit https://console.groq.com/keys
2. Sign up for free (no credit card required)
3. Create an API key
4. Add to `backend/.env`: `GROQ_API_KEY=your_key_here`

### Start the Application
```bash
# Start backend
cd backend
python main.py

# Start frontend (in new terminal)
cd frontend-new
npm run dev
```

Access the app at http://localhost:3000

## Features Overview

- **Automated Product Creation**: 3-stage workflow (create → enrich → finalize)
- **AI-Powered Content**: Generate descriptions, names, and SEO metadata (free with Groq)
- **Token Capture**: Automated browser-based token extraction
- **Real-time Monitoring**: Track batch progress and logs
- **Configuration Management**: Partner-specific settings and policies

## Architecture

- **Backend**: FastAPI (Python) - wraps existing product creation scripts
- **Frontend**: Next.js 14 (React + TypeScript + Tailwind CSS)
- **AI Integration**: Claude API or Groq API (Free) for content generation
- **File Processing**: CSV/Excel upload and processing

## Project Structure

```
product-creation-webapp/
├── backend/                    # FastAPI backend
│   ├── main.py                # Main application
│   ├── config.py              # Configuration management
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   ├── routes/                # API endpoints
│   │   ├── batch.py          # Batch management
│   │   ├── config.py         # Configuration endpoints
│   │   ├── ai.py             # Claude AI integration
│   │   └── upload.py         # File upload handling
│   ├── services/              # Business logic
│   │   ├── script_executor.py # Script execution wrapper
│   │   └── claude_service.py  # Claude API client
│   ├── models/                # Pydantic models
│   └── wrappers/              # Script wrappers (existing scripts)
├── frontend-new/              # Next.js frontend
│   ├── src/
│   │   ├── app/              # Next.js app directory
│   │   │   ├── page.tsx      # Home page
│   │   │   ├── dashboard/    # Batch management
│   │   │   ├── new-batch/    # Batch creation
│   │   │   ├── config/       # Configuration management
│   │   │   ├── ai-assistant/ # AI content generation
│   │   │   └── batch/[id]/  # Batch details
│   │   └── lib/
│   │       └── api.ts        # API client
│   └── package.json
├── config/                    # Configuration files
├── uploads/                   # Uploaded files
└── logs/                      # Execution logs
```

## Setup Instructions

### Quick Start (Free AI with Groq)

1. **Get a free Groq API key**: Visit https://console.groq.com/keys (no credit card required)
2. **Add to backend/.env**: `GROQ_API_KEY=your_key_here`
3. **Start both servers**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   python main.py
   
   # Terminal 2 - Frontend  
   cd frontend-new
   npm run dev
   ```
4. **Access the app**: http://localhost:3000

### Detailed Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   # If you have Visual Studio Build Tools (for pandas compilation):
   pip install -r requirements.txt
   
   # If you don't have build tools, install pre-built wheels:
   pip install fastapi uvicorn[standard] python-multipart pydantic pydantic-settings anthropic openpyxl python-dotenv websockets aiofiles playwright
   pip install pandas
   
   # Install Playwright browsers
   playwright install chromium
   ```

3. **Configure environment variables:**
   Edit `.env` file with your settings:
   ```env
   THRILLO_BASE_URL=https://admin.thrillophilia.com
   THRILLO_CLIENT_ID=1
   THRILLO_ACCESS_TOKEN=your_access_token_here
   
   # Choose one AI provider (Groq is free, Claude is paid)
   GROQ_API_KEY=your_groq_api_key_here  # Get free key at https://console.groq.com/keys
   ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional - if you have Claude access
   ```

4. **Start the backend server:**
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend-new
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   Create `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the frontend server:**
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:3000`

## Features

### 1. Dashboard
- View all product creation batches
- Monitor batch status and progress
- Access batch details and logs

### 2. Batch Creation
- Upload CSV/Excel source files
- Configure batch settings
- Create and manage batches

### 3. Configuration Management
- Partner-specific configurations
- Vendor management
- Policy settings
- Business terms configuration
- Access token management

### 4. AI Assistant (Claude or Groq Integration)
- Generate product descriptions
- Create variant names
- Generate SEO metadata
- Suggest product structures
- **Groq API (Free)**: Uses Llama 3.1 models with generous free tier
- **Claude API (Paid)**: Optional alternative for higher quality output
- **Automatic Fallback**: System automatically uses configured API (prefers Claude, falls back to Groq)

#### Getting a Free Groq API Key

1. Visit https://console.groq.com/keys
2. Sign up for a free account (no credit card required)
3. Create a new API key
4. Copy the key and add it to your `.env` file:
   ```env
   GROQ_API_KEY=gsk_your_api_key_here
   ```
5. The system will automatically use Groq when Claude is not configured

#### Testing AI Integration

Run the test script to verify your AI setup:
```bash
cd backend
python test_groq.py
```

This will test product description generation, variant naming, and SEO content creation.

### 5. Token Capture (Browser Automation)
- **Interactive Token Capture**: Opens browser window for automatic token extraction
- **Playwright Integration**: Uses Chromium to capture Access-Tokens from network requests
- **Token Validation**: Check if tokens are still valid
- **Token Status**: Monitor token age and validity

### 6. Workflow Execution
- 3-stage product creation pipeline
- Dry-run mode for testing
- Real-time log streaming
- Error handling and recovery

## API Endpoints

### Batch Management
- `POST /api/batch` - Create new batch
- `GET /api/batch` - List all batches
- `GET /api/batch/{id}` - Get batch details
- `POST /api/batch/{id}/execute` - Execute workflow stage
- `DELETE /api/batch/{id}` - Delete batch

### Configuration
- `GET /api/config/{partner_id}` - Get partner config
- `POST /api/config/{partner_id}` - Save partner config
- `GET /api/config` - List all configs

### File Upload
- `POST /api/upload/csv` - Upload CSV file
- `POST /api/upload/excel` - Upload Excel file
- `POST /api/upload/config` - Upload config file
- `POST /api/upload/token` - Upload access token
- `GET /api/upload/files` - List uploaded files

### AI Services
- `POST /api/ai/generate-content` - Generate AI content
- `POST /api/ai/suggest-product` - Suggest product structure
- `GET /api/ai/status` - Check AI availability

### Token Capture
- `POST /api/token/capture-interactive` - Start interactive browser-based token capture
- `POST /api/token/capture-from-storage` - Capture token from existing session data
- `POST /api/token/validate` - Validate if a token is still valid
- `GET /api/token/status` - Check current token file status

## Workflow Stages

### Stage 1: Create Products & Variants
- Reads `products_from_sheet.csv`
- Creates products via Thrillophilia API
- Creates variants for new and existing products
- Generates `results_log.csv`

### Stage 2: Enrich Products
- Reads `enrichment_plan.json`
- Renames products and variants
- Adds region tags
- Sets visibility scopes
- Generates `enrichment_results_log.csv`

### Stage 3: Finalize Products
- Applies booking settings
- Attaches policies
- Tags vendors
- Sets pricing
- Activates products and variants
- Shares with reseller
- Generates `finalize_results_log.csv`

## Security Notes

- Access tokens are stored in `config/access_token.txt`
- Never commit access tokens to version control
- Claude API key and Groq API key should be kept secure
- Use environment variables for sensitive data
- Groq API keys are free but should still be protected

## Troubleshooting

### Backend Issues
- Check that all Python dependencies are installed
- Verify `.env` file is configured correctly
- Ensure scripts directory contains the Python scripts
- Check logs in the `logs/` directory

### Frontend Issues
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check that backend is running on the configured port
- Clear browser cache if experiencing issues
- Check browser console for errors

### Script Execution Issues
- Verify CSV file format matches expected structure
- Check that access token is valid and not expired
- Ensure configuration file is properly set up
- Review script logs for detailed error messages

## Development

### Adding New Features
1. Add new endpoints in `backend/routes/`
2. Create corresponding frontend components
3. Update API client in `frontend/src/lib/api.ts`
4. Test with dry-run mode first

### AI Provider Configuration

The system supports multiple AI providers with automatic fallback:

1. **Claude API (Anthropic)**: Higher quality, paid service
   - Set `ANTHROPIC_API_KEY` in `.env`
   - Best for production use with consistent quality requirements

2. **Groq API (Free)**: Fast, generous free tier
   - Set `GROQ_API_KEY` in `.env`
   - Uses Llama 3.1 models
   - Perfect for development and small-scale production
   - Get free key at https://console.groq.com/keys

3. **No AI**: System works without AI
   - Users can manually enter all content
   - Core automation functionality still works

The system automatically selects the best available provider:
- If Claude API key is configured → uses Claude
- If only Groq API key is configured → uses Groq
- If neither is configured → AI features disabled (system still works)

### Database Integration
Currently uses in-memory storage for batches. For production:
1. Replace in-memory storage with a real database
2. Add database models in `backend/models/`
3. Update repository pattern for data access
4. Add database migrations

## License

This project integrates with existing Thrillophilia product creation scripts.