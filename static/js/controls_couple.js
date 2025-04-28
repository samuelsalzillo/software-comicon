let timerInterval;
let startTime;
let isGameActive = false;

function updateNextPlayer() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      if (data.couples && data.couples.length > 0) {
        const nextPlayer = data.couples[0]; // Ora sarà un oggetto con id e name
        $("#next-player").text(`${nextPlayer.id}`);
        $("#next-player-btn").prop("disabled", false);
        console.log(`Next player to start: ${nextPlayer.id}`); // Log del prossimo giocatore
      } else {
        $("#next-player").text("-");
        $("#next-player-btn").prop("disabled", true);
      }
    });
}

function updateAvailability() {
  $.get("/check_availability", function (data) {
    const canStart = data.can_start_couple;
    $("#start-btn").prop("disabled", !canStart);
    $("#status").text(
      `ALFA: ${data.alfa_status} - BRAVO: ${data.bravo_status}`
    );

    if (!canStart) {
      $("#start-btn").attr(
        "title",
        "Attendere che entrambe le piste siano libere"
      );
    } else {
      $("#start-btn").attr("title", "");
    }
  });
}

function updateTimer() {
  if (!isGameActive) return;
  const now = new Date();
  const diff = Math.floor((now - startTime) / 1000);
  const minutes = Math.floor(diff / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (diff % 60).toString().padStart(2, "0");
  $("#timer").text(`${minutes}:${seconds}`);
}

function activateNextPlayer() {
  $("#next-player-btn").prop("disabled", true);
  $("#stop-btn").prop("disabled", false);
  $("#timer").text("00:00");
  $("#current-player").text("-");
  updateAvailability(); // Verifica disponibilità piste
}

function pressButton(button) {
  $.ajax({
    url: "/button_press",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ button: button }),
    success: function (response) {
      if (!response.success) {
        alert(response.error);
        return;
      }

      if (button === "first_start") {
        startTime = new Date();
        isGameActive = true;
        timerInterval = setInterval(updateTimer, 1000);
        $("#next-player-btn").prop("disabled", true);
        $("#start-btn").prop("disabled", true);
        $("#stop-btn").prop("disabled", false);
        $("#current-player").text(response.current_player_bravo.id); // Aggiorna il giocatore corrente
      } else if (button === "first_stop" && isGameActive) {
        isGameActive = false;
        clearInterval(timerInterval);
        $("#next-player-btn").prop("disabled", false);
        $("#start-btn, #stop-btn").prop("disabled", true);
        $("#current-player").text("-"); // Resetta il giocatore corrente
      } else if (button === "third") {
        // Aggiorna lo stato della UI se necessario
        console.log(
          "Third button pressed, couple_in_alfa should be false now."
        );
      }

      updateNextPlayer();
      updateAvailability();
    },
  });
}

// timer per aggiornare la disponibilità delle piste e prossimo giocatore
setInterval(() => {
  updateAvailability();
  updateNextPlayer();
}, 1000);

$(document).ready(function () {
  updateAvailability();
  updateNextPlayer();
});
