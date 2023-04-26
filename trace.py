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

#Sends packet to (ip,port)
def sendPacket(packet, ip, port):
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    sock.sendto(packet,(ip,port))






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
    source = (args.source_hostname,int(args.source_port))
    dest = (args.destination_hostname,int(args.destination_port))

    # sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    # sock.bind((socket.gethostname(), port))



            


    
