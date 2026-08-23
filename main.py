import os
import base64
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.6-flash')

class CommandRequest(BaseModel):
    text: str
    image_base64: str = None

@app.post("/api/command")
async def handle_command(req: CommandRequest):
    try:
        prompt = req.text
        
        if req.image_base64:
            try:
                from PIL import Image
                image_data = base64.b64decode(req.image_base64)
                image = Image.open(io.BytesIO(image_data))
                response = model.generate_content([prompt, image])
            except Exception as img_err:
                print(f"Vision processing error: {str(img_err)}")
                response = model.generate_content(prompt)
        else:
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
    import random
    return {
        "cpu": random.randint(20, 60),
        "ram": random.randint(40, 75)
    }
