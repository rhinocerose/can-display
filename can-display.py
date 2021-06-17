import connect_can
import can
import binascii
import system_dimension

class CanDisplay:
    "This is a class to display parsed CAN bus data in a TUI"

    CELL_VOLTAGE_FRAMES = ['1811f580', '1811f581', '1811f582', '1811f583']
    ERROR_FRAMES = ['1811f580', '1811f581', '1811f582', '1811f583']

    def __init__(self):
        self.SLAVE1_CELLS = [None for i in range(48)]
        self.SLAVE2_CELLS = [None for i in range(32)]
        self.SLAVE3_CELLS = [None for i in range(28)]
        self.SLAVE4_CELLS = [None for i in range(48)]

    def make_cell_voltage_array(self, data, slave_num):
        index = int(data[:2], 16) - 1
        print("Slave Number: " + str(slave_num))
        print("Cell Index:   " + str(index + 1))
        i=0
        packets = int((len(data)/4)-1)
        for i in range(packets):
            first = 4*(i+1)
            last = first + 4
            if int(slave_num) == 0:
                self.SLAVE1_CELLS[index + i] = data[first:last]
            if int(slave_num) == 1:
                self.SLAVE2_CELLS[index + i] = data[first:last]
            if int(slave_num) == 2:
                self.SLAVE3_CELLS[index + i] = data[first:last]
            if int(slave_num) == 3:
                self.SLAVE4_CELLS[index + i] = data[first:last]

    def read_can_messages(self):
        msg = connect_can.can0.recv(10.0)
        if msg:
            data = binascii.hexlify(msg.data).decode(encoding='UTF-8', errors='strict')
            frame_id = hex(msg.arbitration_id)
            if frame_id[2:10] in self.CELL_VOLTAGE_FRAMES:
                print("Frame ID: " + str(frame_id))
                self.make_cell_voltage_array(data, frame_id[-1])
                print("SLAVE 1: " + str(self.SLAVE1_CELLS))
                print("SLAVE 2: " + str(self.SLAVE2_CELLS))
                print("SLAVE 3: " + str(self.SLAVE3_CELLS))
                print("SLAVE 4: " + str(self.SLAVE4_CELLS))

if __name__ == '__main__':
    display = CanDisplay()
    while True:
        display.read_can_messages()
