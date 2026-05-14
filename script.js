// 1. Firebase Configuration (ይህንን ከ Firebase Settings ኮፒ ያደረግከውን ተካው)
const firebaseConfig = {
  databaseURL: "https://my-app-project-1e0bb-default-rtdb.firebaseio.com/"
};

// Firebase ን አስነሳ
firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// 2. ተጫዋቾችን ከ Firebase አንብቦ የሚያሳይ ተግባር
function loadPlayers() {
    const playersRef = database.ref('active_players');
    const playersList = document.getElementById('players-list'); // በ HTML ላይ ያለ ዝርዝር ቦታ

    playersRef.on('value', (snapshot) => {
        const data = snapshot.val();
        playersList.innerHTML = ""; // አሮጌውን ዝርዝር አጽዳ

        if (data) {
            Object.keys(data).forEach(key => {
                const player = data[key];
                
                // የተጫዋቹን መረጃ በስክሪኑ ላይ ፍጠር
                const playerElement = document.createElement('div');
                playerElement.className = 'player-item';
                playerElement.innerHTML = `
                    <div class="player-info">
                        <span class="status-dot ${player.status === 'online' ? 'online' : 'offline'}"></span>
                        <span class="player-name">${player.name}</span>
                    </div>
                    <span class="player-balance">${player.balance} ETB</span>
                `;
                playersList.appendChild(playerElement);
            });
        } else {
            playersList.innerHTML = "<p>ምንም ተጫዋች የለም...</p>";
        }
    });
}

// ገጹ ሲከፈት ተጫዋቾችን መጫን ጀምር
window.onload = loadPlayers;
