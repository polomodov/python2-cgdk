# coding=utf-8

from math import *
from model.ActionType import ActionType
from model.HockeyistState import HockeyistState
from model.HockeyistType import HockeyistType

class MyStrategy:
    # Рассчитаны ли базовые параметры
    once_calculated = False
    # Мои сокомандники
    my_teammates = False
    # Команда противника
    op_teammates = False
    # объект противника
    opponent = False

    # for condifence interval 95%
    z_value = 1.96

    # упрощенная табличка функции Лапласа
    # для точности в один знак после запятой и только до 2 сигма
    laplas_function = {0: 0, 0.1: 0.040, 0.2: 0.079, 0.3: 0.117, 0.4: 0.155, 0.5: 0.191,
                       0.6: 0.225, 0.7: 0.258, 0.8: 0.288, 0.9: 0.315, 1.0: 0.341,
                       1.1: 0.366, 1.2: 0.384, 1.3: 0.403, 1.4: 0.419, 1.5: 0.433,
                       1.6: 0.445, 1.7: 0.455, 1.8: 0.464, 1.9: 0.471, 2: 0.5}

    # разовый расчет базовых параметров
    def calculate_once(self):
        if self.once_calculated == True:
            return True

        if(self.opponent == False):
            self.opponent = self.world.get_opponent_player()

        if(self.my_teammates == False or self.op_teammates == False):
            for hockeyist in self.world.hockeyists:
                if(hockeyist.player_id == self.me.player_id):
                    self.my_teammates[hockeyist.id] = hockeyist
                else:
                    self.op_teammates[hockeyist.id] = hockeyist


    def move(self, me, world, game, move):
        self.me = me
        self.world = world
        self.game = game

        # рассчитываем параметры раз в игру
        self.calculate_once()

        # проверим, что у нас есть возможность что-либо сделать
        if self.can_do_action():
            return False

        if(self.world.puck.owner_player_id == self.me.player_id):
            self.move_with_puck()
        elif(self.world.puck.owner_player_id == self.opponent.player_id):
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
        cell_side = hockeyist.radius
        width = self.world.width
        height = self.world.height
        rows = height / cell_side
        columns = width / cell_side
        net_width = self.game.goal_net_width

        map = []
        for row_index in range(0, rows):
            row = []
            for column_index in range(0, columns):
                # рассчитываем ценность каждой клетки
                row[column_index] = self.evaluate_shot_probability(((row_index+0.5)*cell_side, (column_index + 0.5)*cell_side))
            map[row_index] = row


    def evaluate_shot_probability(self, position, speed=0, strength=1, goalkeeper_fixed=False):
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

        # скорость шайьы после удара
        speed = struck_puck_initial_speed_factor * strength

        # ткущие координаты
        x = position[0]
        y = position[1]
        if goalkeeper_fixed == False:
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
            aim = goalie_net_top - puck_radius
        else:
            aim = goalie_net_bottom - puck_radius

        # дистанция голкипера до приблизительной точки удара
        goalkeeper_distance_to_aim = abs(goalkeeper_position - aim) - puck_radius

        distance_to_aim = self.get_distance(position, (goalie_net_width, aim))
        time_to_aim = distance_to_aim/speed

        # голкипер успеет добраться до точки удара
        # @todo: учесть, текущую скорость голкипера
        if goalie_max_speed*time_to_aim >= goalkeeper_distance_to_aim:
            return 0

        delta = goalkeeper_distance_to_aim - goalie_max_speed*time_to_aim
        alpha = math.atan(delta/ (2 * distance_to_aim))
        probability = 2 * self.laplas_function[round(alpha/strike_angle_deviation)]

        return probability

    def get_distance(self, point1, point2):
        return math.sqrt(pow(point1[0] - point2[0], 2) + pow(point1[1] - point2[1], 2))

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

    def go_to(self, destination, speed):
        """
        Метод для перемещения игрока в точку destination с желаемой скоростью в точке назначения speed
        :param destination:
        :param speed:
        :return:
        """
        if self.can_do_action():
            return
        pass

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