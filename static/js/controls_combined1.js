// controls_combined1.js
// (Codice fornito dall'utente, applico correzioni)

let timerIntervalCouple = null;
let startTimeCouple = null;
let isGameActiveCouple = false;

let timerIntervalSingle = null;
let startTimeSingle = null;
let isGameActiveSingle = false;

let effectiveStartTimeCouple = null;
let effectiveStartTimeSingle = null;

function resetTimer(type) {
  const now = new Date();
  if (type === "couple" && isGameActiveCouple) {
    effectiveStartTimeCouple = now;
    startTimeCouple = now; // Mantieni compatibilità con la logica esistente
    localStorage.setItem("effectiveStartTimeCouple", now.toISOString());
    localStorage.setItem("startTimeCouple", now.toISOString());
    $("#timer-couple").text("00:00");
    console.log("Timer coppia resettato - tempo effettivo aggiornato");
  } else if (type === "single" && isGameActiveSingle) {
    effectiveStartTimeSingle = now;
    startTimeSingle = now; // Mantieni compatibilità con la logica esistente
    localStorage.setItem("effectiveStartTimeSingle", now.toISOString());
    localStorage.setItem("startTimeSingle", now.toISOString());
    $("#timer-single").text("00:00");
    console.log("Timer singolo resettato - tempo effettivo aggiornato");
  }
}

// --- Funzioni di Aggiornamento UI Base ---
function updateNextPlayer() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      $("#next-player").text(data.next_player_alfa_bravo_id || "-");
      $("#next-player-btn").prop("disabled", !data.next_player_alfa_bravo_id);
    })
    .catch((error) => console.error("Error fetching next player data:", error));
}
function updateTimer(type) {
  const now = new Date();
  let diff, minutes, seconds, startTime, timerElement;

  if (type === "couple") {
    startTime = startTimeCouple;
    timerElement = "#timer-couple";
  } else if (type === "single") {
    startTime = startTimeSingle;
    timerElement = "#timer-single";
  } else {
    return;
  }

  if (startTime) {
    diff = Math.floor((now - startTime) / 1000);
    minutes = Math.floor(diff / 60)
      .toString()
      .padStart(2, "0");
    seconds = (diff % 60).toString().padStart(2, "0");
    $(timerElement).text(`${minutes}:${seconds}`);
  } else {
    $(timerElement).text("00:00");
  }
}
function updateUIState() {
  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      // Giocatori Correnti
      let currentCoupleDisplay = "-";
      if (
        data.current_player_bravo &&
        data.current_player_bravo.id &&
        data.current_player_bravo.id.startsWith("GIALLO")
      ) {
        currentCoupleDisplay = data.current_player_bravo.id;
      } else if (
        data.current_player_alfa &&
        data.current_player_alfa.id &&
        data.current_player_alfa.id.startsWith("GIALLO")
      ) {
        currentCoupleDisplay = data.current_player_alfa.id + " (in Alfa)";
      }
      $("#current-player-couple").text(currentCoupleDisplay);
      $("#current-player-single").text(
        data.current_player_alfa &&
          data.current_player_alfa.id &&
          data.current_player_alfa.id.startsWith("BLU")
          ? data.current_player_alfa.id
          : "-"
      );

      // Stato Testuale Piste
      $("#status-couple").text(
        `ALFA: ${data.alfa_status} - BRAVO: ${data.bravo_status}`
      );
      $("#status-single").text(`ALFA: ${data.alfa_status}`);

      // Abilitazione Bottoni START/STOP
      const stdControlsCoupleVisible = $("#standard-controls-couple").is(
        ":visible"
      );
      const stdControlsSingleVisible = $("#standard-controls-single").is(
        ":visible"
      );
      const alfa_free = data.alfa_status === "Libera";
      const bravo_free = data.bravo_status === "Libera";
      $("#start-btn-couple").prop(
        "disabled",
        !stdControlsCoupleVisible ||
          isGameActiveCouple ||
          !(alfa_free && bravo_free)
      );
      $("#start-btn-single").prop(
        "disabled",
        !stdControlsSingleVisible || isGameActiveSingle || !alfa_free
      );
      $("#stop-btn-couple").prop(
        "disabled",
        !stdControlsCoupleVisible ||
          !isGameActiveCouple ||
          !data.can_stop_couple1
      );
      $("#stop-btn-single").prop(
        "disabled",
        !stdControlsSingleVisible ||
          !isGameActiveSingle ||
          !data.can_stop_single1
      );
    })
    .catch((error) => {
      console.error("Error fetching simulation data for UI state 1:", error);
      $(".control-panel button").prop("disabled", true);
      $("#status-couple, #status-single").text("Errore aggiornamento stato");
    });
}
function activateNextPlayer() {
  console.log("activateNextPlayer called - Refreshing UI state for track 1");
  showSection("#standard-controls-couple", "#penalty-section-couple");
  showSection("#standard-controls-couple", "#qualification-section-couple");
  showSection("#standard-controls-single", "#penalty-section-single");
  showSection("#standard-controls-single", "#qualification-section-single");
  updateUIState();
  updateNextPlayer();
}

// --- FORMATTAZIONE TEMPO (Helper) ---
function formatTimeJS(totalMinutes) {
  if (isNaN(totalMinutes) || totalMinutes < 0) return "00:00";
  const minutes = Math.floor(totalMinutes);
  const seconds = Math.floor((totalMinutes - minutes) * 60);
  return `${minutes.toString().padStart(2, "0")}:${seconds
    .toString()
    .padStart(2, "0")}`;
}

// --- Gestione Visibilità Sezioni ---
function showSection(sectionToShow, sectionToHide) {
  $(sectionToHide).hide();
  $(sectionToShow).fadeIn(200);
}

// --- FUNZIONI PER GESTIRE FORM INLINE ---

function showInlinePenaltyForm(data) {
  let typeSuffix = "";
  let standardControlsId = "";
  let penaltySectionId = "";
  if (data.player_type === "couple") {
    typeSuffix = "couple";
    standardControlsId = "#standard-controls-couple";
    penaltySectionId = "#penalty-section-couple";
  } else if (data.player_type === "single") {
    typeSuffix = "single";
    standardControlsId = "#standard-controls-single";
    penaltySectionId = "#penalty-section-single";
  } else {
    return;
  }

  console.log(
    `Showing penalty section ${penaltySectionId} for ${data.player_id}`
  );

  // Calcola la durata CORRETTA usando effectiveStartTime
  let timerDuration = 0;
  const now = new Date();

  if (data.player_type === "couple" && effectiveStartTimeCouple) {
    timerDuration = (now - effectiveStartTimeCouple) / 1000 / 60; // minuti
  } else if (data.player_type === "single" && effectiveStartTimeSingle) {
    timerDuration = (now - effectiveStartTimeSingle) / 1000 / 60; // minuti
  } else {
    // Fallback al calcolo normale se non c'è stato reset
    timerDuration = data.timer_duration_minutes;
  }

  $(`#penalty-player-display-${typeSuffix}`).text(
    data.player_name || data.player_id
  );
  $(`#penalty-timer-display-${typeSuffix}`).text(formatTimeJS(timerDuration));
  $(`#penalty-player-id-${typeSuffix}`).val(data.player_id);
  $(`#penalty-player-name-${typeSuffix}`).val(data.player_name);
  $(`#penalty-timer-duration-${typeSuffix}`).val(timerDuration);
  $(`#penalty-form-${typeSuffix}`)[0].reset();
  $(`#penalty_minutes_${typeSuffix}`).val(0);
  $(`#penalty_seconds_${typeSuffix}`).val(0);
  $(`#penalty-message-${typeSuffix}`)
    .hide()
    .removeClass("success error")
    .text("");
  $(`#submit-penalty-${typeSuffix}`)
    .prop("disabled", false)
    .text("Conferma Score");
  showSection(penaltySectionId, standardControlsId);
}

function showInlineQualificationForm(data) {
  let typeSuffix = "";
  let standardControlsId = "";
  let qualificationSectionId = "";
  let baseType = data.player_type;
  if (baseType === "couple") {
    typeSuffix = "couple";
    standardControlsId = "#standard-controls-couple";
    qualificationSectionId = "#qualification-section-couple";
  } else if (baseType === "single") {
    typeSuffix = "single";
    standardControlsId = "#standard-controls-single";
    qualificationSectionId = "#qualification-section-single";
  } else {
    return;
  }
  console.log(
    `Showing qualification section ${qualificationSectionId} for ${data.player_id}`
  );
  let reasonText = "Complimenti!";
  if (data.reason === "best_today") {
    reasonText = "MIGLIOR TEMPO DI OGGI!";
  } else if (data.reason === "top_3_overall") {
    reasonText = "TOP 3 GENERALE!";
  }
  $(`#qualification-reason-text-${typeSuffix}`).text(
    reasonText + " Inserisci i dati:"
  );
  $(`#modal-player-id-${typeSuffix}`).val(data.player_id);
  $(`#modal-player-name-${typeSuffix}`).val(data.player_name);
  $(`#modal-score-minutes-${typeSuffix}`).val(data.recorded_score);
  $(`#modal-player-type-${typeSuffix}`).val(baseType);
  $(`#modal-qualification-reason-${typeSuffix}`).val(data.reason);
  const formId = `#qualification-form-${typeSuffix}`;
  const messageId = `#modal-message-${typeSuffix}`;
  $(formId)[0].reset();
  $(messageId).hide().removeClass("success error").text("");
  $(`${formId} button[type="submit"]`)
    .prop("disabled", false)
    .text("Salva Dati");
  showSection(qualificationSectionId, standardControlsId);
}

function closeInlineForm(typeSuffix, formType) {
  let standardControlsId = "";
  let formSectionId = "";
  if (typeSuffix === "couple") {
    standardControlsId = "#standard-controls-couple";
    formSectionId = `#${formType}-section-couple`;
  } else if (typeSuffix === "single") {
    standardControlsId = "#standard-controls-single";
    formSectionId = `#${formType}-section-single`;
  } else {
    return;
  }
  console.log(`Closing inline form ${formSectionId}`);
  showSection(standardControlsId, formSectionId);
  if (formType === "penalty") {
    console.log(
      "Penalty form cancelled for",
      typeSuffix,
      "- UI restored, game state unchanged."
    );
    if (typeSuffix === "couple") updateTimer("couple");
    else if (typeSuffix === "single") updateTimer("single");
  } else if (formType === "qualification") {
    console.log("Qualification form closed for", typeSuffix);
  }
  updateUIState();
}

function showInlineMessage(messageTargetId, message, type) {
  const messageDiv = $(messageTargetId);
  if (messageDiv.length) {
    messageDiv
      .removeClass("success error")
      .addClass(type)
      .text(message)
      .fadeIn();
    setTimeout(() => {
      messageDiv.fadeOut();
    }, 4000);
  } else {
    console.error("Target message div not found:", messageTargetId);
  }
}

// --- FUNZIONI PER BOTTONI PENALITA' ---
function addPenaltySeconds(targetSuffix, secondsToAdd) {
  const minInput = $(`#penalty_minutes_${targetSuffix}`);
  const secInput = $(`#penalty_seconds_${targetSuffix}`);
  let currentMinutes = parseInt(minInput.val()) || 0;
  let currentSeconds = parseInt(secInput.val()) || 0;
  let totalSeconds = currentMinutes * 60 + currentSeconds + secondsToAdd;
  if (totalSeconds < 0) totalSeconds = 0;
  const newMinutes = Math.floor(totalSeconds / 60);
  const newSeconds = totalSeconds % 60;
  minInput.val(newMinutes);
  secInput.val(newSeconds);
  console.log(
    `Added ${secondsToAdd}s to ${targetSuffix}. New penalty: ${newMinutes}m ${newSeconds}s`
  );
  // La parte di aggiornamento del testo del bottone è stata rimossa perché event.target non era definito qui
}

function resetPenaltyFields(targetSuffix) {
  $(`#penalty_minutes_${targetSuffix}`).val(0);
  $(`#penalty_seconds_${targetSuffix}`).val(0);
  console.log(`Penalty fields reset for ${targetSuffix}`);
  // La parte di reset del testo del bottone è stata rimossa
}

// --- GESTIONE SUBMIT FORM ---

function submitQualificationForm(typeSuffix) {
  const formId = `#qualification-form-${typeSuffix}`;
  const messageTarget = `#modal-message-${typeSuffix}`;
  const formData = {
    player_id: $(`#modal-player-id-${typeSuffix}`).val(),
    player_name: $(`#modal-player-name-${typeSuffix}`).val(),
    first_name: $(`#first_name-${typeSuffix}`).val().trim(),
    last_name: $(`#last_name-${typeSuffix}`).val().trim(),
    phone_number: $(`#phone_number-${typeSuffix}`).val().trim(),
    score_minutes: $(`#modal-score-minutes-${typeSuffix}`).val(),
    player_type: typeSuffix,
    qualification_reason: $(`#modal-qualification-reason-${typeSuffix}`).val(),
  };
  if (!formData.first_name || !formData.last_name || !formData.phone_number) {
    showInlineMessage(messageTarget, "Compila...", "error");
    return;
  }
  const submitButton = $(`${formId} button[type="submit"]`);
  submitButton.prop("disabled", true).text("Salvataggio...");
  $.ajax({
    url: "/save_contact_info",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(formData),
    success: function (response) {
      if (response.success) {
        showInlineMessage(messageTarget, response.message, "success");
        setTimeout(() => closeInlineForm(typeSuffix, "qualification"), 2500);
      } else {
        showInlineMessage(
          messageTarget,
          response.message || "Errore.",
          "error"
        );
        submitButton.prop("disabled", false).text("Salva Dati");
      }
    },
    error: function (xhr) {
      showInlineMessage(
        messageTarget,
        xhr.responseJSON?.message || "Errore.",
        "error"
      );
      submitButton.prop("disabled", false).text("Salva Dati");
    },
  });
}

function submitPenaltyForm(typeSuffix) {
  const formId = `#penalty-form-${typeSuffix}`;
  const messageSectionId = `#penalty-section-${typeSuffix}`;
  const submitButtonId = `#submit-penalty-${typeSuffix}`;
  const playerType = typeSuffix;
  const playerId = $(`#penalty-player-id-${typeSuffix}`).val();
  const playerName = $(`#penalty-player-name-${typeSuffix}`).val();
  const timerDuration = parseFloat(
    $(`#penalty-timer-duration-${typeSuffix}`).val()
  );
  const penaltyMinutes =
    parseInt($(`#penalty_minutes_${typeSuffix}`).val()) || 0;
  const penaltySeconds =
    parseInt($(`#penalty_seconds_${typeSuffix}`).val()) || 0;
  if (
    isNaN(timerDuration) ||
    isNaN(penaltyMinutes) ||
    isNaN(penaltySeconds) ||
    penaltyMinutes < 0 ||
    penaltySeconds < 0 ||
    penaltySeconds > 59
  ) {
    showInlineMessage(messageSectionId, "Penalità non valida.", "error");
    return;
  }
  const penaltyTotalMinutes = penaltyMinutes + penaltySeconds / 60.0;
  const officialScoreMinutes = timerDuration + penaltyTotalMinutes;
  console.log(
    `Submitting final score for ${playerId} (${playerType}): Official=${officialScoreMinutes.toFixed(
      4
    )}`
  );
  $(submitButtonId).prop("disabled", true).text("Salvataggio...");
  $(`${messageSectionId} .inline-message`).hide();
  $.ajax({
    url: "/submit_combined_score",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      player_id: playerId,
      player_name: playerName,
      player_type: playerType,
      timer_duration_minutes: timerDuration,
      official_score_minutes: officialScoreMinutes,
    }),
    success: function (response) {
      if (response.success) {
        console.log(
          "Score submitted successfully for",
          typeSuffix,
          ". Resetting game state."
        );
        if (typeSuffix === "couple") {
          isGameActiveCouple = false;
          clearInterval(timerIntervalCouple);
          startTimeCouple = null;
          $("#current-player-couple").text("-");
          $("#timer-couple").text("00:00");
        } else if (typeSuffix === "single") {
          isGameActiveSingle = false;
          clearInterval(timerIntervalSingle);
          startTimeSingle = null;
          $("#current-player-single").text("-");
          $("#timer-single").text("00:00");
        }
        closeInlineForm(typeSuffix, "penalty");
        if (response.qualified) {
          console.log("Player qualified!");
          showInlineQualificationForm({
            player_id: response.player_id,
            player_name: response.player_name,
            recorded_score: response.recorded_score,
            player_type: response.player_type,
            reason: response.reason,
          });
        } else {
          console.log("Player did not qualify.");
          updateNextPlayer();
          updateUIState();
        }
      } else {
        showInlineMessage(
          messageSectionId,
          response.error || "Errore.",
          "error"
        );
        $(submitButtonId).prop("disabled", false).text("Conferma Score");
      }
    },
    error: function (xhr) {
      showInlineMessage(
        messageSectionId,
        xhr.responseJSON?.error || "Errore.",
        "error"
      );
      $(submitButtonId).prop("disabled", false).text("Conferma Score");
    },
  });
}

// --- FUNZIONE PRESS BUTTON ---
function pressButton(button, type) {
  console.log(`Button pressed (Track 1): ${button}, Type context: ${type}`);
  $.ajax({
    url: "/button_press",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ button: button }),
    success: function (response) {
      if (!response.success) {
        alert(response.error || "Errore.");
        updateUIState();
        return;
      }
      if (button.includes("_start")) {
        const now = new Date();
        if (type === "couple") {
          effectiveStartTimeCouple = now;
          startTimeCouple = now;
          localStorage.setItem("effectiveStartTimeCouple", now.toISOString());
          localStorage.setItem("startTimeCouple", now.toISOString());
          isGameActiveCouple = true;
          clearInterval(timerIntervalCouple);
          timerIntervalCouple = setInterval(() => updateTimer("couple"), 1000);
          $("#timer-couple").text("00:00");
          if (response.current_player_bravo)
            $("#current-player-couple").text(response.current_player_bravo.id);
          else if (response.current_player_alfa)
            $("#current-player-couple").text(response.current_player_alfa.id);
        } else if (type === "single") {
          effectiveStartTimeSingle = now;
          startTimeSingle = now;
          localStorage.setItem("effectiveStartTimeSingle", now.toISOString());
          localStorage.setItem("startTimeSingle", now.toISOString());
          isGameActiveSingle = true;
          clearInterval(timerIntervalSingle);
          timerIntervalSingle = setInterval(() => updateTimer("single"), 1000);
          $("#timer-single").text("00:00");
          if (response.current_player_alfa)
            $("#current-player-single").text(response.current_player_alfa.id);
        }
        updateUIState();
        updateNextPlayer();
      } else if (
        response.action === "penalty_input_required" &&
        button.includes("_stop")
      ) {
        console.log("Penalty input required for:", response.player_id);
        if (response.player_type === "couple") {
          clearInterval(timerIntervalCouple);
        } else if (response.player_type === "single") {
          clearInterval(timerIntervalSingle);
        }
        showInlinePenaltyForm(response);
      } else {
        updateUIState();
        updateNextPlayer();
      }
    },
    error: function (xhr) {
      alert(`Operazione fallita: ${xhr.responseJSON?.error || "Errore."}`);
      updateUIState();
    },
  });
}

// --- READY E INTERVAL (Corretti con Delegazione Eventi) ---
$(document).ready(function () {
  console.log("Controls Combined 1 Ready (Inline Version - Listener Fixed)");

  // Recupera gli effectiveStartTime dal localStorage
  const savedEffectiveCouple = localStorage.getItem("effectiveStartTimeCouple");
  const savedEffectiveSingle = localStorage.getItem("effectiveStartTimeSingle");

  if (savedEffectiveCouple) {
    effectiveStartTimeCouple = new Date(savedEffectiveCouple);
  }
  if (savedEffectiveSingle) {
    effectiveStartTimeSingle = new Date(savedEffectiveSingle);
  }
  activateNextPlayer();

  fetch("/simulate")
    .then((response) => response.json())
    .then((data) => {
      const savedStartTimeCouple = localStorage.getItem("startTimeCouple");
      const savedStartTimeSingle = localStorage.getItem("startTimeSingle");

      if (savedStartTimeCouple && data.current_player_bravo) {
        startTimeCouple = new Date(savedStartTimeCouple);
        isGameActiveCouple = true;
        timerIntervalCouple = setInterval(() => updateTimer("couple"), 1000);
      } else {
        localStorage.removeItem("startTimeCouple");
      }

      if (
        savedStartTimeSingle &&
        data.current_player_alfa &&
        data.current_player_alfa.id.startsWith("BLU")
      ) {
        startTimeSingle = new Date(savedStartTimeSingle);
        isGameActiveSingle = true;
        timerIntervalSingle = setInterval(() => updateTimer("single"), 1000);
      } else {
        localStorage.removeItem("startTimeSingle");
      }

      activateNextPlayer(); // Spostato qui per assicurarsi che lo stato sia corretto
    })
    .catch((error) => {
      console.error("Errore durante il controllo dello stato server:", error);
      activateNextPlayer(); // In fallback
    });

  // ** Delegazione Eventi una sola volta **
  $(".control-container")
    // Penalità Add Buttons
    .off("click", ".penalty-add-button") // Rimuovi vecchi listener
    .on("click", ".penalty-add-button", function (event) {
      // Aggiungi event qui
      if ($(this).closest(".couple-section, .single-section").length > 0) {
        const seconds = parseInt($(this).data("seconds"));
        const targetSuffix = $(this).data("target-suffix");
        if (!isNaN(seconds) && targetSuffix) {
          addPenaltySeconds(targetSuffix, seconds);
          // La logica per aggiornare il testo del bottone (rimossa da addPenaltySeconds) va qui
          const clickedButton = $(event.target); // Usa event.target
          const currentCount = parseInt(clickedButton.data("counter") || 0);
          const newCount = currentCount + 1;
          clickedButton.data("counter", newCount);
          const baseText =
            clickedButton.data("base-text") ||
            clickedButton
              .text()
              .replace(/\s*\(\d+\)$/, "")
              .trim(); // Regex più robusto
          clickedButton.data("base-text", baseText); // Memorizza il testo base se non già fatto
          clickedButton.text(`${baseText} (${newCount})`);
        }
      }
    })
    // Penalità Reset Buttons
    .off("click", ".reset-penalty-button")
    .on("click", ".reset-penalty-button", function () {
      if ($(this).closest(".couple-section, .single-section").length > 0) {
        const targetSuffix = $(this).data("target-suffix");
        if (targetSuffix) {
          resetPenaltyFields(targetSuffix);
          // Resetta anche il testo di tutti i bottoni Add per questo suffix
          $(`.penalty-add-button[data-target-suffix="${targetSuffix}"]`).each(
            function () {
              const button = $(this);
              const baseText =
                button.data("base-text") ||
                button
                  .text()
                  .replace(/\s*\(\d+\)$/, "")
                  .trim();
              button.data("counter", 0); // Resetta contatore
              button.text(baseText); // Rimuovi conteggio dal testo
            }
          );
        }
      }
    })
    // Penalità Form Submit
    .off("submit", "#penalty-form-couple")
    .on("submit", "#penalty-form-couple", function (event) {
      event.preventDefault();
      submitPenaltyForm("couple");
    })
    .off("submit", "#penalty-form-single")
    .on("submit", "#penalty-form-single", function (event) {
      event.preventDefault();
      submitPenaltyForm("single");
    })
    // Qualifica Form Submit
    .off("submit", "#qualification-form-couple")
    .on("submit", "#qualification-form-couple", function (event) {
      event.preventDefault();
      submitQualificationForm("couple");
    })
    .off("submit", "#qualification-form-single")
    .on("submit", "#qualification-form-single", function (event) {
      event.preventDefault();
      submitQualificationForm("single");
    });
});

setInterval(() => {
  if (
    $(
      "#penalty-section-couple:visible, #qualification-section-couple:visible, #penalty-section-single:visible, #qualification-section-single:visible"
    ).length === 0
  ) {
    updateUIState();
    updateNextPlayer();
    if (isGameActiveCouple) updateTimer("couple");
    if (isGameActiveSingle) updateTimer("single");
  } else {
    if ($("#standard-controls-couple").is(":visible") && isGameActiveCouple)
      updateTimer("couple");
    if ($("#standard-controls-single").is(":visible") && isGameActiveSingle)
      updateTimer("single");
  }
}, 1500);
