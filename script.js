// 1. 500 ቁጥሮችን በሎቢው ላይ መፍጠር
const lobbyGrid = document.getElementById('lobby-grid');
for (let i = 1; i <= 500; i++) {
    let el = document.createElement('div');
    el.className = 'slot-item';
    el.innerText = i;
    lobbyGrid.appendChild(el);
}

// 2. የቢንጎ ካርቴላ ዳታ (ለአብነት)
let myTickets = [
    { id: 59, numbers: [2, 16, 31, 48, 61, 6, 24, 33, 52, 64, 12, 25, 55, 71] },
    { id: 36, numbers: [2, 17, 36, 48, 63, 3, 21, 37, 49, 66, 11, 22, 53, 68] }
];

// 3. ጨዋታው ሲጀምር ካርቴላዎቹን መሳል
function renderMyCards() {
    const container = document.getElementById('my-active-cards');
    myTickets.forEach(ticket => {
        let cardHTML = `<div class="bingo-card-small" id="card-${ticket.id}">
            <div style="font-size:10px; margin-bottom:5px">Cartela ${ticket.id}</div>
            <div class="card-grid">`;
        ticket.numbers.forEach(num => {
            cardHTML += `<div class="cell" id="cell-${ticket.id}-${num}">${num}</div>`;
        });
        cardHTML += `</div></div>`;
        container.innerHTML += cardHTML;
    });
}

// 4. አውቶማቲክ ምልክት ማድረጊያ (Automatic Marker)
function callNumber(num) {
    // በሁሉም ካርቴላዎቼ ውስጥ ይህ ቁጥር ካለ ምልክት አድርግ
    myTickets.forEach(ticket => {
        if (ticket.numbers.includes(num)) {
            let cell = document.getElementById(`cell-${ticket.id}-${num}`);
            if (cell) cell.classList.add('marked');
        }
    });
}

// ለሙከራ ያህል በየ 2 ሰከንዱ ቁጥር እንዲጠራ ማድረግ
let currentCall = 0;
function startGameSimulation() {
    renderMyCards();
    let interval = setInterval(() => {
        let randomNum = Math.floor(Math.random() * 75) + 1;
        callNumber(randomNum);
        currentCall++;
        document.getElementById('called-count').innerText = currentCall;
        
        if (currentCall > 20) { // ከ20 ጥሪ በኋላ አሸናፊ አሳይ
            clearInterval(interval);
            showScreen('winner-screen');
        }
    }, 2000);
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    document.getElementById(screenId).classList.remove('hidden');
}

// አስጀምር
showScreen('selection-screen');
// ከ 5 ሰከንድ በኋላ ወደ ጨዋታው እንዲገባ (ለሙከራ)
setTimeout(() => {
    showScreen('game-screen');
    startGameSimulation();
}, 5000);
