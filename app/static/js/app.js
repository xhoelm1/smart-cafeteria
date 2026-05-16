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
