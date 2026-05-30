from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from engine import bp as engine_bp

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = (BASE_DIR / ".." / ".." / "dist" / "app").resolve()

app = Flask(__name__, static_folder=str(DIST_DIR), static_url_path="")
app.register_blueprint(engine_bp)

try:
    from flask_cors import CORS

    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:4200"]}})
except Exception:
    # CORS is optional when serving the built Angular app from Flask.
    pass


@app.get("/api/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.get("/api/config")
def config() -> tuple[dict[str, str | bool], int]:
    return {
        "angular_dist": str(DIST_DIR),
        "dist_exists": DIST_DIR.exists(),
    }, 200


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if not DIST_DIR.exists():
        return (
            jsonify(
                error="Angular build not found.",
                hint="Run `npm run build` in the app/ folder.",
            ),
            404,
        )

    file_path = DIST_DIR / path
    if path and file_path.is_file():
        return send_from_directory(DIST_DIR, path)

    return send_from_directory(DIST_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
