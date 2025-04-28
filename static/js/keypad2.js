// static/js/keypad2.js

let keypadInput2 = ""; // Variabile specifica per keypad 2
let currentPlayerAlfa2 = null; // Variabile specifica per giocatore in Alfa 2
const correctCode2 = "8746"; // Definisci il codice per il keypad 2 (CAMBIALO SE NECESSARIO)

// Funzione per aggiungere cifre all'input del keypad 2
function addKey2(key) {
  if (keypadInput2.length < 4) {
    // Limite a 4 cifre
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
  if (keypadInput2 === correctCode2) {
    // Controlla se c'è un giocatore in ALFA 2 e se è una coppia (es. ROSA)
    // Assicurati che currentPlayerAlfa2 sia aggiornato correttamente
    if (
      currentPlayerAlfa2 &&
      currentPlayerAlfa2.id &&
      currentPlayerAlfa2.id.startsWith("ROSA")
    ) {
      pressThirdButton2(); // Chiama la funzione per inviare il segnale 'third2'
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
  clearKey2(); // Pulisci l'input dopo il controllo
}

// Funzione per inviare il segnale 'third2' al backend
function pressThirdButton2() {
  fetch("/button_press", {
    // L'endpoint rimane /button_press
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    // Invia l'identificatore specifico per il keypad 2
    body: JSON.stringify({ button: "third2" }),
  })
    .then((response) => {
      if (!response.ok) {
        // Gestione errori HTTP
        return response.json().then((err) => {
          throw new Error(err.error || `Errore ${response.status}`);
        });
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        showKeypad2Notification("Metà percorso 2 attivato con successo.");
        updateCurrentPlayerAlfa2(); // Aggiorna subito lo stato visivo
      } else {
        showKeypad2Notification(
          `Errore: ${data.error || "Attivazione fallita."}`,
          true
        );
      }
    })
    .catch((error) => {
      console.error("Errore durante l'attivazione del pulsante third2:", error);
      showKeypad2Notification(
        `Errore di comunicazione: ${error.message}`,
        true
      );
    });
}

// Funzione per aggiornare la variabile currentPlayerAlfa2 e il display HTML
function updateCurrentPlayerAlfa2() {
  fetch("/simulate") // Chiamiamo /simulate che contiene tutti i dati aggiornati
    .then((response) => response.json())
    .then((data) => {
      currentPlayerAlfa2 = data.current_player_alfa2; // Aggiorna la variabile JS
      // Aggiorna anche il display nell'HTML
      const displayElement = document.getElementById(
        "current-player-alfa2-display"
      );
      if (displayElement) {
        displayElement.textContent = currentPlayerAlfa2
          ? currentPlayerAlfa2.id
          : "-";
      }
    })
    .catch((error) => {
      console.error("Errore aggiornamento giocatore ALFA 2:", error);
      currentPlayerAlfa2 = null; // Resetta in caso di errore
      const displayElement = document.getElementById(
        "current-player-alfa2-display"
      );
      if (displayElement) {
        displayElement.textContent = "Errore";
      }
    });
}

// Funzione per mostrare notifiche nel div specifico del keypad 2
function showKeypad2Notification(message, isError = false) {
  const notificationElement = document.getElementById("notification-keypad2");
  if (notificationElement) {
    notificationElement.textContent = message;
    notificationElement.style.color = isError ? "red" : "#8FBF60";
    notificationElement.style.display = "block"; // Mostra
    // Nasconde dopo 3 secondi
    setTimeout(() => {
      notificationElement.style.display = "none";
      notificationElement.textContent = "";
    }, 3000);
  } else {
    // Fallback con alert se l'elemento non esiste
    alert((isError ? "Errore: " : "") + message);
  }
}

// Aggiorna il giocatore corrente in ALFA 2 all'avvio e poi periodicamente
document.addEventListener("DOMContentLoaded", (event) => {
  updateCurrentPlayerAlfa2(); // Chiamata iniziale
  setInterval(updateCurrentPlayerAlfa2, 5000); // Aggiorna ogni 5 secondi (o intervallo preferito)
});
