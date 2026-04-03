// commands/weather.rs

use crate::commands::localize::handle_localize;

pub fn handle_weather() {
    println!("⛅ Météo en cours...");
    handle_localize();
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
