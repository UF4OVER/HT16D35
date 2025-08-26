# -*- coding: utf-8 -*-
# -------------------------------
#  @Project : H16D35B
#  @Time    : 2025 - 08-25 21:09
#  @FileName: ht16d35b_i2c.py
#  @Software: PyCharm 2024.1.6 (Professional Edition)
#  @System  : Windows 11 23H2
#  @Author  : 33974
#  @Contact : 
#  @Python  : 
# -------------------------------
import time
from machine import I2C

from font import ASCII_5x7


class Command:
    def __init__(self, command: int, val: list):
        self._command = command
        self._val = val

    @property
    def CMD(self):
        print(f"CMD:{self._command}")
        return self._command

    @property
    def VAL(self):
        print(f"VAL:{self._val}")
        return self._val


RESET = Command(0xcc, [0])
# COM引脚控制
COM_CONTROL = Command(0x41, [0xFF])
# COM输出
COM_OUTPUT = Command(0x32, [0x07])
# ROW输出
ROW_OUTPUT = Command(0x42, [0xFF, 0xFF, 0xFF, 0xFF])
# 二进制/灰度模式选择
MODE_SELECTION = Command(0x31, [0x01])
# 恒流率
CONSTANT_CURRENT = Command(0x36, [0x00])  # I ROW_MAX = 20MA
# 全局亮度
GLOBAL_BRIGHTNESS = Command(0x37, [63])  # 63/64 占空比 (修正: 最大值为63)
# OSC振荡器启动
OSC_START = Command(0x35, [0x03])  # 正常显示模式– COM扫描有效


class HT16D35Base:
    def __init__(self, i2c: I2C, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.buffer = [[[0, 0, 0] for _ in range(8)] for _ in range(8)]
        self.display_ram = [0] * 28  # 跟踪当前显示RAM状态

    def _writeCommand(self, command, data=None):
        if data is None:
            self.i2c.writeto(self.addr, bytearray([command]))
        else:
            self.i2c.writeto(self.addr, bytearray([command] + data))

    def _readRam(self, address):
        self._writeCommand(0x81, [address])
        # I2C 读取
        data = self.i2c.readfrom(self.addr, 1)
        return data[0] if data else 0

    def _writeRam(self, address, value):
        self._writeCommand(0x80, [address, value])
        self.display_ram[address] = value  # 更新跟踪状态
    def _mapPixelPins(self, x, y, color):
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
            0: [0, 8, 23],  # 第一列: R, G, B 对应的 ROW 引脚
            1: [1, 9, 22],  # 第二列
            2: [2, 10, 21],  # 第三列
            3: [3, 11, 20],  # 第四列
            4: [4, 12, 19],  # 第五列
            5: [5, 13, 18],  # 第六列
            6: [6, 14, 17],  # 第七列
            7: [7, 15, 16]  # 第八列
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
            7: 7  # 第八行 -> COM7
        }

        # 获取当前列的 ROW 引脚
        r_pin, g_pin, b_pin = column_to_row[x]

        # 获取当前行的 COM 位
        com_pin = row_to_com[y]

        # 准备更新数据
        updates = []
        r, g, b = color

        if r > 0.5:  # 红色
            updates.append((r_pin, com_pin))
        if g > 0.5:  # 绿色
            updates.append((g_pin, com_pin))
        if b > 0.5:  # 蓝色
            updates.append((b_pin, com_pin))

        return updates

    def update(self):
        """
        display on
        :return: None
        """
        # 清空显示 RAM
        # for i in range(28):
        #     self._writeRam(i, 0x00)
        ram_updates = {}
        for y in range(8):
            for x in range(8):
                color = self.buffer[y][x]
                updates = self._mapPixelPins(x, y, color)
                for row_pin, com_pin in updates:
                    if row_pin not in ram_updates:
                        ram_updates[row_pin] = 0
                    ram_updates[row_pin] |= (1 << com_pin)

        # 只更新变化的RAM地址
        for ram_address in range(28):
            new_value = ram_updates.get(ram_address, 0)
            if new_value != self.display_ram[ram_address]:
                self._writeRam(ram_address, new_value)

    def clear(self, color=(0, 0, 0)):
        """
        清除显示

        参数:
        color: (R, G, B) 元组，默认黑色
        """
        # 清除所有显示 RAM
        for i in range(28):  # ROW0-27
            self._writeRam(i, 0x00)

        # 更新缓冲区
        for y in range(8):
            for x in range(8):
                self.buffer[y][x] = color

    def setPoint(self, x, y, color):
        """
        设置单个像素颜色到缓冲区，不直接写硬件
        """
        if 0 <= x < 8 and 0 <= y < 8:
            self.buffer[y][x] = color

    def setBrightness(self, level):
        if level < 0:
            level = 0
        elif level > 63:
            level = 63

        # 设置亮度命令
        self._writeCommand(0x37, [level])


class HT16D35BS(HT16D35Base):
    """
    单个芯片
    """
    def __init__(self, i2c: I2C, addr=0x68):
        super().__init__(i2c, addr)
        self._initChip()
    def _initChip(self):
        """初始化芯片设置"""
        # 软件复位
        self._writeCommand(0XCC)
        time.sleep_ms(5)
        self._writeCommand(MODE_SELECTION.CMD, MODE_SELECTION.VAL)  # 二进制/灰度模式选择
        self._writeCommand(COM_OUTPUT.CMD, COM_OUTPUT.VAL)  # COM输出
        self._writeCommand(CONSTANT_CURRENT.CMD, CONSTANT_CURRENT.VAL)  # 恒流率
        self._writeCommand(GLOBAL_BRIGHTNESS.CMD, GLOBAL_BRIGHTNESS.VAL)  # 全局亮度
        self._writeCommand(COM_CONTROL.CMD, COM_CONTROL.VAL)  # COM引脚控制
        self._writeCommand(ROW_OUTPUT.CMD, ROW_OUTPUT.VAL)  # ROW输出
        self._writeCommand(OSC_START.CMD, OSC_START.VAL)  # OSC振荡器启动
        self.clear()
        self.update()

    def setChar(self, char, x_offset=0, y_offset=0, color=(1, 0, 0)):
        """
        在指定位置显示一个字符
        char: 单个字符
        x_offset, y_offset: 偏移量
        color: (R,G,B)
        """
        # 获取字模数据
        char_data = ASCII_5x7.get(char, ASCII_5x7[' '])

        for col in range(5):
            col_data = char_data[col]
            for row in range(7):
                x = col + x_offset
                y = row + y_offset
                if 0 <= x < 8 and 0 <= y < 8:
                    if col_data & (1 << (6 - row)):
                        self.buffer[y][x] = color  # 点亮像素
                    else:
                        self.buffer[y][x] = (0, 0, 0)  # 关闭像素

        # 最后统一刷新
        self.update()

