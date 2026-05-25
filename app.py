import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are MediAssist, a professional AI-powered medical triage assistant. 
Your role is to help patients understand their symptoms and determine the urgency of care needed.

IMPORTANT GUIDELINES:
- Always remind users you are an AI and cannot replace professional medical advice
- For life-threatening symptoms (chest pain, difficulty breathing, stroke signs), ALWAYS recommend calling emergency services (911)
- Provide clear urgency levels: EMERGENCY, URGENT, MODERATE, or SELF-CARE
- Suggest possible conditions based on symptoms (not a diagnosis)
- Recommend appropriate care pathways (ER, urgent care, primary care, telehealth, home care)
- Ask clarifying questions when needed
- Be empathetic, clear, and professional

Respond ONLY in this JSON format:
{
  "urgency": "EMERGENCY|URGENT|MODERATE|SELF-CARE",
  "urgency_color": "red|orange|yellow|green",
  "summary": "Brief assessment summary (1-2 sentences)",
  "possible_conditions": ["condition1", "condition2", "condition3"],
  "recommended_action": "What they should do right now",
  "care_pathway": "ER|Urgent Care|Primary Care|Telehealth|Home Care",
  "follow_up_questions": ["question1", "question2"],
  "disclaimer": "Standard medical disclaimer",
  "next_steps": ["step1", "step2", "step3"]
}"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/triage", methods=["POST"])
def triage():
    data = request.get_json()
    symptoms = data.get("symptoms", "")
    age = data.get("age", "")
    gender = data.get("gender", "")
    duration = data.get("duration", "")
    medical_history = data.get("medical_history", "")
    conversation_history = data.get("conversation_history", [])

    if not symptoms:
        return jsonify({"error": "Please describe your symptoms"}), 400

    user_message = f"""
Patient Information:
- Age: {age or 'Not provided'}
- Gender: {gender or 'Not provided'}  
- Symptoms: {symptoms}
- Duration: {duration or 'Not specified'}
- Medical History: {medical_history or 'None provided'}

Please assess these symptoms and provide triage guidance.
"""

    messages = conversation_history + [{"role": "user", "content": user_message}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        
        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        result = json.loads(raw)
        return jsonify(result)

    except json.JSONDecodeError as e:
        return jsonify({"error": "Failed to parse AI response", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/followup", methods=["POST"])
def followup():
    data = request.get_json()
    message = data.get("message", "")
    conversation_history = data.get("conversation_history", [])

    if not message:
        return jsonify({"error": "Message is required"}), 400

    messages = conversation_history + [{"role": "user", "content": message}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=messages
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "MediAssist AI"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
