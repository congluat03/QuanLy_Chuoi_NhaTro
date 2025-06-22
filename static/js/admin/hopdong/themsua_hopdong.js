
// Danh sách thời hạn hợp đồng (1 tháng đến 60 tháng)
const durations = Array.from({ length: 60 }, (_, i) => i + 1).map(n => ({
  display: n % 12 === 0 ? `${n / 12} năm` : `${n} tháng`,
  value: n
}));

// Danh sách ngày thu tiền (1 đến 31)
const days = Array.from({ length: 31 }, (_, i) => i + 1).map(n => ({
  display: `${n}`,
  value: n
}));

// Danh sách kỳ thanh toán (1 tháng đến 12 tháng)
const paymentTerms = Array.from({ length: 12 }, (_, i) => i + 1).map(n => ({
  display: n === 12 ? `1 năm` : `${n} tháng`,
  value: n
}));

// Elements cho thời hạn hợp đồng
const durationInput = document.getElementById('thoi-han-hd');
const durationHiddenInput = document.getElementById('thoi-han-hd-value');
const durationDropdown = document.getElementById('duration-dropdown');
const durationList = document.getElementById('duration-list');

// Elements cho ngày thu tiền
const dayInput = document.getElementById('ngay-thu-tien');
const dayHiddenInput = document.getElementById('ngay-thu-tien-value');
const dayDropdown = document.getElementById('day-dropdown');
const dayList = document.getElementById('day-list');

// Elements cho kỳ thanh toán
const paymentTermInput = document.getElementById('ky-thanh-toan');
const paymentTermHiddenInput = document.getElementById('ky-thanh-toan-value');
const paymentTermDropdown = document.getElementById('payment-term-dropdown');
const paymentTermList = document.getElementById('payment-term-list');

// Hàm hiển thị danh sách
function renderList(listElement, items, inputElement, hiddenInput, dropdownElement) {
  listElement.innerHTML = '';
  if (items.length === 0) {
    dropdownElement.classList.add('hidden');
    return;
  }
  items.forEach(item => {
    const li = document.createElement('li');
    li.className = 'px-3 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 cursor-pointer';
    li.textContent = item.display;
    li.onclick = () => {
      inputElement.value = item.display;
      hiddenInput.value = item.value;
      dropdownElement.classList.add('hidden');
    };
    listElement.appendChild(li);
  });
  dropdownElement.classList.remove('hidden');
}

// Hàm lọc thời hạn hợp đồng
function filterDurations(value) {
  const searchTerm = value.toLowerCase().trim();
  const filtered = durations.filter(duration =>
    duration.display.toLowerCase().includes(searchTerm)
  );
  renderList(durationList, filtered, durationInput, durationHiddenInput, durationDropdown);
}

// Hàm lọc ngày thu tiền
function filterDays(value) {
  const searchTerm = value.trim();
  const filtered = days.filter(day =>
    day.display.startsWith(searchTerm)
  );
  renderList(dayList, filtered, dayInput, dayHiddenInput, dayDropdown);
}

// Hàm lọc kỳ thanh toán
function filterPaymentTerms(value) {
  const searchTerm = value.toLowerCase().trim();
  const filtered = paymentTerms.filter(term =>
    term.display.toLowerCase().includes(searchTerm)
  );
  renderList(paymentTermList, filtered, paymentTermInput, paymentTermHiddenInput, paymentTermDropdown);
}

// Hiển thị/ẩn dropdown thời hạn
function toggleDurationDropdown() {
  if (durationDropdown.classList.contains('hidden')) {
    renderList(durationList, durations, durationInput, durationHiddenInput, durationDropdown);
  } else {
    durationDropdown.classList.add('hidden');
  }
}

// Hiển thị/ẩn dropdown ngày
function toggleDayDropdown() {
  if (dayDropdown.classList.contains('hidden')) {
    renderList(dayList, days, dayInput, dayHiddenInput, dayDropdown);
  } else {
    dayDropdown.classList.add('hidden');
  }
}

// Hiển thị/ẩn dropdown kỳ thanh toán
function togglePaymentTermDropdown() {
  if (paymentTermDropdown.classList.contains('hidden')) {
    renderList(paymentTermList, paymentTerms, paymentTermInput, paymentTermHiddenInput, paymentTermDropdown);
  } else {
    paymentTermDropdown.classList.add('hidden');
  }
}
// Ẩn dropdown khi click ngoài
document.addEventListener('click', (e) => {
  if (!durationInput.contains(e.target) && !durationDropdown.contains(e.target)) {
    durationDropdown.classList.add('hidden');
  }
  if (!dayInput.contains(e.target) && !dayDropdown.contains(e.target)) {
    dayDropdown.classList.add('hidden');
  }
  if (!paymentTermInput.contains(e.target) && !paymentTermDropdown.contains(e.target)) {
    paymentTermDropdown.classList.add('hidden');
  }
});