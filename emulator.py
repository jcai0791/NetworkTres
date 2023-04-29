import argparse 
import socket
import struct
import csv
from collections import defaultdict

MAX_BYTES = 6000
TOPOLOGY = defaultdict(lambda : [])
ROUTING = defaultdict(lambda : (b'',0))
####### OLD STUFF #########
def getType(packet):
    pass
#wraps inner packet (payload) with outer header
def encapsulateLinkState(src_ip, src_port,seq_no,ttl,payload):
    packet = struct.pack("!c4sHIII" +("8s"*len(payload)),b'L', src_ip,src_port,seq_no,len(payload), ttl , *[i[0].to_bytes(4,'big') + i[1].to_bytes(4,'big') for i in payload])
    return packet

#returns outer header and inner packet separately
def decapsulateLinkState(packet):
    header = struct.unpack_from("!c4sHIII",packet)
    convert = lambda x: (x[:4], int.from_bytes(x[4:], "big"))
    length = header[4]
    payload = [convert(struct.unpack_from(f"!8s",packet,offset=19+(8*i))[0])  for i in range(length)]

    return header,payload

def encapsulateRouteTrace(TTL, src_ip, src_port, dest_ip, dest_port):
    packet = struct.pack(f"!BI4sH4sH",'T',TTL,src_ip,src_port,dest_ip,dest_port)
    return packet

#returns outer header and inner packet separately
def decapsulateRouteTrace(packet):
    header = struct.unpack(f"!BI4sH4sH")
                  #0   1    2        3        4       5
    return header #T, TTL, srcIP, srcPort, destIP, destPort

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
def readtopology(filename,sip,sport):
    with open(filename, "r") as f:
        d = []
        for row in csv.reader(f, delimiter=' '):
            ip,port = row[0].split(",")
            TOPOLOGY[(socket.inet_aton(ip),int(port))] = list(map(lambda x: (socket.inet_aton(x.split(",")[0]), int(x.split(",")[1]) ),  row[1:]))
    buildForwardTable(socket.inet_aton(sip),int(sport))

def createroutes():
    pass

def forwardpacket(packet,sip,sport):
    t = struct.unpack_from("!c", packet, offset=0)
    if(t == b'H'):
        pass
    elif(t == b'L'):
        header,payload = decapsulateLinkState(packet)
        if(header[4]==0):
            return
        packet = encapsulateLinkState(header[1],header[2], header[3], header[4]-1, payload)
        for n in TOPOLOGY[(sip,sport)]:
            sendPacket(packet,n[0],n[1])

    else: #Routetrace packet
        header = decapsulateRouteTrace(packet)
        if(header[1]==0):
            newRP = encapsulateRouteTrace(0,sip,sport,header[4],header[5])
            sendPacket(newRP,header[2],header[3])
        else:
            newRP = encapsulateRouteTrace(header[1]-1,header[2],header[3],header[4],header[5])
            nextHop = ROUTING[(header[4],header[5])]
            sendPacket(newRP,nextHop[0],nextHop[1])

    #header,_ = decapsulateLinkState(packet)

def buildForwardTable(sip, sport):
    global ROUTING
    ROUTING = { i : i for i in TOPOLOGY[(sip,sport)] }
    q = TOPOLOGY[(sip,sport)]
    visited = {i for i in TOPOLOGY[(sip,sport)]}
    visited.add((sip,sport))
    while len(q) > 0:
        node = q.pop(0)
        for n in TOPOLOGY[node]:
            if(not n in visited):
                q.append(n)
                visited.add(n)
                ROUTING[n] = ROUTING[node]
        




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-f", "--filename")
    args = parser.parse_args()
    filename = args.filename
    port = int(args.port)
    # sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    # sock.bind((socket.gethostname(), port))
    readtopology(filename,"1.0.0.0",1)
    print(ROUTING)
    print(TOPOLOGY)



            


    
