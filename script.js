// script.js - Automated 5 AI Players with Count Display
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

// 2. ካርቴላ ማመንጫ
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

// 3. AI ምርጫ እና የግሪድ ዝግጅት
function initSelection() {
    loadGameState();
    
    // 5 ቦቶች ገና ሲከፈት በራሳቸው እንዲመርጡ
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

    const grid = document.getElementById('slots-grid');
    if(!grid) return;
    grid.innerHTML = "";
    
    for(let i=1; i<=500; i++) {
        let btn = document.createElement('div');
        btn.className = "slot-btn";
        btn.innerText = i;
        
        // AI የመረጣቸው ምልክት እንዲደረግባቸው
        if(selected.includes(i)) {
            btn.classList.add('selected');
            btn.style.borderColor = "var(--orange)";
            btn.style.color = "var(--orange)";
        }
        
        btn.onclick = () => {
            if(selected.includes(i)) {
                selected = selected.filter(x => x !== i);
                btn.classList.remove('selected');
                btn.style.borderColor = "";
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

    let timeLeft = 15;
    const timerEl = document.getElementById('timer');
    const t = setInterval(() => {
        if(timeLeft <= 0) { 
            clearInterval(t); 
            selectionFinished = true;
            saveGameState();
            switchToGame(false); 
        }
        if(timerEl) timerEl.innerText = timeLeft;
        timeLeft--;
    }, 1000);
}

// 4. የተመረጡ ካርቴላዎችን ብዛት እና ዝርዝር ማሳያ
function updatePreview() {
    const bar = document.getElementById('selected-preview-bar');
    if (!bar) return;

    // የቁጥር ማሳያ ክፍል
    let headerHtml = `
        <div style="width: 100%; text-align: center; margin-bottom: 10px; padding: 8px; background: rgba(255, 157, 0, 0.15); border-radius: 10px; border: 1px solid var(--orange);">
            <span style="color: var(--orange); font-weight: 900; font-size: 14px;">
                ጠቅላላ የተመረጡ ካርቴላዎች: ${selected.length}
            </span>
        </div>
    `;

    if (selected.length === 0) {
        bar.innerHTML = headerHtml + '<div style="font-size: 11px; color: #4e6a85; width: 100%; text-align: center; padding-top: 10px;">ምንም አልተመረጠም</div>';
        return;
    }

    bar.innerHTML = headerHtml;
    
    selected.forEach(id => {
        const data = cardData[id];
        let html = `
            <div class="mini-card-detail" style="min-width: 80px; margin-right: 8px; border-color: var(--orange);">
                <div style="font-size: 8px; font-weight: bold; color: var(--orange); margin-bottom: 2px;">ID: #${id}</div>
                <div class="mini-card-header">
                    <span class="cl-b">B</span><span class="cl-i">I</span><span class="cl-n">N</span><span class="cl-g">G</span><span class="cl-o">O</span>
                </div>
                <div class="mini-grid-preview">`;
        for (let r = 0; r < 5; r++) {
            for (let c = 0; c < 5; c++) {
                let val = (r === 2 && c === 2) ? "F" : data[c][r];
                html += `<div class="mini-cell" style="font-size: 7px; padding: 1px 0;">${val}</div>`;
            }
        }
        bar.innerHTML += html + `</div></div>`;
    });
}

// 5. የጨዋታ ገጽ እና AI Auto-Play
function switchToGame(isResume) {
    document.getElementById('selection-page').classList.add('hidden');
    document.getElementById('game-page').classList.remove('hidden');
    
    const area = document.getElementById('active-cards-area');
    area.innerHTML = "";
    
    selected.forEach(id => {
        const data = cardData[id];
        let html = `
            <div class="active-card">
                <div style="font-size: 9px; color: var(--orange); margin-bottom: 4px; font-weight:bold;">CARD #${id}</div>
                <div class="card-grid">`;
        for(let r=0; r<5; r++) {
            for(let c=0; c<5; c++) {
                if(r==2 && c==2) html += `<div class="card-cell hit" style="background:var(--orange); color:#000; font-size:6px">FREE</div>`;
                else {
                    const val = data[c][r];
                    const isHit = calledNumbers.includes(val) ? ' hit" style="background:var(--orange); color:#000"' : '"';
                    html += `<div class="card-cell${isHit} data-val="${val}">${val}</div>`;
                }
            }
        }
        area.innerHTML += html + `</div></div>`;
    });
    
    const board = document.getElementById('game-board');
    board.innerHTML = "";
    for(let r=0; r<15; r++) {
        for(let c=0; c<5; c++) {
            let n = (c * 15) + r + 1;
            const isCalled = calledNumbers.includes(n) ? " called" : "";
            board.innerHTML += `<div class="num-cell${isCalled}" id="bn-${n}">${n}</div>`;
        }
    }
    runEngine();
}

function runEngine() {
    if (engineStarted) return;
    engineStarted = true;

    let allBalls = Array.from({length: 75}, (_, i) => i + 1);
    let remainingBalls = allBalls.filter(b => !calledNumbers.includes(b));

    const engine = setInterval(() => {
        if(isGameOver || remainingBalls.length == 0) return clearInterval(engine);
        
        let n = remainingBalls.splice(Math.floor(Math.random()*remainingBalls.length), 1)[0];
        calledNumbers.push(n);
        saveGameState();
        
        updateBallDisplay(n);
        const cell = document.getElementById(`bn-${n}`);
        if(cell) cell.classList.add('called');

        // AI Auto-Hit logic
        document.querySelectorAll(`[data-val="${n}"]`).forEach(el => {
            el.classList.add('hit');
            el.style.background = "var(--orange)";
            el.style.color = "#000";
        });

        document.getElementById('balls-count').innerText = calledNumbers.length;
        checkWin();
    }, 3000); 
}

function updateBallDisplay(n) {
    let letter = n<=15?'B':n<=30?'I':n<=45?'N':n<=60?'G':'O';
    const colors = {'B':'var(--b-clr)','I':'var(--i-clr)','N':'var(--n-clr)','G':'var(--g-clr)','O':'var(--o-clr)'};
    document.getElementById('ball-num').innerText = n;
    document.getElementById('ball-let').innerText = letter;
    document.getElementById('ball-let').style.color = colors[letter];
}

function checkWin() {
    selected.forEach(id => {
        const data = cardData[id];
        let hits = Array(5).fill().map(() => Array(5).fill(false));
        for(let c=0; c<5; c++) {
            for(let r=0; r<5; r++) {
                if((r==2 && c==2) || calledNumbers.includes(data[c][r])) hits[c][r] = true;
            }
        }
        let win = false;
        for(let i=0; i<5; i++) {
            if(hits[i].every(h => h)) win = true; 
            if(hits.every(col => col[i])) win = true; 
        }
        if([0,1,2,3,4].every(i => hits[i][i]) || [0,1,2,3,4].every(i => hits[i][4-i])) win = true;

        if(win && !isGameOver) {
            isGameOver = true;
            showWinner(id);
        }
    });
}

function showWinner(cardId) {
    localStorage.removeItem('bingo_state_' + userId);
    confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
    document.getElementById('winner-card-num').innerText = "#" + cardId;
    document.getElementById('winner-overlay').classList.remove('hidden');
    
    let count = 5;
    const timer = setInterval(() => {
        count--;
        document.getElementById('reload-timer').innerText = count;
        if(count <= 0) {
            clearInterval(timer);
            location.reload();
        }
    }, 1000);
}

function resetGame() {
    localStorage.removeItem('bingo_state_' + userId);
    location.reload();
}

window.onload = () => {
    initSelection();
    tg.expand();
};
