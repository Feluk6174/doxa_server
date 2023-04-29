use std::sync::mpsc;
use std::sync::mpsc::Receiver;
use std::thread;
use std::net::TcpListener;
use std::io;
pub mod database;
mod connections;
pub mod management;
pub mod cryptography;
pub mod user_actions;
use std::env;
use std::time::Duration;

static CLOCK_TIME:u64 = 30;
static NUM_CONNECTIONS: u64 = 3;

fn main() {
    //env::set_var("RUST_BACKTRACE", "1");
    //gets ip from user input
    let mut ip = String::from("127.0.0.1:");
    let args: Vec<String> = env::args().collect();
    match args.get(1) {
        Some(arg) => {
            println!("{:?}", &args);
            ip += &arg.to_string();
        },
        None => {
            println!("yo wtf");
            let mut input = String::new();
            io::stdin().read_line(&mut input).expect("error: unable to read user input");
            ip += &input.to_string()[0..input.len()-1];
        }
    };
    println!("start");
    //sleeps, to staart other instances during testing
    thread::sleep(Duration::from_secs(10));
    println!("start");
    
    //starts listener
    let listener = TcpListener::bind(ip.clone()).unwrap();

    //initzialises database
    let database_tx = database::start_db();

    //initializes broadcaster
    let broadcast_database_thread = database::ThreadConnection::new(&database_tx);
    let (broadcaster_tx, rx) = mpsc::channel::<Receiver<Vec<u8>>>();
    thread::spawn(move || connections::broadcaster(broadcast_database_thread, rx));

    let (tx, rx) = mpsc::channel::<Vec<u8>>();
    broadcaster_tx.send(rx).unwrap();
    let send_ip = ip.clone();
    thread::spawn(move || management::clock(send_ip, tx));

    for stream in listener.incoming() {
        let stream = stream.unwrap();

        let (tx, rx) = mpsc::channel::<Vec<u8>>();
        let database_thread = database::ThreadConnection::new(&database_tx);
        thread::spawn(move || connections::handle_node(stream, tx, database_thread));
        broadcaster_tx.send(rx).unwrap();
        

        println!("Connection established!");
    }

    drop(listener);
}
