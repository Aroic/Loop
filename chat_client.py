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


global ONLINE

def main():
        parser = argparse.ArgumentParser('Comp/ECPE 177 Web Server')
        parser.add_argument('--version', action='version', version='%(prog)s 3.2.3', help ="This argument will print out the version number of the program")
        #parser.add_argument("--target", action= 'store', dest='target_ip', help="This argument specifies the IP or hostname the client contacts to run the test.", default= 'localhost')
        parser.add_argument("--port", action= 'store', dest='port_num', help="This argument specifies the port number", default= '8765')
        parser.add_argument("--username", action= 'store', dest='user_name', help="This argument specifies the name of the user")
        parser.add_argument("--client", action= 'store_true', dest= 'cs_mode', help= "This argument configures the tester to act as a client.")
        
        args = parser.parse_args()
        ip = args.target_ip
        port = int(args.port_num)
        username = str(args.user_name)
        csmode = args.cs_mode
        
        if(csmode == True):        
                client(ip, port, username)
        else:
                print("NOT TRUE")

def client(ip, port, username):
        
        print(username)
        
        q_join = queue.Queue()
        q_text = queue.Queue()
        q_leave = queue.Queue()
        send_q = queue.Queue()
        establish_connection = client_establish_connection(q_join, q_text, q_leave, send_q, ip, port, username)
        establish_connection.start()
        
        
        
        print("Running GUI Demo")

        # Instantiate class for UI
        ui = clientUI(q_join, q_text, q_leave, send_q, username)

        # Run the UI, and capture CTRL-C to terminate
        try:
                ui.start()
        except KeyboardInterrupt:
                print("Caught CTRL-C, shutting down client")
                global ONLINE
                ONLINE = False
                ui.eventDeleteDisplay()
                print("GUI Demo exiting")




class client_establish_connection(threading.Thread):
        
        def __init__(self, q_join, q_text, q_leave, send_q, ip, port, username):
                threading.Thread.__init__(self)
                print(username)
                self.q_join = q_join
                self.q_text = q_text
                self.q_leave = q_leave
                self.send_q = send_q
                self.username = username
                self.port = port
                self.ip = ip
                # Create TCP socket
                try:
                        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                except socket.error as msg:
                        print("Error: could not create socket")
                        print("Description: " + str(msg))
                        sys.exit()

                print("Connecting to server at " + self.ip + " on port " + str(self.port))
             
                # Connect to server
                
        def run(self):
                receiving = recvClient_data(self.s, self.q_join, self.q_text, self.q_leave)
                sending = sendClient_data(self.ip, self.port, self.s, self.send_q, self.username)
                try:
                        receiving.start()
                except KeyboardInterrupt:
                        print ("Exiting client receive thread")
                try:
                        sending.start()
                except KeyboardInterrupt:
                        print ("Exiting client send thread")
                

class sendClient_data(threading.Thread):
        def __init__(self, ip, port, data_s, send_q, username):
                threading.Thread.__init__(self)
                self.send_q = send_q
                self.username = username
                self.data_s = data_s
                self.ip = ip
                self.port = port
                
                try:
                        self.data_s.connect((self.ip , self.port))
                        
                except socket.error as msg:
                        print("Error: Could not open connection")
                        print("Description: " + str(msg))
                        sys.exit()
         
                print("Connection established")
                
        def run(self): 
                global ONLINE
                ONLINE = True
                
                JOIN_head = "CHAT/1.0 JOIN\r\n"
                JOIN_head += "Username: " + str(self.username) + "\r\n"
                JOIN_head += "\r\n"
                header_data = bytes(JOIN_head, 'ascii')
                
                try:
                        self.data_s.sendall(header_data)
                except socket.error as msg:
                        print("Error: sendall() failed")
                        print("Description: " + str(msg))
                        sys.exit()

                while(ONLINE):
                        print("Value of Online: " + str(ONLINE))
                        try:
                                text_message = self.send_q.get(timeout = 1)
                        except queue.Empty:
                                print("Queue is empty")
                                continue
                        
                        print("TEXT MESSAGE!! " + str(text_message))
                                
                        print("TEXT SENDING")
                        TEXT_head = "CHAT/1.0 TEXT\r\n"
                        TEXT_head += "Username: " + str(self.username) + "\r\n"
                        TEXT_head += "Mesg-len: " + str(len(text_message)) + "\r\n"
                        TEXT_head += "\r\n"
                        TEXT_head += text_message
                        text_data = bytes(TEXT_head, 'ascii')
                        
                        try:
                                self.data_s.sendall(text_data)
                       
                        except socket.error as msg:
                                print("Error: sendall() text_data failed")
                                print("Description: " + str(msg))
                                sys.exit()
                                print("TEXT SENT")
                print("Value of Online: " + str(ONLINE)) 
                
                LEAVE_head = "CHAT/1.0 LEAVE\r\n"
                LEAVE_head += "Username: " + str(self.username) + "\r\n"
                LEAVE_head += "\r\n"
                leave_data = bytes(LEAVE_head, 'ascii')
                
                try:
                        self.data_s.sendall(leave_data)
                except socket.error as msg:
                        print("Error: sendall() failed")
                        print("Description: " + str(msg))
                        sys.exit()

                return
                  


class recvClient_data(threading.Thread):
        def __init__(self, data_s, q_join, q_text, q_leave):
                threading.Thread.__init__(self)
                self.q_join = q_join
                self.q_text = q_text
                self.q_leave = q_leave
                self.data_s = data_s
        def run(self): 
                
                ONLINE = True
                while(ONLINE):
                        print("RECEIVING = " + str(ONLINE))
                        try:
                                print("I am trying to recv!")
                                response = self.data_s.recv(4096)
                                if(len(response) == 0):
                                        response = self.data_s.recv(4096)
                                        response = response + response
                                print("This is response: \n" + str(response))
                        except socket.error as msg:
                                print("Error: unable to recv()")
                                print("Description: " + str(msg))
                                sys.exit()
                        
                        
                        
                        server_response = response.decode('ascii')
                        
                        print("This is server response: \n" + str(server_response))
                        
                        server_response_split = server_response.split('\r\n')
                        
                        print(str(server_response_split[0]))
                        
                        
                        if(server_response_split[0].find("JOIN")):
                                print("FOUND JOIN YOU!!")
                                if(server_response_split[1].find("\r\n\r\n") == -1):
                                        text, separator, username = server_response_split[1].partition(":")
                                print(text)
                                print(separator)
                                print(username)
                                username = username.strip()
                                print(username)
                                self.q_join.put(username)

                        elif(server_response_split[0].find("TEXT")):
                                username = server_response_split[1][10:]
                                text = response_split[4]
                                #print(str(username) + str(text))
                                self.q_text.put((username, text))

                        elif(server_response_split[0].find("LEAVE")):
                                username = server_response_split[1][10:]
                                print ("LEAVE username is... " + str(username))
                                self.q_leave.put(username)

                        else:
                                print("YOU HAVE RECEIVED SOMETHING INVALID HERE!")

                return				
		
                        


class clientUI():
    def __init__(self, q_join, q_text, q_leave, send_q, username):
        self.first_click = True;
        self.q_join = q_join
        self.q_text = q_text
        self.q_leave = q_leave
        self.send_q = send_q
        self.username = username
    def start(self):
        print("Starting clientUI...")
        self.initDisplay()

        self.ui_messages.insert(tkinter.END, "%s has joined the chat room...\n" % self.username)
        self.ui_input.insert(tkinter.END, "<Enter message>")
        self.ui_top.after(100, self.receivedMsg)
        # This call to mainloop() is blocking and will last for the lifetime
        # of the GUI.
        self.ui_top.mainloop()

        # Should only get here after destroy() is called on ui_top
        print("Stopping clientUI...")
        

    def initDisplay(self):
        self.ui_top = tkinter.Tk()
        self.ui_top.wm_title("GUI Demo")
        self.ui_top.resizable('1','1')
        self.ui_top.protocol("WM_DELETE_WINDOW", self.eventDeleteDisplay)
        
        self.ui_messages = ScrolledText(
            master=self.ui_top,
            wrap=tkinter.WORD,
            width=50,  # In chars
            height=25)  # In chars     

        self.ui_input = tkinter.Text(
            master=self.ui_top,
            wrap=tkinter.WORD,
            width=50,
            height=4)
        
        # Bind the button-1 click of the Entry to the handler
        self.ui_input.bind('<Button-1>', self.eventInputClick)
        
        self.ui_button_send = tkinter.Button(
            master=self.ui_top,
            text="Send",
            command=self.sendMsg)

        self.ui_button_file = tkinter.Button(
            master=self.ui_top,
            text="File",
            command=self.sendFile)

        # Compute display position for all objects
        self.ui_messages.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.ui_input.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.ui_button_send.pack(side=tkinter.LEFT)
        self.ui_button_file.pack(side=tkinter.RIGHT)


    # SEND button pressed
    def sendMsg(self):
        # Get user input (minus newline character at end)
        msg = self.ui_input.get("0.0", tkinter.END+"-1c")
        if(len(msg) > 0):
                self.send_q.put(msg)
                print("UI: Got text: '%s'" % msg)

                # Add this data to the message window
                self.ui_messages.insert(tkinter.INSERT, "%s: %s\n" % (self.username, msg))
                self.ui_messages.yview(tkinter.END)  # Auto-scrolling

                # Clean out input field for new data
                self.ui_input.delete("0.0", tkinter.END)



    def receivedMsg(self):
        try:
                joined_username = self.q_join.get(block=False)
                joined = True;
        except queue.Empty:
                joined = False;

        try:
                text_username, text = self.q_text.get(block=False)
                text = True;
        except queue.Empty:
                text = False;

        try:
                left_username = self.q_leave.get(block=False)
                left = True;
        except queue.Empty:
                left = False;

        if(joined):
                self.ui_messages.insert(tkinter.INSERT, str(joined_username) + " has joined the chatroom\n" )
                self.ui_messages.yview(tkinter.END)  # Auto-scrolling

        elif(text):
                self.ui_messages.insert(tkinter.INSERT, str(text_username) + ": " + str(text) + "\n")
                self.ui_messages.yview(tkinter.END)  # Auto-scrolling

        elif(left): 
                self.ui_messages.insert(tkinter.INSERT, str(left_username) + " has left the chat room...\n")
                self.ui_messages.yview(tkinter.END)  # Auto-scrolling

        self.ui_top.after(5000, self.receivedMsg)



    # FILE button pressed
    def sendFile(self):
        file = askopenfilename()

        if(len(file) > 0 and os.path.isfile(file)):
            print("UI: Selected file: %s" % file)
        else:
            print("UI: File operation canceled")

    # Event handler - User closed program via window manager or CTRL-C
    def eventDeleteDisplay(self):
        print("UI: Closing")
        global ONLINE
        ONLINE = False;
        # Continuing closing window now
        self.ui_top.destroy()

    # Event handler - User clicked inside the "ui_input" field
    def eventInputClick(self, event):
        if(self.first_click):
            # If this is the first time the user clicked,
            # clear out the tutorial message currently in the box.
            # Otherwise, ignore it.
            self.ui_input.delete("0.0", tkinter.END)
            self.first_click = False;




if __name__ == "__main__":
    sys.exit(main())

