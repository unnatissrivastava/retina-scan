import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from retina_logic import analyze_retina

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        analysis = analyze_retina(filepath)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

    result_text = (
        f"{analysis['result']}\n"
        f"Confidence: {analysis['confidence']}%\n\n"
        f"{analysis['explanation']}"
    )

    return jsonify({
        "result": result_text,
        "raw_result": analysis["result"],
        "confidence": analysis["confidence"],
        "explanation": analysis["explanation"],
        "details": analysis["details"],
    })


if __name__ == "__main__":
    app.run(debug=True)