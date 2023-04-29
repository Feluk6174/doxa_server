use rand::rngs::OsRng;
use ed25519_dalek::Keypair;
use ed25519_dalek::{Signature, Signer};
use ed25519_dalek::{PublicKey, Verifier};
use std::fs;
use base64;


fn main(){
    gen_keys();
    let key_pair:Keypair = get_keys();
    let msg: &[u8] = b"hello world!";
    //let signature: [u8; 64] = sign(msg, &key_pair);
}

pub fn gen_keys(){
    let mut csprng = OsRng{};
    let keypair = Keypair::generate(&mut csprng);
    println!("{}", base64::encode(keypair.to_bytes()));
    fs::write("key_pair.bin", base64::encode(keypair.to_bytes())).expect("error riting to file");
}

pub fn get_keys() -> Keypair{
    Keypair::from_bytes(&base64::decode(fs::read_to_string("key_pair.bin").expect("Unable to read file")).unwrap()).unwrap()
}

pub fn verify(data:&[u8], signature:&str, public_key:&PublicKey) -> bool{
    match public_key.verify(data, &Signature::from_bytes(&base64::decode(signature).unwrap()).unwrap()) {
        Ok(()) => true,
        Err(_) => false,
    }
}

pub fn sign(data:&[u8], key_pair:&Keypair) -> String{
    base64::encode(key_pair.sign(data).to_bytes())
}

pub fn get_pub_key() -> String {
    base64::encode(Keypair::from_bytes(&base64::decode(fs::read_to_string("key_pair.bin").expect("Unable to read file")).unwrap()).unwrap().public.to_bytes())
}

pub fn get_user_pub_key(bytes:&[u8]) -> PublicKey {
    PublicKey::from_bytes(bytes).unwrap()
}