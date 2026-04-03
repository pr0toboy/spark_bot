// core/command_info.rs

/// Liste des commandes disponibles dans Spark

// Enumération des commandes
#[derive(Clone, Copy)]
pub enum Command {
    Start,
    Remember,
    Recall,
    Help,
    Exit,
    Pomodoro,
    Localize,
    Todo,
    Unknown,
    Remind,
    Weather
}

impl From<&str> for Command {
    fn from(input: &str) -> Self {
        // Ne garder que le premier mot (la commande) pour la recherche
        let cmd_token = input.split_whitespace().next().unwrap_or("");
        all_commands()
            .iter()
            .find(|cmd| cmd.name == cmd_token)
            .map(|cmd| cmd.command)
            .unwrap_or(Command::Unknown)
    }
}
// Structure sur les informations des commandes
pub struct CommandInfo {
    pub name: &'static str,
    pub command: Command,
    pub description: &'static str,
}

pub fn all_commands() -> &'static [CommandInfo] {
    &[
        CommandInfo { name: "/start",    command: Command::Start,    description: "Démarrer une nouvelle tâche" },
        CommandInfo { name: "/remember", command: Command::Remember, description: "Mémoriser une information" },
        CommandInfo { name: "/recall",   command: Command::Recall,   description: "Afficher ce que Spark a mémorisé" },
        CommandInfo { name: "/help",     command: Command::Help,     description: "Afficher la liste des commandes" },
        CommandInfo { name: "/exit",     command: Command::Exit,     description: "Quitter le programme" },
        CommandInfo { name: "/pomodoro", command: Command::Pomodoro, description: "Lancer un minuteur Pomodoro" },
        CommandInfo { name: "/localize", command: Command::Localize, description: "Me localiser dans le monde (IP)" },
        CommandInfo { name: "/todo",     command: Command::Todo,     description: "Gérer une liste de tâches" },
        CommandInfo { name: "/remind",   command: Command::Remind,   description: "Créer un rappel pour une certaine durée" },
        CommandInfo { name: "/weather",  command: Command::Weather,  description: "Affiche la météo d'une ville" },
    ]
}
