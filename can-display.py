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

class Alarms:
    def __init__(self):
        self.contactor_k5_status = None
        self.contactor_k4_status = None
        self.contactor_k7_status = None
        self.bms_supply_voltage_high_alarm_status = None
        self.bms_supply_voltage_low_alarm_status = None
        self.bms_module_temp_high_alarm_status = None
        self.regen_current_high_alarm_status = None
        self.discharge_current_high_alarm_status = None
        self.pack_voltage_high_alarm_status = None
        self.pack_voltage_low_alarm_status = None
        self.cell_voltage_high_alarm_status = None
        self.cell_voltage_low_alarm_status = None
        self.discharge_cell_temp_high_limit = None
        self.discharge_cell_temp_low_limit = None
        self.charge_cell_temp_high_limit = None
        self.charge_cell_temp_low_limit = None
        self.cell_voltage_differential_limit = None
        self.cell_temp_differential_limit = None
        self.soc_high_limit = None
        self.soc_low_limit = None
        self.cell_soc_differential_limit = None
        self.insulation_resistance_limit = None
        self.contactor_k4_position = None
        self.contactor_k5_position = None
        self.contactor_k7_position = None
        self.impending_disconnect = None
        self.slave1_temperature_balance_error = None
        self.slave2_temperature_balance_error = None
        self.slave3_temperature_balance_error = None
        self.slave1_volt_balance_error = None
        self.slave2_volt_balance_error = None
        self.slave3_volt_balance_error = None
        self.cell_volt_acquisition_open_wire = None
        self.bms_internal_can_status = None
        self.power_mode_state = None
        self.isns001_status = None


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
        self.j1b_current = None
        self.k7_current = None
        self.measured_battery_current = None
        self.measured_battery_voltage = None
        self.maximum_regen_current = None
        self.maximum_discharge_current = None
        self.maximum_charge_current = None
        self.maximum_measured_cell_voltage = None
        self.maximum_measured_module_temp = None
        self.minimum_measured_cell_voltage = None
        self.minimum_measured_module_temp = None
        self.connector_v4_voltage = None
        self.volt_average = None
        self.insulation_resistance = None
        self.number_chargers_connected = None
        self.status = Alarms()
        get_sku_parameters(sku)

    def get_sku_parameters(self, sku):
        if sku == 18:
            self.number_of_strings = 4
            self.cells_per_string = 12
            self.create_arrays()
        else:
            print("SKU Unknown")

    def create_arrays(self):
        self.volt_array = [[0.0 for x in range(cells_per_string)] for y in range(number_of_strings)]
        self.soh_array = [[0.0 for x in range(cells_per_string)] for y in range(number_of_strings)]
        self.temp_array = [[0.0 for x in range(cells_per_string)] for y in range(number_of_strings)]

    def update_parameters(self, message):
        decoded = db.decode_message(message.arbitration_id, message.data)
        frame_id = message.arbitration_id
        if frame_id == 1824:
            self.measured_battery_current = decoded['measured_battery_current']
            self.measured_battery_voltage = decoded['measured_battery_voltage']
        elif frame_id == 1825:
            self.maximum_discharge_current = decoded['maximum_discharge_current']
            self.maximum_regen_current = decoded['maximum_regen_current']
        elif frame_id == 1826:
            self.maximum_measured_module_temp = decoded['maximum_measured_module_temp']
            self.minimum_measured_module_temp = decoded['minimum_measured_module_temp']
            self.minimum_measured_cell_voltage = decoded['minimum_measured_cell_voltage']
            self.maximum_measured_cell_voltage = decoded['maximum_measured_cell_voltage']
        elif frame_id == 1827:
            self.soc = decoded['state_of_charge']
            self.connector_v4_voltage = decoded['truck_connector_v4_voltage']
        elif frame_id == 1856:
            self.update_arrays('volt', decoded)
        elif frame_id == 1857:
            self.update_arrays('temp', decoded)
        elif frame_id == 1872:
            sef.soh = decoded['minimum_state_of_health']
            self.insulation_resistance = decoded['insulation_resistance']
        elif frame_id == 1873:
            self.update_arrays('soh', decoded)
        elif frame_id in (1816, 1874):
            self.country = decoded['configuration_country']


    def update_arrays(self, reading_type, decoded):
        if reading_type == 'soh':
            string = decoded['cell_soh_string_number']
            number_of_cells = decoded['cell_soh_number_of_readings']
            starting_cell = decoded['cell_soh_starting_cell']
            value = 'cell_soh_reading_'
            array = self.soh_array
        elif reading_type == 'temp':
            string = decoded['temperature_string_number']
            number_of_cells = decoded['temperature_number_of_readings']
            starting_cell = decoded['temperature_starting_cell']
            value = 'temperature_reading_'
            array = self.temp_array
        elif reading_type = 'volt':
            string = decoded['voltage_string_number']
            number_of_cells = decoded['voltage_number_of_readings']
            starting_cell = decoded['voltage_starting_cell']
            value = 'voltage_reading_'
            array = self.volt_array

        for i in number_of_cells:
            reading = value + str(i)
            array[starting_cell - 1 + i][string - 1] = decoded[value]


    def find_voltage_extremes(self):
        arr_return = self.volt_array
        for i, blah in enumerate(self.monoblock_voltages):
            if i ==  self.monoblock_voltages.index(max(self.monoblock_voltages)):
                arr_return[i] = self.add_color(str("%.3f" % round(val,3)) + "  MAX", self.VOLT_MAX_COLOR)
            elif i ==  self.monoblock_voltages.index(min(self.monoblock_voltages)):
                arr_return[i] = self.add_color(str("%.3f" % round(val,3)) + "  MIN", self.VOLT_MIN_COLOR)
            else:
                arr_return[i] = self.add_color(str("%.3f" % round(val,3)), self.VOLT_COLOR)
        return arr_return


    def find_temperature_extremes(self):
        arr_return = [None for x in range(len(self.monoblock_voltages))]
        for i, blah in enumerate(self.monoblock_temperatures):
            val = self.monoblock_temperatures[i] - 40
            if i == self.monoblock_temperatures.index(max(self.monoblock_temperatures)):
                arr_return[i] = self.add_color(str(val) + "  MAX", self.TEMPERATURE_MAX_COLOR)
            elif i ==  self.monoblock_temperatures.index(min(self.monoblock_temperatures)):
                arr_return[i] = self.add_color(str(val) + "  MIN", self.TEMPERATURE_MIN_COLOR)
            else:
                arr_return[i] = self.add_color(val, self.TEMPERATURE_COLOR)
        return arr_return

class CanDisplay:
    "This is a class to display parsed CAN bus data in a TUI"

    TITLE_COLOR = "bold red"
    VALUE_LABEL_COLOR = "bold green"
    VOLT_MAX_COLOR = "bold red"
    VOLT_MIN_COLOR = "bold blue"
    TEMPERATURE_MAX_COLOR = "bold red"
    TEMPERATURE_MIN_COLOR = "bold blue"
    VOLT_COLOR = "dim magenta"
    TEMPERATURE_COLOR = "dim green"
    STATE_COLOR = "cyan"
    ERROR_STATE_COLOR = "bold red"
    GENERAL_VALUE_COLOR = "white"

    HEADER_PANEL = "[green]Anzen BMS Modbus Interpreter[/green]"
    HEADER_STYLE = Style(color="red", bold=True)


    def __init__(self, sku, interface):
        self.bms_param = BMSParameters(sku)
        self.timestamp = None
        self.layout = Layout()
        self.interface = interface;

    def add_color(self, string, color):
        text = "[" + color + "]" + str(string) + "[/" + color + "]"
        return text

    def new_line(self, number):
        return "\n" * number

    def make_timestamp(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def make_header(self):
        header = Panel(self.HEADER_PANEL + self.timestamp(), style=self.HEADER_STYLE)
        return header

    def make_cell_values_table(self, string_num):
        table = Table(show_header=True,
                      title="Values",
                      header_style="bold magenta",
                      box=box.ROUNDED)
        table.add_column("BATTERY", style="bold")
        table.add_column("VOLTAGE", min_width=20)
        table.add_column("TEMPERATURE", min_width=20)
        for i, value in enumerate(voltages_converted):
            table.add_row(str(i+1), str(value), str(temperatures_converted[i]))
        return Panel(table)

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


    def read_can_messages(self):
        msg = self.interface.recv(90.0)
        if msg:
            self.make_timestamp()
            self.bms_param.update_parameters(msg)
            # data = binascii.hexlify(msg.data).decode(encoding='UTF-8', errors='strict')
            # frame_id = hex(msg.arbitration_id)
            # if frame_id[2:10] in self.CELL_VOLTAGE_FRAMES:
            #     self.make_cell_voltage_array(data, frame_id[-1])
            #     if DEBUG:
            #         print(str(self.SLAVE_CELLS))


    def make_layout(self) -> Layout:
        #time = Panel(self.TIMESTAMP, style = Style(color="red", bold=True))
        self.layout.split_column(
            Layout(self.make_header(), name="header", size=3),
            Layout(name="upper"),
        )

        self.layout["upper"].split_row(
            Layout(name="string1"),
            Layout(name="string2"),
            Layout(name="string3"),
            Layout(name="string4"),
            # Layout(self.make_cell_values_table()),
            Layout(name="right"),
        )

        self.layout["right"].split_column(
            Layout(name="right-top"),
            Layout(self.write_errors(), name="right-middle"),
            Layout(name="right-bottom"),
        )

        self.layout["right-top"].split_row(
            Layout(self.update_system_voltages()),
            Layout(self.update_system_health()),
        )

        return self.layout

if __name__ == '__main__':
    db = cantools.database.load_file('data/anzen-raymond-48cell-can1.dbc')
    can0 = can.interface.Bus(channel='vcan0', bustype='socketcan')
    while True:
        message = can0.recv()
        try:
            print(message.arbitration_id)
            print(db.decode_message(message.arbitration_id, message.data))
        except:
            print("unknown frame")
    # display = CanDisplay(can0, 18)
    # with Live(display.make_layout(), screen=True) as live:
    #    while True:
    #        display.read_can_messages()
    #        live.update(display.make_layout())
