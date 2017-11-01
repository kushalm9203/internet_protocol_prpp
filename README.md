
A protocol that randomizes and constantly updates the transport layer ports being used for transmission of data over the internet to provide enhanced security.

Running the client_script file with the given command line inputs will initiate a client connection to the server through an interactive command line environment.

The file can be run as: ./client_script --arg -- arg .....

After this the user will be promted to enter: send; recv, close. If send or recv are given, the local file desciption, and the target file description on the server also need to be provided. If close is given, no other arguments should be given. The command line argument --source lets the user decide whether to input text from stdin, or read data from a file. The command line argument --target lets the user decide whether to write to a file on server or write to stdout. For more help use ./client_script -h

Running the server_script file with the given command line inputs will initiate a server connenction that listens for a client connection and provides an interactive command line environment. If verbose is set, it dumps information regarding connection and packets onto the command line.

The file can be run as: ./server_script --arg -- arg .....

After this the server program listens for possible client connections. For more help use ./server_script -h.
