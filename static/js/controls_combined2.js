let timerIntervalCouple2 = null;
let startTimeCouple2 = null;
let isGameActiveCouple2 = false;
let effectiveStartTimeCouple2 = null; // Aggiunto per gestire il reset

let timerIntervalSingle2 = null;
let startTimeSingle2 = null;
let isGameActiveSingle2 = false;
let effectiveStartTimeSingle2 = null; // Aggiunto per gestire il reset

// --- Funzioni di Aggiornamento UI Base ---
function updateNextPlayer2() {
  fetch("/simulate")
    .then((r) => r.json())
    .then((d) => {
      $("#next-player2").text(d.next_player_alfa_bravo_id2 || "-");
    })
    .catch((e) => console.error("Error fetch next P2:", e));
}

function updateTimer2(type) {
  const now = new Date();
  let diff, minutes, seconds, startTime, timerElement;

  if (type === "couple2") {
    startTime = effectiveStartTimeCouple2 || startTimeCouple2; // Usa effectiveStartTime se disponibile
    timerElement = "#timer-couple2";
  } else if (type === "single2") {
    startTime = effectiveStartTimeSingle2 || startTimeSingle2; // Usa effectiveStartTime se disponibile
    timerElement = "#timer-single2";
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

// --- FUNZIONE RESET TIMER PER COMBINED2 ---
function resetTimer2(type) {
  const now = new Date();
  if (type === "couple2" && isGameActiveCouple2) {
    effectiveStartTimeCouple2 = now;
    localStorage.setItem("effectiveStartTimeCouple2", now.toISOString());
    $("#timer-couple2").text("00:00");
    console.log("Timer coppia P2 resettato - tempo effettivo aggiornato");
  } else if (type === "single2" && isGameActiveSingle2) {
    effectiveStartTimeSingle2 = now;
    localStorage.setItem("effectiveStartTimeSingle2", now.toISOString());
    $("#timer-single2").text("00:00");
    console.log("Timer singolo P2 resettato - tempo effettivo aggiornato");
  }
}

function updateUIState2() {
  fetch("/simulate")
    .then((r) => r.json())
    .then((data) => {
      // Giocatori Correnti
      let currentCouple2Display = "-";
      if (
        data.current_player_bravo2 &&
        data.current_player_bravo2.id &&
        data.current_player_bravo2.id.startsWith("ROSA")
      ) {
        currentCouple2Display = data.current_player_bravo2.id;
      } else if (
        data.current_player_alfa2 &&
        data.current_player_alfa2.id &&
        data.current_player_alfa2.id.startsWith("ROSA")
      ) {
        currentCouple2Display = data.current_player_alfa2.id + " (in Alfa2)";
      }
      $("#current-player-couple2").text(currentCouple2Display);

      $("#current-player-single2").text(
        data.current_player_alfa2 &&
          data.current_player_alfa2.id &&
          (data.current_player_alfa2.id.startsWith("ARANCIO") ||
            data.current_player_alfa2.id.startsWith("BIANCO"))
          ? data.current_player_alfa2.id
          : "-"
      );

      // Stato Piste
      $("#status-couple2").text(
        `ALFA2: ${data.alfa2_status} - BRAVO2: ${data.bravo2_status}`
      );
      $("#status-single2").text(`ALFA2: ${data.alfa2_status}`);

      // Abilitazione Bottoni
      const stdControlsCouple2Visible = $("#standard-controls-couple2").is(
        ":visible"
      );
      const stdControlsSingle2Visible = $("#standard-controls-single2").is(
        ":visible"
      );
      const alfa2_free = data.alfa2_status === "Libera";
      const bravo2_free = data.bravo2_status === "Libera";

      $("#start-btn-couple2").prop(
        "disabled",
        !stdControlsCouple2Visible ||
          isGameActiveCouple2 ||
          !(alfa2_free && bravo2_free)
      );
      $("#start-btn-single2").prop(
        "disabled",
        !stdControlsSingle2Visible || isGameActiveSingle2 || !alfa2_free
      );
      $("#stop-btn-couple2").prop(
        "disabled",
        !stdControlsCouple2Visible ||
          !isGameActiveCouple2 ||
          !data.can_stop_couple2
      );
      $("#stop-btn-single2").prop(
        "disabled",
        !stdControlsSingle2Visible ||
          !isGameActiveSingle2 ||
          !data.can_stop_single2
      );
      // Abilitazione pulsanti RESET
      $("#reset-btn-couple2").prop(
        "disabled",
        !stdControlsCouple2Visible || !isGameActiveCouple2
      );
      $("#reset-btn-single2").prop(
        "disabled",
        !stdControlsSingle2Visible || !isGameActiveSingle2
      );
    })
    .catch((e) => {
      console.error("Error fetching simulation data for UI state 2:", e);
      $(".control-panel button").prop("disabled", true);
      $("#status-couple2, #status-single2").text("Errore aggiornamento stato");
    });
}

function activateNextPlayer2() {
  console.log("activateNextPlayer2 called - Refreshing UI state for track 2");
  showSection("#standard-controls-couple2", "#penalty-section-couple2");
  showSection("#standard-controls-couple2", "#qualification-section-couple2");
  showSection("#standard-controls-single2", "#penalty-section-single2");
  showSection("#standard-controls-single2", "#qualification-section-single2");
  updateUIState2();
  updateNextPlayer2();
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
function showInlinePenaltyForm2(data) {
  let typeSuffix = "";
  let standardControlsId = "";
  let penaltySectionId = "";
  if (data.player_type === "couple2") {
    typeSuffix = "couple2";
    standardControlsId = "#standard-controls-couple2";
    penaltySectionId = "#penalty-section-couple2";
  } else if (data.player_type === "single2") {
    typeSuffix = "single2";
    standardControlsId = "#standard-controls-single2";
    penaltySectionId = "#penalty-section-single2";
  } else {
    return;
  }

  // Calcola la durata CORRETTA usando effectiveStartTime
  let timerDuration = 0;
  const now = new Date();

  if (data.player_type === "couple2" && effectiveStartTimeCouple2) {
    timerDuration = (now - effectiveStartTimeCouple2) / 1000 / 60; // minuti
  } else if (data.player_type === "single2" && effectiveStartTimeSingle2) {
    timerDuration = (now - effectiveStartTimeSingle2) / 1000 / 60; // minuti
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

function showInlineQualificationForm2(data) {
  let typeSuffix = "";
  let standardControlsId = "";
  let qualificationSectionId = "";
  let baseType = data.player_type;
  if (baseType === "couple") {
    typeSuffix = "couple2";
    standardControlsId = "#standard-controls-couple2";
    qualificationSectionId = "#qualification-section-couple2";
  } else if (baseType === "single") {
    typeSuffix = "single2";
    standardControlsId = "#standard-controls-single2";
    qualificationSectionId = "#qualification-section-single2";
  } else {
    return;
  }

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

function closeInlineForm2(typeSuffix, formType) {
  let standardControlsId = "";
  let formSectionId = "";
  if (typeSuffix === "couple2") {
    standardControlsId = "#standard-controls-couple2";
    formSectionId = `#${formType}-section-couple2`;
  } else if (typeSuffix === "single2") {
    standardControlsId = "#standard-controls-single2";
    formSectionId = `#${formType}-section-single2`;
  } else {
    return;
  }

  showSection(standardControlsId, formSectionId);
  if (formType === "penalty") {
    if (typeSuffix === "couple2") updateTimer2("couple2");
    else if (typeSuffix === "single2") updateTimer2("single2");
  }
  updateUIState2();
}

function showInlineMessage2(messageTargetId, message, type) {
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
function addPenaltySeconds2(targetSuffix, secondsToAdd) {
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
}

function resetPenaltyFields2(targetSuffix) {
  $(`#penalty_minutes_${targetSuffix}`).val(0);
  $(`#penalty_seconds_${targetSuffix}`).val(0);
}

// --- GESTIONE SUBMIT FORM ---
function submitQualificationForm2(typeSuffix) {
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
    showInlineMessage2(
      messageTarget,
      "Compila tutti i campi obbligatori",
      "error"
    );
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
        showInlineMessage2(messageTarget, response.message, "success");
        setTimeout(() => closeInlineForm2(typeSuffix, "qualification"), 2500);
      } else {
        showInlineMessage2(
          messageTarget,
          response.message || "Errore durante il salvataggio",
          "error"
        );
        submitButton.prop("disabled", false).text("Salva Dati");
      }
    },
    error: function (xhr) {
      showInlineMessage2(
        messageTarget,
        xhr.responseJSON?.message || "Errore di connessione",
        "error"
      );
      submitButton.prop("disabled", false).text("Salva Dati");
    },
  });
}

function submitPenaltyForm2(typeSuffix) {
  const formId = `#penalty-form-${typeSuffix}`;
  const messageSectionId = `#penalty-section-${typeSuffix}`;
  const submitButtonId = `#submit-penalty-${typeSuffix}`;
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
    showInlineMessage2(messageSectionId, "Penalità non valida", "error");
    return;
  }

  const penaltyTotalMinutes = penaltyMinutes + penaltySeconds / 60.0;
  const officialScoreMinutes = timerDuration + penaltyTotalMinutes;

  $(submitButtonId).prop("disabled", true).text("Salvataggio...");
  $(`${messageSectionId} .inline-message`).hide();

  $.ajax({
    url: "/submit_combined_score",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      player_id: playerId,
      player_name: playerName,
      player_type: typeSuffix,
      timer_duration_minutes: timerDuration,
      official_score_minutes: officialScoreMinutes,
    }),
    success: function (response) {
      if (response.success) {
        if (typeSuffix === "couple2") {
          isGameActiveCouple2 = false;
          clearInterval(timerIntervalCouple2);
          startTimeCouple2 = null;
          effectiveStartTimeCouple2 = null;
          localStorage.removeItem("startTimeCouple2");
          localStorage.removeItem("effectiveStartTimeCouple2");
          $("#current-player-couple2").text("-");
          $("#timer-couple2").text("00:00");
        } else if (typeSuffix === "single2") {
          isGameActiveSingle2 = false;
          clearInterval(timerIntervalSingle2);
          startTimeSingle2 = null;
          effectiveStartTimeSingle2 = null;
          localStorage.removeItem("startTimeSingle2");
          localStorage.removeItem("effectiveStartTimeSingle2");
          $("#current-player-single2").text("-");
          $("#timer-single2").text("00:00");
        }

        closeInlineForm2(typeSuffix, "penalty");

        if (response.qualified) {
          showInlineQualificationForm2({
            player_id: response.player_id,
            player_name: response.player_name,
            recorded_score: response.recorded_score,
            player_type: response.player_type,
            reason: response.reason,
          });
        } else {
          updateNextPlayer2();
          updateUIState2();
        }
      } else {
        showInlineMessage2(
          messageSectionId,
          response.error || "Errore durante l'invio",
          "error"
        );
        $(submitButtonId).prop("disabled", false).text("Conferma Score");
      }
    },
    error: function (xhr) {
      showInlineMessage2(
        messageSectionId,
        xhr.responseJSON?.error || "Errore di connessione",
        "error"
      );
      $(submitButtonId).prop("disabled", false).text("Conferma Score");
    },
  });
}

// --- FUNZIONE PRESS BUTTON PISTA 2 ---
function pressButton2(button, typeContext) {
  console.log(
    `Button pressed (Track 2): ${button}, Type context: ${typeContext}`
  );

  $.ajax({
    url: "/button_press",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ button: button }),
    success: function (response) {
      if (!response.success) {
        alert(response.error || "Errore.");
        updateUIState2();
        return;
      }

      if (button.includes("_start")) {
        const now = new Date();
        if (typeContext === "couple2") {
          startTimeCouple2 = now;
          effectiveStartTimeCouple2 = now;
          localStorage.setItem("startTimeCouple2", now.toISOString());
          localStorage.setItem("effectiveStartTimeCouple2", now.toISOString());
          isGameActiveCouple2 = true;
          clearInterval(timerIntervalCouple2);
          timerIntervalCouple2 = setInterval(
            () => updateTimer2("couple2"),
            1000
          );
          $("#timer-couple2").text("00:00");
          if (response.current_player_bravo2) {
            $("#current-player-couple2").text(
              response.current_player_bravo2.id
            );
          } else if (response.current_player_alfa2) {
            $("#current-player-couple2").text(response.current_player_alfa2.id);
          }
        } else if (typeContext === "single2") {
          startTimeSingle2 = now;
          effectiveStartTimeSingle2 = now;
          localStorage.setItem("startTimeSingle2", now.toISOString());
          localStorage.setItem("effectiveStartTimeSingle2", now.toISOString());
          isGameActiveSingle2 = true;
          clearInterval(timerIntervalSingle2);
          timerIntervalSingle2 = setInterval(
            () => updateTimer2("single2"),
            1000
          );
          $("#timer-single2").text("00:00");
          if (response.current_player_alfa2) {
            $("#current-player-single2").text(response.current_player_alfa2.id);
          }
        }
        updateUIState2();
        updateNextPlayer2();
      } else if (
        response.action === "penalty_input_required" &&
        button.includes("_stop")
      ) {
        if (response.player_type === "couple2") {
          clearInterval(timerIntervalCouple2);
        } else if (response.player_type === "single2") {
          clearInterval(timerIntervalSingle2);
        }
        showInlinePenaltyForm2(response);
      } else {
        updateUIState2();
        updateNextPlayer2();
      }
    },
    error: function (xhr) {
      alert(`Operazione fallita: ${xhr.responseJSON?.error || "Errore."}`);
      updateUIState2();
    },
  });
}

// --- INIT E EVENTI ---
$(document).ready(function () {
  console.log("Controls Combined 2 Ready");
  activateNextPlayer2();

  // Recupera stato da localStorage
  const savedStartTimeCouple2 = localStorage.getItem("startTimeCouple2");
  const savedEffectiveCouple2 = localStorage.getItem(
    "effectiveStartTimeCouple2"
  );
  const savedStartTimeSingle2 = localStorage.getItem("startTimeSingle2");
  const savedEffectiveSingle2 = localStorage.getItem(
    "effectiveStartTimeSingle2"
  );

  fetch("/simulate")
    .then((r) => r.json())
    .then((data) => {
      if (
        savedStartTimeCouple2 &&
        (data.current_player_bravo2?.id?.startsWith("ROSA") ||
          data.current_player_alfa2?.id?.startsWith("ROSA"))
      ) {
        startTimeCouple2 = new Date(savedStartTimeCouple2);
        effectiveStartTimeCouple2 = savedEffectiveCouple2
          ? new Date(savedEffectiveCouple2)
          : startTimeCouple2;
        isGameActiveCouple2 = true;
        timerIntervalCouple2 = setInterval(() => updateTimer2("couple2"), 1000);
      } else {
        localStorage.removeItem("startTimeCouple2");
        localStorage.removeItem("effectiveStartTimeCouple2");
      }

      if (
        savedStartTimeSingle2 &&
        data.current_player_alfa2?.id &&
        (data.current_player_alfa2.id.startsWith("ARANCIO") ||
          data.current_player_alfa2.id.startsWith("BIANCO"))
      ) {
        startTimeSingle2 = new Date(savedStartTimeSingle2);
        effectiveStartTimeSingle2 = savedEffectiveSingle2
          ? new Date(savedEffectiveSingle2)
          : startTimeSingle2;
        isGameActiveSingle2 = true;
        timerIntervalSingle2 = setInterval(() => updateTimer2("single2"), 1000);
      } else {
        localStorage.removeItem("startTimeSingle2");
        localStorage.removeItem("effectiveStartTimeSingle2");
      }
    })
    .catch((e) => console.error("Errore nel ripristino stato:", e));

  // Delegazione eventi
  $(".control-container")
    .on("click", ".penalty-add-button", function () {
      const seconds = parseInt($(this).data("seconds"));
      const targetSuffix = $(this).data("target-suffix");
      if (!isNaN(seconds) && targetSuffix) {
        addPenaltySeconds2(targetSuffix, seconds);
      }
    })
    .on("click", ".reset-penalty-button", function () {
      const targetSuffix = $(this).data("target-suffix");
      if (targetSuffix) {
        resetPenaltyFields2(targetSuffix);
      }
    })
    .on("submit", "#penalty-form-couple2", function (e) {
      e.preventDefault();
      submitPenaltyForm2("couple2");
    })
    .on("submit", "#penalty-form-single2", function (e) {
      e.preventDefault();
      submitPenaltyForm2("single2");
    })
    .on("submit", "#qualification-form-couple2", function (e) {
      e.preventDefault();
      submitQualificationForm2("couple2");
    })
    .on("submit", "#qualification-form-single2", function (e) {
      e.preventDefault();
      submitQualificationForm2("single2");
    });
});

setInterval(() => {
  if (
    $(
      "#penalty-section-couple2:visible, #qualification-section-couple2:visible, #penalty-section-single2:visible, #qualification-section-single2:visible"
    ).length === 0
  ) {
    updateUIState2();
    updateNextPlayer2();
    if (isGameActiveCouple2) updateTimer2("couple2");
    if (isGameActiveSingle2) updateTimer2("single2");
  } else {
    if ($("#standard-controls-couple2").is(":visible") && isGameActiveCouple2)
      updateTimer2("couple2");
    if ($("#standard-controls-single2").is(":visible") && isGameActiveSingle2)
      updateTimer2("single2");
  }
}, 1500);
