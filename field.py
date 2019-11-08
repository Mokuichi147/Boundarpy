# coding: utf-8

import copy
from time import time

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
            if len(line[num]) == 0:
                continue
            for index in [c for c,l in enumerate(line[num]) if l == position[num]]:
                line_min = line_sub[num][index][0]
                line_max = line_sub[num][index][1]
                if line_min <= position[1-num] <= line_max:
                    result_list.append([num, index])
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
        if result == 'error':
            import sys; sys.exit()

        if len(result) != 0:
            normal = result[0]
            pos = result[1]
            result_ = self.JudgeLine(creation, creation_sub, pos)
            for num, index in result_:
                if creation_normal[num][index] == normal[num]:
                    return [True, True]
            return [True, False]
        return [False, b_cross[0]]
    
    def JudgePosition(self, line, line_sub, position, line_normal=None, normal_scale=1):
        '''
        頂点と重なっている線の端の情報を返す
        return [[normal, position, line_info]]
        '''
        result_list = []
        line_info_list = self.JudgeLine(line, line_sub, position, line_normal, normal_scale)
        for line_info in line_info_list:
            min_pos, max_pos = self.GetPosition(line_info)
            pos = min_pos[:] if position == max_pos else max_pos[:]
            normal = self.CreateNormal(position, pos)
            result_list.append([normal[:], pos[:], line_info[:]])
        return result_list

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
        for i in range(4):
            if len(border_cross[i]) == 0:
                print('[ error ]', 'cross border line not found')
                print('[ error ]', border_cross)
                return 'error'

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

    def IsInLine(self, line, line_sub, line_info, position_list):
        '''
        入力された線上に点があるかを返す
        return [[position](点の位置), ...]
        '''
        result_list = []
        for pos in position_list:
            for xy, index in line_info:
                if line[xy][index] == pos[xy]:
                    if line_sub[xy][index][0] <= pos[1-xy] <= line_sub[xy][index][1]:
                        result_list.append(pos)
        return result_list
    
    def NearestPosition(self, position, position_0, position_1):
        '''
        近いほうの点を返す
        '''
        p0 = abs(position_0[0] - position[0]) + abs(position_0[1] - position[1])
        p1 = abs(position_1[0] - position[0]) + abs(position_1[1] - position[1])
        if p0 <= p1:
            return position_0
        else:
            return position_1
    
    def CreateNormalClockwise(self, normal, anti=False):
        '''
        時計回り、反時計回りと内側の向きの情報から優先順位と正しい向きを返す
        return [direction_list, normal_list]
        '''
        invertion = -1 if anti else 1

        if normal == [1, 0]:
            return [[[1,0], [0,-1*invertion], [-1,0]], [[0,1*invertion], [1,0], [0,-1*invertion]]]
        elif normal == [0, 1]:
            return [[[0,1], [1*invertion,0], [0,-1]], [[-1*invertion,0], [0,1], [1*invertion,0]]]
        elif normal == [-1, 0]:
            return [[[-1,0], [0,1*invertion], [1,0]], [[0,-1*invertion], [-1,0], [0,1*invertion]]]
        elif normal == [0, -1]:
            return [[[0,-1], [-1*invertion,0], [0,1]], [[1*invertion,0], [0,-1], [-1*invertion,0]]]
    
    def SearchClockwise(self, line, line_sub, line_normal, begin_position, begin_normal, end_position, end_normal, anti=False):
        '''
        時計回りと反時計回りの２方向から調べる
        return [領域を囲う向きが正しいか(Bool: 正しい=True), [line_info, ...]]
        '''
        normal = begin_normal
        position = begin_position
        pre_position = position[:]

        result_list = []
        start_time = time()
        while 2 < time() - start_time:
            direction_list, normal_list = self.CreateNormalClockwise(normal, anti=anti)
            judge_line_result = self.JudgeLine(line, line_sub, position)
            judge_line_direction = []
            for judge in judge_line_result:
                min_pos, max_pos = self.GetPosition(line, line_sub, judge)
                pos = max_pos if position == min_pos else min_pos
                judge_line_direction.append(self.CreateNormal(position, pos))
            for i in range(3):
                for index in range(len(judge_line_direction)):
                    if direction_list[i] == judge_line_direction[index]:
                        if normal_list[i] == self.GetNormal(line_normal, judge):
                            pre_position = position[:]
                            position = pos[:]
                            result_list.append(judge_line_result[index][:])
                        else:
                            return [False, result_list]
                        break
            is_in_line = self.IsInLine(line, line_sub, result_list[-1], end_position)
            if len(is_in_line) == 1:
                # 領域判定
                return
            elif len(is_in_line) == 2:
                nearest_pos = self.NearestPosition(pre_position, is_in_line[0], is_in_line[1])
                # 領域判定
                return
        return 'error'

    
    def SearchPositionOnLine(self, line, line_sub, line_normal, begin_position, begin_normal, end_position, end_normal):
        '''
        入力された座標が線上を通ってゴール地点まで探索する
        return [反転させるかどうか, ([line_info, ...])]
        '''
        begin_result = self.JudgeLine(line, line_sub, begin_position)
        for b_result in begin_result:
            line_result = self.IsInLine(line, line_sub, b_result, end_position)
            if len(line_result) > 0:
                # 初めの線に目的地があった場合
                return
        
        line_info_list = [copy.deepcopy(begin_result)]

        if len(begin_result) == 1:
            if begin_normal == [1, 0] or begin_normal == [0, -1]:
                anticlockwise, clockwise = self.GetPosition(line, line_sub, begin_result[0])
            else:
                clockwise, anticlockwise = self.GetPosition(line, line_sub, begin_result[0])
            normal = self.GetNormal(line_normal, begin_result[0])
            anticlockwise_result = self.SearchClockwise(line, line_sub, line_normal, anticlockwise, normal, end_position, end_normal, anti=True)
            clockwise_result = self.SearchClockwise(line, line_sub, line_normal, clockwise, normal, end_position, end_normal)
        elif len(begin_result) == 2:
            pass
        else:
            return 'error'

    def SearchPosition(self, line, line_sub, line_normal, begin_position, end_position, end_normal):
        '''
        入力された座標が線上を通ってゴール地点まで探索する(旧)
        return 領域を囲う向きが正しいか(Bool: 正しい=True)
        '''
        position_list = [begin_position]
        log = []
        start_time = time()
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
                        continue
                    if self.GetNormal(line_normal, result_line) == self.CreateNormal(position, pos[0]):
                        next_position_list += pos
                    else:
                        next_position_list += pos
                result_positions = self.IsInLine(line, line_sub, result_lines, end_position)
                if len(result_positions) > 0:
                    # 発見
                    print(log)
                    print(f'[   ,   ] {time() - start_time:.5f}')
                    if len(result_positions) == 2:
                        e_pos = self.NearestPosition(position, result_positions[0], result_positions[1])
                    else:
                        e_pos = result_positions[0]
                    nor = self.CreateNormal(position, e_pos)
                    index = end_position.index(e_pos)
                    print('[   ,   ]', end_normal[index], nor)
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
                print('[ error ]seach position error')
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
            print('[   ,   ] cross')
            if cross_result[1]:
                print('[   ,   ] normal')
                self.creation_line_normal = self.InversionNormalOne(self.creation_line_normal)
                self.creation[1] = self.InversionNormal(self.creation[1])
            return
        print(f'[{cross_result[1][0]:>3},{cross_result[1][1]:>3}]not cross')

        search_pos_result = self.SearchPosition(self.border_line, self.border_line_sub, self.border_line_normal, cross_result[1], self.creation[0], self.creation[1])
        if search_pos_result == None:
            return 'error'
        if not search_pos_result:
            print('[   ,   ] normal')
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

        if len(self.creation_line_direction) == 0:
            print(f'[{pre_position[0]:>3},{pre_position[1]:>3}]draw begin {controller}')
        else:
            print(f'[{pre_position[0]:>3},{pre_position[1]:>3}] turn {controller}')

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
