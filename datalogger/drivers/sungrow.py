from pymodbus.client import ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


class SungrowDriver:
    def __init__(self, port: str, slave_id: int, mppt_count=9, string_count=18):
        self.client = ModbusSerialClient(
            port=port,
            baudrate=9600,
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=1,
            method="rtu"
        )
        self.slave_id = slave_id
        self.mppt_count = mppt_count
        self.string_count = string_count
        self.client.connect()

    def read_block(self, address: int, count: int):
        result = self.client.read_input_registers(address - 1, count=count, unit=self.slave_id)
        if result.isError():
            return None
        return result.registers

    def decode_u16(self, value):
        return None if value in [0xFFFF, None] else value

    def decode_u32(self, regs):
        decoder = BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.Big, wordorder=Endian.Little)
        val = decoder.decode_32bit_uint()
        return None if val == 0xFFFFFFFF else val

    def decode_s16(self, value):
        return None if value in [0x7FFF, None] else value

    def decode_s32(self, regs):
        decoder = BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.Big, wordorder=Endian.Little)
        val = decoder.decode_32bit_int()
        return None if val == 0x7FFFFFFF else val

    def read_realtime_ac(self):
        regs = self.read_block(5019, 18)
        if not regs:
            return None

        decoder = BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.Big, wordorder=Endian.Little)

        return {
            "voltage_ab": self.decode_u16(decoder.decode_16bit_uint()) / 10,
            "voltage_bc": self.decode_u16(decoder.decode_16bit_uint()) / 10,
            "voltage_ca": self.decode_u16(decoder.decode_16bit_uint()) / 10,
            "current_a": self.decode_u16(decoder.decode_16bit_uint()) / 10,
            "current_b": self.decode_u16(decoder.decode_16bit_uint()) / 10,
            "current_c": self.decode_u16(decoder.decode_16bit_uint()) / 10,
            "power": self.decode_u32([regs[12], regs[13]]),
            "reactive_power": self.decode_s32([regs[14], regs[15]]),
            "power_factor": self.decode_s16(regs[16]) / 1000,
            "frequency": self.decode_u16(regs[17]) / 10
        }

    def read_mppt(self):
        regs = self.read_block(5011, self.mppt_count * 2)
        if not regs:
            return None

        mppt_data = []
        for i in range(self.mppt_count):
            v = self.decode_u16(regs[i * 2])
            i_ = self.decode_u16(regs[i * 2 + 1])
            mppt_data.append({
                "mppt_index": i + 1,
                "voltage": v / 10 if v is not None else None,
                "current": i_ / 10 if i_ is not None else None
            })
        return mppt_data

    def read_strings(self):
        regs = self.read_block(7013, self.string_count)
        if not regs:
            return None

        return [
            {
                "string_index": i + 1,
                "current": self.decode_u16(val) / 100 if self.decode_u16(val) is not None else None
            }
            for i, val in enumerate(regs)
        ]

    def read_error(self):
        regs = self.read_block(5038, 8)
        if not regs:
            return None

        decoder = BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.Big)
        return {
            "work_state": self.decode_u16(decoder.decode_16bit_uint()),
            "fault_time": {
                "year": self.decode_u16(decoder.decode_16bit_uint()),
                "month": self.decode_u16(decoder.decode_16bit_uint()),
                "day": self.decode_u16(decoder.decode_16bit_uint()),
                "hour": self.decode_u16(decoder.decode_16bit_uint()),
                "minute": self.decode_u16(decoder.decode_16bit_uint()),
                "second": self.decode_u16(decoder.decode_16bit_uint())
            },
            "fault_code": self.decode_u16(decoder.decode_16bit_uint())
        }

    def read_energy(self):
        day = self.read_block(5003, 1)
        month = self.read_block(5128, 2)
        total = self.read_block(5144, 2)
        runtime = self.read_block(5113, 1)

        if not all([day, month, total, runtime]):
            return None

        return {
            "energy_day_kwh": self.decode_u16(day[0]) / 10 if self.decode_u16(day[0]) is not None else None,
            "energy_month_kwh": self.decode_u32(month) / 10 if self.decode_u32(month) is not None else None,
            "energy_total_kwh": self.decode_u32(total) / 10 if self.decode_u32(total) is not None else None,
            "runtime_today_min": self.decode_u16(runtime[0])
        }

    def read_all_realtime(self):
        return {
            "ac": self.read_realtime_ac(),
            "mppt": self.read_mppt(),
            "strings": self.read_strings(),
            "error": self.read_error(),
            "energy": self.read_energy()
        }

    def close(self):
        self.client.close()
