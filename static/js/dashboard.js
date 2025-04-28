function formatTimeRome(date) {
  if (!date) return "N/D";

  // Crea un formatter per l'ora di Roma
  const options = {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Europe/Rome",
  };

  return new Date(date).toLocaleTimeString("it-IT", options);
}

function updateDashboard() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      // Aggiorna la coda coppie

      // Controlla e imposta il colore del testo per i campi "Nessun Giocatore in coda"
      // Funzione per determinare il colore in base all'ID del giocatore
      function getPlayerColor(playerId) {
        if (!playerId || playerId === "Nessun Giocatore in coda")
          return "#000000";
        if (playerId.includes("GIALLO")) return "#FFD700";
        if (playerId.includes("ROSA")) return "#FFC0CB";
        if (playerId.includes("VERDE")) return "#008000";
        if (playerId.includes("NERO")) return "#000000";
        if (playerId.includes("BLU")) return "#0000FF";
        if (playerId.includes("BIANCO")) return "#FFFFFF";
        if (playerId.includes("ROSSO")) return "#FF0000";
        return "#000000";
      }

      // Array degli elementi da controllare
      const nextPlayerFields = [
        "next-player-alfa-bravo-text",
        "next-player-alfa-bravo2-text",
        "next-charlie-text",
        "next-statico-text",
      ];

      // Aggiorna il colore per ogni elemento
      nextPlayerFields.forEach((fieldId) => {
        const element = document.getElementById(fieldId);
        if (element) {
          element.style.color = getPlayerColor(element.textContent);
        }
      });

      const couplesBoard = document.getElementById("couples-board");
      if (couplesBoard) {
        couplesBoard.innerHTML = "";
        data.couples.forEach((player) => {
          const timeDisplay =
            player.estimated_time === "PROSSIMO INGRESSO"
              ? "PROSSIMO INGRESSO"
              : formatTimeRome(player.estimated_time);
          const li = document.createElement("li");
          li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
          couplesBoard.appendChild(li);
        });
      }

      // Aggiorna la coda singoli
      const singlesBoard = document.getElementById("singles-board");
      if (singlesBoard) {
        singlesBoard.innerHTML = "";
        data.singles.forEach((player) => {
          const timeDisplay =
            player.estimated_time === "PROSSIMO INGRESSO"
              ? "PROSSIMO INGRESSO"
              : formatTimeRome(player.estimated_time);
          const li = document.createElement("li");
          li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
          singlesBoard.appendChild(li);
        });
      }

      // se non ci sono singoli ne coppie in coda nella board, resettami il prossimo giocatore
      if (data.couples.length === 0 && data.singles.length === 0) {
        const nextPlayerAlfaBravoText = document.getElementById(
          "next-player-alfa-bravo-text"
        );
        if (nextPlayerAlfaBravoText) {
          nextPlayerAlfaBravoText.textContent = "Nessun Giocatore in coda";
        }
      }

      // se non ci sono singoli ne coppie in coda nella board, resettami il prossimo giocatore
      if (data.couples2.length === 0 && data.singles2.length === 0) {
        const nextPlayerAlfaBravo2Text = document.getElementById(
          "next-player-alfa-bravo2-text"
        );
        if (nextPlayerAlfaBravo2Text) {
          nextPlayerAlfaBravo2Text.textContent = "Nessun Giocatore in coda";
        }
      }

      // Aggiorna la coda coppie 2 (Viola)
      const couples2Board = document.getElementById("couples2-board");
      if (couples2Board) {
        couples2Board.innerHTML = "";
        if (data.couples2) {
          // Verifica che data.couples2 esista
          data.couples2.forEach((player) => {
            const timeDisplay =
              player.estimated_time === "PROSSIMO INGRESSO"
                ? "PROSSIMO INGRESSO"
                : formatTimeRome(player.estimated_time);
            const li = document.createElement("li");
            li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
            couples2Board.appendChild(li);
          });
        }
      }

      // Aggiorna la coda singoli 2 (Bianco)
      const singles2Board = document.getElementById("singles2-board");
      if (singles2Board) {
        singles2Board.innerHTML = "";
        if (data.singles2) {
          // Verifica che data.singles2 esista
          data.singles2.forEach((player) => {
            const timeDisplay =
              player.estimated_time === "PROSSIMO INGRESSO"
                ? "PROSSIMO INGRESSO"
                : formatTimeRome(player.estimated_time);
            const li = document.createElement("li");
            li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
            singles2Board.appendChild(li);
          });
        }
      }

      // Aggiorna prossimo giocatore Alfa2/Bravo2
      const nextPlayerAlfaBravo2Text = document.getElementById(
        "next-player-alfa-bravo2-text"
      );
      if (nextPlayerAlfaBravo2Text) {
        if (data.next_player_alfa_bravo_id2) {
          nextPlayerAlfaBravo2Text.textContent = `${data.next_player_alfa_bravo_id2}`;
          // Aggiungi la classe CSS appropriata in base al tipo di giocatore
          if (data.next_player_alfa_bravo_id2.includes("ROSA")) {
            nextPlayerAlfaBravo2Text.className = "next-player couple2";
          } else if (data.next_player_alfa_bravo_id2.includes("BIANCO")) {
            nextPlayerAlfaBravo2Text.className = "next-player single2";
          }
        } else {
          nextPlayerAlfaBravo2Text.textContent = "Nessun Giocatore in coda";
        }
      }

      // Aggiorna giocatore corrente in Alfa2
      const currentPlayerAlfa2 = document.getElementById(
        "current-player-alfa2"
      );
      const alfa2Duration = document.getElementById("alfa2-duration");
      if (currentPlayerAlfa2 && alfa2Duration) {
        if (data.current_player_alfa2) {
          currentPlayerAlfa2.textContent = data.current_player_alfa2["id"];
          alfa2Duration.textContent = data.alfa2_duration || "-";
        } else {
          currentPlayerAlfa2.textContent = "Nessun giocatore";
          alfa2Duration.textContent = "-";
        }
      }

      // Aggiorna giocatore corrente in Bravo2
      const currentPlayerBravo2 = document.getElementById(
        "current-player-bravo2"
      );
      const bravo2Duration = document.getElementById("bravo2-duration");
      if (currentPlayerBravo2 && bravo2Duration) {
        if (data.current_player_bravo2) {
          currentPlayerBravo2.textContent = data.current_player_bravo2.id;
          bravo2Duration.textContent = data.bravo2_duration || "-";
        } else {
          currentPlayerBravo2.textContent = "Nessun giocatore";
          bravo2Duration.textContent = "-";
        }
      }

      // Aggiorna stato e colore card ALFA2
      const alfa2State = $("#alfa2-state");
      const alfa2Remaining = $("#alfa2-remaining");
      const alfa2Status = $("#alfa2-status");
      if (alfa2State && alfa2Remaining && alfa2Status) {
        // Usa .length con jQuery
        alfa2State.text(data.alfa2_status || "-");
        alfa2Remaining.text(data.alfa2_remaining || "-");
        alfa2Status
          .removeClass("occupied free")
          .addClass(data.alfa2_status === "Occupata" ? "occupied" : "free");
      }

      // Aggiorna stato e colore card BRAVO2
      const bravo2State = $("#bravo2-state");
      const bravo2Remaining = $("#bravo2-remaining");
      const bravo2Status = $("#bravo2-status");
      if (bravo2State && bravo2Remaining && bravo2Status) {
        // Usa .length con jQuery
        bravo2State.text(data.bravo2_status || "-");
        bravo2Remaining.text(data.bravo2_remaining || "-");
        bravo2Status
          .removeClass("occupied free")
          .addClass(data.bravo2_status === "Occupata" ? "occupied" : "free");
      }

      // se non ci sono charlie in coda nella board, resettami il prossimo giocatore
      if (data.charlie.length === 0) {
        const nextCharlieText = document.getElementById("next-charlie-text");
        if (nextCharlieText) {
          nextCharlieText.textContent = "Nessun Giocatore in coda";
        }
      }

      // Aggiorna la coda Charlie
      const charlieBoard = document.getElementById("charlie-board");
      if (charlieBoard) {
        charlieBoard.innerHTML = "";
        data.charlie.forEach((player) => {
          const timeDisplay =
            player.estimated_time === "PROSSIMO INGRESSO"
              ? "PROSSIMO INGRESSO"
              : formatTimeRome(player.estimated_time);
          const li = document.createElement("li");
          li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
          charlieBoard.appendChild(li);
        });
      }

      // Aggiorna la coda Statico
      const staticoBoard = document.getElementById("statico-board");
      if (staticoBoard) {
        staticoBoard.innerHTML = "";
        if (data.statico) {
          data.statico.forEach((player) => {
            const timeDisplay =
              player.estimated_time === "PROSSIMO INGRESSO"
                ? "PROSSIMO INGRESSO"
                : formatTimeRome(player.estimated_time);
            const li = document.createElement("li");
            li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
            staticoBoard.appendChild(li);
          });
        }
      }

      // Aggiorna il prossimo giocatore statico
      const nextStaticoText = document.getElementById("next-statico-text");
      if (
        nextStaticoText &&
        data.next_player_statico_id &&
        data.next_player_statico_name
      ) {
        nextStaticoText.textContent =
          `${data.next_player_statico_id}` || "nessun giocatore in coda";
        // Aggiungi la classe CSS appropriata per Statico
        if (data.next_player_statico_id.includes("ROSSO")) {
          nextStaticoText.className = "next-player statico";
        }
      }

      const nextPlayerAlfaBravoText = document.getElementById(
        "next-player-alfa-bravo-text"
      );
      if (
        nextPlayerAlfaBravoText &&
        data.next_player_alfa_bravo_id &&
        data.next_player_alfa_bravo_name
      ) {
        nextPlayerAlfaBravoText.textContent =
          `${data.next_player_alfa_bravo_id}` || "nessun giocatore in coda";
        // Aggiungi la classe CSS appropriata in base al tipo di giocatore
        if (data.next_player_alfa_bravo_id.includes("GIALLO")) {
          nextPlayerAlfaBravoText.className = "next-player couple";
        } else if (data.next_player_alfa_bravo_id.includes("BLU")) {
          nextPlayerAlfaBravoText.className = "next-player single";
        }
      }

      const nextCharlieText = document.getElementById("next-charlie-text");
      if (
        nextCharlieText &&
        data.next_player_charlie_id &&
        data.next_player_charlie_name
      ) {
        nextCharlieText.textContent =
          `${data.next_player_charlie_id}` || "nessun giocatore in coda";
        // Aggiungi la classe CSS appropriata per Charlie
        if (data.next_player_charlie_id.includes("VERDE")) {
          nextCharlieText.className = "next-player charlie";
        }
      }

      const nextCharliePlayer = document.getElementById("next-charlie-player");
      if (nextCharliePlayer) {
        nextCharliePlayer.textContent = data.next_charlie_player || "-";
      }

      // Aggiorna il giocatore corrente in Alfa
      const currentPlayerAlfa = document.getElementById("current-player-alfa");
      const alfaDuration = document.getElementById("alfa-duration");
      if (currentPlayerAlfa && alfaDuration) {
        if (data.current_player_alfa) {
          currentPlayerAlfa.textContent = data.current_player_alfa["id"];
          alfaDuration.textContent = data.alfa_duration;
        } else {
          currentPlayerAlfa.textContent = "Nessun giocatore";
          alfaDuration.textContent = "-";
        }
      }

      // Aggiorna il giocatore corrente in Bravo
      const currentPlayerBravo = document.getElementById(
        "current-player-bravo"
      );
      const bravoDuration = document.getElementById("bravo-duration");
      if (currentPlayerBravo && bravoDuration) {
        if (data.current_player_bravo) {
          currentPlayerBravo.textContent = data.current_player_bravo.id;
          bravoDuration.textContent = data.bravo_duration;
        } else {
          currentPlayerBravo.textContent = "Nessun giocatore";
          bravoDuration.textContent = "-";
        }
      }

      // Aggiorna il giocatore corrente in Charlie
      const currentPlayerCharlie = document.getElementById(
        "current-player-charlie"
      );
      const charlieDuration = document.getElementById("charlie-duration");
      if (currentPlayerCharlie && charlieDuration) {
        if (data.current_player_charlie) {
          currentPlayerCharlie.textContent = data.current_player_charlie.id;
          charlieDuration.textContent = data.charlie_duration;
        } else {
          currentPlayerCharlie.textContent = "Nessun giocatore";
          charlieDuration.textContent = "-";
        }
      }

      // Aggiorna i giocatori correnti in pista statico
      const currentPlayerDelta = document.getElementById(
        "current-player-delta"
      );
      const deltaDuration = document.getElementById("delta-duration");
      if (currentPlayerDelta && deltaDuration) {
        if (data.current_player_delta) {
          currentPlayerDelta.textContent = data.current_player_delta.id;
          deltaDuration.textContent = data.delta_duration;
        } else {
          currentPlayerDelta.textContent = "Nessun giocatore";
          deltaDuration.textContent = "-";
        }
      }

      const currentPlayerEcho = document.getElementById("current-player-echo");
      const echoDuration = document.getElementById("echo-duration");
      if (currentPlayerEcho && echoDuration) {
        if (data.current_player_echo) {
          currentPlayerEcho.textContent = data.current_player_echo.id;
          echoDuration.textContent = data.echo_duration;
        } else {
          currentPlayerEcho.textContent = "Nessun giocatore";
          echoDuration.textContent = "-";
        }
      }

      // Aggiorna lo stato e il colore della card ALFA
      const alfaState = $("#alfa-state");
      const alfaRemaining = $("#alfa-remaining");
      const alfaStatus = $("#alfa-status");
      if (alfaState && alfaRemaining && alfaStatus) {
        alfaState.text(data.alfa_status);
        alfaRemaining.text(data.alfa_remaining);
        alfaStatus
          .removeClass("occupied free")
          .addClass(data.alfa_status === "Occupata" ? "occupied" : "free");
      }

      // Aggiorna lo stato e il colore della card BRAVO
      const bravoState = $("#bravo-state");
      const bravoRemaining = $("#bravo-remaining");
      const bravoStatus = $("#bravo-status");
      if (bravoState && bravoRemaining && bravoStatus) {
        bravoState.text(data.bravo_status);
        bravoRemaining.text(data.bravo_remaining);
        bravoStatus
          .removeClass("occupied free")
          .addClass(data.bravo_status === "Occupata" ? "occupied" : "free");
      }

      // Aggiorna lo stato e il colore della card CHARLIE
      const charlieState = $("#charlie-state");
      const charlieRemaining = $("#charlie-remaining");
      const charlieStatus = $("#charlie-status");
      if (charlieState && charlieRemaining && charlieStatus) {
        charlieState.text(data.charlie_status);
        charlieRemaining.text(data.charlie_remaining);
        charlieStatus
          .removeClass("occupied free")
          .addClass(data.charlie_status === "Occupata" ? "occupied" : "free");
      }

      // Aggiorna lo stato delle piste statico
      const deltaState = $("#delta-state");
      const deltaRemaining = $("#delta-remaining");
      const deltaStatus = $("#delta-status");
      if (deltaState && deltaRemaining && deltaStatus) {
        deltaState.text(data.delta_status);
        deltaRemaining.text(data.delta_remaining);
        deltaStatus
          .removeClass("occupied free")
          .addClass(data.delta_status === "Occupata" ? "occupied" : "free");
      }

      const echoState = $("#echo-state");
      const echoRemaining = $("#echo-remaining");
      const echoStatus = $("#echo-status");
      if (echoState && echoRemaining && echoStatus) {
        echoState.text(data.echo_status);
        echoRemaining.text(data.echo_remaining);
        echoStatus
          .removeClass("occupied free")
          .addClass(data.echo_status === "Occupata" ? "occupied" : "free");
      }
    });

  // Aggiorna la visualizzazione degli skippati
  updateSkipped();
}

function skipNextPlayerAlfaBravo2() {
  const nextPlayer = document.getElementById(
    "next-player-alfa-bravo2-text"
  ).textContent;
  if (
    nextPlayer &&
    nextPlayer !== "Nessun Giocatore In Coda" &&
    nextPlayer !== "-"
  ) {
    fetch("/skip_next_player_alfa_bravo2", {
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
        // Aggiorna solo gli elementi necessari
        if (data.next_player_alfa_bravo_id) {
          document.getElementById("next-player-alfa-bravo2-text").textContent =
            data.next_player_alfa_bravo2_id;
        } else {
          document.getElementById("next-player-alfa-bravo2-text").textContent =
            "Nessun Giocatore In Coda";
        }
        updateSkipped(); // Aggiorna esplicitamente la lista degli skippati
        updateBoards(); // Aggiorna le board
      })
      .catch((error) => {
        console.error("Errore durante lo skip:", error);
      });
  }
}

// Aggiorna la funzione skipNextPlayerAlfaBravo
function skipNextPlayerAlfaBravo() {
  const nextPlayer = document.getElementById(
    "next-player-alfa-bravo-text"
  ).textContent;
  if (
    nextPlayer &&
    nextPlayer !== "Nessun Giocatore In Coda" &&
    nextPlayer !== "-"
  ) {
    fetch("/skip_next_player_alfa_bravo", {
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
        // Aggiorna solo gli elementi necessari
        if (data.next_player_alfa_bravo_id) {
          document.getElementById("next-player-alfa-bravo-text").textContent =
            data.next_player_alfa_bravo_id;
        } else {
          document.getElementById("next-player-alfa-bravo-text").textContent =
            "Nessun Giocatore In Coda";
        }
        updateSkipped(); // Aggiorna esplicitamente la lista degli skippati
        updateBoards(); // Aggiorna le board
      })
      .catch((error) => {
        console.error("Errore durante lo skip:", error);
      });
  }
}

// Aggiorna la funzione skipNextPlayerCharlie
function skipNextPlayerCharlie() {
  const nextPlayer = document.getElementById("next-charlie-text").textContent;
  if (
    nextPlayer &&
    nextPlayer !== "Nessun Giocatore In Coda" &&
    nextPlayer !== "-"
  ) {
    fetch("/skip_charlie_player", {
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
        if (data.next_player_charlie_id) {
          document.getElementById("next-charlie-text").textContent =
            data.next_player_charlie_id;
        } else {
          document.getElementById("next-charlie-text").textContent =
            "Nessun Giocatore In Coda";
        }
        updateSkipped();
        updateBoards();
      })
      .catch((error) => {
        console.error("Errore durante lo skip:", error);
      });
  }
}

// Aggiungi la funzione per lo skip statico
function skipNextPlayerStatico() {
  const nextPlayer = document.getElementById("next-statico-text").textContent;
  if (
    nextPlayer &&
    nextPlayer !== "Nessun Giocatore In Coda" &&
    nextPlayer !== "-"
  ) {
    fetch("/skip_statico_player", {
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
        if (data.next_player_statico_id) {
          document.getElementById("next-statico-text").textContent =
            data.next_player_statico_id;
        } else {
          document.getElementById("next-statico-text").textContent =
            "Nessun Giocatore In Coda";
        }
        updateSkipped();
        updateBoards();
      })
      .catch((error) => {
        console.error("Errore durante lo skip:", error);
      });
  }
}
function updateSkippedList() {
  $.get("/get_skipped", function (data) {
    const skippedList = $("#skipped-list");
    skippedList.empty();

    data.couples.forEach(function (couple) {
      skippedList.append(`
                  <div class="skipped-item couple" onclick="restoreSkipped('${couple.id}')">
                      ${couple.id}
                  </div>
              `);
    });

    data.singles.forEach(function (single) {
      skippedList.append(`
                  <div class="skipped-item single" onclick="restoreSkipped('${single.id}')">
                      ${single.id}
                  </div>
              `);
    });
  });
}

function restoreSkipped(playerId) {
  console.log("Tentativo di ripristino giocatore:", playerId);
  $.ajax({
    url: "/restore_skipped_as_next",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ id: playerId }),
    success: function (response) {
      console.log("Giocatore ripristinato con successo:", playerId);
      console.log("Risposta server:", response);
      updateSkippedList();
      updateBoards();
    },
    error: function (error) {
      console.error("Errore durante il ripristino del giocatore:", error);
    },
  });
}

function skipCharliePlayer() {
  const nextPlayer = document.getElementById("next-charlie-text").textContent;
  fetch("/skip_charlie_player", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then(() => updateDashboard());
}

function updateSkipped() {
  fetch("/get_skipped")
    .then((response) => response.json())
    .then((data) => {
      const createSkippedButtons = (containerId, players, className) => {
        const container = document.getElementById(containerId);
        if (container) {
          container.innerHTML = ""; // Pulisci prima di aggiungere
          if (players && players.length > 0) {
            players.forEach((player) => {
              const button = document.createElement("button");
              button.className = `skipped-button ${className}`; // Usa la classe CSS corretta
              button.textContent = player.id;
              button.onclick = () => restoreSkipped(player.id);
              container.appendChild(button);
            });
          }
        } else {
          // console.warn(`Container skipped non trovato: ${containerId}`);
        }
      };

      // Aggiorna tutte le sezioni, incluse le nuove
      createSkippedButtons("skipped-couples-buttons", data.couples, "couple");
      createSkippedButtons("skipped-singles-buttons", data.singles, "single");
      createSkippedButtons(
        "skipped-couples2-buttons",
        data.couples2,
        "couple2"
      ); // NUOVO
      createSkippedButtons(
        "skipped-singles2-buttons",
        data.singles2,
        "single2"
      ); // NUOVO
      createSkippedButtons("skipped-charlie-buttons", data.charlie, "charlie");
      createSkippedButtons("skipped-statico-buttons", data.statico, "statico");
    })
    .catch((error) => {
      console.error("Errore durante il recupero degli skipped:", error);
    });
}

// Assicurati che la funzione venga chiamata regolarmente
setInterval(() => {
  updateSkipped();
  updateDashboard();
}, 1000);
// Aggiorna la dashboard ogni secondo

$(document).ready(function () {
  updateSkipped();
  updateDashboard();
});

function updateBoards() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      // Aggiorna la coda coppie
      const couplesBoard = document.getElementById("couples-board");
      if (couplesBoard) {
        couplesBoard.innerHTML = "";
        data.couples.forEach((player) => {
          const timeDisplay =
            player.estimated_time === "PROSSIMO INGRESSO"
              ? "PROSSIMO INGRESSO"
              : formatTimeRome(player.estimated_time);
          const li = document.createElement("li");
          li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
          couplesBoard.appendChild(li);
        });
      }

      // Aggiorna la coda singoli
      const singlesBoard = document.getElementById("singles-board");
      if (singlesBoard) {
        singlesBoard.innerHTML = "";
        data.singles.forEach((player) => {
          const timeDisplay =
            player.estimated_time === "PROSSIMO INGRESSO"
              ? "PROSSIMO INGRESSO"
              : formatTimeRome(player.estimated_time);
          const li = document.createElement("li");
          li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button class="trash-button" onclick="deletePlayer('${player.id}')"><img class="trash-icon" src="/static/icons/trash.svg" alt="Delete"></button>`;
          singlesBoard.appendChild(li);
        });
      }

      // se non ci sono singoli ne coppie in coda nella board, resettami il prossimo giocatore
      if (data.couples.length === 0 && data.singles.length === 0) {
        const nextPlayerAlfaBravoText = document.getElementById(
          "next-player-alfa-bravo-text"
        );
        if (nextPlayerAlfaBravoText) {
          nextPlayerAlfaBravoText.textContent = "Nessun Giocatore in coda";
        }
      }
      // se non ci sono singoli ne coppie in coda nella board, resettami il prossimo giocatore
      if (data.couples2.length === 0 && data.singles2.length === 0) {
        const nextPlayerAlfaBravo2Text = document.getElementById(
          "next-player-alfa-bravo2-text"
        );
        if (nextPlayerAlfaBravo2Text) {
          nextPlayerAlfaBravo2Text.textContent = "Nessun Giocatore in coda";
        }
      }

      // Aggiorna la coda Charlie
      const charlieBoard = document.getElementById("charlie-board");
      if (charlieBoard) {
        charlieBoard.innerHTML = "";
        data.charlie.forEach((player) => {
          const timeDisplay =
            player.estimated_time === "PROSSIMO INGRESSO"
              ? "PROSSIMO INGRESSO"
              : formatTimeRome(player.estimated_time);
          const li = document.createElement("li");
          li.innerHTML = `${player.id} - Ingresso: ${timeDisplay} <button onclick="deletePlayer('${player.id}')"><img src="/static/icons/trash.svg" alt="Delete"></button>`;
          charlieBoard.appendChild(li);
        });
      }

      const nextPlayerAlfaBravoText = document.getElementById(
        "next-player-alfa-bravo-text"
      );
      if (
        nextPlayerAlfaBravoText &&
        data.next_player_alfa_bravo_id &&
        data.next_player_alfa_bravo_name
      ) {
        nextPlayerAlfaBravoText.textContent =
          `${data.next_player_alfa_bravo_id}` || "nessun giocatore in coda";
        // Aggiungi la classe CSS appropriata in base al tipo di giocatore
        if (data.next_player_alfa_bravo_id.includes("GIALLO")) {
          nextPlayerAlfaBravoText.className = "next-player couple";
        } else if (data.next_player_alfa_bravo_id.includes("BLU")) {
          nextPlayerAlfaBravoText.className = "next-player single";
        }
      }
      const nextPlayerAlfaBravo2Text = document.getElementById(
        "next-player-alfa-bravo2-text"
      );
      if (
        nextPlayerAlfaBravo2Text &&
        data.next_player_alfa_bravo2_id &&
        data.next_player_alfa_bravo2_name
      ) {
        nextPlayerAlfaBravo2Text.textContent =
          `${data.next_player_alfa_bravo2_id}` || "nessun giocatore in coda";
        // Aggiungi la classe CSS appropriata in base al tipo di giocatore
        if (data.next_player_alfa_bravo2_id.includes("ROSA")) {
          nextPlayerAlfaBravo2Text.className = "next-player couple2";
        } else if (data.next_player_alfa_bravo2_id.includes("BIANCO")) {
          nextPlayerAlfaBravo2Text.className = "next-player single2";
        }
      }

      const nextCharlieText = document.getElementById("next-charlie-text");
      if (
        nextCharlieText &&
        data.next_player_charlie_id &&
        data.next_player_charlie_name
      ) {
        nextCharlieText.textContent =
          `${data.next_player_charlie_id}` || "nessun giocatore in coda";
        // Aggiungi la classe CSS appropriata per Charlie
        if (data.next_player_charlie_id.includes("VERDE")) {
          nextCharlieText.className = "next-player charlie";
        }
      }

      // Aggiorna il giocatore corrente in Alfa
      const currentPlayerAlfa = document.getElementById("current-player-alfa");
      const alfaDuration = document.getElementById("alfa-duration");
      if (currentPlayerAlfa && alfaDuration) {
        if (data.current_player_alfa) {
          currentPlayerAlfa.textContent = data.current_player_alfa["id"];
          alfaDuration.textContent = data.alfa_duration;
        } else {
          currentPlayerAlfa.textContent = "Nessun giocatore";
          alfaDuration.textContent = "-";
        }
      }

      // Aggiorna il giocatore corrente in Bravo
      const currentPlayerBravo = document.getElementById(
        "current-player-bravo"
      );
      const bravoDuration = document.getElementById("bravo-duration");
      if (currentPlayerBravo && bravoDuration) {
        if (data.current_player_bravo) {
          currentPlayerBravo.textContent = data.current_player_bravo.id;
          bravoDuration.textContent = data.bravo_duration;
        } else {
          currentPlayerBravo.textContent = "Nessun giocatore";
          bravoDuration.textContent = "-";
        }
      }

      // Aggiorna il giocatore corrente in Charlie
      const currentPlayerCharlie = document.getElementById(
        "current-player-charlie"
      );
      const charlieDuration = document.getElementById("charlie-duration");
      if (currentPlayerCharlie && charlieDuration) {
        if (data.current_player_charlie) {
          currentPlayerCharlie.textContent = data.current_player_charlie.id;
          charlieDuration.textContent = data.charlie_duration;
        } else {
          currentPlayerCharlie.textContent = "Nessun giocatore";
          charlieDuration.textContent = "-";
        }
      }

      // Aggiorna lo stato e il colore della card ALFA
      const alfaState = $("#alfa-state");
      const alfaRemaining = $("#alfa-remaining");
      const alfaStatus = $("#alfa-status");
      if (alfaState && alfaRemaining && alfaStatus) {
        alfaState.text(data.alfa_status);
        alfaRemaining.text(data.alfa_remaining);
        alfaStatus
          .removeClass("occupied free")
          .addClass(data.alfa_status === "Occupata" ? "occupied" : "free");
      }

      // Aggiorna lo stato e il colore della card BRAVO
      const bravoState = $("#bravo-state");
      const bravoRemaining = $("#bravo-remaining");
      const bravoStatus = $("#bravo-status");
      if (bravoState && bravoRemaining && bravoStatus) {
        bravoState.text(data.bravo_status);
        bravoRemaining.text(data.bravo_remaining);
        bravoStatus
          .removeClass("occupied free")
          .addClass(data.bravo_status === "Occupata" ? "occupied" : "free");
      }

      // Aggiorna lo stato e il colore della card CHARLIE
      const charlieState = $("#charlie-state");
      const charlieRemaining = $("#charlie-remaining");
      const charlieStatus = $("#charlie-status");
      if (charlieState && charlieRemaining && charlieStatus) {
        charlieState.text(data.charlie_status);
        charlieRemaining.text(data.charlie_remaining);
        charlieStatus
          .removeClass("occupied free")
          .addClass(data.charlie_status === "Occupata" ? "occupied" : "free");
      }
    });
}

function addCharliePlayer() {
  const name = document.getElementById("playerName").value;
  const id = document.getElementById("playerId").value;
  fetch("/add_charlie_player", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: name, id: id }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert("Giocatore aggiunto con successo!");
        updateDashboard(); // Update the dashboard to reflect the new Charlie player
      } else {
        alert("Errore nell'aggiunta del giocatore.");
      }
    });
}

// Funzione formatTimeRome (assicurati sia definita)
function formatTimeRome(date) {
  if (!date || date === "N/D") return "N/D";
  try {
    const options = {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Europe/Rome",
    };
    // Prova a creare la data, gestendo possibili errori
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) {
      // Controlla se la data non è valida
      return "N/D";
    }
    return dateObj.toLocaleTimeString("it-IT", options);
  } catch (e) {
    console.error("Errore formattazione data:", date, e);
    return "N/D"; // Ritorna N/D in caso di errore
  }
}
// Funzione formatTimeRome (assicurati sia definita)
function formatTimeRome(date) {
  if (!date || date === "N/D") return "N/D";
  try {
    const options = {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Europe/Rome",
    };
    // Prova a creare la data, gestendo possibili errori
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) {
      // Controlla se la data non è valida
      return "N/D";
    }
    return dateObj.toLocaleTimeString("it-IT", options);
  } catch (e) {
    console.error("Errore formattazione data:", date, e);
    return "N/D"; // Ritorna N/D in caso di errore
  }
}

function deletePlayer(playerId) {
  fetch(`/delete_player`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id: playerId }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        updateDashboard();
      } else {
        alert("Errore nella cancellazione del giocatore.");
      }
    });
}
