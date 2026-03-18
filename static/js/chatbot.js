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
    'STRICT RULES:\n' +
    '- You ONLY discuss food-related topics. This is absolute.\n' +
    '- If asked about anything non-food-related (politics, news, sports, relationships, tech, etc.), ' +
    'respond warmly but firmly: "Ha! I\'m Chef Bella — food is my entire world! I can\'t help with that one, ' +
    'but if you\'re hungry or curious about cooking, I\'m your girl! 🍳"\n' +
    '- Keep responses concise and conversational — aim for 2-4 short paragraphs max unless a recipe is requested.\n' +
    '- Format ingredient lists and steps with simple markdown (* for bullets, 1. for numbered steps).\n' +
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
      bubble.innerHTML = window.BellAI.renderMarkdown(text);
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
      window.BellAI.callGemini(history, SYSTEM_PROMPT)
        .then(function (reply) {
          history.push({ role: 'model', parts: [{ text: reply }] });
          if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
          setTyping(false);
          appendMessage('bot', reply);
        })
        .catch(function (err) {
          setTyping(false);
          var errMsg = err.message || 'Something went wrong.';
          if (errMsg.indexOf('API_KEY_INVALID') !== -1 || errMsg.indexOf('401') !== -1) {
            errMsg = 'Your API key seems invalid. Click ⚙️ API key below to update it.';
            window.BellAI.clearApiKey();
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
