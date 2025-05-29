// static/js/keypad2.js

let keypadInput2 = ""; // Variabile specifica per keypad 2
let currentPlayerAlfa2 = null; // Variabile specifica per giocatore in Alfa 2
let currentCode2 = ""; // Il codice corrente generato
let isFirstUpdate = true; // Flag per il primo aggiornamento

// Mappa dei colori
const colorMap = {
    '0': 'white',
    '1': 'yellow',
    '2': 'green',
    '3': 'blue',
    '4': 'red',
    '5': 'orange',
    '6': 'pink',
    '7': 'brown',
    '8': 'purple',
    '9': 'black'
};

// Funzione per generare un codice casuale di 4 cifre
function generateRandomCode() {
    let code = '';
    for (let i = 0; i < 4; i++) {
        code += Math.floor(Math.random() * 10).toString();
    }
    console.log("Codice generato:", code); // Debug log
    return code;
}

// Funzione per impostare i quadrati in stato inattivo (grigio)
function setSquaresInactive2() {
    for (let i = 1; i <= 4; i++) {
        const square = document.getElementById(`color-square2-${i}`);
        if (square) {
            // Rimuovi tutte le classi di colore esistenti
            Object.values(colorMap).forEach(color => {
                square.classList.remove(`color-${color}`);
            });
            // Aggiungi la classe inattiva
            square.classList.add('color-inactive');
        }
    }
}

// Funzione per aggiornare i quadrati colorati
function updateColorSquares2(code) {
    if (!code) {
        setSquaresInactive2();
        return;
    }
    
    for (let i = 0; i < 4; i++) {
        const digit = code[i];
        const colorClass = `color-${colorMap[digit]}`;
        const square = document.getElementById(`color-square2-${i + 1}`);
        if (square) {
            // Rimuovi tutte le classi di colore esistenti
            Object.values(colorMap).forEach(color => {
                square.classList.remove(`color-${color}`);
            });
            square.classList.remove('color-inactive');
            // Aggiungi la nuova classe di colore
            square.classList.add(colorClass);
        }
    }
}

// Funzione per aggiungere cifre all'input del keypad 2
function addKey2(key) {
    if (keypadInput2.length < 4) {
        keypadInput2 += key;
        updateKeypadDisplay2();
    }
}

// Funzione per pulire l'input del keypad 2
function clearKey2() {
    keypadInput2 = "";
    updateKeypadDisplay2();
}

// Funzione per aggiornare il display del keypad 2
function updateKeypadDisplay2() {
    const display = document.getElementById("keypad-display2");
    if (display) {
        display.value = "*".repeat(keypadInput2.length);
    }
}

// Funzione per verificare il codice inserito nel keypad 2
function checkCode2() {
    console.log("Codice inserito:", keypadInput2); // Debug log
    console.log("Codice attuale:", currentCode2); // Debug log
    
    if (keypadInput2 === currentCode2) {
        if (currentPlayerAlfa2 && currentPlayerAlfa2.id && currentPlayerAlfa2.id.startsWith("ROSA")) {
            pressThirdButton2();
        } else {
            let message = "Nessuna Coppia 2 (Rosa) in ALFA 2.";
            if (currentPlayerAlfa2 && currentPlayerAlfa2.id) {
                message = `Giocatore ${currentPlayerAlfa2.id} in ALFA 2 non è una Coppia 2 (Rosa).`;
            } else if (!currentPlayerAlfa2) {
                message = "Nessun giocatore attualmente in ALFA 2.";
            }
            showKeypad2Notification(message, true);
        }
    } else {
        showKeypad2Notification("Codice non valido", true);
    }
    clearKey2();
}

// Funzione per inviare il segnale 'third2' al backend
function pressThirdButton2() {
    fetch("/button_press", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ button: "third2" }),
    })
    .then((response) => {
        if (!response.ok) {
            return response.json().then((err) => {
                throw new Error(err.error || `Errore ${response.status}`);
            });
        }
        return response.json();
    })
    .then((data) => {
        if (data.success) {
            showKeypad2Notification("Metà percorso 2 attivato con successo.");
            // Resetta il codice e imposta i quadrati in grigio
            currentCode2 = "";
            setSquaresInactive2();
            updateCurrentPlayerAlfa2();
        } else {
            showKeypad2Notification(`Errore: ${data.error || "Attivazione fallita."}`, true);
        }
    })
    .catch((error) => {
        console.error("Errore durante l'attivazione del pulsante third2:", error);
        showKeypad2Notification(`Errore di comunicazione: ${error.message}`, true);
    });
}

// Funzione per aggiornare la variabile currentPlayerAlfa2 e il display HTML
function updateCurrentPlayerAlfa2() {
    fetch("/simulate")
        .then((response) => response.json())
        .then((data) => {
            const previousPlayer = currentPlayerAlfa2;
            currentPlayerAlfa2 = data.current_player_alfa2;
            const displayElement = document.getElementById("current-player-alfa2-display");
            if (displayElement) {
                displayElement.textContent = currentPlayerAlfa2 ? currentPlayerAlfa2.id : "-";
            }
            
            // Se c'è un nuovo giocatore ROSA in ALFA 2, genera un nuovo codice
            if (currentPlayerAlfa2 && currentPlayerAlfa2.id && currentPlayerAlfa2.id.startsWith("ROSA")) {
                // Genera il codice se è il primo aggiornamento o se non c'era già un giocatore ROSA
                if (isFirstUpdate || !previousPlayer || !previousPlayer.id || !previousPlayer.id.startsWith("ROSA")) {
                    currentCode2 = generateRandomCode();
                    updateColorSquares2(currentCode2);
                    isFirstUpdate = false;
                }
            } else {
                // Se non c'è un giocatore ROSA, resetta il codice e imposta i quadrati in grigio
                currentCode2 = "";
                setSquaresInactive2();
            }
        })
        .catch((error) => {
            console.error("Errore aggiornamento giocatore ALFA 2:", error);
            currentPlayerAlfa2 = null;
            const displayElement = document.getElementById("current-player-alfa2-display");
            if (displayElement) {
                displayElement.textContent = "Errore";
            }
            // In caso di errore, resetta il codice e imposta i quadrati in grigio
            currentCode2 = "";
            setSquaresInactive2();
        });
}

// Funzione per mostrare notifiche nel div specifico del keypad 2
function showKeypad2Notification(message, isError = false) {
    const notificationElement = document.getElementById("notification-keypad2");
    if (notificationElement) {
        notificationElement.textContent = message;
        notificationElement.style.color = isError ? "red" : "#8FBF60";
        notificationElement.style.display = "block";
        setTimeout(() => {
            notificationElement.style.display = "none";
            notificationElement.textContent = "";
        }, 3000);
    } else {
        console.warn("Elemento notifica #notification-keypad2 non trovato. Messaggio:", message);
    }
}

// Inizializzazione al caricamento della pagina
document.addEventListener("DOMContentLoaded", (event) => {
    // Inizia con i quadrati in grigio
    setSquaresInactive2();
    
    // Forza il primo aggiornamento immediato
    updateCurrentPlayerAlfa2();
    // Poi imposta l'intervallo per gli aggiornamenti successivi
    setInterval(updateCurrentPlayerAlfa2, 5000);
});
