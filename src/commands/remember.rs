// commands/remember.rs

///Mémoriser une information

use crate::core::input::get_input;
use crate::core::structures::Context;

// fonction handle
pub fn handle_remember(ctx: &mut Context) {
    println!("Que dois-je me souvenir ?");
    ctx.memory = get_input();
    println!("Ok, je m'en souviendrai !");
}