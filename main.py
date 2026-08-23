import os
import base64
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import google.generativeai as genai

app = FastAPI()

# Enable CORS so your Electron/React frontend can talk to this backend smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini with the API key from environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize the Gemini 3.6-flash model as required
model = genai.GenerativeModel('gemini-3.6-flash')

class CommandRequest(BaseModel):
    text: str
    image_base64: str = None  # Optional field for screen snapshots/vision analysis

@app.post("/api/command")
async def handle_command(req: CommandRequest):
    try:
        prompt = req.text
        
        # Check if an image snapshot was sent for Screen Vision analysis
        if req.image_base64:
            # Decode the base64 image string back into a PIL Image
            image_data = base64.b64decode(req.image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Send both text prompt and image to Gemini Vision
            response = model.generate_content([prompt, image])
        else:
            # Standard text-only generation
            response = model.generate_content(prompt)
            
        return {
            "message": response.text.upper(),
            "audio": None
        }
        
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    # Simulated or real telemetry data for CPU/RAM
    import random
    return {
        "cpu": random.randint(20, 60),
        "ram": random.randint(40, 75)
    }
