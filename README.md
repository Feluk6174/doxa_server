# TdR_server
In this repository, te code for the server made for our "Treball de recerca" is stored, if you are looking for the GUI or the simulations, those are stored in the following repos:

Android app: https://github.com/Feluk6174/TdR_gui

Simulations: https://github.com/Feluk6174/TdR_simulations

## Instalation guide
The following installation is for Linux, concretly, ubuntu and arch based distros. The same or similar steps sould work with other OSs, but they might have to be adapted.

This project has beentested using python 3.10.7.

### installing the database
First, we have to install the database. We use Mariadb pakage, but a mysql database should also work, but this has not been tested.

To install mariad on arch, run the following commands:

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

Then 
