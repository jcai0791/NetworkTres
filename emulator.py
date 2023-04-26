import argparse 
import socket
import struct
import csv
from collections import defaultdict

MAX_BYTES = 6000

####### OLD STUFF #########

#wraps inner packet (payload) with outer header
def encapsulate(priority, src_ip, src_port, dest_ip, dest_port,payload):
    packet = struct.pack(f"!B4sH4sHI{len(payload)}s",priority,src_ip,src_port,dest_ip,dest_port,len(payload),payload)
    return packet

#returns outer header and inner packet separately
def decapsulate(packet):
    header = struct.unpack_from("!B4sH4sHI",packet)
    length = header[5]
    payload = struct.unpack_from(f"!{length}s",packet,offset=17)[0]
    return header,payload

#Parses topology table
def parseTable(fileName, selfHostname, selfPort):
    with open(fileName, "r") as f:
        d = defaultdict(lambda : ("",0,0,0))
        reader = csv.reader(f,delimiter=' ')
        for row in reader:
            if(row[0]==selfHostname and int(row[1])==selfPort):
                destHost = socket.inet_aton(socket.gethostbyname(row[2]))
                destPort = int(row[3])
                nextHost = socket.gethostbyname(row[4])
                nextPort = int(row[5])
                delay = int(row[6])/1000.0
                lossProb = int(row[7])
                d[(destHost, destPort)] = (nextHost,nextPort, delay, lossProb) 
        return d

#Sends packet to (ip,port)
def sendPacket(packet, ip, port):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(packet,(ip,port))

######## HELPERS #######
def sendHello():
    pass

def sendLinkState():
    pass

####### REQUIRED FUNCTIONS ########
def readtopology(filename):
    pass

def createroutes():
    pass

def forwardpacket():
    pass

def buildForwardTable():
    pass




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-f", "--filename")
    args = parser.parse_args()
    filename = args.filename
    port = int(args.port)
    # sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    # sock.bind((socket.gethostname(), port))
    readtopology(filename)



            


    
