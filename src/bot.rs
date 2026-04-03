// bot.rs

/// Cerveau de Spark
/// Boucle principale du projet qui traduit les commandes reçu en fonction à exécuter

////////////////////////////   IMPORT   ////////////////////////////////
use crate::core::input::{
    get_input,
    welcome_message
};
use crate::commands::{
    help, localize, pomodoro, recall, remember, remind, start, todo, weather
};
use crate::core::command_info::Command;
use crate::core::structures::Context;

///////////////////////////////////////////////////////////////////////

// Fonction principale de Spark
pub fn spark_bot() {

    let mut ctx = Context {
        memory: String::new(),
        todo_list: HashMap::new(),
        reminders: std::sync::Arc::new(std::sync::Mutex::new(Vec::new()))
    };

    // Message de bienvenue
    welcome_message();

    loop {
        let input = get_input();

        match Command::from(input.as_str()) {
            Command::Start => start::handle_start(), //Démarrer une nouvelle tâche (fais rien pour l'instant)
            Command::Remember => remember::handle_remember(&mut ctx), //Mémoriser une information
            Command::Recall => recall::handle_recall(&ctx.memory), //Afficher ce que Spark a mémorisé
            Command::Pomodoro => pomodoro::handle_pomodoro(), //Lancer un minuteur Pomodoro
            Command::Localize => localize::handle_localize(), //Me localiser dans le monde (IP)
            Command::Todo => todo::handle_todo(&mut ctx.todo_list), //Gérer une liste de tâches
            Command::Remind => remind::handle_remind(&mut ctx, input.as_str()), //Créer un rappel pour une certaine durée
            Command::Help => help::handle_help(), //Afficher la liste des commandes
            Command::Weather => weather::handle_weather(), //Afficher la météo d'une ville
            Command::Exit => { // Quitter la conversation avec Spark
                println!("À bientôt !");
                break;
            }
            Command::Unknown => println!("Commande inconnue !"),
        }
    }
}
