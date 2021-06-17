import can
import binascii
import time

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
        self.NUMBER_OF_BATTERIES = self.get_number_batteries()
        self.SLAVE_CELLS = [[None for i in range(48)],
                [None for i in range((self.NUMBER_OF_BATTERIES - 31) * 4)],
                [None for i in range(28)],
                [None for i in range(48)]]
        self.SYSTEM_VOLTAGE = None
        self.INVERTER_VOLTAGE = None
        self.PSU_VOLTAGE = None
        self.SYSTEM_CURRENT = None
        self.HALL_CURRENT = None
        self.SHUNT_CURRENT = None
        self.M800_TEMPERATURE = None
        self.R3000_TEMPERATURE = None
        self.DIODE_TEMPERATURE = None
        self.CONTACTOR_TEMPERATURE = None
        self.SYSTEM_STATE = None
        self.SOC = None
        self.SOH = None
        self.CIRCUIT_BREAKER_STATUS = None
        self.CIRCUIT_BREAKER_RELAY = None
        self.CONTACTOR_STATUS = None
        self.FIRMWARE_VERSION = None
        self.INSTANT_POWER = None
        self.CUMULATIVE_ENERGY = None
        self.TIMESTAMP = None
        self.layout = Layout()

    def send_request(self, arbitration_id, data):
        send_params = can.Message(
            arbitration_id=arbitration_id, data=data, extended_id=True)
        self.can0.send(send_params)

    def get_number_batteries(self):
        batteries = 0
        start_time = time.time()
        self.send_request(0x181fe8f4, [0x14, 0, 0, 0, 0, 0, 0, 0])
        while True:
            try:
                if time.time() - start_time > 5:
                    self.send_request(0x181fe8f4, [0x14, 0, 0, 0, 0, 0, 0, 0])
                    startTime = time.time()
                message = self.can0.recv(10.0)
                if message:
                    data = binascii.hexlify(message.data)
                    frame = hex(message.arbitration_id)
                    if frame[2:10] == "1814f4e8" and int(data[0:2], 16) == 1:
                        batteries = int(data[10:12], 16)
                        break
                else:
                    batteries = 4
            except Exception as e:
                print("error is ", str(e))
        return  batteries

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
            self.SLAVE_CELLS[int(slave_num)][index + i] = float(int(data[first:last], 16)) / 1000.0

    def make_cell_voltage_table(self):
        table = Table(show_header=True,
                title="Cell Values",
                header_style="bold magenta",
                box=box.ROUNDED)

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
