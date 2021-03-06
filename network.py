# TODO: multiple inputs/outputs

# TODO: Saving!

# TODO: fix ports here too!
import curses

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

    def init_windows(self):
        # TODO: ~magic numbers~
        self.node_wins = [[curses.newwin(18, 28, (y*20)+3, (x*33)+6)
                           for x in xrange(self.width)]
                          for y in xrange(self.height)]
        self.port_wins = []
        for row in xrange(self.height*2 + 1):
            winrow = []
            if row % 2: # horizontal
                for col in xrange(self.width + 1):
                    winrow.append(curses.newwin(5, 4, ((row-1)*10)+9, col*33))
            else: # vertical
                for col in xrange(self.width):
                    winrow.append(curses.newwin(3, 11, row*10, (col*33)+13))
            self.port_wins.append(winrow)

    def draw_static(self):
        for y in xrange(self.height):
            for x in xrange(self.width):
                self.nodes[y][x].print_static_nc(self.node_wins[y][x])
        for y in xrange(len(self.ports)):
            for x in xrange(len(self.ports[y])):
                self.ports[y][x].print_static_nc(self.port_wins[y][x], y%2)

    def print_nc(self):
        for y in xrange(self.height):
            for x in xrange(self.width):
                self.nodes[y][x].print_nc(self.node_wins[y][x])
        for y in xrange(len(self.ports)):
            for x in xrange(len(self.ports[y])):
                pass
                self.ports[y][x].print_nc(self.port_wins[y][x], y%2)


    def step(self):
        if self.input_data and self.in_port.peek() is None:
            self.in_port.give(self.input_data.pop(0))
        if not(self.out_port.peek() is None):
            self.output_data.append(self.out_port.take())

        for y in xrange(self.height):
            for x in xrange(self.width):
                self.nodes[y][x].step()
