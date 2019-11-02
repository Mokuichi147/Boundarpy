# coding: utf-8

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
    
    def CreateNormal(self, begin_position, end_position):
        '''
        2点間の方向を返す
        '''
        nx = end_position[0] - begin_position[0]
        ny = end_position[1] - begin_position[1]
        nx = 0 if nx == 0 else 1 if nx > 0 else -1
        ny = 0 if ny == 0 else 1 if ny > 0 else -1
        return [nx, ny]
    
    def InversionNormal(self, normal):
        '''
        向きを反転させる
        '''
        for num in range(2):
            if len(normal[num]) > 0:
                for i in range(len(normal[num])):
                    normal[num][i] *= -1
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
    
    def SearchPosition(self, line, line_sub, line_normal, begin_position, end_position, end_normal):
        '''
        入力された座標が線上を通ってゴール地点まで探索する
        return 領域を囲う向きが正しいか(Bool: 正しい=True)
        '''
        position_list = [begin_position]
        pre_lines = []
        while True:
            for position in position_list:
                result_lines = self.JudgeLine(line, line_sub, position)
                result_positions = self.IsInLine(line, line_sub, result_lines, end_position)
                if len(result_positions) > 0:
                    # 発見
                    for e_pos in result_positions:
                        nor = self.CreateNormal(position, e_pos)
                        index = end_position.index(e_pos)
                        if end_normal[index] == nor:
                            return False
                    return True

            # 次の点を線から求める
            next_position_list = []
            for i in range(len(result_lines)):
                xy = result_lines[i][0]
                index = result_lines[i][1]
                for j in range(2):
                    position = [0, 0]
                    position[xy] = line[xy][index]
                    position[1-xy] = line_sub[xy][index][j]
                    if not position in position_list:
                        next_position_list.append(position[:])
            position_list = next_position_list[:]
    
    def Search(self, enemy_position):
        '''
        memo: 引数以外に依存している
        '''
        cross_result = self.JudgeLineCross(self.creation_line, self.creation_line_sub, self.creation_line_normal, self.border_line, self.border_line_sub, enemy_position)
        if cross_result[0]:
            if cross_result[1]:
                self.creation_line_normal = self.InversionNormal(self.creation_line_normal)
            return

        search_pos_result = self.SearchPosition(self.border_line, self.border_line_sub, self.border_line_normal, cross_result[1], self.creation[0], self.creation[1])
        if not search_pos_result:
            self.creation_line_normal = self.InversionNormal(self.creation_line_normal)
        return

    def CreationUpdate(self, controller, position, pre_position):
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
        # 作成用: main:[[x],[y]] sub:[[x_y],[y_x]] normal:[[x_n],[y_n]]  direction:[[1,0], [0,1], ...] creation:[[b_pos, e_pos], [b_normal, e_normal]]
        self.creation_line = [[], []]
        self.creation_line_sub = [[], []]
        self.creation_line_normal = [[], []]
        self.creation_line_direction = []
        self.creation = [[0, 0], [[0, 0], [0, 0]]]


class App:
    def __init__(self):
        self.controller = Controller()
        self.field = Field(box_size=[10,20, 200,150], player_position=[10,20])

        self.pos = [10, 20]
        self.pre_pos = self.pos[:]
        self.x = 10
        self.y = 20
        self.pre_x = self.x
        self.pre_y = self.y

        self.move_scale = 2

        self.player_x = 5
        self.player_y = 5
        self.player_img = 0

        self.enemy_position = [170, 40]
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

        # MAX: 213x160
        pyxel.init(210, 160, scale=2, fps=30)
        pyxel.load('assets/main.pyxres')
        pyxel.run(self.Update, self.Draw)

    def JudgeLine(self):
        self.pre_on_line = self.on_line
        self.on_line = False
        for x_index in [i for i, x in enumerate(self.x_border_line) if x == self.x]:
            if self.x_border_line_y[x_index][0] <= self.y <= self.x_border_line_y[x_index][1]:
                self.on_line = True
                self.pre_on_line_info = self.on_line_info
                self.on_line_info = [0, x_index]
        for y_index in [i for i, y in enumerate(self.y_border_line) if y == self.y]:
            if self.y_border_line_x[y_index][0] <= self.x <= self.y_border_line_x[y_index][1]:
                self.on_line = True
                self.pre_on_line_info = self.on_line_info
                self.on_line_info = [1, y_index]

    def JudgeBorderLine(self, position):
        result_list = []
        for x_index in [i for i, x in enumerate(self.x_border_line) if x == position[0]]:
            if self.x_border_line_y[x_index][0] <= position[1] <= self.x_border_line_y[x_index][1]:
                result_list.append([0, x_index])
        for y_index in [i for i, y in enumerate(self.y_border_line) if y == position[1]]:
            if self.y_border_line_x[y_index][0] <= position[0] <= self.y_border_line_x[y_index][1]:
                result_list.append([1, y_index])
        # 0:縦 1:横
        return result_list

    def JudgeDrawLine(self, position, all_check=True, normal=False):
        result_list = []
        if all_check:
            count_list = [i for i in range(len(self.draw_line))]
        else:
            count_list = [0, -1]

        for i in count_list:
            one, n, [sx,sy], [ex,ey] = self.draw_line[i]
            min_x = sx if one != [-1, 0] else ex
            max_x = ex if one != [-1, 0] else sx
            min_y = sy if one != [0, -1] else ey
            max_y = ey if one != [0, -1] else sy
            if normal:
                min_x += n[0]
                max_x += n[0]
                min_y += n[1]
                max_y += n[1]
            if min_x <= position[0] <= max_x and min_y <= position[1] <= max_y:
                result_list.append(i)
        return result_list

    def TargetVector(self, start, goal, num=False):
        wx = goal[0] - start[0]
        wy = goal[1] - start[1]

        if wx >= 0 and wy <= 0:
            # 右上
            weight = [1, 4, 2, 3] if wx > abs(wy) else [4, 1, 3, 2]
        elif wx >= 0 and wy >= 0:
            # 右下
            weight = [1, 2, 4, 3] if wx > wy else [2, 1, 3, 4]
        elif wx <= 0 and wy >= 0:
            # 左下
            weight = [3, 2, 4, 1] if abs(wx) > wy else [2, 3, 1, 4]
        else:
            # 左上
            weight = [3, 4, 2, 1] if abs(wx) > abs(wy) else [4, 3, 1, 2]
        if num:
            return weight

        result_list = []
        for w in weight:
            if w == 1:
                result_list.append([1, 0])
            elif w == 2:
                result_list.append([0, 1])
            elif w == 3:
                result_list.append([-1, 0])
            else:
                result_list.append([0, -1])
        return result_list

    def ReDrawListNormal(self):
        for i in range(len(self.draw_line)):
            _, [nx, ny], _, _ = self.draw_line[i]
            self.draw_line[i][1] = [nx * -1, ny * -1]


    def Update(self):
        self.controller.Update()

        self.pre_pos = self.pos[:]
        self.pos[0] += self.controller.stick[0] * self.move_scale
        self.pos[1] += self.controller.stick[1] * self.move_scale

        result = self.field.JudgeLine(self.field.creation_line, self.field.creation_line_sub, self.pos)
        #result = self.JudgeDrawLine([self.x, self.y])
        if len(result) > 0:
            self.pos = self.pre_pos[:]
            return

        self.pre_on_line = self.on_line
        result = self.field.JudgeLine(self.field.border_line, self.field.border_line_sub, self.pos)
        if len(result) > 0:
            self.on_line = True
        else:
            self.on_line = False
        #self.JudgeLine()

        if not self.on_line and self.pre_on_line:
            # 領域外に出たとき
            result = self.field.JudgeLine(self.field.border_line, self.field.border_line_sub, self.pre_pos)
            for num, index in result:
                normal = [0, 0]
                normal[num] = self.field.border_line_normal[num][index]
                if normal == self.controller.stick:
                    self.field.creation[0][0] = self.pos[:]
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
            self.field.Search(self.enemy_position)
            self.field.CreationClear()
        elif not self.on_line and not self.pre_on_line:
            self.field.CreationUpdate(self.controller.stick, self.pos, self.pre_pos)

        """
        if self.on_line and not self.pre_on_line:
            ''' 枠に入ってきたとき '''
            self.draw_line[-1][3] = [self.x, self.y]
            # 向きチェック
            count = 0
            min_count = 0
            min_num = self.game_box[2] + self.game_box[3]
            for _, _, _, [ex,ey] in self.draw_line:
                if min_num > abs(self.enemy_position[0]-ex) + abs(self.enemy_position[1]-ey):
                    min_num = abs(self.enemy_position[0]-ex) + abs(self.enemy_position[1]-ey)
                    min_count = count
                count += 1
            one, n, [sx,sy], [ex,ey] = self.draw_line[min_count]

            pos = self.enemy_position[:]
            pre_pos = pos[:]
            pos_info = []
            pre_pos_info = []
            goal = False
            move = self.TargetVector(pos, [ex,ey])
            draw_line_all_check = True
            count = 0
            while not goal:
                count += 1
                # posがdraw_line上か
                result = self.JudgeDrawLine(pos, all_check=draw_line_all_check)
                if len(result) > 0:
                    # pre_posの位置確認
                    pre_result = self.JudgeDrawLine(pre_pos, normal=True)
                    print(self.draw_line)
                    if len(pre_result) == 0:
                        # normalを反転させる
                        print('normalを反転させたよ')
                        self.ReDrawListNormal()
                    print('finish', count)
                    print(self.draw_line)
                    goal = True
                    continue

                # border_line上か
                result = self.JudgeBorderLine(pos)
                if len(result) > 0:
                    pre_result = self.JudgeBorderLine(pre_pos)
                    if len(pre_result) == 0 or len(result) > 1:
                        draw_line_all_check = False
                        # 進行方向を決める
                        if len(result) > 1 and len(pre_result) > 0:
                            result.remove(pre_result[0])
                        move = self.TargetVector(pos, [ex,ey])
                        if result[0][0] == 0 and move[0][1] == 0:
                            move = [move[1], move[2]]
                        elif result[0][0] == 1 and move[0][0] == 0:
                            move = [move[1], move[2]]
                # pos Update
                pre_pos = pos[:]
                pos = [pos[0] + move[0][0], pos[1] + move[0][1]]

            # 新しい枠の作成
            s_result = self.JudgeBorderLine(self.draw_line[0][2])
            e_result = self.JudgeBorderLine(self.draw_line[-1][3])
            result_total = [i for i in s_result if i in e_result]
            # s:self.draw_line[0][2]  g:self.draw_line[-1][3]
            if len(result_total) > 0:
                # スタートとゴールが同じ枠からだった場合
                print('同じ')
                if result_total[0][0] == 0:
                    # xが変わらない場合
                    line_x = self.x_border_line[result_total[0][1]]
                    line_y_min, line_y_max = self.x_border_line_y[result_total[0][1]]
                    line_y = []
                    if self.draw_line[0][1][1] == 1:
                        line_y.append([self.draw_line[0][2][1], line_y_max])
                        line_y.append([line_y_min, self.draw_line[-1][3][1]])
                    else:
                        line_y.append([self.draw_line[-1][3][1], line_y_max])
                        line_y.append([line_y_min, self.draw_line[0][2][1]])
                    del self.x_border_line[result_total[0][1]]
                    del self.x_border_line_y[result_total[0][1]]
                    line_normal = self.x_border_line_normal.pop(result_total[0][1])
                    self.x_border_line += [line_x, line_x]
                    self.x_border_line_y += line_y[:]
                    self.x_border_line_normal += [line_normal, line_normal]
                else:
                    # yが変わらない場合
                    line_y = self.y_border_line[result_total[0][1]]
                    line_x_min, line_x_max = self.y_border_line_x[result_total[0][1]]
                    line_x = []
                    if self.draw_line[0][1][0] == 1:
                        line_x.append([self.draw_line[0][2][0], line_x_max])
                        line_x.append([line_x_min, self.draw_line[-1][3][0]])
                    else:
                        line_x.append([self.draw_line[-1][3][0], line_x_max])
                        line_x.append([line_x_min, self.draw_line[0][2][0]])
                    del self.y_border_line[result_total[0][1]]
                    del self.y_border_line_x[result_total[0][1]]
                    line_normal = self.y_border_line_normal.pop(result_total[0][1])
                    self.y_border_line += [line_y, line_y]
                    self.y_border_line_x += line_x[:]
                    self.y_border_line_normal += [line_normal, line_normal]
            else:
                print('違う')
                if len(s_result) == 1:
                    if s_result[0][0] == 0:
                        line_x = self.x_border_line[s_result[0][1]]
                        min_y, max_y = self.x_border_line_y[s_result[0][1]]
                        if self.draw_line[0][1][1] == 1:
                            line_y = [self.draw_line[0][2][1], max_y]
                            end_position = [line_x, min_y]
                        else:
                            line_y = [min_y, self.draw_line[0][2][1]]
                            end_position = [line_x, max_y]
                        self.x_border_line_y[s_result[0][1]] = line_y
                    else:
                        line_y = self.y_border_line[s_result[0][1]]
                        min_x, max_x = self.y_border_line_x[s_result[0][1]]
                        if self.draw_line[0][1][0] == 1:
                            line_x = [max_x, self.draw_line[0][2][0]]
                            end_position = [min_x, line_y]
                        else:
                            line_x = [min_x, self.draw_line[0][2][0]]
                            end_position = [max_x, line_y]
                        self.y_border_line_x[s_result[0][1]] = line_x

                if len(e_result) == 1:
                    if e_result[0][0] == 0:
                        line_x = self.x_border_line[e_result[0][1]]
                        min_y, max_y = self.x_border_line_y[e_result[0][1]]
                        if self.draw_line[-1][1][1] == 1:
                            self.x_border_line_y[e_result[0][1]] = [self.draw_line[-1][3][1], max_y]
                        else:
                            self.x_border_line_y[e_result[0][1]] = [self.draw_line[-1][3][1], min_y]
                    else:
                        line_y = self.y_border_line[e_result[0][1]]
                        min_x, max_x = self.y_border_line_x[e_result[0][1]]
                        if self.draw_line[-1][1][0] == 1:
                            self.y_border_line_x[e_result[0][1]] = [max_x, self.draw_line[-1][3][0]]
                        else:
                            self.y_border_line_x[e_result[0][1]] = [min_x, self.draw_line[-1][3][0]]

            for normal, [nx,ny], [sx,sy], [ex,ey] in self.draw_line:
                if normal == [0, 1] or normal == [0, -1]:
                    self.x_border_line.append(sx)
                    self.x_border_line_y.append([sy, ey] if sy < ey else [ey, sy])
                    self.x_border_line_normal.append(nx)
                    self.x_all_line.append(sx)
                    self.x_all_line_y.append([sy, ey] if sy < ey else [ey, sy])
                else:
                    self.y_border_line.append(sy)
                    self.y_border_line_x.append([sx, ex] if sx < ex else [ex, sx])
                    self.y_border_line_normal.append(ny)
                    self.y_all_line.append(sy)
                    self.y_all_line_x.append([sx, ex] if sx < ex else [ex, sx])

            # 領域の塗りつぶしと割合の計算

            self.draw_line.clear()
        elif not self.on_line and self.pre_on_line:
            ''' 枠から出たとき '''
            # 枠の外側なら移動させない
            if self.on_line_info[0] == 0:
                if self.x_border_line[self.on_line_info[1]] + self.x_border_line_normal[self.on_line_info[1]] * self.move_scale != self.x:
                    self.x = self.pre_x
                    self.y = self.pre_y
                    self.on_line = True
                    return
            else:
                if self.y_border_line[self.on_line_info[1]] + self.y_border_line_normal[self.on_line_info[1]] * self.move_scale != self.y:
                    self.x = self.pre_x
                    self.y = self.pre_y
                    self.on_line = True
                    return
            # 線を引くための情報を追加する
            self.draw_line.append([self.controller.stick, self.field.ConvertToNormal(self.controller.stick), [self.pre_x,self.pre_y], [self.x,self.y]])
        
        if self.on_line:
            return
        
        if self.draw_line[-1][0] == self.controller.stick:
            self.draw_line[-1][3] = [self.x, self.y]
        elif self.controller.stick != [0, 0]:
            self.draw_line.append([self.controller.stick, self.field.ConvertToNormal(self.controller.stick), [self.pre_x,self.pre_y], [self.x,self.y]])
        """


    def Draw(self):
        pyxel.cls(0)

        # 領域の描画

        # 現在描き途中の線
        for index in range(len(self.field.creation_line[0])):
            pyxel.line(self.field.creation_line[0][index], self.field.creation_line_sub[0][index][0], self.field.creation_line[0][index], self.field.creation_line_sub[0][index][1], self.line_color_accent)
        for index in range(len(self.field.creation_line[1])):
            pyxel.line(self.field.creation_line_sub[1][index][0], self.field.creation_line[1][index], self.field.creation_line_sub[1][index][1], self.field.creation_line[1][index], self.line_color_accent)

        # すべての線
        for x_count in range(len(self.x_all_line)):
            pyxel.line(self.x_all_line[x_count], self.x_all_line_y[x_count][0], self.x_all_line[x_count], self.x_all_line_y[x_count][1], self.line_color_no_accent)
        for y_count in range(len(self.y_all_line)):
            pyxel.line(self.y_all_line_x[y_count][0], self.y_all_line[y_count], self.y_all_line_x[y_count][1], self.y_all_line[y_count], self.line_color_no_accent)

        # 枠
        for x_count in range(len(self.x_border_line)):
            pyxel.line(self.x_border_line[x_count], self.x_border_line_y[x_count][0], self.x_border_line[x_count], self.x_border_line_y[x_count][1], self.line_color)
        for y_count in range(len(self.y_border_line)):
            pyxel.line(self.y_border_line_x[y_count][0], self.y_border_line[y_count], self.y_border_line_x[y_count][1], self.y_border_line[y_count], self.line_color)

        # ゲームの枠
        #pyxel.rectb(self.game_box[0], self.game_box[1], self.game_box[2] - self.game_box[0] + 1, self.game_box[3] - self.game_box[1] + 1, self.line_color)

        # プレイヤー
        if len(self.controller.button_list) > 0:
            self.player_img = 8 + self.controller.button_list[0] * 8 if self.controller.button_list[0] < 4 else 0
        else:
            self.player_img = 0
        pyxel.blt(self.pos[0] -2, self.pos[1] -2, 0, self.player_img, 0, self.player_x, self.player_y, 0)

        # 敵
        pyxel.pix(self.enemy_position[0], self.enemy_position[1], 15)

if __name__=='__main__':
    App()
