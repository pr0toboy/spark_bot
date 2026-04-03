// commands/weather.rs

// Affiche la météo d'une ville

<<<<<<< Updated upstream
pub fn handle_weather() {
    println!("⛅ Commande /weather non encore implémentée.");
}
=======
// structure des informations à donner à l'utilisateur
#[derive(Deserialize, Debug)]
struct Meteo {
    city: Option<String>,
    weather: Option<String>,
    wind: Option<String>,
    temperature: Option<String>,
    barometer: Option<String>,
}

//fonction handle
pub fn handle_weather() {
    println!("🔍 Analyse de la météo en cours...");

    //récupère les informations de localisation depuis le site "https://ipinfo.io/json"
    let response = get("");
    match response {
        Ok(resp) => {
            let location: Result<Location, _> = resp.json();
            match location {
                Ok(loc) => {
                    println!("🌍 IP : {}", loc.ip.unwrap_or("Inconnue".to_string()));
                    println!("📍 Ville : {}", loc.city.unwrap_or("Inconnue".to_string()));
                    println!("🗺️ Région : {}", loc.region.unwrap_or("Inconnue".to_string()));
                    println!("🇺🇳 Pays : {}", loc.country.unwrap_or("Inconnu".to_string()));
                    println!("🛰️ Coordonnées : {}", loc.loc.unwrap_or("Inconnues".to_string()));
                    println!("🏢 Fournisseur : {}", loc.org.unwrap_or("Inconnu".to_string()));
                }
                Err(_) => println!("Erreur de lecture des données JSON."),
            }
        }
        Err(_) => println!("Erreur de connexion à l’API."),
    }
}

fn wc_emoji(code: i32) -> (&'static str, &'static str) {
    match code {
        0 => ("☀️", "Ciel dégagé"),
        1 => ("🌤️", "Plutôt clair"),
        2 => ("⛅", "Partiellement nuageux"),
        3 => ("☁️", "Couvert"),
        45 | 48 => ("🌫️", "Brouillard"),
        51 | 53 | 55 => ("🌦️", "Bruine"),
        61 => ("🌦️", "Pluie faible"),
        63 => ("🌧️", "Pluie"),
        65 => ("🌧️", "Pluie forte"),
        66 | 67 => ("🌧️❄️", "Pluie verglaçante"),
        71 | 73 | 75 => ("❄️", "Neige"),
        77 => ("🌨️", "Grains de neige"),
        80 => ("🌦️", "Averses faibles"),
        81 => ("🌧️", "Averses"),
        82 => ("🌧️🌧️", "Averses fortes"),
        85 | 86 => ("🌨️", "Averses de neige"),
        95 | 96 | 99 => ("⛈️", "Orage"),
        _ => ("❓", "Inconnu"),
    }
}
>>>>>>> Stashed changes
