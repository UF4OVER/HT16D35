# -*- coding: utf-8 -*-
# -------------------------------
#  @Project : H16D35B
#  @Time    : 2025 - 08-25 09:48
#  @FileName: main.py
#  @Software: PyCharm 2024.1.6 (Professional Edition)
#  @System  : Windows 11 23H2
#  @Author  : 33974
#  @Contact : 
#  @Python  : 
# -------------------------------
import time

from ht16d35b import HT16D35

# 使用 I2C 接口
display = HT16D35("i2c", scl=18, sda=17, addr=0x68)

# display.set_pixel(5, 0, (1, 0, 0))  # 蓝色
# display.update()

def demo_font():

    display.display_char('B', color=(0, 1, 0))  # 绿色字母 B
    # time.sleep(2)

    # display.display_char('C', color=(0, 0, 1))  # 蓝色字母 C
    # time.sleep(2)


    display.update()

# 运行演示
if __name__ == "__main__":
    demo_font()