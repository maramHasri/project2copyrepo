import os
import uvicorn
from main import app

if __name__ == "__main__":
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Use 0.0.0.0 to accept connections from any IP
    # This is required for cloud deployments like Render
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        workers=1,     # Single worker for Render
        log_level="info"
    ) 