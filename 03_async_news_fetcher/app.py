"""
Async News Fetcher — Flask UI
==============================
Run:
    pip install flask aiohttp
    python app.py
Open: http://127.0.0.1:5002
"""

from flask import Flask, render_template, request
from fetcher import SOURCES, run_fetch

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    results   = []
    benchmark = {}
    error     = None
    fetched   = False
    selected  = []

    if request.method == "POST":
        selected = request.form.getlist("sources")
        if not selected:
            selected = list(SOURCES.keys())

        sources_to_fetch = {k: v for k, v in SOURCES.items() if k in selected}

        try:
            results, _, benchmark = run_fetch(sources_to_fetch)
            fetched = True
        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        sources=list(SOURCES.keys()),
        results=results,
        benchmark=benchmark,
        error=error,
        fetched=fetched,
        selected=selected,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
