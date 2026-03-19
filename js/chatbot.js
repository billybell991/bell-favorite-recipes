/* ==========================================================
   Chef Bella — Food-Only AI Chatbot Widget
   Runs on every page. Requires ai-features.js to be loaded first.
   ========================================================== */
(function () {
  'use strict';

  var SYSTEM_PROMPT =
    'You are Chef Bella, the warm and friendly cooking guide for the Bell Family Recipe website. ' +
    'You were created to help the Bell family — and anyone visiting the site — discover the joy of cooking.\n\n' +
    'YOUR PERSONALITY:\n' +
    '- Warm, enthusiastic, and encouraging — like a knowledgeable family friend\n' +
    '- Genuinely passionate about ingredients, techniques, and flavor\n' +
    '- Patient with beginners, excited to go deep for experienced cooks\n' +
    '- Occasionally charming and playful — you love food puns\n\n' +
    'WHAT YOU HELP WITH:\n' +
    '- Recipe ideas and suggestions (especially Bell family favorites)\n' +
    '- Cooking techniques, temperatures, timing\n' +
    '- Ingredient substitutions and swaps\n' +
    '- Meal planning and what to make with given ingredients\n' +
    '- Food storage, safety, and shelf life\n' +
    '- Baking science, flavor pairings, seasoning tips\n' +
    '- Understanding unfamiliar ingredients or cuisines\n' +
    '- General kitchen advice and troubleshooting\n\n' +
    'THE BELL FAMILY COLLECTION includes: Air Fryer recipes, Instant Pot recipes, Keto recipes, ' +
    'Mom\'s Cookbook, Family Recipes, Wedding Favorites, Friends & Neighbors recipes, Internet Finds, and more.\n\n' +
    'RECIPE RECOMMENDATION RULES (very important):\n' +
    '- When recommending recipes, mention them BY NAME only — just the recipe title, a one-sentence tease, and encouragement to click it. Do NOT write out ingredients or steps.\n' +
    '- Each message may include a [Recipes in our collection...] note with exact titles. ALWAYS use those EXACT titles word-for-word — the site turns them into clickable links automatically.\n' +
    '- If no recipe list is provided, keep recommendations vague ("we have some great chicken dishes!") rather than inventing specific titles.\n' +
    '- Only write out a full recipe if the user explicitly asks for one AND no matching recipe was listed in the context.\n\n' +
    'STRICT RULES:\n' +
    '- You ONLY discuss food-related topics. This is absolute.\n' +
    '- If asked about anything non-food-related (politics, news, sports, relationships, tech, etc.), ' +
    'respond warmly but firmly: "Ha! I\'m Chef Bella — food is my entire world! I can\'t help with that one, ' +
    'but if you\'re hungry or curious about cooking, I\'m your girl! 🍳"\n' +
    '- Keep responses concise and conversational — aim for 2-4 short paragraphs max.\n' +
    '- Never identify yourself as an AI, a language model, or mention Google/Gemini.';

  var MAX_HISTORY = 20; // messages kept in context
  var history = []; // {role, parts: [{text}]}

  /* ── Resolve Chef Bella image URL ── */
  function bellaImgSrc() {
    var base = '/';
    var cssLink = document.querySelector('link[href*="css/style.css"]');
    if (cssLink) {
      var m = cssLink.getAttribute('href').match(/(\/[^?#]*\/)css\/style\.css/);
      if (m) base = m[1];
    }
    return base + 'images/chef-bella.png';
  }

  function bellaAvatar(cls) {
    return '<img src="' + bellaImgSrc() + '" alt="Chef Bella" class="' + cls + '" onerror="this.outerHTML=\'👩\u200d🍳\'">';
  }

  /* ── Build the widget DOM ── */
  function buildWidget() {
    // Toggle button
    var toggle = document.createElement('button');
    toggle.className = 'chatbot-toggle';
    toggle.setAttribute('aria-label', 'Chat with Chef Bella');
    toggle.innerHTML =
      '<div class="chatbot-bubble"><img src="" class="bella-toggle-img" alt="Chef Bella" onerror="this.style.display=\'none\'"></div>' +
      '<span class="chatbot-toggle-label">Chef Bella</span>';
    // Set src after insert so bellaImgSrc() can read the DOM
    setTimeout(function() {
      var img = toggle.querySelector('.bella-toggle-img');
      if (img) img.src = bellaImgSrc();
    }, 0);

    // Chat panel
    var panel = document.createElement('div');
    panel.className = 'chatbot-panel';
    panel.setAttribute('aria-live', 'polite');
    panel.innerHTML =
      '<div class="chatbot-header">' +
        '<div class="chatbot-avatar"><img class="bella-header-img" src="" alt="Chef Bella" onerror="this.style.display=\'none\'"></div>' +
        '<div class="chatbot-header-info">' +
          '<div class="chatbot-header-name">Chef Bella</div>' +
          '<div class="chatbot-header-status"><span class="chatbot-status-dot"></span> Your food guide</div>' +
        '</div>' +
        '<button class="chatbot-header-close" aria-label="Close chat">✕</button>' +
      '</div>' +
      '<div class="chatbot-messages" id="chatbot-messages"></div>' +
      '<div class="chatbot-typing" id="chatbot-typing">' +
        '<div class="typing-avatar"><img class="bella-typing-img" src="" alt="Chef Bella" onerror="this.style.display=\'none\'"></div>' +
        '<div class="typing-dots"><span></span><span></span><span></span></div>' +
      '</div>' +
      '<div class="chatbot-input-area">' +
        '<textarea class="chatbot-input" id="chatbot-input" placeholder="Ask me anything food-related!" rows="1" aria-label="Message Chef Bella"></textarea>' +
        '<button class="chatbot-send" id="chatbot-send" aria-label="Send message">' +
          '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>' +
        '</button>' +
      '</div>' +
      '<div class="chatbot-footer">' +
        '<span class="chatbot-footer-hint">🍴 Food questions only</span>' +
      '</div>';

    document.body.appendChild(toggle);
    document.body.appendChild(panel);

    // Set image srcs now that elements are in the DOM
    var bellaSrc = bellaImgSrc();
    ['.bella-header-img', '.bella-typing-img'].forEach(function (sel) {
      var el = panel.querySelector(sel);
      if (el) el.src = bellaSrc;
    });

    return { toggle: toggle, panel: panel };
  }

  /* ── Recipe index for linkification ── */
  var recipeIndex = null;

  function loadRecipeIndex() {
    if (recipeIndex !== null) return;
    recipeIndex = [];
    var base = '/';
    var cssLink = document.querySelector('link[href*="css/style.css"]');
    if (cssLink) {
      var m = cssLink.getAttribute('href').match(/(\/[^?#]*\/)css\/style\.css/);
      if (m) base = m[1];
    }
    fetch(base + 'index.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        recipeIndex = data
          .filter(function (item) {
            return item.title && item.permalink && item.permalink.indexOf('/recipes/') !== -1;
          })
          .sort(function (a, b) { return b.title.length - a.title.length; });
      })
      .catch(function () { recipeIndex = []; });
  }

  function linkifyRecipes(text) {
    if (!recipeIndex || !recipeIndex.length) return text;
    var base = '/';
    var cssLink = document.querySelector('link[href*="css/style.css"]');
    if (cssLink) {
      var m = cssLink.getAttribute('href').match(/(\/[^?#]*\/)css\/style\.css/);
      if (m) base = m[1];
    }
    var used = {};
    recipeIndex.forEach(function (recipe) {
      var title = recipe.title;
      if (title.length < 6) return;
      if (used[title.toLowerCase()]) return;
      var url = recipe.permalink.match(/^https?:\/\//)
        ? recipe.permalink
        : base.replace(/\/$/, '') + recipe.permalink;
      var escaped = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      // Match titles not already inside a markdown link bracket
      var re = new RegExp('(?<!\\[)(' + escaped + ')(?!\\])', 'gi');
      if (re.test(text)) {
        re.lastIndex = 0;
        text = text.replace(re, '[' + title + '](' + url + ')');
        used[title.toLowerCase()] = true;
      }
    });
    return text;
  }

  /* ── Message rendering ── */
  function appendMessage(role, text) {
    var messages = document.getElementById('chatbot-messages');
    if (!messages) return;

    var div = document.createElement('div');
    div.className = 'chat-message ' + role;

    var avatarHtml = role === 'bot'
      ? '<div class="chat-message-avatar"><img src="' + bellaImgSrc() + '" alt="Chef Bella" onerror="this.outerHTML=\'👩‍🍳\'"></div>'
      : '<div class="chat-message-avatar">🧑</div>';

    var bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    // Render the text safely using BellAI's markdown renderer
    if (window.BellAI) {
      var processed = (role === 'bot') ? linkifyRecipes(text) : text;
      bubble.innerHTML = window.BellAI.renderMarkdown(processed);
      // Style any recipe links Bella inserted
      bubble.querySelectorAll('a[href*="/recipes/"]').forEach(function (a) {
        a.classList.add('bella-recipe-link');
      });
    } else {
      bubble.textContent = text;
    }

    if (role === 'bot') {
      div.innerHTML = avatarHtml;
      div.appendChild(bubble);
    } else {
      div.appendChild(bubble);
      div.innerHTML += avatarHtml;
    }

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function setTyping(visible) {
    var el = document.getElementById('chatbot-typing');
    if (el) {
      el.classList.toggle('visible', visible);
      var messages = document.getElementById('chatbot-messages');
      if (messages) messages.scrollTop = messages.scrollHeight;
    }
  }

  /* ── Find recipes relevant to user's message ── */
  function findRelevantRecipes(userText) {
    if (!recipeIndex || !recipeIndex.length) return [];
    var stopWords = {'what':1,'with':1,'have':1,'that':1,'this':1,'from':1,'your':1,'make':1,'some':1,'good':1,'best':1,'like':1,'need':1,'want':1,'give':1,'find':1,'show':1,'tell':1,'help':1,'about':1,'just':1,'also':1,'more':1};
    var words = userText.toLowerCase()
      .replace(/[^a-z0-9 ]/g, ' ').split(/\s+/)
      .filter(function(w) { return w.length > 3 && !stopWords[w]; });
    if (!words.length) return [];
    return recipeIndex
      .map(function(r) {
        var title = r.title.toLowerCase();
        var score = words.reduce(function(s, w) { return s + (title.indexOf(w) !== -1 ? 1 : 0); }, 0);
        return { recipe: r, score: score };
      })
      .filter(function(r) { return r.score > 0; })
      .sort(function(a, b) { return b.score - a.score; })
      .slice(0, 10)
      .map(function(r) { return r.recipe; });
  }

  /* ── Send a message ── */
  function sendMessage(text) {
    if (!text.trim()) return;

    var input  = document.getElementById('chatbot-input');
    var sendBtn = document.getElementById('chatbot-send');
    if (input) { input.value = ''; input.style.height = 'auto'; }
    if (sendBtn) sendBtn.disabled = true;

    appendMessage('user', text);

    history.push({ role: 'user', parts: [{ text: text }] });
    if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);

    setTyping(true);

    if (!window.BellAI) {
      setTyping(false);
      appendMessage('bot', 'Oops! Something went wrong. Please refresh the page and try again.');
      if (sendBtn) sendBtn.disabled = false;
      return;
    }

    window.BellAI.requireApiKey(function () {
      // Build API messages — inject matching recipe titles so Bella uses exact names
      var apiMessages = history.slice();
      var relevant = findRelevantRecipes(text);
      if (relevant.length) {
        var titleList = relevant.map(function(r) { return '"' + r.title + '"'; }).join(', ');
        var last = apiMessages[apiMessages.length - 1];
        apiMessages[apiMessages.length - 1] = {
          role: 'user',
          parts: [{ text: last.parts[0].text + '\n\n[Recipes in our collection relevant to this — use these EXACT titles when recommending: ' + titleList + ']' }]
        };
      }
      window.BellAI.callGemini(apiMessages, SYSTEM_PROMPT)
        .then(function (reply) {
          history.push({ role: 'model', parts: [{ text: reply }] });
          if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
          setTyping(false);
          appendMessage('bot', reply);
        })
        .catch(function (err) {
          setTyping(false);
          var errMsg = err.message || 'Something went wrong.';
          if (errMsg.indexOf('API_KEY_INVALID') !== -1 || errMsg.indexOf('401') !== -1 ||
              errMsg.indexOf('API_KEY_HTTP_REFERRER_BLOCKED') !== -1 ||
              errMsg.indexOf('leaked') !== -1 || errMsg.indexOf('reported') !== -1) {
            errMsg = 'Chef Bella is having trouble connecting. Please try again or contact the site owner.';
          }
          appendMessage('bot', '⚠️ ' + errMsg);
        })
        .finally(function () {
          if (sendBtn) sendBtn.disabled = false;
        });
    });
  }

  /* ── Auto-resize textarea ── */
  function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
  }

  /* ── Greeting ── */
  function showGreeting() {
    var greetings = [
      'Hey there! 👋 I\'m Chef Bella, your personal food guide. Got ingredients you want to use up? Need a recipe idea? Ask away — I live for this stuff! 🍳',
      'Hi! I\'m Chef Bella 🍴 Ask me about recipes, cooking tips, ingredient swaps — anything food! That\'s literally my whole world.',
      'Welcome! I\'m Chef Bella 👩‍🍳 Whether you need a quick dinner idea or want to know why your cake sank, I\'m here to help!'
    ];
    var msg = greetings[Math.floor(Math.random() * greetings.length)];
    setTimeout(function () {
      appendMessage('bot', msg);
    }, 300);
  }

  /* ── Wire up the widget ── */
  function init() {
    var els = buildWidget();
    var toggle = els.toggle;
    var panel  = els.panel;
    var isOpen = false;
    var greeted = false;

    // Pre-load recipe index so first response can linkify immediately
    loadRecipeIndex();

    function openChat() {
      isOpen = true;
      panel.classList.add('open');
      toggle.classList.add('chatbot-open');
      var bubble = toggle.querySelector('.chatbot-bubble');
      if (bubble) bubble.innerHTML = '✕';
      toggle.setAttribute('aria-label', 'Close Chef Bella');

      if (!greeted) {
        greeted = true;
        showGreeting();
      }

      // Check if API key is set and show notice if not
      updateKeyWarning();

      var input = document.getElementById('chatbot-input');
      if (input) setTimeout(function () { input.focus(); }, 100);
    }

    function closeChat() {
      isOpen = false;
      panel.classList.remove('open');
      toggle.classList.remove('chatbot-open');
      var bubble = toggle.querySelector('.chatbot-bubble');
      if (bubble) {
        var bubbleImg = '<img src="' + bellaImgSrc() + '" class="bella-toggle-img" alt="Chef Bella" onerror="this.style.display=\'none\'">';
        bubble.innerHTML = bubbleImg;
      }
      toggle.setAttribute('aria-label', 'Chat with Chef Bella');
    }

    function updateKeyWarning() {
      var existing = panel.querySelector('.chatbot-key-warning');
      if (existing) existing.remove();

      if (!window.BellAI || window.BellAI.getApiKey()) return;

      var warning = document.createElement('div');
      warning.className = 'chatbot-key-warning';
      warning.innerHTML =
        '⚠️ No API key set. <a id="chatbot-key-setup">Set up Gemini key</a> to start chatting.';

      // Insert before input area
      var inputArea = panel.querySelector('.chatbot-input-area');
      if (inputArea) panel.insertBefore(warning, inputArea);

      var setupLink = document.getElementById('chatbot-key-setup');
      if (setupLink) {
        setupLink.addEventListener('click', function () {
          window.BellAI.showApiKeyModal(function () {
            warning.remove();
          });
        });
      }
    }

    // Toggle button — stopPropagation prevents the document click handler
    // from firing on the same event and immediately closing what we just opened
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (isOpen) closeChat(); else openChat();
    });

    // Close button inside panel
    var closeBtn = panel.querySelector('.chatbot-header-close');
    if (closeBtn) closeBtn.addEventListener('click', closeChat);

    // Send button
    var sendBtn = document.getElementById('chatbot-send');
    if (sendBtn) {
      sendBtn.addEventListener('click', function () {
        var input = document.getElementById('chatbot-input');
        if (input) sendMessage(input.value.trim());
      });
    }

    // Enter to send (Shift+Enter for newline)
    var inputEl = document.getElementById('chatbot-input');
    if (inputEl) {
      inputEl.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage(inputEl.value.trim());
        }
      });
      inputEl.addEventListener('input', function () {
        autoResize(inputEl);
      });
    }

    // Close panel if user clicks outside it (but not on the toggle)
    document.addEventListener('click', function (e) {
      if (isOpen && !panel.contains(e.target) && !toggle.contains(e.target)) {
        closeChat();
      }
    });
  }

  // Initialize after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

}());
