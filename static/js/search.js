// Search functionality using Fuse.js
(function () {
  var fuse = null;
  var indexLoaded = false;
  var indexLoading = null;

  var navSearch = document.querySelector('.nav-search');
  var searchToggle = document.querySelector('.search-toggle');
  var input = document.getElementById('search-input');
  var results = document.getElementById('search-results');
  var heroInput = document.getElementById('hero-search-input');
  var heroResults = document.getElementById('hero-search-results');
  var heroBtn = document.getElementById('hero-search-btn');

  // Load search index (returns a promise, deduplicates calls)
  function loadSearchIndex() {
    if (indexLoaded) return Promise.resolve();
    if (indexLoading) return indexLoading;
    indexLoading = new Promise(function (resolve) {
      // Build base URL from the CSS link href (works with both relative and absolute URLs)
      var baseUrl = '/';
      var cssLink = document.querySelector('link[href*="css/style.css"]');
      if (cssLink) {
        var href = cssLink.getAttribute('href');
        // Strip to just the path portion (handles both relative and absolute URLs)
        var match = href.match(/(\/[^?#]*\/)css\/style\.css/);
        if (match) {
          baseUrl = match[1];
        }
      }
      var xhr = new XMLHttpRequest();
      xhr.open('GET', baseUrl + 'index.json');
      xhr.onload = function () {
        if (xhr.status === 200) {
          try {
            var data = JSON.parse(xhr.responseText);
            fuse = new Fuse(data, {
              keys: [
                { name: 'title', weight: 0.4 },
                { name: 'categories', weight: 0.2 },
                { name: 'tags', weight: 0.15 },
                { name: 'description', weight: 0.15 },
                { name: 'content', weight: 0.1 }
              ],
              threshold: 0.35,
              includeScore: true,
              minMatchCharLength: 2
            });
            indexLoaded = true;
          } catch (e) {
            console.error('Failed to parse search index:', e);
          }
        }
        resolve();
      };
      xhr.onerror = function () {
        console.error('Failed to load search index');
        resolve();
      };
      xhr.send();
    });
    return indexLoading;
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ── Nav search (magnifying glass, click-to-open) ──

  function openNavSearch() {
    if (navSearch) navSearch.classList.add('open');
    loadSearchIndex();
    if (input) {
      input.focus();
      // Re-run search if there's already text
      if (input.value.trim().length >= 2) {
        doNavSearch(input.value.trim());
      }
    }
  }

  function closeNavSearch() {
    if (navSearch) navSearch.classList.remove('open');
    if (input) input.value = '';
    if (results) results.innerHTML = '';
  }

  function doNavSearch(query) {
    if (!fuse || !query || query.length < 2) {
      if (results) results.innerHTML = '';
      return;
    }
    var hits = fuse.search(query, { limit: 15 });
    if (hits.length === 0) {
      results.innerHTML = '<div class="search-no-results"><p>No recipes found for "<strong>' +
        escapeHtml(query) + '</strong>"</p><p>Try a different search term</p></div>';
      return;
    }
    results.innerHTML = hits.map(function (r) {
      var item = r.item;
      var cat = item.categories ? item.categories.join(', ') : '';
      var desc = item.description || (item.content ? item.content.substring(0, 120) + '...' : '');
      return '<a href="' + item.permalink + '" class="search-result-item">' +
        (cat ? '<span class="search-result-category">' + escapeHtml(cat) + '</span>' : '') +
        '<h4>' + escapeHtml(item.title) + '</h4>' +
        (desc ? '<p>' + escapeHtml(desc) + '</p>' : '') +
        '</a>';
    }).join('');
  }

  // Toggle nav search on magnifying glass click
  if (searchToggle) {
    searchToggle.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (navSearch && navSearch.classList.contains('open')) {
        closeNavSearch();
      } else {
        openNavSearch();
      }
    });
  }

  // Close nav search when clicking outside
  document.addEventListener('click', function (e) {
    if (navSearch && navSearch.classList.contains('open') && !navSearch.contains(e.target)) {
      closeNavSearch();
    }
  });

  // Prevent clicks inside the search dropdown from closing it
  if (navSearch) {
    var dropdown = navSearch.querySelector('.search-dropdown');
    if (dropdown) {
      dropdown.addEventListener('click', function (e) {
        e.stopPropagation();
      });
    }
  }

  if (input) {
    input.addEventListener('input', function () {
      var q = this.value.trim();
      loadSearchIndex().then(function () {
        doNavSearch(q);
      });
    });
    // Prevent enter from doing anything weird
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') e.preventDefault();
    });
  }

  // ── Hero search (homepage, dynamic results below search bar) ──

  function doHeroSearch(query) {
    if (!heroResults) return;
    if (!fuse || !query || query.length < 2) {
      heroResults.innerHTML = '';
      heroResults.classList.remove('visible');
      return;
    }
    var hits = fuse.search(query, { limit: 30 });
    if (hits.length === 0) {
      heroResults.innerHTML = '<div class="search-no-results"><p>No recipes found for "<strong>' +
        escapeHtml(query) + '</strong>"</p><p>Try a different search term</p></div>';
      heroResults.classList.add('visible');
      return;
    }
    heroResults.innerHTML = '<div class="hero-results-grid">' + hits.map(function (r) {
      var item = r.item;
      var cat = item.categories ? item.categories.join(', ') : '';
      var desc = item.description || (item.content ? item.content.substring(0, 100) + '...' : '');
      return '<a href="' + item.permalink + '" class="hero-result-card">' +
        (cat ? '<span class="hero-result-category">' + escapeHtml(cat) + '</span>' : '') +
        '<h4>' + escapeHtml(item.title) + '</h4>' +
        (desc ? '<p>' + escapeHtml(desc) + '</p>' : '') +
        '</a>';
    }).join('') + '</div>';
    heroResults.classList.add('visible');
  }

  function clearHeroResults() {
    if (heroResults) {
      heroResults.innerHTML = '';
      heroResults.classList.remove('visible');
    }
  }

  if (heroInput) {
    // Preload index immediately on homepage
    loadSearchIndex();

    heroInput.addEventListener('input', function () {
      var q = this.value.trim();
      loadSearchIndex().then(function () {
        doHeroSearch(q);
      });
    });

    // Also trigger on Enter key
    heroInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        var q = this.value.trim();
        loadSearchIndex().then(function () {
          doHeroSearch(q);
        });
      }
    });
  }

  if (heroBtn) {
    heroBtn.addEventListener('click', function () {
      var q = heroInput ? heroInput.value.trim() : '';
      loadSearchIndex().then(function () {
        doHeroSearch(q);
      });
    });
  }

  // Close hero results when clicking outside
  document.addEventListener('click', function (e) {
    if (heroInput && heroResults) {
      var heroBar = heroInput.closest('.hero-search');
      if (heroBar && !heroBar.contains(e.target) && !heroResults.contains(e.target)) {
        clearHeroResults();
      }
    }
  });

  // ── Keyboard shortcuts ──

  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      openNavSearch();
    }
    if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      e.preventDefault();
      openNavSearch();
    }
    if (e.key === 'Escape') {
      closeNavSearch();
      clearHeroResults();
    }
  });
})();