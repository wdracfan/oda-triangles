import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line, Triangle
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

import random
random.seed(596)

# размеры окна
w = Window.width
h = Window.height

# координаты вершин треугольников
lower_coords = [w * 14 / 15, w / 15, w / 15, w / 15, w * 14 / 15, w * 14 / 15]
upper_coords = [w / 15, h - w / 15, w * 14 / 15, h - w / 15, w / 15, h - w / 15 - w * 13 / 15]

# радиус жирной точки на отрезке
radius = 20

layout = None

lower_triangle = None
upper_triangle = None

restart_button = None

import math

def distance(ax, ay, bx, by):
    return math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)

# вершина
class Vertex:
    def __init__(self, x, y, weight = 1):
        self.x = x
        self.y = y
        self.weight = weight

    def equals(self, other):
        EPS = 10e-8

        ox = lower_coords[0] # координаты прямого угла нижнего треугольника
        oy = lower_coords[1]
        ux = upper_coords[0] # координаты прямого угла верхнего треугольника
        uy = upper_coords[1] 

        # отрезки лежат в одном треугольнике
        if abs(self.x - other.x) < EPS and abs(self.y - other.y) < EPS:
            return True
        
        # отрезки лежат в разных треугольниках
        if abs((ox - self.x) - (other.x - ux)) < EPS and abs((self.y - oy) - (uy - other.y)) < EPS:
            return True
        
        return False
    
# отрезок
class Segment(Widget):
    def __init__(self, a: Vertex, b: Vertex, triangle, neighbours = [], active = True):
        # neighbours - список противолежащих вершин (либо одна, либо две)
        super(Segment, self).__init__()

        self.a = a
        self.b = b
        self.triangle = triangle
        self.neighbours = neighbours
        self.active = active
        
        self.color = (1, 1, 1, 1)
        
        self.centre = [
                (self.a.x * self.a.weight + self.b.x * self.b.weight) / (self.a.weight + self.b.weight),
                (self.a.y * self.a.weight + self.b.y * self.b.weight) / (self.a.weight + self.b.weight)
        ]

        self.draw()

    def equals(self, other):
        return (self.a.equals(other.a) and self.b.equals(other.b)) or (self.a.equals(other.b) and self.b.equals(other.a))

    def draw(self):
        with self.canvas:
            Color(*self.color)
            Line(points=[self.a.x, self.a.y, self.b.x, self.b.y], width=3.5)
            Ellipse(pos=(self.centre[0] - radius, self.centre[1] - radius), size=(2 * radius, 2 * radius))

    def split(self):
        # убираем текущий отрезок
        layout.remove_widget(self)
        self.active = False

        centre_vertex = Vertex(self.centre[0], self.centre[1], self.a.weight + self.b.weight)

        # добавляем два новых - куски старого
        one = Segment(self.a, centre_vertex, self.triangle, list(self.neighbours))
        two = Segment(centre_vertex, self.b, self.triangle, list(self.neighbours))
        layout.add_widget(one)
        layout.add_widget(two)
        self.triangle.segments.append(one)
        self.triangle.segments.append(two)

        # соединяем "середину" разбитого отрезка с противолежащими вершинами
        for vertex in self.neighbours:
            new = Segment(centre_vertex, vertex, self.triangle, [self.a, self.b])
            layout.add_widget(new)
            self.triangle.segments.append(new)

            segm = self.triangle.get_segment(self.a, vertex)
            if segm:
                if segm.neighbours[0] == self.b:
                    segm.neighbours[0] = centre_vertex
                elif len(segm.neighbours) > 1:
                    segm.neighbours[1] = centre_vertex

            segm = self.triangle.get_segment(self.b, vertex)
            if segm:
                if segm.neighbours[0] == self.a:
                    segm.neighbours[0] = centre_vertex
                elif len(segm.neighbours) > 1:
                    segm.neighbours[1] = centre_vertex

    def on_touch_down(self, touch):
        if distance(touch.pos[0], touch.pos[1], self.centre[0], self.centre[1]) <= radius:
            self.split()
            check_win()

# треугольник
class MyTriangle(Widget):
    def __init__ (self, ax, ay, bx, by, cx, cy):
        super(MyTriangle, self).__init__()
        
        self.ax = ax
        self.ay = ay
        self.bx = bx
        self.by = by
        self.cx = cx
        self.cy = cy

        # создаём вершины
        vertex1 = Vertex(ax, ay, 1)
        vertex2 = Vertex(bx, by, 1)
        vertex3 = Vertex(cx, cy, 1)

        # создаём отрезки
        segment1 = Segment(vertex1, vertex2, self)
        segment2 = Segment(vertex1, vertex3, self)
        segment3 = Segment(vertex2, vertex3, self)

        # указываем противолежащие вершины для каждого отрезка
        segment1.neighbours = [vertex3]
        segment2.neighbours = [vertex2]
        segment3.neighbours = [vertex1]

        # храним отрезки
        self.segments = [segment1, segment2, segment3]

        # добавляем на холст
        layout.add_widget(self)

        for i in self.segments:
            layout.add_widget(i)

        # генерируем подразбиения
        self.generate_state()

        # отрисовываем
        self.draw()

    def equals(self, other):
        # выделяем только активные (неразбитые) отрезки
        active = [i for i in self.segments if i.active]
        other_active = [i for i in other.segments if i.active]

        return_false = False

        # ищем соответствия для отрезков одного треугольника
        for i in active:
            found = False
            for j in other_active:
                if i.equals(j):
                    found = True
                    break
            if found:
                i.color = (1, 1, 1, 1) # если нашли, красим в белый
                i.draw()
            if not found:
                i.color = (1, 0, 0, 1) # если не нашли, красим в красный
                i.draw()
                return_false = True

        # ищем соответствия для отрезков другого треугольника
        for j in other_active:
            found = False
            for i in active:
                if i.equals(j):
                    found = True
                    break
            if found:
                j.color = (1, 1, 1, 1)
                j.draw()
            if not found:
                j.color = (1, 0, 0, 1)
                j.draw()
        
        if return_false:
            return False
        
        return True

    def draw(self):
        with self.canvas:
            Color(0.01, 0.2, 0.05, 0.5)
            Triangle(points=[self.ax, self.ay, self.bx, self.by, self.cx, self.cy])

    def get_segment(self, a, b):
        for s in self.segments:
            if (s.a == a and s.b == b or s.a == b and s.b == a):
                return s
        return None
    
    def generate_state(self):
        number_of_steps = random.randint(1, 3)
        for _ in range(number_of_steps):
            active_segments = [i for i in self.segments if i.active]
            segment_to_split = active_segments[random.randint(0, len(active_segments) - 1)]
            segment_to_split.split()

def check_win(with_button=True):
    global lower_triangle
    global upper_triangle
    
    if lower_triangle.equals(upper_triangle):
        if not with_button: # для случая, если сразу сгенерировались одинаковые подразбиения
            restart()
            return
    
        layout.remove_widget(restart_button)
        btn = Button(text = "You won! Restart",
                font_size = "20sp",
                background_color = (0, 1, 0, 0.5),
                size = (250, 50),
                size_hint = (None, None),
                pos = (w / 2 - 125, h / 2 - 25))
        btn.bind(on_press = lambda x: restart())
        layout.add_widget(btn)

def restart():
    layout.clear_widgets()

    global lower_triangle
    lower_triangle = MyTriangle(*lower_coords)

    global upper_triangle
    upper_triangle = MyTriangle(*upper_coords)

    global restart_button
    restart_button = Button(text = "Restart",
                font_size = "20sp",
                size = (200, 50),
                size_hint = (None, None),
                pos = (w / 2 - 100, h / 2 - 25))
    restart_button.bind(on_press = lambda x: restart())

    layout.add_widget(restart_button)

    check_win(with_button=False)

class TrianglesApp(App):
    def build(self):
        global layout
        layout = FloatLayout()
        self.box = layout

        restart()

        return self.box

if __name__ == '__main__':
    TrianglesApp().run()