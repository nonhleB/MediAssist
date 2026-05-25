import os
import json
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ✅ Gemini client (ONLY ONCE)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are MediAssist, a professional AI-powered medical triage assistant.
Your role is to help patients understand their symptoms and determine urgency.

Respond ONLY in valid JSON:
{
  "urgency": "EMERGENCY|URGENT|MODERATE|SELF-CARE",
  "urgency_color": "red|orange|yellow|green",
  "summary": "",
  "possible_conditions": [],
  "recommended_action": "",
  "care_pathway": "",
  "follow_up_questions": [],
  "disclaimer": "",
  "next_steps": []
}
"""

def parse_ai_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])
    return json.loads(raw)


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

        user_message = f"Symptoms: {symptoms}"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_message
        )

        raw = response.text
        result = parse_ai_json(raw)

        return jsonify(result)

    except Exception as e:
        logger.exception(e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/followup", methods=["POST"])
def followup():
    try:
        data = request.get_json(force=True)
        message = data.get("message", "")

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message
        )

        raw = response.text
        result = parse_ai_json(raw)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "MediAssist AI",
        "gemini_key_set": bool(os.environ.get("GEMINI_API_KEY"))
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
