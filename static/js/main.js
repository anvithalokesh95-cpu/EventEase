/**
 * EventEase - Main JavaScript
 * Interactive UI behaviors, toasts, search filtering, and navigation
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const navMenu = document.getElementById('navMenu');
  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      navMenu.classList.toggle('show');
    });
  }

  // 2. Flash Toast Auto-Dismiss
  const toasts = document.querySelectorAll('.flash-toast');
  toasts.forEach(toast => {
    setTimeout(() => {
      toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  });

  // 3. Category Filter Pills (Instant Client-side Filter on events list)
  const categoryPills = document.querySelectorAll('.category-pill');
  const eventCards = document.querySelectorAll('.event-card-item');

  if (categoryPills.length > 0 && eventCards.length > 0) {
    categoryPills.forEach(pill => {
      pill.addEventListener('click', () => {
        const selectedSlug = pill.getAttribute('data-slug');
        
        categoryPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');

        filterEvents(selectedSlug, getCurrentSearchQuery());
      });
    });
  }

  // 4. Live Search Input Debouncing
  const liveSearchInput = document.getElementById('liveEventSearch');
  if (liveSearchInput && eventCards.length > 0) {
    liveSearchInput.addEventListener('input', debounce((e) => {
      const activePill = document.querySelector('.category-pill.active');
      const selectedSlug = activePill ? activePill.getAttribute('data-slug') : 'all';
      filterEvents(selectedSlug, e.target.value.toLowerCase().trim());
    }, 250));
  }

  function getCurrentSearchQuery() {
    const input = document.getElementById('liveEventSearch');
    return input ? input.value.toLowerCase().trim() : '';
  }

  function filterEvents(slug, query) {
    let visibleCount = 0;
    const noResultsMsg = document.getElementById('noEventsMatch');

    eventCards.forEach(card => {
      const cardCategory = card.getAttribute('data-category');
      const cardTitle = (card.getAttribute('data-title') || '').toLowerCase();
      const cardDesc = (card.getAttribute('data-desc') || '').toLowerCase();
      const cardLocation = (card.getAttribute('data-location') || '').toLowerCase();

      const matchesCategory = (slug === 'all' || !slug || cardCategory === slug);
      const matchesQuery = (!query || cardTitle.includes(query) || cardDesc.includes(query) || cardLocation.includes(query));

      if (matchesCategory && matchesQuery) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (noResultsMsg) {
      noResultsMsg.style.display = (visibleCount === 0) ? 'block' : 'none';
    }
  }

  // Helper debounce
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // 5. Modal Helpers
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  };
});
