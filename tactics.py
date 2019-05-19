"""
tactics for agent for pysc2
author: lzhbrian (https://lzhbrian.me)
date: 2019.5.18
license: MIT
"""

import numpy as np
from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import units

FUNCTIONS = actions.FUNCTIONS

# class tactic
# contains 3 functions:
#   check_available_func
#   select_executer_func
#   exec_func
class Tactic:
    def __init__(self, check_available_func, select_executer_func, exec_func, once=False):
        self.func1 = check_available_func
        self.func2 = select_executer_func
        self.func3 = exec_func
        self.add_func1 = lambda *argv: True
        self.once = once
        self.execed = False

    def check_tactic_executable(self, *argv):
        if self.once:
            if self.execed:
                return False
            else:
                self.execed = True
        return self.func1(*argv) and self.add_func1(*argv)

    def select_executer_func(self, *argv):
        return self.func2(*argv)

    def exec_func(self, *argv):
        return self.func3(*argv)

    def add_additional_check_tactic_executable(self, additional_func):
        self.add_func1 = additional_func

def get_unit_cnt(obs, unit_type):
    cnt = 0
    for unit in obs.observation.feature_units:
        if unit.unit_type == unit_type:
            cnt += 1
    return cnt

def get_one_idle_scv(obs):
    """
    check if any idle scv are available
    :return idle_scv_pos: [x, y], if no, return None
    """
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Terran.SCV and int(unit.order_length) == 0:
            return [unit.x, unit.y]
    return None

def get_one_idle_marine(obs):
    """
    check if any idle marine are available
    :return idle_scv_pos: [x, y], if no, return None
    """
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Terran.Marine and int(unit.order_length) == 0:
            return [unit.x, unit.y]
    return None

def get_busy_marine_cnt(obs):
    cnt = 0
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Terran.Marine and int(unit.order_length) != 0:
            cnt += 1
    return cnt

def get_idle_marine_cnt(obs):
    cnt = 0
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Terran.Marine and int(unit.order_length) == 0:
            cnt += 1
    return cnt

def get_one_random_scv(obs):
    a = get_one_idle_scv(obs)
    if a:
        return a
    else:
        for unit in obs.observation.feature_units:
            if unit.unit_type == units.Terran.SCV:
                return [unit.x, unit.y]

def get_minerals_positions(obs):
    res = []
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Neutral.MineralField:
            return [unit.x, unit.y]

def get_mineralshards_positions(obs):
    pos = get_one_idle_marine(obs)
    res = []
    for unit in obs.observation.feature_units:
        if unit.alliance == features.PlayerRelative.NEUTRAL:
            res.append([unit.x, unit.y])
    distances = np.linalg.norm(np.array(res) - np.array(pos), axis=1)
    closest_mineral_xy = res[np.argmin(distances)]
    return closest_mineral_xy

# get command center with fewer orders queued
# command center is in [33, 33], radius = 9 for BuildMarine and CollectMineralsAndGas
def get_command_center_positions(obs):
    order_len = 999
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Terran.CommandCenter and unit.order_length < order_len:
            pos = [unit.x, unit.y]
            r = unit.radius
            order_len = unit.order_length
    return pos

# get new command center position
def get_new_command_center_position(obs):
    x, y, r = None, None, None
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Terran.CommandCenter:
            x, y = unit.x, unit.y
            r = unit.radius
    if x < 42:
        x = x + 2 * r
    else:
        x = x - 2 * r
    return [x, y]

# radius = 6
def get_barracks_position(obs):
    order_len = 999
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Terran.Barracks and unit.order_length < order_len:
            pos = [unit.x, unit.y]
            order_len = unit.order_length
    return pos

def get_enemy_pos(obs):
    min_health = 99999
    pos = [0, 0]
    for unit in obs.observation.feature_units:
        if unit.alliance == features.PlayerRelative.ENEMY and unit.health < min_health:
            pos = [unit.x, unit.y]
            min_health = unit.health
    return pos

def get_enemy_pos_y_min_max(obs):
    y_min = 888
    y_max = 0
    for unit in obs.observation.feature_units:
        if unit.alliance == features.PlayerRelative.ENEMY:
            if unit.y < y_min:
                y_min = unit.y
                min_pos = [unit.x, unit.y - 20]
            if unit.y > y_max:
                y_max = unit.y
                max_pos = [unit.x, unit.y + 20]
    return [min_pos, max_pos]

# get potential supply depot pos
def get_potential_supply_depot_pos(obs):
    potential_barracks_pos = []
    for x in [22, 30, 38, 46]:
        for y in [12, 20, 46, 54]:
            potential_barracks_pos.append([int(x), int(y)])
    idx = get_unit_cnt(obs, units.Terran.SupplyDepot)
    if idx > len(potential_barracks_pos) - 1:
        for unit in obs.observation.feature_units:
            if unit.unit_type == units.Terran.CommandCenter:
                x, y = unit.x, unit.y
                r = unit.radius
                delta_x = np.random.randint(-4 * r, r)
                delta_y = np.random.randint(-4 * r, 4 * r)
                return [x + delta_x, y + delta_y]
    else:
        return potential_barracks_pos[idx]


def get_potential_barracks_pos(obs):
    # for unit in obs.observation.feature_units:
    #     if unit.unit_type == units.Terran.CommandCenter:
    #         x, y = unit.x, unit.y
    #         r = unit.radius
    #         delta_x = np.random.randint(r, 5 * r)
    #         delta_y = np.random.randint(-3 * r, 3 * r)
    #         return [x + delta_x, y + delta_y]

    potential_barracks_pos = []
    for x in [56, 69, 72]:
        for y in [7, 22, 37, 52]:
            potential_barracks_pos.append([int(x), int(y)])
    return potential_barracks_pos[get_unit_cnt(obs, units.Terran.Barracks)]
    # return [0, 0]

def get_zerg_pos(obs):
    min_health = 99999
    pos = [0, 0]
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Zerg.Zergling:
            pos = [unit.x, unit.y]
            min_health = unit.health
    return pos

def get_baneling_pos(obs):
    pos = [0, 0]
    for unit in obs.observation.feature_units:
        if unit.unit_type == units.Zerg.Baneling:
            pos = [unit.x, unit.y]
            return pos

def food_cap_equal_used(obs):
    return obs.observation.player[features.Player.food_cap] == obs.observation.player[features.Player.food_used]

def food_cap_available(obs):
    return obs.observation.player[features.Player.food_cap] > obs.observation.player[features.Player.food_used]

def make_save_pos(obs, pos):
    x, y = pos[0], pos[1]
    x = min(max(0, x), obs.observation.feature_screen.shape[1] - 1)
    y = min(max(0, y), obs.observation.feature_screen.shape[2] - 1)
    return [x, y]

# build new command center
tactic_build_command_center = Tactic(
    lambda obs, *argv: obs.observation.player[features.Player.minerals] >= 450,
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_random_scv(obs))),
    lambda obs, *argv: FUNCTIONS.Build_CommandCenter_screen("now", make_save_pos(obs, get_new_command_center_position(obs))) \
                       if FUNCTIONS.Build_CommandCenter_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

# build supply depot
tactic_build_supply_depot = Tactic(
    lambda obs, *argv: obs.observation.player[features.Player.minerals] >= 100,
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_random_scv(obs))),
    lambda obs, *argv: FUNCTIONS.Build_SupplyDepot_screen("now", make_save_pos(obs, get_potential_supply_depot_pos(obs))) \
                       if FUNCTIONS.Build_SupplyDepot_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

# tactic build barracks
tactic_build_barracks = Tactic(
    lambda obs, *argv: obs.observation.player[features.Player.minerals] >= 150,
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_random_scv(obs))),
    lambda obs, *argv: FUNCTIONS.Build_Barracks_screen("now", make_save_pos(obs, get_potential_barracks_pos(obs))) \
                       if FUNCTIONS.Build_Barracks_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

# harvest mineral
tactic_harvest_mineral = Tactic(
    lambda obs, *argv: get_one_idle_scv(obs),
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_idle_scv(obs))),
    lambda obs, *argv: FUNCTIONS.Harvest_Gather_screen("now", make_save_pos(obs, get_minerals_positions(obs))) \
                       if FUNCTIONS.Harvest_Gather_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

# train scv
tactic_train_scv = Tactic(
    lambda obs, *argv: food_cap_available(obs) and \
                       get_unit_cnt(obs, units.Terran.CommandCenter) >= 1 and \
                       obs.observation.player[features.Player.minerals] >= 50,
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_command_center_positions(obs))),
    lambda obs, *argv: FUNCTIONS.Train_SCV_quick("now") \
                       if FUNCTIONS.Train_SCV_quick.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

tactic_train_marine = Tactic(
    lambda obs, *argv: food_cap_available(obs) and \
                       get_unit_cnt(obs, units.Terran.Barracks) >= 1 and \
                       obs.observation.player[features.Player.minerals] >= 50,
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_barracks_position(obs))),
    lambda obs, *argv: FUNCTIONS.Train_Marine_quick("now") \
                       if FUNCTIONS.Train_Marine_quick.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

# collect mineral shards
tactic_collect_mineralshards = Tactic(
    lambda obs, *argv: get_one_idle_marine(obs),
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_idle_marine(obs))),
    lambda obs, *argv: FUNCTIONS.Move_screen("now", make_save_pos(obs, get_mineralshards_positions(obs))) \
                       if FUNCTIONS.Move_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

tactic_attack_zerg_pioneer = Tactic(
    lambda obs, *argv: get_one_idle_marine(obs),
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_idle_marine(obs))),
    lambda obs, *argv: FUNCTIONS.Attack_screen("now", make_save_pos(obs, get_zerg_pos(obs))) \
                       if FUNCTIONS.Attack_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

tactic_attack_baneling_pioneer = Tactic(
    lambda obs, *argv: get_one_idle_marine(obs),
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_idle_marine(obs))),
    lambda obs, *argv: FUNCTIONS.Attack_screen("now", make_save_pos(obs, get_baneling_pos(obs))) \
                       if FUNCTIONS.Attack_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

tactic_attack_all = Tactic(
    lambda obs, *argv: True,
    lambda obs, *argv: FUNCTIONS.select_army("select"),
    lambda obs, *argv: FUNCTIONS.Attack_screen("now", make_save_pos(obs, get_enemy_pos_y_min_max(obs)[0])) \
                       if FUNCTIONS.Attack_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

tactic_attack_zerg_all = Tactic(
    lambda obs, *argv: get_one_idle_marine(obs),
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_idle_marine(obs))),
    lambda obs, *argv: FUNCTIONS.Attack_screen("now", make_save_pos(obs, get_zerg_pos(obs))) \
                       if FUNCTIONS.Attack_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

tactic_move_to_enemy_top = Tactic(
    lambda obs, *argv: get_one_idle_marine(obs),
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_idle_marine(obs))),
    lambda obs, *argv: FUNCTIONS.Move_screen("now", make_save_pos(obs, get_enemy_pos_y_min_max(obs)[0])) \
                       if FUNCTIONS.Attack_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

tactic_move_to_enemy_bottom = Tactic(
    lambda obs, *argv: get_one_idle_marine(obs),
    lambda obs, *argv: FUNCTIONS.select_point("select", make_save_pos(obs, get_one_idle_marine(obs))),
    lambda obs, *argv: FUNCTIONS.Move_screen("now", make_save_pos(obs, get_enemy_pos_y_min_max(obs)[1])) \
                       if FUNCTIONS.Attack_screen.id in obs.observation.available_actions else FUNCTIONS.no_op()
)

# no op
tactic_no_op = Tactic(
    lambda *argv: True,
    lambda *argv: FUNCTIONS.no_op(),
    lambda *argv: FUNCTIONS.no_op()
)
