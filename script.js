// script.js ፋይል ውስጥ የሚገባ ኮድ

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

// 1. Game Reset logic
function resetGame() {
    localStorage.removeItem('bingo_state_' + userId);
    location.reload();
}

// 2. State Management
function saveGameState() {
    localStorage.setItem('bingo_state_' + userId, JSON.stringify({
        selected, cardData, calledNumbers, selectionFinished
    }));
}

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

// 3. AI Engine: በራሳቸው እንዲጫወቱ የሚያደርገው
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
        
        const boardCell = document.getElementById(`bn-${n}`);
        if(boardCell) boardCell.classList.add('called');

        // --- AI AUTO-PLAY LOGIC ---
        // ይህ ክፍል ነው ቦቶቹ በራሳቸው እንዲመቱ የሚያደርገው
        const targetCells = document.querySelectorAll(`[data-val="${n}"]`);
        targetCells.forEach(cell => {
            cell.classList.add('hit'); 
            cell.style.backgroundColor = "#ff9d00"; 
            cell.style.color = "#000";
        });

        document.getElementById('balls-count').innerText = calledNumbers.length;
        checkWin();
    }, 3000); 
}

function checkWin() {
    if (selected.length === 0) return;
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

function updateBallDisplay(n) {
    let letter = n<=15?'B':n<=30?'I':n<=45?'N':n<=60?'G':'O';
    const colors = {'B':'#00d2ff','I':'#9d50bb','N':'#ff3e3e','G':'#00ff85','O':'#ffae00'};
    const bNum = document.getElementById('ball-num');
    const bLet = document.getElementById('ball-let');
    if(bNum && bLet) {
        bNum.innerText = n;
        bLet.innerText = letter;
        bLet.style.color = colors[letter];
    }
}

function showWinner(cardId) {
    localStorage.removeItem('bingo_state_' + userId);
    if(typeof confetti === 'function') confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
    const winOverlay = document.getElementById('winner-overlay');
    const winCardNum = document.getElementById('winner-card-num');
    if(winOverlay && winCardNum) {
        winCardNum.innerText = "#" + cardId;
        winOverlay.classList.remove('hidden');
    }
    
    let count = 5;
    const timer = setInterval(() => {
        count--;
        const relTimer = document.getElementById('reload-timer');
        if(relTimer) relTimer.innerText = count;
        if(count <= 0) {
            clearInterval(timer);
            location.reload();
        }
    }, 1000);
}

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

function initSelection() {
    loadGameState();
    if (selectionFinished) {
        switchToGame(true);
        return;
    }

    const grid = document.getElementById('slots-grid');
    if(!grid) return;
    
    for(let i=1; i<=500; i++) {
        let btn = document.createElement('div');
        btn.className = "slot-btn";
        btn.innerText = i;
        if(selected.includes(i)) btn.classList.add('selected');
        
        btn.onclick = () => {
            if(selected.includes(i)) {
                selected = selected.filter(x => x !== i);
                btn.classList.remove('selected');
            } else if(selected.length < 3) {
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
    if(timerEl) {
        const t = setInterval(() => {
            timeLeft--; 
            timerEl.innerText = timeLeft;
            if(timeLeft <= 0) { 
                clearInterval(t); 
                selectionFinished = true;
                saveGameState();
                switchToGame(false); 
            }
        }, 1000);
    }
}

function updatePreview() {
    const bar = document.getElementById('selected-preview-bar');
    if (!bar) return;
    if (selected.length === 0) {
        bar.innerHTML = '<div style="font-size: 11px; color: #4e6a85; width: 100%; text-align: center; padding-top: 20px;">ካርቴላ ሲመርጡ ዝርዝሩ እዚህ ይታያል</div>';
        return;
    }
    bar.innerHTML = "";
    selected.forEach(id => {
        const data = cardData[id];
        let html = `
            <div class="mini-card-detail">
                <div style="font-size: 8px; font-weight: bold; color: #778899; margin-bottom: 2px;">#${id}</div>
                <div class="mini-card-header">
                    <span style="color:#00d2ff">B</span><span style="color:#9d50bb">I</span><span style="color:#ff3e3e">N</span><span style="color:#00ff85">G</span><span style="color:#ffae00">O</span>
                </div>
                <div class="mini-grid-preview">`;
        for (let r = 0; r < 5; r++) {
            for (let c = 0; c < 5; c++) {
                let val = (r === 2 && c === 2) ? "F" : data[c][r];
                html += `<div class="mini-cell">${val}</div>`;
            }
        }
        bar.innerHTML += html + `</div></div>`;
    });
}

function switchToGame(isResume) {
    const selPage = document.getElementById('selection-page');
    const gamePage = document.getElementById('game-page');
    if(selPage) selPage.classList.add('hidden');
    if(gamePage) gamePage.classList.remove('hidden');
    
    const area = document.getElementById('active-cards-area');
    if(area) {
        area.innerHTML = "";
        selected.forEach(id => {
            const data = cardData[id];
            let html = `
                <div class="active-card">
                    <div style="font-size: 8px; color: #556677; margin-bottom: 4px;">CARD #${id}</div>
                    <div class="card-header-letters">
                        <div style="color:#00d2ff">B</div><div style="color:#9d50bb">I</div><div style="color:#ff3e3e">N</div><div style="color:#00ff85">G</div><div style="color:#ffae00">O</div>
                    </div>
                    <div class="card-grid">`;
            for(let r=0; r<5; r++) {
                for(let c=0; c<5; c++) {
                    if(r==2 && c==2) html += `<div class="card-cell hit" style="font-size:6px; background:#ff9d00; color:#000">FREE</div>`;
                    else {
                        const val = data[c][r];
                        const isHit = calledNumbers.includes(val) ? ' hit" style="background:#ff9d00; color:#000"' : '"';
                        html += `<div class="card-cell${isHit} data-val="${val}">${val}</div>`;
                    }
                }
            }
            area.innerHTML += html + `</div></div>`;
        });
    }
    
    const board = document.getElementById('game-board');
    if(board) {
        board.innerHTML = "";
        for(let r=0; r<15; r++) {
            for(let c=0; c<5; c++) {
                let n = (c * 15) + r + 1;
                const isCalled = calledNumbers.includes(n) ? " called" : "";
                board.innerHTML += `<div class="num-cell${isCalled}" id="bn-${n}">${n}</div>`;
            }
        }
    }
    runEngine();
}

window.onload = () => {
    initSelection();
    tg.expand();
};
