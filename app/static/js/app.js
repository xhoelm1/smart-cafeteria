// Flash auto-dismiss
(function () {
  setTimeout(function () {
    var stack = document.getElementById('flash-stack');
    if (stack) stack.remove();
  }, 4000);
})();

// Live menu search
(function () {
  var input = document.getElementById('menu-search');
  if (!input) return;
  var grid = document.getElementById('menu-grid');
  var empty = document.getElementById('no-results');
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    var cards = grid.querySelectorAll('.menu-card');
    var visible = 0;
    cards.forEach(function (card) {
      var name = card.getAttribute('data-name') || '';
      var match = name.indexOf(q) !== -1;
      card.style.display = match ? '' : 'none';
      if (match) visible += 1;
    });
    if (empty) empty.hidden = visible !== 0;
  });
})();

// Notifications bell polling
(function () {
  var bell = document.getElementById('bell-count');
  if (!bell) return;
  function refresh() {
    fetch('/api/notifications/unread_count', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        if (data.count > 0) {
          bell.hidden = false;
          bell.textContent = data.count;
        } else {
          bell.hidden = true;
        }
      })
      .catch(function () {});
  }
  setInterval(refresh, 10000);
})();

// Add-to-cart via JSON API (no page reload)
(function () {
  var forms = document.querySelectorAll('form.add-to-cart-form');
  if (!forms.length) return;
  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

  function ensureStack() {
    var stack = document.getElementById('flash-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.id = 'flash-stack';
      stack.className = 'flash-stack';
      document.body.appendChild(stack);
    }
    return stack;
  }

  function toast(message, type) {
    var stack = ensureStack();
    var el = document.createElement('div');
    el.className = 'flash flash-' + (type || 'info');
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(function () { el.remove(); }, 3500);
  }

  function updateCard(form, info) {
    var card = form.closest('.menu-card');
    if (!card || !info) return;
    var chip = card.querySelector('.chip');
    if (chip && info.stock_status) {
      chip.className = 'chip chip-' + info.stock_status;
      chip.textContent = info.stock_status === 'sold_out'
        ? 'Sold Out'
        : info.stock_status === 'low' ? 'Low Stock' : 'In Stock';
    }
    var qtyInput = form.querySelector('input[name="quantity"]');
    if (qtyInput && typeof info.stock === 'number') {
      qtyInput.max = Math.max(info.stock, 1);
      if (parseInt(qtyInput.value, 10) > info.stock) {
        qtyInput.value = Math.max(info.stock, 1);
      }
    }
  }

  function isSoldOut(form) {
    var card = form.closest('.menu-card');
    return !!(card && card.querySelector('.chip-sold_out'));
  }

  forms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var qtyInput = form.querySelector('input[name="quantity"]');
      var btn = form.querySelector('button[type="submit"]');
      var itemId = parseInt(form.dataset.itemId, 10);
      if (!itemId) {
        toast('Could not identify item.', 'error');
        return;
      }
      var payload = {
        item_id: itemId,
        quantity: parseInt(qtyInput && qtyInput.value, 10) || 1
      };
      if (btn) btn.disabled = true;
      fetch('/api/cart/add', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(payload)
      })
        .then(function (r) {
          return r.json().catch(function () { return null; }).then(function (data) {
            return { ok: r.ok, status: r.status, data: data };
          });
        })
        .then(function (res) {
          if (res.ok && res.data && res.data.ok) {
            toast(res.data.message, res.data.capped ? 'info' : 'success');
            updateCard(form, res.data.item);
          } else {
            var msg = (res.data && res.data.error) || 'Could not add to cart.';
            toast(msg, 'error');
          }
        })
        .catch(function () {
          toast('Network error. Please try again.', 'error');
        })
        .then(function () {
          if (btn) btn.disabled = isSoldOut(form);
        });
    });
  });
})();

// Order status polling on detail page
window.pollOrderStatus = function (orderId) {
  var el = document.getElementById('order-status');
  if (!el) return;
  function refresh() {
    fetch('/api/orders/' + orderId + '/status', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        if (data.status !== el.textContent.trim()) {
          el.className = 'status status-' + data.status;
          el.textContent = data.status;
        }
      })
      .catch(function () {});
  }
  setInterval(refresh, 5000);
};
