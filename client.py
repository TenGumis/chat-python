import tkinter as tk
import threading
from tkinter import messagebox
from socket import *
import time
import sys

s = socket(AF_INET, SOCK_STREAM) #utworzenie gniazda
s.connect(('localhost', 12345)) #nawiazanie polaczenia

def parse(x):
    if(x.count(';')>=4):
        tmp=x.split(';')
        if(tmp[0]=='msg'):
            return (('msg',tmp[1],tmp[2],tmp[3]),';'.join(tmp[4:],))
        elif tmp[0]=='usr':
            return (('usr',tmp[3].split(',')),';'.join(tmp[4:],))
        elif tmp[0]=='logok':
            return ('logok',';'.join(tmp[4:],))  
        elif tmp[0]=='logfail':
            return ('logfail',';'.join(tmp[4:],))        
    else:
        return (None,x)

class Client(tk.Frame):
    def __init__(self,nickname,buff,master=None):
        tk.Frame.__init__(self,master)
        self.master.minsize(600,400)
        self.grid(sticky = tk.N + tk.S + tk.E + tk.W)
        self.master.rowconfigure(0,weight=1)
        self.master.columnconfigure(0,weight=1)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.createWidgets()
        self.selectedUser=None
        self.nickname=nickname
        self.master.title('Chat: '+str(nickname))
        self.ucho= Hear(self,buff);
        self.ucho.start()
    
    def showMessage(self,frm,to,message,sep=' => '):
        self.chatBox.insert(tk.END, frm+sep+to+':\n'+message+'\n')
        self.chatBox.see(tk.END)

    def updateUsers(self,k):
        self.userList.delete(0,tk.END)
        k.insert(0,'ALL')
        for x in range(len(k)):
            self.userList.insert(x,k[x])
        self.userList.activate(0)
            

    def createWidgets(self):
        
        self.chatFrame= tk.Frame(self)
        self.chatFrame.grid(row = 0, column = 0, rowspan=10,sticky = tk.S+tk.N+tk.E+tk.W)
        self.chatBox= tk.Text(self.chatFrame, height=10)
        self.chatBox.grid(row = 0, column = 0,sticky = tk.S+tk.N+tk.E+tk.W)
        self.chatBox.bind("<Key>", lambda e: "break")
        self.sscr=tk.Scrollbar(self.chatFrame)
        self.sscr.grid(column=1, row=0,sticky=tk.N + tk.S + tk.W + tk.E)
        self.chatBox.config(yscrollcommand=self.sscr.set)
        self.sscr.config(command=self.chatBox.yview)
        self.chatFrame.columnconfigure(0,weight=1)
        self.chatFrame.rowconfigure(0,weight=1)

        self.usersFrame = tk.Frame(self)
        self.usersFrame.grid(column=1, row=0, rowspan=15, padx=5,sticky=tk.N + tk.S + tk.W + tk.E)
        scr = tk.Scrollbar(self.usersFrame)
        scr.grid(column=1, row=1,sticky=tk.N + tk.S + tk.W + tk.E)
        
        userLabel= tk.Label(self.usersFrame,text='User list:').grid(column=0,row=0, sticky = tk.N+tk.S+tk.E+tk.W)    
        self.userList=tk.Listbox(self.usersFrame)
        self.userList.insert(0,'ALL')
        self.userList.activate(0)

        self.userList.grid(column=0, row=1, sticky = tk.N+tk.S+tk.E+tk.W)
        self.userList.config(yscrollcommand=scr.set)
        scr.config(command=self.userList.yview)
          
        self.usersFrame.columnconfigure(0,weight=1)
        self.usersFrame.rowconfigure(0,weight=1)
        self.usersFrame.rowconfigure(1,weight=15)      

        self.messageBox= tk.Text(self,height=3)
        self.messageBox.grid(row = 10, column = 0 , rowspan=5,sticky = tk.S+ tk.N +tk.E+tk.W)
        
        self.sendButton = tk.Button(self, text='Send Message')
        self.sendButton.myName = "Send Button"
        self.sendButton.grid(row = 15, column = 0, sticky = tk.N+tk.S+tk.E+tk.W)
        self.sendButton.bind("<Button-1>" , self.send)
        self.exitButton = tk.Button(self, text='Exit')
        self.exitButton.myName = "Exit Button"
        self.exitButton.grid(row=15,column=1, sticky = tk.N+tk.S+tk.E+tk.W)
        self.exitButton.bind("<Button-1>" , self.exit)
        
        self.master.bind_all("<Return>", self.send)

        for i in range(16):
            self.rowconfigure(i,weight=1) 
        self.columnconfigure(0,weight=3)
        self.columnconfigure(1,weight=1)

    def handler(self, event):
        pass
    
    def send(self,event):
        to=self.userList.get(tk.ACTIVE)
        msg=self.messageBox.get('1.0',tk.END).strip()
        if len(msg)==0:
            self.messageBox.delete('0.0',tk.END)
            self.messageBox.insert(tk.INSERT, "Message cannot be empty.")
        else:
            if self.ucho.status==True:
                msg='msg;'+self.nickname+";"+to+";"+msg+';'
                s.send(bytes(msg, 'UTF-8'))
            self.messageBox.delete('1.0', tk.END)

    def exit(self,event):
        if self.ucho.status==True:
            msg='logout;;;'+self.nickname+';'  
            s.send(bytes(msg, 'UTF-8'))
            s.close()
        self.ucho.status=False
        self.master.destroy()
        

    def on_closing(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.exit(None)
        
class Hear(threading.Thread):
    def __init__(self,root,buff):
        self.buff=buff
        self.root=root
        self.status=True
        super().__init__(daemon=True)

    def run(self):
        try:
            while self.status:
                while self.buff.count(';')>=4:
                    tmp=parse(self.buff)
                    self.buff=tmp[1]
                    if (tmp[0] is not None ):
                        tmp=tmp[0]
                        if(tmp[0] == 'msg'):
                            self.root.showMessage(tmp[1],tmp[2],tmp[3])
                        else:
                            self.root.updateUsers(tmp[1])
                try:
                    echodane=''            
                    echodane = s.recv(1024)
                    if not echodane:
                        self.root.showMessage('','','The connection to server failed.','')
                        self.status=False
                        s.close()
                        break
                except:
                    self.root.showMessage('','','The connection to server failed.','')
                    self.status=False
                    s.close()
                    return
                echodane=echodane.decode('UTF-8')
                self.buff+=echodane
                
        finally:
            s.close()

buff=''
nickname=None
while nickname is None:        
    nickname = input('nickaneme: ')
    if(nickname != 'ALL' and nickname!=''):
        msg='login;;;'+nickname+';'  
        s.send(bytes(msg, 'UTF-8'))
        while True:        
            data = s.recv(1024).decode('UTF-8')
            tmp=parse(buff+data)
            buff=tmp[1]
            if(tmp[0]=='logok'):
                break;
            elif tmp[0]=='logfail':
                print("This nickname has already been taken.")
                nickname=None
                break;                
        
    else:
        print("This nickname has already been taken.")
clientApp = Client(nickname=nickname,buff=buff) 
clientApp.mainloop()
