// controls_combined2.js
// Questo file gestisce la logica di Combined 2 (ROSA per coppie, ARANCIO/BIANCO per singoli)
// La logica di priorità delle code è la stessa di Combined 1:
// - Se entrambe le piste sono libere: priorità a coppia (ROSA)
// - Se ALFA2 è libera e BRAVO2 è occupata: priorità a singolo (ARANCIO/BIANCO)
// - Se ALFA2 è occupata (indipendentemente da BRAVO2): priorità a coppia (ROSA)

let timerIntervalCouple2 = null;
let startTimeCouple2 = null;
let isGameActiveCouple2 = false;

let timerIntervalSingle2 = null;
let startTimeSingle2 = null;
let isGameActiveSingle2 = false;

// --- Funzioni di Aggiornamento UI Base ---
function updateNextPlayer2() {
  fetch("/simulate")
    .then((r) => r.json())
    .then((d) => {
      $("#next-player2").text(d.next_player_alfa_bravo_id2 || "-");
      // Non c'è il bottone next-player-btn2 nell'HTML fornito, quindi nessuna gestione qui
    })
    .catch((e) => console.error("Error fetch next P2:", e));
}

function updateTimer2(type) {
  const now = new Date();
  let diff, minutes, seconds, startTime, timerElement;
  if (type === "couple2") {
    startTime = startTimeCouple2;
    timerElement = "#timer-couple2";
  } else if (type === "single2") {
    startTime = startTimeSingle2;
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
        // Verifica ID inizia con ROSA
        currentCouple2Display = data.current_player_bravo2.id;
      } else if (
        data.current_player_alfa2 &&
        data.current_player_alfa2.id &&
        data.current_player_alfa2.id.startsWith("ROSA")
      ) {
        currentCouple2Display = data.current_player_alfa2.id + " (in Alfa2)";
      }
      $("#current-player-couple2").text(currentCouple2Display);

      // Verifica che l'ID inizi con ARANCIO o BIANCO (i singoli nella pista combined2)
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

      // Abilitazione Bottoni START/STOP (considerando visibilità controlli standard e stato gioco)
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
      ); // Logica corretta
      $("#stop-btn-single2").prop(
        "disabled",
        !stdControlsSingle2Visible ||
          !isGameActiveSingle2 ||
          !data.can_stop_single2
      ); // Logica corretta
    })
    .catch((e) => {
      console.error("Error fetching simulation data for UI state 2:", e);
      $(".control-panel button").prop("disabled", true);
      $("#status-couple2, #status-single2").text("Errore aggiornamento stato");
    });
}

function activateNextPlayer2() {
  console.log("activateNextPlayer2 called - Refreshing UI state for track 2");
  // Mostra controlli standard, nascondi form
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
  console.log(
    `Showing penalty section ${penaltySectionId} for ${data.player_id}`
  );
  $(`#penalty-player-display-${typeSuffix}`).text(
    data.player_name || data.player_id
  );
  $(`#penalty-timer-display-${typeSuffix}`).text(
    formatTimeJS(data.timer_duration_minutes)
  );
  $(`#penalty-player-id-${typeSuffix}`).val(data.player_id);
  $(`#penalty-player-name-${typeSuffix}`).val(data.player_name);
  $(`#penalty-timer-duration-${typeSuffix}`).val(data.timer_duration_minutes);
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
  const messageId = `#modal-message-${typeSuffix}`; // Usa ID corretto
  $(formId)[0].reset();
  $(messageId).hide().removeClass("success error").text("");
  $(`${formId} button[type="submit"]`)
    .prop("disabled", false)
    .text("Salva Dati");
  showSection(qualificationSectionId, standardControlsId);
}

// ** Correzione Qui: Non resettare isGameActive su annulla penalità **
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
  console.log(`Closing inline form ${formSectionId}`);
  showSection(standardControlsId, formSectionId);
  if (formType === "penalty") {
    console.log(
      "Penalty form cancelled for",
      typeSuffix,
      "- UI restored, game state unchanged."
    );
    // NON resettare isGameActiveCouple2 o isGameActiveSingle2 qui
    if (typeSuffix === "couple2") updateTimer2("couple2");
    else if (typeSuffix === "single2") updateTimer2("single2");
  } else if (formType === "qualification") {
    console.log("Qualification form closed for", typeSuffix);
  }
  updateUIState2(); // Aggiorna stato bottoni alla fine
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
  console.log(
    `Added ${secondsToAdd}s to ${targetSuffix}. New penalty: ${newMinutes}m ${newSeconds}s`
  );
}
function resetPenaltyFields2(targetSuffix) {
  $(`#penalty_minutes_${targetSuffix}`).val(0);
  $(`#penalty_seconds_${targetSuffix}`).val(0);
  console.log(`Penalty fields reset for ${targetSuffix}`);
}

// --- GESTIONE SUBMIT FORM ---

// Funzione Submit Qualifica Pista 2
function submitQualificationForm2(typeSuffix) {
  const formId = `#qualification-form-${typeSuffix}`;
  const messageTarget = `#modal-message-${typeSuffix}`; // Usa ID corretto
  const baseType = $(`#modal-player-type-${typeSuffix}`).val();
  const formData = {
    player_id: $(`#modal-player-id-${typeSuffix}`).val(),
    player_name: $(`#modal-player-name-${typeSuffix}`).val(),
    first_name: $(`#first_name-${typeSuffix}`).val().trim(),
    last_name: $(`#last_name-${typeSuffix}`).val().trim(),
    phone_number: $(`#phone_number-${typeSuffix}`).val().trim(),
    score_minutes: $(`#modal-score-minutes-${typeSuffix}`).val(),
    player_type: baseType,
    qualification_reason: $(`#modal-qualification-reason-${typeSuffix}`).val(),
  };
  if (!formData.first_name || !formData.last_name || !formData.phone_number) {
    showInlineMessage2(messageTarget, "Compila...", "error");
    return;
  } // Usa showInlineMessage2
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
      } // Usa ...2
      else {
        showInlineMessage2(
          messageTarget,
          response.message || "Errore.",
          "error"
        );
        submitButton.prop("disabled", false).text("Salva Dati");
      } // Usa showInlineMessage2
    },
    error: function (xhr) {
      showInlineMessage2(
        messageTarget,
        xhr.responseJSON?.message || "Errore.",
        "error"
      );
      submitButton.prop("disabled", false).text("Salva Dati");
    }, // Usa showInlineMessage2
  });
}

// Funzione Submit Penalità Pista 2 ( ** Corretta logica success ** )
function submitPenaltyForm2(typeSuffix) {
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
    showInlineMessage2(messageSectionId, "Penalità non valida.", "error");
    return;
  } // Usa showInlineMessage2
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
        // ** Reset Stato Gioco QUI **
        console.log(
          "Score submitted successfully for",
          typeSuffix,
          ". Resetting game state."
        );
        if (typeSuffix === "couple2") {
          isGameActiveCouple2 = false;
          clearInterval(timerIntervalCouple2);
          startTimeCouple2 = null;
          localStorage.removeItem("startTimeCouple2"); // <--- AGGIUNTO
          $("#current-player-couple2").text("-");
          $("#timer-couple2").text("00:00");
        } else if (typeSuffix === "single2") {
          isGameActiveSingle2 = false;
          clearInterval(timerIntervalSingle2);
          startTimeSingle2 = null;
          localStorage.removeItem("startTimeSingle2"); // <--- AGGIUNTO
          $("#current-player-single2").text("-");
          $("#timer-single2").text("00:00");
        }
        // ** Chiudi form DOPO aver resettato stato **
        closeInlineForm2(typeSuffix, "penalty"); // Mostra controlli standard
        if (response.qualified) {
          console.log("Player qualified!");
          showInlineQualificationForm2({
            player_id: response.player_id,
            player_name: response.player_name,
            recorded_score: response.recorded_score,
            player_type: response.player_type,
            reason: response.reason,
          }); // Mostra form qualifica
        } else {
          console.log("Player did not qualify.");
          updateNextPlayer2();
          updateUIState2();
        } // Aggiorna UI se non qualificato
      } else {
        showInlineMessage2(
          messageSectionId,
          response.error || "Errore.",
          "error"
        );
        $(submitButtonId).prop("disabled", false).text("Conferma Score");
      } // Usa showInlineMessage2
    },
    error: function (xhr) {
      showInlineMessage2(
        messageSectionId,
        xhr.responseJSON?.error || "Errore.",
        "error"
      );
      $(submitButtonId).prop("disabled", false).text("Conferma Score");
    }, // Usa showInlineMessage2
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
      console.log("Response from /button_press for track 2:", response);
      if (!response.success) {
        alert(response.error || "Errore.");
        updateUIState2();
        return;
      }
      if (button.includes("_start")) {
        if (typeContext === "couple2") {
          startTimeCouple2 = new Date();
          localStorage.setItem("startTimeCouple2", startTimeCouple2.toISOString()); // <--- AGGIUNTO
          isGameActiveCouple2 = true;
          clearInterval(timerIntervalCouple2);
          timerIntervalCouple2 = setInterval(
            () => updateTimer2("couple2"),
            1000
          );
          $("#timer-couple2").text("00:00");
          if (response.current_player_bravo2)
            $("#current-player-couple2").text(
              response.current_player_bravo2.id
            );
          else if (response.current_player_alfa2)
            $("#current-player-couple2").text(response.current_player_alfa2.id);
        } else if (typeContext === "single2") {
          startTimeSingle2 = new Date();
          localStorage.setItem("startTimeSingle2", startTimeSingle2.toISOString()); // <--- AGGIUNTO
          isGameActiveSingle2 = true;
          clearInterval(timerIntervalSingle2);
          timerIntervalSingle2 = setInterval(
            () => updateTimer2("single2"),
            1000
          );
          $("#timer-single2").text("00:00");
          if (response.current_player_alfa2)
            $("#current-player-single2").text(response.current_player_alfa2.id);
        }
        updateUIState2();
        updateNextPlayer2();
      } else if (
        response.action === "penalty_input_required" &&
        button.includes("_stop")
      ) {
        console.log("Penalty input required for track 2:", response.player_id);
        if (response.player_type === "couple2") {
          clearInterval(timerIntervalCouple2);
        } else if (response.player_type === "single2") {
          clearInterval(timerIntervalSingle2);
        }
        showInlinePenaltyForm2(response); // Mostra sezione inline penalità Pista 2
      } else {
        updateUIState2();
        updateNextPlayer2();
      } // Per 'third2'
    },
    error: function (xhr) {
      alert(`Operazione fallita: ${xhr.responseJSON?.error || "Errore."}`);
      updateUIState2();
    },
  });
}

// --- READY E INTERVAL (Corretti con Delegazione Eventi) ---
$(document).ready(function () {
  console.log("Controls Combined 2 Ready (Inline Version - Listener Fixed)");
  activateNextPlayer2(); // Imposta stato iniziale UI

  fetch("/simulate")
    .then((r) => r.json())
    .then((data) => {
      const savedStartTimeCouple2 = localStorage.getItem("startTimeCouple2");
      const savedStartTimeSingle2 = localStorage.getItem("startTimeSingle2");

      if (
        savedStartTimeCouple2 &&
        ((data.current_player_bravo2 &&
          data.current_player_bravo2.id.startsWith("ROSA")) ||
         (data.current_player_alfa2 &&
          data.current_player_alfa2.id.startsWith("ROSA")))
      ) {
        startTimeCouple2 = new Date(savedStartTimeCouple2);
        isGameActiveCouple2 = true;
        clearInterval(timerIntervalCouple2);
        timerIntervalCouple2 = setInterval(() => updateTimer2("couple2"), 1000);
      } else {
        localStorage.removeItem("startTimeCouple2");
      }

      if (
        savedStartTimeSingle2 &&
        data.current_player_alfa2 &&
        (data.current_player_alfa2.id.startsWith("ARANCIO") ||
         data.current_player_alfa2.id.startsWith("BIANCO"))
      ) {
        startTimeSingle2 = new Date(savedStartTimeSingle2);
        isGameActiveSingle2 = true;
        clearInterval(timerIntervalSingle2);
        timerIntervalSingle2 = setInterval(() => updateTimer2("single2"), 1000);
      } else {
        localStorage.removeItem("startTimeSingle2");
      }
    })
    .catch((e) => {
      console.error("Errore nel ripristino stato timer:", e);
    });

  // ** Delegazione Eventi una sola volta **
  $(".control-container")
    .off("click", ".penalty-add-button")
    .on("click", ".penalty-add-button", function () {
      if ($(this).closest(".couple-section2, .single-section2").length > 0) {
        const seconds = parseInt($(this).data("seconds"));
        const targetSuffix = $(this).data("target-suffix");
        if (!isNaN(seconds) && targetSuffix) {
          addPenaltySeconds2(targetSuffix, seconds);
        }
      }
    })
    .off("click", ".reset-penalty-button")
    .on("click", ".reset-penalty-button", function () {
      if ($(this).closest(".couple-section2, .single-section2").length > 0) {
        const targetSuffix = $(this).data("target-suffix");
        if (targetSuffix) {
          resetPenaltyFields2(targetSuffix);
        }
      }
    })
    .off("submit", "#penalty-form-couple2")
    .on("submit", "#penalty-form-couple2", function (event) {
      event.preventDefault();
      submitPenaltyForm2("couple2");
    })
    .off("submit", "#penalty-form-single2")
    .on("submit", "#penalty-form-single2", function (event) {
      event.preventDefault();
      submitPenaltyForm2("single2");
    })
    .off("submit", "#qualification-form-couple2")
    .on("submit", "#qualification-form-couple2", function (event) {
      event.preventDefault();
      submitQualificationForm2("couple2");
    })
    .off("submit", "#qualification-form-single2")
    .on("submit", "#qualification-form-single2", function (event) {
      event.preventDefault();
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
