#!/usr/bin/env python3

# Simple GUI demo
#
# Set script as executable via: chmod +x gui.py
# Run via:  ./gui.py
#
# Note: The Tkinter packages may not be installed by default.
# To install:   sudo apt-get install python3-tk




import signal
import socket
import sys
import argparse
import threading 
import struct
import io
import queue
import os
import tkinter
import time
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename




def main():
        parser = argparse.ArgumentParser('Comp/ECPE 177 Web Server')
        parser.add_argument('--version', action='version', version='%(prog)s 3.2.3', help ="This argument will print out the version number of the program")
        parser.add_argument("--target", action= 'store', dest='target_ip', help="This argument specifies the IP or hostname the client contacts to run the test.", default= 'localhost')
        parser.add_argument("--port", action= 'store', dest='port_num', help="This argument specifies the port number", default= '8765')
        #parser.add_argument("--server", action= 'store_false', dest= 'cs_mode', help= "This argument configures the tester to act as a server.")

        args = parser.parse_args()
        ip = args.target_ip
        port = int(args.port_num)
        #csmode = args.cs_mode
        #if(csmode == False):        
        server(ip, port)



def server(ip, port):
        q = queue.Queue(maxsize=0)
        establish_connection = server_establish_connection(q, ip, port)
        establish_connection.start()        
        
class server_establish_connection(threading.Thread):
        def __init__(self, q, ip, port):
                threading.Thread.__init__(self)
        
                self.q = q
                self.port = int(port)
                self.ip = ip
                self.chat_users = []      

                try:
                        self.listen_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                except socket.error as msg:
                        print("Error: could not create socket")
                        print("Description: " + str(msg))
                        sys.exit()

                try:
                        self.host=''  # Bind to all interfaces
                        self.listen_s.bind((self.host, self.port))
                except socket.error as msg:
                        print("Error: unable to bind on port " + str(self.port))
                        print("Description: " + str(msg))
                        sys.exit()

                try:
                        backlog=10  
                        self.listen_s.listen(backlog)
                except socket.error as msg:
                        print("Error: unable to listen()")
                        print("Description: " + str(msg))
                        sys.exit()    

                print("Listening socket bound to port " + str(self.port))

                #print("HELLO YOU HAVE REACHED BEFORE THE WHILE LOOP")

                
        def run(self):
                #print("HELLO YOU HAVE REACHED AFTER THE WHILE LOOP")
                while(True):
                        try:
                                (self.ctrl_s, self.client_addr) = self.listen_s.accept()
                        except socket.error as msg:
                                print("Error: unable to accept()")
                                print("Description: " + str(msg))
                                sys.exit()

                        print("Accepted incoming connection from client")
                        print("Client IP, Port = %s" % str(self.client_addr))
                        print("THIS IS CTRL_S: " + str(self.ctrl_s))
                        print("YOU ARE ABOUT TO START THE RECEIVING THREAD!!")
                        receiving = server_receive(self.ctrl_s, self.q, self.ip, self.port, self.chat_users)
                        receiving.start()
                        echoing = echo_client_joined(self.ctrl_s, self.q, self.chat_users)
                        echoing.start()
        
class server_receive(threading.Thread):
        def __init__(self, ctrl_s, q, ip, port, chat_users):
                threading.Thread.__init__(self)
                self.q = q
                self.port = int(port)
                self.ip = ip   
                self.ctrl_s = ctrl_s
                self.chat_users = chat_users
                
        def run(self):
                ONLINE = True
                
                while(ONLINE):
                        
                        print("Value of ONLINE: " + str(ONLINE))
                        try:
                                print("This is the control socket: " + str(self.ctrl_s))
                                client_request = self.ctrl_s.recv(4096)
                                if(len(client_request)) > 0:
                                        if(str(client_request).find("CHAT/1.0")):
                                                while(str(client_request).find("LEAVE") == -1):
                                                        self.q.put((client_request, self.ctrl_s))
                                                        client_request = self.ctrl_s.recv(4096)
                                                        print(str(client_request))
                                                print("THIS IS CLIENT REQUEST WHEN YOU LEAVE: " + str(client_request))
                                                      
                                                print("FOUND LEAVE!!")
                                                self.q.put((client_request, self.ctrl_s))
                                                ONLINE = False;

                                else:
                                        print ("THIS DOESN'T BELONG TO THE CHAT")
                        except socket.error as msg:
                                print("Error: unable to recv()")
                                print("Description: " + str(msg))
                                sys.exit()
                        
                        

                        
                
                try:
                        self.ctrl_s.close()
                except socket.error as msg:
                        print("Error: unable to close() client socket")
                        print("Description: " + str(msg))

                return

                
class echo_client_joined(threading.Thread):
        def __init__(self, ctrl_s, q, chat_users): 
                threading.Thread.__init__(self)   
                #self.ctrl_s = ctrl_s
                self.chat_users = chat_users
                self.q = q
        def run(self):

                ONLINE = True

                while(ONLINE):
                        print("You have now entered the echo client: ")
                        client_data, ctrl_s = self.q.get()
                        
                        print("Client Data: " + str(client_data))
                        
                        message = client_data.decode('ascii')
                        print("Client Data Decode: " + str(message))
                       
                        
                        
                        
               
                        
                        if(message.find("JOIN")):
                                
                                self.chat_users.append(ctrl_s)

                        elif(message.find("TEXT")):
                                username = split_message[1][10:]

                        elif(message.find("LEAVE")):
                                self.chat_users.remove(ctrl_s)
                                if(len(self.chat_users) == 0):
                                        ONLINE = False
                        else:
                                print("HI")
                        
                        print("YOU MADE IT THIS FAR NOW FINISH THIS THING AND SEND THE CLIENT DATA")
                        
                        for i in range(len(self.chat_users)):
                                print(str(self.chat_users))
                                #if(str(self.chat_users[i]) != str(ctrl_s)):
                                print(str(self.chat_users[i]) +" : " +str(ctrl_s))
                                self.chat_users[i].sendall(bytes(client_data))
                       
                        return
                
if __name__ == "__main__":
    sys.exit(main())
