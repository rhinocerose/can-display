import can
import binascii

from rich import box
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.live import Live
from rich.text import Text

class CanDisplay:
    "This is a class to display parsed CAN bus data in a TUI"

    CELL_VOLTAGE_FRAMES = ['1811f580', '1811f581', '1811f582', '1811f583']
    ERROR_FRAMES = ['183fcce8']

    can0 = can.interface.Bus(channel='can0', bustype='socketcan_native')

    def __init__(self):
        self.SLAVE_CELLS = [[None for i in range(48)], [None for i in range(32)], [None for i in range(28)], [None for i in range(48)]]
        self.layout = Layout()
        
    def add_color(self, string, color):
        text = "[" + color + "]" + str(string) + "[/" + color + "]"
        return text

    def new_line(self, number):
        return "\n" * number
    
    def make_cell_voltage_array(self, data, slave_num):
        index = int(data[:2], 16) - 1
        print("Slave Number: " + str(slave_num))
        print("Cell Index:   " + str(index + 1))
        packets = int((len(data)/4)-1)
        for i in range(packets):
            first = 4*(i+1)
            last = first + 4
            self.SLAVE_CELLS[int(slave_num)][index + i] = data[first:last]

    def make_cell_table(self):
        while self.SLAVE_CELLS[1][-1] == None:
            self.SLAVE_CELLS[1].pop()
        
    def read_can_messages(self):
        msg = self.can0.recv(10.0)
        if msg:
            data = binascii.hexlify(msg.data).decode(encoding='UTF-8', errors='strict')
            frame_id = hex(msg.arbitration_id)
            if frame_id[2:10] in self.CELL_VOLTAGE_FRAMES:
                print("Frame ID: " + str(frame_id))
                self.make_cell_voltage_array(data, frame_id[-1])
                print("SLAVE 1: " + str(self.SLAVE_CELLS))

if __name__ == '__main__':
    display = CanDisplay()
    while True:
        display.read_can_messages()
