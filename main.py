# coding: utf-8

from field import Field
from controller import Controller

import copy
from random import randint as ri
from time import time, sleep
import pyxel


class App:
    def __init__(self):
        self.Clear()

        # MAX: 213x160
        pyxel.init(210, 160, caption='Boundarpy', scale=2, fps=30)
        pyxel.load('assets/main.pyxres')
        pyxel.run(self.Update, self.Draw)
    
    def Clear(self):
        print('[===,===]GAME START')
        self.controller = Controller(keybord=True)
        self.field = Field(box_size=[10,30, 200,150], player_position=[10,30])

        self.pos = [10, 30]
        self.pre_pos = self.pos[:]

        self.move_scale = 2

        self.player_x = 5
        self.player_y = 5
        self.player_img = 0

        self.enemy_position = [170, 40]
        self.enemy_pre_position = self.enemy_position[:]
        self.enemy_normal = [[-1*self.move_scale, 1*self.move_scale][ri(0,1)], [-1*self.move_scale, 1*self.move_scale][ri(0,1)]]
        self.enemy_pre_normal = self.enemy_normal[:]
        self.enemy_size = 9

        self.game_box = (10,20, 200,150)

        self.line_color = 13
        self.line_color_accent = 14
        self.line_color_no_accent = 5

        self.on_line = True
        self.pre_on_line = True
        # [X or Y, count]
        self.on_line_info = []
        self.pre_on_line_info = []

        self.game = True
        self.game_message = 'CLEAR THE GAME'
        self.game_count = 0

    def Update(self):
        self.controller.Update()

        if 9 in self.controller.up_list:
            self.Clear()
            return
        
        if not self.game:
            if pyxel.play_pos(0) != -1:
                pyxel.stop(0)
            return
        
        if pyxel.play_pos(0) == -1:
            pyxel.playm(0, loop=True)
        
        if self.enemy_pre_position == self.enemy_position:
            self.game_count += 1
            if self.game_count > 30:
                self.game = False
                print('[###,###]CLEAR THE GAME')
                return
        else:
            self.game_count = 0

        self.pre_pos = self.pos[:]
        self.pos[0] += self.controller.stick[0] * self.move_scale
        self.pos[1] += self.controller.stick[1] * self.move_scale

        self.enemy_pre_position = self.enemy_position[:]
        self.enemy_position[0] += self.enemy_normal[0]
        self.enemy_position[1] += self.enemy_normal[1]

        result = self.field.JudgeLine(self.field.border_line, self.field.border_line_sub, self.enemy_position)
        if len(result) > 0:
            self.enemy_position = self.enemy_pre_position[:]
            self.enemy_pre_normal = self.enemy_normal[:]
            self.enemy_normal = [0, 0]
            start_time = time()
            while 2 > time() - start_time and (self.enemy_normal == [0, 0] or self.enemy_normal == self.enemy_pre_normal):
                self.enemy_normal = [[-1*self.move_scale, 0, 1*self.move_scale][ri(-1,1)], [-1*self.move_scale, 0, 1*self.move_scale][ri(-1,1)]]
            if not 2 > time() - start_time:
                self.game = False
                self.game_message = 'GAMEOVER'
                print('[###,###]GAMEOVER')
                return
        result = self.field.JudgeLine(self.field.creation_line, self.field.creation_line_sub, self.enemy_position)
        if len(result) > 0:
            self.game = False
            self.game_message = 'GAMEOVER'
            print('[###,###]GAMEOVER')
            return

        result = self.field.JudgeLine(self.field.creation_line, self.field.creation_line_sub, self.pos)
        if len(result) > 0:
            if self.field.creation[0][0] != self.pos:
                self.pos = self.pre_pos[:]
                return

        self.pre_on_line = self.on_line
        result = self.field.JudgeLine(self.field.border_line, self.field.border_line_sub, self.pos)
        if len(result) > 0:
            self.on_line = True
        else:
            self.on_line = False

        if not self.on_line and self.pre_on_line:
            # 領域外に出たとき
            result = self.field.JudgeLine(self.field.border_line, self.field.border_line_sub, self.pre_pos)
            for num, index in result:
                normal = [0, 0]
                normal[num] = self.field.border_line_normal[num][index]
                if normal == self.controller.stick:
                    self.field.creation[0][0] = self.pre_pos[:]
                    self.field.creation[1][0] = self.field.ConvertToNormal(self.controller.stick)
                    self.field.creation[2][0] = self.pos[:]
                    self.field.CreationUpdate(self.controller.stick, self.pos, self.pre_pos)
                    return
            self.pos = self.pre_pos[:]
            self.on_line = True
            return
        elif self.on_line and not self.pre_on_line:
            print(f'[{self.pos[0]:>3},{self.pos[1]:>3}]draw end')
            self.field.creation[0][1] = self.pos[:]
            self.field.creation[1][1] = self.field.ConvertToNormal(self.controller.stick)
            self.field.creation[2][1] = self.pre_pos[:]
            self.field.CreationUpdate(self.controller.stick, self.pos, self.pre_pos)
            if self.field.Search(self.enemy_position) == 'error':
                self.game = False
                self.game_message = 'GAMEOVER'
                print('[###,###]GAMEOVER')
                return
            self.field.UpdateAllLine()
            self.field.UpdateBorderLine()
            self.field.CreationClear()
        elif not self.on_line and not self.pre_on_line:
            self.field.CreationUpdate(self.controller.stick, self.pos, self.pre_pos)
            # 領域の塗りつぶしと割合の計算
        
        if not self.on_line and self.pre_pos != self.pos:
            pyxel.play(1, 1)
        elif pyxel.play_pos(1) != -1:
            pyxel.stop(1)


    def Draw(self):
        if not self.game:
            if self.game_message == 'GAMEOVER':
                pyxel.rect(70, 60, 73, 45, 1)
                pyxel.text(90, 70, self.game_message, 7)
            else:
                pyxel.rect(70, 60, 78, 45, 1)
                pyxel.text(80, 70, self.game_message, 10)
            if self.controller.keyboad:
                pyxel.text(78, 90, 'press SPACE KEY', 7)
            else:
                pyxel.text(85, 90, 'press START', 7)
            return

        pyxel.cls(0)

        if self.controller.keyboad:
            pyxel.text(10, 10, 'RESTART: SPACE KEY', 7)
        else:
            pyxel.text(10, 10, 'RESTART: START Button', 7)

        # 領域の描画

        # 現在描き途中の線
        for index in range(len(self.field.creation_line[0])):
            pyxel.line(self.field.creation_line[0][index], self.field.creation_line_sub[0][index][0], self.field.creation_line[0][index], self.field.creation_line_sub[0][index][1], self.line_color_accent)
        for index in range(len(self.field.creation_line[1])):
            pyxel.line(self.field.creation_line_sub[1][index][0], self.field.creation_line[1][index], self.field.creation_line_sub[1][index][1], self.field.creation_line[1][index], self.line_color_accent)

        # すべての線
        for index in range(len(self.field.all_line[0])):
            pyxel.line(self.field.all_line[0][index], self.field.all_line_sub[0][index][0], self.field.all_line[0][index], self.field.all_line_sub[0][index][1], self.line_color_no_accent)
        for index in range(len(self.field.all_line[1])):
            pyxel.line(self.field.all_line_sub[1][index][0], self.field.all_line[1][index], self.field.all_line_sub[1][index][1], self.field.all_line[1][index], self.line_color_no_accent)

        # 枠
        for index in range(len(self.field.border_line[0])):
            pyxel.line(self.field.border_line[0][index], self.field.border_line_sub[0][index][0], self.field.border_line[0][index], self.field.border_line_sub[0][index][1], self.line_color)
        for index in range(len(self.field.border_line[1])):
            pyxel.line(self.field.border_line_sub[1][index][0], self.field.border_line[1][index], self.field.border_line_sub[1][index][1], self.field.border_line[1][index], self.line_color)

        # ゲームの枠
        #pyxel.rectb(self.game_box[0], self.game_box[1], self.game_box[2] - self.game_box[0] + 1, self.game_box[3] - self.game_box[1] + 1, self.line_color)

        # プレイヤー
        if len(self.controller.button_list) > 0:
            self.player_img = 8 + self.controller.button_list[0] * 8 if self.controller.button_list[0] < 4 else 0
        else:
            self.player_img = 0
        pyxel.blt(self.pos[0] -2, self.pos[1] -2, 0, self.player_img, 0, self.player_x, self.player_y, 0)

        # 敵
        pyxel.blt(self.enemy_position[0]-2, self.enemy_position[1]-2, 0, 0, 8, self.player_x, self.player_y, 0)

if __name__=='__main__':
    App()
