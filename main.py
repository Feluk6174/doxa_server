import database
import threading, socket, sys
import log

import managment
import user_actions
import conn
import conf


def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        HOST = s.getsockname()[0]
        s.close()
    except OSError:
        HOST = "127.0.0.1"
    try:
        PORT = int(sys.argv[1])
    except IndexError:
        PORT = int(input("Input port: "))
    IP = HOST+":"+str(PORT)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    connections = []
    clients = []

    try:
        if sys.argv[2] == "-v":
            logger = log.Logger(f"logs/main_log_{PORT}_", vervose = True)
        else:
            logger = log.Logger(f"logs/main_log_{PORT}_")
    except IndexError:
        logger = log.Logger(f"logs/main_log_{PORT}_")

    db = database.Database(logger = logger)

    managment.init(logger, clients, connections, db, HOST, IP, PORT, server)
    user_actions.init(logger, db)
    conn.init(logger, clients, connections, db)

    db.create()
    db.querry("INSERT INTO grups VALUES(0, '{\"pos\": [0, 0]}');")

    logger.log("Welcome to ...")
    logger.log("""
                                                                                    
                     #@@@@@@@@@@@,                                              
            (@@@@@@@@@@@@@@@@@@@@@@@@@@@                                        
       @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                                   
      /@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&                       (#    
        @@@@@@@    .#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&/*,. *@@@@@@@@@    
         @@@@@@           @@@@@@&      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    
          @@@@@@    @/     @@@@          @@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    
          (@@@@@@   @@@     @@    @@@    @@@@    @@@@&  .&@@@@@@@@@@@@@@@@@#    
           @@@@@@   &@@@    @    @@@@    #@@@%   @@@    @@@@    @@@@@@@@@@@     
           @@@@@@   (@@@    @    @@@@    &@@@@        *@@@@@    @@@@@@@@@@@     
           ,@@@@@   (@@%   .&   *@@@@    @@@@@       @@@@@@      @@@@@@@@@      
            @@@@@   @@@    @%    @@@*    @@@@&     #@@@@@@*  @@  @@@@@@@@       
            @@@@    @@    @@@    @@.    @@@@       (@@@@@@   @.  @@@@@@@        
           (@@@@         @@@@          @@@.    @   ,@@@@@       .@@@@@@         
           @@@@@       @@@@@@@        @@@    @@@    @@@@         @@@@@@         
          @@@@@    @@@@@@@@@@@@@    @@@/    @@@@    @@@    %@*   @@@@@@         
         @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    @@     @@@ ,*,@@@@@@        
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@**@@@@@@@@@@@@@@@@@@@@*       
       @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&      
     .@@@@@.                         *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     
                                           .@@@@@@@@@@@@@@@                   
    """)
    logger.log(f"========[SERVER RUNNING ON {IP}]========")
    thread = threading.Thread(target=managment.clock)
    thread.start()
    thread = threading.Thread(target=managment.start)
    thread.start()
    managment.main()
    
if __name__ == "__main__":
    main()
