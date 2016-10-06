# TODO: real error handling

# TODO: fix how ports work, each port is actually 2 ports
#       currently commands like "MOV UP UP" will not work

# TODO: Optional commas in instructions

INT_MIN = -999
INT_MAX = 999

SRC = 0
DST = 1
LABEL = 2

REG_PORTS = ["UP", "DOWN", "LEFT", "RIGHT"]
PORTS = REG_PORTS + ["ANY", "LAST"]
REGISTERS = ["ACC", "NIL"]


def clamp(val, low, high):
    """Return val, within [low,high]"""

    if val < low:
        return low
    elif val > high:
        return high
    return val


def readFile(filename):
    prg_file = open(filename)
    
    net_height, net_width = map(int, prg_file.readline().strip().split(','))
    in_port = map(int, prg_file.readline().strip().split(','))
    out_port = map(int, prg_file.readline().strip().split(','))
    nodes = [[Node() for _ in xrange(net_width)]
             for _ in xrange(net_height)]
    links = [[Link() for _ in xrange(net_width + row%2)]
             for row in xrange(net_height*2 + 1)]
    for ny in xrange(net_height):
        for nx in xrange(net_width):
            nodes[ny][nx].add_link("UP", links[ny*2][nx])
            nodes[ny][nx].add_link("DOWN", links[(ny+1)*2][nx])
            nodes[ny][nx].add_link("LEFT", links[(ny*2)+1][nx])
            nodes[ny][nx].add_link("RIGHT", links[(ny*2)+1][nx+1])

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
           links[in_port[0]][in_port[1]], links[out_port[0]][out_port[1]], \
           nodes, links


class Link:
    def __init__(self):
        self.val = None

    def __str__(self):
        return "Val: %s" % ("?" if self.val is None else str(self.val))

    def peek(self):
        return self.val

    def take(self):
        ret = self.val
        self.val = None
        return ret

    def give(self, val):
        if self.val != None:
            raise
        self.val = val

class Node:
    def __init__(self):
        self.acc = 0
        self.bak = 0
        self.links = {}
        self.links["LAST"] = None
        self.code = ""
        self.program = ""
        self.labels = {}
        self.pc = 0
        self.program_length = 0

        self.instructions = {
            "NOP": self.nop,
            "MOV": self.mov,
            "SWP": self.swp,
            "SAV": self.sav,
            "ADD": self.add,
            "SUB": self.sub,
            "NEG": self.neg,
            "JMP": self.jmp,
            "JEZ": self.jez,
            "JNZ": self.jnz,
            "JGZ": self.jgz,
            "JLZ": self.jlz,
            "JRO": self.jro
        }

        self.argument_rules = {
            "NOP": (),
            "MOV": (SRC, DST),
            "SWP": (),
            "SAV": (),
            "ADD": (SRC,),
            "SUB": (SRC,),
            "NEG": (),
            "JMP": (LABEL,),
            "JEZ": (LABEL,),
            "JNZ": (LABEL,),
            "JGZ": (LABEL,),
            "JLZ": (LABEL,),
            "JRO": (SRC,)
        }

    def __str__(self):
        return "PC: %d\nACC: %d\nBAK: %d" % (self.pc, self.acc, self.bak)

    def print_program(self):
        print "LABELS"
        for label in self.labels:
            print label, self.labels[label]
        print "\nPROGRAM"
        for instr in self.program:
            print instr[0].__name__, instr[1:]


    def add_link(self, name, link):
        """Add a link to the Node"""

        self.links[name] = link


    def resolve_src(self, src):
        """Get the numerical value of a "SRC" argument.
        If the argument is a port, it will take the value."""

        # TODO: There's probably some BS with "ANY":
        #         need to figure out which link gets taken from first
        #         in the event of a tie
        if src in PORTS:
            return self.links[src].take()
            self.links["LAST"] = self.links[src]
        elif src == "ACC":
            return self.acc
        elif src == "NIL":
            return 0
        else:
            return src

    def label_jump(self, label):
        return self.labels[label] - self.pc

    # Command functions all return the change in the PC after running
    def nop(self):
        return add("NIL")

    def mov(self, src, dst):
        if src in PORTS and self.links[src].peek() is None:
            return 0
        elif dst in PORTS:
            if self.links[dst].peek() is None:
                self.links[dst].give(self.resolve_src(src))
            else:
                return 0
        elif dst == "ACC":
            self.acc = self.resolve_src(src)
        return 1

    def swp(self):
        self.acc, self.bak = self.bak, self.acc
        return 1

    def sav(self):
        self.bak = self.acc
        return 1

    def add(self, src):
        val = self.resolve_src(src)
        if val is None:
            return 0
        else:
            self.acc = clamp(self.acc + val, INT_MIN, INT_MAX)
            return 1

    def sub(self, src):
        val = self.resolve_src(src)
        if val is None:
            return 0
        else:
            self.acc = clamp(self.acc - val, INT_MIN, INT_MAX)
            return 1

    def neg(self):
        self.acc = -self.acc
        return 1

    def jmp(self, label):
        return self.label_jump(label)

    def jez(self, label):
        return self.label_jump(label) if self.acc == 0 else 1

    def jnz(self, label):
        return self.label_jump(label) if self.acc != 0 else 1

    def jgz(self, label):
        return self.label_jump(label) if self.acc > 0 else 1

    def jlz(self, label):
        return self.label_jump(label) if self.acc < 0 else 1

    def jro(self, src):
        val = self.resolve_src(src)
        return 0 if val is None else val


    def assemble(self):
        """Doesn't actually "assemble" just sets self.program to a
        list of (function, arg1, ..., argn)
        Also checks the validity of the args"""

        splitlines = []
        self.labels = {}
        self.program_length = 0
        lone_labels = []
        for rawline in self.code.split('\n'):
            line = rawline.strip().split()
            if line:
                if line[0][-1] == ':': #label
                    if line[1:]: #label with instruction
                        self.labels[line[0][:-1]] = self.program_length
                        for label in lone_labels:
                            self.labels[label] = self.program_length
                        lone_labels = []
                        splitlines.append(line[1:])
                        self.program_length += 1
                    else: #label without instruction
                        lone_labels.append(line[0][:-1])
                else:
                    splitlines.append(line)
                    for label in lone_labels:
                        self.labels[label] = self.program_length
                    lone_labels = []
                    self.program_length += 1

        self.program = []
        for line in splitlines:
            if line:
                if line[0] in self.instructions:
                    if not self.check_args(
                        line[1:],
                        self.argument_rules[line[0]]):
                        raise
                    else:
                        self.program.append(
                            (self.instructions[line[0]],)
                            + tuple(line[1:]))
                else:
                    raise
            else:
                raise #label finding is supposed to strip blank lines



    def check_args(self, args, rules):
        """Check that a list of arguments "args", fits the rules
        described by the "rules" array"""

        if len(args) != len(rules):
            return False
        for argnum in xrange(len(args)):
            if rules[argnum] == SRC:
                if ((args[argnum] not in PORTS) and
                    (args[argnum] not in REGISTERS) and
                    (not args[argnum].isdigit()) and
                    (not (args[0] == '-' and args[argnum][1:].isdigit()))):
                   print "wrong SRC"
                   return False

            elif rules[argnum] == DST:
                if ((args[argnum] not in PORTS) and
                    (args[argnum] not in REGISTERS)):
                   print "wrong DST"
                   return False

            elif rules[argnum] == LABEL:
                if args[argnum] not in self.labels:
                    print "wrong label"
                    return False

            else:
                raise
                return False
        return True

    def step(self):
        if self.program:
            instr = self.program[self.pc]
            self.pc = (self.pc + instr[0](*instr[1:])) % self.program_length


node_row_size = 4
node_column_size = 3


"""
An example network:
o  : Node
|  : vertical link
-- : Horizontal link

   |  |  |
 --o--o--o--
   |  |  |
 --o--o--o--
   |  |  |
"""


net_height, net_width, in_port, out_port, nodes, links = readFile("programs/example-program-1.tis")


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
            print y, x
            nodes[y][x].step()

    print in_queue
    print out_queue
    print
