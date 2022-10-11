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
        self.fan001_state = None
        self.htr001_state = None
        self.htr002_state = None


class BMSParameters:
    def __init__(self, sku):
        self.cells_per_string = None
        self.number_of_strings = None
        self.volt_array = None
        self.temp_array = None
        self.soh_array = None
        self.country = None
        self.sku = sku
        self.soc = None
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
        self.location1_primary_temp = None
        self.location1_secondary_temp = None
        self.location2_primary_temp = None
        self.location2_secondary_temp = None
        self.status = Alarms()
        self.get_sku_parameters(sku)

    def get_sku_parameters(self, sku):
        if sku == 18:
            self.number_of_strings = 4
            self.cells_per_string = 12
            self.create_arrays()
        else:
            print("SKU Unknown")

    def create_arrays(self):
        self.volt_array = [[0.0 for x in range(self.cells_per_string)] for y in range(self.number_of_strings)]
        self.soh_array = [[0.0 for x in range(self.cells_per_string)] for y in range(self.number_of_strings)]
        self.temp_array = [[0.0 for x in range(self.cells_per_string)] for y in range(self.number_of_strings)]

    def update_parameters(self, message):
        if message.arbitration_id in (404744436, 405858548):
            return
        decoded = db.decode_message(message.arbitration_id, message.data)
        print(decoded)
        frame_id = message.arbitration_id
        try:
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
            elif frame_id == 1830:
                self.update_statuses(decoded)
            elif frame_id == 1856:
                self.update_arrays('volt', decoded)
            elif frame_id == 1857:
                self.update_arrays('temp', decoded)
            elif frame_id == 1872:
                self.soh = decoded['minimum_state_of_health']
                self.insulation_resistance = decoded['insulation_resistance']
            elif frame_id == 1873:
                self.update_arrays('soh', decoded)
            elif frame_id == 1875:
                self.update_arrays('soc', decoded)
            elif frame_id == 1876:
                self.location1_primary_temp = decoded['location1_primary_temp']
                self.location1_secondary_temp = decoded['location1_secondary_temp']
                self.location2_primary_temp = decoded['location2_primary_temp']
                self.location2_secondary_temp = decoded['location2_secondary_temp']
            elif frame_id in (1816, 1874):
                self.country = decoded['configuration_country']
            else:
                pass
        except:
            pass

    def update_statuses(self, decoded):
        self.status.contactor_k4_status = decoded['contactor_k4_status']
        self.status.contactor_k5_status = decoded['contactor_k5_status']
        self.status.contactor_k7_status = decoded['contactor_k7_status']
        self.status.contactor_k4_position = decoded['contactor_k4_position']
        self.status.contactor_k5_position = decoded['contactor_k5_position']
        self.status.contactor_k7_position = decoded['contactor_k7_position']
        self.status.bms_supply_voltage_high_alarm_status = decoded['bms_supply_voltage_high_alarm_status']
        self.status.bms_supply_voltage_low_alarm_status = decoded['bms_supply_voltage_low_alarm_status']
        self.status.bms_module_temp_high_alarm_status = decoded['bms_module_temp_high_alarm_status']
        self.status.regen_current_high_alarm_status = decoded['regen_current_high_alarm_status']
        self.status.discharge_current_high_alarm_status = decoded['discharge_current_high_alarm_status']
        self.status.pack_voltage_high_alarm_status = decoded['pack_voltage_high_alarm_status']
        self.status.pack_voltage_low_alarm_status = decoded['pack_voltage_low_alarm_status']
        self.status.cell_voltage_high_alarm_status = decoded['cell_voltage_high_alarm_status']
        self.status.cell_voltage_low_alarm_status = decoded['cell_voltage_low_alarm_status']
        self.status.discharge_cell_temp_high_limit = decoded['discharge_cell_temp_high_limit']
        self.status.discharge_cell_temp_low_limit = decoded['discharge_cell_temp_low_limit']
        self.status.charge_cell_temp_high_limit = decoded['charge_cell_temp_high_limit']
        self.status.charge_cell_temp_low_limit = decoded['charge_cell_temp_low_limit']
        self.status.cell_voltage_differential_limit = decoded['cell_voltage_differential_limit']
        self.status.cell_temp_differential_limit = decoded['cell_temp_differential_limit']
        self.status.soc_high_limit = decoded['soc_high_limit']
        self.status.soc_low_limit = decoded['soc_low_limit']
        self.status.cell_soc_differential_limit = decoded['cell_soc_differential_limit']
        self.status.insulation_resistance_limit = decoded['insulation_resistance_limit']
        self.status.impending_disconnect = decoded['impending_disconnect']
        self.status.slave1_temperature_balance_error = decoded['slave1_temperature_balance_error']
        self.status.slave2_temperature_balance_error = decoded['slave2_temperature_balance_error']
        self.status.slave3_temperature_balance_error = decoded['slave3_temperature_balance_error']
        self.status.slave1_volt_balance_error = decoded['slave1_volt_balance_error']
        self.status.slave2_volt_balance_error = decoded['slave2_volt_balance_error']
        self.status.slave3_volt_balance_error = decoded['slave3_volt_balance_error']
        self.status.cell_volt_acquisition_open_wire = decoded['cell_volt_acquisition_open_wire']
        self.status.bms_internal_can_status = decoded['bms_internal_can_status']
        self.status.power_mode_state = decoded['power_mode_state']
        self.status.isns001_status = decoded['isns001_status']
        self.status.fan001_state = decoded['fan001_state']
        self.status.htr001_state = decoded['htr001_state']
        self.status.htr002_state = decoded['htr002_state']

    def update_arrays(self, reading_type, decoded):
        if reading_type == 'soh':
            string = decoded['cell_soh_string_number']
            number_of_cells = decoded['cell_soh_number_of_readings']
            starting_cell = decoded['cell_soh_starting_cell']
            value = 'cell_soh_reading_1'
            array = self.soh_array
        if reading_type == 'soc':
            string = decoded['cell_soc_string_number']
            number_of_cells = decoded['cell_soc_number_of_readings']
            starting_cell = decoded['cell_soc_starting_cell']
            value = 'cell_soc_reading_1'
            array = self.soc_array
        elif reading_type == 'temp':
            string = decoded['temperature_string_number']
            number_of_cells = decoded['temperature_number_of_readings']
            starting_cell = decoded['temperature_starting_cell']
            value = 'temperature_reading_1'
            array = self.temp_array
        elif reading_type == 'volt':
            string = decoded['voltage_string_number']
            number_of_cells = decoded['voltage_number_of_readings']
            starting_cell = decoded['voltage_starting_cell']
            value = 'voltage_reading_1'
            array = self.volt_array

        # for i in range(number_of_cells):
        #     reading = value + str(i)
        #     array[starting_cell - 1 + i][string - 1] = decoded[value]
        return


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

    def make_header(self) -> Panel:
        text = Text()
        text.append("Anzen BMS Modbus Interpreter", style = "green")
        # header = Panel(self.HEADER_PANEL, style=self.HEADER_STYLE)
        header = Panel(text)
        # header = Panel(self.HEADER_PANEL + self.timestamp(), style=self.HEADER_STYLE)
        return header

    def make_cell_values_table(self, string_num):
        table = Table(show_header=True,
                      # title="Values",
                      header_style="bold magenta",
                      box=box.ROUNDED)
        table.add_column("BATTERY", style="bold")
        table.add_column("VOLTAGE", min_width=20)
        table.add_column("TEMPERATURE", min_width=20)
        for i, value in enumerate(voltages_converted):
            table.add_row(str(i+1), str(value), str(temperatures_converted[i]))
        return Panel(table)

    def make_status_table(self):
        table = Table(show_header=True,
                      # title="BMS Status",
                      header_style="bold magenta",
                      box=box.ROUNDED)
        table.add_column("VARIABLE", style="bold")
        table.add_column("STATUS", style="bold")
        table.add_row("K4 Status", self.color_status(self.bms_param.status.contactor_k4_status))
        table.add_row("K5 Status", self.color_status(self.bms_param.status.contactor_k5_status))
        table.add_row("K7 Status", self.color_status(self.bms_param.status.contactor_k7_status))
        table.add_row("K4 Position", self.color_status(self.bms_param.status.contactor_k4_position))
        table.add_row("K5 Position", self.color_status(self.bms_param.status.contactor_k5_position))
        table.add_row("K7 Position", self.color_status(self.bms_param.status.contactor_k7_position))
        table.add_row("Imp. Disconnect", self.color_status(self.bms_param.status.impending_disconnect))
        table.add_row("Power Mode", self.color_status(self.bms_param.status.power_mode_state))
        table.add_row("FAN001 Status", self.color_status(self.bms_param.status.fan001_state))
        table.add_row("HTR001 Status", self.color_status(self.bms_param.status.htr001_state))
        table.add_row("HTR002 Status", self.color_status(self.bms_param.status.htr002_state))
        return table

    def make_alarm_table(self):
        table = Table(show_header=True,
                      # title="Alarms",
                      header_style="bold magenta",
                      box=box.ROUNDED)
        table.add_column("VARIABLE", style="bold")
        table.add_column("STATUS", style="bold")
        table.add_row("Supply Volt High", self.color_status(self.bms_param.status.bms_supply_voltage_high_alarm_status))
        table.add_row("Supply Volt Low", self.color_status(self.bms_param.status.bms_supply_voltage_low_alarm_status))
        table.add_row("BMS Temp High", self.color_status(self.bms_param.status.bms_module_temp_high_alarm_status))
        table.add_row("Regen Curr High", self.color_status(self.bms_param.status.regen_current_high_alarm_status))
        table.add_row("Disch Curr High", self.color_status(self.bms_param.status.discharge_current_high_alarm_status))
        table.add_row("Pack Volt High", self.color_status(self.bms_param.status.pack_voltage_high_alarm_status))
        table.add_row("Pack Volt Low", self.color_status(self.bms_param.status.pack_voltage_low_alarm_status))
        table.add_row("Cell Volt High", self.color_status(self.bms_param.status.cell_voltage_high_alarm_status))
        table.add_row("Cell Volt Low", self.color_status(self.bms_param.status.cell_voltage_low_alarm_status))
        table.add_row("Disch Temp High", self.color_status(self.bms_param.status.discharge_cell_temp_high_limit))
        table.add_row("Disch Temp Low", self.color_status(self.bms_param.status.discharge_cell_temp_low_limit))
        table.add_row("Charge Temp High", self.color_status(self.bms_param.status.charge_cell_temp_high_limit))
        table.add_row("Charge Temp Low", self.color_status(self.bms_param.status.charge_cell_temp_low_limit))
        table.add_row("Cell Volt Diff", self.color_status(self.bms_param.status.cell_voltage_differential_limit))
        table.add_row("Cell Temp Diff", self.color_status(self.bms_param.status.cell_temp_differential_limit))
        table.add_row("SOC High", self.color_status(self.bms_param.status.soc_high_limit))
        table.add_row("SOC Low", self.color_status(self.bms_param.status.soc_low_limit))
        table.add_row("SOC Diff", self.color_status(self.bms_param.status.cell_soc_differential_limit))
        table.add_row("Insul Resist", self.color_status(self.bms_param.status.insulation_resistance_limit))
        table.add_row("Slave1 Temp Bal", self.color_status(self.bms_param.status.slave1_temperature_balance_error))
        table.add_row("Slave2 Temp Bal", self.color_status(self.bms_param.status.slave2_temperature_balance_error))
        table.add_row("Slave3 Temp Bal", self.color_status(self.bms_param.status.slave3_temperature_balance_error))
        table.add_row("Slave1 Volt Bal", self.color_status(self.bms_param.status.slave1_volt_balance_error))
        table.add_row("Slave2 Volt Bal", self.color_status(self.bms_param.status.slave2_volt_balance_error))
        table.add_row("Slave3 Volt Bal", self.color_status(self.bms_param.status.slave3_volt_balance_error))
        table.add_row("Open Wire", self.color_status(self.bms_param.status.cell_volt_acquisition_open_wire))
        table.add_row("CAN Status", self.color_status(self.bms_param.status.bms_internal_can_status))
        table.add_row("ISNS001 Status", self.color_status(self.bms_param.status.isns001_status))
        return table

    def color_status(self, value):
        text = Text()
        if str(value) == "OK":
            text.append("OK", style="green")
        elif str(value) == "On":
            text.append("On", style="green")
        elif str(value) == "Closed":
            text.append("Closed", style="green")
        elif str(value) == "Normal":
            text.append("Normal", style="green")
        elif str(value) == "Critical":
            text.append("Critical", style="red")
        elif str(value) == "Off":
            text.append("Off", style="red")
        elif str(value) == "Open":
            text.append("Open", style="red")
        elif str(value) == "Impending Disconnect":
            text.append("Imp Disc", style="red")
        else:
            text.append(str(value))
        return text

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
            Layout(self.make_status_table(), name="right-middle", size=15),
            Layout(self.make_alarm_table(), name="right-top", size=35),
        )


        return self.layout

if __name__ == '__main__':
    db = cantools.database.load_file('data/anzen-raymond-48cell-can1.dbc')
    can0 = can.interface.Bus(channel='vcan0', bustype='socketcan')
    # while True:
    #     message = can0.recv()
    #     try:
    #         print(message.arbitration_id)
    #         print(db.decode_message(message.arbitration_id, message.data))
    #     except:
    #         print("unknown frame")
    display = CanDisplay(18, can0)
    with Live(display.make_layout(), screen=True, auto_refresh=False) as live:
       while True:
           display.read_can_messages()
           live.update(display.make_layout())
