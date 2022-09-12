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

import cantools

DEBUG = True

class BMSParameters:
    def __init__(self, sku):
        self.cells_per_string = None
        self.number_of_strings = None
        self.volt_array = None
        self.temp_array = None
        self.soh_array = None
        self.country = None
        self.sku = sku
        self.soc - None
        self.soh = None
        self.j1a_current = None
        get_sku_parameters(sku)

    def get_sku_parameters(self, sku):
        if sku == 18:
            self.number_of_strings = 4
            self.cells_per_string = 12
            self.create_arrays()
        else:
            print("SKU Unknown")

    def create_arrays(self):
        self.volt_array = [[0 for x in range(cells_per_string)] for y in range(number_of_strings)]
        self.soh_array = [[0 for x in range(cells_per_string)] for y in range(number_of_strings)]
        self.temp_array = [[0 for x in range(cells_per_string)] for y in range(number_of_strings)]

    def update_parameters(self, message):
        decoded = db.decode_message(message.arbitration_id, message.data)
        frame_id = message.arbitration_id
        if frame_id == 1830:
            self.country = decoded['country']
        elif frame_id == 1827:
            self.soc = decoded['state_of_charge']

    def update_arrays(self, string, starting_cell, number_of_cells):
        if string == 1:
            pass


class CanDisplay:
    "This is a class to display parsed CAN bus data in a TUI"

    CELL_VOLTAGE_FRAMES = ['1811f580', '1811f581', '1811f582', '1811f583']
    CELL_VOLT_FRAMES = ['740']
    CELL_TEMP_FRAMES = ['741']
    CELL_SOH_FRAMES = ['751']
    STATUS_FRAMES = ['720', '721', '722', '723', '724', '725', '726', '727', '730', '750', '752']
    ERROR_FRAMES = ['183fcce8']

    can0 = can.interface.Bus(channel='vcan0', bustype='socketcan')

    def __init__(self, sku, interface):
        self.bms_param = BMSParameters(sku)
        self.TIMESTAMP = None
        self.layout = Layout()
        self.interface = interface;

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
    db = cantools.database.load_file('data/anzen-raymond-48cell-can1.dbc')
    db.messages
    data = db.get_message_by_name('Status')
    can0 = can.interface.Bus(channel='vcan0', bustype='socketcan')
    while True:
        message = can0.recv()
        try:
            print(message.arbitration_id)
            print(db.decode_message(message.arbitration_id, message.data))
        except:
            print("unknown frame")
    # print(data.signals)
    # db.decode_message(0x750, bytearray([56,00,25]))
    # display = CanDisplay()
    # with Live(display.make_layout(), screen=True) as live:
    #    while True:
    #        display.read_can_messages()
    #        live.update(display.make_layout())
