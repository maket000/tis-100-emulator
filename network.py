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

    return net_height, net_width, \
           ports[in_port[0]][in_port[1]], ports[out_port[0]][out_port[1]], \
           nodes, ports


net_height, net_width, in_port, out_port, nodes, ports = read_file("programs/example-program-1.tis")


in_queue = [1, 0, -1]
out_queue = []

print in_queue
print out_queue
print
while 1:
    raw_input()
    if in_queue and in_port.peek() is None:
        in_port.give(in_queue.pop(0))
    if not (out_port.peek() is None):
        out_queue.append(out_port.take())

    for y in xrange(net_height):
        for x in xrange(net_width):
            nodes[y][x].step()

    print in_queue
    print out_queue
    print
