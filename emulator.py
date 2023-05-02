import argparse 
import socket
import struct
import csv
from collections import defaultdict
import asyncio
import errno
import copy
from datetime import datetime, timedelta
MAX_BYTES = 6000
TOPOLOGY = defaultdict(lambda : [])
HELLO = {}
ROUTING = defaultdict(lambda : (b'',0))
SEQ_NO = defaultdict(lambda : 0)
####### OLD STUFF #########
def printInfo(sip,sport):
    print(f"ROUTING FOR NODE ({sip},{sport})")
    for key,value in ROUTING.items():
        print(key, f"nextHop: {value}")
    print(f"TOPOLOGY FOR NODE ({sip},{sport})")
    for key,value in TOPOLOGY.items():
        print(key, f"Adjacent Nodes {value}")
#wraps inner packet (payload) with outer header
def encapsulateHello(src_ip,src_port):
    packet = struct.pack("!c4sH", b'H', src_ip, src_port)
    return packet
def encapsulateLinkState(src_ip, src_port,seq_no,ttl,payload):
    packet = struct.pack("!c4sHIII" +("8s"*len(payload)),b'L', src_ip,src_port,seq_no,len(payload), ttl , *[i[0] + i[1].to_bytes(4,'big') for i in payload])
    return packet

#returns outer header and inner packet separately
def decapsulateLinkState(packet):
    header = struct.unpack_from("!c4sHIII",packet)
    convert = lambda x: (x[:4], int.from_bytes(x[4:], "big"))
    length = header[4]
    payload = [convert(struct.unpack_from(f"!8s",packet,offset=19+(8*i))[0])  for i in range(length)]

    return header,payload
def decapsulateHello(packet):
    header = struct.unpack_from("!c4sH",packet)
    return header

def encapsulateRouteTrace(TTL, src_ip, src_port, dest_ip, dest_port):
    packet = struct.pack(f"!cI4sH4sH",b'T',TTL,src_ip,src_port,dest_ip,dest_port)
    return packet

#returns outer header and inner packet separately
def decapsulateRouteTrace(packet):
    header = struct.unpack_from(f"!BI4sH4sH",packet)
                  #0   1    2        3        4       5
    return header #T, TTL, srcIP, srcPort, destIP, destPort

#Sends packet to (ip,port)
def sendPacket(packet, ip, port,sock):
    sock.sendto(packet,(ip,port))

######## HELPERS #######

   




####### REQUIRED FUNCTIONS ########
def readtopology(filename,sip,sport):
    global HELLO, TOPOLOGY
    with open(filename, "r") as f:
        d = []
        for row in csv.reader(f, delimiter=' '):
            ip,port = row[0].split(",")
            TOPOLOGY[(socket.inet_aton(ip),int(port))] = list(map(lambda x: (socket.inet_aton(x.split(",")[0]), int(x.split(",")[1]) ),  row[1:]))
    buildForwardTable(sip,sport)
    HELLO = { i : datetime.now() for i in TOPOLOGY[(sip,sport)]}

async def sendHello(sip,sport,sock):
    while True:
        for i in TOPOLOGY[(sip,int(sport))]:
            sendPacket(encapsulateHello(sip,sport),socket.inet_ntoa(i[0]),i[1],sock)  
        await asyncio.sleep(.5)
async def sendLinkState(sip,sport,sock):
    global SEQ_NO
    while True:
        for i in TOPOLOGY[(sip,int(sport))]:
            SEQ_NO[(sip,sport)]+=1
            sendPacket(encapsulateLinkState(sip,sport,SEQ_NO[(sip,sport)],25,TOPOLOGY[(sip, sport)]),socket.inet_ntoa(i[0]),i[1],sock)
        await asyncio.sleep(.75)
async def recvAndCheck(sip,sport,sock):
    global SEQ_NO, HELLO, TOPOLOGY
    while True:
        data = None
        try:
            data, addr = sock.recvfrom(MAX_BYTES)
        except socket.error as e:
            err = e.args[0] 
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                pass
            else:
                # a "real" error occurred
                print(e)

        if(data):
            t = struct.unpack_from("!c", data, offset=0)
            if(t[0] == b'H'):
                packet = decapsulateHello(data)
                if(not (packet[1], packet[2]) in HELLO):
                    HELLO[(packet[1],packet[2])] = datetime.now()
                    TOPOLOGY[(sip,sport)] = TOPOLOGY[(sip,sport)]  + [(packet[1], packet[2])]
                    buildForwardTable(sip,sport)
                    SEQ_NO[(sip,sport)] += 1
                    for j in TOPOLOGY[(sip,sport)]:
                        sendPacket(encapsulateLinkState(sip,sport,SEQ_NO[(sip,sport)],25,TOPOLOGY[(sip, sport)]),socket.inet_ntoa(j[0]),j[1],sock)
                for i in HELLO.keys():
                    if(packet[1] == i[0] and packet[2] == i[1]):
                        HELLO[i] = datetime.now()
            elif(t[0] == b'L'):
                header,payload = decapsulateLinkState(data)
                if(header[3] > SEQ_NO[(header[1], header[2])] and not payload == TOPOLOGY[(header[1],int(header[2]))]):
                    SEQ_NO[(header[1],header[2])] = header[3]
                    TOPOLOGY[(header[1],header[2])] = payload
                    forwardpacket(data, sip,sport,sock)
                    buildForwardTable(sip,sport)
            else:
                forwardpacket(data,sip,sport,sock)
        expired = []
        for i in HELLO.keys():

            if(abs(datetime.now()- HELLO[i]) > timedelta(milliseconds=600)):
                TOPOLOGY[(sip,sport)] = [j for j in TOPOLOGY[(sip,sport)] if not j == i]
                expired.append(i)
                buildForwardTable(sip,sport)
                SEQ_NO[(sip,sport)] += 1
                for j in TOPOLOGY[(sip,sport)]:
                    sendPacket(encapsulateLinkState(sip,sport, SEQ_NO[(sip,sport)],25,TOPOLOGY[(sip, sport)]),socket.inet_ntoa(j[0]),j[1],sock)
        for i in expired:
            HELLO.pop(i)

                
        await asyncio.sleep(0)
async def main(sip,sport,sock):
    task=asyncio.create_task(recvAndCheck(sip,sport,sock))
    task1 = asyncio.create_task(sendHello(sip,sport,sock))
    task2= asyncio.create_task(sendLinkState(sip,sport,sock))
    await task
    await task1
    await task2
def createroutes(sip,sport,sock):
    asyncio.run(main(sip,sport,sock))



def forwardpacket(packet,sip,sport,sock):
    t = struct.unpack_from("!c", packet, offset=0)
    if(t[0] == b'H'):
        pass
    elif(t[0] == b'L'):
        header,payload = decapsulateLinkState(packet)
        if(header[4]==0):
            return
        packet = encapsulateLinkState(header[1],header[2], header[3], header[4]-1, payload)
        for n in TOPOLOGY[(sip,sport)]:
            sendPacket(packet,socket.inet_ntoa(n[0]),n[1],sock)

    else: #Routetrace packet
        header = decapsulateRouteTrace(packet)
        if(header[1]==0):
            newRP = encapsulateRouteTrace(0,sip,sport,header[4],header[5])
            sendPacket(newRP,socket.inet_ntoa(header[2]),header[3],sock)
        else:
            newRP = encapsulateRouteTrace(header[1]-1,header[2],header[3],header[4],header[5])
            if((header[4],header[5]) in ROUTING):
                nextHop = ROUTING[(header[4],header[5])]
                sendPacket(newRP,socket.inet_ntoa(nextHop[0]),nextHop[1],sock)

            else:
                print("next hop not found")

    #header,_ = decapsulateLinkState(packet)

def buildForwardTable(sip, sport):
    global ROUTING
    ROUTING = { i : i for i in TOPOLOGY[(sip,sport)] }
    q = copy.deepcopy(TOPOLOGY[(sip,sport)])
    visited = {i for i in TOPOLOGY[(sip,sport)]}
    visited.add((sip,sport))
    while len(q) > 0:
        node = q.pop(0)
        for n in TOPOLOGY[node]:
            if(not n in visited):
                q.append(n)
                visited.add(n)
                ROUTING[n] = ROUTING[node]
    ROUTING[(sip, sport)] = None
     rintInfo(sip,sport)
        




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port")
    parser.add_argument("-f", "--filename")
    args = parser.parse_args()
    filename = args.filename
    port = int(args.port)
    addr = socket.inet_aton(socket.gethostbyname(socket.gethostname()))
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)

    sock.bind((socket.gethostname(), port))
    sock.setblocking(False)

    readtopology(args.filename,addr,port)
    createroutes(addr,port,sock)

            


    
