/**
 * Game UI — Virtual keyboard + tile preview for Guess the Word
 */
(function () {
    'use strict';

    const guessInput = document.querySelector('.guess-input');
    const guessForm = document.getElementById('guessForm');
    const tiles = [
        document.getElementById('c0'),
        document.getElementById('c1'),
        document.getElementById('c2'),
        document.getElementById('c3'),
        document.getElementById('c4'),
    ];

    if (!guessInput) return; // game is complete, nothing to do

    // --- Input synchronisation ---
    guessInput.addEventListener('input', function () {
        const val = this.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 5);
        this.value = val;
        tiles.forEach((tile, i) => {
            if (!tile) return;
            if (i < val.length) {
                tile.textContent = val[i];
                tile.classList.add('has-letter');
            } else {
                tile.textContent = '';
                tile.classList.remove('has-letter');
            }
        });
    });

    // Hide the real input visually (keyboard-driven) but keep accessible
    guessInput.style.cssText = 'position:absolute;opacity:0;pointer-events:none;width:1px;height:1px;';
    guessInput.setAttribute('aria-hidden', 'true');

    // Focus the input so keyboard events land on it
    guessInput.focus();

    // --- Virtual keyboard ---
    document.querySelectorAll('.key[data-letter]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const letter = this.dataset.letter;
            if (guessInput.value.length < 5) {
                guessInput.value += letter;
                guessInput.dispatchEvent(new Event('input'));
            }
        });
    });

    const keyBackspace = document.getElementById('keyBackspace');
    if (keyBackspace) {
        keyBackspace.addEventListener('click', function () {
            guessInput.value = guessInput.value.slice(0, -1);
            guessInput.dispatchEvent(new Event('input'));
        });
    }

    const keyEnter = document.getElementById('keyEnter');
    if (keyEnter) {
        keyEnter.addEventListener('click', function () {
            if (guessInput.value.length === 5) {
                guessForm.submit();
            }
        });
    }

    // Physical keyboard still works too
    document.addEventListener('keydown', function (e) {
        if (e.ctrlKey || e.altKey || e.metaKey) return;
        if (e.key === 'Enter' && guessInput.value.length === 5) {
            guessForm.submit();
        } else if (e.key === 'Backspace') {
            guessInput.value = guessInput.value.slice(0, -1);
            guessInput.dispatchEvent(new Event('input'));
        } else if (/^[a-zA-Z]$/.test(e.key) && guessInput.value.length < 5) {
            guessInput.value += e.key.toUpperCase();
            guessInput.dispatchEvent(new Event('input'));
        }
    });

    // --- Colour the virtual keyboard from existing guesses ---
    // Reads guess rows that have been revealed and marks keys accordingly
    // Priority: green > orange > grey
    const priority = { green: 3, orange: 2, grey: 1 };
    const keyMap = {};

    document.querySelectorAll('.guess-row').forEach(function (row) {
        const filledTiles = row.querySelectorAll('.tile.filled, .tile.green, .tile.orange, .tile.grey');
        filledTiles.forEach(function (tile) {
            const letter = tile.textContent.trim();
            if (!letter) return;
            let colour = null;
            if (tile.classList.contains('green')) colour = 'green';
            if (tile.classList.contains('orange')) colour = 'orange';
            if (tile.classList.contains('grey')) colour = 'grey';
            if (!colour) return;
            if (!keyMap[letter] || priority[colour] > priority[keyMap[letter]]) {
                keyMap[letter] = colour;
            }
        });
    });

    Object.entries(keyMap).forEach(function ([letter, colour]) {
        const btn = document.querySelector(`.key[data-letter="${letter}"]`);
        if (btn) btn.classList.add(colour);
    });

})();
