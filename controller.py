# coding: utf-8

import pyxel

class Controller:
    def __init__(self, keybord=False):
        self.keyboad = keybord
        if not self.keyboad:
            self.JoystickInit()
        
        self.joystick_x = 0
        self.joystick_y = 0

        self.stick = [0, 0]
        self.stick_rollover = [0, 0]

        self.down_list = []
        self.up_list   = []
        self.button_list = []
    
    def JoystickInit(self):
        import pygame
        from pygame import locals
        pygame.init()
        if pygame.joystick.get_count() == 0:
            print('controller not found')
            self.keyboad = True
        else:
            self.keyboad = False
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
    
    def GetJoystick(self):
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
    
    def GetKeybord(self):
        self.joystick_x = 0
        self.joystick_y = 0
        if pyxel.btn(pyxel.KEY_W):
            self.joystick_y -= 1
        if pyxel.btn(pyxel.KEY_A):
            self.joystick_x -= 1
        if pyxel.btn(pyxel.KEY_S):
            self.joystick_y += 1
        if pyxel.btn(pyxel.KEY_D):
            self.joystick_x += 1

        if pyxel.btnp(pyxel.KEY_SPACE):
            self.up_list.append(9)
        if pyxel.btnr(pyxel.KEY_SPACE):
            self.down_list.append(9)

    def Update(self):
        self.down_list.clear()
        self.up_list.clear()

        if self.keyboad:
            self.GetKeybord()
        else:
            self.GetJoystick()
        
        for down in self.down_list:
            self.button_list.append(down)
        for up in self.up_list:
            try:
                self.button_list.remove(up)
            except:
                pass

        self.stick_rollover = [self.joystick_x, self.joystick_y]
        if self.stick_rollover == [0, 0]:
            self.stick = [0, 0]
        elif self.stick != [0, 0] and self.stick_rollover[0] != 0 and self.stick_rollover[1] != 0:
            pass
        elif self.stick_rollover[0] != 0:
            self.stick = [self.stick_rollover[0], 0]
        else:
            self.stick = [0, self.stick_rollover[1]]
