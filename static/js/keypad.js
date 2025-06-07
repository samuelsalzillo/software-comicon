// static/js/keypad.js

let keypadInput = ""; // Variabile specifica per keypad 1
let currentPlayerAlfa = null; // Variabile specifica per giocatore in Alfa 1
let currentCode = ""; // Il codice corrente generato

// Mappa dei colori
const colorMap = {
  0: "white",
  1: "brown",
  2: "red",
  3: "orange",
  4: "black",
  5: "green",
  6: "gray",
  7: "blue",
};

// Funzione per generare un codice casuale di 4 cifre (da 0 a 7)
function generateRandomCode() {
  const digits = [0, 1, 2, 3, 4, 5, 6, 7]; // Cifre consentite da 0 a 7
  let code = "";
  for (let i = 0; i < 4; i++) {
    const randomIndex = Math.floor(Math.random() * digits.length);
    code += digits[randomIndex].toString();
    // Non rimuoviamo la cifra per permettere ripetizioni, se desiderato
  }
  return code;
}

// Funzione per impostare i quadrati in stato inattivo (grigio)
function setSquaresInactive() {
  for (let i = 1; i <= 4; i++) {
    const square = document.getElementById(`color-square-${i}`);
    if (square) {
      // Rimuovi tutte le classi di colore esistenti
      Object.values(colorMap).forEach((color) => {
        square.classList.remove(`color-${color}`);
      });
      // Aggiungi la classe inattiva
      square.classList.add("color-inactive");
    }
  }
}

// Funzione per aggiornare i quadrati colorati
function updateColorSquares(code) {
  if (!code) {
    setSquaresInactive();
    return;
  }

  for (let i = 0; i < 4; i++) {
    const digit = code[i];
    const colorClass = `color-${colorMap[digit]}`;
    const square = document.getElementById(`color-square-${i + 1}`);
    if (square) {
      // Rimuovi tutte le classi di colore esistenti
      Object.values(colorMap).forEach((color) => {
        square.classList.remove(`color-${color}`);
      });
      square.classList.remove("color-inactive");
      // Aggiungi la nuova classe di colore
      square.classList.add(colorClass);
    }
  }
}

// Funzione per aggiungere cifre all'input del keypad 1
function addKey(key) {
  if (keypadInput.length < 4) {
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
  if (keypadInput === currentCode) {
    if (
      currentPlayerAlfa &&
      currentPlayerAlfa.id &&
      currentPlayerAlfa.id.startsWith("GIALLO")
    ) {
      pressThirdButton();
    } else {
      let message = "Nessuna Coppia 1 (Giallo) in ALFA.";
      if (currentPlayerAlfa && currentPlayerAlfa.id) {
        message = `Giocatore ${currentPlayerAlfa.id} in ALFA non è una Coppia 1 (Giallo).`;
      } else if (!currentPlayerAlfa) {
        message = "Nessun giocatore attualmente in ALFA.";
      }
      showKeypad1Notification(message, true);
    }
  } else {
    showKeypad1Notification("Codice non valido", true);
  }
  clearKey();
}

// Funzione per inviare il segnale 'third' al backend
function pressThirdButton() {
  fetch("/button_press", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ button: "third" }),
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
        showKeypad1Notification("Metà percorso 1 attivato con successo.");
        // Resetta il codice e imposta i quadrati in grigio
        currentCode = "";
        setSquaresInactive();
        updateCurrentPlayerAlfa();
      } else {
        showKeypad1Notification(
          `Errore: ${data.error || "Attivazione fallita."}`,
          true
        );
      }
    })
    .catch((error) => {
      console.error("Errore durante l'attivazione del pulsante third:", error);
      showKeypad1Notification(
        `Errore di comunicazione: ${error.message}`,
        true
      );
    });
}

// Funzione per aggiornare la variabile currentPlayerAlfa e il display HTML
function updateCurrentPlayerAlfa() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      const previousPlayer = currentPlayerAlfa;
      currentPlayerAlfa = data.current_player_alfa;
      const displayElement = document.getElementById(
        "current-player-alfa-display"
      );
      if (displayElement) {
        displayElement.textContent = currentPlayerAlfa
          ? currentPlayerAlfa.id
          : "-";
      }

      // Se c'è un nuovo giocatore GIALLO in ALFA, genera un nuovo codice
      if (
        currentPlayerAlfa &&
        currentPlayerAlfa.id &&
        currentPlayerAlfa.id.startsWith("GIALLO")
      ) {
        // Genera il codice solo se non c'era già un giocatore GIALLO
        if (
          !previousPlayer ||
          !previousPlayer.id ||
          !previousPlayer.id.startsWith("GIALLO")
        ) {
          currentCode = generateRandomCode();
          updateColorSquares(currentCode);
        }
      } else {
        // Se non c'è un giocatore GIALLO, resetta il codice e imposta i quadrati in grigio
        currentCode = "";
        setSquaresInactive();
      }
    })
    .catch((error) => {
      console.error("Errore aggiornamento giocatore ALFA:", error);
      currentPlayerAlfa = null;
      const displayElement = document.getElementById(
        "current-player-alfa-display"
      );
      if (displayElement) {
        displayElement.textContent = "Errore";
      }
      // In caso di errore, resetta il codice e imposta i quadrati in grigio
      currentCode = "";
      setSquaresInactive();
    });
}

// Funzione per mostrare notifiche nel div specifico del keypad 1
function showKeypad1Notification(message, isError = false) {
  const notificationElement = document.getElementById("notification-keypad1");
  if (notificationElement) {
    notificationElement.textContent = message;
    notificationElement.style.color = isError ? "red" : "#8FBF60";
    notificationElement.style.display = "block";
    setTimeout(() => {
      notificationElement.style.display = "none";
      notificationElement.textContent = "";
    }, 3000);
  } else {
    console.warn(
      "Elemento notifica #notification-keypad1 non trovato. Messaggio:",
      message
    );
  }
}

// Inizializzazione al caricamento della pagina
document.addEventListener("DOMContentLoaded", (event) => {
  // Inizia con i quadrati in grigio
  setSquaresInactive();

  updateCurrentPlayerAlfa();
  setInterval(updateCurrentPlayerAlfa, 5000);
});