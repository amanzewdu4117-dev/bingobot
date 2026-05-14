// script.js - Full Automated AI Version (With 5 AI Players)
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

// 3. AI ምርጫ (5 AI ተጫዋቾች በራሳቸው እንዲመርጡ)
function initSelection() {
    loadGameState();
    
    // 5 ቦቶች ገና ሲከፈት በራሳቸው እንዲመርጡ
    if (selected.length === 0) {
        while(selected.length < 5) { // እዚህ ጋር ነው 5 የተደረገው
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
        
        // AI የመረጣቸው በቢጫ እንዲታዩ
        if(selected.includes(i)) {
            btn.classList.add('selected');
            btn.style.backgroundColor = "#ffae00"; 
            btn.style.color = "#000";
        }
        
        btn.onclick = () => {
            if(selected.includes(i)) {
                selected = selected.filter(x => x !== i);
                btn.classList.remove('selected');
                btn.style.backgroundColor = "";
            } else if(selected.length < 10) { // አንተም እስከ 5 ካርቴላ መጨመር ትችላለህ
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

    let timeLeft = 10;
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

// 4. የጨዋታ ገጽ ሽግግር
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
                    <div style="font-size: 9px; color: #ffae00; margin-bottom: 4px; font-weight:bold;">AI CARD #${id}</div>
                    <div class="card-grid">`;
            for(let r=0; r<5; r++) {
                for(let c=0; c<5; c++) {
                    if(r==2 && c==2) html += `<div class="card-cell hit" style="background:#ffae00; color:#000">FREE</div>`;
                    else {
                        const val = data[c][r];
                        const isHit = calledNumbers.includes(val) ? ' hit" style="background:#ffae00; color:#000"' : '"';
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
        for(let n=1; n<=75; n++) {
            const isCalled = calledNumbers.includes(n) ? " called" : "";
            board.innerHTML += `<div class="num-cell${isCalled}" id="bn-${n}">${n}</div>`;
        }
    }
    runEngine();
}

// 5. AI Auto-Play Engine
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

        // AI Auto-Hit: ሁሉም ቦቶች በራሳቸው ቁጥራቸውን ይመታሉ
        const targetCells = document.querySelectorAll(`[data-val="${n}"]`);
        targetCells.forEach(cell => {
            cell.classList.add('hit'); 
            cell.style.backgroundColor = "#ffae00"; 
            cell.style.color = "#000";
        });

        if(document.getElementById('balls-count')) 
            document.getElementById('balls-count').innerText = calledNumbers.length;
        
        checkWin();
    }, 3000); 
}

function updateBallDisplay(n) {
    let letter = n<=15?'B':n<=30?'I':n<=45?'N':n<=60?'G':'O';
    const bNum = document.getElementById('ball-num');
    const bLet = document.getElementById('ball-let');
    if(bNum) bNum.innerText = n;
    if(bLet) bLet.innerText = letter;
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
            alert("BINGO! AI Card #" + id + " Won!");
            localStorage.removeItem('bingo_state_' + userId);
            location.reload();
        }
    });
}

function updatePreview() {
    const bar = document.getElementById('selected-preview-bar');
    if (!bar) return;
    bar.innerHTML = "";
    selected.forEach(id => {
        bar.innerHTML += `<div style="display:inline-block; margin:5px; padding:5px; background:#1a2b3c; border-radius:5px; font-size:10px;">AI Card #${id}</div>`;
    });
}

window.onload = initSelection;
