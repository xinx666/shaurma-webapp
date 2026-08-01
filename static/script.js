// ============================================
// script.js — ПОЛНАЯ ЛОГИКА ПРИЛОЖЕНИЯ
// ============================================

let currentCategory = 'shawarma';
let cart = [];
let selectedProduct = null;
let selectedSize = 'medium';
let selectedRemoved = [];
let selectedExtras = [];
let editingCartIndex = null;
let userOrders = [];
let currentUserId = null;

// ===== ЗАГРУЗКА СОХРАНЁННЫХ ДАННЫХ =====
document.addEventListener('DOMContentLoaded', function() {
    if (window.Telegram && Telegram.WebApp) {
        Telegram.WebApp.ready();
        const user = Telegram.WebApp.initDataUnsafe?.user;
        if (user) {
            currentUserId = user.id;
            console.log('👤 Пользователь:', user.first_name, 'ID:', currentUserId);
        }
    }

    loadOrdersFromStorage();
    loadCartFromStorage();

    renderProducts('shawarma');

    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentCategory = this.dataset.category;
            renderProducts(currentCategory);
        });
    });

    document.getElementById('cartButton').addEventListener('click', openCart);

    document.getElementById('productModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });

    addOrderHistoryButton();
});

// ===== РАБОТА С LOCALSTORAGE =====
function saveCartToStorage() {
    try {
        localStorage.setItem('shaurma_cart', JSON.stringify(cart));
    } catch (e) {
        console.log('Не удалось сохранить корзину');
    }
}

function loadCartFromStorage() {
    try {
        const saved = localStorage.getItem('shaurma_cart');
        if (saved) {
            cart = JSON.parse(saved);
        }
    } catch (e) {
        console.log('Не удалось загрузить корзину');
    }
}

function saveOrdersToStorage() {
    try {
        localStorage.setItem('shaurma_orders', JSON.stringify(userOrders));
    } catch (e) {
        console.log('Не удалось сохранить заказы');
    }
}

function loadOrdersFromStorage() {
    try {
        const saved = localStorage.getItem('shaurma_orders');
        if (saved) {
            userOrders = JSON.parse(saved);
        }
    } catch (e) {
        console.log('Не удалось загрузить заказы');
    }
}

// ===== ОТРИСОВКА ТОВАРОВ =====
function renderProducts(category) {
    const container = document.getElementById('productList');
    const products = menuData[category] || [];

    if (products.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px 20px; color: #7a5a9a;">
                <div style="font-size: 48px; margin-bottom: 12px;">🛠️</div>
                <div style="font-size: 18px; font-weight: 600; color: #b39ddb;">В разработке</div>
                <div style="font-size: 14px; margin-top: 6px;">Скоро здесь появятся новые вкусные позиции! 🙏</div>
            </div>
        `;
        return;
    }

    container.innerHTML = products.map(product => {
        let displayPrice = '';
        let displayWeight = '';
        if (product.has_sizes) {
            displayPrice = `от ${product.price.medium} ₽`;
            displayWeight = `${product.weight.medium}–${product.weight.xxl} г`;
        } else {
            displayPrice = `${product.price} ₽`;
            displayWeight = `${product.weight} г`;
        }

        const inStock = product.in_stock !== false;
        const isDrink = product.is_drink === true;

        // Общее количество товара в корзине (по id)
        const totalQty = cart
            .filter(item => item.id === product.id)
            .reduce((sum, item) => sum + item.qty, 0);

        let buttonHtml = '';
        if (!inStock) {
            buttonHtml = `
                <div style="margin-top:10px; padding:8px; border-radius:12px; background:#2a1a4a; color:#7a5a9a; text-align:center; font-size:13px; font-weight:600; cursor:pointer;" onclick="openProduct(${product.id})">
                    Скоро появится 🤗
                </div>
            `;
        } else if (isDrink) {
            if (totalQty > 0) {
                buttonHtml = `
                    <div class="qty-control">
                        <button class="qty-btn" onclick="event.stopPropagation(); changeDrinkQty(${product.id}, -1)">−</button>
                        <span>${totalQty}</span>
                        <button class="qty-btn" onclick="event.stopPropagation(); changeDrinkQty(${product.id}, 1)">+</button>
                    </div>
                `;
            } else {
                buttonHtml = `
                    <button class="add-btn" onclick="event.stopPropagation(); addDrink(${product.id})">+ Добавить</button>
                `;
            }
        } else if (totalQty > 0) {
            buttonHtml = `
                <div class="qty-control">
                    <button class="qty-btn" onclick="event.stopPropagation(); changeQtyFromCard(${product.id}, -1)">−</button>
                    <span>${totalQty}</span>
                    <button class="qty-btn" onclick="event.stopPropagation(); openProduct(${product.id})">+</button>
                </div>
            `;
        } else {
            buttonHtml = `
                <button class="add-btn" onclick="event.stopPropagation(); openProduct(${product.id})">+ Добавить</button>
            `;
        }

        return `
            <div class="product-card">
                <div class="card-image" onclick="openProduct(${product.id})">
                    ${product.img && product.img !== 'nope.jpg' 
                        ? `<img src="${product.img}" alt="${product.name}" />` 
                        : '🥙'
                    }
                </div>
                <div class="card-body">
                    <h3 onclick="openProduct(${product.id})">${product.name}</h3>
                    <div class="price" onclick="openProduct(${product.id})">${displayPrice}</div>
                    <div class="weight" onclick="openProduct(${product.id})">${displayWeight}</div>
                    ${buttonHtml}
                </div>
            </div>
        `;
    }).join('');

    updateCartBadge();
}

function addDrink(productId) {
    const product = findProduct(productId);
    if (!product) return;

    const existing = cart.find(item => item.id === productId && !item.size);
    if (existing) {
        existing.qty += 1;
    } else {
        cart.push({
            id: product.id,
            name: product.name,
            size: null,
            price: product.price,
            weight: product.weight,
            removed: [],
            extras: [],
            qty: 1,
            img: product.img || '🥙'
        });
    }
    saveCartToStorage();
    renderProducts(currentCategory);
    updateCartBadge();
}

function changeDrinkQty(productId, delta) {
    const existing = cart.find(item => item.id === productId && !item.size);
    if (existing) {
        existing.qty += delta;
        if (existing.qty <= 0) {
            cart = cart.filter(item => !(item.id === productId && !item.size));
        }
    }
    saveCartToStorage();
    renderProducts(currentCategory);
    updateCartBadge();
}

function changeQtyFromCard(productId, delta) {
    const product = findProduct(productId);
    if (!product) return;

    // Удаляем последний добавленный товар с этим id (если есть)
    // Ищем товар с этим id
    const items = cart.filter(item => item.id === productId);
    if (items.length === 0) return;
    
    // Берем последний добавленный (или любой)
    const target = items[items.length - 1];
    target.qty += delta;
    if (target.qty <= 0) {
        cart = cart.filter(item => item !== target);
    }
    saveCartToStorage();
    renderProducts(currentCategory);
    updateCartBadge();
}

// ===== ПОИСК ТОВАРА =====
function findProduct(id) {
    for (const cat in menuData) {
        const found = menuData[cat].find(p => p.id === id);
        if (found) return found;
    }
    return null;
}

// ===== ФОРМАТИРОВАНИЕ ВРЕМЕНИ =====
function getAvailableTimes() {
    const now = new Date();
    const novosibirskOffset = 7 * 60;
    const localOffset = now.getTimezoneOffset();
    const offsetDiff = novosibirskOffset + localOffset;
    const novosibirskTime = new Date(now.getTime() + offsetDiff * 60 * 1000);
    
    const currentMinutes = novosibirskTime.getHours() * 60 + novosibirskTime.getMinutes();
    const availableTimes = [];
    
    const isWorkingTime = currentMinutes >= 11 * 60 && currentMinutes <= 22 * 60;
    
    if (!isWorkingTime) {
        if (currentMinutes >= 22 * 60) {
            availableTimes.push('завтра к:');
        }
        let timeMinutes = 11 * 60;
        while (timeMinutes <= 22 * 60) {
            const hours = Math.floor(timeMinutes / 60);
            const mins = timeMinutes % 60;
            availableTimes.push(`${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`);
            timeMinutes += 15;
        }
        return availableTimes;
    }
    
    availableTimes.push('как можно скорее');
    let timeMinutes = 11 * 60;
    while (timeMinutes <= 22 * 60) {
        if (timeMinutes > currentMinutes + 15) {
            const hours = Math.floor(timeMinutes / 60);
            const mins = timeMinutes % 60;
            availableTimes.push(`${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`);
        }
        timeMinutes += 15;
    }
    
    return availableTimes;
}

// ===== ОТКРЫТИЕ ТОВАРА (МОДАЛКА) =====
function openProduct(productId, editIndex = null) {
    const product = findProduct(productId);
    if (!product) return;

    if (product.is_drink) {
        const modal = document.getElementById('productModal');
        const content = document.getElementById('modalContent');
        const inStock = product.in_stock !== false;

        const totalQty = cart
            .filter(item => item.id === productId)
            .reduce((sum, item) => sum + item.qty, 0);

        let html = `
            <div class="modal-image">
                ${product.img && product.img !== 'nope.jpg' 
                    ? `<img src="${product.img}" alt="${product.name}" />` 
                    : '🥙'
                }
            </div>
            <h2>${product.name}</h2>
            <div class="modal-desc">${product.description || ''}</div>
            <div class="modal-composition">🧾 Состав: ${product.composition}</div>
            <div style="font-size: 11px; color: #7a5a9a; text-align: center; margin-bottom: 4px;">КБЖУ</div>
            <div class="modal-kbju">
                <span>🔥 ${product.kcals} ккал</span>
                <span>💪 ${product.proteins}г</span>
                <span>🧈 ${product.fats}г</span>
                <span>🍞 ${product.carbs}г</span>
            </div>
            ${!inStock ? '<div style="text-align:center;padding:16px;color:#7a5a9a;">❌ Временно отсутствует</div>' : ''}
            
            ${inStock ? `
                <div style="display: flex; align-items: center; gap: 16px; justify-content: center; margin: 16px 0;">
                    <button class="qty-btn-modal" onclick="changeDrinkQtyInModal(-1)">−</button>
                    <span style="font-size: 20px; font-weight: 700; min-width: 30px; text-align: center;" id="drinkModalQty">${totalQty}</span>
                    <button class="qty-btn-modal" onclick="changeDrinkQtyInModal(1)">+</button>
                </div>
            ` : ''}
            
            <div class="modal-actions">
                ${inStock ? `<button class="btn-add" onclick="addDrinkFromModal(${product.id})">🛒 Добавить</button>` : ''}
                <button class="btn-close" onclick="closeModal()">Закрыть</button>
            </div>
        `;

        content.innerHTML = html;
        modal.classList.add('open');
        return;
    }

    const inStock = product.in_stock !== false;
    
    selectedProduct = product;
    selectedSize = product.has_sizes ? 'medium' : null;
    selectedRemoved = [];
    selectedExtras = [];
    editingCartIndex = editIndex;

    if (editIndex === null) {
        const existingItem = cart.find(item => item.id === productId);
        if (existingItem) {
            selectedSize = existingItem.size || (product.has_sizes ? 'medium' : null);
            selectedRemoved = existingItem.removed || [];
            selectedExtras = existingItem.extras || [];
        }
    } else if (editIndex !== null && cart[editIndex]) {
        const item = cart[editIndex];
        selectedSize = item.size || (product.has_sizes ? 'medium' : null);
        selectedRemoved = item.removed || [];
        selectedExtras = item.extras || [];
    }

    const modal = document.getElementById('productModal');
    const content = document.getElementById('modalContent');

    // Общее количество товара в корзине (по id)
    const currentQty = cart
        .filter(item => item.id === product.id)
        .reduce((sum, item) => sum + item.qty, 0);

    let html = `
        <div class="modal-image">
            ${product.img && product.img !== 'nope.jpg' 
                ? `<img src="${product.img}" alt="${product.name}" />` 
                : '🥙'
            }
        </div>
        <h2>${product.name}</h2>
        <div class="modal-desc">${product.description || ''}</div>
        <div class="modal-composition">🧾 Состав: ${product.composition}</div>
    `;

    if (product.kcals_per_100) {
        html += `
            <div style="font-size: 11px; color: #7a5a9a; text-align: center; margin-bottom: 4px;">КБЖУ на 100г</div>
            <div class="modal-kbju">
                <span>🔥 ${product.kcals_per_100} ккал</span>
                <span>💪 ${product.proteins_per_100}г</span>
                <span>🧈 ${product.fats_per_100}г</span>
                <span>🍞 ${product.carbs_per_100}г</span>
            </div>
        `;
    }

    if (product.has_sizes) {
        html += `
            <div class="size-selector">
                <button class="size-btn ${selectedSize === 'medium' ? 'active' : ''}" data-size="medium" onclick="selectSize('medium')">
                    Средний <span class="size-price">${product.price.medium} ₽</span>
                </button>
                <button class="size-btn ${selectedSize === 'large' ? 'active' : ''}" data-size="large" onclick="selectSize('large')">
                    Большой <span class="size-price">${product.price.large} ₽</span>
                </button>
                <button class="size-btn ${selectedSize === 'xxl' ? 'active' : ''}" data-size="xxl" onclick="selectSize('xxl')">
                    XXL <span class="size-price">${product.price.xxl} ₽</span>
                </button>
            </div>
        `;
    }

    if (inStock && product.ingredients_to_remove && product.ingredients_to_remove.length > 0) {
        html += `<div class="ingredients-remove"><p>❌ Исключить ингредиенты:</p>`;
        product.ingredients_to_remove.forEach(ing => {
            const checked = selectedRemoved.includes(ing) ? 'checked' : '';
            html += `
                <label>
                    <input type="checkbox" value="${ing}" ${checked} /> ${ing}
                </label>
            `;
        });

        if (product.can_remove_chicken !== false) {
            const checked = selectedRemoved.includes('курица') ? 'checked' : '';
            html += `
                <label>
                    <input type="checkbox" value="курица" ${checked} /> курица
                </label>
            `;
        }

        html += `</div>`;
    }

    if (inStock) {
        html += `
            <div class="ingredients-remove" style="border-top:1px solid #2a1a4a; padding-top:12px; margin-top:4px;">
                <p>➕ Дополнения</p>
                <label>
                    <input type="checkbox" value="курица +30г" data-extra='{"name":"курица +30г","price":50}' ${selectedExtras.includes('курица +30г') ? 'checked' : ''} /> Курица (+30г) <span style="color:#ff4081;">+50 ₽</span>
                </label>
                <label>
                    <input type="checkbox" value="сыр +30г" data-extra='{"name":"сыр +30г","price":50}' ${selectedExtras.includes('сыр +30г') ? 'checked' : ''} /> Сыр (+30г) <span style="color:#ff4081;">+50 ₽</span>
                </label>
                <label>
                    <input type="checkbox" value="халапеньо +20г" data-extra='{"name":"халапеньо +20г","price":40}' ${selectedExtras.includes('халапеньо +20г') ? 'checked' : ''} /> Халапеньо (+20г) <span style="color:#ff4081;">+40 ₽</span>
                </label>
            </div>
            <div style="text-align:center; padding:8px; background:rgba(213,0,176,0.1); border-radius:12px; margin-bottom:12px; color:#b39ddb; font-size:13px;">
                🛒 В корзине: <span style="color:#ff4081; font-weight:700;" id="cartQtyDisplay">${currentQty}</span> шт.
            </div>
        `;
    }

    if (!inStock) {
        html += `
            <div style="text-align:center;padding:16px;color:#7a5a9a;">🙏 Скоро появится</div>
        `;
    }

    const btnText = editIndex !== null ? '💾 Сохранить изменения' : '🛒 Добавить в корзину';
    html += `
        <div class="modal-actions">
            ${inStock ? `<button class="btn-add" onclick="addToCartFromModal()">${btnText}</button>` : ''}
            <button class="btn-close" onclick="closeModal()">Закрыть</button>
        </div>
    `;

    content.innerHTML = html;
    modal.classList.add('open');
}

// ===== ДЛЯ НАПИТКОВ В МОДАЛКЕ =====
let drinkModalQty = 0;
let drinkModalId = null;

function changeDrinkQtyInModal(delta) {
    const qtySpan = document.getElementById('drinkModalQty');
    let qty = parseInt(qtySpan.textContent) + delta;
    if (qty < 0) qty = 0;
    qtySpan.textContent = qty;
    drinkModalQty = qty;
}

function addDrinkFromModal(productId) {
    const qtySpan = document.getElementById('drinkModalQty');
    let qty = parseInt(qtySpan.textContent);
    if (qty <= 0) {
        alert('Выберите количество');
        return;
    }

    const product = findProduct(productId);
    if (!product) return;

    const existing = cart.find(item => item.id === productId && !item.size);
    if (existing) {
        existing.qty = qty;
    } else {
        cart.push({
            id: product.id,
            name: product.name,
            size: null,
            price: product.price,
            weight: product.weight,
            removed: [],
            extras: [],
            qty: qty,
            img: product.img || '🥙'
        });
    }

    saveCartToStorage();
    closeModal();
    renderProducts(currentCategory);
    updateCartBadge();
}

// ===== ВЫБОР РАЗМЕРА =====
function selectSize(size) {
    selectedSize = size;
    document.querySelectorAll('.size-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.size === size);
    });
}

// ===== ЗАКРЫТИЕ МОДАЛКИ =====
function closeModal() {
    document.getElementById('productModal').classList.remove('open');
    editingCartIndex = null;
    drinkModalId = null;
}

// ===== ДОБАВЛЕНИЕ ИЗ МОДАЛКИ (для шаурмы) =====
function addToCartFromModal() {
    if (!selectedProduct) return;

    let price = selectedProduct.price;
    let weight = selectedProduct.weight;
    let size = null;

    if (selectedProduct.has_sizes) {
        size = selectedSize || 'medium';
        price = selectedProduct.price[size];
        weight = selectedProduct.weight[size];
    }

    const removedCheckboxes = document.querySelectorAll('.ingredients-remove input[type="checkbox"]:not([data-extra])');
    const removed = Array.from(removedCheckboxes).filter(cb => cb.checked).map(cb => cb.value);

    const extraCheckboxes = document.querySelectorAll('.ingredients-remove input[data-extra]');
    const extras = [];
    let extraPrice = 0;
    extraCheckboxes.forEach(cb => {
        if (cb.checked) {
            const data = JSON.parse(cb.dataset.extra);
            extras.push(data.name);
            extraPrice += data.price;
        }
    });

    const finalPrice = price + extraPrice;

    if (editingCartIndex !== null) {
        cart[editingCartIndex] = {
            ...cart[editingCartIndex],
            size: size,
            price: finalPrice,
            weight: weight,
            removed: removed,
            extras: extras
        };
        saveCartToStorage();
        closeModal();
        renderProducts(currentCategory);
        updateCartBadge();
        openCart();
        return;
    }

    const existing = cart.find(item => 
        item.id === selectedProduct.id && 
        item.size === size && 
        JSON.stringify(item.removed) === JSON.stringify(removed) &&
        JSON.stringify(item.extras) === JSON.stringify(extras)
    );

    if (existing) {
        existing.qty += 1;
    } else {
        cart.push({
            id: selectedProduct.id,
            name: selectedProduct.name,
            size: size,
            price: finalPrice,
            weight: weight,
            removed: removed,
            extras: extras,
            qty: 1,
            img: selectedProduct.img || '🥙'
        });
    }

    saveCartToStorage();
    updateCartBadge();
    renderProducts(currentCategory);
    
    // ✅ ОБНОВЛЯЕМ ТОЛЬКО ЦИФРУ В МОДАЛКЕ
    const qtyDisplay = document.getElementById('cartQtyDisplay');
    if (qtyDisplay) {
        // Считаем ВСЕ позиции этого товара в корзине (по id)
        const updatedQty = cart
            .filter(item => item.id === selectedProduct.id)
            .reduce((sum, item) => sum + item.qty, 0);
        qtyDisplay.textContent = updatedQty;
    }
    
    // Сбрасываем галочки
    document.querySelectorAll('.ingredients-remove input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    selectedRemoved = [];
    selectedExtras = [];
}

// ===== ОБНОВЛЕНИЕ ЗНАЧКА КОРЗИНЫ =====
function updateCartBadge() {
    const total = cart.reduce((sum, item) => sum + item.qty, 0);
    document.getElementById('cartCount').textContent = total;
}

// ===== ОТКРЫТИЕ КОРЗИНЫ =====
function openCart() {
    if (cart.length === 0) {
        alert('🛒 Корзина пуста');
        return;
    }

    const modal = document.getElementById('productModal');
    const content = document.getElementById('modalContent');

    let html = `
        <h2 style="margin-bottom:12px;">🛒 Моя корзина</h2>
        <div style="margin-bottom:8px;color:#7a5a9a;font-size:14px;">
            📍 Самовывоз: ул. Большевистская, 151
        </div>
    `;

    let total = 0;
    cart.forEach((item, index) => {
        const itemTotal = item.price * item.qty;
        total += itemTotal;
        const removedText = item.removed.length > 0 ? `без: ${item.removed.join(', ')}` : '';
        const extrasText = item.extras.length > 0 ? `доп: ${item.extras.join(', ')}` : '';
        const details = [removedText, extrasText].filter(t => t).join(' | ');
        html += `
            <div class="cart-item" onclick="openProduct(${item.id}, ${index})">
                <div style="font-size:28px;">${item.img && item.img !== 'nope.jpg' ? '🥙' : '🍽️'}</div>
                <div class="item-info">
                    <h4>${item.name} ${item.size ? `(${item.size})` : ''}</h4>
                    <div class="item-details">${item.weight ? `${item.weight}г` : ''} ${details ? '| ' + details : ''}</div>
                </div>
                <div class="item-qty" onclick="event.stopPropagation();">
                    <button onclick="changeQtyInCart(${index}, -1)">−</button>
                    <span>${item.qty}</span>
                    <button onclick="changeQtyInCart(${index}, 1)">+</button>
                </div>
            </div>
        `;
    });

    const availableTimes = getAvailableTimes();
    let timeOptions = availableTimes.map(t => 
        `<option value="${t}">${t}</option>`
    ).join('');

    html += `
        <div style="margin: 16px 0;">
            <label style="display:block; color:#b39ddb; font-weight:600; margin-bottom:4px;">💬 Комментарий к заказу</label>
            <input type="text" id="orderComment" style="width:100%; padding:12px; border-radius:12px; border:1px solid #2a1a4a; background:#1a132e; color:#f0e6ff; font-size:14px;" placeholder="Например: побольше соуса..." />
        </div>
        <div style="margin: 16px 0;">
            <label style="display:block; color:#b39ddb; font-weight:600; margin-bottom:4px;">🕐 Время получения</label>
            <select id="orderTime" style="width:100%; padding:12px; border-radius:12px; border:1px solid #2a1a4a; background:#1a132e; color:#f0e6ff; font-size:14px;">
                ${timeOptions}
            </select>
        </div>
        <div style="margin: 16px 0;">
            <label style="display:block; color:#b39ddb; font-weight:600; margin-bottom:4px;">💳 Способ оплаты</label>
            <select id="paymentMethod" style="width:100%; padding:12px; border-radius:12px; border:1px solid #2a1a4a; background:#1a132e; color:#f0e6ff; font-size:14px;">
                <option value="наличными при получении">Наличными при получении</option>
                <option value="картой при получении">Картой при получении</option>
            </select>
        </div>
        <div class="cart-total">ИТОГО: ${total} ₽</div>
        <div class="modal-actions">
            <button class="btn-add" onclick="checkout()">✅ Заказать</button>
            <button class="btn-close" onclick="closeModal()">Закрыть</button>
        </div>
    `;

    content.innerHTML = html;
    modal.classList.add('open');
}

// ===== ИЗМЕНЕНИЕ КОЛИЧЕСТВА В КОРЗИНЕ =====
function changeQtyInCart(index, delta) {
    cart[index].qty += delta;
    if (cart[index].qty <= 0) {
        cart.splice(index, 1);
    }
    if (cart.length === 0) {
        closeModal();
        updateCartBadge();
        renderProducts(currentCategory);
        return;
    }
    saveCartToStorage();
    openCart();
    updateCartBadge();
    renderProducts(currentCategory);
}

// ===== ОФОРМЛЕНИЕ ЗАКАЗА =====
function checkout() {
    if (cart.length === 0) {
        alert('Корзина пуста');
        return;
    }

    const comment = document.getElementById('orderComment')?.value || '';
    const time = document.getElementById('orderTime')?.value || 'как можно скорее';
    const payment = document.getElementById('paymentMethod')?.value || 'наличными при получении';

    let orderText = '';
    let total = 0;
    cart.forEach(item => {
        const sum = item.price * item.qty;
        total += sum;
        const removedText = item.removed.length > 0 ? `без: ${item.removed.join(', ')}` : '';
        const extrasText = item.extras.length > 0 ? `доп: ${item.extras.join(', ')}` : '';
        const details = [removedText, extrasText].filter(t => t).join(' | ');
        orderText += `• ${item.name} ${item.size ? `(${item.size})` : ''} × ${item.qty} = ${sum} ₽`;
        if (details) orderText += ` (${details})`;
        orderText += '\n';
    });

    const orderData = {
        items: [...cart],
        total: total,
        comment: comment,
        time: time,
        payment: payment,
        date: new Date().toLocaleString()
    };
    
    const order = {
        id: Date.now(),
        ...orderData
    };
    userOrders.push(order);
    saveOrdersToStorage();

    let botOrderText = `🆕 НОВЫЙ ЗАКАЗ!\n\n`;
    cart.forEach(item => {
        const sum = item.price * item.qty;
        const removedText = item.removed.length > 0 ? `без: ${item.removed.join(', ')}` : '';
        const extrasText = item.extras.length > 0 ? `доп: ${item.extras.join(', ')}` : '';
        const details = [removedText, extrasText].filter(t => t).join(' | ');
        botOrderText += `• ${item.name} ${item.size ? `(${item.size})` : ''} × ${item.qty} = ${sum} ₽`;
        if (details) botOrderText += ` (${details})`;
        botOrderText += '\n';
    });
    botOrderText += `\n💰 Итого: ${total} ₽`;
    botOrderText += `\n📍 Самовывоз: ул. Большевистская, 151`;
    botOrderText += `\n💬 Комментарий: ${comment || 'нет'}`;
    botOrderText += `\n🕐 Получение: ${time}`;
    botOrderText += `\n💳 Оплата: ${payment}`;

    sendOrderToBot(botOrderText);

    alert('✅ Заказ оформлен!\n\n' + botOrderText);

    cart = [];
    saveCartToStorage();
    closeModal();
    updateCartBadge();
    renderProducts(currentCategory);
    
    setTimeout(() => {
        if (confirm('📋 Хотите посмотреть историю ваших заказов?')) {
            showOrderHistory();
        }
    }, 500);
}

function sendOrderToBot(orderText) {
    const payload = JSON.stringify({
        type: 'order',
        order: orderText,
        user_id: currentUserId
    });
    
    // Отправляем на наш сервер
    fetch('/webapp_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('✅ Заказ оформлен!');
        } else {
            alert('❌ Ошибка при оформлении заказа');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('❌ Ошибка при оформлении заказа');
    });
}

// ===== ИСТОРИЯ ЗАКАЗОВ =====
function showOrderHistory() {
    if (userOrders.length === 0) {
        alert('📋 У вас пока нет заказов');
        return;
    }

    const modal = document.getElementById('productModal');
    const content = document.getElementById('modalContent');

    let html = `
        <h2 style="margin-bottom:12px;">📋 Мои заказы</h2>
    `;

    const ordersToShow = [...userOrders].reverse().slice(0, 5);
    ordersToShow.forEach((order, index) => {
        const itemsText = order.items.map(item => 
            `${item.name} ${item.size ? `(${item.size})` : ''} × ${item.qty}`
        ).join(', ');
        html += `
            <div style="background:#1a132e; border-radius:12px; padding:12px; margin-bottom:10px; border:1px solid #2a1a4a;">
                <div style="display:flex; justify-content:space-between; color:#b39ddb; font-size:12px;">
                    <span>#${order.id.toString().slice(-6)}</span>
                    <span>${order.date}</span>
                </div>
                <div style="margin:4px 0;">${itemsText}</div>
                <div style="display:flex; justify-content:space-between; color:#ff4081; font-weight:700;">
                    <span>${order.time}</span>
                    <span>${order.total} ₽</span>
                </div>
            </div>
        `;
    });

    if (userOrders.length > 5) {
        html += `<div style="text-align:center;color:#7a5a9a;font-size:12px;">Показаны последние 5 заказов</div>`;
    }

    html += `
        <div class="modal-actions">
            <button class="btn-close" onclick="closeModal()">Закрыть</button>
        </div>
    `;

    content.innerHTML = html;
    modal.classList.add('open');
}

// ===== КНОПКА ИСТОРИИ ЗАКАЗОВ =====
function addOrderHistoryButton() {
    if (document.getElementById('historyBtn')) return;
    
    const historyBtn = document.createElement('button');
    historyBtn.id = 'historyBtn';
    historyBtn.textContent = '📋';
    historyBtn.title = 'История заказов';
    historyBtn.onclick = showOrderHistory;
    document.body.appendChild(historyBtn);
}