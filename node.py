# TODO: real error handling

# TODO: fix how ports work

# TODO: Comments(#)
#       Program Titles(##)

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

class Port:
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
        self.ports = {}
        self.ports["LAST"] = None
        self.code = ""
        self.program = ""
        self.labels = {}
        self.pc = 0
        self.program_length = 0
        self.display_lines = []
        self.program_name = None

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


    def print_labels(self):
        for label in self.labels:
            print label, self.labels[label]

    def print_instructions(self):
        for instr in self.program:
            print instr[0].__name__, instr[1:]

    def print_registers(self):
        return "ACC: %d\nBAK: %d" % (self.acc, self.bak)

    def print_program(self):
        for line_num, line in enumerate(self.code.split('\n')):
            if line_num == self.display_lines[self.pc]:
                print ">",
            else:
                print " ",
            print line


    def add_port(self, name, port):
        """Add a port to the Node"""

        self.ports[name] = port


    def resolve_src(self, src):
        """Get the numerical value of a "SRC" argument.
        If the argument is a port, it will take the value."""

        if src in PORTS:
            return self.ports[src].take()
            self.ports["LAST"] = self.ports[src]
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
        if src in PORTS and self.ports[src].peek() is None:
            return 0
        elif dst in PORTS:
            if self.ports[dst].peek() is None:
                self.ports[dst].give(self.resolve_src(src))
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
        self.display_lines = []
        lone_labels = []
        for line_num, raw_line in enumerate(self.code.split('\n')):
            title_pos = raw_line.find("##") #program title
            if title_pos != -1:
                self.program_name = raw_line[title_pos+2:]
                raw_line = raw_line[title_pos]
            comment_pos = raw_line.find('#') #comments
            if comment_pos != -1:
                raw_line = raw_line[:comment_pos]

            line = raw_line.strip().split()
            if line:
                if line[0][-1] == ':': #label
                    if line[1:]: #label with instruction
                        self.labels[line[0][:-1]] = self.program_length
                        for label in lone_labels:
                            self.labels[label] = self.program_length
                        lone_labels = []
                        splitlines.append(line[1:])
                        self.program_length += 1
                        self.display_lines.append(line_num)
                    else: #label without instruction
                        lone_labels.append(line[0][:-1])
                else: #instruction
                    splitlines.append(line)
                    for label in lone_labels:
                        self.labels[label] = self.program_length
                    lone_labels = []
                    self.program_length += 1
                    self.display_lines.append(line_num)

        self.program = []
        for line in splitlines:
            if line:
                if line[0] in self.instructions:
                    args = [arg.rstrip(',') for arg in line[1:]]
                    if not self.check_args(
                        args,
                        self.argument_rules[line[0]]):
                        raise
                    else:
                        self.program.append(
                            (self.instructions[line[0]],)
                            + tuple(args))
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
