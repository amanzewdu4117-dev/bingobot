// script.js - Multiplayer Sync Fixed
const firebaseConfig = { 
    apiKey: "AIzaSyD2l0Q4JCedRIshH0vqacqCee0L1qVwN_g", 
    databaseURL: "https://my-app-project-1e0bb-default-rtdb.firebaseio.com" 
};
firebase.initializeApp(firebaseConfig);
const db = firebase.database();
const tg = window.Telegram.WebApp;
const userId = (tg.initDataUnsafe?.user?.id || "dev").toString();

let selected = [], cardData = {}, calledNumbers = [], isGameOver = false, engineStarted = false;
let selectionFinished = false;
let serverOffset = 0; // ሰዓት ለማመሳሰል

// 1. መረጃ መጫኛ
function loadGameState() {
    const saved = localStorage.getItem('bingo_state_' + userId);
    if (saved) {
        const state = JSON.parse(saved);
        selected = state.selected || [];
        cardData = state.cardData || {};
        calledNumbers = state.calledNumbers || [];
        selectionFinished = state.selectionFinished || false;
        return true;
    }
    return false;
}

function saveGameState() {
    localStorage.setItem('bingo_state_' + userId, JSON.stringify({
        selected, cardData, calledNumbers, selectionFinished
    }));
}

// 2. ካርቴላ ማመንጫ (ያለህበት)
function generateCard() {
    let card = [];
    let ranges = [[1,15],[16,30],[31,45],[46,60],[61,75]];
    for(let c=0; c<5; c++) {
        let col = [];
        while(col.length<5) {
            let n = Math.floor(Math.random()*15)+ranges[c][0];
            if(!col.includes(n)) col.push(n);
        }
        card.push(col.sort((a,b)=>a-b));
    }
    return card;
}

// 3. የተመሳሰለ የሰዓት ቆጠራ (Multiplayer Sync)
function initSelection() {
    loadGameState();

    // Firebase Server Time Offset - ለሁሉም እኩል እንዲሆን
    db.ref(".info/serverTimeOffset").on("value", snap => {
        serverOffset = snap.val() || 0;
    });

    if (selected.length === 0) {
        while(selected.length < 5) {
            let randomSlot = Math.floor(Math.random() * 500) + 1;
            if(!selected.includes(randomSlot)) {
                selected.push(randomSlot);
                cardData[randomSlot] = generateCard();
            }
        }
        saveGameState();
    }

    if (selectionFinished) {
        switchToGame(true);
        return;
    }

    // Grid ዝግጅት
    const grid = document.getElementById('slots-grid');
    if(!grid) return;
    grid.innerHTML = "";
    for(let i=1; i<=500; i++) {
        let btn = document.createElement('div');
        btn.className = "slot-btn";
        btn.innerText = i;
        if(selected.includes(i)) btn.classList.add('selected');
        btn.onclick = () => {
            if(selected.includes(i)) {
                selected = selected.filter(x => x !== i);
                btn.classList.remove('selected');
            } else if(selected.length < 10) { 
                selected.push(i);
                cardData[i] = generateCard();
                btn.classList.add('selected');
            }
            updatePreview();
            saveGameState();
        };
        grid.appendChild(btn);
    }
    updatePreview();

    // --- ዋናው ማስተካከያ እዚህ ጋር ነው (Firebase Timer) ---
    db.ref('liveGame/timerStartTime').on('value', snap => {
        let startTime = snap.val();
        if(!startTime) return;

        const timerEl = document.getElementById('timer');
        const t = setInterval(() => {
            let now = Date.now() + serverOffset;
            let diff = Math.floor((now - startTime) / 1000);
            let timeLeft = 15 - diff;

            if(timeLeft <= 0) { 
                clearInterval(t); 
                if(timerEl) timerEl.innerText = "0";
                selectionFinished = true;
                saveGameState();
                switchToGame(false); 
            } else {
                if(timerEl) timerEl.innerText = timeLeft;
            }
        }, 1000);
    });
}

// 4. Preview Update (ያለህበት)
function updatePreview() {
    const bar = document.getElementById('selected-preview-bar');
    if (!bar) return;
    let headerHtml = `<div style="width: 100%; text-align: center; margin-bottom: 10px; padding: 10px; background: rgba(255, 157, 0, 0.2); border-radius: 8px; border: 2px solid var(--orange);"><span style="color: white; font-weight: bold; font-size: 16px;">ጠቅላላ የተመረጡ: ${selected.length}</span></div>`;
    if (selected.length === 0) { bar.innerHTML = headerHtml + '<div style="color: #ccc; text-align: center;">ምንም አልተመረጠም</div>'; return; }
    let cardsHtml = "";
    selected.forEach(id => {
        const data = cardData[id];
        cardsHtml += `<div class="mini-card-detail" style="min-width: 85px; margin-right: 8px; border: 1px solid var(--orange); border-radius: 5px; padding: 5px; background: #1a222c;"><div style="font-size: 9px; font-weight: bold; color: var(--orange); text-align: center;">ID: #${id}</div><div class="mini-grid-preview" style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px; margin-top: 3px;">`;
        for (let r = 0; r < 5; r++) { for (let c = 0; c < 5; c++) {
            let val = (r === 2 && c === 2) ? "F" : data[c][r];
            cardsHtml += `<div style="font-size: 7px; color: white; text-align: center; background: #2c3949;">${val}</div>`;
        }}
        cardsHtml += `</div></div>`;
    });
    bar.innerHTML = headerHtml + `<div style="display: flex; overflow-x: auto; padding-bottom: 5px;">${cardsHtml}</div>`;
}

// 5. ጨዋታ መቀየር (switchToGame)
function switchToGame(isResume) {
    const selectionPage = document.getElementById('selection-page');
    const gamePage
