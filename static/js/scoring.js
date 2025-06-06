let enviroment_treasure_hunt = 0

fetch("/config/treasure_hunt_active")
   .then(response => response.json())
   .then(config => {
    enviroment_treasure_hunt = config
    const componente = document.getElementById('treasure_hunt');
    if(enviroment_treasure_hunt === 0)
        componente.style.display = 'none'
    })


    function updateLeaderboard() {
      const sync = document.getElementById('myToggle');
      let checked = "?sync=False"
      if(sync)
        checked = sync.checked ? "?sync=True" : "?sync=False"
      fetch("/get_scores" + checked)
        .then((response) => response.json())
        .then((data) => {
          const couplesLeaderboard = document.getElementById(
            "couples-leaderboard"
          );
          const singlesLeaderboard = document.getElementById(
            "singles-leaderboard"
          );
          const charlieLeaderboard = document.getElementById(
            "charlie-leaderboard"
          );

          const topPlayersContainer = document.getElementById(
            "top-players-container"
          );

          couplesLeaderboard.innerHTML = "";
          singlesLeaderboard.innerHTML = "";
          charlieLeaderboard.innerHTML = "";
          topPlayersContainer.innerHTML = "";

          function createPlayerDiv(player, index) {
            const div = document.createElement("div");
            div.style.display = "flex";
            div.style.alignItems = "center";

            const rank = document.createElement("h3");
            rank.textContent = `${index + 1}.`;
            rank.style.marginRight = "10px";

            if (index < 3) {
              rank.style.color = "gold";
            } else {
              rank.style.color = "white";
            }

            const playerInfo = document.createElement("b");
            playerInfo.textContent = `${player[0]} - ${player[1]}`;
            if (player[0].startsWith("ROSSO")) {
              playerInfo.style.backgroundColor = "red";
            } else if (player[0].startsWith("GIALLO")) {
              playerInfo.style.backgroundColor = "#F29F05";
            } else if (player[0].startsWith("BLU")) {
              playerInfo.style.backgroundColor = "#1F598C";
            } else if (player[0].startsWith("VERDE")) {
              playerInfo.style.backgroundColor = "#8FBF60";
            } else if (player[0].startsWith("ROSA")) {
              playerInfo.style.backgroundColor = "#D95276";
            } else if (player[0].startsWith("BIANCO")) {
              playerInfo.style.backgroundColor = "white";
            } else {
              playerInfo.style.backgroundColor = "gray"; // Default color
            }
            // style color black if player[o].startsWith("BIANCO") or startsWith("ROSA")
            playerInfo.style.color = player[0].startsWith("BIANCO")
              ? "black"
              : "white";
            playerInfo.style.padding = "5px";
            playerInfo.style.borderRadius = "5px";

            div.appendChild(rank);
            div.appendChild(playerInfo);
            div.style.marginBottom = "5px";
            return div;
          }

          data.couples.forEach((player, index) => {
            couplesLeaderboard.appendChild(createPlayerDiv(player, index));
          });

          data.singles.forEach((player, index) => {
            singlesLeaderboard.appendChild(createPlayerDiv(player, index));
          });

          data.charlie.forEach((player, index) => {
            charlieLeaderboard.appendChild(createPlayerDiv(player, index));
          });

          // Aggiungi i migliori 3 giocatori per ogni classifica
          fetch("/leaderboard/top3")
            .then((response) => response.json())
            .then((top3Data) => {
              const categories = ["couples", "singles", "charlie"];
              categories.forEach((category) => {
                const topPlayers = top3Data[category];
                if (topPlayers && topPlayers.length > 0) {
                  const categoryDiv = document.createElement("div");
                  categoryDiv.innerHTML = `<h4>${category.toUpperCase()}</h4>`;
                  const ul = document.createElement("ul");
                  topPlayers.forEach((player, index) => {
                    const li = document.createElement("li");
                    li.textContent = `${index + 1}. ${player.name} (${
                      player.score
                    })`;
                    ul.appendChild(li);
                  });
                  categoryDiv.appendChild(ul);
                  categoryDiv.style.color = "white";
                  topPlayersContainer.appendChild(categoryDiv);
                }
              });
            })
            .catch((error) =>
              console.error(
                "Errore durante il caricamento dei migliori 3 giocatori:",
                error
              )
            );
        })
        .catch((error) =>
          console.error(
            "Errore durante l'aggiornamento della classifica:",
            error
          )
        );
    }

    // Aggiorna la classifica ogni secondo
    setInterval(updateLeaderboard, 10000);

    // Aggiorna la classifica all'avvio della pagina
    document.addEventListener("DOMContentLoaded", updateLeaderboard);