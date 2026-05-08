document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('bingo-grid');
    
    // 25 የቢንጎ ቁጥሮችን ለመፍጠር
    for (let i = 0; i < 25; i++) {
        const cell = document.createElement('div');
        cell.classList.add('cell');
        cell.textContent = Math.floor(Math.random() * 75) + 1;
        grid.appendChild(cell);
    }
});

function checkBingo() {
    alert("ቢንጎ ቼክ እየተደረገ ነው...");
}
