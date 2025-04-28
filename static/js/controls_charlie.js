let timerInterval;
let startTime;
let isGameActive = false;

function updateNextPlayer() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      // Aggiorna prossimo giocatore Charlie
      const charlieQueue = data.charlie || [];
      if (charlieQueue.length > 0) {
        const nextPlayer = charlieQueue[0]; // Oggetto {id, name, estimated_time}
        // Mostra solo l'ID come prima, ma potresti usare anche il nome
        $("#next-player").text(`${nextPlayer.id}`);
        $("#next-player-btn").prop("disabled", isGameActive); // Disabilita solo se gioco attivo
        console.log(`Next player Charlie: ${nextPlayer.id}`);
      } else {
        $("#next-player").text("Nessun Giocatore In Coda");
        // Disabilita se non ci sono giocatori *e* gioco non attivo
        $("#next-player-btn").prop(
          "disabled",
          !isGameActive && charlieQueue.length === 0
        );
      }

      // Aggiorna stato pista Charlie
      updateTrackStatus(data);

      // Aggiorna giocatore corrente Charlie (se presente)
      if (data.current_player_charlie) {
        $("#current-player").text(
          `${data.current_player_charlie.name || ""} - ${
            data.current_player_charlie.id
          }`
        );
      } else if (!isGameActive) {
        // Resetta solo se non c'è un gioco attivo
        $("#current-player").text("-");
      }
    })
    .catch((error) => console.error("Error fetching simulation data:", error));
}

function updateSkipped() {
  fetch("/get_skipped")
    .then((response) => response.json())
    .then((data) => {
      const createSkippedButtons = (containerId, players, className) => {
        const container = document.getElementById(containerId);
        if (!container) return; // Esce se il container non esiste
        container.innerHTML = ""; // Pulisce
        if (players && players.length > 0) {
          players.forEach((player) => {
            const button = document.createElement("button");
            // Usa player.id per testo e onclick
            button.className = `skipped-button ${className}`;
            button.textContent = player.id;
            button.onclick = () => restoreSkipped(player.id);
            container.appendChild(button);
          });
        } else {
          // Opzionale: mostra un messaggio se non ci sono skippati
          // container.innerHTML = '<p class="no-skipped">Nessuno skippato</p>';
        }
      };

      // Aggiorna solo la sezione Charlie se siamo in controls_charlie.js
      createSkippedButtons("skipped-charlie-buttons", data.charlie, "charlie");
    })
    .catch((error) => {
      console.error("Errore durante il recupero degli skipped:", error);
    });
}

// Assicurati che la funzione venga chiamata regolarmente
setInterval(() => {
  updateSkipped();
}, 1000);
// Aggiorna la dashboard ogni secondo

function restoreSkipped(playerId) {
  console.log("Tentativo di ripristino giocatore:", playerId);
  $.ajax({
    url: "/restore_skipped_as_next",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ id: playerId }),
    success: function (response) {
      console.log("Giocatore ripristinato con successo:", playerId);
      updateNextPlayer(); // Aggiorna la vista del prossimo giocatore
      updateSkipped(); // Rimuove il bottone dagli skippati
      // updateBoards(); // Se esiste una funzione globale per aggiornare tutte le board
    },
    error: function (xhr, status, error) {
      console.error("Errore durante il ripristino del giocatore:", error);
      alert(`Errore ripristino: ${xhr.responseJSON?.error || error}`);
    },
  });
}

function skipNextPlayerCharlie() {
  const nextPlayerId = document.getElementById("next-player").textContent;
  // Controlla che non sia il testo placeholder o vuoto
  if (
    nextPlayerId &&
    nextPlayerId !== "Nessun Giocatore In Coda" &&
    nextPlayerId !== "-"
  ) {
    console.log("Skipping Charlie player:", nextPlayerId);
    fetch("/skip_charlie_player", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: nextPlayerId }), // Passa l'ID corretto
    })
      .then((response) => {
        if (!response.ok)
          throw new Error(`Errore ${response.status} nello skip`);
        return response.json();
      })
      .then((data) => {
        console.log("Skip response:", data);
        if (data.success) {
          // Aggiorna UI dopo lo skip
          updateNextPlayer();
          updateSkipped();
          // updateBoards(); // Se applicabile
        } else {
          throw new Error(data.error || "Errore sconosciuto durante lo skip.");
        }
      })
      .catch((error) => {
        console.error("Errore durante lo skip:", error);
        alert(`Errore skip: ${error.message}`);
      });
  } else {
    console.log("Nessun giocatore Charlie da skippare.");
  }
}

function updateTrackStatus(data) {
  // Assumendo che 'data' sia l'oggetto JSON da /simulate
  const charlieStatus = data.charlie_status || "Libera"; // Default a Libera
  const charlieRemaining = data.charlie_remaining || "0min";
  const canStartCharlie = charlieStatus === "Libera";

  // Abilita/Disabilita START in base allo stato della pista Charlie
  $("#start-btn").prop("disabled", !canStartCharlie || isGameActive); // Disabilita se Occupata o gioco già attivo

  // Aggiorna testo stato
  $("#status").text(`${charlieStatus} - ${charlieRemaining}`);

  // Tooltip per START
  if (!canStartCharlie) {
    $("#start-btn").attr("title", "Attendere che la pista CHARLIE sia libera");
  } else if (isGameActive) {
    $("#start-btn").attr("title", "Gioco Charlie già in corso");
  } else {
    $("#start-btn").attr("title", "Avvia gioco Charlie"); // Rimuovi/resetta tooltip
  }

  // Abilita/Disabilita STOP solo se il gioco è attivo
  $("#stop-btn").prop("disabled", !isGameActive);
  if (!isGameActive) {
    $("#stop-btn").attr("title", "Nessun gioco Charlie da fermare");
  } else {
    $("#stop-btn").attr("title", "Ferma gioco Charlie");
  }

  // Abilita/Disabilita PROSSIMO GIOCATORE
  // Si abilita solo se il gioco NON è attivo E c'è un giocatore in coda
  const hasNextPlayer =
    $("#next-player").text() !== "Nessun Giocatore In Coda" &&
    $("#next-player").text() !== "-";
  $("#next-player-btn").prop("disabled", isGameActive || !hasNextPlayer);
  if (isGameActive) {
    $("#next-player-btn").attr("title", "Gioco in corso");
  } else if (!hasNextPlayer) {
    $("#next-player-btn").attr("title", "Nessun giocatore in coda");
  } else {
    $("#next-player-btn").attr("title", "Attiva prossimo giocatore");
  }
}

function updateTimer() {
  if (!isGameActive || !startTime) return; // Aggiunto controllo per startTime
  const now = new Date();
  const diff = Math.floor((now - startTime) / 1000);
  const minutes = Math.floor(diff / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (diff % 60).toString().padStart(2, "0");
  $("#timer").text(`${minutes}:${seconds}`);
}

function activateNextPlayer() {
  console.log(
    "activateNextPlayer called - resetting UI for next potential game"
  );
  // Resetta l'UI allo stato 'pronto per iniziare' (se la pista è libera)
  isGameActive = false;
  clearInterval(timerInterval);
  startTime = null;
  $("#timer").text("00:00");
  $("#current-player").text("-");
  // Aggiorna la disponibilità (che abiliterà/disabiliterà i bottoni)
  updateNextPlayer(); // Questo aggiornerà anche lo stato dei bottoni tramite updateTrackStatus
}

function pressButton(button) {
  console.log(`Button pressed: ${button}`);

  // --- START ---
  if (button === "charlie_start") {
    // Blocco Optimistic UI Update (opzionale, ma migliora UX)
    $("#start-btn").prop("disabled", true).attr("title", "Avvio in corso...");
    $("#stop-btn").prop("disabled", true); // Disabilita stop momentaneamente
    $("#next-player-btn").prop("disabled", true); // Disabilita prossimo durante l'avvio

    $.ajax({
      url: "/button_press",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ button: button }),
      success: function (response) {
        console.log("Start response:", response);
        if (response.success && response.current_player_charlie) {
          startTime = new Date();
          isGameActive = true;
          timerInterval = setInterval(updateTimer, 1000); // Avvia timer JS

          // Aggiorna UI allo stato "attivo"
          $("#current-player").text(
            `${response.current_player_charlie.name || ""} - ${
              response.current_player_charlie.id
            }`
          );
          $("#start-btn")
            .prop("disabled", true)
            .attr("title", "Gioco Charlie in corso");
          $("#stop-btn")
            .prop("disabled", false)
            .attr("title", "Ferma gioco Charlie"); // ABILITA STOP
          $("#next-player-btn").prop("disabled", true); // Mantiene disabilitato durante gioco
          $("#status").text("Occupata - 00:00"); // Stato iniziale timer
          $("#timer").text("00:00"); // Resetta display timer

          // Potrebbe essere utile aggiornare subito la lista next player
          updateNextPlayer(); // Rimuove il giocatore appena partito dalla lista 'next'
        } else {
          // Errore backend o nessun giocatore restituito
          alert(response.error || "Errore durante l'avvio del gioco.");
          // Ripristina stato UI pre-start
          activateNextPlayer(); // Usa questa per resettare
        }
      },
      error: function (xhr, status, error) {
        console.error("Error starting Charlie game:", status, error);
        alert(
          `Errore comunicazione avvio: ${xhr.responseJSON?.error || error}`
        );
        // Ripristina stato UI pre-start
        activateNextPlayer(); // Usa questa per resettare
      },
    });
  }
  // --- STOP ---
  else if (button === "charlie_stop" && isGameActive) {
    // Blocco Optimistic UI Update
    $("#stop-btn").prop("disabled", true).attr("title", "Stop in corso...");

    $.ajax({
      url: "/button_press",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ button: button }),
      success: function (response) {
        console.log("Stop response:", response);
        if (response.success && response.player_id) {
          // Il backend ha registrato il timer e liberato la pista.
          // NON resettiamo l'UI principale qui.
          isGameActive = false;
          clearInterval(timerInterval); // Ferma timer JS
          // Conserva ID e nome del giocatore che ha finito
          stoppedPlayerId = response.player_id;
          stoppedPlayerName = response.player_name;

          // Mostra il modal per l'input manuale
          showManualScoreModal(stoppedPlayerId, stoppedPlayerName);
          // Lo stato UI (bottoni, current player) verrà aggiornato
          // SOLO quando il modal manuale viene chiuso o inviato.
        } else {
          // Errore backend
          alert(response.error || "Errore durante lo stop del gioco.");
          $("#stop-btn")
            .prop("disabled", false)
            .attr("title", "Ferma gioco Charlie"); // Riabilita stop se fallisce
        }
      },
      error: function (xhr, status, error) {
        console.error("Error stopping Charlie game:", status, error);
        alert(`Errore comunicazione stop: ${xhr.responseJSON?.error || error}`);
        $("#stop-btn")
          .prop("disabled", false)
          .attr("title", "Ferma gioco Charlie"); // Riabilita stop se fallisce
      },
    });
  } else if (button === "charlie_stop" && !isGameActive) {
    console.warn("Attempted to stop Charlie game, but not active.");
  }
}

function showManualScoreModal(playerId, playerName) {
  console.log("Showing manual score modal for:", playerId, playerName);
  // Popola i campi nascosti
  $("#manual-player-id").val(playerId);
  $("#manual-player-name").val(playerName);

  // Resetta i campi di input e il messaggio
  $("#manual-score-form")[0].reset();
  $("#manual-score-message").hide().removeClass("success error").text("");
  $("#submit-manual-score-btn")
    .prop("disabled", false)
    .text("Salva Tempo e Verifica"); // Riabilita bottone

  // Mostra il modal
  $("#manual-score-modal").css("display", "flex");
}

// Chiude il modal per inserire il tempo manualmente E AGGIORNA L'UI PRINCIPALE
function closeManualScoreModal() {
  console.log("Closing manual score modal and resetting UI.");
  $("#manual-score-modal").fadeOut();
  // Resetta lo stato dell'interfaccia principale come se il gioco fosse finito
  activateNextPlayer(); // Questa funzione ora resetta l'UI correttamente
  // Pulisci variabili globali temporanee
  stoppedPlayerId = null;
  stoppedPlayerName = null;
}

// Mostra il modal per i dati di contatto del qualificato
function showCharlieQualificationModal(data) {
  console.log("Showing Charlie qualification modal for:", data.player_id);
  // Popola campi nascosti del modal di qualifica
  $("#qual-player-id").val(data.player_id);
  $("#qual-player-name").val(data.player_name);
  $("#qual-score-minutes").val(data.recorded_score);
  $("#qual-player-type").val(data.player_type); // Sarà 'charlie'
  $("#qual-qualification-reason").val(data.reason);

  // Aggiorna testo motivo qualifica
  let reasonText = "Complimenti per l'ottimo tempo!";
  if (data.reason === "best_today") {
    reasonText = "Hai registrato il MIGLIOR TEMPO DI OGGI per G&G!";
  } else if (data.reason === "top_3_overall") {
    reasonText = "Sei entrato nella TOP 3 GENERALE G&G!";
  }
  $("#charlie-qualification-reason-text").text(
    reasonText + " Inserisci i dati per essere ricontattato:"
  );

  // Resetta form e messaggio del modal di qualifica
  $("#charlie-qualification-form")[0].reset();
  $("#charlie-qualification-message")
    .hide()
    .removeClass("success error")
    .text("");
  $('#charlie-qualification-form button[type="submit"]')
    .prop("disabled", false)
    .text("Salva Dati Contatto");

  // Mostra il modal di qualifica
  $("#charlie-qualification-modal").css("display", "flex");
}

// Chiude il modal dei dati di contatto
function closeCharlieQualificationModal() {
  $("#charlie-qualification-modal").fadeOut();
}

// Helper per mostrare messaggi nei modal
function showModalMessage(modalId, message, type) {
  const messageDiv = $(`#${modalId}-message`); // Es: #manual-score-message
  messageDiv.removeClass("success error").addClass(type).text(message).fadeIn();
  // Nascondi dopo 5 secondi
  setTimeout(() => {
    messageDiv.fadeOut();
  }, 5000);
}

// --- GESTIONE INVIO FORM MODAL ---

// Gestione invio form Manual Score
$("#manual-score-form").on("submit", function (event) {
  event.preventDefault();
  console.log("Submitting manual score form...");

  const minutes = $("#score_minutes").val();
  const seconds = $("#score_seconds").val();
  const milliseconds = $("#score_milliseconds").val();
  const playerId = $("#manual-player-id").val();
  const playerName = $("#manual-player-name").val();

  // Validazione base
  if (
    minutes === "" ||
    seconds === "" ||
    milliseconds === "" ||
    isNaN(minutes) ||
    isNaN(seconds) ||
    isNaN(milliseconds) ||
    minutes < 0 ||
    minutes > 59 ||
    seconds < 0 ||
    seconds > 59 ||
    milliseconds < 0 ||
    milliseconds > 999
  ) {
    showModalMessage(
      "manual-score",
      "Inserisci un tempo valido (MM: 0-59, SS: 0-59, mmm: 0-999).",
      "error"
    );
    return;
  }

  const formData = {
    player_id: playerId,
    player_name: playerName,
    minutes: parseInt(minutes),
    seconds: parseInt(seconds),
    milliseconds: parseInt(milliseconds),
  };

  const submitButton = $("#submit-manual-score-btn");
  submitButton.prop("disabled", true).text("Salvataggio...");
  $("#manual-score-message").hide(); // Nascondi messaggi precedenti

  $.ajax({
    url: "/submit_charlie_score", // NUOVO ENDPOINT
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(formData),
    success: function (response) {
      console.log("Submit score response:", response);
      if (response.success) {
        // Chiudi questo modal (e resetta UI principale) PRIMA di mostrare il prossimo
        closeManualScoreModal();

        // Controlla se qualificato
        if (response.qualified) {
          console.log("Player qualified! Reason:", response.reason);
          // Mostra il modal di qualifica passando i dati necessari
          showCharlieQualificationModal({
            player_id: response.player_id,
            player_name: response.player_name,
            recorded_score: response.recorded_score,
            player_type: response.player_type, // Sarà 'charlie'
            reason: response.reason,
          });
        } else {
          console.log("Player did not qualify.");
          // Potresti mostrare un messaggio temporaneo non modale qui se vuoi
          // ad es. usando un toast o una notifica
          // showToast("Punteggio G&G salvato!");
        }
        // Aggiorna la dashboard/liste se necessario (es. leaderboard visibile)
        // updateDashboard();
        updateSkipped(); // Aggiorna skipped se serve
        updateNextPlayer(); // Assicura che il prossimo sia corretto
      } else {
        showModalMessage(
          "manual-score",
          response.error || "Errore salvataggio punteggio.",
          "error"
        );
        submitButton.prop("disabled", false).text("Salva Tempo e Verifica");
      }
    },
    error: function (xhr, status, error) {
      console.error("Error submitting manual score:", status, error);
      const errorMsg = xhr.responseJSON
        ? xhr.responseJSON.error
        : "Errore di comunicazione.";
      showModalMessage("manual-score", errorMsg, "error");
      submitButton.prop("disabled", false).text("Salva Tempo e Verifica");
    },
  });
});

// Gestione invio form Qualification Charlie
$("#charlie-qualification-form").on("submit", function (event) {
  event.preventDefault();
  console.log("Submitting Charlie qualification form...");

  const formData = {
    // Dati dai campi nascosti
    player_id: $("#qual-player-id").val(),
    player_name: $("#qual-player-name").val(),
    score_minutes: $("#qual-score-minutes").val(),
    player_type: $("#qual-player-type").val(),
    qualification_reason: $("#qual-qualification-reason").val(),
    // Dati dai campi visibili
    first_name: $("#qual_first_name").val().trim(),
    last_name: $("#qual_last_name").val().trim(),
    phone_number: $("#qual_phone_number").val().trim(),
  };

  // Validazione base contatto
  if (!formData.first_name || !formData.last_name || !formData.phone_number) {
    showModalMessage(
      "charlie-qualification",
      "Per favore, compila Nome, Cognome e Telefono.",
      "error"
    );
    return;
  }

  const submitButton = $(this).find('button[type="submit"]');
  submitButton.prop("disabled", true).text("Salvataggio...");
  $("#charlie-qualification-message").hide();

  $.ajax({
    url: "/save_contact_info", // Endpoint generico per salvare contatti
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(formData),
    success: function (response) {
      console.log("Save contact info response:", response);
      if (response.success) {
        showModalMessage(
          "charlie-qualification",
          response.message || "Dati contatto salvati!",
          "success"
        );
        setTimeout(closeCharlieQualificationModal, 2500); // Chiudi dopo successo
      } else {
        showModalMessage(
          "charlie-qualification",
          response.message || "Errore salvataggio contatti.",
          "error"
        );
        submitButton.prop("disabled", false).text("Salva Dati Contatto");
      }
    },
    error: function (xhr, status, error) {
      console.error("Error saving contact info:", status, error);
      const errorMsg = xhr.responseJSON
        ? xhr.responseJSON.message
        : "Errore di comunicazione.";
      showModalMessage("charlie-qualification", errorMsg, "error");
      submitButton.prop("disabled", false).text("Salva Dati Contatto");
    },
  });
});

// timer per aggiornare la disponibilità delle piste e prossimo giocatore
setInterval(() => {
  if (!isGameActive) {
    // Aggiorna solo se non c'è un gioco attivo (per evitare conflitti)
    updateNextPlayer(); // Aggiorna prossimo giocatore e stato pista
    updateSkipped(); // Aggiorna lista skippati
  }
  if (isGameActive) {
    updateTimer(); // Aggiorna timer se attivo
  }
}, 1500); // Intervallo leggermente più lungo

$(document).ready(function () {
  console.log("Charlie Controls Ready");
  activateNextPlayer(); // Stato iniziale UI
  updateSkipped(); // Carica skippati iniziali

  // Listener per chiudere i modal (oltre ai bottoni nel form)
  $(".close-button").on("click", function () {
    const modalId = $(this).closest(".modal").attr("id");
    if (modalId === "manual-score-modal") {
      closeManualScoreModal();
    } else if (modalId === "charlie-qualification-modal") {
      closeCharlieQualificationModal();
    }
  });

  // Chiudi modal cliccando sullo sfondo
  $(".modal").on("click", function (event) {
    if ($(event.target).is(".modal")) {
      const modalId = $(this).attr("id");
      if (modalId === "manual-score-modal") {
        closeManualScoreModal();
      } else if (modalId === "charlie-qualification-modal") {
        closeCharlieQualificationModal();
      }
    }
  });
});
