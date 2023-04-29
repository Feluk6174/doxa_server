use std::env;
fn main() {
    let args: Vec<String> = env::args().collect();
    println!("{:?}", args.clone());
    match &args.get(1) {
        Some(_) => println!("ok"),
        None => println!("no ok")
    };
}