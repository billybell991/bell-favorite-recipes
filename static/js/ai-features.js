/* ============================================================
   Bell Recipes — Shared AI Utilities & Favorites Management
   Exposes window.BellAI for use by all feature scripts
   ============================================================ */
(function (window) {
  'use strict';

  var GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';
  var STORAGE_KEY_API  = 'gemini_api_key';
  var STORAGE_KEY_FAVS = 'recipe_favorites';
  var STORAGE_KEY_BOOK = 'recipe_book_generated';

  // Built-in key — family members never need to configure anything
  var DEFAULT_API_KEY = 'AIzaSyBcj5c0VAb6vh_qXFeIn4FQYfbvJ8247BA';

  /* ── helpers ── */
  function escHtml(str) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(String(str)));
    return d.innerHTML;
  }

  /** Detect the site base URL by inspecting the stylesheet link tag */
  function getBaseUrl() {
    var baseUrl = '/';
    var cssLink = document.querySelector('link[href*="css/style.css"]');
    if (cssLink) {
      var href = cssLink.getAttribute('href');
      var match = href.match(/(\/[^?#]*\/)css\/style\.css/);
      if (match) baseUrl = match[1];
    }
    return baseUrl;
  }

  /* ── Gemini API key management ── */
  function getApiKey()      { return localStorage.getItem(STORAGE_KEY_API) || DEFAULT_API_KEY; }
  function setApiKey(key)   { localStorage.setItem(STORAGE_KEY_API, key.trim()); }
  function clearApiKey()    { localStorage.removeItem(STORAGE_KEY_API); }

  function showApiKeyModal(onSuccess, onCancel) {
    // Key is pre-configured — just call success immediately
    if (onSuccess) onSuccess(getApiKey());
  }

  function requireApiKey(onSuccess) {
    onSuccess(getApiKey());
  }

  /* ── Gemini text generation ── */
  function callGemini(messages, systemPrompt) {
    var key = getApiKey();
    if (!key) return Promise.reject(new Error('No API key configured.'));

    var body = {
      contents: messages,
      generationConfig: { temperature: 0.75, maxOutputTokens: 2048 }
    };
    if (systemPrompt) {
      body.systemInstruction = { parts: [{ text: systemPrompt }] };
    }

    return fetch(GEMINI_ENDPOINT + '?key=' + encodeURIComponent(key), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          var msg = (data.error && data.error.message) || ('API error ' + res.status);
          throw new Error(msg);
        }
        try {
          return data.candidates[0].content.parts[0].text;
        } catch (e) {
          throw new Error('Unexpected response format from Gemini.');
        }
      });
    });
  }

  /* ── Simple markdown → HTML renderer (safe subset) ── */
  function renderMarkdown(md) {
    if (!md) return '';
    var lines = md.split('\n');
    var html = '';
    var inUl = false, inOl = false;

    function closeLists() {
      if (inUl) { html += '</ul>'; inUl = false; }
      if (inOl) { html += '</ol>'; inOl = false; }
    }

    function inlineFormat(text) {
      // 1. Extract markdown links FIRST, replace with placeholders
      var links = [];
      text = text.replace(/\[([^\]]+)\]\(((?:https?:\/\/|\/)[^)]+)\)/g, function (_, label, url) {
        var idx = links.length;
        links.push('<a href="' + url + '" class="bella-recipe-link">' + label + '</a>');
        return '\x00LINK' + idx + '\x00';
      });
      // 2. Escape HTML in the remaining text
      text = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      // 3. Apply bold/italic
      text = text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>');
      // 4. Restore links
      text = text.replace(/\x00LINK(\d+)\x00/g, function (_, i) { return links[+i]; });
      return text;
    }

    lines.forEach(function (line) {
      if (/^#{1,2}\s/.test(line)) {
        closeLists();
        html += '<h2>' + inlineFormat(line.replace(/^#{1,2}\s+/, '')) + '</h2>';
      } else if (/^#{3,}\s/.test(line)) {
        closeLists();
        html += '<h3>' + inlineFormat(line.replace(/^#{3,}\s+/, '')) + '</h3>';
      } else if (/^\d+\.\s/.test(line)) {
        if (!inOl) { closeLists(); html += '<ol>'; inOl = true; }
        html += '<li>' + inlineFormat(line.replace(/^\d+\.\s+/, '')) + '</li>';
      } else if (/^[-*]\s/.test(line)) {
        if (!inUl) { closeLists(); html += '<ul>'; inUl = true; }
        html += '<li>' + inlineFormat(line.replace(/^[-*]\s+/, '')) + '</li>';
      } else if (line.trim() === '') {
        closeLists();
        html += '<br>';
      } else {
        closeLists();
        html += '<p>' + inlineFormat(line) + '</p>';
      }
    });
    closeLists();
    return html;
  }

  /* ── Favorites management ── */
  function getFavorites() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY_FAVS)) || []; }
    catch (e) { return []; }
  }
  function isFavorite(permalink) {
    return getFavorites().some(function (r) { return r.permalink === permalink; });
  }
  function addFavorite(recipe) {
    var favs = getFavorites();
    if (!favs.some(function (r) { return r.permalink === recipe.permalink; })) {
      favs.unshift(recipe);
      localStorage.setItem(STORAGE_KEY_FAVS, JSON.stringify(favs));
    }
  }
  function removeFavorite(permalink) {
    var favs = getFavorites().filter(function (r) { return r.permalink !== permalink; });
    localStorage.setItem(STORAGE_KEY_FAVS, JSON.stringify(favs));
  }
  function toggleFavorite(recipe) {
    if (isFavorite(recipe.permalink)) {
      removeFavorite(recipe.permalink);
      return false;
    }
    addFavorite(recipe);
    return true;
  }

  /* ── Generated recipe book management ── */
  function getGeneratedRecipes() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY_BOOK)) || []; }
    catch (e) { return []; }
  }
  function saveGeneratedRecipe(recipe) {
    var recipes = getGeneratedRecipes();
    recipes.unshift(recipe);
    if (recipes.length > 50) recipes = recipes.slice(0, 50);
    localStorage.setItem(STORAGE_KEY_BOOK, JSON.stringify(recipes));
  }
  function removeGeneratedRecipe(id) {
    var recipes = getGeneratedRecipes().filter(function (r) { return r.id !== id; });
    localStorage.setItem(STORAGE_KEY_BOOK, JSON.stringify(recipes));
  }

  /* ── Public API ── */
  window.BellAI = {
    getBaseUrl: getBaseUrl,
    escHtml: escHtml,
    renderMarkdown: renderMarkdown,
    getApiKey: getApiKey,
    setApiKey: setApiKey,
    clearApiKey: clearApiKey,
    showApiKeyModal: showApiKeyModal,
    requireApiKey: requireApiKey,
    callGemini: callGemini,
    getFavorites: getFavorites,
    isFavorite: isFavorite,
    addFavorite: addFavorite,
    removeFavorite: removeFavorite,
    toggleFavorite: toggleFavorite,
    getGeneratedRecipes: getGeneratedRecipes,
    saveGeneratedRecipe: saveGeneratedRecipe,
    removeGeneratedRecipe: removeGeneratedRecipe
  };

}(window));
