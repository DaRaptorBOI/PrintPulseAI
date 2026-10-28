import json
from datetime import datetime, timezone
import os
import urllib.parse
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request
from google import genai
import requests

load_dotenv()

app = Flask(__name__)
client = genai.Client()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrintPulse AI | Live 3D Demand & Gigs Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- Header -->
        <header class="flex justify-between items-center mb-8 pb-6 border-b border-slate-800">
            <div>
                <h1 class="text-3xl font-extrabold tracking-tight text-cyan-400">PrintPulse <span class="text-white">AI</span></h1>
                <p class="text-slate-400 text-sm mt-1">Live AI-powered 3D printing & modeling demand intelligence engine</p>
            </div>
            <div class="flex items-center gap-3">
                <span class="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-semibold px-4 py-2 rounded-xl text-xs uppercase tracking-wider">Public Beta (Free)</span>
                <button onclick="fetchLiveDemand()" id="scan-btn" class="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-6 py-3 rounded-xl transition shadow-lg shadow-cyan-500/20 flex items-center gap-2">
                    <span>Scan Live Markets</span>
                </button>
            </div>
        </header>

        <!-- Controls -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl mb-8 flex flex-col gap-6 shadow-xl">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Smart AI Keyword Filter</label>
                    <input type="text" id="keywords" placeholder="e.g. dragon, gear, helmet" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Monetization Filter</label>
                    <select id="budget-filter" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                        <option value="all">Show All Requests</option>
                        <option value="paid">Paid / Tipping Only ($ / Commission)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Results Limit</label>
                    <select id="limit-filter" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                        <option value="25" selected>25 Items</option>
                    </select>
                </div>
            </div>

            <div>
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Target Communities:</label>
                <div class="flex gap-3 flex-wrap">
                    <label class="flex items-center gap-2 bg-slate-950 border border-cyan-500 p-2.5 rounded-xl cursor-pointer">
                        <input type="checkbox" name="sub" value="3Drequests" checked class="accent-cyan-500">
                        <span class="text-xs font-medium text-cyan-400">r/3Drequests</span>
                    </label>
                    <label class="flex items-center gap-2 bg-slate-950 border border-slate-800 p-2.5 rounded-xl cursor-pointer hover:border-cyan-500/50">
                        <input type="checkbox" name="sub" value="3Dprinting" checked class="accent-cyan-500">
                        <span class="text-xs font-medium text-slate-300">r/3Dprinting</span>
                    </label>
                </div>
            </div>
        </div>

        <!-- Loading Indicator -->
        <div id="loading" class="hidden text-center py-16">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-cyan-500 border-t-transparent mb-4"></div>
            <p class="text-slate-400 font-medium animate-pulse">Scanning live community demand & processing with Gemini AI...</p>
        </div>

        <!-- Results Grid -->
        <div id="results-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="col-span-full text-center py-16 border-2 border-dashed border-slate-800 rounded-2xl">
                <p class="text-slate-500 text-lg">Click "Scan Live Markets" above to load live requests!</p>
            </div>
        </div>
    </div>

    <script>
        async function fetchLiveDemand() {
            const btn = document.getElementById('scan-btn');
            const loading = document.getElementById('loading');
            const grid = document.getElementById('results-grid');
            const keywords = document.getElementById('keywords').value;
            const budgetFilter = document.getElementById('budget-filter').value;
            const limitFilter = document.getElementById('limit-filter').value;

            const selectedSubs = [];
            document.querySelectorAll('input[name="sub"]:checked').forEach(cb => selectedSubs.push(cb.value));

            if (selectedSubs.length === 0) {
                alert('Please select at least one subreddit!');
                return;
            }

            btn.disabled = true;
            loading.classList.remove('hidden');
            grid.innerHTML = '';

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 20000);

            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        keywords: keywords, 
                        subreddits: selectedSubs, 
                        budget_filter: budgetFilter,
                        limit: limitFilter
                    }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);
                const data = await response.json();
                loading.classList.add('hidden');
                btn.disabled = false;

                if (data.status === 'success') {
                    renderCards(data.items);
                } else {
                    grid.innerHTML = `<div class="col-span-full text-center text-red-400 py-8">Error: ${data.message}</div>`;
                }
            } catch (err) {
                clearTimeout(timeoutId);
                loading.classList.add('hidden');
                btn.disabled = false;
                grid.innerHTML = `<div class="col-span-full text-center text-red-400 py-8">Request timed out. Try again!</div>`;
            }
        }

        function renderCards(items) {
            const grid = document.getElementById('results-grid');
            if (!items || items.length === 0) {
                grid.innerHTML = `<div class="col-span-full text-center text-slate-400 py-8">No requests found. Try clearing keywords!</div>`;
                return;
            }

            grid.innerHTML = '';
            items.forEach(item => {
                const card = document.createElement('div');
                card.className = "bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-cyan-500/50 transition shadow-xl";

                card.innerHTML = `
                    <div>
                        <div class="flex justify-between items-start gap-2 mb-3">
                            <span class="bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold px-3 py-1 rounded-full">${item.category || 'General'}</span>
                            <span class="text-xs text-slate-400 font-medium">${item.subreddit || 'Reddit'}</span>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">${item.model_requested || 'Custom 3D Request'}</h3>
                        <p class="text-slate-300 text-sm mb-4 leading-relaxed">${item.description || ''}</p>
                    </div>
                    <div>
                        <div class="flex justify-between items-center text-xs text-slate-400 border-t border-slate-800 pt-4 mb-4">
                            <span>User: <strong class="text-slate-200">${item.author || 'Anonymous'}</strong></span>
                            <span class="text-emerald-400 font-semibold">${item.budget || 'None'}</span>
                        </div>
                        <a href="${item.link}" target="_blank" class="block w-full text-center bg-slate-800 hover:bg-cyan-500 hover:text-slate-950 text-cyan-400 font-semibold py-2.5 rounded-xl transition text-sm">
                            View Original Post ↗
                        </a>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/scan", methods=["POST"])
def scan_reddit():
    data = request.json or {}
    keywords = data.get("keywords", "").strip()
    max_results = int(data.get("limit", 25))
    subreddits = data.get("subreddits", ["3Drequests", "3Dprinting"])

    posts_dict = {}

    for sub in subreddits:
        target_url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
        proxy_url = f"https://api.allorigins.win/raw?url={urllib.parse.quote(target_url)}"

        try:
            response = requests.get(proxy_url, timeout=10)
            if response.status_code == 200:
                data_json = response.json()
                children = data_json.get("data", {}).get("children", [])

                for child in children:
                    post_data = child.get("data", {})
                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")
                    permalink = post_data.get("permalink", "")
                    link = f"https://www.reddit.com{permalink}" if permalink else ""
                    author = post_data.get("author", "Unknown")

                    body_snippet = selftext[:300] if selftext else ""
                    combined_text = f"{title} - {body_snippet}"

                    if combined_text not in posts_dict:
                        posts_dict[combined_text] = {
                            "link": link,
                            "subreddit": f"r/{sub}",
                            "author": author,
                            "raw_title": title,
                            "raw_desc": body_snippet,
                        }
        except Exception as e:
            print(f"Error fetching r/{sub} via proxy JSON: {e}")

    if not posts_dict:
        return jsonify({"status": "success", "items": []})

    all_posts_text = ""
    for text_key, info in posts_dict.items():
        all_posts_text += (
            f"Subreddit: {info['subreddit']}\nAuthor:"
            f" {info['author']}\nTitle: {info['raw_title']}\nDescription:"
            f" {info['raw_desc']}\nLink: {info['link']}\n---\n"
        )

    keyword_prompt = (
        f"Focus primarily on requests matching: '{keywords}'."
        if keywords
        else (
            "Extract all recent 3D printing topics, questions, and requests found"
            " in the text."
        )
    )

    try:
        ai_response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=(
                "Analyze these live Reddit posts.\n"
                f"{keyword_prompt}\n\n"
                f"Extract up to {max_results} items. Return your response strictly as a JSON array of objects with these exact keys: "
                "'model_requested', 'subreddit', 'author', 'category', 'description', 'budget', 'link'. "
                "CRITICAL: Match the exact 'Link' provided in the raw text for each post so the URL is correct and clickable. "
                "Do not include any markdown formatting or extra text outside the JSON array.\n\n"
                f"{all_posts_text}"
            ),
        )

        clean_text = ai_response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        parsed_items = json.loads(clean_text.strip())
        return jsonify({"status": "success", "items": parsed_items})

    except Exception as e:
        print(f"AI parsing error: {e}")
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    print("Starting PrintPulse AI Server...")
    app.run(debug=True, port=5000)