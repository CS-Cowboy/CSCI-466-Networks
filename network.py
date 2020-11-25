import queue
import threading
import re

## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)
    
    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)
            
        
## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths 
    dst_S_length = 5
    prot_S_length = 1
    
    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : ]        
        return self(dst, prot_S, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return self.addr
       
    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router
class Router:
    
    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfaces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}
        self.rt_tbl_D = []
        self.neighbors = []
        #DONE: set up the routing table for connected hosts
        for x in self.cost_D.keys(): #x is a string key from cost_D
            self.neighbors.append(x)

        lstTmp = list()
        for x in self.cost_D.keys():
            for k,v in self.cost_D[x].items():
                lstTmp.append(int(v))
            self.rt_tbl_D.append(lstTmp) #add vertical list to the table.
            lstTmp = list()



       # self.rt_tbl_D =    # {destination: {router: cost}}   # dict((f for d in cost_D.keys() , ((x,y) for x in cost[d].keys() for y in cost[d].values()) ) 
        print('%s: Initialized routing table' % self)
        self.print_routes()
    
        
    ## Print routing table
    def print_routes(self):
        #DONE: print the routes as a two dimensional table
        self.print_doubleline()
        self.print_table(self.rt_tbl_D)
        self.print_doubleline()

    def print_doubleline(self):
        print('*=======================================================================================================*')
    def print_singleline(self):
        print('\n*-------------------------------------------------------------------------------------------------------*')

    def print_table(self, data):
        blockSpace = '|   ' #for even spacing
        print(blockSpace, self.name, end='  ')
        for f in self.neighbors: #print the neighbors along the top
            print(blockSpace, f, end='  ')
        print('|',end='')
        self.print_singleline()

        l = len(self.neighbors)

        for x in range(l): #print the table!
            if(self.neighbors[x][0] == 'R'): #If a router (sorta hacky...)
                print(blockSpace, self.neighbors[x], ' ', end='') #print the router at left column
                for y in range(len(data)):
                    print(blockSpace, data[y][0], '  ', end='') #print the cost!               
            else:
                print('')
        print('|')

    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            

    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1
            
            self.intf_L[1].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % \
                (self, p, i, 1))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # DONE: Send out a routing table update
        #create a routing table update packet
        chunks = []
        l = len(self.rt_tbl_D)
        for j in range(l):
                chunks.append(self.neighbors[j])
                chunks.append(self.rt_tbl_D[j][0])
        s = str(chunks)
        #print(s)
        p = NetworkPacket(0, 'control', s)
        try:
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        #TODO: add logic to update the routing tables and
        # possibly send out routing updates
        s = re.sub('[^A-Za-z0-9- ]+', '', p.data_S) #use regex to replace extra non alphanumeric chars + spaces.
        l = s.split() #split based on spaces in to list 'l'
        #print(l)
        #We get a packet p from the neighbors.
        #We update the corresponding NEIGHBOR node costs.
        #DV is neighborly.
        for j in range(len(l)):
            if(j % 2 == 0 and not l[j] in self.neighbors): #If J even and does not exist within our updated list
                self.neighbors.append(l[j]) #add it to the neighbors list
                self.rt_tbl_D.append(list(l[j+1]))

        for k in self.neighbors: #k is a neighbor
            #add the updated value from l to the table.
            if(k in l): #if k is in our updated list
                f = l.index(k) #find its index in l
                g = self.neighbors.index(k)
                self.rt_tbl_D[g][0] = int(self.rt_tbl_D[g][0]) + int(l[f+1])

        #self.print_routes()
        
        if(self.name == "RA"):
            i = 0
            self.send_routes(i)
        elif(self.name == "RB"):
            i = 1
            self.send_routes(i)
        else:
            i = 0
        print('%s: Received routing update %s from interface %d' % (self, p, i))
        #MUST SEND BELMAN FORD UPDATE OUT TO DESTINATION


                

                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 