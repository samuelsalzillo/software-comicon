let timerInterval;
let startTime;
let isGameActive = false;

function updateNextPlayer() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      // Aggiorna prossimo giocatore FIGT
      const figtQueue = data.figt || [];
      if (figtQueue.length > 0) {
        const nextPlayer = figtQueue[0];
        $("#next-player").text(`${nextPlayer.id}`);
        $("#next-player-btn").prop("disabled", isGameActive);
        console.log(`Next player FIGT: ${nextPlayer.id}`);
      } else {
        $("#next-player").text("Nessun Giocatore In Coda");
        $("#next-player-btn").prop("disabled", !isGameActive && figtQueue.length === 0);
      }

      // Aggiorna stato pista FIGT
      updateTrackStatus(data);

      // Aggiorna giocatore corrente FIGT
      if (data.current_player_figt) {
        $("#current-player").text(`${data.current_player_figt_name || ""} - ${data.current_player_figt}`);
      } else if (!isGameActive) {
        $("#current-player").text("-");
      }
    })
    .catch((error) => console.error("Error fetching simulation data:", error));
}

function updateSkipped() {
  fetch("/get_skipped")
    .then((response) => response.json())
    .then((data) => {
      const container = document.getElementById("skipped-figt-buttons");
      if (!container) return;
      container.innerHTML = "";
      if (data.figt && data.figt.length > 0) {
        data.figt.forEach((player) => {
          const button = document.createElement("button");
          button.className = "skipped-button figt";
          button.textContent = player.id;
          button.onclick = () => restoreSkipped(player.id);
          container.appendChild(button);
        });
      }
    })
    .catch((error) => console.error("Errore recupero skipped:", error));
}

function restoreSkipped(playerId) {
  $.ajax({
    url: "/restore_skipped_as_next",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ id: playerId }),
    success: function () {
      updateNextPlayer();
      updateSkipped();
    },
    error: function (xhr) {
      alert(`Errore ripristino: ${xhr.responseJSON?.error || "Errore sconosciuto"}`);
    },
  });
}

function skipNextPlayerFigt() {
  const nextPlayerId = document.getElementById("next-player").textContent;
  if (nextPlayerId && nextPlayerId !== "Nessun Giocatore In Coda" && nextPlayerId !== "-") {
    fetch("/skip_figt_player", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: nextPlayerId }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          updateNextPlayer();
          updateSkipped();
        } else {
          alert(data.error);
        }
      });
  }
}

function updateTrackStatus(data) {
  const figtStatus = data.figt_status || "Libera";
  const figtRemaining = data.figt_remaining || "0min";
  const canStartFigt = figtStatus === "Libera";

  $("#start-btn").prop("disabled", !canStartFigt || isGameActive);
  $("#status").text(`${figtStatus} - ${figtRemaining}`);

  $("#stop-btn").prop("disabled", !isGameActive);
  
  const hasNextPlayer = $("#next-player").text() !== "Nessun Giocatore In Coda" && $("#next-player").text() !== "-";
  $("#next-player-btn").prop("disabled", isGameActive || !hasNextPlayer);
}

function updateTimer() {
  if (!isGameActive || !startTime) return;
  const now = new Date();
  const diff = Math.floor((now - startTime) / 1000);
  const minutes = Math.floor(diff / 60).toString().padStart(2, "0");
  const seconds = (diff % 60).toString().padStart(2, "0");
  $("#timer").text(`${minutes}:${seconds}`);
}

function activateNextPlayer() {
  isGameActive = false;
  clearInterval(timerInterval);
  startTime = null;
  $("#timer").text("00:00");
  $("#current-player").text("-");
  updateNextPlayer();
}

function pressButton(button) {
  if (button === "figt_start") {
    $.ajax({
      url: "/button_press",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ button: button }),
      success: function (response) {
        if (response.success) {
          startTime = new Date();
          localStorage.setItem("startTimeFigt", startTime.toISOString());
          isGameActive = true;
          timerInterval = setInterval(updateTimer, 1000);
          $("#current-player").text(response.current_player_figt);
          updateNextPlayer();
        } else {
          alert(response.error);
        }
      },
    });
  } else if (button === "figt_stop" && isGameActive) {
    $.ajax({
      url: "/button_press",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ button: button }),
      success: function (response) {
        if (response.success) {
          isGameActive = false;
          clearInterval(timerInterval);
          showManualScoreModal(response.player_id, response.player_name);
        } else {
          alert(response.error);
        }
      },
    });
  }
}

function showManualScoreModal(playerId, playerName) {
  $("#manual-player-id").val(playerId);
  $("#manual-player-name").val(playerName);
  $("#manual-score-form")[0].reset();
  $("#manual-score-message").hide();
  $("#manual-score-modal").css("display", "flex");
}

function closeManualScoreModal() {
  $("#manual-score-modal").fadeOut();
  activateNextPlayer();
}

$("#manual-score-form").on("submit", function (e) {
  e.preventDefault();
  const formData = {
    player_id: $("#manual-player-id").val(),
    player_name: $("#manual-player-name").val(),
    minutes: parseInt($("#score_minutes").val()),
    seconds: parseInt($("#score_seconds").val()),
    milliseconds: parseInt($("#score_milliseconds").val()),
  };

  $.ajax({
    url: "/submit_figt_score",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(formData),
    success: function (response) {
      if (response.success) {
        closeManualScoreModal();
        if (response.is_top_6) {
          showFigtQualificationModal(response.entry_id);
        }
      } else {
        alert(response.error);
      }
    },
  });
});

function showFigtQualificationModal(entryId) {
  $("#qual-entry-id").val(entryId);
  $("#figt-qualification-form")[0].reset();
  $("#figt-qualification-modal").css("display", "flex");
}

function closeFigtQualificationModal() {
  $("#figt-qualification-modal").fadeOut();
}

$("#figt-qualification-form").on("submit", function (e) {
  e.preventDefault();
  const formData = {
    entry_id: $("#qual-entry-id").val(),
    first_name: $("#qual_first_name").val(),
    last_name: $("#qual_last_name").val(),
    phone: $("#qual_phone_number").val(),
  };

  $.ajax({
    url: "/save_figt_contact",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(formData),
    success: function (response) {
      if (response.success) {
        closeFigtQualificationModal();
      } else {
        alert(response.error);
      }
    },
  });
});

$(document).ready(function () {
  updateNextPlayer();
  updateSkipped();
  setInterval(updateNextPlayer, 5000);
  setInterval(updateSkipped, 5000);
});
