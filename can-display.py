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
                header_style="bold magenta",
                box=box.ROUNDED)
        table.add_column("SLAVE 1", style="bold", min_width=20)
        table.add_column("BATTERY #", style="bold", min_width=20)
        table.add_column("VOLTAGE", style="bold", min_width=20)
        table.add_column("SLAVE 2", style="bold", min_width=20)
        table.add_column("BATTERY #", style="bold", min_width=20)
        table.add_column("VOLTAGE", style="bold", min_width=20)
        table.add_column("SLAVE 3", style="bold", min_width=20)
        table.add_column("BATTERY #", style="bold", min_width=20)
        table.add_column("VOLTAGE", style="bold", min_width=20)
        table.add_column("SLAVE 4", style="bold", min_width=20)
        table.add_column("BATTERY #", style="bold", min_width=20)
        table.add_column("VOLTAGE", style="bold", min_width=20)
        i = 0
        for j in range(len(self.SLAVE_CELLS[i])):
            cell_value1 = str(self.SLAVE_CELLS[0][j])
            cell_value4 = str(self.SLAVE_CELLS[3][j])
            try:
                cell_value2 = str(self.SLAVE_CELLS[1][j])
            except IndexError as error:
                cell_value2 = "     "
            try:
                cell_value3 = str(self.SLAVE_CELLS[2][j])
            except IndexError as error:
                cell_value3 = "     "
            table.add_row(str(i+1), str(j+1), cell_value1,
                          str(i+2), str(j+1), cell_value2,
                          str(i+3), str(j+1), cell_value3,
                          str(i+4), str(j+1), cell_value4,
                          )
        return Panel(table)

    def read_can_messages(self):
        msg = self.can0.recv(10.0)
        if msg:
            data = binascii.hexlify(msg.data).decode(encoding='UTF-8', errors='strict')
            frame_id = hex(msg.arbitration_id)
            if frame_id[2:10] in self.CELL_VOLTAGE_FRAMES:
                self.make_cell_voltage_array(data, frame_id[-1])
                self.make_cell_voltage_table()

    def make_layout(self) -> Layout:
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(self.make_cell_voltage_table())
        )

        return self.layout

if __name__ == '__main__':
    display = CanDisplay()
    with Live(display.make_layout(), screen=True) as live:
        while True:
            time.sleep(1)
            live.update(display.make_layout())
    #while True:
        #display.read_can_messages()
