import can
import binascii
import time

from datetime import datetime

from rich import box
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.live import Live
from rich.text import Text

DEBUG = False

class CanDisplay:
    "This is a class to display parsed CAN bus data in a TUI"

    CELL_VOLTAGE_FRAMES = ['1811f580', '1811f581', '1811f582', '1811f583']
    ERROR_FRAMES = ['183fcce8']

    can0 = can.interface.Bus(channel='vcan0', bustype='socketcan')

    def __init__(self):
        self.NUMBER_OF_BATTERIES = self.get_number_batteries()
        self.SLAVE_CELLS = [[0.0 for i in range(48)],
                [0.0 for i in range((self.NUMBER_OF_BATTERIES - 31) * 4)],
                [0.0 for i in range(28)],
                [0.0 for i in range(48)]]
        self.SLAVE1_LENGTH = len(self.SLAVE_CELLS[0])/4
        self.SLAVE2_LENGTH = len(self.SLAVE_CELLS[1])/4
        self.SLAVE3_LENGTH = len(self.SLAVE_CELLS[2])/4
        self.SLAVE4_LENGTH = len(self.SLAVE_CELLS[3])/4
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
        while self.check_sparsity():
            self.read_can_messages()

    def send_request(self, arbitration_id, data):
        send_params = can.Message(
            arbitration_id=arbitration_id, data=data, is_extended_id=True)
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

    def make_timestamp(self):
        self.TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def make_header(self):
        header = self.add_color("LAST UPDATED:  ", "red") + self.add_color(self.TIMESTAMP, "blue")
        return Panel(header, style = Style(color="red", bold=True))

    def make_cell_voltage_array(self, data, slave_num):
        self.read_can_messages()
        index = int(data[:2], 16) - 1
        if DEBUG:
            print("Slave Number: " + str(slave_num))
            print("Cell Index:   " + str(index + 1))
        packets = int((len(data)/4)-1)
        for i in range(packets):
            first = 4*(i+1)
            last = first + 4
            temp_val = float(int(data[first:last], 16)) / 1000.0
            self.SLAVE_CELLS[int(slave_num)][index + i] = self.color_cell_voltages(temp_val)
        self.make_cell_voltage_table()

    def color_cell_voltages(self, value):
        if 3.75 > float(value) > 3.5:
            color = "dim red"
        elif float(value) > 3.75:
            color = "red"
        elif float(value) < 1.5:
            color = "blue"
        else:
            color = "white"
        return self.add_color(str("%.3f" % round(value, 3)), color)

    def check_sparsity(self):
        sparse = False
        for i in range(len(self.SLAVE_CELLS)):
            for j in range(len(self.SLAVE_CELLS[i])):
                if DEBUG:
                    print(str(self.SLAVE_CELLS[i][j]))
                if self.SLAVE_CELLS[i][j] == 0.0:
                    sparse = True
                    break
                else:
                    pass
        if DEBUG:
            print(str(sparse))
        return sparse

    def make_cell_voltage_table(self):
        if not self.check_sparsity():
            batt_num2 = "    "
            batt_num3 = "    "
            table = Table(show_header=True,
                    header_style="bold magenta",
                    box=box.ROUNDED)
            table.add_column("BATTERY #", style="bold", min_width=10)
            table.add_column("VOLTAGE", style="bold", min_width=10)
            table.add_column("BATTERY #", style="bold", min_width=10)
            table.add_column("VOLTAGE", style="bold", min_width=10)
            table.add_column("BATTERY #", style="bold", min_width=10)
            table.add_column("VOLTAGE", style="bold", min_width=10)
            table.add_column("BATTERY #", style="bold", min_width=10)
            table.add_column("VOLTAGE", style="bold", min_width=10)
            i = 0
            for j in range(len(self.SLAVE_CELLS[i])):
                battery = int(j / 4) + 1
                cell_value1 = self.SLAVE_CELLS[0][j]
                cell_value4 = self.SLAVE_CELLS[3][j]
                batt_num1 = str(i+1) + '-' + str(battery) + " (" + str(battery) + ")"
                batt_num4 = str(i+4) + '-' + str(battery) + " (" + str(int(battery + self.SLAVE1_LENGTH + self.SLAVE2_LENGTH + self.SLAVE3_LENGTH)) + ")"
                try:
                    cell_value2 = self.SLAVE_CELLS[1][j]
                    batt_num2 = str(i+2) + '-' + str(battery) + " (" + str(int(battery + self.SLAVE1_LENGTH)) + ")"
                except IndexError as error:
                    cell_value2 = "     "
                    batt_num2 = "    "
                try:
                    cell_value3 = self.SLAVE_CELLS[2][j]
                    batt_num3 = str(i+3) + '-' + str(battery) + " (" + str(int(battery + self.SLAVE1_LENGTH + self.SLAVE2_LENGTH)) + ")"
                except IndexError as error:
                    cell_value3 = "     "
                    batt_num3 = "    "
                table.add_row(batt_num1, str(cell_value1),
                              batt_num2, str(cell_value2),
                              batt_num3, str(cell_value3),
                              batt_num4, str(cell_value4),
                              )
            return table

    def read_can_messages(self):
        msg = self.can0.recv(90.0)
        if msg:
            self.make_timestamp()
            data = binascii.hexlify(msg.data).decode(encoding='UTF-8', errors='strict')
            frame_id = hex(msg.arbitration_id)
            if frame_id[2:10] in self.CELL_VOLTAGE_FRAMES:
                self.make_cell_voltage_array(data, frame_id[-1])
                if DEBUG:
                    print(str(self.SLAVE_CELLS))

    def make_layout(self) -> Layout:
        #time = Panel(self.TIMESTAMP, style = Style(color="red", bold=True))
        self.layout.split_column(
            Layout(self.make_header(), name="header", size=3),
            Layout(self.make_cell_voltage_table()),
        )

        return self.layout

if __name__ == '__main__':
    display = CanDisplay()
    with Live(display.make_layout(), screen=True) as live:
       while True:
           display.read_can_messages()
           live.update(display.make_layout())
