'use strict';

const express = require('express');
const path    = require('path');

const app  = express();
const PORT = process.env.PORT || 3000;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models';

app.use(express.json({ limit: '10mb' }));

// ── Render → Railway redirect ─────────────────────────────────────────────────
const RAILWAY_URL = 'https://bell-favorite-recipes.up.railway.app';
app.use((req, res, next) => {
  if (req.hostname === 'bell-favorite-recipes.onrender.com') {
    return res.send(`<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bell Favorite Recipes has moved!</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{min-height:100vh;display:flex;align-items:center;justify-content:center;
    font-family:'Segoe UI',system-ui,sans-serif;background:#faf7f4;color:#3b2f2f}
  .card{text-align:center;padding:3rem 2rem;max-width:480px;
    background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.1)}
  h1{font-size:1.6rem;margin-bottom:.75rem}
  p{font-size:1.05rem;color:#6b5b5b;margin-bottom:1.5rem;line-height:1.5}
  a.btn{display:inline-block;padding:.85rem 2rem;background:#a0522d;color:#fff;
    border-radius:50px;text-decoration:none;font-weight:600;font-size:1.05rem;
    transition:background .2s}
  a.btn:hover{background:#7a3e22}
  .emoji{font-size:2.5rem;margin-bottom:1rem}
</style></head><body>
<div class="card">
  <div class="emoji">&#127869;</div>
  <h1>We&rsquo;ve Moved!</h1>
  <p>Bell Favorite Recipes has a new home. Update your bookmarks!</p>
  <a class="btn" href="${RAILWAY_URL}">Go to the new site &rarr;</a>
</div></body></html>`);
  }
  next();
});

// ── Gemini proxy ──────────────────────────────────────────────────────────────
// POST /api/gemini?model=MODEL_NAME
// Forwards the request body to Google's Gemini API, injecting the server-side key.
// model defaults to 'gemini-2.5-flash' for text; pass 'gemini-3.1-flash-image-preview'
// (or any other supported model) for image generation.
app.post('/api/gemini', async (req, res) => {
  if (!GEMINI_API_KEY) {
    return res.status(500).json({
      error: { message: 'Gemini API key is not configured on the server. Contact the site owner.' }
    });
  }

  const model = (req.query.model || 'gemini-2.5-flash').replace(/[^a-zA-Z0-9._-]/g, '');
  const url   = `${GEMINI_BASE}/${model}:generateContent?key=${GEMINI_API_KEY}`;

  try {
    const upstream = await fetch(url, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(req.body)
    });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(502).json({ error: { message: 'Proxy error: ' + err.message } });
  }
});

// ── Static Hugo site ──────────────────────────────────────────────────────────
app.use(express.static(path.join(__dirname, 'public')));

// Hugo 404 page fallback
app.use((req, res) => {
  const p = path.join(__dirname, 'public', '404.html');
  res.status(404).sendFile(p, (err) => {
    if (err) res.status(404).send('Page not found');
  });
});

app.listen(PORT, () => console.log(`Bell Recipes server on port ${PORT}`));
