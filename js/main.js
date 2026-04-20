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

  // Dropdown and submenu handling
  var dropdown = document.querySelector('.nav-dropdown');
  var dropdownToggle = document.querySelector('.nav-dropdown-toggle');

  if (dropdown && dropdownToggle) {
    if (window.innerWidth > 768) {
      // Desktop: mouseenter/mouseleave with delay for forgiving hover
      var dropdownHideTimer;
      dropdown.addEventListener('mouseenter', function () {
        clearTimeout(dropdownHideTimer);
        dropdown.classList.add('open');
      });
      dropdown.addEventListener('mouseleave', function () {
        dropdownHideTimer = setTimeout(function () {
          dropdown.classList.remove('open');
          // Also close any open submenus
          document.querySelectorAll('.nav-submenu-item.open').forEach(function (item) {
            item.classList.remove('open');
          });
        }, 250);
      });

      // Submenu items: mouseenter/mouseleave with delay
      var submenuItems = document.querySelectorAll('.nav-submenu-item');
      submenuItems.forEach(function (item) {
        var subHideTimer;
        item.addEventListener('mouseenter', function () {
          clearTimeout(subHideTimer);
          // Close other open submenus
          document.querySelectorAll('.nav-submenu-item.open').forEach(function (other) {
            if (other !== item) other.classList.remove('open');
          });
          item.classList.add('open');
        });
        item.addEventListener('mouseleave', function () {
          subHideTimer = setTimeout(function () {
            item.classList.remove('open');
          }, 200);
        });
      });
    } else {
      // Mobile: click to toggle
      dropdownToggle.addEventListener('click', function (e) {
        var isOpen = dropdown.classList.contains('open');

        // First tap: open dropdown but stay on page
        if (!isOpen) {
          e.preventDefault();
          dropdown.classList.add('open');
          return;
        }

        // Second tap when already open: allow navigation
        // (no preventDefault here)
      });

      var submenuLinks = document.querySelectorAll('.nav-submenu-link');
      submenuLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
          var item = this.closest('.nav-submenu-item');
          if (!item) return;

          var isOpen = item.classList.contains('open');

          // First tap: open this submenu (and close others) but stay on page
          if (!isOpen) {
            e.preventDefault();
            document.querySelectorAll('.nav-submenu-item.open').forEach(function (other) {
              if (other !== item) other.classList.remove('open');
            });
            item.classList.add('open');
            return;
          }

          // Second tap on an already-open item: allow navigation to the parent page
          // (no preventDefault here so the browser follows the link normally)
        });
      });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function (e) {
      if (dropdown && !dropdown.contains(e.target)) {
        dropdown.classList.remove('open');
        document.querySelectorAll('.nav-submenu-item.open').forEach(function (item) {
          item.classList.remove('open');
        });
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