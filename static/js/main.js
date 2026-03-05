// Main site JavaScript
(function () {
  // Mobile menu toggle
  const menuToggle = document.querySelector('.mobile-menu-toggle');
  const nav = document.getElementById('site-nav');

  if (menuToggle && nav) {
    menuToggle.addEventListener('click', function () {
      nav.classList.toggle('open');
      const expanded = nav.classList.contains('open');
      menuToggle.setAttribute('aria-expanded', expanded);
    });
  }

  // Mobile dropdown toggle (touch devices)
  var dropdownToggle = document.querySelector('.nav-dropdown-toggle');
  if (dropdownToggle) {
    dropdownToggle.addEventListener('click', function (e) {
      if (window.innerWidth <= 768) {
        e.preventDefault();
        this.parentElement.classList.toggle('open');
      }
    });
  }

  // Sort buttons
  const sortBtns = document.querySelectorAll('.sort-btn');
  const grid = document.getElementById('recipes-grid');

  sortBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      sortBtns.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');

      if (!grid) return;
      const cards = Array.from(grid.querySelectorAll('.recipe-card'));
      const sortType = btn.getAttribute('data-sort');

      cards.sort(function (a, b) {
        if (sortType === 'alpha') {
          return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title'));
        } else {
          return (b.getAttribute('data-date') || '').localeCompare(a.getAttribute('data-date') || '');
        }
      });

      cards.forEach(function (card) { grid.appendChild(card); });
    });
  });

  // View toggle (grid/list)
  const viewBtns = document.querySelectorAll('.view-btn');

  viewBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      viewBtns.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');

      if (!grid) return;
      const viewType = btn.getAttribute('data-view');
      grid.classList.toggle('list-view', viewType === 'list');
    });
  });
})();