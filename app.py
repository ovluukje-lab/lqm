# LQM Advertentie Agent - Flask API en web-UI

from flask import Flask, request, jsonify, render_template, send_from_directory
import os

from extractor import extract_from_url
from lqm_scorer import (
    ExtractedData,
    score_all,
    total_lqm_score,
    summary_by_category,
    LQMScoreItem,
)

app = Flask(__name__, static_folder="static", template_folder="static")


@app.after_request
def add_cors(response):
    """Sta aanroepen vanaf andere domeinen toe (voor frontend op eigen hosting, API hier)."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def analyze():
    """Accepteert JSON: { "url": "https://..." } en retourneert LQM-rapport."""
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "Geen URL opgegeven."}), 400

    extracted, err = extract_from_url(url)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    items = score_all(extracted)
    total = total_lqm_score(items)
    by_category = summary_by_category(items)

    # Serialiseer voor JSON
    def item_to_dict(i: LQMScoreItem) -> dict:
        return {
            "attribute": i.attribute,
            "category": i.category,
            "score": i.score,
            "type": i.type_,
            "reason": i.reason,
            "not_applicable": i.not_applicable,
        }

    return jsonify({
        "ok": True,
        "url": url,
        "total_lqm_score": total,
        "items": [item_to_dict(i) for i in items],
        "by_category": {
            cat: {
                "bonus": info["bonus"],
                "malus": info["malus"],
                "items": [item_to_dict(i) for i in info["items"]],
            }
            for cat, info in by_category.items()
        },
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
