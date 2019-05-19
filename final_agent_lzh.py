"""
agent for pysc2
author: lzhbrian
date: 2019.5.18
license: MIT
"""

import numpy as np
from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import units
FUNCTIONS = actions.FUNCTIONS

from . import tactics

# base tactic agent
class TacticAgent(base_agent.BaseAgent):
    def setup(self, obs_spec, action_spec):
        super(TacticAgent, self).setup(obs_spec, action_spec)
        if "feature_units" not in obs_spec:
            raise Exception("This agent requires the feature_units observation.")
        self.possible_tactic_list = [
            tactics.tactic_no_op
        ]

    def reset(self):
        super(TacticAgent, self).reset()
        self.select_new_tactic = True # if True: select tactic, else: exec the selected tactic
        self.tactic_idx = 0

        # renew 
        for idx, tactic in enumerate(self.possible_tactic_list):
            tactic.execed = False
            self.possible_tactic_list[idx] = tactic

        self.first_obs = None

    def step(self, obs):
        super(TacticAgent, self).step(obs)
        if not self.first_obs:
            self.first_obs = obs

        # select new tactic, and click on executer
        if self.select_new_tactic:
            self.select_new_tactic = False
            for idx, tactic in enumerate(self.possible_tactic_list):
                if tactic.check_tactic_executable(obs):
                    self.tactic_idx = idx
                    break
            return self.possible_tactic_list[self.tactic_idx].select_executer_func(obs)

        # in command, exec
        else:
            self.select_new_tactic = True
            return self.possible_tactic_list[self.tactic_idx].exec_func(obs)


class CollectMineralShards(base_agent.BaseAgent):
    def setup(self, obs_spec, action_spec):
        super(CollectMineralShards, self).setup(obs_spec, action_spec)
        if "feature_units" not in obs_spec:
            raise Exception("This agent requires the feature_units observation.")

    def reset(self):
        super(CollectMineralShards, self).reset()
        self._marine_selected = False
        self._previous_mineral_xy = [-1, -1]

    def step(self, obs):
        super(CollectMineralShards, self).step(obs)
        marines = [unit for unit in obs.observation.feature_units if unit.alliance == features.PlayerRelative.SELF]
        if not marines:
            return FUNCTIONS.no_op()
        marine_unit = next((m for m in marines if m.is_selected == self._marine_selected), marines[0])
        marine_xy = [marine_unit.x, marine_unit.y]

        if not marine_unit.is_selected:
            self._marine_selected = True
            return FUNCTIONS.select_point("select", marine_xy)
        if FUNCTIONS.Move_screen.id in obs.observation.available_actions:
            minerals = [[unit.x, unit.y] for unit in obs.observation.feature_units if unit.alliance == features.PlayerRelative.NEUTRAL]
            if self._previous_mineral_xy in minerals:
                minerals.remove(self._previous_mineral_xy)
            if minerals:
                distances = np.linalg.norm(np.array(minerals) - np.array(marine_xy), axis=1)
                closest_mineral_xy = minerals[np.argmin(distances)]
                self._marine_selected = False
                self._previous_mineral_xy = closest_mineral_xy
                return FUNCTIONS.Move_screen("now", closest_mineral_xy)
        return FUNCTIONS.no_op()


class CollectMineralsAndGas(TacticAgent):
    def setup(self, obs_spec, action_spec):
        super(CollectMineralsAndGas, self).setup(obs_spec, action_spec)
        possible_tactic_list_and_additional_check = [
            (tactics.tactic_build_command_center,
             lambda obs: tactics.get_unit_cnt(obs, units.Terran.CommandCenter) <= 1),
            (tactics.tactic_build_supply_depot,
             lambda obs: tactics.get_unit_cnt(obs, units.Terran.SupplyDepot) < 3 and \
                         tactics.get_unit_cnt(obs, units.Terran.CommandCenter) >= 2 and \
                         tactics.food_cap_equal_used(obs)),
            (tactics.tactic_harvest_mineral, None),
            (tactics.tactic_train_scv, None),
            (tactics.tactic_no_op, None) # the last one should be tactic_no_op, if no above tactic executable
        ]
        self.possible_tactic_list = []
        for tactic, additional_func in possible_tactic_list_and_additional_check:
            if additional_func:
                tactic.add_additional_check_tactic_executable(additional_func)
            self.possible_tactic_list.append(tactic)


class BuildMarines(TacticAgent):
    def setup(self, obs_spec, action_spec):
        super(BuildMarines, self).setup(obs_spec, action_spec)
        
        # score = 132
        possible_tactic_list_and_additional_check = [
            (tactics.tactic_harvest_mineral, None),
            # building tactics should be placed higher place
            (tactics.tactic_build_supply_depot,
             lambda obs: tactics.food_cap_equal_used(obs)),
            (tactics.tactic_build_barracks,
             lambda obs: tactics.get_unit_cnt(obs, units.Terran.Barracks) < 7),
            (tactics.tactic_train_marine,
             lambda obs: tactics.get_unit_cnt(obs, units.Terran.Barracks) >= 7),
            (tactics.tactic_train_scv,
             lambda obs: tactics.get_unit_cnt(obs, units.Terran.SCV) < 20),
            (tactics.tactic_no_op, None) # the last one should be tactic_no_op, if no above tactic executable
        ]

        self.possible_tactic_list = []
        for tactic, additional_func in possible_tactic_list_and_additional_check:
            if additional_func:
                tactic.add_additional_check_tactic_executable(additional_func)
            self.possible_tactic_list.append(tactic)


class DefeatZerglingsAndBanelings(TacticAgent):
    def setup(self, obs_spec, action_spec):
        super(DefeatZerglingsAndBanelings, self).setup(obs_spec, action_spec)

        possible_tactic_list_and_additional_check = [
            (tactics.tactic_attack_zerg_pioneer,
             lambda obs: tactics.get_unit_cnt(obs, units.Zerg.Baneling) > 0 and \
                         tactics.get_busy_marine_cnt(obs) <= 3),
            (tactics.tactic_attack_zerg_all,
             lambda obs: tactics.get_unit_cnt(obs, units.Zerg.Baneling) <= 2),
            (tactics.tactic_no_op, None) # the last one should be tactic_no_op, if no above tactic executable
        ]

        self.possible_tactic_list = []
        for tactic, additional_func in possible_tactic_list_and_additional_check:
            if additional_func:
                tactic.add_additional_check_tactic_executable(additional_func)
            self.possible_tactic_list.append(tactic)


class DefeatRoaches(TacticAgent):
    def setup(self, obs_spec, action_spec):
        super(DefeatRoaches, self).setup(obs_spec, action_spec)

        possible_tactic_list_and_additional_check = [
            (tactics.tactic_attack_all, None),
            (tactics.tactic_no_op, None) # the last one should be tactic_no_op, if no above tactic executable
        ]

        self.possible_tactic_list = []
        for tactic, additional_func in possible_tactic_list_and_additional_check:
            if additional_func:
                tactic.add_additional_check_tactic_executable(additional_func)
            self.possible_tactic_list.append(tactic)

