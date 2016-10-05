# TODO: real error handling

INT_MIN = -999
INT_MAX = 999

SRC = 0
DST = 1
LABEL = 2

PORTS = ["UP", "DOWN", "LEFT", "RIGHT", "ANY", "LAST"]
REGISTERS = ["ACC", "NIL"]


def clamp(val, low, high):
    """Return val, within [low,high]"""

    if val < low:
        return low
    elif val > high:
        return high
    return val


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

    def printProgram(self):
        print "LABELS"
        for label in self.labels:
            print label, self.labels[label]
        print "\nPROGRAM"
        for instr in self.program:
            print instr[0].__name__, instr[1:]


    def addLink(self, name, link):
        """Add a link to the Node"""

        self.links[name] = link


    def resolveSrc(self, src):
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

    def labelJump(self, label):
        return self.labels[label] - self.pc

    # Command functions all return the change in the PC after running
    def nop(self):
        return add("NIL")

    def mov(self, src, dst):
        if src in PORTS and self.links[src].peek() is None:
            return None
        elif dst in PORTS:
            if self.links[dst].peek() is None:
                self.links[dst].give(self.resolveSrc(src))
            else:
                return None
        elif dst == "ACC":
            self.acc = self.resolveSrc(src)
        return 1

    def swp(self):
        self.acc, self.bak = self.bak, self.acc
        return 1

    def sav(self):
        self.bak = self.acc
        return 1

    def add(self, src):
        val = self.resolveSrc(src)
        if val is None:
            return 0
        else:
            self.acc = clamp(self.acc + val, INT_MIN, INT_MAX)
            return 1

    def sub(self, src):
        val = self.resolveSrc(src)
        if val is None:
            return 0
        else:
            self.acc = clamp(self.acc - val, INT_MIN, INT_MAX)
            return 1

    def neg(self):
        self.acc = -self.acc
        return 1

    def jmp(self, label):
        return self.labelJump(label)

    def jez(self, label):
        return self.labelJump(label) if self.acc == 0 else 1

    def jnz(self, label):
        return self.labelJump(label) if self.acc != 0 else 1

    def jgz(self, label):
        return self.labelJump(label) if self.acc > 0 else 1

    def jlz(self, label):
        return self.labelJump(label) if self.acc < 0 else 1

    def jro(self, src):
        val = self.resolveSrc(src)
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
                    if not self.checkArgument(
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



    def checkArgument(self, args, rules):
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
        print self.pc
        instr = self.program[self.pc]
        print instr[0].__name__, instr[1:]
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

# TODO: read network configurations from a file
nodes = [[Node() for _ in xrange(node_row_size)]
         for _ in xrange(node_column_size)]
links = [[Link() for _ in xrange(node_row_size + row%2)]
         for row in xrange(node_column_size*2 + 1)]

for ny in xrange(node_column_size):
    for nx in xrange(node_row_size):
        nodes[ny][nx].addLink("UP", links[ny*2][nx])
        nodes[ny][nx].addLink("DOWN", links[(ny+1)*2][nx])
        nodes[ny][nx].addLink("LEFT", links[(ny*2)+1][nx])
        nodes[ny][nx].addLink("RIGHT", links[(ny*2)+1][nx+1])


# Simple Test Program

nodes[0][0].code = """INIT: SUB ACC
ST: ADD UP
JEZ END
SAV
JMP ST

END:
MOV ACC DOWN
"""

nodes[0][0].assemble()
nodes[0][0].printProgram()


in_queue = [1, 0, -1]
while 1:
    raw_input()
    if in_queue and links[0][0].peek() is None:
        links[0][0].give(in_queue.pop(0))

    nodes[0][0].step()

    print in_queue
    print links[0][0]
    print nodes[0][0]
