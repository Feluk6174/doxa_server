use crate::database;
use std::time::{SystemTime, UNIX_EPOCH, Duration};
use std::sync::mpsc::Sender;
use std::thread;

use crate::CLOCK_TIME;

pub fn get_time() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}

fn ip_bytes(ip:String) -> Vec<u8> {
    let mut bytes:Vec<u8> = Vec::new();
    let mut vec = ip.split(".").collect::<Vec<&str>>();
    let a = vec[vec.len()-1];
    vec.remove(vec.len()-1);
    let vec2 = a.split(":").collect::<Vec<&str>>();
    vec.push(vec2[0]);

    for s in vec {
        bytes.push(s.parse::<u8>().unwrap());
    }

    bytes.push(vec2[1].parse::<u16>().unwrap().to_be_bytes()[0]);
    bytes.push(vec2[1].parse::<u16>().unwrap().to_be_bytes()[1]);

    println!("{:?}", bytes);
    bytes
}

pub fn manage_ip(data: Vec<u8>, db: &database::ThreadConnection, broadcast_tx:&Sender<Vec<u8>>) {
    let ip:String = format!("{}.{}.{}.{}:{}", data[0], data[1], data[2], data[3], (data[4] as u16) << 8 | data[5] as u16);

    //println!("ip: {}", ip);

    let broadcast_vec:Vec<u8> = vec![0, 0, 0, 7, 2, data[0], data[1], data[2], data[3], data[4], data[5]];

    //println!("ips1: {:?}", db.querry_ips("SELECT * FROM ips;").unwrap());

    db.execute(&format!("DELETE FROM ips WHERE timestamp <= {}", get_time()-CLOCK_TIME*2)).unwrap();
    let res = db.querry_ips(&format!("SELECT * FROM ips WHERE ip = '{}';", ip)).unwrap();

    //println!("ips2: {:?}", db.querry_ips("SELECT * FROM ips;").unwrap());

    if res.len() == 0 {
        match db.execute(&format!("INSERT INTO ips(ip, timestamp) VALUES('{}', {});", ip, get_time())) {
            Err(e) => {
                println!("{}", e); 
                return
            },
            Ok(_) => {
                broadcast_tx.send(broadcast_vec).unwrap();
            }
        }
    }
    else if res[0].get_timestamp() <= get_time()-CLOCK_TIME {
        let err1 = match db.execute(&format!("DELETE FROM ips WHERE ip = '{}'", ip)) {
            Ok(_) => true,
            Err(_) => false
        };

        let err2 = match db.execute(&format!("INSERT INTO ips(ip, timestamp) VALUES('{}', {})", ip, get_time())) {
            Ok(_) => true,
            Err(_) => false
        };
        if !err1 && !err2 {
            broadcast_tx.send(broadcast_vec).unwrap();
        }
    }
    //println!("ips3: {:?}", db.querry_ips("SELECT * FROM ips;").unwrap());
}

pub fn clock(ip:String, broadcast_tx:Sender<Vec<u8>>) {
    let ip = ip_bytes(ip);
    thread::sleep(Duration::from_secs(CLOCK_TIME));
    loop {
        let ip_msg:Vec<u8> = vec![0, 0, 0, 7, 2, ip[0], ip[1], ip[2], ip[3], ip[4], ip[5]];
        println!("{:?} {}", ip, get_time());
        broadcast_tx.send(ip_msg).unwrap();

        thread::sleep(Duration::from_secs(CLOCK_TIME));
    }
}