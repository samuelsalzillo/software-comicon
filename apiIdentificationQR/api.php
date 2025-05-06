<?php
// Author: Dario Arienzo Mercenari SOCS
// Data: 07/05/2025

// Parametri di connessione al database Aruba
$servername = "89.46.111.73";
$username = "Sql1252807";
$password = "Is9F?IXkwb90kaOd";
$dbname = "Sql1252807_3";

// Connessione al database
$conn = new mysqli($servername, $username, $password, $dbname);

// Controllo della connessione
if ($conn->connect_error) {
    die(json_encode(["success" => false, "error" => "Connessione fallita: " . $conn->connect_error]));
}

// Query: leggi tutti i record da "identificativi"
$sql = "SELECT * FROM identificativi";  // 
$result = $conn->query($sql);

$data = [];

// Itero i risultati
if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
}

// Chiudi la connessione
$conn->close();

// Restituisci i dati in formato JSON
header('Content-Type: application/json');
echo json_encode(["success" => true, "data" => $data]);
?>