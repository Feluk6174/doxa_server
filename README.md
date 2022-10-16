# TdR_server
In this repository, te code for the server made for our "Treball de recerca" is stored, if you are looking for the GUI or the simulations, those are stored in the following repos:

Android app: https://github.com/Feluk6174/TdR_gui

Simulations: https://github.com/Feluk6174/TdR_simulations

## Instalation guide
The following installation is for Linux, concretly, ubuntu and arch based distros. The same or similar steps sould work with other OSs, but they might have to be adapted.

This project has beentested using python 3.10.7.

First run the following commands:
```
    $ git clone https://github.com/Feluk6174/TdR_server.git
    $ cd TdR_server
```

Then install the libraries using the followuing command:
```
    $ pip install -r requirements.txt
```

### installing the database
First, we have to install the database. We use `mariadb`, but a `mysql` database should also work, but this has not been tested.

To install `mariadb` on arch, run the following commands:

```
    $ sudo pacman -S mariadb
    $ sudo mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
```

To install it on ubuntu, run the follwing:
```
    $ sudo apt update
    $ sudo apt install mariadb-server
```

Run the following commands, to start the database, and make that the database starts after system reboot: 
```
    $ sudo systemctl start mariadb.service
    $ sudo systemctl enable mariadb.service
```

To improve the seurity of the instalation, run the following command:

```
    $ sudo mysql_secure_installation
```

Select the configuations that you find adecuate.

#### Creating the user
Run the following command to enter the database:
```
    $ sudo mysql
```

Run the following command to create the database.
```
    MariaDB> CREATE DATABASE TdR;
```

Run the following command to create the user that will manage the database, replacing `[password]` with the password for the user.
```
    MariaDB> CREATE USER 'TdR'@'localhost' IDENTIFIED BY '[password]';
```

Run the following command to give acces to the user to the database.
```
    MariaDB> GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES, RELOAD on TdR.* TO 'TdR'@'localhost' WITH GRANT OPTION;
```

Run the following command to make sure that new privileges are put to efect.
```
    MariaDB> FLUSH PRIVILEGES;
```

Now you can exit the database, using `Ctrl+C` or running the following command `exit`.

Finaly finish setting up the database execute the `setup_db.py` script:
```
    $ python setup_db.py
```
### Starting the program
Creating a service, will make that the program starts after system reboot.

To do this, modify the `TdR.service`, replacing `[path]` with the path to `main.py` (you can get the path runing `pwd`, and appending `/main.py` to the end), and replacing `[port]` with the port where the program will run.

Then copy the TdR.service file to the `/etc/systemd/system` folder.
```
    $ sudo cp ./TdR.service /etc/systemd/system
```

Finally we can start the program.
```
    $ sudo systemctl start TdR
```

And enable it, this will make the program start after reboot
```
    $ sudo systemctl enable TdR
```