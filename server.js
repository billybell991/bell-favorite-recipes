'use strict';

const express = require('express');
const path    = require('path');

const app  = express();
const PORT = process.env.PORT || 3000;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models';

app.use(express.json({ limit: '10mb' }));

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
