import uvicorn
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Run the FastAPI app
    # host="0.0.0.0" allows access from outside the container/local machine if needed
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
