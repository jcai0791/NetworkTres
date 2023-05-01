import argparse 
import socket
import struct
import csv
from collections import defaultdict
import asyncio
from datetime import datetime, timedelta
MAX_BYTES = 6000
TOPOLOGY = defaultdict(lambda : [])
HELLO = {}
ROUTING = defaultdict(lambda : (b'',0))
####### OLD STUFF #########
def getType(packet):
    pass
#wraps inner packet (payload) with outer header
def encapsulateHello(src_ip,src_port):
    packet = struct.pack("!c4sH", 'H', src_ip, src_port)
    return packet
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
def decapsulateHello(packet):
    header = struct.unpack_from("!c4sH",packet)
    return header

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
def sendHello(sip,sport):
    for i in TOPOLOGY[(socket.inet_aton(sip),int(sport))]:
        sendPacket(encapsulateHello(sip,sport),i[0],i[1])


def sendLinkState(seq_no):
    for i in TOPOLOGY[(socket.inet_aton(sip),int(sport))]:
        sendPacket(encapsulateLinkState(sip,sport,seq_no,20,),i[0],i[1])

####### REQUIRED FUNCTIONS ########
def readtopology(filename,sip,sport):
    global HELLO
    with open(filename, "r") as f:
        d = []
        for row in csv.reader(f, delimiter=' '):
            ip,port = row[0].split(",")
            TOPOLOGY[(socket.inet_aton(ip),int(port))] = list(map(lambda x: (socket.inet_aton(x.split(",")[0]), int(x.split(",")[1]) ),  row[1:]))
    buildForwardTable(sip,sport)
    HELLO = { i : datetime.now() for i in TOPOLOGY[(sip,sport)]}

async def sendHello(sip,sport):
    while True:
        sendHello(sip,sport)
        await asyncio.sleep(.5)
async def sendLinkState(sip,sport):
    while True:
        sendLinkState(sip,sport)
        await asyncio.sleep(.75)
async def recvAndCheck(sip,sport):
    while True:
        data, addr = sock.recvfrom(MAX_BYTES)
        t = struct.unpack_from("!c", data, offset=0)

        if(t == 'H'):
            packet = decapsulateHello(data)
            for i in HELLO.keys():
                if(packet[1] == i[0] and packet[2] == i[1]):
                    HELLO[i] = datetime.now()
                if(datime.now()- HELLO[i] > datetime.timedelta(seconds=1)):
                    TOPOLOGY[(sip,sport)] = [j for j in TOPOLOGY[(sip,sport)] if not j == i]
                    buildForwardTable(sip,sport)
        if(t == 'L'):
            header,payload = decapsulateLinkState(data)
            TOPOLOGY[(header[1],header[2])] = payload
            forwardpacket(data, sip,sport)
            buildForwardTable(sip,sport)
        else:
            forwardpacket(data,sip,sport)
        await asyncio.sleep(0)
def createroutes(sip,sport):
    loop = asyncio.get_event_loop()
    task=loop.create_task(recvAndCheck)
    task1 = loop.create_task(sendHello)
    task2= loop.create_task(sendLinkState)
    loop.run_until_complete(asyncio.gather(task,task1))

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
    addr = socket.inet_aton(socket.gethostname())
    # sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    # sock.bind((socket.gethostname(), port))
    readtopology(filename,"1.0.0.0",1)
    print(ROUTING)
    print(TOPOLOGY)



            


    
