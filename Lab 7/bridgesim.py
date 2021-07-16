import locale
class Bridge:
    def __init__(self, trace, i, root_port_id = 0, adjacent_ports = {}, received_bpdu = {}, forwarding_table = []):
        self.trace = trace
        self.root_id = i
        self.i = i
        self.best_received_bpdu = self.BPDU(root_id = i,root_path_cost = -1,bridge_id = float('inf'), port_id = 0)
        self.data = self.Data()
        self.root_path_cost = 0
        self.root_port_id = root_port_id
        self.adjacent_ports = set(adjacent_ports)
        self.received_bpdu = set(received_bpdu)
        self.forwarding_table = forwarding_table
        self.bpdu = self.BPDU()

    class BPDU:
        def __init__(self, root_id = float('inf'), root_path_cost = float('inf'), bridge_id = float('inf'), port_id = locale.CHAR_MAX):
            self.root_id = root_id
            self.root_path_cost = root_path_cost
            self.bridge_id = bridge_id
            self.port_id = port_id
        def __lt__(self, other):
            if self.root_id != other.root_id:
                return self.root_id < other.root_id
            elif self.root_path_cost != other.root_path_cost:
                return self.root_path_cost < other.root_path_cost
            elif self.bridge_id != other.bridge_id:
                return self.bridge_id < other.bridge_id
            elif self.port_id != other.port_id:
                return self.port_id < other.port_id
            else:
                return False
    class Port:
        def __init__(self, port_id, best_received_bpdu):
            self.port_id = port_id
            self.best_received_bpdu = best_received_bpdu
        def __lt__(self, other):
            if self.port_id != other.port_id:
                return self.port_id < other.port_id
            else:
                return self.best_received_bpdu < other.best_received_bpdu
    class Data:
        def __init__(self, time = -1, host1_id = 0, host2_id = 0, port_id = '0'):
            self.time = time
            self.host1_id = host1_id
            self.host2_id = host2_id
            self.port_id = port_id
        def __lt__(self, other):
            if self.time != other.time:
                return self.time < other.time
            elif self.port_id != other.port_id:
                return self.port_id < other.port_id
            elif self.host1_id != other.host1_id:
                return self.host1_id < other.host1_id
            elif self.host2_id != other.host2_id:
                return self.host2_id < other.host2_id
            else:
                return False
    def UpdateStatus(self, bpdu):
        self.best_received_bpdu = bpdu
        self.root_id = bpdu.root_id
        self.root_path_cost = bpdu.root_path_cost + 1
        self.root_port_id = bpdu.port_id
    def GetBPDU(self, port_id):
        bpdu1 = self.BPDU()
        bpdu1.root_id = self.root_id
        bpdu1.root_path_cost = self.root_path_cost
        bpdu1.bridge_id = self.i
        bpdu1.port_id = port_id
        return bpdu1
    def GetPort(self, port_id):
        for port in self.adjacent_ports:
            if port.port_id == port_id:
                return port
        return False
    def GetDesignatedPorts(self):
        designated_ports = set({})
        for port in self.adjacent_ports:
            w = self.GetBPDU(port.port_id)
            if w < port.best_received_bpdu:
                designated_ports.add(port.port_id)
        return designated_ports
    def GetForwardingPorts(self):
        forwarding_ports = self.GetDesignatedPorts()
        if self.root_id != self.i:
            forwarding_ports.add(self.root_port_id)
        return forwarding_ports
    def UpdateOnReceivedBPDU(self, time):
        templ = sorted(self.received_bpdu)
        for bpdu_message in templ:
            if bpdu_message[0] == time:
                bpdu = bpdu_message[1];
                portg = self.GetPort(bpdu.port_id)
                if bpdu < portg.best_received_bpdu:
                    self.adjacent_ports.remove(portg)
                    y = self.Port(bpdu.port_id,bpdu)
                    self.adjacent_ports.add(y)
                if bpdu < self.best_received_bpdu:
                    self.UpdateStatus(bpdu)
                    self.received_bpdu.remove(bpdu_message)
                if self.trace == 1:
                    print(str(time)+" B"+str(self.i)+" r (B"+str(bpdu.root_id)+", "+str(bpdu.root_path_cost)+", B"+str(bpdu.bridge_id)+")")
           
    def  GenerateBPDU(self,time):
        generated_bpdu = set({})
        atleast_one_insertion = False
        for designated_port_id in self.GetDesignatedPorts():
            x = self.GetBPDU(designated_port_id)
            generated_bpdu.add((time+1, x))
            atleast_one_insertion = True
        if self.trace == 1 and atleast_one_insertion:
            print(str(time)+" B"+str(self.i)+" s (B"+str(self.root_id)+", "+str(self.root_path_cost)+", B"+str(self.i)+")")
        return generated_bpdu
    def GenerateData(self, time):
        generated_data = set({})
        forwarding_ports = set({})
        forwarding_port = self.forwarding_table[self.data.host2_id]
        if forwarding_port != 0:
            forwarding_ports.add(forwarding_port)
        else:
            forwarding_ports = self.GetForwardingPorts()
        for port_id in forwarding_ports:
            if port_id != self.data.port_id:
                hello = self.Data()
                hello.time = time+1
                hello.host1_id = self.data.host1_id
                hello.host2_id = self.data.host2_id
                hello.port_id = port_id
                generated_data.add(hello)
                if self.trace == 1:
                    print(str(time)+" B"+str(self.i)+" s "+str(self.data.port_id)+" --> "+str(port_id))
        return generated_data
        


def SpanningTreeProtocol():
    global network_graph
    global lan_to_bridges
    num_of_bridges = len(network_graph) - 1
    time = 0
    while time < 100:
        for bridge_num in range(1,num_of_bridges+1):
            network_graph[bridge_num].UpdateOnReceivedBPDU(time);

        for bridge_num in range(1,num_of_bridges+1):
            generated_messages = network_graph[bridge_num].GenerateBPDU(time)               
            for siterator in generated_messages:
                bpdu = siterator[1]
                for receiver_bridge_num in range(len(lan_to_bridges[bpdu.port_id])):
                    if lan_to_bridges[bpdu.port_id][receiver_bridge_num] != bridge_num:
                        network_graph[lan_to_bridges[bpdu.port_id][receiver_bridge_num]].received_bpdu.add(siterator)
        time+=1
    for bridge_num in range(1,num_of_bridges+1):
            bridge = network_graph[bridge_num]
            designated_ports = bridge.GetDesignatedPorts()
            print('B'+str(bridge.i)+":",end=" ")
            for port in sorted(bridge.adjacent_ports):
                if port.port_id in designated_ports:
                    port_status = "DP"
                elif port.port_id == bridge.root_port_id:
                    port_status = "RP"
                else:
                    port_status = "NP"
                print(str(port.port_id)+'-'+port_status,end=" ")
            print('\n',end="")

def LearningBridges():
    global network_graph
    global host_to_lan
    global data_transfers
    num_of_bridges = len(network_graph) - 1
    num_of_hosts = len(host_to_lan) - 1
    global_time = 0
    lan_to_bridges = {}

    for bridge in network_graph:
        bridge.forwarding_table = [0 for item in range(num_of_hosts+1)]
        forwarding_ports = bridge.GetForwardingPorts()
        for port in forwarding_ports:
            if port in lan_to_bridges:
                lan_to_bridges[port].add(bridge.i)
            else:
                lan_to_bridges[port] = {bridge.i}

    for data_transfer in data_transfers:
        global_time += 100
        host1_id = data_transfer[0]
        host2_id = data_transfer[1]
        host1_lan = host_to_lan[host1_id]
        host2_lan = host_to_lan[host2_id]
        time = global_time

        for bridge_id in sorted(lan_to_bridges[host1_lan]):
            network_graph[bridge_id].data.time = time + 1
            network_graph[bridge_id].data.host1_id = host1_id
            network_graph[bridge_id].data.host2_id = host2_id
            network_graph[bridge_id].data.port_id = host1_lan

        time += 1
        while time - global_time < 100:
            for bridge in network_graph:
                if time == bridge.data.time:
                    if bridge.forwarding_table[bridge.data.host1_id] == 0:
                        solver = bridge.data.port_id
                        designated_ports = bridge.GetDesignatedPorts()
                        if solver in designated_ports or solver == bridge.root_port_id: 
                            bridge.forwarding_table[bridge.data.host1_id] = bridge.data.port_id
                            if bridge.trace == 1:
                                print(str(time)+" B"+str(bridge.i)+" r "+str(bridge.data.port_id)+" --> -")
            for bridge_num in range(1,num_of_bridges+1):
                if network_graph[bridge_num].data.time == time:
                    generated_data = network_graph[bridge_num].GenerateData(time)
                    for data in generated_data:
                        for receiver_bridge_num in lan_to_bridges[data.port_id]:
                            if receiver_bridge_num != bridge_num:
                                network_graph[receiver_bridge_num].data = data
            time += 1

        for bridge_num in range(1,num_of_bridges+1):
            bridge = network_graph[bridge_num]
            print("B"+str(bridge.i)+":")
            print("HOST ID | FORWARDING PORT")
            for host_id in range(len(bridge.forwarding_table)):
                if bridge.forwarding_table[host_id] != 0:
                    print("H"+str(host_id)+" | "+str(bridge.forwarding_table[host_id]))
        print('\n',end="")

def ReadNetworkGraph(num_of_bridges, trace):
    global network_graph
    global lan_to_bridges
    bridge = Bridge(trace = trace, i = 0)
    network_graph = [bridge]

    for bridge_num in range(1,num_of_bridges+1):
        bridge = Bridge(trace = trace, i = bridge_num)
        network_graph.append(bridge)

    for read_bridge_count in range(1,num_of_bridges+1):
        words = list(input().split())
        num = int(words[0][1:-1])
        for i in range(1,len(words)):
            bridge = network_graph[num]
            bpdu = bridge.BPDU()
            bpdu.root_id = float('inf')
            bpdu.root_path_cost = float('inf')
            bpdu.bridge_id = float('inf')
            bpdu.port_id = locale.CHAR_MAX
            z = bridge.Port(words[i], bpdu)
            bridge.adjacent_ports.add(z)
            # for ports in network_graph[num].adjacent_ports:
            #     print("hi", num, ports.best_received_bpdu.root_id)
            if words[i] in lan_to_bridges:
                lan_to_bridges[words[i]].append(num)
            else:
                lan_to_bridges[words[i]] = [num]

    for lan in lan_to_bridges:
        lan_to_bridges[lan].sort()

def ReadHostToLan(num_of_lans):
    global host_to_lan
    for read_lan_count in range(num_of_lans):
        words = list(input().split())
        lan = words[0][0]
        for i in range(1,len(words)):
            host_id = int(words[i][1:])
            if host_id >= len(host_to_lan):
                host_to_lan = host_to_lan + ['Z' for item in range(host_id - len(host_to_lan) + 1)]
            host_to_lan[host_id] = lan

def ReadDataTransfers(num_of_data_transfers):
    global data_transfers
    for i in range(num_of_data_transfers):
        hosts = list(input().split())
        host1_value = int(hosts[0][1:])
        host2_value = int(hosts[1][1:])
        data_transfers.append((host1_value, host2_value))

trace = int(input())
num_of_bridges = int(input())
network_graph = []
lan_to_bridges = {}
ReadNetworkGraph(num_of_bridges, trace)
num_of_lans = len(lan_to_bridges)
SpanningTreeProtocol()
host_to_lan = []
ReadHostToLan(num_of_lans)
num_of_hosts = len(host_to_lan) - 1
num_of_data_transfers = int(input())
data_transfers = []
ReadDataTransfers(num_of_data_transfers)
LearningBridges()