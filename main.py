# coding: utf-8

import copy
from random import randint as ri
from time import time
import pyxel
import pygame
from pygame import locals

class Controller:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print('controller not found')
            self.keyboad = True
        else:
            self.keyboad = False
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        
        self.joystick_x = 0
        self.joystick_y = 0

        self.stick = [0, 0]
        self.stick_rollover = [0, 0]

        self.down_list = []
        self.up_list   = []
        self.button_list = []

    def Update(self):
        self.down_list.clear()
        self.up_list.clear()

        for event in pygame.event.get():
            if event.type == pygame.locals.JOYAXISMOTION:
                self.joystick_x = self.joystick.get_axis(0)
                self.joystick_y = self.joystick.get_axis(1)
                self.joystick_x = 1 if self.joystick_x > 0 else -1 if self.joystick_x < 0 else 0
                self.joystick_y = 1 if self.joystick_y > 0 else -1 if self.joystick_y < 0 else 0
            elif event.type == pygame.locals.JOYBUTTONDOWN:
                self.down_list.append(event.button)
            else:
                self.up_list.append(event.button)
        
        for down in self.down_list:
            self.button_list.append(down)
        for up in self.up_list:
            self.button_list.remove(up)

        self.stick_rollover = [self.joystick_x, self.joystick_y]
        if self.stick_rollover == [0, 0]:
            self.stick = [0, 0]
        elif self.stick != [0, 0] and self.stick_rollover[0] != 0 and self.stick_rollover[1] != 0:
            pass
        elif self.stick_rollover[0] != 0:
            self.stick = [self.stick_rollover[0], 0]
        else:
            self.stick = [0, self.stick_rollover[1]]


class Field:
    def __init__(self, box_size=[10,30, 200,150], player_position=[10, 30]):
        self.position = player_position
        self.pre_position = self.position[:]
        self.box = box_size

        # 描画用: main:[[x],[y]] sub:[[x_y],[y_x]]
        self.all_line = [self.box[::2], self.box[1::2]]
        self.all_line_sub = [[self.box[1::2],self.box[1::2]], [self.box[::2],self.box[::2]]]

        # 判定用: main:[[x],[y]] sub:[[x_y],[y_x]] normal:[[x_n],[y_n]]
        self.border_line = [self.box[::2], self.box[1::2]]
        self.border_line_sub = [[self.box[1::2],self.box[1::2]], [self.box[::2],self.box[::2]]]
        self.border_line_normal = [[1, -1], [1, -1]]

        # 作成用: main:[[x],[y]] sub:[[x_y],[y_x]] normal:[[x_n],[y_n]]  direction:[[1,0], [0,1], ...] creation:[[b_pos, e_pos], [b_normal, e_normal]]
        self.creation_line = [[], []]
        self.creation_line_sub = [[], []]
        self.creation_line_normal = [[], []]
        self.creation_line_direction = []
        self.creation = [[0, 0], [[0, 0], [0, 0]]]
    
    def GetPosition(self, line, line_sub, line_info):
        '''
        return [min_pos, max_pos]
        '''
        num, index = line_info
        if num == 0:
            return [[line[num][index], line_sub[num][index][0]],  [line[num][index], line_sub[num][index][1]]]
        else:
            return [[line_sub[num][index][0], line[num][index]],  [line_sub[num][index][1], line[num][index]]]
    
    def GetNormal(self, line_normal, line_info):
        '''
        return [1, 0]
        '''
        num, index = line_info
        if num == 0:
            return [line_normal[num][index], 0]
        else:
            return [0, line_normal[num][index]]

    def JudgeLine(self, line, line_sub, position, line_normal=None, normal_scale=1):
        '''
        入力された座標に対して重なっている線の情報を返す
        return [ [XorY, index], [XorY, index], ...]
        '''
        result_list = []
        if line_normal != None:
            for num in range(2):
                for i in range(len(line[num])):
                    line[num][i] += line_normal[num][i] * normal_scale
        for num in range(2):
            for index in [c for c,l in enumerate(line[num]) if l == position[num]]:
                line_min = line_sub[num][index][0]
                line_max = line_sub[num][index][1]
                if line_min <= position[1-num] <= line_max:
                    result_list.append([num, index])
        # [ [XorY, index], ... ]
        return result_list

    def JudgeLineCross(self, creation, creation_sub, creation_normal, border, border_sub, position):
        '''
        十字上に探索する
        return [探索完了か(bool), [反転させるか or pos]]
        '''
        creation_cross_result = self.LineCross(creation, creation_sub, position)
        creation_cross = self.ConvertToCross(position, creation_cross_result)
        c_cross = self.NearestCross(creation_cross, position)
        border_cross_result = self.LineCross(border, border_sub, position)
        border_cross = self.ConvertToCross(position, border_cross_result)
        b_cross = self.NearestCross(border_cross, position)

        result = self.ComparsionCross(c_cross, b_cross)
        if len(result) != 0:
            normal = result[0]
            pos = result[1]
            result_ = self.JudgeLine(creation, creation_sub, pos)
            for num, index in result_:
                if creation_normal[num][index] == normal[num]:
                    return [True, True]
            return [True, False]
        return [False, b_cross[0]]


    
    def NearestCross(self, cross, position):
        '''
        一番近い点だけにする
        return [[1,0], [0,1], [-1,0], [0,-1]]
        '''
        if len(cross[0]) > 0:
            nearest = cross[0][0][:]
            if len(cross[0]) > 1:
                for pos in cross[0]:
                    if nearest[0] > pos[0]:
                        nearest = pos[:]
            cross[0] = nearest[:]
        if len(cross[1]) > 0:
            nearest = cross[1][0][:]
            if len(cross[1]) > 1:
                for pos in cross[1]:
                    if nearest[1] > pos[1]:
                        nearest = pos[:]
            cross[1] = nearest[:]
        if len(cross[2]) > 0:
            nearest = cross[2][0][:]
            if len(cross[2]) > 1:
                for pos in cross[2]:
                    if nearest[0] < pos[0]:
                        nearest = pos[:]
            cross[2] = nearest[:]
        if len(cross[3]) > 0:
            nearest = cross[3][0][:]
            if len(cross[3]) > 1:
                for pos in cross[3]:
                    if nearest[1] < pos[1]:
                        nearest = pos[:]
            cross[3] = nearest[:]
        return cross

    def ComparsionCross(self, creation_cross, border_cross):
        '''
        return creation_lineのほうが近いか
        '''
        if len(creation_cross[0]) != 0:
            if creation_cross[0][0] <= border_cross[0][0]:
                return [[1, 0], creation_cross[0]]
        if len(creation_cross[1]) != 0:
            if creation_cross[1][1] <= border_cross[1][1]:
                return [[0, 1], creation_cross[1]]
        if len(creation_cross[2]) != 0:
            if creation_cross[2][0] >= border_cross[2][0]:
                return [[-1, 0], creation_cross[2]]
        if len(creation_cross[3]) != 0:
            if creation_cross[3][1] >= border_cross[3][1]:
                return [[0, -1], creation_cross[3]]
        return []

    def LineCross(self, line, line_sub, position):
        '''
        入力された座標に対して十字上に線があった場合、その座標を返す
        return [ position, ...]
        '''
        result_list = []
        for num in range(2):
            for index in range(len(line_sub[num])):
                if line_sub[num][index][0] <= position[1-num] <= line_sub[num][index][1]:
                    pos = [0, 0]
                    pos[num] = line[num][index]
                    pos[1-num] = position[1-num]
                    result_list.append(pos)
        return result_list
    
    def ConvertToCross(self, position, cross_position):
        '''
        入力された位置に対する方向によって仕分ける
        return [[1,0], [0,1], [-1,0], [0,-1]]
        '''
        result_list = [[], [], [], []]
        for pos in cross_position:
            n = self.CreateNormal(position, pos)
            if n == [1, 0]:
                result_list[0].append(pos[:])
            elif n == [0, 1]:
                result_list[1].append(pos[:])
            elif n == [-1, 0]:
                result_list[2].append(pos[:])
            else:
                result_list[3].append(pos[:])
        return result_list

    
    def ConvertToNormal(self, direction):
        '''
        進行方向から右向きのNormalを返す
        '''
        if direction == [1, 0]:
            return [0, 1]
        elif direction == [0, 1]:
            return [-1, 0]
        elif direction == [-1, 0]:
            return [0, -1]
        elif direction == [0, -1]:
            return [1, 0]
        else:
            return [0, 0]
    
    def CreateNormal(self, begin_position, end_position):
        '''
        2点間の方向を返す
        '''
        nx = end_position[0] - begin_position[0]
        ny = end_position[1] - begin_position[1]
        nx = 0 if nx == 0 else 1 if nx > 0 else -1
        ny = 0 if ny == 0 else 1 if ny > 0 else -1
        return [nx, ny]
    
    def InversionNormalOne(self, normal):
        '''
        向きを反転させる
        return [1, -1, 1, 1, ...]
        '''
        for num in range(2):
            if len(normal[num]) > 0:
                for i in range(len(normal[num])):
                    normal[num][i] *= -1
        return normal
    
    def InversionNormal(self, normal):
        '''
        向きを反転させる
        return [[1,0], [-1,0], ...]
        '''
        for index in range(len(normal)):
            normal[index][0] *= -1
            normal[index][1] *= -1
        return normal

    def IsInLine(self, line, line_sub, line_info, end_position):
        '''
        入力された線上に点があるかを返す
        return [[end_position](点の位置), ...]
        '''
        result_list = []
        for position in end_position:
            for xy, index in line_info:
                if line[xy][index] == position[xy]:
                    if line_sub[xy][index][0] <= position[1-xy] <= line_sub[xy][index][1]:
                        result_list.append(position)
        return result_list
    
    def NearestPosition(self, position, position_0, position_1):
        p0 = abs(position_0[0] - position[0]) + abs(position_0[1] - position[1])
        p1 = abs(position_1[0] - position[0]) + abs(position_1[1] - position[1])
        if p0 <= p1:
            return position_0
        else:
            return position_1

    def SearchPosition(self, line, line_sub, line_normal, begin_position, end_position, end_normal):
        '''
        入力された座標が線上を通ってゴール地点まで探索する
        return 領域を囲う向きが正しいか(Bool: 正しい=True)
        '''
        position_list = [begin_position]
        log = []
        start_time = time()
        print(start_time)
        while 2 > time() - start_time:
            log += copy.deepcopy(position_list)
            next_position_list = []
            for position in position_list:
                result_lines = self.JudgeLine(line, line_sub, position)
                for result_line in result_lines:
                    pos = self.GetPosition(line, line_sub, result_line)
                    if position in pos:
                        pos.remove(position)
                    if pos in log:
                        pass
                    if self.GetNormal(line_normal, result_line) == self.CreateNormal(position, pos[0]):
                        next_position_list += pos
                    elif len(result_line) == 3:
                        print('33333333333')
                    else:
                        next_position_list += pos
                result_positions = self.IsInLine(line, line_sub, result_lines, end_position)
                if len(result_positions) > 0:
                    # 発見
                    print(time() - start_time)
                    if len(result_positions) == 2:
                        e_pos = self.NearestPosition(position, result_positions[0], result_positions[1])
                    else:
                        e_pos = result_positions[0]
                    nor = self.CreateNormal(position, e_pos)
                    index = end_position.index(e_pos)
                    print(end_normal[index], nor)
                    if end_normal[index] == nor:
                        return False
                    line_infos = self.JudgeLine(line, line_sub, e_pos)
                    for line_info in line_infos:
                        pos_lis = self.GetPosition(line, line_sub, line_info)
                        if e_pos in pos_lis:
                            pos_lis.remove(e_pos)
                            if end_normal[index] == self.CreateNormal(e_pos, pos_lis[0]):
                                return False
                    return True
            if next_position_list == []:
                print('seach position error')
                import sys; sys.exit()

            # 次の点を求める
            for pos in position_list:
                if pos in next_position_list:
                    next_position_list.remove(pos)
            position_list = next_position_list[:]
        
        return None
    
    def Search(self, enemy_position):
        '''
        memo: 引数以外に依存している
        '''
        cross_result = self.JudgeLineCross(self.creation_line, self.creation_line_sub, self.creation_line_normal, self.border_line, self.border_line_sub, enemy_position)
        if cross_result[0]:
            print('cross')
            if cross_result[1]:
                print('normal')
                self.creation_line_normal = self.InversionNormalOne(self.creation_line_normal)
                self.creation[1] = self.InversionNormal(self.creation[1])
            return
        print('not cross',  cross_result[1])

        search_pos_result = self.SearchPosition(self.border_line, self.border_line_sub, self.border_line_normal, cross_result[1], self.creation[0], self.creation[1])
        if search_pos_result == None:
            return 'error'
        if not search_pos_result:
            print('normal')
            self.creation_line_normal = self.InversionNormalOne(self.creation_line_normal)
            self.creation[1] = self.InversionNormal(self.creation[1])
        return

    def CreationUpdate(self, controller, position, pre_position):
        '''
        memo: 引数以外に依存している
        '''
        if controller == [0, 0]:
            return
        if len(self.creation_line_direction) != 0:
            if self.creation_line_direction[-1] == controller:
                if controller == [1, 0]:
                    self.creation_line_sub[1][-1][1] = position[0]
                elif controller == [0, 1]:
                    self.creation_line_sub[0][-1][1] = position[1]
                elif controller == [-1, 0]:
                    self.creation_line_sub[1][-1][0] = position[0]
                elif controller == [0, -1]:
                    self.creation_line_sub[0][-1][0] = position[1]
                return
        self.creation_line_direction.append(controller[:])
        if controller == [1, 0]:
            self.creation_line[1].append(position[1])
            self.creation_line_sub[1].append([pre_position[0], position[0]])
            self.creation_line_normal[1].append(controller[0])
        elif controller == [-1, 0]:
            self.creation_line[1].append(position[1])
            self.creation_line_sub[1].append([position[0], pre_position[0]])
            self.creation_line_normal[1].append(controller[0])
        elif controller == [0, 1]:
            self.creation_line[0].append(position[0])
            self.creation_line_sub[0].append([pre_position[1], position[1]])
            self.creation_line_normal[0].append(controller[1]*-1)
        else:
            self.creation_line[0].append(position[0])
            self.creation_line_sub[0].append([position[1], pre_position[1]])
            self.creation_line_normal[0].append(controller[1]*-1)
        return
    
    def CreationClear(self):
        '''
        creation_line関係の変数を初期化する
        '''
        self.creation_line = [[], []]
        self.creation_line_sub = [[], []]
        self.creation_line_normal = [[], []]
        self.creation_line_direction = []
        self.creation = [[0, 0], [[0, 0], [0, 0]]]
    
    def UpdateAllLine(self):
        '''
        memo: 引数以外に依存している
        '''
        for num in range(2):
            self.all_line[num] += copy.deepcopy(self.creation_line[num])
            self.all_line_sub[num] += copy.deepcopy(self.creation_line_sub[num][:])
    
    def AddBorderLine(self):
        for num in range(2):
            self.border_line[num] += copy.deepcopy(self.creation_line[num])
            self.border_line_sub[num] += copy.deepcopy(self.creation_line_sub[num])
            self.border_line_normal[num] += copy.deepcopy(self.creation_line_normal[num])
        return
    
    def UpdateBorderLine(self):
        '''
        memo: 引数以外に依存している
        '''
        b_lines = self.JudgeLine(self.border_line, self.border_line_sub, self.creation[0][0])
        e_lines = self.JudgeLine(self.border_line, self.border_line_sub, self.creation[0][1])
        sum_line = [i for i in b_lines if i in e_lines]
        if len(sum_line) > 0:
            num, index = sum_line[0]
            min_pos, max_pos = self.GetPosition(self.border_line, self.border_line_sub, sum_line[0])
            if (self.creation[0][0] == min_pos and self.creation[0][1] == min_pos) or (self.creation[0][0] == max_pos and self.creation[0][1] == max_pos):
                pass
            elif (self.creation[0][0] == min_pos and self.creation[0][1] == max_pos) or (self.creation[0][0] == max_pos and self.creation[0][1] == min_pos):
                del self.border_line[num][index]
                del self.border_line_sub[num][index]
                del self.border_line_normal[num][index]
            elif self.creation[0][0] == min_pos or self.creation[0][0] == max_pos:
                [_, pos], [_, normal] = self.creation
                if self.CreateNormal(pos, min_pos) == normal:
                    self.border_line_sub[num][index][1] = pos[normal[1]]
                elif self.CreateNormal(pos, max_pos) == normal:
                    self.border_line_sub[num][index][0] = pos[normal[1]]
            elif self.creation[0][1] == min_pos or self.creation[0][1] == max_pos:
                [pos, _], [normal, _] = self.creation
                if self.CreateNormal(pos, min_pos) == normal:
                    self.border_line_sub[num][index][1] = pos[normal[1]]
                elif self.CreateNormal(pos, max_pos) == normal:
                    self.border_line_sub[num][index][0] = pos[normal[1]]
            else:
                [b_pos, e_pos], [b_n, e_n] = self.creation
                del self.border_line[num][index]
                del self.border_line_sub[num][index]
                normal = self.border_line_normal[num].pop(index)
                if self.CreateNormal(b_pos, min_pos) == b_n:
                    self.border_line[b_n[0]].append(self.creation[0][b_n[0]][b_n[0]])
                    self.border_line_sub[b_n[0]].append([min_pos[b_n[1]], b_pos[b_n[1]]])
                    self.border_line_normal[b_n[0]].append(normal)
                    self.border_line[b_n[0]].append(self.creation[0][b_n[0]][b_n[0]])
                    self.border_line_sub[b_n[0]].append([e_pos[b_n[1]], max_pos[b_n[1]]])
                    self.border_line_normal[b_n[0]].append(normal)
                else:
                    self.border_line[b_n[0]].append(self.creation[0][b_n[0]][b_n[0]])
                    self.border_line_sub[b_n[0]].append([min_pos[b_n[1]], e_pos[b_n[1]]])
                    self.border_line_normal[b_n[0]].append(normal)
                    self.border_line[b_n[0]].append(self.creation[0][b_n[0]][b_n[0]])
                    self.border_line_sub[b_n[0]].append([b_pos[b_n[1]], max_pos[b_n[1]]])
                    self.border_line_normal[b_n[0]].append(normal)
            self.AddBorderLine()
            return

        for be in range(2):
            lines = self.JudgeLine(self.border_line, self.border_line_sub, self.creation[0][be])
            for line_info in lines:
                num, index = line_info
                for pos in self.GetPosition(self.border_line, self.border_line_sub, line_info):
                    if self.CreateNormal(self.creation[0][be], pos) == self.creation[1][be]:
                        if self.creation[1][be] == [1, 0]:
                            self.border_line_sub[num][index][0] = self.creation[0][be][0]
                        elif self.creation[1][be] == [0, 1]:
                            self.border_line_sub[num][index][0] = self.creation[0][be][1]
                        elif self.creation[1][be] == [-1, 0]:
                            self.border_line_sub[num][index][1] = self.creation[0][be][0]
                        elif self.creation[1][be] == [0, -1]:
                            self.border_line_sub[num][index][1] = self.creation[0][be][1]
        self.AddBorderLine()


class App:
    def __init__(self):
        self.Clear()

        # MAX: 213x160
        pyxel.init(210, 160, scale=2, fps=30)
        pyxel.load('assets/main.pyxres')
        pyxel.run(self.Update, self.Draw)
    
    def Clear(self):
        self.controller = Controller()
        self.field = Field(box_size=[10,30, 200,150], player_position=[10,30])

        self.pos = [10, 30]
        self.pre_pos = self.pos[:]

        self.move_scale = 2

        self.player_x = 5
        self.player_y = 5
        self.player_img = 0

        self.enemy_position = [170, 40]
        self.enemy_pre_position = self.enemy_position[:]
        self.enemy_normal = [[-2, 2][ri(0,1)], [-2, 2][ri(0,1)]]
        self.enemy_pre_normal = self.enemy_normal[:]
        self.enemy_size = 9

        self.game_box = (10,20, 200,150)

        # 描画用の枠
        self.x_all_line = [10, 200]
        self.y_all_line = [20, 150]
        self.x_all_line_y = [[20,150], [20,150]]
        self.y_all_line_x = [[10,200], [10,200]]

        # 移動できる枠
        self.x_border_line = [10, 200]
        self.y_border_line = [20, 150]
        self.x_border_line_y = [[20,150], [20,150]]
        self.y_border_line_x = [[10,200], [10,200]]
        self.x_border_line_normal = [1, -1]
        self.y_border_line_normal = [1, -1]

        # [ [進行方向, [法線], [描き始めの位置], [現在の位置]], ...,  [進行方向, [法線], [描き始めの位置], [現在の位置]] ]
        self.draw_line = []

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
                self.enemy_normal = [[-2, 0, 2][ri(-1,1)], [-2, 0, 2][ri(-1,1)]]
            if not 2 > time() - start_time:
                self.game = False
                self.game_message = 'GAMEOVER'
                return
        result = self.field.JudgeLine(self.field.creation_line, self.field.creation_line_sub, self.enemy_position)
        if len(result) > 0:
            self.game = False
            self.game_message = 'GAMEOVER'
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
                    self.field.CreationUpdate(self.controller.stick, self.pos, self.pre_pos)
                    return
            self.pos = self.pre_pos[:]
            self.on_line = True
            return
        elif self.on_line and not self.pre_on_line:
            self.field.creation[0][1] = self.pos[:]
            self.field.creation[1][1] = self.field.ConvertToNormal(self.controller.stick)
            self.field.CreationUpdate(self.controller.stick, self.pos, self.pre_pos)
            if self.field.Search(self.enemy_position) == 'error':
                self.game = False
                self.game_message = 'GAMEOVER'
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
            pyxel.text(85, 90, 'press START', 7)
            return

        pyxel.cls(0)

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
