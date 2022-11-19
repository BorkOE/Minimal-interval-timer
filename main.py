import pygame as pg
from pygame.math import Vector2 as V
from sys import exit
from settings import *

flags = pg.RESIZABLE

def sec(min):
    return min * 60

class Graphics():
    x_marg = 5
    def __init__(self, screen):
        self.screen = screen
        self.surf = pg.Surface((300, 200))
        self.event_image = None # Holds image without timer
        self.image = None # Holds final image
        self.rect = self.surf.get_rect()
        self.reset_pos()

    def reset_pos(self):
        self.rect.topleft = (0,0)
    
    def set_event_graphics(self, event, next_event):
        self.event_image = self.surf.copy()
        if event == warmup_txt:
            self.event_image.fill('yellow')
        elif event == rest_txt:
            self.event_image.fill('green')
        elif event == cooldown_txt:
            self.event_image.fill('yellow')
        else:
            self.event_image.fill('red')
            
        event_text = self.render_text(event, 35)
        next_text = self.render_text(next_txt+':', 18)
        next_event_text = self.render_text(next_event, 20)
        self.event_image.blit(event_text, (self.x_marg,5))
        self.event_image.blit(next_text, (self.x_marg, 70))
        self.event_image.blit(next_event_text, (self.x_marg, 80))

    def handle_event(self, name, time, tot_time, next_event):
        '''Changes graphics according to event'''
        self.set_event_graphics(name, next_event)
        self.update_time(time, tot_time)

    def update_time(self, time, tot_time):
        self.image = self.event_image.copy()
        text_time = self.render_text(self.expand_sec(time), 30)
        text_tot_time = self.render_text(self.expand_sec(tot_time), 16)
        self.image.blit(text_time, (self.x_marg,35))
        self.image.blit(text_tot_time, (self.x_marg,55))

    def expand_sec(self, sec):
        min = int(sec/60)
        sec = sec % 60
        if min:
            out = f'{min} min {sec} sec'
        else:
            out = f'{sec} sec'
        return out

    def render_text(self, text, sz=18, col=(20,20,20), topleft=None, topright=None, center=None):
        font = pg.font.SysFont(None, sz)
        text = font.render(str(text), True, col)   # Av någon anledning försvinner texten med antialiasing ibland
        rect = None
        if topleft:
            rect = text.get_rect(topleft=topleft)
        if topright:
            rect = text.get_rect(topright=topright)
        if center:
            rect = text.get_rect(center=center)
        if rect:
            return text, rect
        else:
            return text

    def update_screen(self):
        self.screen.blit(self.image, self.rect)

    def end_screen(self):
        self.image.fill('black')

class Timer():
    def __init__(self, screen, time_vals):
        self.t_0 = pg.time.get_ticks()
        self.last_sec = 0
        self.total_time_left = sec(time_vals['tot_tid'])
        self.active = False
        self.tt = self.get_timetable(time_vals)
        self.current_event= None
        self.current_event_dict = None
        self.event_list = list(self.tt.keys())
        self.graphics = Graphics(screen)
    
    def get_timetable(self, time_vals):
        disp_tid = sec(time_vals['tot_tid']) - sec(time_vals['uppvärm_tid']) - sec(time_vals['nedvarv_tid'])
        if time_vals['n_spurt']:
            mellan_sprint = int(disp_tid / time_vals['n_spurt'])
        else:
            mellan_sprint = 0 
            time_vals['spurt_tid'] = 0
        tt = {}
        tt.update({warmup_txt:sec(time_vals['uppvärm_tid'])})
        # tt.update({'uppvärmning':3}) # DEBUG

        for i in range(time_vals['n_spurt']):
            sprint = f'{sprint_txt} {i+1}'
            vila = f'{rest_txt} {i+1}'
            tt.update({sprint:time_vals['spurt_tid']})
            tt.update({vila:mellan_sprint - time_vals['spurt_tid']})
        tt.update({cooldown_txt:sec(time_vals['nedvarv_tid'])})
        # tt = {'nedvarv':5}  # DEBUG
        return tt
    
    def run(self):
        if not self.current_event_dict:
            self.next_event()
        self.time_current_event()
        self.graphics.update_screen()

    def next_event(self):
        ''''''
        # TODO: handle end
        if self.event_list:
            self.current_event = self.event_list.pop(0)
            if self.event_list:
                next_event = self.event_list[0]
            else: 
                next_event = end_txt
            self.current_event_dict = {self.current_event:self.tt.pop(self.current_event)}
            self.graphics.handle_event(self.current_event, self.current_event_dict[self.current_event], self.total_time_left, next_event)
        else:
            self.graphics.end_screen()

    def time_current_event(self):
        if self.one_sec():
            self.total_time_left += -1
            time_left = self.current_event_dict[self.current_event]
            if time_left > 0:
                self.current_event_dict[self.current_event] += -1
                self.graphics.update_time(self.current_event_dict[self.current_event], self.total_time_left)
            else:
                self.next_event()

    def one_sec(self):
        delta_t = pg.time.get_ticks() - self.t_0
        sec = int(delta_t / 1000)
        if sec != self.last_sec:
            self.last_sec = sec
            return True
        else:
            return False

class Inputbox():
    w,h = 220,20
    def __init__(self, pos, input_text, default_input=''):
        '''inputbox with text to the left'''
        self.active = False
        self.surf = pg.Surface((self.w,self.h))
        self.surf.fill('white')
        self.rect = self.surf.get_rect(topleft=pos)
        self.input = str(default_input)
        self.render_box()
        self.render_input_text(input_text)
        self.update()

    def render_box(self, col=(20,20,20), width=1):
        sz = (30, self.h)
        self.box_rect = pg.Rect(((self.rect.w-sz[0],0), sz))
        pg.draw.rect(self.surf, col, self.box_rect, width)

    def render_input_text(self, input_text):
        text, text_rect = self.render_text(input_text, topright=self.rect.topright-V(self.rect.topleft)+V(-self.box_rect.w-15,5))
        self.surf.blit(text,text_rect)

    def render_text(self, text, sz=18, col=(20,20,20), topleft=None, topright=None, center=None):
        font = pg.font.SysFont(None, sz)
        text = font.render(str(text), False, col)   # Av någon anledning försvinner texten med antialiasing ibland
        if topleft:
            rect = text.get_rect(topleft=topleft)
        if topright:
            rect = text.get_rect(topright=topright)
        if center:
            rect = text.get_rect(center=center)
        return text, rect
    
    def activate(self):
        self.active = True
        self.render_box(col=(20,250,20))
        self.update()
    
    def deactivate(self):
        self.active = False
        self.render_box()
        self.update()

    def update(self):
        '''Draw text in inputbox'''
        self.image = self.surf.copy()   # Copy of surf without inputbox text
        text, text_rect = self.render_text(self.input, center=self.box_rect.center)
        self.image.blit(text, text_rect)

class Startscreen():
    def __init__(self, screen):
        self.active = False
        self.input_boxes = {}
        self.any_active_box = False
        self.toogle()
    
    def toogle(self, reset=True):
        y_delta = 25
        x_pos = -10
        if self.active:
            self.active = False
            pg.display.set_mode((min_screen_width,min_screen_height), flags)
        else: # Activate
            self.active = True
            pg.display.set_mode((screen_width,screen_height), flags)
            if reset:
                self.input_boxes.update({
                    'tot_tid':Inputbox((x_pos,5+(y_delta*0)), f'{total_time_txt} (min)', default_input=tot_time_def),
                    'uppvärm_tid':Inputbox((x_pos,5+(y_delta*1)), f'{warmup_txt} (min)', default_input=warmup_time_def),
                    'n_spurt':Inputbox((x_pos,5+y_delta*2), n_sprint, default_input=sprint_count_def),
                    'spurt_tid':Inputbox((x_pos,5+(y_delta*3)), f'{sprint_txt} (sec)', default_input=sprint_time_def),
                    'nedvarv_tid':Inputbox((x_pos,5+(y_delta*4)), f'{cooldown_txt} (min)', default_input=cooldown_time_def),
                })

    def startscreen(self, screen, event_list, mouse_pos):
        for box in self.input_boxes.values():
            screen.blit(box.image, box.rect)
    
    def check_click(self, pos):
        hit = False
        for box in self.input_boxes.values():
            if box.rect.collidepoint(pos):
                box.activate()
                hit = True
            else:
                box.deactivate()
        if hit:
            self.any_active_box = True
        else:
            self.any_active_box = False
    
    def mark_next_box(self):
        box_list = list(self.input_boxes.keys())
        box = {k:v for k,v in self.input_boxes.items() if v.active}
        if box:
            idx_active_box = box_list.index(list(box.keys())[0])
            active_box = list(box.values())[0]
            active_box.deactivate()
            if idx_active_box+1 < len(box_list):
                self.input_boxes.get(box_list[idx_active_box+1]).activate()
            else:
                self.input_boxes.get(box_list[0]).activate()

    def type_to_box(self, event_list):
        if self.any_active_box:
            box = [b for b in self.input_boxes.values() if b.active]
            if box:
                box = box[0]
            else:
                return
            for e in event_list:
                if e.type == pg.KEYUP:
                    if e.key in [pg.K_RETURN, pg.K_TAB, pg.K_ESCAPE, pg.K_SPACE]:
                        return
                    elif e.key == pg.K_BACKSPACE:
                        box.input = box.input[:-1]
                    elif e.key == pg.K_DELETE:
                        box.input = ''
                    else:
                        box.input += e.unicode
            box.update()
        
    def get_input_values(self):
        '''Returns values from inputboxes in a dict if valid, else False'''
        time_vals = {}
        for var, box in self.input_boxes.items():
            input_val = box.input.strip()
            if input_val.isdigit():
                val = int(input_val)
            else:
                return False
            time_vals.update({var:val})
        return time_vals
            
class App():
    debug = True
    FRAMERATE = 30

    def __init__(self):
        version = '0.1'
        pg.init()
        self.screen = pg.display.set_mode((screen_width, screen_height), flags)
        self.running = True
        self.fullscreen = False
        pg.display.set_caption(f'Interval training {version}')
        self.clock = pg.time.Clock()
        self.timer = None
        self.startscreen = Startscreen(self.screen)

    def run(self):
        """Run the main event loop."""
        while self.running:
            self.screen.fill('white')
            event_list = pg.event.get()
            mouse_pos = pg.mouse.get_pos()
            
            for e in event_list:
                if e.type == pg.QUIT:
                    exit()
                if e.type == pg.KEYUP:
                    if e.key == pg.K_ESCAPE and not self.startscreen.active:
                        self.startscreen.toogle(reset=False)
                        self.timer = None
                    if self.startscreen.active:
                        if e.key == pg.K_RETURN: 
                            self.startscreen.toogle()
                        if e.key == pg.K_TAB:
                            self.startscreen.mark_next_box()
                    if self.startscreen.active:
                        self.startscreen.type_to_box(event_list)
                if e.type == pg.MOUSEBUTTONUP and e.button == 1:
                    if self.startscreen.active:
                        self.startscreen.check_click(mouse_pos)

            if self.startscreen.active:
                '''Draw startscreen'''
                self.startscreen.startscreen(self.screen, event_list, mouse_pos)
            else:
                '''Draw timer''' # TODO: draw timer 
                # Try to get input values, if fail..
                input_vals = self.startscreen.get_input_values()
                if not input_vals:
                    self.startscreen.toogle(reset=False)
                else:
                    if not self.timer:
                        self.timer = Timer(self.screen, input_vals)
                    self.timer.run()

            pg.display.update()
            self.clock.tick(self.FRAMERATE) 

        pg.quit()

if __name__ == '__main__':
    App().run()


    
