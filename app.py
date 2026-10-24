import json
from datetime import datetime, timezone
import os
import xml.etree.ElementTree as ET
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

        <!-- Notification Banner for Fallbacks -->
        <div id="notice-banner" class="hidden bg-amber-500/10 border border-amber-500/30 text-amber-300 px-6 py-4 rounded-2xl mb-6 text-sm font-medium"></div>

        <!-- Controls: Filters, Time Windows, Results Limit & 15 Subreddits -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl mb-8 flex flex-col gap-6 shadow-xl">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <!-- Keyword Filter -->
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Smart AI Keyword Filter</label>
                    <input type="text" id="keywords" placeholder="e.g. dragon, gear, helmet" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                </div>
                <!-- Budget Filter -->
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Monetization Filter</label>
                    <select id="budget-filter" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                        <option value="all">Show All Requests</option>
                        <option value="paid">Paid / Tipping Only ($ / Commission)</option>
                    </select>
                </div>
                <!-- Time Window Filter -->
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Time Window Filter</label>
                    <select id="time-filter" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                        <option value="today">Today (Last 24 Hours)</option>
                        <option value="3days" selected>Last 3 Days</option>
                        <option value="week">Last Week</option>
                        <option value="month">Last Month</option>
                        <option value="all">Anytime</option>
                    </select>
                </div>
                <!-- Results Limit Filter -->
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Results Limit</label>
                    <select id="limit-filter" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                        <option value="25" selected>25 Items</option>
                        <option value="50">50 Items</option>
                        <option value="100">100 Items</option>
                    </select>
                </div>
            </div>

            <!-- Subreddit Checkboxes -->
            <div>
                <div class="flex justify-between items-center mb-3">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400">Select Subreddits to Scan (15 Communities):</label>
                    <button type="button" onclick="toggleAll(true)" class="text-xs text-cyan-400 hover:underline">Select All</button>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-5 gap-3" id="sub-checkboxes"></div>
            </div>
        </div>

        <!-- Loading Indicator -->
        <div id="loading" class="hidden text-center py-16">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-cyan-500 border-t-transparent mb-4"></div>
            <p class="text-slate-400 font-medium animate-pulse">Scanning live communities & running semantic AI analysis...</p>
        </div>

        <!-- Results Grid -->
        <div id="results-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="col-span-full text-center py-16 border-2 border-dashed border-slate-800 rounded-2xl">
                <p class="text-slate-500 text-lg">Select your filters and click "Scan Live Markets" above!</p>
            </div>
        </div>
    </div>

    <script>
        const subredditsList = [
            "3Drequests", "3Dprinting", "functionalprint", "3Dmodeling", "cosplayprops",
            "TabletopMiniatures", "BambuLab", "FixMyPrint", "CAD", "Solidworks",
            "Blender", "resinprinting", "PrintedMinis", "3Dprintingdeals", "AdditiveManufacturing"
        ];

        const container = document.getElementById('sub-checkboxes');
        subredditsList.forEach(sub => {
            container.innerHTML += `
                <label class="flex items-center gap-2 bg-slate-950 border border-slate-800 p-2.5 rounded-xl cursor-pointer hover:border-cyan-500/50 transition">
                    <input type="checkbox" name="sub" value="${sub}" checked class="accent-cyan-500">
                    <span class="text-xs font-medium text-slate-300 truncate">r/${sub}</span>
                </label>
            `;
        });

        function toggleAll(status) {
            document.querySelectorAll('input[name="sub"]').forEach(cb => cb.checked = status);
        }

        async function fetchLiveDemand() {
            const btn = document.getElementById('scan-btn');
            const loading = document.getElementById('loading');
            const grid = document.getElementById('results-grid');
            const noticeBanner = document.getElementById('notice-banner');
            const keywords = document.getElementById('keywords').value;
            const budgetFilter = document.getElementById('budget-filter').value;
            const timeFilter = document.getElementById('time-filter').value;
            const limitFilter = document.getElementById('limit-filter').value;

            noticeBanner.classList.add('hidden');
            noticeBanner.innerHTML = '';

            const selectedSubs = [];
            document.querySelectorAll('input[name="sub"]:checked').forEach(cb => selectedSubs.push(cb.value));

            if (selectedSubs.length === 0) {
                alert('Please select at least one subreddit!');
                return;
            }

            btn.disabled = true;
            loading.classList.remove('hidden');
            grid.innerHTML = '';

            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        keywords: keywords, 
                        subreddits: selectedSubs, 
                        budget_filter: budgetFilter,
                        time_filter: timeFilter,
                        limit: limitFilter
                    })
                });

                const data = await response.json();
                loading.classList.add('hidden');
                btn.disabled = false;

                if (data.status === 'success') {
                    if (data.fallback_triggered && keywords) {
                        noticeBanner.classList.remove('hidden');
                        noticeBanner.innerHTML = `⚠️ We couldn't find anything matching exact keyword "<strong>${keywords}</strong>", but here are other top trending requests instead!`;
                    }
                    renderCards(data.items);
                } else {
                    grid.innerHTML = `<div class="col-span-full text-center text-red-400 py-8">Error: ${data.message}</div>`;
                }
            } catch (err) {
                loading.classList.add('hidden');
                btn.disabled = false;
                grid.innerHTML = `<div class="col-span-full text-center text-red-400 py-8">Failed to connect to local server or request timed out. Try lowering the limit to 25 or 50.</div>`;
            }
        }

        function renderCards(items) {
            const grid = document.getElementById('results-grid');
            if (!items || items.length === 0) {
                grid.innerHTML = `<div class="col-span-full text-center text-slate-400 py-8">No requests found matching your filters. Try broadening your criteria!</div>`;
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
    budget_filter = data.get("budget_filter", "all")
    time_filter = data.get("time_filter", "3days")
    max_results = int(data.get("limit", 25))
    subreddits = data.get("subreddits", ["3Drequests", "3Dprinting"])

    now = datetime.now(timezone.utc)
    delta_mapping = {
        "today": 24,
        "3days": 72,
        "week": 168,
        "month": 720,
        "all": 999999,
    }
    delta_hours = delta_mapping.get(time_filter, 72)

    posts_dict = {}
    post_count = 0
    fetch_cap = min(max_results * 2, 120)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
    }

    for sub in subreddits:
        if post_count >= fetch_cap:
            break
        url = f"https://www.reddit.com/r/{sub}/new.rss"
        try:
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)

                for entry in entries:
                    if post_count >= fetch_cap:
                        break

                    updated_elem = entry.find("atom:updated", ns)
                    if updated_ess_elem := updated_elem is not None and updated_elem.text:
                        try:
                            post_time = datetime.fromisoformat(
                                updated_elem.text.replace("Z", "+00:00")
                            )
                            age_hours = (now - post_time).total_seconds() / 3600
                            if age_hours > delta_hours:
                                continue
                        except Exception:
                            pass

                    title = (
                        entry.find("atom:title", ns).text
                        if entry.find("atom:title", ns) is not None
                        else ""
                    )
                    summary_elem = entry.find("atom:summary", ns)
                    body = summary_elem.text if summary_elem is not None else ""
                    link_elem = entry.find("atom:link", ns)
                    link = (
                        link_elem.attrib.get("href", "") if link_elem is not None else ""
                    )
                    author_elem = entry.find("atom:author/atom:name", ns)
                    author = (
                        author_elem.text if author_elem is not None else "Unknown"
                    )

                    posts_dict[title] = {
                        "link": link,
                        "subreddit": f"r/{sub}",
                        "author": author,
                    }
                    post_count += 1
        except Exception as e:
            print(f"Skipping r/{sub}: {e}")

    if not posts_dict:
        return jsonify({"status": "success", "items": []})

    all_posts_text = ""
    for title, info in posts_dict.items():
        all_posts_text += (
            f"Subreddit: {info['subreddit']}\nAuthor:"
            f" {info['author']}\nTitle: {title}\nLink: {info['link']}\n---\n"
        )

    keyword_prompt = (
        f"Focus primarily on requests matching or related to: '{keywords}'."
        if keywords
        else (
            "Extract the most prominent custom modeling or printing requests"
            " found."
        )
    )

    budget_prompt = (
        "ONLY include requests that mention a budget, tip, payment, or commission"
        " ($ or paid)."
        if budget_filter == "paid"
        else "Include all relevant requests regardless of budget."
    )

    try:
        ai_response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=(
                "Analyze these recent live Reddit posts.\n"
                f"{keyword_prompt}\n{budget_prompt}\n\n"
                f"Extract up to {max_results} matching items. Return your response strictly as a JSON array of objects with these exact keys: "
                "'model_requested', 'subreddit', 'author', 'category', 'description', 'budget', 'link'. "
                "CRITICAL: Match the exact 'Link' provided in the raw text for each post so the URL is correct and clickable. "
                "If very few or zero posts match the specific keyword strictly, include the next best trending requests to fill the count. "
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

        for item in parsed_items:
            title_key = item.get("model_requested", "")
            if not item.get("link") or item.get("link") == "#":
                for t, info in posts_dict.items():
                    if any(word in t.lower() for word in title_key.lower().split()[:2]):
                        item["link"] = info["link"]
                        break

        # Check if keyword fallback was likely triggered (if keyword was typed but returned items don't strongly match it)
        fallback_triggered = False
        if keywords:
            keyword_lower = keywords.lower()
            match_found = any(
                keyword_lower in item.get("model_requested", "").lower()
                or keyword_lower in item.get("description", "").lower()
                for item in parsed_items
            )
            if not match_found and len(parsed_items) > 0:
                fallback_triggered = True

        return jsonify({
            "status": "success",
            "items": parsed_items,
            "fallback_triggered": fallback_triggered,
        })
    except Exception as e:
        print(f"AI parsing error: {e}")
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    print("Starting PrintPulse AI Public Beta Server...")
    app.run(debug=True, port=5000)