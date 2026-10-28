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

        <!-- Notification Banner -->
        <div id="notice-banner" class="hidden bg-amber-500/10 border border-amber-500/30 text-amber-300 px-6 py-4 rounded-2xl mb-6 text-sm font-medium"></div>

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
                <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Target Community:</label>
                <div class="flex gap-3">
                    <label class="flex items-center gap-2 bg-slate-950 border border-cyan-500 p-2.5 rounded-xl cursor-pointer">
                        <input type="checkbox" name="sub" value="3Drequests" checked class="accent-cyan-500">
                        <span class="text-xs font-medium text-cyan-400">r/3Drequests (Core Gig Market)</span>
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
            const noticeBanner = document.getElementById('notice-banner');
            const keywords = document.getElementById('keywords').value;
            const budgetFilter = document.getElementById('budget-filter').value;
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