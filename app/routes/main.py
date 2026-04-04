from flask import Blueprint, request, jsonify, redirect, abort

from app.models.short_link import ShortLink

main_bp = Blueprint("main", __name__)


def _serialize_link(link, base_url=None):
    """Helper to serialize a ShortLink model to a dictionary."""
    data = {
        "short_code": link.short_code,
        "original_url": link.original_url,
        "click_count": getattr(link, "click_count", 0),  # defaults to 0 for newly created links
        "created_at": link.created_at.isoformat() if link.created_at else None,
    }
    if base_url:
        data["short_url"] = f"{base_url}/{link.short_code}"
    return data


@main_bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@main_bp.route("/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or {}
    original_url = data.get("url") or request.form.get("url", "")
    if isinstance(original_url, str):
        original_url = original_url.strip()

    if not original_url:
        return jsonify({"error": "url is required"}), 400

    # Basic URL normalisation
    if not original_url.startswith(("http://", "https://")):
        original_url = "https://" + original_url

    try:
        link = ShortLink.create_link(original_url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    base_url = request.host_url.rstrip("/")
    return jsonify(_serialize_link(link, base_url)), 201


@main_bp.route("/<short_code>")
def redirect_url(short_code):
    link = ShortLink.get_by_code(short_code)
    if not link:
        abort(404)
    link.increment_clicks()
    return redirect(link.original_url, code=302)


@main_bp.route("/stats/<short_code>")
def stats(short_code):
    link = ShortLink.get_by_code(short_code)
    if not link:
        return jsonify({"error": "not found"}), 404

    return jsonify(_serialize_link(link))


@main_bp.route("/links")
def list_links():
    links = ShortLink.select().order_by(ShortLink.created_at.desc()).limit(50)
    base_url = request.host_url.rstrip("/")
    return jsonify([_serialize_link(l, base_url) for l in links])
