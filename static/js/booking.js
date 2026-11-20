/**
 * EventEase - Booking Interactivity
 * Dynamic ticket calculation, real-time totals, checkout validation
 */

document.addEventListener('DOMContentLoaded', () => {
  const qtyInput = document.getElementById('ticketQuantity');
  const btnMinus = document.getElementById('btnQtyMinus');
  const btnPlus = document.getElementById('btnQtyPlus');
  const unitPriceEl = document.getElementById('unitPrice');
  const totalAmountEl = document.getElementById('totalAmount');
  const hiddenTotalInput = document.getElementById('hiddenTotalAmount');
  const availableEl = document.getElementById('maxAvailable');

  if (!qtyInput) return;

  const unitPrice = parseFloat(unitPriceEl ? unitPriceEl.getAttribute('data-price') : 0);
  const maxAvailable = parseInt(availableEl ? availableEl.getAttribute('data-max') : 10, 10);

  function updateTotal() {
    let count = parseInt(qtyInput.value, 10);
    if (isNaN(count) || count < 1) count = 1;
    if (count > maxAvailable) count = maxAvailable;

    qtyInput.value = count;
    const total = (count * unitPrice).toFixed(2);

    if (totalAmountEl) {
      totalAmountEl.textContent = `$${total}`;
    }
    if (hiddenTotalInput) {
      hiddenTotalInput.value = total;
    }
  }

  if (btnMinus) {
    btnMinus.addEventListener('click', () => {
      let current = parseInt(qtyInput.value, 10) || 1;
      if (current > 1) {
        qtyInput.value = current - 1;
        updateTotal();
      }
    });
  }

  if (btnPlus) {
    btnPlus.addEventListener('click', () => {
      let current = parseInt(qtyInput.value, 10) || 1;
      if (current < maxAvailable) {
        qtyInput.value = current + 1;
        updateTotal();
      }
    });
  }

  qtyInput.addEventListener('change', updateTotal);
  qtyInput.addEventListener('keyup', updateTotal);

  // Initialize total
  updateTotal();
});
