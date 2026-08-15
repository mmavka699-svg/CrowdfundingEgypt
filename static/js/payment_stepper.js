// ==========================================================================
// Payment Stepper — Vanilla JS single-page navigation (no page reloads).
// The only network call is the final JSON POST that persists the operation.
// Shared by both project donation and wallet top-up views.
// ==========================================================================
(function () {
    'use strict';

    var stepper = document.getElementById('donStepper');
    if (!stepper) return; // eligibility block shown instead

    var postUrl = stepper.dataset.donateUrl || stepper.dataset.chargeUrl;
    var redirectUrl = stepper.dataset.projectUrl || stepper.dataset.profileUrl;
    var profileUrl = stepper.dataset.profileUrl;
    var maxAmount = stepper.dataset.maxAmount ? Number(stepper.dataset.maxAmount) : null;

    // Preset quick-select amounts. Currency is "EGP".
    var PRESETS = stepper.dataset.presets ? stepper.dataset.presets.split(',').map(Number) : [25, 50, 100, 250, 500, 1000];
    var CURRENCY = 'EGP';

    var panels = document.querySelectorAll('.don-panel');
    var steps  = document.querySelectorAll('#donProgress li');

    // Persistent flow state
    var state = {
        amount: '',
        method: null,
        secondaryMethod: null,
        cardName: '', cardNumber: '', cardExpiry: '', cardCvv: '',
        redirect: null
    };

    // ------------------------------------------------------------------
    // Tiny DOM helpers
    // ------------------------------------------------------------------
    function el(id) { return document.getElementById(id); }

    function showError(id, message) {
        var box = el(id);
        if (!box) return;
        box.textContent = message || '';
        box.classList.toggle('d-none', !message);
    }
    function clearError(id) { showError(id, ''); }

    // Number formatter: 1234567.5 -> "1,234,567.5"
    function formatNumber(value) {
        var str = String(value).replace(/[^0-9.]/g, '');
        if (!str) return '';
        var parts = str.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return parts.join('.');
    }
    function unformatNumber(value) {
        return String(value).replace(/[^0-9.]/g, '');
    }

    // ------------------------------------------------------------------
    // Step navigation
    // ------------------------------------------------------------------
    function goToStep(target) {
        // Hide every panel, reveal only the target one
        panels.forEach(function (panel) {
            panel.classList.toggle('active', panel.dataset.panel === String(target));
        });

        // Update progress indicator
        var cardSkipped = state.method !== 'card' && state.secondaryMethod !== 'card';   // step 3 only used for cards
        steps.forEach(function (li) {
            var n = Number(li.dataset.step);
            li.classList.remove('active', 'done', 'skipped');
            if (n === target) {
                li.classList.add('active');
            } else if (n < target) {
                li.classList.add('done');
            } else if (n === 3 && cardSkipped) {
                li.classList.add('skipped');
            }
        });

        // Focus management per step
        if (target === 4) {
            var pwd = document.getElementById('donPasswordInput');
            if (pwd) pwd.focus();
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function nextFromPayment() {
        // Card method -> card-details step; wallet methods -> straight to PIN
        goToStep(state.method === 'card' || state.secondaryMethod === 'card' ? 3 : 4);
    }

    // ------------------------------------------------------------------
    // STEP 1 — Amount (+) presets
    // ------------------------------------------------------------------
    var presetsBox = el('donPresets');
    if (presetsBox) {
        PRESETS.forEach(function (value) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'don-preset';
            btn.textContent = CURRENCY + ' ' + value;
            btn.setAttribute('data-value', value);
            presetsBox.appendChild(btn);
        });

        var presetBtns = presetsBox.querySelectorAll('.don-preset');
        function setActivePreset(cleanValue) {
            presetBtns.forEach(function (btn) {
                btn.classList.toggle('active', btn.dataset.value === cleanValue);
            });
        }
        presetBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var amountInput = el('donAmountInput');
                amountInput.value = btn.dataset.value;
                setActivePreset(btn.dataset.value);
                amountInput.focus();
            });
        });
    }

    var amountInput = el('donAmountInput');
    if (amountInput) {
        amountInput.addEventListener('input', function () {
            this.value = formatNumber(this.value);
            if(typeof setActivePreset === 'function') setActivePreset(unformatNumber(this.value));
        });
    }

    var donAmountNext = el('donAmountNext');
    if (donAmountNext) {
        donAmountNext.addEventListener('click', function () {
            var raw = unformatNumber(amountInput.value);
            state.amount = raw;

            var error = '';
            var val = Number(raw);
            if (!val || val <= 0) {
                error = 'Please enter an amount greater than zero.';
            } else if (maxAmount !== null && val > maxAmount) {
                error = 'This project only needs ' + formatNumber(maxAmount) + ' ' + CURRENCY + ' more to reach its goal.';
            }
            if (error) {
                showError('donAmountError', error);
                amountInput.focus();
                return;
            }
            clearError('donAmountError');
            goToStep(2);
        });
    }

    // ------------------------------------------------------------------
    // STEP 2 — Payment method
    // ------------------------------------------------------------------
    var methodLabels = document.querySelectorAll('.don-method');
    var addCardBtn = el('donAddCardBtn');

    methodLabels.forEach(function (label) {
        label.addEventListener('click', function () {
            methodLabels.forEach(function (l) { l.classList.remove('active'); });
            label.classList.add('active');
            state.method = label.dataset.method;
            clearError('donMethodError');
        });
    });

    if (addCardBtn) {
        addCardBtn.addEventListener('click', function () {
            state.method = 'card';
            methodLabels.forEach(function (l) { l.classList.remove('active'); });
            var cardEl = document.querySelector('.don-method[data-method="card"]');
            if (cardEl) cardEl.classList.add('active');
            goToStep(3);
        });
    }

    var methodNext = el('donMethodNext');
    if (methodNext) {
        methodNext.addEventListener('click', function () {
            if (!state.method) {
                showError('donMethodError', 'Please select a payment method to continue.');
                return;
            }
            clearError('donMethodError');

            if (state.method === 'wallet') {
                var walletBal = Number(stepper.dataset.walletBalance || 0);
                var amount = Number(state.amount);
                if (walletBal >= amount) {
                    state.secondaryMethod = null;
                    goToStep(4);
                    return;
                } else if (walletBal > 0) {
                    state.method = 'wallet_split';
                    state.secondaryMethod = 'card';
                    var notice = el('donSplitNotice');
                    if (notice) notice.classList.remove('d-none');
                    if(el('donSplitWalletAmount')) el('donSplitWalletAmount').textContent = formatNumber(walletBal);
                    if(el('donSplitCardAmount')) el('donSplitCardAmount').textContent = formatNumber(amount - walletBal);
                    goToStep(3);
                    return;
                } else {
                    showError('donMethodError', 'Your wallet is empty. Please select another payment method.');
                    return;
                }
            } else {
                var notice = el('donSplitNotice');
                if (notice) notice.classList.add('d-none');
                state.secondaryMethod = null;
                nextFromPayment();
            }
        });
    }

    // ------------------------------------------------------------------
    // STEP 3 — Card details + live preview
    // ------------------------------------------------------------------
    var cardNameInput = el('donCardNameInput');
    var cardNumberInput = el('donCardNumberInput');
    var cardExpiryInput = el('donCardExpiryInput');
    var cardCvvInput = el('donCardCvvInput');

    function formatCardNumber(value) {
        return value.replace(/\D/g, '').slice(0, 19)
                    .replace(/(.{4})/g, '$1 ').trim();
    }
    function formatExpiry(value) {
        var digits = value.replace(/\D/g, '').slice(0, 4);
        return digits.length > 2 ? digits.slice(0, 2) + '/' + digits.slice(2) : digits;
    }

    if (cardNameInput) {
        cardNameInput.addEventListener('input', function () {
            state.cardName = this.value.toUpperCase();
            if(el('donCardName')) el('donCardName').textContent = state.cardName || 'YOUR NAME';
        });
    }
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function () {
            state.cardNumber = this.value.replace(/\D/g, '');
            this.value = formatCardNumber(state.cardNumber);
            var display = state.cardNumber.replace(/.(?=.{4})/g, '•').replace(/(.{4})/g, '$1 ').trim();
            if(el('donCardNum')) el('donCardNum').textContent = display.length ? display : '•••• •••• •••• ••••';
        });
    }
    if (cardExpiryInput) {
        cardExpiryInput.addEventListener('input', function () {
            state.cardExpiry = this.value;
            this.value = formatExpiry(this.value);
            if(el('donCardExpiry')) el('donCardExpiry').textContent = this.value || 'MM/YY';
        });
    }
    if (cardCvvInput) {
        cardCvvInput.addEventListener('input', function () {
            this.value = this.value.replace(/\D/g, '').slice(0, 4);
            state.cardCvv = this.value;
        });
    }

    var donCardNext = el('donCardNext');
    if (donCardNext) {
        donCardNext.addEventListener('click', function () {
            var error = '';
            if (state.cardName.trim().length < 2) {
                error = 'Please enter the cardholder name.';
            } else if (state.cardNumber.length < 13) {
                error = 'Please enter a valid card number.';
            } else if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(state.cardExpiry)) {
                error = 'Expiry date must be in MM/YY format.';
            } else if (cardCvvInput.value.length < 3) {
                error = 'CVV must be 3 or 4 digits.';
            }

            if (error) { showError('donCardError', error); return; }
            clearError('donCardError');
            goToStep(4);
        });
    }

    // Back from PIN: return to the card step if a card was chosen, else to payment
    var donPinBack = el('donPinBack');
    if (donPinBack) {
        donPinBack.addEventListener('click', function () {
            goToStep(state.method === 'card' || state.secondaryMethod === 'card' ? 3 : 2);
        });
    }

    // ------------------------------------------------------------------
    // Back buttons (data-back target)
    // ------------------------------------------------------------------
    document.querySelectorAll('.don-back[data-back]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            goToStep(Number(btn.dataset.back));
        });
    });

    // ------------------------------------------------------------------
    // STEP 4 — Password entry
    // ------------------------------------------------------------------
    function getPasswordValue() {
        var input = el('donPasswordInput');
        return input ? input.value : '';
    }

    // ------------------------------------------------------------------
    // STEP 4 -> submit the operation (single AJAX POST creates the record)
    // ------------------------------------------------------------------
    var confirmBtn = el('donConfirm');
    var confirmText = el('donConfirmText');
    var spinner = el('donSpinner');

    function setConfirmLoading(loading) {
        if(confirmBtn) confirmBtn.disabled = loading;
        if(confirmText) confirmText.classList.toggle('d-none', loading);
        if(spinner) spinner.classList.toggle('d-none', !loading);
    }

    if (confirmBtn) {
        confirmBtn.addEventListener('click', function () {
            var pwd = getPasswordValue();
            if (!pwd) {
                showError('donError', 'Please enter your password to confirm.');
                var pwdInput = el('donPasswordInput');
                if (pwdInput) pwdInput.focus();
                return;
            }
            clearError('donError');

            setConfirmLoading(true);

            var payload = {
                amount: state.amount,
                payment_method: state.method,
                password: pwd
            };
            // Card details travel only when a card is being used
            if (state.method === 'card' || state.secondaryMethod === 'card') {
                payload.card_name = state.cardName;
                payload.card_number = state.cardNumber;
                payload.card_expiry = state.cardExpiry;
                if(cardCvvInput) payload.card_cvv = cardCvvInput.value;
                if (state.secondaryMethod) {
                    payload.secondary_payment_method = state.secondaryMethod;
                }
            }

            var csrf = el('donCsrfToken');

            fetch(postUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf ? csrf.value : '',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(payload)
            })
                .then(function (response) { return response.json(); })
                .then(function (result) {
                    setConfirmLoading(false);
                    if (result.success) {
                        state.redirect = result.redirect_url || redirectUrl;
                        if(el('donSuccessAmount')) el('donSuccessAmount').textContent = result.amount + ' ' + CURRENCY;
                        if(el('donSuccessTitle')) el('donSuccessTitle').textContent = result.project_title || '';
                        goToStep(5);
                    } else {
                        showError('donError', result.error || 'Something went wrong. Please try again.');
                    }
                })
                .catch(function () {
                    setConfirmLoading(false);
                    showError('donError', 'Network error — please check your connection and try again.');
                });
        });
    }

    // ------------------------------------------------------------------
    // STEP 5 — Success actions
    // ------------------------------------------------------------------
    var donOkBtn = el('donOkBtn');
    if (donOkBtn) {
        donOkBtn.addEventListener('click', function () {
            window.location.href = state.redirect || redirectUrl;
        });
    }

    var profileLink = el('donProfileLink');
    if (profileLink && profileUrl) {
        profileLink.setAttribute('href', profileUrl + '#donationsTab');
    }

    // Kick off the flow on the amount step
    goToStep(1);
})();