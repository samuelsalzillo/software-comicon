// static/js/keypad.js

let keypadInput = ""; // Variabile specifica per keypad 1
let currentPlayerAlfa = null; // Variabile specifica per giocatore in Alfa 1
const correctCode = "8523"; // Definisci il codice per il keypad 1 (CAMBIALO SE NECESSARIO)

// Funzione per aggiungere cifre all'input del keypad 1
function addKey(key) {
  if (keypadInput.length < 4) {
    // Limite a 4 cifre
    keypadInput += key;
    updateKeypadDisplay();
  }
}

// Funzione per pulire l'input del keypad 1
function clearKey() {
  keypadInput = "";
  updateKeypadDisplay();
}

// Funzione per aggiornare il display del keypad 1
function updateKeypadDisplay() {
  const display = document.getElementById("keypad-display");
  if (display) {
    display.value = "*".repeat(keypadInput.length);
  }
}

// Funzione per verificare il codice inserito nel keypad 1
function checkCode() {
  if (keypadInput === correctCode) {
    // Controlla se c'è un giocatore in ALFA e se è una coppia (es. GIALLO)
    // Assicurati che currentPlayerAlfa sia aggiornato correttamente
    if (
      currentPlayerAlfa &&
      currentPlayerAlfa.id &&
      currentPlayerAlfa.id.startsWith("GIALLO")
    ) {
      pressThirdButton(); // Chiama la funzione per inviare il segnale 'third'
    } else {
      let message = "Nessuna Coppia 1 (Giallo) in ALFA.";
      if (currentPlayerAlfa && currentPlayerAlfa.id) {
        message = `Giocatore ${currentPlayerAlfa.id} in ALFA non è una Coppia 1 (Giallo).`;
      } else if (!currentPlayerAlfa) {
        message = "Nessun giocatore attualmente in ALFA.";
      }
      showKeypad1Notification(message, true); // Mostra notifica di errore
    }
  } else {
    showKeypad1Notification("Codice non valido", true); // Mostra notifica di errore
  }
  clearKey(); // Pulisci l'input dopo il controllo
}

// Funzione per inviare il segnale 'third' al backend
function pressThirdButton() {
  fetch("/button_press", {
    // L'endpoint rimane /button_press
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    // Invia l'identificatore specifico per il keypad 1
    body: JSON.stringify({ button: "third" }),
  })
    .then((response) => {
      // Gestione errori HTTP migliorata
      if (!response.ok) {
        return response.json().then((err) => {
          throw new Error(err.error || `Errore ${response.status}`);
        });
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        showKeypad1Notification("Metà percorso 1 attivato con successo."); // Mostra notifica successo
        updateCurrentPlayerAlfa(); // Aggiorna subito lo stato visivo
      } else {
        showKeypad1Notification(
          `Errore: ${data.error || "Attivazione fallita."}`,
          true
        ); // Mostra notifica errore
      }
    })
    .catch((error) => {
      console.error("Errore durante l'attivazione del pulsante third:", error);
      showKeypad1Notification(
        `Errore di comunicazione: ${error.message}`,
        true
      ); // Mostra notifica errore di comunicazione
    });
}

// Funzione per aggiornare la variabile currentPlayerAlfa e il display HTML
function updateCurrentPlayerAlfa() {
  fetch("/simulate") // Chiamiamo /simulate che contiene tutti i dati aggiornati
    .then((response) => response.json())
    .then((data) => {
      currentPlayerAlfa = data.current_player_alfa; // Aggiorna la variabile JS
      // Aggiorna anche il display nell'HTML
      const displayElement = document.getElementById(
        "current-player-alfa-display"
      );
      if (displayElement) {
        displayElement.textContent = currentPlayerAlfa
          ? currentPlayerAlfa.id
          : "-";
      }
    })
    .catch((error) => {
      console.error("Errore aggiornamento giocatore ALFA:", error);
      currentPlayerAlfa = null; // Resetta in caso di errore
      const displayElement = document.getElementById(
        "current-player-alfa-display"
      );
      if (displayElement) {
        displayElement.textContent = "Errore"; // Mostra errore nel display
      }
    });
}

// Funzione per mostrare notifiche nel div specifico del keypad 1
function showKeypad1Notification(message, isError = false) {
  const notificationElement = document.getElementById("notification-keypad1"); // Usa l'ID corretto per questo keypad
  if (notificationElement) {
    notificationElement.textContent = message;
    notificationElement.style.color = isError ? "red" : "green";
    notificationElement.style.display = "block"; // Mostra
    // Nasconde dopo 3 secondi
    setTimeout(() => {
      notificationElement.style.display = "none";
      notificationElement.textContent = "";
    }, 3000);
  } else {
    // Fallback con console.log se l'elemento non esiste (meglio di alert)
    console.warn(
      "Elemento notifica #notification-keypad1 non trovato. Messaggio:",
      message
    );
  }
}

// Aggiorna il giocatore corrente in ALFA all'avvio e poi periodicamente
document.addEventListener("DOMContentLoaded", (event) => {
  updateCurrentPlayerAlfa(); // Chiamata iniziale
  // Aggiorna ogni 5 secondi (o intervallo preferito, allineato a keypad2.js)
  setInterval(updateCurrentPlayerAlfa, 5000);
});
