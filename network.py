# TODO: multiple inputs/outputs

# TODO: fix ports here too!

import node

def read_file(filename):
    prg_file = open(filename)

    net_height, net_width = map(int, prg_file.readline().strip().split(','))
    in_port = map(int, prg_file.readline().strip().split(','))
    out_port = map(int, prg_file.readline().strip().split(','))
    nodes = [[node.Node() for _ in xrange(net_width)]
             for _ in xrange(net_height)]
    ports = [[node.Port() for _ in xrange(net_width + row%2)]
             for row in xrange(net_height*2 + 1)]
    for ny in xrange(net_height):
        for nx in xrange(net_width):
            nodes[ny][nx].add_port("UP", ports[ny*2][nx])
            nodes[ny][nx].add_port("DOWN", ports[(ny+1)*2][nx])
            nodes[ny][nx].add_port("LEFT", ports[(ny*2)+1][nx])
            nodes[ny][nx].add_port("RIGHT", ports[(ny*2)+1][nx+1])

    node_header = prg_file.readline()
    while node_header:
        node_y, node_x = map(int, node_header.strip().split(','))
        code = ""
        code_line = prg_file.readline()
        while code_line.strip() != '~':
            code += code_line
            code_line = prg_file.readline()
        nodes[node_y][node_x].code = code
        node_header = prg_file.readline()
    prg_file.close()

    for y in xrange(net_height):
        for x in xrange(net_width):
            nodes[y][x].assemble()

    return {
        "height": net_height,
        "width": net_width,
        "in_port": ports[in_port[0]][in_port[1]],
        "out_port": ports[out_port[0]][out_port[1]],
        "nodes": nodes,
        "ports": ports
    }


class Network:
    def __init__(self, filename, input_data=[]):
        net_dat = read_file(filename)
        self.height = net_dat["height"]
        self.width = net_dat["width"]
        self.in_port = net_dat["in_port"]
        self.out_port = net_dat["out_port"]
        self.nodes = net_dat["nodes"]
        self.ports = net_dat["ports"]

        self.input_data = input_data
        self.output_data = []

    def step(self):
        if self.input_data and self.in_port.peek() is None:
            self.in_port.give(self.input_data.pop(0))
        if not(self.out_port.peek() is None):
            self.output_data.append(self.out_port.take())

        for y in xrange(self.height):
            for x in xrange(self.width):
                self.nodes[y][x].step()

    def print_state(self):
        print '-' * 16
        self.nodes[0][0].print_registers()
        self.nodes[0][0].print_program()
        print "\nINPUT:", self.input_data
        print "OUTPUT:", self.output_data
        print




program_file = "programs/example-program-1.tis"
input_data = [1, 0, -1]
net = Network(program_file, input_data)

net.print_state()
while 1:
    raw_input()
    net.step()
    net.print_state()
