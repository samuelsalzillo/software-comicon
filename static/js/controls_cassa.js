let coupleCounter = 1;
let singleCounter = 1;
let coupleCounter2 = 1;
let singleCounter2 = 1;
let charlieCounter = 1;
let staticoCounter = 1;
$(document).ready(function () {
  fetchLastPlayerIds(); // Imposta i counter basati sugli ID attuali
  updateDashboard();
  setInterval(updateDashboard, 1000); // Aggiorna la dashboard ogni secondo
});

function fetchLastPlayerIds() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      let maxCouple = 0,
        maxSingle = 0,
        maxCouple2 = 0,
        maxSingle2 = 0,
        maxCharlie = 0,
        maxStatico = 0;

      if (data.couples.length > 0) {
        let lastCouple = data.couples[data.couples.length - 1];
        maxCouple = parseInt(lastCouple.id.split(" ")[1]) || 0;
      }

      if (data.singles.length > 0) {
        let lastSingle = data.singles[data.singles.length - 1];
        maxSingle = parseInt(lastSingle.id.split(" ")[1]) || 0;
      }

      // Coppie Rosa (NUOVO)
      if (data.couples2 && data.couples2.length > 0) {
        const ids = data.couples2
          .map((p) => parseInt(p.id.split(" ")[1]))
          .filter((n) => !isNaN(n));
        if (ids.length > 0) maxCouple2 = Math.max(...ids);
      }

      // Singoli Bianco (NUOVO)
      if (data.singles2 && data.singles2.length > 0) {
        const ids = data.singles2
          .map((p) => parseInt(p.id.split(" ")[1]))
          .filter((n) => !isNaN(n));
        if (ids.length > 0) maxSingle2 = Math.max(...ids);
      }

      if (data.charlie.length > 0) {
        let lastCharlie = data.charlie[data.charlie.length - 1];
        maxCharlie = parseInt(lastCharlie.id.split(" ")[1]) || 0;
      }

      if (data.statico && data.statico.length > 0) {
        let lastStatico = data.statico[data.statico.length - 1];
        maxStatico = parseInt(lastStatico.id.split(" ")[1]) || 0;
      }

      // Imposta i counter al numero successivo
      coupleCounter = maxCouple + 1;
      singleCounter = maxSingle + 1;
      coupleCounter2 = maxCouple2 + 1; // NUOVO
      singleCounter2 = maxSingle2 + 1; // NUOVO
      charlieCounter = maxCharlie + 1;
      staticoCounter = maxStatico + 1;

      // Aggiorna i pulsanti con il valore corretto
      document.getElementById("playerId-coppia").value = `${coupleCounter}`;
      document.getElementById("playerId-singolo").value = `${singleCounter}`;
      $("#playerId-coppia2").val(coupleCounter2); // NUOVO
      $("#playerId-singolo2").val(singleCounter2); // NUOVO
      document.getElementById("playerId-charlie").value = `${charlieCounter}`;
      document.getElementById("playerId-statico").value = `${staticoCounter}`;
    })
    .catch((error) => console.error("Errore nel recupero degli ID:", error));
}

// Aggiungi questo codice per sincronizzare con dashboard.js
function handleSkip(playerType) {
  let elementId, endpoint;

  switch (playerType) {
    case "alfa-bravo":
      elementId = "next-player-alfa-bravo-text";
      endpoint = "/skip_next_player_alfa_bravo";
      break;
    case "alfa-bravo2": // NUOVO CASO
      elementId = "next-player-alfa-bravo2-text";
      endpoint = "/skip_next_player_alfa_bravo2"; // NUOVO ENDPOINT (da creare in app.py)
      break;
    case "charlie":
      elementId = "next-charlie-text";
      endpoint = "/skip_charlie_player";
      break;
    case "statico":
      elementId = "next-statico-text";
      endpoint = "/skip_statico_player";
      break;
    default:
      return;
  }

  const nextPlayer = document.getElementById(elementId).textContent;
  if (
    nextPlayer &&
    nextPlayer !== "Nessun Giocatore In Coda" &&
    nextPlayer !== "-"
  ) {
    fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id: nextPlayer }),
    })
      .then((response) => {
        if (!response.ok) throw new Error("Errore nella chiamata di skip");
        return response.json();
      })
      .then((data) => {
        // Forza l'aggiornamento completo della dashboard
        updateDashboard();
        showNotification("Giocatore skippato con successo");
      })
      .catch((error) => {
        console.error("Errore durante lo skip:", error);
        showNotification("Errore durante lo skip del giocatore", true);
      });
  }
}

// Sostituisci le funzioni esistenti con queste
function skipNextPlayerAlfaBravo() {
  handleSkip("alfa-bravo");
}

function skipNextPlayerAlfaBravo2() {
  handleSkip("alfa-bravo2");
}

function skipNextPlayerCharlie() {
  handleSkip("charlie");
}

function skipNextPlayerStatico() {
  handleSkip("statico");
}

// Coppia (Giallo)
$("#queueForm-coppia").on("submit", function (event) {
  event.preventDefault();
  const playerId = $("#playerId-coppia").val();
  addPlayer("couple", playerId, "GIALLO", "/add_couple", "#playerId-coppia");
});

// Singolo (Blu)
$("#queueForm-singolo").on("submit", function (event) {
  event.preventDefault();
  const playerId = $("#playerId-singolo").val();
  addPlayer("single", playerId, "BLU", "/add_single", "#playerId-singolo");
});

// Coppia 2 (Rosa) - NUOVO
$("#queueForm-coppia2").on("submit", function (event) {
  event.preventDefault();
  const playerId = $("#playerId-coppia2").val();
  addPlayer("couple2", playerId, "ROSA", "/add_couple2", "#playerId-coppia2"); // Nuovo tipo, nome, endpoint, input ID
});

// Singolo 2 (Bianco) - NUOVO
$("#queueForm-singolo2").on("submit", function (event) {
  event.preventDefault();
  const playerId = $("#playerId-singolo2").val();
  addPlayer(
    "single2",
    playerId,
    "BIANCO",
    "/add_single2",
    "#playerId-singolo2"
  ); // Nuovo tipo, nome, endpoint, input ID
});

// Charlie (Verde)
$("#queueForm-charlie").on("submit", function (event) {
  event.preventDefault();
  const playerId = $("#playerId-charlie").val();
  addPlayer("charlie", playerId, "VERDE", "/add_charlie", "#playerId-charlie");
});

// Statico (Rosso)
$("#queueForm-statico").on("submit", function (event) {
  event.preventDefault();
  const playerId = $("#playerId-statico").val();
  addPlayer("statico", playerId, "ROSSO", "/add_statico", "#playerId-statico");
});

// document.getElementById('add-couple-btn').addEventListener('click', function () {
//     if (coupleCounter < 100) {
//         addPlayer('couple', coupleCounter, 'GIALLO');
//         coupleCounter++;
//         this.textContent = `Aggiungi Coppia (GIALLO) ${coupleCounter}`;
//     } else {
//         showNotification('Limite massimo di 100 coppie raggiunto.', true);
//         addPlayer('couple', coupleCounter, 'GIALLO');
//         coupleCounter = 1; // Reset the counter
//         this.textContent = `Aggiungi Coppia (GIALLO) ${coupleCounter}`;
//     }
// });

// document.getElementById('add-single-btn').addEventListener('click', function () {
//     if (singleCounter < 100) {
//         addPlayer('single', singleCounter, 'BLU');
//         singleCounter++;
//         this.textContent = `Aggiungi Singolo (BLU) ${singleCounter}`;
//     } else {
//         showNotification('Limite massimo di 100 singoli raggiunto.', true);
//         addPlayer('single', singleCounter, 'BLU');
//         singleCounter = 1; // Reset the counter
//         this.textContent = `Aggiungi Singolo (BLU) ${singleCounter}`;
//     }
// });

// document.getElementById('add-charlie-btn').addEventListener('click', function () {
//     if (charlieCounter < 100) {
//         addPlayer('charlie', charlieCounter, 'VERDE');
//         charlieCounter++;
//         this.textContent = `Aggiungi Charlie (VERDE) ${charlieCounter}`;
//     } else {
//         showNotification('Limite massimo di 100 Charlie raggiunto.', true);
//         addPlayer('charlie', charlieCounter, 'VERDE');
//         charlieCounter = 1; // Reset the counter
//         this.textContent = `Aggiungi Charlie (VERDE) ${charlieCounter}`;
//     }
// });

// Funzione generica per aggiungere giocatore
function addPlayer(type, id, name, endpoint, inputSelector) {
  const numericId = Number(id);
  if (isNaN(numericId) || numericId <= 0) {
    showNotification("ID Giocatore non valido.", true);
    return;
  }

  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: numericId, name: name }), // Invia l'ID come numero
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const formattedId = `${name} ${String(numericId).padStart(3, "0")}`; // Ricrea l'ID formattato per la notifica
        showNotification(`${formattedId} aggiunto con successo!`);
        updateDashboard(); // Aggiorna la dashboard
        // Incrementa e aggiorna l'input field per il prossimo ID
        $(inputSelector).val(numericId + 1);
        // Aggiorna i contatori globali (opzionale, se fetchLastPlayerIds non viene richiamato subito)
        switch (type) {
          case "couple":
            coupleCounter = numericId + 1;
            $(inputSelector).addClass("next-player couple");
            break;
          case "single":
            singleCounter = numericId + 1;
            $(inputSelector).addClass("next-player single");
            break;
          case "couple2":
            coupleCounter2 = numericId + 1;
            $(inputSelector).addClass("next-player couple2");
            break;
          case "single2":
            singleCounter2 = numericId + 1;
            $(inputSelector).addClass("next-player single2");
            break;
          case "charlie":
            charlieCounter = numericId + 1;
            $(inputSelector).addClass("next-player charlie");
            break;
          case "statico":
            staticoCounter = numericId + 1;
            $(inputSelector).addClass("next-player statico");
            break;
        }
      } else {
        showNotification(
          `Errore nell'aggiunta: ${data.error || "Errore sconosciuto"}`,
          true
        );
      }
    })
    .catch((error) => {
      console.error(`Errore fetch ${endpoint}:`, error);
      showNotification("Errore di comunicazione con il server.", true);
    });
}

// --- Funzioni Utilità (esistenti) ---
function showNotification(message, isError = false) {
  const notification = $("#notification");
  notification.text(message);
  notification.css("color", isError ? "#F23207" : "green");
  // Usa fadeOut e fadeIn per un effetto più gradevole
  notification.fadeIn().delay(3000).fadeOut();
}

function deletePlayer(playerId) {
  // Chiedi conferma prima di eliminare
  if (!confirm(`Sei sicuro di voler eliminare il giocatore ${playerId}?`)) {
    return;
  }

  fetch(`/delete_player`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: playerId }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(`Giocatore ${playerId} eliminato.`);
        updateDashboard(); // Aggiorna subito dopo l'eliminazione
      } else {
        showNotification(
          `Errore nella cancellazione del giocatore ${playerId}.`,
          true
        );
      }
    })
    .catch((error) => {
      console.error("Errore fetch delete_player:", error);
      showNotification(
        "Errore di comunicazione durante la cancellazione.",
        true
      );
    });
}

$(document).ready(function () {
  updateDashboard();
});
