"""
app.py
======
Flask application entry point.

Route groups:
  - Pages:        /, /settings, /chat
  - Dashboard API: /api/dashboard/*  (stats, charts, activity, notifications)
  - AI API:        /api/ai/*         (chat, playground, streaming)
  - Prompts API:   /api/prompts/*    (CRUD for saved/favorite prompts)
  - Settings API:  /api/settings

Run with:
    python app.py
or:
    flask --app app run --debug
"""

from __future__ import annotations

import logging

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from ai_service import AIServiceError, ChatMessage, ai_service
from analytics import analytics_engine
from config import config
from dashboard_service import dashboard_service

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_dashboard")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = config.secret_key

for warning in config.validate():
    logger.warning(warning)


@app.context_processor
def inject_globals() -> dict:
    """Values available to every Jinja template."""
    return {
        "app_name": config.app_name,
        "currency_symbol": config.currency_symbol,
        "ai_configured": ai_service.is_configured,
        "available_models": ai_service.available_models(),
    }


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_error):
    return render_template("dashboard.html", error_message="Page not found."), 404


@app.errorhandler(500)
def server_error(error):
    logger.exception("Unhandled server error: %s", error)
    return jsonify({"error": "Internal server error. Check the server logs for details."}), 500


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    settings = dashboard_service.get_settings()
    summary = analytics_engine.summary()
    notifications = dashboard_service.list_notifications()[:6]
    activity = analytics_engine.recent_activity(limit=8)
    return render_template(
        "dashboard.html",
        settings=settings,
        summary=summary,
        notifications=notifications,
        unread_count=dashboard_service.unread_count(),
        activity=activity,
        active_page="dashboard",
    )


@app.route("/settings")
def settings_page():
    settings = dashboard_service.get_settings()
    notifications = dashboard_service.list_notifications()[:6]
    return render_template(
        "settings.html",
        settings=settings,
        notifications=notifications,
        unread_count=dashboard_service.unread_count(),
        active_page="settings",
    )


@app.route("/chat")
def chat_page():
    settings = dashboard_service.get_settings()
    prompts = dashboard_service.list_prompts()
    notifications = dashboard_service.list_notifications()[:6]
    return render_template(
        "chat.html",
        settings=settings,
        prompts=prompts,
        notifications=notifications,
        unread_count=dashboard_service.unread_count(),
        active_page="chat",
    )


# ---------------------------------------------------------------------------
# Dashboard API
# ---------------------------------------------------------------------------
@app.route("/api/dashboard/summary")
def api_dashboard_summary():
    return jsonify(analytics_engine.summary())


@app.route("/api/dashboard/charts/requests")
def api_chart_requests():
    days = request.args.get("days", default=14, type=int)
    return jsonify(analytics_engine.requests_over_time(days=days))


@app.route("/api/dashboard/charts/tokens")
def api_chart_tokens():
    days = request.args.get("days", default=14, type=int)
    return jsonify(analytics_engine.token_usage_over_time(days=days))


@app.route("/api/dashboard/charts/costs")
def api_chart_costs():
    days = request.args.get("days", default=14, type=int)
    return jsonify(analytics_engine.cost_over_time(days=days))


@app.route("/api/dashboard/charts/response-times")
def api_chart_response_times():
    days = request.args.get("days", default=14, type=int)
    return jsonify(analytics_engine.response_times(days=days))


@app.route("/api/dashboard/charts/categories")
def api_chart_categories():
    return jsonify(analytics_engine.prompt_categories())


@app.route("/api/dashboard/activity")
def api_dashboard_activity():
    limit = request.args.get("limit", default=10, type=int)
    return jsonify(analytics_engine.recent_activity(limit=limit))


@app.route("/api/dashboard/most-used-prompts")
def api_most_used_prompts():
    limit = request.args.get("limit", default=5, type=int)
    return jsonify(analytics_engine.most_used_prompts(limit=limit))


@app.route("/api/dashboard/notifications")
def api_list_notifications():
    return jsonify(dashboard_service.list_notifications())


@app.route("/api/dashboard/notifications/<notification_id>/read", methods=["POST"])
def api_read_notification(notification_id: str):
    ok = dashboard_service.mark_notification_read(notification_id)
    return jsonify({"success": ok})


@app.route("/api/dashboard/notifications/read-all", methods=["POST"])
def api_read_all_notifications():
    dashboard_service.mark_all_read()
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# AI API
# ---------------------------------------------------------------------------
def _parse_history(payload: dict) -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    system_prompt = payload.get("system_prompt")
    if system_prompt:
        messages.append(ChatMessage(role="system", content=system_prompt))
    for item in payload.get("history", []):
        role = item.get("role")
        content = item.get("content", "")
        if role in {"user", "assistant"} and content:
            messages.append(ChatMessage(role=role, content=content))
    user_message = payload.get("message")
    if user_message:
        messages.append(ChatMessage(role="user", content=user_message))
    return messages


@app.route("/api/ai/chat", methods=["POST"])
def api_ai_chat():
    if not ai_service.is_configured:
        return jsonify({"error": "OPENAI_API_KEY is not configured on the server."}), 400

    payload = request.get_json(force=True) or {}
    messages = _parse_history(payload)
    if not messages:
        return jsonify({"error": "No message provided."}), 400

    try:
        result = ai_service.complete(
            messages=messages,
            model=payload.get("model"),
            temperature=payload.get("temperature"),
            category="chat",
        )
    except AIServiceError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(
        {
            "text": result.text,
            "model": result.model,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.prompt_tokens + result.completion_tokens,
            "response_time_ms": result.response_time_ms,
        }
    )


@app.route("/api/ai/chat/stream", methods=["POST"])
def api_ai_chat_stream():
    if not ai_service.is_configured:
        return jsonify({"error": "OPENAI_API_KEY is not configured on the server."}), 400

    payload = request.get_json(force=True) or {}
    messages = _parse_history(payload)
    if not messages:
        return jsonify({"error": "No message provided."}), 400

    generator = ai_service.stream(
        messages=messages,
        model=payload.get("model"),
        temperature=payload.get("temperature"),
        category="chat",
    )
    return Response(
        stream_with_context(generator),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/ai/playground", methods=["POST"])
def api_ai_playground():
    if not ai_service.is_configured:
        return jsonify({"error": "OPENAI_API_KEY is not configured on the server."}), 400

    payload = request.get_json(force=True) or {}
    prompt = payload.get("prompt", "")
    if not prompt.strip():
        return jsonify({"error": "Prompt is required."}), 400

    messages = []
    system_prompt = payload.get("system_prompt")
    if system_prompt:
        messages.append(ChatMessage(role="system", content=system_prompt))
    messages.append(ChatMessage(role="user", content=prompt))

    try:
        result = ai_service.complete(
            messages=messages,
            model=payload.get("model"),
            temperature=payload.get("temperature"),
            category="playground",
            json_mode=bool(payload.get("json_mode")),
        )
    except AIServiceError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(
        {
            "text": result.text,
            "model": result.model,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.prompt_tokens + result.completion_tokens,
            "response_time_ms": result.response_time_ms,
        }
    )


@app.route("/api/ai/models")
def api_ai_models():
    return jsonify({"models": ai_service.available_models(), "configured": ai_service.is_configured})


# ---------------------------------------------------------------------------
# Prompts API
# ---------------------------------------------------------------------------
@app.route("/api/prompts", methods=["GET"])
def api_list_prompts():
    return jsonify(dashboard_service.list_prompts())


@app.route("/api/prompts", methods=["POST"])
def api_create_prompt():
    payload = request.get_json(force=True) or {}
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    if not title or not content:
        return jsonify({"error": "Both title and content are required."}), 400
    prompt = dashboard_service.create_prompt(
        title=title,
        content=content,
        category=payload.get("category", "general"),
        favorite=bool(payload.get("favorite", False)),
    )
    return jsonify(prompt), 201


@app.route("/api/prompts/<prompt_id>", methods=["PATCH"])
def api_update_prompt(prompt_id: str):
    payload = request.get_json(force=True) or {}
    prompt = dashboard_service.update_prompt(prompt_id, **payload)
    if not prompt:
        return jsonify({"error": "Prompt not found."}), 404
    return jsonify(prompt)


@app.route("/api/prompts/<prompt_id>/favorite", methods=["POST"])
def api_toggle_favorite(prompt_id: str):
    prompt = dashboard_service.toggle_favorite(prompt_id)
    if not prompt:
        return jsonify({"error": "Prompt not found."}), 404
    return jsonify(prompt)


@app.route("/api/prompts/<prompt_id>", methods=["DELETE"])
def api_delete_prompt(prompt_id: str):
    ok = dashboard_service.delete_prompt(prompt_id)
    if not ok:
        return jsonify({"error": "Prompt not found."}), 404
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Settings API
# ---------------------------------------------------------------------------
@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify(dashboard_service.get_settings())


@app.route("/api/settings", methods=["POST"])
def api_update_settings():
    payload = request.get_json(force=True) or {}
    settings = dashboard_service.update_settings(**payload)
    return jsonify(settings)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting %s on http://%s:%s", config.app_name, config.host, config.port)
    app.run(host=config.host, port=config.port, debug=config.debug)
