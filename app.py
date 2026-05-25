import os 
import json 
import logging 
from flask import Flask, request, jsonify, render_template 
from flask_cors import CORS 
from google import genai 
from google.genai import types

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__)  

app = Flask(__name__) 
CORS(app)  

# ✅ FIXED: Using your exact env var name "Gemini API Key"
API_KEY = os.environ.get("Gemini API Key")
if not API_KEY:
    raise ValueError("Gemini API Key environment variable not set. Get one at https://aistudio.google.com/api-keys")

client = genai.Client(api_key=API_KEY)  

SYSTEM_PROMPT = """You are MediAssist, a professional AI-powered medical triage assistant. Your role is to help patients understand their symptoms and determine urgency. You do not diagnose. You do not prescribe.

Respond ONLY in valid JSON with these exact keys:
{
  "urgency": "EMERGENCY|URGENT|MODERATE|SELF-CARE",
  "urgency_color": "red|orange|yellow|green", 
  "summary": "1-2 sentence plain language summary",
  "possible_conditions": ["list of 1-3 broad possibilities, not diagnoses"],
  "recommended_action": "What the patient should do now",
  "care_pathway": "ER|Urgent care|GP appointment|Pharmacy|Home care",
  "follow_up_questions": ["2-3 questions to clarify"],
  "disclaimer": "This is not medical advice.",
  "next_steps": ["Concrete steps user can take"]
}"""

BASE_DISCLAIMER = "MediAssist is not a substitute for professional medical advice, diagnosis, or treatment. For emergencies in South Africa call 10177 or 112."

def safe_json_parse(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(f"Gemini returned non-JSON: {raw[:200]}")
        raise ValueError("AI returned invalid format")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/triage", methods=["POST"])
def triage():
    try:
        data = request.get_json(force=True)
        symptoms = data.get("symptoms", "").strip()
        
        if not symptoms:
            return jsonify({"error": "Please describe symptoms"}), 400
        if len(symptoms) > 2000:
            return jsonify({"error": "Symptom description too long. Max 2000 characters."}), 400

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Patient reports: {symptoms}",
            config=config
        )
        
        result = safe_json_parse(response.text)
        result["disclaimer"] = BASE_DISCLAIMER
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Triage error: {type(e).__name__}: {e}")
        return jsonify({"error": "Unable to process triage request. Please try again."}), 500

@app.route("/api/followup", methods=["POST"])
def followup():
    try:
        data = request.get_json(force=True)
        message = data.get("message", "").strip()
        symptoms = data.get("original_symptoms", "")
        history = data.get("history", [])
        
        if not message:
            return jsonify({"error": "Message required"}), 400

        contents = [types.Content(role="user", parts=[types.Part.from_text(f"Initial symptoms: {symptoms}")])]
        for turn in history:
            contents.append(types.Content(role=turn["role"], parts=[types.Part.from_text(turn["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(message)]))
        
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config
        )
        
        result = safe_json_parse(response.text)
        result["disclaimer"] = BASE_DISCLAIMER
        return jsonify(result)

    except Exception as e:
        logger.error(f"Followup error: {type(e).__name__}: {e}")
        return jsonify({"error": "Unable to process followup."}), 500

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "MediAssist AI",
        "gemini_key_set": bool(API_KEY)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
