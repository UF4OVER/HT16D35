from machine import Pin, SPI, I2C
import time

from font import ASCII_5x7


class HT16D35:
    def __init__(self, interface_type='spi', **kwargs):
        """
        初始化 HT16D35 驱动器，专为 KEM-5088-RGB 数码管模块设计

        参数:
        interface_type: 'spi' 或 'i2c'
        **kwargs: 接口相关参数
            SPI: sck, mosi, miso, cs, baudrate
            I2C: scl, sda, addr (默认 0x68)
        """
        self.interface_type = interface_type.lower()

        if self.interface_type == 'spi':
            self.spi = SPI(kwargs.get('spi_bus', 0),
                           baudrate=kwargs.get('baudrate', 1000000),
                           polarity=0,
                           phase=0,
                           sck=Pin(kwargs.get('sck', 0)),
                           mosi=Pin(kwargs.get('mosi', 1)),
                           miso=Pin(kwargs.get('miso', 2)))
            self.cs = Pin(kwargs.get('cs', 3), Pin.OUT)
            self.cs.value(1)
        elif self.interface_type == 'i2c':
            self.i2c = I2C(kwargs.get('i2c_bus', 0),
                           scl=Pin(kwargs.get('scl', 5)),
                           sda=Pin(kwargs.get('sda', 4)),
                           freq=kwargs.get('freq', 400000))
            self.addr = kwargs.get('addr', 0x68)
        else:
            raise ValueError("不支持的接口类型，请选择 'spi' 或 'i2c'")

        # 初始化显示缓冲区 (8x8x3)
        self.buffer = [[[0, 0, 0] for _ in range(8)] for _ in range(8)]

        # 初始化芯片
        self.init_chip()

    def write_command(self, command, data=None):
        """写入命令到芯片"""
        if self.interface_type == 'spi':
            self.cs.value(0)
            self.spi.write(bytearray([command]))
            if data is not None:
                self.spi.write(bytearray(data))
            self.cs.value(1)
        else:  # I2C
            if data is None:
                self.i2c.writeto(self.addr, bytearray([command]))
            else:
                self.i2c.writeto(self.addr, bytearray([command] + data))

    def init_chip(self):
        """初始化芯片设置"""
        # 软件复位
        self.write_command(0xCC)
        time.sleep(0.01)

        # 设置二进制模式
        self.write_command(0x31, [0x01])  # 二进制模式

        # 设置 COM 输出数量为 8
        self.write_command(0x32, [0x07])  # COM0-7

        # 设置恒流率 (最大电流)
        self.write_command(0x36, [0x00])

        # 设置全局亮度 (最大亮度)
        self.write_command(0x37, [0x40])  # 64/64 占空比

        # 设置 COM 引脚控制 (开启所有 COM 输出)
        self.write_command(0x41, [0xFF])

        # 设置 ROW 引脚控制 (开启所有 ROW 输出)
        # 根据 KEM-5088-RGB 的特殊引脚排列
        self.write_command(0x42, [0xFF, 0xFF, 0xFF, 0xFF])

        # 开启系统振荡器和显示
        self.write_command(0x35, [0x03])

        # 清除显示
        self.clear()
        self.update()

    def map_pixel_to_pins(self, x, y, color):
        """
        将像素位置映射到 KEM-5088-RGB 的特殊引脚排列

        参数:
        x: X 坐标 (0-7, 列)
        y: Y 坐标 (0-7, 行)
        color: (R, G, B) 元组

        返回:
        需要更新的 ROW 引脚和对应的位掩码
        """
        # KEM-5088-RGB 的特殊引脚映射
        # 模块引脚: 1,9,28 是第一列的 RGB
        #           2,10,27 是第二列
        #           ...
        #           8,16,21 是第八列

        # 定义列到 ROW 引脚的映射
        column_to_row = {
            0: [0, 8, 23],   # 第一列: R, G, B 对应的 ROW 引脚
            1: [1, 9, 22],   # 第二列
            2: [2, 10, 21],  # 第三列
            3: [3, 11, 20],  # 第四列
            4: [4, 12, 19],  # 第五列
            5: [5, 13, 18],  # 第六列
            6: [6, 14, 17],  # 第七列
            7: [7, 15, 16]   # 第八列
        }

        # 定义行到 COM 引脚的映射
        # 模块的 17,18,19,20,29,30,31,32 是 8 个行的共阳极
        # 对应 COM0-7
        row_to_com = {
            0: 0,  # 第一行 -> COM0
            1: 1,  # 第二行 -> COM1
            2: 2,  # 第三行 -> COM2
            3: 3,  # 第四行 -> COM3
            4: 4,  # 第五行 -> COM4
            5: 5,  # 第六行 -> COM5
            6: 6,  # 第七行 -> COM6
            7: 7   # 第八行 -> COM7
        }

        # 获取当前列的 ROW 引脚
        r_pin, g_pin, b_pin = column_to_row[x]

        # 获取当前行的 COM 位
        com_bit = row_to_com[y]

        # 准备更新数据
        updates = []
        r, g, b = color

        if r > 0.5:  # 红色
            updates.append((r_pin, com_bit))
        if g > 0.5:  # 绿色
            updates.append((g_pin, com_bit))
        if b > 0.5:  # 蓝色
            updates.append((b_pin, com_bit))

        return updates

    def set_pixel(self, x, y, color):
        """
        设置单个像素的颜色

        参数:
        x: X 坐标 (0-7, 列)
        y: Y 坐标 (0-7, 行)
        color: (R, G, B) 元组，每个值 0-1 (0=关, 1=开)
        """
        if 0 <= x < 8 and 0 <= y < 8:
            self.buffer[y][x] = color


    def read_display_ram(self, address):
        """
        读取显示 RAM 的值
        """
        # 发送读命令
        self.write_command(0x81, [address])

        # 读取数据 (SPI 需要额外处理)
        if self.interface_type == 'spi':
            self.cs.value(0)
            # 发送空字节以读取数据
            self.spi.write(bytearray([0x00]))
            # 读取响应
            data = self.spi.read(1)
            self.cs.value(1)
            return data[0] if data else 0
        else:
            # I2C 读取
            data = self.i2c.readfrom(self.addr, 1)
            return data[0] if data else 0

    def write_display_ram(self, address, value):
        """
        写入显示 RAM
        """
        self.write_command(0x80, [address, value])

    def clear(self, color=(0, 0, 0)):
        """
        清除显示

        参数:
        color: (R, G, B) 元组，默认黑色
        """
        # 清除所有显示 RAM
        for i in range(28):  # ROW0-27
            self.write_display_ram(i, 0x00)

        # 更新缓冲区
        for y in range(8):
            for x in range(8):
                self.buffer[y][x] = color


    def update(self):
        """
        更新整个显示
        这种方法效率较低，但确保显示正确
        """
        # 先清除所有显示 RAM
        for i in range(28):  # ROW0-27
            self.write_display_ram(i, 0x00)

        # 然后逐个设置每个像素
        for y in range(8):
            for x in range(8):
                color = self.buffer[y][x]
                updates = self.map_pixel_to_pins(x, y, color)

                for row_pin, com_bit in updates:
                    # 计算显示 RAM 地址
                    ram_address = row_pin
                    # 读取当前值
                    current_value = self.read_display_ram(ram_address)
                    # 设置相应的位
                    new_value = current_value | (1 << com_bit)
                    # 写回显示 RAM
                    self.write_display_ram(ram_address, new_value)
    def set_brightness(self, level):
        """
        设置全局亮度

        参数:
        level: 亮度级别 (0-63)
        """
        if level < 0:
            level = 0
        elif level > 63:
            level = 63

        # 设置亮度命令
        self.write_command(0x37, [level])
    def display_char(self, char, x_offset=1, y_offset=0, color=(1, 0, 0)):
        """
        在指定位置显示一个字符

        参数:
        char: 要显示的字符
        x_offset: X 偏移量 (0-3)
        y_offset: Y 偏移量 (0-1)
        color: (R, G, B) 元组
        """
        # 获取字符的点阵数据
        if char in ASCII_5x7:
            char_data = ASCII_5x7[char]
        else:
            # 如果字符不在字库中，显示空格
            char_data = ASCII_5x7[' ']

        # 清除显示
        self.clear()

        # 显示字符
        for col in range(5):  # 5列
            col_data = char_data[col]
            for row in range(7):  # 7行
                # 检查该位是否被设置（注意位顺序）
                if col_data & (1 << (6-row)):
                    x = col + x_offset
                    y = row + y_offset
                    if 0 <= x < 8 and 0 <= y < 8:
                        self.set_pixel(x, y, color)

        # 更新显示
        self.update()
