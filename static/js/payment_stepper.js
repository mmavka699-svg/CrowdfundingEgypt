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
        var cardSkipped = (state.method !== 'card' && state.secondaryMethod !== 'card' && state.method !== 'wallet_split') || (state.method && state.method.startsWith('saved_card_'));   // step 3 only used for new cards
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
            prepareVerifyStep();
            var focusId = state.method === 'wallet' ? 'donPasswordInput'
                        : (state.method === 'card' || state.secondaryMethod === 'card') ? 'donOtpInput'
                        : (state.method === 'paypal' ? 'donPpEmail' : 'donBioConfirm');
            var focusEl = document.getElementById(focusId);
            if (focusEl && focusEl.focus) focusEl.focus();
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function nextFromPayment() {
        // Card method -> card-details step; wallet handled in methodNext; everything
        // else (gateways, saved cards) -> straight to the Verify step (they render their provider sheet there)
        if (state.method === 'card' || state.secondaryMethod === 'card') {
            goToStep(3);
        } else {
            goToStep(4);
        }
    }

    // ------------------------------------------------------------------
    // STEP 4 — reveal the right verify control:
    //   wallet  -> password | card/split -> 3-D Secure OTP | gateways -> provider sheet
    // ------------------------------------------------------------------
    function prepareVerifyStep() {
        var passWrap   = el('donVerifyPassword');
        var otpWrap    = el('donVerifyOtp');
        var gwWrap     = el('donVerifyGateway');
        var bioSheet   = el('donBioSheet');
        var paypalPop  = el('donPaypalPopup');
        var verifyActions = document.querySelector('.don-panel[data-panel="4"] .don-actions');

        if (passWrap) passWrap.style.display = 'none';
        if (otpWrap)  otpWrap.style.display  = 'none';
        if (gwWrap)   gwWrap.style.display   = 'none';

        if (verifyActions) {
            if (state.method === 'paypal') {
                verifyActions.style.display = 'none';
            } else {
                verifyActions.style.display = '';
            }
        }

        if (state.method === 'wallet') {
            if (el('donVerifyTitle')) el('donVerifyTitle').textContent = 'Verify Password';
            if (el('donVerifySub')) el('donVerifySub').textContent = '';
            if (passWrap) passWrap.style.display = 'block';
        } else if (state.method === 'card' || state.secondaryMethod === 'card' || (state.method && state.method.startsWith('saved_card_'))) {
            if (el('donVerifyTitle')) el('donVerifyTitle').textContent = 'Bank Confirmation';
            if (el('donVerifySub')) el('donVerifySub').textContent = '';
            if (otpWrap) otpWrap.style.display = 'block';
        } else {
            // Gateway (PayPal / Google Pay / Apple Pay)
            if (el('donVerifyTitle')) el('donVerifyTitle').textContent = 'Complete Your Payment';
            if (el('donVerifySub')) el('donVerifySub').textContent = '';
            if (gwWrap) gwWrap.style.display = 'block';
            setupGatewaySheet();
        }
    }

    // ------------------------------------------------------------------
    // STEP 4 — gateway sheet (PayPal / Google Pay / Apple Pay)
    // The user approves inside a simulated provider sheet/popup that lives
    // right in the Verify panel (same place as the OTP), a token is returned,
    // and the operation is submitted immediately -> success.
    // ------------------------------------------------------------------
    var GATEWAY_META = {
        paypal:     { name: 'PayPal',     icon: 'fa-paypal' },
        google_pay: { name: 'Google Pay', icon: 'fa-google-pay' },
        apple_pay:  { name: 'Apple Pay',  icon: 'fa-apple-pay' }
    };

    var bioSheetEl = el('donBioSheet');
    var paypalPopupEl = el('donPaypalPopup');

    function isGatewayMethod(m) {
        return m === 'paypal' || m === 'google_pay' || m === 'apple_pay';
    }

    function setupGatewaySheet() {
        var meta = GATEWAY_META[state.method] || { name: 'Provider', icon: 'fa-brands' };

        if (state.method === 'paypal') {
            if (bioSheetEl) bioSheetEl.style.display = 'none';
            if (paypalPopupEl) paypalPopupEl.style.display = 'block';
            if (el('donPpAmount')) el('donPpAmount').textContent = CURRENCY + ' ' + formatNumber(state.amount);
        } else {
            if (bioSheetEl) {
                bioSheetEl.style.display = 'block';
                if (el('donBioIcon')) el('donBioIcon').className = 'fa-brands ' + meta.icon + ' don-sheet-sym';
                if (el('donBioBrand')) el('donBioBrand').textContent = meta.name;
                if (el('donBioAmount')) el('donBioAmount').textContent = CURRENCY + ' ' + formatNumber(state.amount);
                if (el('donBioSecured')) el('donBioSecured').textContent =
                    state.method === 'google_pay' ? 'Google Pay' : 'Apple / Google';
                if (el('donBioSub')) el('donBioSub').textContent =
                    'Authenticate with Face ID or Touch ID to confirm this payment via ' + meta.name + '.';
            }
            if (paypalPopupEl) paypalPopupEl.style.display = 'none';
        }

        var first = state.method === 'paypal' ? el('donPpEmail') : el('donBioConfirm');
        if (first && first.focus) first.focus();
    }

    function gatewayLoading(id, loading, label) {
        var btn = el(id);
        if (!btn) return;
        btn.disabled = loading;
        if (loading) {
            btn.setAttribute('data-orig', btn.innerHTML);
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> ' +
                (label || 'Approving…');
        } else {
            btn.innerHTML = btn.getAttribute('data-orig') || btn.innerHTML;
        }
    }

    function submitGateway(approvalId, approved) {
        clearError(approvalId);
        if (!approved) {
            showError(approvalId, 'The payment was not approved by the provider. Please approve first.');
            return;
        }
        var btnId = approvalId === 'donBioError' ? 'donBioConfirm' : 'donPpApprove';
        gatewayLoading(btnId, true, approvalId === 'donBioError' ? 'Authenticating…' : 'Approving…');
        var payload = {
            amount: state.amount,
            payment_method: state.method,
            gateway_token: 'sim_' + state.method + '_approved'
        };
        // Small artificial delay so the biometric / login step feels real before the POST.
        setTimeout(function () { submitPayment(payload, approvalId); }, 900);
    }

    // Biometric sheet: Tap to "authenticate" with Face ID / Touch ID.
    if (el('donBioConfirm')) {
        el('donBioConfirm').addEventListener('click', function () {
            submitGateway('donBioError', true);
        });
    }
    // PayPal popup: "Log In & Approve" -> provider returns token.
    if (el('donPpApprove')) {
        el('donPpApprove').addEventListener('click', function () {
            var emailInput = el('donPpEmail'), passInput = el('donPpPass');
            if ((emailInput && !emailInput.value.trim()) || (passInput && !passInput.value.trim())) {
                showError('donPpError', 'Please sign in with your PayPal credentials to approve this payment.');
                var foc = !emailInput.value.trim() ? emailInput : passInput;
                if (foc && foc.focus) foc.focus();
                return;
            }
            submitGateway('donPpError', true);
        });
    }
    // Back out of the sheet to the payment-method step.
    [el('donBioCancel'), el('donPpCancel'), el('donPpClose')].forEach(function (btn) {
        if (btn) btn.addEventListener('click', function () { goToStep(2); });
    });

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
    // Shared submit: single AJAX POST persists the operation for every path
    // (wallet password / card OTP in the stepper, gateway token in the modal).
    // ------------------------------------------------------------------
    var confirmBtn = el('donConfirm');
    var confirmText = el('donConfirmText');
    var spinner = el('donSpinner');

    function setConfirmLoading(loading) {
        if(confirmBtn) confirmBtn.disabled = loading;
        if(confirmText) confirmText.classList.toggle('d-none', loading);
        if(spinner) spinner.classList.toggle('d-none', !loading);
    }

    function submitPayment(payload, errorBox) {
        errorBox = errorBox || 'donError';
        setConfirmLoading(true);
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
                gatewayLoading('donBioConfirm', false);
                gatewayLoading('donPpApprove', false);

                if (result.success) {
                    state.redirect = result.redirect_url || redirectUrl;
                    if(el('donSuccessAmount')) el('donSuccessAmount').textContent = result.amount + ' ' + CURRENCY;
                    if(el('donSuccessTitle')) el('donSuccessTitle').textContent = result.project_title || '';
                    goToStep(5);
                } else {
                    showError(errorBox, result.error || 'Something went wrong. Please try again.');
                }
            })
            .catch(function () {
                setConfirmLoading(false);
                gatewayLoading('donBioConfirm', false);
                gatewayLoading('donPpApprove', false);
                showError(errorBox, 'Network error — please check your connection and try again.');
            });
    }

if (confirmBtn) {
        confirmBtn.addEventListener('click', function () {
            var isCardFlow = state.method === 'card' || state.secondaryMethod === 'card';
            var isSavedCardFlow = state.method && state.method.startsWith('saved_card_');

            var payload = {
                amount: state.amount,
                payment_method: isSavedCardFlow ? 'saved_card' : state.method
            };
            
            if (isSavedCardFlow) {
                payload.saved_card_id = state.method.replace('saved_card_', '');
            }

            if (state.method === 'wallet') {
                var pwd = getPasswordValue();
                if (!pwd) {
                    showError('donError', 'Please enter your password to confirm.');
                    var pwInput = el('donPasswordInput');
                    if (pwInput) pwInput.focus();
                    return;
                }
                payload.password = pwd;
            } else if (isCardFlow || isSavedCardFlow) {
                var otpInput = el('donOtpInput');
                var otpValue = otpInput ? otpInput.value.trim() : '';
                if (otpValue !== '123456') {
                    showError('donError', 'Invalid confirmation code. Please enter the 6-digit code sent to your phone (Demo: 123456).');
                    if (otpInput) otpInput.focus();
                    return;
                }
                payload.otp = otpValue;
            }

            clearError('donError');

            // Card details travel only when a card is being used
            if (isCardFlow) {
                payload.card_name = state.cardName;
                payload.card_number = state.cardNumber;
                payload.card_expiry = state.cardExpiry;
                if(cardCvvInput) payload.card_cvv = cardCvvInput.value;
                if (state.secondaryMethod) {
                    payload.secondary_payment_method = state.secondaryMethod;
                }
                
                var saveCardCheck = el('donSaveCardCheck');
                if (saveCardCheck && saveCardCheck.checked) {
                    payload.save_card = true;
                }
            }

            submitPayment(payload, 'donError');
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