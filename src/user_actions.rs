use crate::database;
use crate::cryptography;
use crate::database::ThreadConnection;
use crate::management::get_time;
use std::sync::mpsc::Sender;
use base64;
use ed25519_dalek::Signature;
use rand::{thread_rng, Rng};
use rand::distributions::Alphanumeric;

pub fn register(mut data: Vec<u8>, db: &database::ThreadConnection, broadcast_tx:&Sender<Vec<u8>>) -> u8 {
    // byte 1: len username
    // byte 2

    let mut data_point:usize = 2;
    
    //username len = data[0]
    //info len = data[1]
    let username = String::from_utf8(data[data_point..data[0] as usize+data_point].to_vec()).unwrap();
    data_point += data[0] as usize;
    let info = String::from_utf8(data[data_point..data[1] as usize+data_point].to_vec()).unwrap();
    data_point += data[1] as usize;
    let public_key = String::from_utf8(data[data_point..44+data_point].to_vec()).unwrap();
    data_point += 44;
    let profile_picture = String::from_utf8(data[data_point..64+data_point].to_vec()).unwrap();
    data_point += 64;
    let signature = String::from_utf8(data[data_point..data_point+88].to_vec()).unwrap();
    let keyfile:String = thread_rng().sample_iter(&Alphanumeric).take(30).map(char::from).collect();

    let size = (data.len()+1).to_be_bytes();

    println!("{:?}", data);

    match cryptography::verify(&data[2..data_point], &signature, &cryptography::get_user_pub_key(&base64::decode(&public_key).unwrap())) {
        true => {
            println!("1");
            let mut broadcast_vec = vec![size[4], size[5], size[6], size[7], 64];
            broadcast_vec.append(&mut data);

            let res = db.querry_users(&format!("SELECT * FROM users WHERE user_name = '{}';", username)).unwrap(); 
            println!("res {:?}", res);
            if res.len() == 0 {
                let sql = format!("INSERT INTO users(user_name, public_key, key_file, timestamp, profile_picture, info) VALUES('{}', '{}', '{}', {}, '{}', '{}');", username, &public_key, keyfile, get_time(), profile_picture, info);
                match db.execute(&sql) {
                    Ok(_) => {
                        println!("2");
                        broadcast_tx.send(broadcast_vec).unwrap();
                        return 1
                    },
                    Err(e) => {
                        println!("{}", e);
                        return 64;
                    }
                }
            }
            else {
                return 66;
            }
        },
        false => {
            return 65;
        }
    }
}

pub fn post(mut data:Vec<u8>, db:&database::ThreadConnection, broadcast_tx:&Sender<Vec<u8>>) -> u8 {
    //byte 1: len user-name
    //byte 2: len post

    let mut data_point:usize = 2;

    let id = String::from_utf8(data[data_point..data_point+23].to_vec()).unwrap();
    data_point += 23;
    let user_name = String::from_utf8(data[data_point..data[0] as usize+data_point].to_vec()).unwrap();
    data_point += data[0] as usize;
    let post = String::from_utf8(data[data_point..data[1] as usize+data_point].to_vec()).unwrap();
    data_point += data[1] as usize;
    let background_color = data[data_point];
    data_point += 1;
    let timestamp = get_time();
    let signature = String::from_utf8(data[data_point..data_point+88].to_vec()).unwrap();

    let res = db.querry_users(&format!("SELECT * FROM users WHERE user_name = '{}';", user_name)).unwrap();

    println!("{},\n {},\n {},\n {},\n {},\n {}", id, user_name, post, background_color, timestamp, signature);

    if res.len() == 0 {
        return 64
    }

    let public_key = cryptography::get_user_pub_key(&base64::decode(&res[0].public_key).unwrap());
    
    println!("{:?} {}", &data[2..data_point], id);

    match cryptography::verify(&data[2..data_point], &signature, &public_key) {
        true => {
            let size = (data.len()+1).to_be_bytes();
            let mut broadcast_vec = vec![size[4], size[5], size[6], size[7], 64];
            broadcast_vec.append(&mut data);

            let sql = format!("INSERT INTO posts(id, user_name, post, background_color, timestamp, signature) VALUE('{}', '{}', '{}', {}, {}, '{}')", id, user_name, post, background_color, timestamp, signature);
            return match db.execute(&sql) {
                Ok(_) => {
                    broadcast_tx.send(broadcast_vec).unwrap();
                    1
                },
                Err(_) => 66
            };
        },
        false => {
            return 65
        }
    }
}

pub fn update_info(mut data:Vec<u8>, db:&database::ThreadConnection, broadcast_tx:&Sender<Vec<u8>>) -> u8 {
    let mut data_point:usize = 2;

    let user_name = String::from_utf8(data[data_point..data_point+data[0] as usize].to_vec()).unwrap();
    data_point += data[0] as usize;
    let info = String::from_utf8(data[data_point..data_point+data[1] as usize].to_vec()).unwrap();
    data_point += data[1] as usize;
    let signature = String::from_utf8(data[data_point..data_point+88].to_vec()).unwrap();

    let res = db.querry_users(&format!("SELECT * FROM users WHERE user_name = '{}';", user_name)).unwrap();

    if res.len() == 0 {
        return 64
    }

    let public_key = cryptography::get_user_pub_key(&base64::decode(&res[0].public_key).unwrap());

    match cryptography::verify(&data[2..data_point], &signature, &public_key) {
        true => {
            let size = (data.len()+1).to_be_bytes();
            let mut broadcast_vec = vec![size[4], size[5], size[6], size[7], 64];
            broadcast_vec.append(&mut data);

            let sql = format!("UPDATE users SET info = '{}' WHERE user_name = '{}';", info, user_name);
            return match db.execute(&sql) {
                Ok(_) => {
                    broadcast_tx.send(broadcast_vec).unwrap();
                    1
                },
                Err(_) => 66
            };
        },
        false => {
            return 65
        }
    }

    0
}

pub fn update_profile_picture(mut data:Vec<u8>, db:&database::ThreadConnection, broadcast_tx:&Sender<Vec<u8>>) -> u8 {
    let mut data_point:usize = 1;

    let user_name = String::from_utf8(data[data_point..data_point+data[0] as usize].to_vec()).unwrap();
    data_point += data[0] as usize;
    let profile_picture = String::from_utf8(data[data_point..data_point+64].to_vec()).unwrap();
    data_point += 64;
    let signature = String::from_utf8(data[data_point..data_point+88].to_vec()).unwrap();

    let res = db.querry_users(&format!("SELECT * FROM users WHERE user_name = '{}';", user_name)).unwrap();

    if res.len() == 0 {
        return 64
    }

    let public_key = cryptography::get_user_pub_key(&base64::decode(&res[0].public_key).unwrap());

    match cryptography::verify(&data[1..data_point], &signature, &public_key) {
        true => {
            let size = (data.len()+1).to_be_bytes();
            let mut broadcast_vec = vec![size[4], size[5], size[6], size[7], 64];
            broadcast_vec.append(&mut data);

            let sql = format!("UPDATE users SET profile_picture = '{}' WHERE user_name = '{}';", profile_picture, user_name);
            return match db.execute(&sql) {
                Ok(_) => {
                    broadcast_tx.send(broadcast_vec).unwrap();
                    1
                },
                Err(_) => 66
            };
        },
        false => {
            return 65
        }
    }

    0
}

pub fn get_user(mut data:Vec<u8>, db:&database::ThreadConnection, broadcast_tx:&Sender<Vec<u8>>) -> Vec<u8> {
    let user_name = String::from_utf8(data[1..data[0] as usize+1].to_vec()).unwrap();
    let mut res = match db.querry_users(&format!("SELECT * FROM users WHERE user_name = '{}'", user_name)) {
        Ok(res) => {
            res
        },
        Err(_) => return vec![65],
    };

    if res.len() == 0 {
        return vec![64]
    }

    let mut data = vec![1];
    data.append(&mut res[0].to_bytes());

    data
}