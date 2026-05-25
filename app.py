import os
import json
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
CORS(app)

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    logger.error("ANTHROPIC_API_KEY is not set!")

client = anthropic.Anthropic(api_key=api_key)

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

Respond ONLY in this JSON format with no markdown fences, no preamble, just raw JSON:
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


def parse_ai_json(raw):
    """Robustly parse JSON from AI response, stripping fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # drop first line (```json or ```) and last line (```)
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(raw.strip())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/triage", methods=["POST"])
def triage():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        symptoms = data.get("symptoms", "").strip()
        if not symptoms:
            return jsonify({"error": "Please describe your symptoms"}), 400

        age = data.get("age", "")
        gender = data.get("gender", "")
        duration = data.get("duration", "")
        medical_history = data.get("medical_history", "")
        conversation_history = data.get("conversation_history", [])

        user_message = f"""Patient Information:
- Age: {age or 'Not provided'}
- Gender: {gender or 'Not provided'}
- Symptoms: {symptoms}
- Duration: {duration or 'Not specified'}
- Medical History: {medical_history or 'None provided'}

Please assess these symptoms and provide triage guidance."""

        messages = conversation_history[-18:] + [{"role": "user", "content": user_message}]

        logger.info(f"Triage request: symptoms='{symptoms[:60]}...'")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=messages
        )

        raw = response.content[0].text
        logger.info(f"Raw AI response (first 200): {raw[:200]}")

        result = parse_ai_json(raw)
        return jsonify(result)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} | raw: {raw[:300]}")
        return jsonify({"error": "AI returned unexpected format. Please try again."}), 500

    except anthropic.AuthenticationError:
        logger.error("Invalid ANTHROPIC_API_KEY")
        return jsonify({"error": "Authentication failed. Check your API key in Render environment variables."}), 401

    except anthropic.RateLimitError:
        logger.error("Rate limit hit")
        return jsonify({"error": "Rate limit reached. Please wait a moment and try again."}), 429

    except anthropic.APIStatusError as e:
        logger.error(f"Anthropic API error: {e.status_code} - {e.message}")
        return jsonify({"error": f"AI service error: {e.message}"}), 502

    except Exception as e:
        logger.exception(f"Unexpected error in /api/triage: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/followup", methods=["POST"])
def followup():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "Message is required"}), 400

        conversation_history = data.get("conversation_history", [])
        messages = conversation_history[-18:] + [{"role": "user", "content": message}]

        logger.info(f"Followup request: '{message[:60]}'")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=messages
        )

        raw = response.content[0].text
        result = parse_ai_json(raw)
        return jsonify(result)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in followup: {e}")
        return jsonify({"error": "AI returned unexpected format. Please try again."}), 500

    except Exception as e:
        logger.exception(f"Unexpected error in /api/followup: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/health")
def health():
    key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return jsonify({
        "status": "ok",
        "service": "MediAssist AI",
        "api_key_set": key_set
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
