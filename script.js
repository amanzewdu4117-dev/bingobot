const board = document.getElementById('board');
const numbers = Array.from({length: 25}, (_, i) => i + 1).sort(() => Math.random() - 0.5);

numbers.forEach(num => {
    const cell = document.createElement('div');
    cell.className = 'cell';
    cell.textContent = num;
    cell.onclick = () => {
        cell.classList.toggle('selected');
    };
    board.appendChild(cell);
});
