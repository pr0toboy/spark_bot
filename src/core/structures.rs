// core/structure.rs

/// Centralise les structures et contextes nécessaires pour le bot et ses commandes

use serde::Deserialize;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime};

#[derive(Deserialize, Debug)]
pub struct Location {
    pub city: Option<String>,
    pub region: Option<String>,
    pub country: Option<String>,
    pub loc: Option<String>, // latitude,longitude
    pub ip: Option<String>,
    pub org: Option<String>,
}

/// Structure pour la commande /remind
pub struct Reminder {
    pub message: String,
    pub duration: Duration,
    pub creation_time: SystemTime,
}

/// Mémoire de Spark
pub struct Context {
    pub memory: String, // pour remember/recall
    pub todo_list: HashMap<String, Vec<String>>, // pour /todo 
    pub reminders: Arc<Mutex<Vec<Reminder>>>, // pour /remind : stockage thread-safe et clonable pour les handlers qui spawn des threads
}