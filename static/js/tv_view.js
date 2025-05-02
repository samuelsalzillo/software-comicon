function formatTimeRome(date) {
  // Formats date object or ISO string into HH:MM for Rome timezone
  if (!date || date === "N/D") return "N/D";
  try {
    const options = {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Europe/Rome",
    };
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) {
      // console.warn(`Invalid date passed to formatTimeRome: ${date}`);
      return "N/D";
    }
    return dateObj.toLocaleTimeString("it-IT", options);
  } catch (e) {
    console.error("Errore formattazione data:", date, e);
    return "N/D";
  }
}

function updateListContent(listId, players) {
  const listElement = document.getElementById(listId);
  if (!listElement) {
    console.error(`Element with ID ${listId} not found.`);
    return;
  }

  // --- Simple Populate List ---
  listElement.innerHTML = ""; // Clear current list content
  const isEmpty = !Array.isArray(players) || players.length === 0;

  if (isEmpty) {
    const li = document.createElement("li");
    li.textContent = "Nessun Giocatore in Coda";
    listElement.appendChild(li);
    listElement.classList.add("empty"); // Add class for styling empty list
  } else {
    listElement.classList.remove("empty");
    players.forEach((player) => {
      // Basic check for valid player data
      if (!player || typeof player.id === "undefined") {
        console.warn(`Invalid player data in list ${listId}:`, player);
        return; // Skip this invalid player entry
      }

      const timeDisplay =
        player.estimated_time === "PROSSIMO INGRESSO"
          ? "PROSSIMO INGRESSO"
          : formatTimeRome(player.estimated_time);
      const li = document.createElement("li");
      li.textContent = `${player.id} - ${timeDisplay}`;

      // Add a class based on the player's type
      const playerIdStr = String(player.id);
      if (playerIdStr.includes("GIALLO")) li.classList.add("bg-yellow");
      else if (playerIdStr.includes("BLU")) li.classList.add("bg-blue");
      else if (playerIdStr.includes("ROSA")) li.classList.add("bg-pink");
      else if (playerIdStr.includes("BIANCO")) li.classList.add("bg-white");
      else if (playerIdStr.includes("VERDE")) li.classList.add("bg-green");
      else if (playerIdStr.includes("ROSSO")) li.classList.add("bg-red");

      // Add blinking effect for "PROSSIMO INGRESSO"
      if (player.estimated_time === "PROSSIMO INGRESSO") {
        li.classList.add("blinking");
      }

      li.style.fontWeight = "bold"; // Fallback to black if color is not defined
      listElement.appendChild(li);
    });
  }
  // Scroll the container viewport back to top after update (optional)
  const viewport = listElement.closest(".list-viewport");
  if (viewport) {
    viewport.scrollTop = 0;
  }
}

// Fetch data and update all lists periodically
function updateAllLists() {
  fetch("/simulate") // Fetch data from the backend endpoint
    .then((response) => {
      if (!response.ok) {
        // Handle HTTP errors (e.g., 404, 500)
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json(); // Parse JSON response
    })
    .then((data) => {
      // Ensure data properties exist and are arrays, provide empty arrays as defaults
      const couples = Array.isArray(data.couples) ? data.couples : [];
      const singles = Array.isArray(data.singles) ? data.singles : [];
      const couples2 = Array.isArray(data.couples2) ? data.couples2 : [];
      const singles2 = Array.isArray(data.singles2) ? data.singles2 : [];
      const charlie = Array.isArray(data.charlie) ? data.charlie : [];
      const statico = Array.isArray(data.statico) ? data.statico : [];

      // Update each specific list using the fetched (and validated) data
      updateListContent("tv-couples-list", couples);
      updateListContent("tv-singles-list", singles);
      updateListContent("tv-couples2-list", couples2);
      updateListContent("tv-singles2-list", singles2);
      updateListContent("tv-charlie-list", charlie);
      updateListContent("tv-statico-list", statico);

      // Clear any previous general error messages if fetch was successful
      document.querySelectorAll(".error-message").forEach((el) => el.remove());
    })
    .catch((error) => {
      // Handle network errors or errors during fetch/processing
      console.error("Error fetching or processing simulation data:", error);
      // Display a user-friendly error message (e.g., in the first list)
      const firstList = document.getElementById("tv-couples-list");
      if (firstList && !firstList.querySelector(".error-message")) {
        const errorLi = document.createElement("li");
        errorLi.textContent = "Errore caricamento dati...";
        errorLi.style.color = "red";
        errorLi.classList.add("error-message");
        firstList.innerHTML = ""; // Clear previous content
        firstList.appendChild(errorLi);
      }
    });
}

// --- Initialization ---
// Wait for the DOM to be fully loaded before running scripts
document.addEventListener("DOMContentLoaded", () => {
  updateAllLists(); // Perform initial data load when the page is ready
  // Set up periodic updates using setInterval
  // Updates every 10000 milliseconds (10 seconds). Adjust interval as needed.
  setInterval(updateAllLists, 10000);
});
