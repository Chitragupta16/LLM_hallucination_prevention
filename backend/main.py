from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os
import logging
from typing import Optional, List, Dict
import uuid
from fact_extract import fact_extractor 
from refdatabase import wikipedia_verifier
from confidence_scorer import confidence_scorer
from contradiction_detector import contradiction_detector
from response_formatter import response_formatter


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="LLM Hallucination Prevention API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-latest')  

# In-memory conversation storage
conversations = {}

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    extracted_facts: List[Dict] = []  
    confidence_report: Dict = {} 
    contradictions: List[Dict] = []
    formatted_response: Dict={}
    
# Health check endpoint
@app.get("/")
async def root():
    return {"status": "LLM Proxy is running", "model": "gemini-1.5-flash"}

# Main chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Session {session_id}: Received message: {request.message}")
        
        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        # Add user message to history
        conversations[session_id].append({
            "role": "user",
            "parts": [request.message]
        })
        
        # Create chat with history
        chat = model.start_chat(history=conversations[session_id][:-1])
        
        # Send message and get response
        response = chat.send_message(request.message)
        response_text = response.text
        
        # Add assistant response to history
        conversations[session_id].append({
            "role": "model",
            "parts": [response_text]
        })
        
        # Extract facts from response
        extracted_facts = fact_extractor.extract_facts(response_text)
        logger.info(f"Session {session_id}: Extracted {len(extracted_facts)} facts")
        
        # Verify facts against Wikipedia
        verified_facts = wikipedia_verifier.verify_facts(extracted_facts)
        logger.info(f"Session {session_id}: Verified {len(verified_facts)} facts")
        
        # *** NEW: Check for contradictions with previous messages ***
        contradictions = contradiction_detector.detect_contradictions(session_id, verified_facts)
        if contradictions:
            logger.warning(f"Session {session_id}: ⚠️  Found {len(contradictions)} contradiction(s)!")
        
        # Add facts to session history (for future contradiction checks)
        contradiction_detector.add_facts(session_id, verified_facts)
        
        # Calculate confidence score
        confidence_report = confidence_scorer.score_response(verified_facts)
        
        # *** NEW: Adjust confidence if contradictions found ***
        if contradictions:
            # Lower confidence if contradictions exist
            confidence_report['overall_confidence'] = 'low'
            confidence_report['color'] = 'red'
            confidence_report['emoji'] = '🔴'
            confidence_report['summary'] = f"⚠️  {len(contradictions)} contradiction(s) detected in conversation"
        
        formatted_response = response_formatter.format_response(response_text, verified_facts,contradictions)
        
        logger.info(f"Session {session_id}: {confidence_report['emoji']} Overall confidence: {confidence_report['overall_confidence']} ({confidence_report['confidence_score']})")
        
        logger.info(f"Session {session_id}: Response generated successfully")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            extracted_facts=verified_facts,
            confidence_report=confidence_report,
            contradictions=contradictions,  
            formatted_response=formatted_response
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get conversation history
@app.get("/history/{session_id}")
async def get_history(session_id: str):
    if session_id not in conversations:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "history": conversations[session_id]}

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation and fact history for a session"""
    if session_id in conversations:
        del conversations[session_id]
    contradiction_detector.clear_session(session_id)
    return {"message": f"Session {session_id} cleared"}