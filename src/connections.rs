use std::sync::mpsc;
use std::sync::mpsc::{Receiver};
use std::{thread, vec};
use std::io::{Read, Write};
use std::net::{TcpStream, Shutdown};
use crate::{database, NUM_CONNECTIONS};
use crate::management;
use crate::user_actions;

use database::IP;

fn node_helper(rx:mpsc::Receiver<Vec<u8>>, tx:mpsc::Sender<Vec<u8>>, broadcast_tx:mpsc::Sender<Vec<u8>>, db: database::ThreadConnection){
    let mut data:Vec<u8>;
    loop {
        data = rx.recv().unwrap();
        println!("2 {} {:?}", data.len(), data);

        match data[0] {
            255 => {
                break
            } 
            0 => {
                for i in 0..data.len() {
                    data[i] += 1;
                }
            }
            1 => {
                data.remove(0);
                broadcast_tx.send(data).unwrap();
                data = Vec::new();
            }
            2 => {
                data.remove(0);
                management::manage_ip(data, &db, &broadcast_tx);
                data = Vec::new();
            } 
            64 => {
                data.remove(0);
                let res = user_actions::register(data, &db, &broadcast_tx);
                data = vec![res];
            }
            65 => {
                data.remove(0);
                let res = user_actions::post(data, &db, &broadcast_tx);
                data = vec![res];
            }
            66 => {
                data.remove(0);
                let res = user_actions::update_info(data, &db, &broadcast_tx);
                data = vec![res];
            }
            67 => {
                data.remove(0);
                let res = user_actions::update_profile_picture(data, &db, &broadcast_tx);
                data = vec![res];
            }
            129 => {
                data.remove(0);
                data = user_actions::get_user(data, &db, &broadcast_tx);
            }
            _ => {
                for i in 0..data.len() {
                    data[i] += 1;
                }
            }
        }
        tx.send(data).unwrap();
    }
}

pub fn handle_node(mut stream:TcpStream, broadcast_tx:mpsc::Sender<Vec<u8>>, db: database::ThreadConnection){
    let mut data = [0 as u8; 50];
    let (tx1, rx) = mpsc::channel();
    let (tx, rx1) = mpsc::channel();
    thread::spawn(move || node_helper(rx1, tx1, broadcast_tx, db));
    let mut send_data:Vec<u8> = Vec::new();
    let mut return_data:Vec<u8> = Vec::new();
    let mut read:u32 = 0;
    let mut size:u32 = 0;
    'main: while match stream.read(&mut data) {
        Ok(_) => {
            for byte in data{
                if data == [0; 50] {
                    continue;
                }
                if read == 0{
                    if byte == 255 {
                        tx.send(vec![255_u8]).unwrap();
                        break 'main;
                    }
                }
                else if read < 4{
                    size |= (byte as u32) << 8*(3-read);
                }
                else{
                    send_data.push(byte);
                    println!("{}, {}, {:?}",size, read-3, send_data);
                }
                if read == size+3 && read != 0 {
                    read = 0;
                    size = 0;
                    println!("send {:?}", send_data);
                    if send_data[0] == 64 {
                        println!("1");
                    }
                    tx.send(send_data).unwrap();
                    return_data = rx.recv().unwrap();
                    println!("{:?}", return_data);
                    stream.write(&return_data).unwrap();
                    send_data = Vec::new();
                    data = [0; 50];
                }
                else {
                    read += 1;
                }
            }
            true
        },
        Err(_) => {
            println!("An error occurred, terminating connection with {}", stream.peer_addr().unwrap());
            stream.shutdown(Shutdown::Both).unwrap();
            false
        }
    } {}

}

pub fn broadcaster(db: database::ThreadConnection, rx: Receiver<Receiver<Vec<u8>>>) {
    //let ips: Vec<IP> = db.querry_ips(&format!("SELECT * FROM ips ORDER BY RAND() LIMIT {};", NUM_CONNECTIONS)).unwrap();
    let mut streams: Vec<TcpStream> = Vec::new(); 
    let mut recievers: Vec<Receiver<Vec<u8>>> = Vec::new();

    let mut connected = 0;
    while connected <= NUM_CONNECTIONS {
        let ips: Vec<IP> = db.querry_ips(&format!("SELECT * FROM ips ORDER BY RAND() LIMIT {};", 1)).unwrap();
        for ip in ips.iter() {
            match TcpStream::connect(ip.get_ip()) {
                Ok(stream) => {
                    streams.push(stream);
                    connected += 1;
                },
                Err(_) => {}
            }
            
        }
    }

    loop {
        match rx.try_recv(){
            Ok(rx) => recievers.push(rx),
            Err(_) => (),
        };
        for recieber in recievers.iter() {
            match recieber.try_recv() {
                Ok(data) => {
                    for mut stream in &streams {
                        stream.write(&data).unwrap();
                    }
                },
                Err(_) => (),
            };
        }
    }
}
