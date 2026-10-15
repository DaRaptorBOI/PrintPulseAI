import json
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv  # Loads variables from your hidden .env file
from flask import Flask, jsonify, render_template_string, request
from google import genai
import requests

# Load local environment variables securely
load_dotenv()

app = Flask(__name__)

# Safely initialize Gemini using the secure system environment variable
client = genai.Client()

# Professional SaaS Dashboard HTML Template
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
                <a href="#pricing" class="bg-slate-900 border border-slate-800 hover:border-cyan-500 text-slate-300 font-semibold px-4 py-2.5 rounded-xl transition text-sm">Upgrade Pro ($19/mo)</a>
                <button onclick="fetchLiveDemand()" id="scan-btn" class="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-6 py-3 rounded-xl transition shadow-lg shadow-cyan-500/20 flex items-center gap-2">
                    <span>Scan Live Markets</span>
                </button>
            </div>
        </header>

        <!-- Controls: Filters & 15 Subreddits -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl mb-8 flex flex-col gap-6 shadow-xl">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Keyword Filter -->
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Smart AI Keyword / Topic Filter</label>
                    <input type="text" id="keywords" placeholder="e.g. dragon, replacement gear, mechanical parts, helmet" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                </div>
                <!-- Budget Filter -->
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Monetization Filter</label>
                    <select id="budget-filter" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:border-cyan-500">
                        <option value="all">Show All Requests</option>
                        <option value="paid">Paid / Tipping Only ($ / Commission)</option>
                    </select>
                </div>
            </div>

            <!-- Subreddit Checkboxes (15 Total) -->
            <div>
                <div class="flex justify-between items-center mb-3">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400">Select Subreddits to Scan (15 Communities):</label>
                    <button type="button" onclick="toggleAll(true)" class="text-xs text-cyan-400 hover:underline">Select All</button>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-5 gap-3" id="sub-checkboxes">
                    <!-- Injected via HTML/JS -->
                </div>
            </div>
        </div>

        <!-- Loading Indicator -->
        <div id="loading" class="hidden text-center py-16">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-cyan-500 border-t-transparent mb-4"></div>
            <p class="text-slate-400 font-medium animate-pulse">Scanning 15 live communities & running semantic AI filtering...</p>
        </div>

        <!-- Results Grid -->
        <div id="results-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="col-span-full text-center py-16 border-2 border-dashed border-slate-800 rounded-2xl">
                <p class="text-slate-500 text-lg">Select your target subreddits, set your filters, and click "Scan Live Markets" above!</p>
            </div>
        </div>

        <!-- Pricing Section -->
        <section id="pricing" class="mt-20 pt-12 border-t border-slate-800 text-center">
            <h2 class="text-2xl font-bold text-white mb-3">Unlock Unlimited Real-Time Gigs</h2>
            <p class="text-slate-400 text-sm max-w-xl mx-auto mb-8">Get instant desktop alerts the second someone posts a paid 3D design request or custom modeling commission online.</p>
            <div class="inline-block bg-slate-900 border border-cyan-500/30 p-8 rounded-3xl shadow-2xl">
                <div class="text-4xl font-extrabold text-cyan-400 mb-2">$19<span class="text-sm font-normal text-slate-400">/month</span></div>
                <ul class="text-left text-sm text-slate-300 space-y-3 mb-8 mt-6">
                    <li>✓ Scans all 15+ 3D printing & CAD subreddits</li>
                    <li>✓ Advanced AI Budget & Commission Detector</li>
                    <li>✓ Direct Link Click-Throughs to Claim Gigs</li>
                </ul>
                <a href="https://buy.stripe.com/test_placeholder" target="_blank" class="block bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-8 py-3.5 rounded-xl transition shadow-lg shadow-cyan-500/20">Upgrade to Pro Now</a>
            </div>
        </section>
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
            const keywords = document.getElementById('keywords').value;
            const budgetFilter = document.getElementById('budget-filter').value;

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
                    body: JSON.stringify({ keywords: keywords, subreddits: selectedSubs, budget_filter: budgetFilter })
                });

                const data = await response.json();
                loading.classList.add('hidden');
                btn.disabled = false;

                if (data.status === 'success') {
                    renderCards(data.items);
                } else {
                    grid.innerHTML = `<div class="col-span-full text-center text-red-400 py-8">Error: ${data.message}</div>`;
                }
            } catch (err) {
                loading.classList.add('hidden');
                btn.disabled = false;
                grid.innerHTML = `<div class="col-span-full text-center text-red-400 py-8">Failed to connect to local server.</div>`;
            }
        }

        function renderCards(items) {
            const grid = document.getElementById('results-grid');
            if (!items || items.length === 0) {
                grid.innerHTML = `<div class="col-span-full text-center text-slate-400 py-8">No matching requests found. Try broadening your keywords or filters.</div>`;
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
    subreddits = data.get("subreddits", ["3Drequests", "3Dprinting"])

    all_posts_text = ""
    post_count = 0
    max_posts = 25

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
    }

    for sub in subreddits:
        if post_count >= max_posts:
            break
        url = f"https://www.reddit.com/r/{sub}/new.rss"
        try:
            response = requests.get(url, headers=headers, timeout=4)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)

                for entry in entries:
                    if post_count >= max_posts:
                        break
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

                    all_posts_text += f"Subreddit: r/{sub}\nAuthor: {author}\nTitle: {title}\nBody: {body}\nLink: {link}\n---\n"
                    post_count += 1
        except Exception as e:
            print(f"Skipping r/{sub}: {e}")

    if not all_posts_text:
        return jsonify({"status": "success", "items": []})

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
                "Analyze these live Reddit posts from multiple communities.\n"
                f"{keyword_prompt}\n{budget_prompt}\n\n"
                "Extract up to 15 matching items. Return your response strictly as a JSON array of objects with these exact keys: "
                "'model_requested', 'subreddit', 'author', 'category', 'description', 'budget', 'link'. "
                "If none match strictly, return top closest trending requests so the list is never empty. "
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
    print("Starting PrintPulse AI Production Server...")
    print("Open your web browser and go to: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)