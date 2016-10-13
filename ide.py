from curses import wrapper
import time

import network


def main(stdscr):
    program_file = "programs/example-program-1.tis"
    input_data = [1, 0, -1]
    net = network.Network(program_file, input_data)
    net.init_windows()
    net.draw_static()

    while 1:
        stdscr.getch()
        net.print_nc()
        net.step()


if __name__ == "__main__":
    wrapper(main)