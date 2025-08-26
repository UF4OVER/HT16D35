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


from machine import I2C, Pin
import time
import math

DEBUG = False
if DEBUG:
    from ht16d35b import HT16D35BS

    # 使用 I2C 接口
    display = HT16D35BS(I2C(0, scl=Pin(18), sda=Pin(17)), addr=0x68)

    # 动画测试函数
    def animation_test():
        # 1. 清屏
        display.clear()
        display.update()
        time.sleep(1)

        # 2. 逐个点亮LED - 从左到右，从上到下
        for y in range(8):
            for x in range(8):
                display.setPoint(x, y, (1, 1, 1))  # 白色
                display.update()
                time.sleep(0.1)

        time.sleep(1)

        # 3. 清屏
        display.clear()
        display.update()
        time.sleep(0.5)

        # 4. 对角线动画
        for i in range(15):  # 8+8-1条对角线
            display.clear()
            for x in range(8):
                y = i - x
                if 0 <= y < 8:
                    # 根据对角线索引设置不同颜色
                    if i % 3 == 0:
                        color = (1, 0, 0)  # 红色
                    elif i % 3 == 1:
                        color = (0, 1, 0)  # 绿色
                    else:
                        color = (0, 0, 1)  # 蓝色
                    display.setPoint(x, y, color)
            display.update()
            time.sleep(0.3)

        time.sleep(1)

        # 5. 圆形扩散效果
        display.clear()
        display.update()
        center_x, center_y = 3.5, 3.5
        for r in range(6):  # 半径从0到5
            for x in range(8):
                for y in range(8):
                    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if r <= distance < r + 1:
                        # 根据半径设置颜色
                        if r % 3 == 0:
                            display.setPoint(x, y, (1, 0, 0))  # 红色
                        elif r % 3 == 1:
                            display.setPoint(x, y, (0, 1, 0))  # 绿色
                        else:
                            display.setPoint(x, y, (0, 0, 1))  # 蓝色
            display.update()
            time.sleep(0.5)

        time.sleep(1)

        # 6. 心形图案
        display.clear()
        heart_pattern = [
            [0, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]
        for y in range(8):
            for x in range(8):
                if heart_pattern[y][x]:
                    display.setPoint(x, y, (1, 0, 0))  # 红色心形
        display.update()
        time.sleep(2)

        # 7. 颜色渐变效果
        display.clear()
        colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1)]
        for i in range(24):  # 循环4轮
            display.clear()
            for y in range(8):
                for x in range(8):
                    color_index = (x + y + i) % len(colors)
                    display.setPoint(x, y, colors[color_index])
            display.update()

    # 运行动画测试
    animation_test()

else:
    from ht16d35b import HT16D35BS
    # 使用 I2C 接口
    display = HT16D35BS(I2C(0, scl=Pin(18), sda=Pin(17)), addr=0x68)
    display.clear()
    def display_all_ascii_chars(display):
        """
        展示ASCII_5x7中所有字符的函数
        """
        from font import ASCII_5x7

        # 清空显示
        display.clear()

        # 获取所有字符并按ASCII码排序
        chars = sorted(ASCII_5x7.keys())

        # 显示所有字符，每行显示一个字符
        for i, char in enumerate(chars):
            # 显示字符
            display.setChar(char, 1, 1, (1,0,1))
            # 等待一段时间以便观察
            import time
            time.sleep_ms(500)

        # 最后全部显示一遍
        display.update()

    display_all_ascii_chars(display)