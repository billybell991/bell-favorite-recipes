// Search functionality using Fuse.js
(function () {
  let fuse = null;
  let searchIndex = null;

  const navSearch = document.querySelector('.nav-search');
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');

  // Load search index
  async function loadSearchIndex() {
    if (searchIndex) return;
    try {
      const baseUrl = document.querySelector('link[rel="stylesheet"]').href.replace(/css\/style\.css.*/, '');
      const response = await fetch(baseUrl + 'index.json');
      searchIndex = await response.json();
      fuse = new Fuse(searchIndex, {
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
    } catch (e) {
      console.error('Failed to load search index:', e);
    }
  }

  function openSearch() {
    if (navSearch) navSearch.classList.add('open');
    loadSearchIndex();
    if (input) input.focus();
  }

  function closeSearch() {
    if (navSearch) navSearch.classList.remove('open');
    if (input) input.value = '';
    if (results) results.innerHTML = '';
  }

  function performSearch(query) {
    if (!fuse || !query || query.length < 2) {
      results.innerHTML = '';
      return;
    }

    const searchResults = fuse.search(query, { limit: 15 });

    if (searchResults.length === 0) {
      results.innerHTML = '<div class="search-no-results"><p>No recipes found for "<strong>' +
        query.replace(/[<>&"]/g, '') + '</strong>"</p><p>Try a different search term</p></div>';
      return;
    }

    results.innerHTML = searchResults.map(function (result) {
      const item = result.item;
      const categories = item.categories ? item.categories.join(', ') : '';
      const description = item.description || (item.content ? item.content.substring(0, 120) + '...' : '');

      return '<a href="' + item.permalink + '" class="search-result-item">' +
        (categories ? '<span class="search-result-category">' + categories + '</span>' : '') +
        '<h4>' + item.title + '</h4>' +
        (description ? '<p>' + description + '</p>' : '') +
        '</a>';
    }).join('');
  }

  // Event listeners — open on hover, preload index
  if (navSearch) {
    navSearch.addEventListener('mouseenter', function () {
      loadSearchIndex();
    });
  }

  // Close when clicking outside
  document.addEventListener('click', function (e) {
    if (navSearch && !navSearch.contains(e.target)) {
      closeSearch();
    }
  });

  if (input) {
    input.addEventListener('input', function () {
      performSearch(this.value.trim());
    });
  }

  // Keyboard shortcut: Ctrl/Cmd+K or / to open search, Escape to close
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      openSearch();
    }
    if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      e.preventDefault();
      openSearch();
    }
    if (e.key === 'Escape') {
      closeSearch();
    }
  });
})();