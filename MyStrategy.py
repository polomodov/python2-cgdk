# coding=utf-8

from math import *
from model.ActionType import ActionType
from model.HockeyistState import HockeyistState
from model.HockeyistType import HockeyistType

class MyStrategy:
    # Рассчитаны ли базовые параметры
    once_calculated = False
    # Мои сокомандники
    my_teammates = {}
    # Команда противника
    op_teammates = {}
    # объект противника
    opponent = False

    # for condifence interval 95%
    Z_VALUE = 1.96

    # упрощенная табличка функции Лапласа
    # для точности в один знак после запятой и только до 2 сигма
    LAPLAS_FUNCTION = {0: 0, 0.1: 0.040, 0.2: 0.079, 0.3: 0.117, 0.4: 0.155, 0.5: 0.191,
                       0.6: 0.225, 0.7: 0.258, 0.8: 0.288, 0.9: 0.315, 1.0: 0.341,
                       1.1: 0.366, 1.2: 0.384, 1.3: 0.403, 1.4: 0.419, 1.5: 0.433,
                       1.6: 0.445, 1.7: 0.455, 1.8: 0.464, 1.9: 0.471, 2: 0.5}

    # разовый расчет базовых параметров
    def calculate_once(self):
        if self.once_calculated == True:
            return True

        self.opponent = self.world.get_opponent_player()
        self.my_player = self.world.get_my_player()

        self.my_net = self.my_player.net_front
        self.opponent_net = self.opponent.net_front

        for hockeyist in self.world.hockeyists:
            if(hockeyist.player_id == self.me.player_id):
                self.my_teammates[hockeyist.id] = hockeyist
                self.actions[hockeyist.id] = None
            else:
                self.op_teammates[hockeyist.id] = hockeyist

        self.calculate_position_values()
        self.once_calculated = True

    def move(self, me, world, game, move):
        self.me = me
        self.world = world
        self.game = game
        self.move_object = move

        #self.go_to(self.world.puck.x, self.world.puck.y, 0, 0)

        # рассчитываем параметры раз в игру
        self.calculate_once()

        # проверим, что у нас есть возможность что-либо сделать
        if not self.can_do_action():
            return False

        if(self.world.puck.owner_player_id == self.me.player_id):
            self.move_with_puck()
        elif(self.world.puck.owner_player_id == self.opponent.id):
            self.move_without_puck()
        else:
            self.move_free_puck()

    def move_with_puck(self):
        """
        Стратегия игры с шайбой
        :return:
        """

        pass

    def move_without_puck(self):
        """
        Стратегия для игры без шайбы
        :return:
        """
        # один идет атаковать
        # второй защищается и пытается отобрать шайьу
        # если есть третий, то он атакует, стоит и ждет паса
        
        pass

    def move_free_puck(self):
        """
        Стратегия для игры на свободных шайбах
        :return:
        """
        pass


    def calculate_position_values(self):
        """
        Первоначальная оценка поля
        делим поле на квадраты со строной в радиус хоккеиста
        :return:
        """
        hockeyist = self.world.hockeyists[0]
        cell_side = 10
        # ширина поля - размер между воротами оппонентов
        width = abs(self.my_net - self.opponent_net)
        if(self.my_net < self.opponent_net):
            my_net = 'left'
        else:
            my_net = 'right'

        height = self.world.height
        rows = int(height / cell_side)
        columns = int(width / cell_side)
        net_width = self.game.goal_net_width

        self.map = [[0 for x in xrange(columns)] for x in xrange(rows)]
        for row_index in range(0, rows):
            for column_index in range(0, columns):
                if(my_net == 'right' and (column_index < 8 or column_index > 15)):
                    value = (0, 0)
                elif(my_net == 'left' and (column_index < columns - 15 or column_index > columns - 8)):
                    value = (0, 0)
                elif(row_index > self.game.goal_net_top/cell_side and row_index < (self.game.goal_net_top + self.game.goal_net_width)/cell_side):
                    value = (0, 0)
                else:
                    value_full = self.evaluate_shot_probability(((column_index+0.5)*cell_side, (row_index+0.5)*cell_side), 0, 1, False)
                    value_fast = self.evaluate_shot_probability(((column_index+0.5)*cell_side, (row_index+0.5)*cell_side), 0, 0.75, False)
                    value = (value_fast, value_full)
                # рассчитываем ценность каждой клетки
                self.map[row_index][column_index] = value


    def evaluate_shot_probability(self, position, speed=0, strength=1, current_goalkeeper_position=True):
        """
        Метод для оценки вероятности попадания прямого удара
        :return:
        """
        # параметры голкипера
        goalie_max_speed = self.game.goalie_max_speed
        goalie_radius = self.world.hockeyists[0].radius

        # параметры ворот
        goalie_net_height = self.game.goal_net_height
        goalie_net_top = self.game.goal_net_top
        goalie_net_bottom = goalie_net_top + goalie_net_height
        goalie_net_width = self.game.goal_net_width

        # параметры удара
        struck_puck_initial_speed_factor = self.game.struck_puck_initial_speed_factor
        strike_angle_deviation = self.game.strike_angle_deviation

        # параметры шайбы
        puck_radius = self.world.puck.radius

        # скорость шайбы после удара
        speed = struck_puck_initial_speed_factor * strength

        # ткущие координаты
        x = position[0]
        y = position[1]
        if current_goalkeeper_position==True:
            # определяем позицию голкипера
            for index in self.op_teammates:
                op_teammate = self.op_teammates[index]
                if(op_teammate.type == HockeyistType.GOALIE):
                    goalkeeper_position = op_teammate.y
                    break
        else:
            if y <= goalie_net_top:
                goalkeeper_position = goalie_net_top + goalie_radius
            elif y >= goalie_net_bottom:
                goalkeeper_position = goalie_net_bottom - goalie_radius
            else:
               goalkeeper_position = y

        #  и целевую отметку в первом приближении куда стоит пробить (верхнюю или нижнюю штангу)
        # @todo: добавить учет направления текущей скорости голкипера
        if goalkeeper_position > (goalie_net_top + goalie_net_bottom)/2:
            aim = goalie_net_top + puck_radius
        else:
            aim = goalie_net_bottom - puck_radius

        # дистанция голкипера до приблизительной точки удара
        goalkeeper_distance_to_aim = abs(goalkeeper_position - aim) - goalie_radius - puck_radius

        distance_to_aim = self.get_distance(position, (self.opponent_net, aim))
        time_to_aim = distance_to_aim/speed

        # голкипер успеет добраться до точки удара
        # @todo: учесть, текущую скорость голкипера
        if goalie_max_speed*time_to_aim >= goalkeeper_distance_to_aim:
            return 0

        delta = goalkeeper_distance_to_aim - goalie_max_speed*time_to_aim
        alpha = atan(delta/(2 * distance_to_aim))
        value = round(alpha/strike_angle_deviation, 1)
        if(value > 2):
            value = 2.0
        probability = 2 * self.LAPLAS_FUNCTION[value]

        return probability

    def get_distance(self, point1, point2):
        return sqrt(pow(point1[0] - point2[0], 2) + pow(point1[1] - point2[1], 2))

    def can_do_action(self):
        """
        Проверка возможности осуществлять действия хоккеистом
        :return:
        """
        if(self.me.state != HockeyistState.KNOCKED_DOWN and
           self.me.state != HockeyistState.RESTING and
           self.me.remaining_cooldown_ticks == 0):
            return False
        else:
            return True

    def go_to(self, destination_x, destination_y, destination_speed_x, destination_speed_y, ignore_destination_speed=False):
        """
        Метод для перемещения игрока в точку destination с желаемой скоростью в точке назначения speed
        :param destination:
        :param speed:
        :return:
        """

        # Мое положение
        x0 = self.me.x
        y0 = self.me.y
        vx0 = self.me.speed_x
        vy0 = self.me.speed_y

        # Ускорение хоккеиста
        a_speed_up = self.game.hockeyist_speed_up_factor
        a_speed_down = self.game.hockeyist_speed_down_factor
        
        # параметры угла и угловой скорости
        current_angle = self.me.angle
        angular_speed = self.me.angular_speed

        # параметры скорости
        max_speed = self.game.hockeyist_max_speed
        current_speed = sqrt(vx0**2 + vy0**2)

        # Положение, которое хотим получить на выходе
        x1 = destination_x
        y1 = destination_y
        vx1 = destination_speed_x
        vy1 = destination_speed_y

        # вектор желаемого перемещения
        sx = x1 - x0
        sy = y1 - y0
        # вектор дельты желемой скорости
        delta_vx = vx1 - vx0
        delta_vy = vy1 - vy0

        # считаем направление между вектором ожидаемой скорости и вектором ожимаемого перемещения
        s_length = sqrt(sx**2 + sy**2)
        delta_v_length = sqrt(delta_vx**2 + delta_vy**2)

        # почти стоим на месте или до цели еще далеко
        if current_speed/max_speed <= 0.2 or s_length > 100:
            # определяем угол на цель
            delta_angle = self.me.get_angle_to(x1, y1)
            # определяем стоит ли доворачиваться или просто можно ускоряться
            if delta_angle < 0.1:
                self.move_object.speed_up = 1
            else:
                self.move_object.turn = delta_angle

            return False

        # добрались
        if(s_length < 10):
            return True


        # Теперь учитываем с какой скоростью хотим оказаться в заданной точке

        if(s_length > 0 and delta_v_length == 0):
            cos_phi = 1
        else:
            cos_phi = (sx * delta_vx + sy * delta_vy) / s_length * delta_v_length
            if(cos_phi > 1):
                cos_phi = 1
            elif(cos_phi < -1):
                cos_phi = -1

        phi = acos(cos_phi)

        # довольно точно направлены на цель, ускоряемся
        if abs(phi - current_angle) < 0.1 and angular_speed < 1:
            self.move_object.speed_up = 1
        # направление совпадает, доварачиваем хоккеиста
        elif (cos_phi > 0):
            if (phi - current_angle) > 0:
                self.move_object.turn = - 1
            else:
                self.move_object.turn = 1
        # направление противоположное
        else:
            # если расстояние большое, пробуем разворот по кругу
            if sx > 200 and sy > 100:
                if phi - current_angle > 0.7:
                    self.move_object.speed_up = 1
                else:
                    self.move.turn = 1
            elif sx > 200 and sy < -100:
                if phi - current_angle < -0.7:
                    self.move_object.speed_up = 1
                else:
                    self.move_object.turn = -1
            # тупо поворачиваемся в нужную сторону
            else:
                angle_to_aim = self.me.get_angle_to(x1, y1)
                self.move_object.turn = angle_to_aim


    def get_pass_probability(self, hockeyist):
        """
        Метод для оценки вероятности успешности паса
        :param hockeyist:
        :return:
        """

    def access_hockeyist_shot_position(self, hockeyist):
        """
        Метод для оценки позиции хоккеиста
        Оценка с точки зрения возможности забить
        :param hockeyist:
        :return:
        """

    def access_hockeyist_to_opponent_position(self, hockeyist):
        """
        Метод для оценки позиции хоккеиста
        Оценка с точки зрения близости противников
        :param hockeyist:
        :return:
        """


    def get_angle_from_to(self, angle, x0, y0, x1, y1):
        absolute_angle_to = atan2(y1 - y0, x1 - x0)
        relative_angle_to = absolute_angle_to - angle

        while relative_angle_to > pi:
            relative_angle_to -= 2.0 * pi

        while relative_angle_to < -pi:
            relative_angle_to += 2.0 * pi

        return relative_angle_to
