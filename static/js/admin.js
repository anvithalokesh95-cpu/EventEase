/**
 * EventEase - Admin Dashboard Scripts
 * Sidebar responsiveness, quick search, interactive charts, and confirmation modals
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const adminMobileToggle = document.getElementById('adminMobileToggle');
  const adminSidebar = document.querySelector('.admin-sidebar');
  if (adminMobileToggle && adminSidebar) {
    adminMobileToggle.addEventListener('click', () => {
      adminSidebar.classList.toggle('show');
    });
  }

  // 2. Table Filter Search
  const adminSearchInput = document.getElementById('adminTableSearch');
  if (adminSearchInput) {
    adminSearchInput.addEventListener('keyup', (e) => {
      const term = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll('.data-table tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  }

  // 3. Confirm Delete Handlers
  const deleteForms = document.querySelectorAll('.form-delete-confirm');
  deleteForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const itemName = form.getAttribute('data-item') || 'this item';
      const confirmed = confirm(`Are you sure you want to permanently delete ${itemName}? This action cannot be undone.`);
      if (!confirmed) {
        e.preventDefault();
      }
    });
  });

  // 4. Render Pure SVG Dashboard Charts (No heavy external dependencies needed!)
  const chartContainer = document.getElementById('revenueAnalyticsChart');
  if (chartContainer) {
    renderSimpleChart(chartContainer);
  }

  function renderSimpleChart(container) {
    const rawData = container.getAttribute('data-points');
    let points = [35, 55, 40, 75, 60, 95, 80]; // fallback
    if (rawData) {
      try {
        points = JSON.parse(rawData);
      } catch (err) {}
    }

    const svgWidth = 600;
    const svgHeight = 220;
    const padding = 35;
    const maxVal = Math.max(...points, 100);

    const xStep = (svgWidth - padding * 2) / (points.length - 1);
    const coords = points.map((p, idx) => {
      const x = padding + idx * xStep;
      const y = svgHeight - padding - (p / maxVal) * (svgHeight - padding * 2);
      return { x, y, val: p };
    });

    // Create polyline and fill path
    const pathD = coords.reduce((acc, c, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${c.x} ${c.y}`, '');
    const fillD = `${pathD} L ${coords[coords.length - 1].x} ${svgHeight - padding} L ${coords[0].x} ${svgHeight - padding} Z`;

    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    let svgHtml = `
      <svg viewBox="0 0 ${svgWidth} ${svgHeight}" width="100%" height="220" style="overflow: visible;">
        <defs>
          <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#4F46E5" stop-opacity="0.35" />
            <stop offset="100%" stop-color="#4F46E5" stop-opacity="0.0" />
          </linearGradient>
        </defs>
        <!-- Horizontal Guide Lines -->
        <line x1="${padding}" y1="${padding}" x2="${svgWidth - padding}" y2="${padding}" stroke="#E2E8F0" stroke-dasharray="4" />
        <line x1="${padding}" y1="${(svgHeight - padding * 2) / 2 + padding}" x2="${svgWidth - padding}" y2="${(svgHeight - padding * 2) / 2 + padding}" stroke="#E2E8F0" stroke-dasharray="4" />
        <line x1="${padding}" y1="${svgHeight - padding}" x2="${svgWidth - padding}" y2="${svgHeight - padding}" stroke="#CBD5E1" stroke-width="1.5" />
        
        <!-- Shaded Area -->
        <path d="${fillD}" fill="url(#chartGrad)" />
        
        <!-- Trend Line -->
        <path d="${pathD}" fill="none" stroke="#4F46E5" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    `;

    // Data points & X labels
    coords.forEach((c, idx) => {
      svgHtml += `
        <circle cx="${c.x}" cy="${c.y}" r="4" fill="#FFFFFF" stroke="#4F46E5" stroke-width="2.5" />
        <text x="${c.x}" y="${svgHeight - 12}" font-family="Inter, sans-serif" font-size="11" fill="#64748B" text-anchor="middle">${labels[idx] || ''}</text>
      `;
    });

    svgHtml += `</svg>`;
    container.innerHTML = svgHtml;
  }
});
