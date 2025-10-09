# OpenHeavy

A multi-agent AI chat application, simulation of grok heavy.

## Example of working

<img width="953" height="616" alt="{2844B5D9-00C8-4472-B35C-BC108F305B11}" src="https://github.com/user-attachments/assets/4e0788b7-6101-4d7b-b65e-fe5d7af7b917" /> 
(1 agents working, 1 agent finish work)

<img width="1030" height="586" alt="{FC2EE2E0-55DB-4FFD-BE41-3308038E6113}" src="https://github.com/user-attachments/assets/31b2de07-71ac-4efd-b3b5-860cf3886648" /> 
(final response



## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager
- Access to OpenAI-compatible API (NVIDIA API configured by default)
- SearXNG search service running on `localhost:8888` (for web search functionality)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   git clone https://github.com/valerka1292/OpenHeavy.git
   cd OpenHeavy
   ```


2. **Install dependencies:**
   ```bash
   make install
   # or manually:
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```
   
   **Required settings in .env:**
   ```bash
   # LLM API Configuration
   BASE_URL=https://integrate.api.nvidia.com/v1
   MODEL=qwen/qwen3-235b-a22b
   
   # Required API Keys
   API_KEY=your_actual_api_key_here
   FLASK_SECRET_KEY=your_secret_key_here
   ```
   
   **Optional settings:**
   ```bash
   # Search API (for web search functionality)
   SEARCH_API_URL=http://localhost:8888/search
   
   # Flask settings
   FLASK_PORT=5000
   FLASK_DEBUG=false
   
   # Logging
   LOG_LEVEL=INFO
   LOG_FORMAT=json
   ```

4. **Run the application:**
   ```bash
   make run
   # or manually:
   python src/main.py
   ```

5. **Open your browser:**
   Navigate to `http://localhost:5000`
