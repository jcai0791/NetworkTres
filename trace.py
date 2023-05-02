import argparse 
import socket
import struct
import csv
from collections import defaultdict
import sys
MAX_BYTES = 6000

####### OLD STUFF #########

#wraps inner packet (payload) with outer header
def encapsulateRouteTrace(TTL, src_ip, src_port, dest_ip, dest_port):
    packet = struct.pack(f"!cI4sH4sH",b'T',TTL,src_ip,src_port,dest_ip,dest_port)
    return packet

#returns outer header and inner packet separately
def decapsulateRouteTrace(packet):
    header = struct.unpack_from(f"!cI4sH4sH", packet)
    return header

def receiveResponse(listenSocket):
    header = None
    try:
        data, addr = listenSocket.recvfrom(MAX_BYTES)
        header = decapsulateRouteTrace(data)
    except:
        return header
                  #0   1    2        3        4       5
    return header #T, TTL, srcIP, srcPort, destIP, destPort


#Sends packet to (ip,port). ip is bytes
def sendPacket(packet, ip, port):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(packet,(socket.inet_ntoa(ip),port))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--routetrace_port")
    parser.add_argument("-b", "--source_hostname")
    parser.add_argument("-c", "--source_port")
    parser.add_argument("-d", "--destination_hostname")
    parser.add_argument("-e", "--destination_port")
    parser.add_argument("-f", "--debug_option")
    args = parser.parse_args()
    port = int(args.routetrace_port)
    sourceIP = socket.inet_aton(socket.gethostbyname(args.source_hostname))
    sourcePort = int(args.source_port)
    destIP = socket.inet_aton(socket.gethostbyname(args.destination_hostname))
    destPort = int(args.destination_port)
    ownIP = socket.inet_aton(socket.gethostbyname(socket.gethostname()))
    debug = int(args.debug_option)

    listenSocket = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    listenSocket.bind((socket.gethostname(), port))
    listenSocket.settimeout(5)
    done = False
    curTTL = 0
    while not done:
        rPacket = encapsulateRouteTrace(curTTL,ownIP,port,destIP,destPort)
        sendPacket(rPacket,sourceIP,sourcePort)
        if(debug==1):
            print("=====Sent Packet====")
            print("TTL: ",curTTL)
            print("Source IP: ",socket.inet_ntoa(sourceIP))
            print("Source Port: ",sourcePort)
            print("Dest IP: ",socket.inet_ntoa(destIP))
            print("Dest Port: ",destPort)
            print("=====================")
        response = receiveResponse(listenSocket)
        if(response == None):
            print("Cannont reach node")
            sys.exit()
        print("Received Response from: ",(socket.inet_ntoa(response[4]),response[5]))
        if(debug == 1):
            print("=====Received Packet====")
            print("TTL: ",response[1])
            print("Source IP: ",socket.inet_ntoa(response[2]))
            print("Source Port: ",response[3])
            print("Dest IP: ",socket.inet_ntoa(response[4]))
            print("Dest Port: ",response[5])
            print("=====================")
        if(response[2] == destIP and response[3] == destPort):
            print("Destination reached")
            done = True
        else:
            curTTL += 1







            


    
