import json
from types import SimpleNamespace
from collections import deque
from random import random
import matplotlib.pyplot as plt
import pdb

class Enemy:
    def __init__(self, name, level, ui):
        self.modifiers = self.Modifier()
        with open('./enemy_data.json') as f:
            data = json.load(f)
        e = data[name]
        e = json.dumps(e)
        enemy_data = json.loads(e, object_hook=lambda d: SimpleNamespace(**d))
        self.name = name

        self.health_type = enemy_data.health_type
        self.shield_type = enemy_data.shield_type
        self.armor_type = enemy_data.armor_type

        self.base_health = enemy_data.base_health
        self.base_shield = enemy_data.base_shield
        self.base_armor = enemy_data.base_armor
        self.base_level = enemy_data.base_level

        self.enemy_type = enemy_data.enemy_type

        if level < self.base_level:
            self.level = self.base_level
        else:
            self.level = level

        self.old_scaling = ui.old_scaling_checkbox.isChecked()

        self.health_modifiers = self.modifiers.get_modifier(self.health_type)
        self.shield_modifiers = self.modifiers.get_modifier(self.shield_type)
        self.armor_modifiers = self.modifiers.get_modifier(self.armor_type)

        self.SP_armor_buff = ui.SP_armor_buff_spinner.value()
        self.SP_health_buff = ui.SP_health_buff_spinner.value()
        self.SP_shield_buff = ui.SP_shield_buff_spinner.value()

        self.armor_debuff = 1
        self.health_debuff = 1
        self.armor_debuff = 1

        self.max_health = self.get_scaled_health() * self.SP_health_buff
        self.max_shield = self.get_scaled_shield() * self.SP_shield_buff
        self.max_armor = self.get_scaled_armor() * self.SP_armor_buff
        #print( self.max_health, self.max_shield, self.max_armor )
        self.ehp = self.max_health*(1+self.max_armor/300)+self.max_shield

        self.current_health = self.max_health
        self.current_shield = self.max_shield
        self.current_armor = self.max_armor

        self.impact_proc_manager = self.ImpactProcManager(self)
        self.puncture_proc_manager = self.PunctureProcManager(self)
        self.slash_proc_manager = self.SlashProcManager(self)
        self.heat_proc_manager = self.HeatProcManager(self)
        self.cold_proc_manager = self.ColdProcManager(self)
        self.electric_proc_manager = self.ElectricProcManager(self)
        self.toxin_proc_manager = self.ToxinProcManager(self)
        self.blast_proc_manager = self.BlastProcManager(self)
        self.radiation_proc_manager = self.RadiationProcManager(self)
        self.gas_proc_manager = self.GasProcManager(self)
        self.magnetic_proc_manager = self.MagneticProcManager(self)
        self.viral_proc_manager = self.ViralProcManager(self)
        self.corrosive_proc_manager = self.CorrosiveProcManager(self)
        self.void_proc_manager = self.VoidProcManager(self)

        self.proc_managers = [self.impact_proc_manager, self.puncture_proc_manager, self.slash_proc_manager,
                                self.heat_proc_manager, self.cold_proc_manager, self.electric_proc_manager,
                                self.toxin_proc_manager, self.blast_proc_manager, self.radiation_proc_manager,
                                self.gas_proc_manager, self.magnetic_proc_manager, self.viral_proc_manager,
                                self.corrosive_proc_manager, self.void_proc_manager]

        self.magnetic_multiplier = 1
        self.viral_multiplier =1
        self.corrosive_armor_strip = 1
        self.heat_armor_strip = 1

        self.body_part_multiplier = ui.body_part_multiplier_spinner.value()
        if ui.critical_headshot_bonus_checkbox.isChecked():
            self.critical_headshot_bonus = 2
        else:
            self.critical_headshot_bonus = 1

        self.proc_immunity = [1]*20

        if self.enemy_type == 'ET_NORMAL':
            self.innate_damage_reduction = 1
        elif self.enemy_type == 'ET_DEMOLISHER' or self.enemy_type == 'ET_DEMOLYST':
            self.innate_damage_reduction = 0.8
            self.proc_immunity[8] = 0
        elif self.enemy_type == 'ET_CONDRIX':
            self.innate_damage_reduction = 1
            self.proc_immunity = [0]*20
        elif self.enemy_type == 'ET_EIDOLON':
            self.innate_damage_reduction = 1
            self.critical_headshot_bonus = 2
            self.proc_immunity = [0]*20
        elif self.enemy_type == 'ET_LEPHANTIS':
            self.innate_damage_reduction = 0.3
        elif self.enemy_type == 'ET_DEIMOS':
            self.proc_immunity[11] = 0
        elif self.enemy_type == 'ET_DEIMOS_JUGULUS':
            self.proc_immunity[11] = 0
            self.innate_damage_reduction = 0.8
        elif self.enemy_type == 'ET_DEIMOS_SAXUM':
            self.proc_immunity[11] = 0
            self.innate_damage_reduction = 1

        self.previous_hit_time = 0
        self.time = 0
        self.total_unreduced_damage = 0
        self.shield_active = bool(self.base_shield)
        self.damage_instance_list = []


    def kill(self, weapon):
        time = []
        shield_time = []
        health = []
        shield = []
        armor = [self.current_armor]
        armor_time = [0]
        prev_health = self.current_health
        prev_shield = self.current_shield
        self.shield_active = bool(self.current_shield)
        weapon.apply_proc_immunity(self.proc_immunity)
        while self.current_health > 0:
            # find effect to execute next
            if len(weapon.weapon_effects) > 0:
                time_list = [f.next_event for f in weapon.weapon_effects]
                mindex = time_list.index(min(time_list))

                if weapon.main_effect.next_event < time_list[mindex]:
                    next_weapon_event = weapon.main_effect
                else:
                    next_weapon_event = weapon.weapon_effects[mindex]
            else:
                next_weapon_event = weapon.main_effect

            time_list = [f.get_next_event_time() for f in self.proc_managers]
            mindex = time_list.index(min(time_list))
            next_proc_event = self.proc_managers[mindex]


            prev_health = self.current_health
            prev_shield = self.current_shield
            #health.append(self.current_health)
            #shield.append(self.current_shield)if self.current_shield>0

            # execute next event
            if next_weapon_event.next_event < next_proc_event.get_next_event_time():
                cur_effect = next_weapon_event
                if not cur_effect.is_secondary_effect:
                    # roll multishot
                    if random() < cur_effect.modded_pellets%1:
                        plts = int(cur_effect.modded_pellets+1)
                    else:
                        plts = int(cur_effect.modded_pellets)
                    cur_effect.multishot_state = plts
                    if cur_effect.trigger == 'HELD':
                        self.set_time(cur_effect.next_event)
                        self.apply_damage( [f*plts for f in cur_effect.modded_damage], cur_effect)
                        self.apply_beam_status(cur_effect)
                        #refresh
                        cur_effect.refresh_state()
                    else:
                        for i in range(plts):
                            if weapon.hit_scaling:
                                cur_effect.modded_damage = [cur_effect.modded_damage[i]+cur_effect.modded_base_damage[i] for i in range(len(cur_effect.modded_damage))]
                            self.set_time(cur_effect.next_event)
                            res = self.apply_damage(cur_effect.modded_damage, cur_effect)
                            #print(res)
                            self.apply_status(cur_effect)
                            #refresh
                            cur_effect.refresh_state()
                    #store multishot state in each secondary effect
                    for seff in weapon.weapon_effects:
                        seff.multishot_history.append(plts)
                else:

                    if cur_effect.trigger == 'HELD':
                        plts = cur_effect.multishot_history[0]
                        self.set_time(cur_effect.next_event)
                        self.apply_damage( [f*plts for f in cur_effect.modded_damage], cur_effect)
                        self.apply_beam_status(cur_effect)
                        #refresh
                        cur_effect.refresh_state()
                    else:

                        # roll multishot (secondary effect modded multishot)
                        if random() < cur_effect.modded_pellets%1:
                            plts = int(cur_effect.modded_pellets+1)
                        else:
                            plts = int(cur_effect.modded_pellets)
                        cur_effect.multishot_state = plts

                        # loop over primary effect multishot state and then secondary effect multishot state
                        for i in range(cur_effect.multishot_history[0]):
                            for i in range(plts):
                                self.set_time(cur_effect.next_event)
                                self.apply_damage(cur_effect.modded_damage, cur_effect)
                                self.apply_status(cur_effect)
                                #refresh
                                cur_effect.refresh_state()

                if cur_effect.current_stance_proc:
                    self.apply_proc(2)

                cur_effect.refresh_next_event()

            else:
                #print("Proc ID: %s"%next_proc_event.proc_id)
                self.set_time( next_proc_event.get_next_event_time() )
                next_proc_event.execute()

            if self.get_modified_armor() != armor[-1]:
                armor.append(armor[-1])
                armor_time.append(self.time-1e-3)
                armor_time.append(self.time)
                armor.append(self.get_modified_armor())

            if prev_health != self.current_health:
                health.append(prev_health)
                health.append(self.current_health)
                time.append(self.time-1e-3)
                time.append(self.time)

            if prev_shield != self.current_shield:
                shield.append(prev_shield)
                shield.append(self.current_shield)
                shield_time.append(self.time-1e-3)
                shield_time.append(self.time)


            if self.time >20:
                if self.max_health-self.current_health+self.max_shield-self.current_shield <=0:
                    return (1000, time, health,shield_time,shield, armor_time, armor)
                return ((self.max_health+self.max_shield) * self.time/(self.max_health-self.current_health+self.max_shield-self.current_shield), time, health,shield_time,shield, armor_time, armor)
        #print(self.total_unreduced_damage)
        return (max(0.001, self.time), time, health, shield_time, shield, armor_time, armor)

    def apply_damage(self, dmg, weapon_effect, proc = False):
        shield_break = False
        self.total_unreduced_damage += sum(dmg)
        applied_shield_damage = 0
        applied_health_damage = 0
        total_applied_damage = self.current_health+self.current_shield
        if self.current_shield > 0:
            for i, elem in enumerate(dmg):
                if i != 6:
                    applied_shield_damage += elem * self.shield_modifiers[i] * self.magnetic_multiplier
                else:
                    applied_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * self.get_modifier_armor_reduction(i)
        else:
            for i, elem in enumerate(dmg):
                applied_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * self.get_modifier_armor_reduction(i)
        before = self.current_health
        applied_shield_damage = applied_shield_damage * self.get_all_enemy_multipliers()
        applied_health_damage = applied_health_damage * self.get_all_enemy_multipliers()
        if proc:
            self.current_shield -= applied_shield_damage * self.get_special_damage_reduction(applied_shield_damage, weapon_effect)
            self.current_health -= applied_health_damage * self.get_special_damage_reduction(applied_health_damage, weapon_effect)
        else:
            self.current_shield -= applied_shield_damage * self.get_special_damage_reduction(applied_shield_damage, weapon_effect) * self.get_critical_damage_state(weapon_effect)
            self.current_health -= applied_health_damage * self.get_special_damage_reduction(applied_health_damage, weapon_effect) * self.get_critical_damage_state(weapon_effect)
        #print("Health Damage: %.2f, Multishot: %.0f, Time: %.2f"%( before - self.current_health, weapon_effect.multishot_state, self.time))
        #print(applied_health_damage * self.get_special_damage_reduction(applied_health_damage, weapon_effect) * self.get_critical_damage_state(weapon_effect) * self.get_all_enemy_multipliers(), self.get_critical_damage_state(weapon_effect))

        applied_health_damage = 0
        if self.current_shield < 0:
            shield_break = True
            ratio = abs(self.current_shield/applied_shield_damage)
            for i, elem in enumerate(dmg):
                #elem = round(elem/weapon_effect.quantum, 0) * weapon_effect.quantum
                applied_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * ratio * self.get_modifier_armor_reduction(i)

            applied_health_damage = applied_health_damage * self.get_all_enemy_multipliers()
            if proc:
                self.current_health -= applied_health_damage * self.get_special_damage_reduction(applied_health_damage, weapon_effect)
            else:
                self.current_health -= applied_health_damage * self.get_special_damage_reduction(applied_health_damage, weapon_effect) * self.get_critical_damage_state(weapon_effect)
            self.current_shield = 0

        if weapon_effect.weapon.shattering_impact and dmg[0]:
            self.base_armor -= 6
            self.current_armor = self.get_scaled_armor()*self.SP_armor_buff
        if weapon_effect.weapon.amalgam_argonak_metal_auger:
            self.base_armor -= 6
            self.current_armor = self.get_scaled_armor()*self.SP_armor_buff

        if not shield_break:
            # there are infinite possibilities of heat damage instances, so ignore them
            # ignore all procs for now
            if not (proc and dmg[3]) and not proc:
                self.damage_instance_list.append(round(total_applied_damage - (self.current_health+self.current_shield),0))
        if self.current_health <0:
            self.current_health = 0
        total_applied_damage -= (self.current_health+self.current_shield)
        #print(self.get_critical_damage_state(weapon_effect))
        return total_applied_damage

    def set_time(self, t):
        self.previous_hit_time = self.time
        self.time = t

    def apply_status(self, weapon_effect):
        # apply guaranteed status effects (>100% sc)
        for i in range( int(weapon_effect.modded_status_chance) ):
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.add_proc(i, weapon_effect)
                    break
                proc_roll -= sts

        # apply remaining status chance
        if weapon_effect.status_proc:
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.add_proc(i, weapon_effect)
                    break
                proc_roll -= sts

    def apply_beam_status(self, weapon_effect):
        # apply guaranteed status effects (>100% sc)
        for i in range( int(weapon_effect.modded_status_chance * weapon_effect.multishot_state) ):
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.add_proc(i, weapon_effect)
                    break
                proc_roll -= sts

        # apply remaining status chance
        if random()<( (weapon_effect.modded_status_chance*weapon_effect.multishot_state)%1 ):
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.add_proc(i, weapon_effect)
                    break
                proc_roll -= sts

    def add_proc(self, index, weapon_effect):
        if index == 0:
            pass
            self.impact_proc_manager.add_proc(weapon_effect)
        elif index == 1:
            pass
            self.puncture_proc_manager.add_proc(weapon_effect)
        elif index == 2:
            self.slash_proc_manager.add_proc(weapon_effect)
        elif index == 3:
            self.heat_proc_manager.add_proc(weapon_effect)
        elif index == 4:
            pass
            self.cold_proc_manager.add_proc(weapon_effect)
        elif index == 5:
            self.electric_proc_manager.add_proc(weapon_effect)
        elif index == 6:
            self.toxin_proc_manager.add_proc(weapon_effect)
        elif index == 7:
            pass
            self.blast_proc_manager.add_proc(weapon_effect)
        elif index == 8:
            pass
            self.radiation_proc_manager.add_proc(weapon_effect)
        elif index == 9:
            self.gas_proc_manager.add_proc(weapon_effect)
        elif index == 10:
            self.magnetic_proc_manager.add_proc(weapon_effect)
        elif index == 11:
            self.viral_proc_manager.add_proc(weapon_effect)
        elif index == 12:
            self.corrosive_proc_manager.add_proc(weapon_effect)
        elif index == 13:
            pass
            self.void_proc_manager.add_proc(weapon_effect)

    class ImpactProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'IMPACT'

        def add_proc(self, weapon_effect):
            np = self.ImpactProc(self.enemy, weapon_effect)
            if len(self.proc_dq) == 0:
                self.next_event = np.expiry
            elif len(self.proc_dq) == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            if len(self.proc_dq) == 0:
                self.next_event = 2**32
            else:
                self.next_event = self.proc_dq[0].expiry

        class ImpactProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    class PunctureProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'PUNCTURE'

        def add_proc(self, weapon_effect):
            np = self.PunctureProc(self.enemy, weapon_effect)
            if len(self.proc_dq) == 0:
                self.next_event = np.expiry
            elif len(self.proc_dq) == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            if len(self.proc_dq) == 0:
                self.next_event = 2**32
            else:
                self.next_event = self.proc_dq[0].expiry

        class PunctureProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    class SlashProcManager:
        def __init__(self, enemy):
            self.enemy = enemy
            self.container_list = deque([])
            self.container_index = 0
            self.proc_id = 'SLASH'
            self.total_applied_damage = 0

        def increment_index(self, max, current_index):
            if current_index+1 > max-1:
                return 0
            else:
                return current_index + 1

        def decrement_index(self, max, current_index):
            if current_index-1 < 0:
                return max-1
            else:
                return current_index-1

        def add_proc(self, weapon_effect):
            # create new proc
            np = self.SlashProc(self.enemy, weapon_effect)

            # get previous added container
            previous_index = self.decrement_index(len(self.container_list),self.container_index)
            res_container = None
            for container in self.container_list:
                if container.index == previous_index:
                    res_container = container
                    break

            # Check if proc happened at the same time
            if len(self.container_list)>0 and res_container is not None and res_container.proc_dq[-1].offset == self.enemy.time:
                # add it to same container as last proc
                res_container.add_proc(np)
            else:
                if len(self.container_list)<10:
                    self.container_list.append(self.ProcContainer(self.enemy, self.container_index, self))
                # add to next container and increment container index
                for container in self.container_list:
                    if container.index == self.container_index:
                        container.add_proc(np)
                        break
                self.container_index = self.increment_index( 10, self.container_index)

        def get_next_event_time(self):
            # Return event time
            if len(self.container_list)>0:
                return self.container_list[0].next_event
            else:
                return 12345678910

        def execute(self):
            # execute proc if exists
            if len(self.container_list[0].proc_dq) > 0:
                self.container_list[0].execute()
                if len(self.container_list[0].proc_dq)<=0:
                    self.container_list.popleft()
                    # shift all indeces down and set container_index to end
                    for container in self.container_list:
                        container.index-=1
                    self.container_index=len(self.container_list)
                else:
                    self.container_list.append(self.container_list.popleft())
            else:
                print("No proc to execute")

        class ProcContainer:
            def __init__(self, enemy, index, manager):
                self.manager = manager
                self.enemy = enemy
                self.index = index
                self.next_event = 696969696969
                self.total_damage = [0]*20
                self.proc_dq = deque([])

            def add_proc(self, proc):
                # If it is a new container, set the event time to first proc
                if len(self.proc_dq) == 0:
                    self.next_event = proc.next_event
                # add proc to list
                self.proc_dq.append(proc)
                # add proc damage to total
                self.total_damage[14] += proc.damage[14]

            def execute(self):
                app_dmg = self.enemy.apply_damage(self.total_damage, self.proc_dq[0].weapon_effect, proc = True)
                self.manager.total_applied_damage += app_dmg
                # Increment individual proc stats
                for proc in self.proc_dq:
                    proc.next_event += 1
                    proc.executed_count += 1
                # Remove any expired procs
                self.recursive_pop()
                # Change container level next_event time to valid proc
                if len(self.proc_dq)==0:
                    self.next_event = 420420420420
                self.next_event += 1

            def recursive_pop(self):
                # Check if oldest proc has expired
                if self.proc_dq[0].executed_count >= self.proc_dq[0].ticks:
                    # Remove damage from total
                    self.total_damage[14] -= self.proc_dq[0].damage[14]
                    # Remove procc from list
                    self.proc_dq.popleft()

                    # if there are more procs in the list, check if they expired
                    if len(self.proc_dq)>0:
                        self.recursive_pop()

        class SlashProc:
            def __init__(self, enemy, weapon_effect):
                self.weapon_effect = weapon_effect
                self.enemy = enemy

                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = self.enemy.time + self.life
                self.expired = False
                self.executed_count = 0
                self.ticks = int(self.life)
                self.damage = [0]*20
                if weapon_effect.trigger =='HELD':
                    self.damage[14] = 0.35 * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.innate_damage_reduction * weapon_effect.multishot_state
                else:
                    self.damage[14] = 0.35 * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.innate_damage_reduction


                self.offset = self.enemy.time
                self.next_event = self.offset + 1

    '''
    class SlashProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.proc_id = 'SLASH'

        def add_proc(self, weapon_effect):
            np = self.SlashProc(self.enemy, weapon_effect)
            self.proc_dq.append(np)

        def get_next_event_time(self):
            if len(self.proc_dq) > 0:
                return self.proc_dq[0].next_event
            else:
                return 2**31

        def execute(self):
            before = self.enemy.current_health
            self.enemy.apply_damage(self.proc_dq[0].damage, self.proc_dq[0].weapon_effect, proc = True)
            self.proc_dq[0].next_event += 1
            self.proc_dq[0].index += 1
            if self.proc_dq[0].index >= self.proc_dq[0].ticks:
                self.proc_dq.popleft()
            else:
                self.proc_dq.append(self.proc_dq.popleft())
            after = self.enemy.current_health

        class SlashProc:
            def __init__(self, enemy, weapon_effect):
                self.weapon_effect = weapon_effect
                self.enemy = enemy

                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False
                self.index = 0
                self.ticks = int(self.life)
                self.damage = [0]*20
                self.damage[14] = 0.35 * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.innate_damage_reduction
                #print("Tot proc damage: %.2f, Modded base dmg: %.2f, bane: %.4f, crit state: %.2f, innate dr: %.4f"%( self.damage[14],  weapon_effect.modded_total_base_damage, (1+weapon_effect.weapon.bane_mods), enemy.get_critical_damage_state(weapon_effect), enemy.innate_damage_reduction))

                self.offset = enemy.time
                self.next_event = self.offset + 1
    '''
    class HeatProcManager:
        # For heat procs, the offset is constant, no need to pop an append elements to keep track of next event
        def __init__(self, enemy):
            self.heat_proc_dq = deque([])
            self.heat_proc_armor_strip = None
            self.heat_proc_armor_regen = None
            self.proc_id = 'HEAT'
            self.total_applied_damage = 0

            self.offset = 2**31
            self.next_event = self.offset + 1
            self.expiry = 0

            self.total_damage_list = [0]*20

            self.event_list = [0]*4
            self.enemy = enemy

        def add_proc(self, weapon_effect):
            if len(self.heat_proc_dq) == 0:
                self.offset = self.enemy.time
                self.next_event = self.offset + 1
                # create new heat strip
                self.heat_proc_armor_strip = self.HeatProcArmorStrip(self.enemy, weapon_effect)
                # create new armor regen
                self.heat_proc_armor_regen = self.HeatProcArmorRegen(self.enemy, weapon_effect)

            hpr = self.HeatProc(self.enemy, weapon_effect)
            self.expiry = self.enemy.time + 6 * (1+weapon_effect.weapon.status_duration_mods)
            self.total_damage_list[3] += hpr.damage
            self.heat_proc_dq.append(hpr)

        def get_next_event_time(self):
            if len(self.heat_proc_dq) > 0:
                # front of deque is end in terms of list comp
                return min(self.heat_proc_dq[-1].expiry, self.next_event, self.heat_proc_armor_strip.next_event, self.heat_proc_armor_regen.next_event)
            else:
                return 2**31

        def execute(self):
            '''
                Damage event:       0
                Expiry event:       1
                Armor Strip event:  2
                Armor Regen event:  3
            '''

            self.event_list[0] = self.next_event
            self.event_list[1] = self.expiry
            self.event_list[2] = self.heat_proc_armor_strip.next_event
            self.event_list[3] = self.heat_proc_armor_regen.next_event

            selected_event = self.event_list.index(min(self.event_list))

            if selected_event == 0:
                app_dmg = self.enemy.apply_damage(self.total_damage_list, self.heat_proc_dq[-1].weapon_effect, proc = True)
                self.total_applied_damage += app_dmg
                self.next_event += 1

            elif selected_event == 1:
                hpr = self.heat_proc_dq.popleft()
                self.total_damage_list[3] -= hpr.damage
                del hpr
                self.expiry = 0
                # start heat proc armor regen
                self.heat_proc_armor_regen.offset = enemy.time
                self.heat_proc_armor_regen.next_event = self.offset + self.time_increment
            elif selected_event == 2:
                self.heat_proc_armor_strip.execute()
            elif selected_event == 3:
                self.heat_proc_armor_regen.execute()

        class HeatProc:
            def __init__(self, enemy, weapon_effect):
                if weapon_effect.trigger =='HELD':
                    self.damage = 0.5 * (1+weapon_effect.weapon.heat_mods) * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.innate_damage_reduction * weapon_effect.multishot_state
                else:
                    self.damage = 0.5 * (1+weapon_effect.weapon.heat_mods) * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.innate_damage_reduction

                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.ticks = int(self.life)
                self.expiry = enemy.time + self.life
                self.expired = False
                self.weapon_effect = weapon_effect

        class HeatProcArmorStrip:
            def __init__(self, enemy, weapon_effect):
                self.offset = enemy.time
                self.time_increment = 0.5 * (1+weapon_effect.weapon.status_duration_mods)
                self.next_event = self.offset + self.time_increment
                self.index = 0
                self.enemy = enemy
                self.expired = False

            def execute(self):
                if self.index == 0:
                    self.enemy.heat_armor_strip = 0.85
                elif self.index == 1:
                    self.enemy.heat_armor_strip = 0.7
                elif self.index == 2:
                    self.enemy.heat_armor_strip = 0.6
                elif self.index == 3:
                    self.enemy.heat_armor_strip = 0.5

                self.index += 1
                self.next_event = self.next_event + self.time_increment

                if self.index >= 4:
                    self.expired = True
                    self.next_event = 2**32

        class HeatProcArmorRegen:
            def __init__(self, enemy, weapon_effect):

                self.time_increment = 1.5 * (1+weapon_effect.weapon.status_duration_mods)
                self.offset = 10000000000
                self.next_event = 10000000000
                self.index = 0
                self.enemy = enemy
                self.expired = False

            def execute(self):
                if self.index == 0:
                    self.enemy.heat_armor_strip = 0.6
                elif self.index == 1:
                    self.enemy.heat_armor_strip = 0.7
                elif self.index == 2:
                    self.enemy.heat_armor_strip = 0.85
                elif self.index == 3:
                    self.enemy.heat_armor_strip = 1

                self.index += 1
                self.next_event = self.next_event + self.time_increment

                if self.index >= 4:
                    self.expired = True
                    self.next_event = 2**32

    class ColdProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'COLD'

        def add_proc(self, weapon_effect):
            np = self.ColdProc(self.enemy, weapon_effect)
            if len(self.proc_dq) == 0:
                self.next_event = np.expiry
            elif len(self.proc_dq) == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            if len(self.proc_dq) == 0:
                self.next_event = 2**32
            else:
                self.next_event = self.proc_dq[0].expiry

        class ColdProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    class ElectricProcManager:
        # For heat procs, the offset is constant, no need to pop an append elements to keep track of next event
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.offset = 2**31
            self.next_event = self.offset
            self.total_damage_list = [0]*20
            self.event_list = [0]*2
            self.enemy = enemy
            self.proc_id = 'ELECTRIC'
            self.total_applied_damage = 0


        def add_proc(self, weapon_effect):
            if len(self.proc_dq) == 0:
                self.offset = self.enemy.time
                self.next_event = self.offset

            np = self.ElectricProc(self.enemy, weapon_effect)
            self.total_damage_list[5] += np.damage
            self.proc_dq.append(np)

        def get_next_event_time(self):
            if len(self.proc_dq) > 0:
                # front of deque is end in terms of list comp
                return min(self.proc_dq[0].expiry, self.next_event)
            else:
                return 2**31

        def execute(self):
            '''
                Damage event:       0
                Expiry event:       1
            '''
            self.event_list[0] = self.next_event
            self.event_list[1] = self.proc_dq[0].expiry

            selected_event = self.event_list.index(min(self.event_list))

            if selected_event == 0:
                bfore = self.enemy.current_health
                app_dmg = self.enemy.apply_damage(self.total_damage_list, self.proc_dq[0].weapon_effect, proc = True)
                self.total_applied_damage += app_dmg
                # print("     Electric Proc: %.2f, Time: %.2f"%(bfore-self.enemy.current_health, self.enemy.time))
                self.next_event += 1
            elif selected_event == 1:
                np = self.proc_dq.popleft()
                self.total_damage_list[5] -= np.damage
                del np
                self.expiry = 2**31

        class ElectricProc:
            def __init__(self, enemy, weapon_effect):
                # print("Multishot state: %.2f, CD state: %.2f, Viral Mult: %.2f"%(weapon_effect.multishot_state,enemy.get_critical_damage_state(weapon_effect), enemy.viral_multiplier))
                if weapon_effect.trigger =='HELD':
                    self.damage = 0.5 * (1+weapon_effect.weapon.electric_mods) * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.get_all_enemy_multipliers() * weapon_effect.multishot_state
                else:
                    self.damage = 0.5 * (1+weapon_effect.weapon.electric_mods) * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.get_all_enemy_multipliers()
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False
                self.weapon_effect = weapon_effect


    class ToxinProcManager:
        def __init__(self, enemy):
            self.enemy = enemy
            # self.ProcContainer(self.enemy) for i in range(10)
            self.container_list = deque([])
            self.container_index = 0
            self.proc_id = 'TOXIN'
            self.total_applied_damage = 0

        def increment_index(self, max, current_index):
            if current_index+1 > max-1:
                return 0
            else:
                return current_index + 1

        def decrement_index(self, max, current_index):
            if current_index-1 < 0:
                return max-1
            else:
                return current_index-1

        def add_proc(self, weapon_effect):
            # create new proc
            np = self.ToxinProc(self.enemy, weapon_effect)

            # get previous added container
            previous_index = self.decrement_index(len(self.container_list),self.container_index)
            res_container = None
            for container in self.container_list:
                if container.index == previous_index:
                    res_container = container
                    break

            # Check if proc happened at the same time
            if len(self.container_list)>0 and res_container is not None and res_container.proc_dq[-1].offset == self.enemy.time:
                # add it to same container as last proc
                res_container.add_proc(np)
            else:
                if len(self.container_list)<10:
                    self.container_list.append(self.ProcContainer(self.enemy, self.container_index, self))
                # add to next container and increment container index
                for container in self.container_list:
                    if container.index == self.container_index:
                        container.add_proc(np)
                        break
                self.container_index = self.increment_index( 10, self.container_index)

        def get_next_event_time(self):
            # Return event time
            if len(self.container_list)>0:
                return self.container_list[0].next_event
            else:
                return 12345678910

        def execute(self):

            '''
            print("ToxinProcManager.execute()")

            print("\nPRE EXECUTION: ")
            for container in self.container_list:
                print("Container Index: %d, Procs times: "%container.index, end="")
                for proc in container.proc_dq:
                    print(proc.next_event, end=", ")
                print("")
            '''

            #pdb.set_trace()
            # execute proc if exists
            if len(self.container_list[0].proc_dq) > 0:
                self.container_list[0].execute()
                if len(self.container_list[0].proc_dq)<=0:
                    self.container_list.popleft()
                    # shift all indeces down and set container_index to end
                    for container in self.container_list:
                        container.index-=1
                    self.container_index=len(self.container_list)
                else:
                    self.container_list.append(self.container_list.popleft())
            else:
                print("No proc to execute")

            '''
            print("\nPOST EXECUTION: %d")
            for container in self.container_list:
                print("Container Index: %d, Procs times: "%container.index, end="")
                for proc in container.proc_dq:
                    print(proc.next_event, end=", ")
                print("")
            '''

            #pdb.set_trace()

        class ProcContainer:
            def __init__(self, enemy, index, manager):
                self.manager = manager
                self.enemy = enemy
                self.index = index
                self.next_event = 696969696969
                self.total_damage = [0]*20
                self.proc_dq = deque([])

            def add_proc(self, proc):
                # If it is a new container, set the event time to first proc
                if len(self.proc_dq) == 0:
                    self.next_event = proc.next_event
                # add proc to list
                self.proc_dq.append(proc)
                # add proc damage to total
                self.total_damage[6] += proc.damage[6]

            def execute(self):
                app_dmg = self.enemy.apply_damage(self.total_damage, self.proc_dq[0].weapon_effect, proc = True)
                self.manager.total_applied_damage += app_dmg
                # Increment individual proc stats
                for proc in self.proc_dq:
                    proc.next_event += 1
                    proc.executed_count += 1
                # Remove any expired procs
                self.recursive_pop()
                # Change container level next_event time to valid proc
                if len(self.proc_dq)==0:
                    self.next_event = 420420420420
                self.next_event += 1

            def recursive_pop(self):
                # Check if oldest proc has expired
                if self.proc_dq[0].executed_count >= self.proc_dq[0].ticks:
                    # Remove damage from total
                    self.total_damage[6] -= self.proc_dq[0].damage[6]
                    # Remove procc from list
                    self.proc_dq.popleft()

                    # if there are more procs in the list, check if they expired
                    if len(self.proc_dq)>0:
                        self.recursive_pop()

        class ToxinProc:
            def __init__(self, enemy, weapon_effect):
                self.weapon_effect = weapon_effect
                self.enemy = enemy

                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = self.enemy.time + self.life
                self.expired = False
                self.executed_count = 0
                self.ticks = int(self.life)
                self.damage = [0]*20
                if weapon_effect.trigger =='HELD':
                    self.damage[6] = 0.5 * (1+weapon_effect.weapon.toxin_mods) * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.innate_damage_reduction * weapon_effect.nultishot_state
                else:
                    self.damage[6] = 0.5 * (1+weapon_effect.weapon.toxin_mods) * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.innate_damage_reduction

                self.offset = self.enemy.time
                self.next_event = self.offset + 1

    class BlastProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'BLAST'

        def add_proc(self, weapon_effect):
            np = self.BlastProc(self.enemy, weapon_effect)
            if len(self.proc_dq) == 0:
                self.next_event = np.expiry
            elif len(self.proc_dq) == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            if len(self.proc_dq) == 0:
                self.next_event = 2**32
            else:
                self.next_event = self.proc_dq[0].expiry

        class BlastProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    class RadiationProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'RADIATION'

        def add_proc(self, weapon_effect):
            np = self.RadiationProc(self.enemy, weapon_effect)
            if len(self.proc_dq) == 0:
                self.next_event = np.expiry
            elif len(self.proc_dq) == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            if len(self.proc_dq) == 0:
                self.next_event = 2**32
            else:
                self.next_event = self.proc_dq[0].expiry

        class RadiationProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    class GasProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.offset = 2**31
            self.next_event = self.offset
            self.total_damage_list = [0]*20
            self.event_list = [0]*2
            self.enemy = enemy
            self.proc_id = 'GAS'
            self.total_applied_damage = 0

        def add_proc(self, weapon_effect):
            if len(self.proc_dq) == 0:
                self.offset = self.enemy.time
                self.next_event = self.offset
            elif len(self.proc_dq) == 10:
                # remove oldest proc
                old = self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry
                self.total_damage_list[9] -= old.damage

            np = self.GasProc(self.enemy, weapon_effect)
            self.total_damage_list[9] += np.damage
            self.proc_dq.append(np)

        def get_next_event_time(self):
            if len(self.proc_dq) > 0:
                # front of deque is end in terms of list comp
                return min(self.proc_dq[0].expiry, self.next_event)
            else:
                return 2**31

        def execute(self):
            '''
                Damage event:       0
                Expiry event:       1
            '''
            self.event_list[0] = self.next_event
            self.event_list[1] = self.proc_dq[0].expiry

            selected_event = self.event_list.index(min(self.event_list))

            if selected_event == 0:
                app_dmg = self.enemy.apply_damage(self.total_damage_list, self.proc_dq[0].weapon_effect, proc = True)
                self.total_applied_damage += app_dmg
                self.next_event += 1
            elif selected_event == 1:
                np = self.proc_dq.popleft()
                self.total_damage_list[9] -= np.damage
                del np
                self.expiry = 2**31

        class GasProc:
            def __init__(self, enemy, weapon_effect):
                if weapon_effect.trigger =='HELD':
                    self.damage = 0.5 * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.get_all_enemy_multipliers() * weapon_effect.multishot_state
                else:
                    self.damage = 0.5 * weapon_effect.modded_total_base_damage * (1+weapon_effect.weapon.bane_mods) * enemy.get_critical_damage_state(weapon_effect) * enemy.get_all_enemy_multipliers()

                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False
                self.weapon_effect = weapon_effect

    class MagneticProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'MAGNETIC'

        def add_proc(self, weapon_effect):
            np = self.MagneticProc(self.enemy, weapon_effect)
            length = len(self.proc_dq)
            if length == 0:
                self.next_event = np.expiry
            elif length == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)
            length = len(self.proc_dq)

            if length >= 1:
                self.enemy.magnetic_multiplier = 2 + 0.25*(length-1)
            else:
                self.enemy.magnetic_multiplier = 1

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            length = len(self.proc_dq)
            if length == 0:
                self.next_event = 2**32
                self.enemy.magnetic_multiplier = 1
            else:
                self.next_event = self.proc_dq[0].expiry
                self.enemy.magnetic_multiplier = 2 + 0.25*(length-1)

        class MagneticProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    class ViralProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'VIRAL'

        def add_proc(self, weapon_effect):
            np = self.ViralProc(self.enemy, weapon_effect)
            length = len(self.proc_dq)
            if length == 0:
                self.next_event = np.expiry
                self.enemy.viral_multiplier = 2
            elif length == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)
            length = len(self.proc_dq)

            if length >= 1:
                self.enemy.viral_multiplier = 2 + 0.25*(length-1)
            else:
                self.enemy.viral_multiplier = 1

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            length = len(self.proc_dq)
            if length == 0:
                self.next_event = 2**32
                self.enemy.viral_multiplier = 1
            else:
                self.next_event = self.proc_dq[0].expiry
                self.enemy.viral_multiplier = 2 + 0.25*(length-1)

        class ViralProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    class CorrosiveProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'CORROSIVE'

        def add_proc(self, weapon_effect):
            np = self.CorrosiveProc(self.enemy, weapon_effect)
            length = len(self.proc_dq)
            if length == 0:
                self.next_event = np.expiry
            elif length == 10:
                # remove oldest proc
                self.proc_dq.popleft()
                self.next_event = self.proc_dq[0].expiry

            self.proc_dq.append(np)
            length = len(self.proc_dq)

            if length >= 1:
                self.enemy.corrosive_armor_strip = 1-(0.2+0.06*length)
            else:
                self.enemy.corrosive_armor_strip = 1

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            length = len(self.proc_dq)
            if length == 0:
                self.next_event = 2**32
                self.enemy.corrosive_armor_strip = 1
            else:
                self.next_event = self.proc_dq[0].expiry
                self.enemy.corrosive_armor_strip = 1-(0.2+0.06*length)

        class CorrosiveProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 6 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False


    class VoidProcManager:
        def __init__(self, enemy):
            self.proc_dq = deque([])
            self.enemy = enemy
            self.next_event = 2**32
            self.proc_id = 'VOID'

        def add_proc(self, weapon_effect):
            np = self.BlastProc(self.enemy, weapon_effect)
            if len(self.proc_dq) == 0:
                self.next_event = np.expiry
            elif len(self.proc_dq) == 1:
                # remove oldest proc
                self.proc_dq.popleft()

            self.proc_dq.append(np)
            self.next_event = self.proc_dq[0].expiry

        def get_next_event_time(self):
            return self.next_event

        def execute(self):
            self.proc_dq.popleft()
            if len(self.proc_dq) == 0:
                self.next_event = 2**32
            else:
                self.next_event = self.proc_dq[0].expiry

        class BlastProc:
            def __init__(self, enemy, weapon_effect):
                self.life = 4 * (1+weapon_effect.weapon.status_duration_mods)
                self.expiry = enemy.time + self.life
                self.expired = False

    def get_critical_damage_state(self, weapon_effect, tier=None):
        crit_enhance_proc = 1 if random() < weapon_effect.weapon.critical_enhance_mods else 0
        base = 0.8 if self.enemy_type == 'ET_DEMOLISHER' and tier !=0 else 1
        #base =1
        if tier is not None:
            if tier != 0:
                tier = tier + crit_enhance_proc
            return (tier) * (weapon_effect.modded_critical_multiplier * self.critical_headshot_bonus - base) + base
        else:
            if weapon_effect.critical_proc:
                return (weapon_effect.min_critical_tier + 1 + crit_enhance_proc) * (weapon_effect.modded_critical_multiplier * self.critical_headshot_bonus - base) + base
            else:
                if weapon_effect.min_critical_tier == 0:
                    crit_enhance_proc = 0
                    base = 1
                return (weapon_effect.min_critical_tier + crit_enhance_proc) * (weapon_effect.modded_critical_multiplier * self.critical_headshot_bonus - base) + base

    def get_first_shot_damage(self, dmg, weapon_effect, crit_tier, multi_madness = 1):
        applied_shield_damage = 0
        applied_health_damage = 0
        if self.current_shield > 0:
            for i, elem in enumerate(dmg):
                if i != 6:
                    applied_shield_damage += elem * self.shield_modifiers[i] * self.magnetic_multiplier
                else:
                    applied_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * self.get_modifier_armor_reduction(i)
        else:
            for i, elem in enumerate(dmg):
                applied_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * self.get_modifier_armor_reduction(i)

        applied_shield_damage = applied_shield_damage * self.get_all_enemy_multipliers()
        applied_health_damage = applied_health_damage * self.get_all_enemy_multipliers()

        #print("calc dmg: %.10f"%applied_health_damage)
        #print("DR: %.10f"%self.get_special_damage_reduction(applied_health_damage* multi_madness, weapon_effect, crit_tier))

        applied_shield_damage = applied_shield_damage * self.get_special_damage_reduction(applied_shield_damage * multi_madness, weapon_effect, crit_tier) * self.get_critical_damage_state(weapon_effect, crit_tier)
        applied_health_damage = applied_health_damage * self.get_special_damage_reduction(applied_health_damage * multi_madness, weapon_effect, crit_tier) * self.get_critical_damage_state(weapon_effect, crit_tier)




        #print("After: ", applied_health_damage)
        #print(applied_health_damage * self.get_special_damage_reduction(applied_health_damage, weapon_effect) * self.get_critical_damage_state(weapon_effect) * self.get_all_enemy_multipliers(), self.get_critical_damage_state(weapon_effect))

        overflow_health_damage = 0
        if self.current_shield < 0:
            ratio = abs(self.current_shield/applied_shield_damage)
            for i, elem in enumerate(dmg):
                #elem = round(elem/weapon_effect.quantum, 0) * weapon_effect.quantum
                overflow_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * ratio * self.get_modifier_armor_reduction(i)

            overflow_health_damage = overflow_health_damage * self.get_all_enemy_multipliers()
            overflow_health_damage = overflow_health_damage * self.get_special_damage_reduction(overflow_health_damage * multi_madness, weapon_effect, crit_tier) * self.get_critical_damage_state(weapon_effect, crit_tier)

        return ( (applied_shield_damage), (applied_health_damage), (overflow_health_damage) )

    def get_unreduced_damage_and_dps(self, dmg, weapon_effect, multi_madness = 1):
        applied_shield_damage = 0
        applied_health_damage = 0
        if self.current_shield > 0:
            for i, elem in enumerate(dmg):
                if i != 6:
                    applied_shield_damage += elem * self.shield_modifiers[i] * self.magnetic_multiplier
                else:
                    applied_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * self.get_modifier_armor_reduction(i)
        else:
            for i, elem in enumerate(dmg):
                applied_health_damage += elem * self.health_modifiers[i] * self.viral_multiplier * self.get_modifier_armor_reduction(i)

        applied_shield_damage = applied_shield_damage * self.get_all_enemy_multipliers() * multi_madness
        applied_health_damage = applied_health_damage * self.get_all_enemy_multipliers() * multi_madness

        shield_dps = applied_shield_damage * weapon_effect.dps_multiplier
        health_dps = applied_health_damage * weapon_effect.dps_multiplier

        # Weird shotgun mechanic
        if weapon_effect.base_pellets > 1:
            shield_dps = shield_dps/2
            health_dps = health_dps/2

        return ( applied_shield_damage, applied_health_damage ,shield_dps, health_dps)

    class Modifier:
        '''
        0   Impact
        1   Puncture
        2   Slash
        3   Heat
        4   Cold
        5   Electric
        6   Toxin
        7   Blast
        8   Radiation
        9   Gas
        10  Magnetic
        11  Viral
        12  Corrosive
        13  Void
        14  True
        15
        16
        17
        18
        19
        '''
        def __init__(self):
            self.ferrite = [1,1.5,0.85,1,1,1,1.25,0.75,1,1,1,1,1.75,1,1,1,1,1,1,1]
            self.alloy = [1,1.15,0.5,1,1.25,0.5,1,1,1.75,1,0.5,1,1,1,1,1,1,1,1,1]
            self.infested_sinew = [1,1.25,1,1,1.25,1,1,0.5,1.5,1,1,1,1,1,1,1,1,1,1,1]

            self.proto_shield = [1.15,0.5,1,0.5,1,1,1,1,1,1,1.75,1,0.5,1,1,1,1,1,1,1]
            self.shield = [1.5,0.8,1,1,1.5,1,1,1,0.75,1,1.75,1,1,1,1,1,1,1,1,1]
            self.eidolon_shield = [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0]

            self.infested = [1,1,1.25,1.25,1,1,1,1,0.5,1.75,1,0.5,1,1,1,1,1,1,1,1]
            self.robotic = [1,1.25,0.75,1,1,1.5,0.75,1,1.25,1,1,1,1,1,1,1,1,1,1,1]
            self.cloned_flesh = [0.75,1,1.25,1.25,1,1,1,1,1,0.5,1,1.75,1,0.5,1,1,1,1,1,1]
            self.infested_flesh = [1,1,1.5,1.5,0.5,1,1,1,1,1.5,1,1,1,1,1,1,1,1,1,1]
            self.flesh = [0.75,1,1.25,1,1,1,1.5,1,1,0.75,1,1.5,1,1,1,1,1,1,1,1]
            self.fossilized = [1,1,1.15,1,0.75,1,0.5,1.5,0.25,1,1,1,1.75,0.5,1,1,1,1,1,1]
            self.machinery = [1.25,1,1,1,1,1.5,0.75,1.75,1,1,1,0.75,1,0.5,1,1,1,1,1,1]

            self.tenno_shield = [0.75]*20
            self.tenno_health = [1]*20
            self.tenno_armor = [1]*20

            self.none = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        def get_modifier(self, name):
            if name == "Ferrite":
                return self.ferrite
            elif name == "Alloy":
                return self.alloy
            elif name == "Proto Shield":
                return self.proto_shield
            elif name == "Shield":
                return self.shield
            elif name == "Eidolon Shield":
                return self.eidolon_shield
            elif name == "Infested":
                return self.infested
            elif name == "Robotic":
                return self.robotic
            elif name == "Cloned Flesh":
                return self.cloned_flesh
            elif name == "Infested Flesh":
                return self.infested_flesh
            elif name == "Flesh":
                return self.flesh
            elif name == "Fossilized":
                return self.fossilized
            elif name == "Infested Sinew":
                return self.infested_sinew
            elif name == "Machinery":
                return self.machinery
            elif name == "Tenno Health":
                return self.tenno_health
            elif name == "Tenno Shield":
                return self.tenno_shield
            elif name == "Tenno Armor":
                return self.tenno_armor

    def get_scaled_health(self):
        f1 = 1 + 0.015*(self.level - self.base_level)**2
        if self.old_scaling:
            return self.base_health*f1
        f2 = 1 + (24*(5**0.5)/5)*(self.level - self.base_level)**0.5
        if self.level <= 70:
            return self.base_health*f1
        elif self.level >= 80:
            return self.base_health*f2
        else:
            t = (self.level-self.base_level-70)/10
            s = 3*t**2-2*t**3
            return self.base_health*f1*(1-s)+f2*s

    def get_scaled_shield(self):
        if self.base_shield <= 0:
            return 0
        f0 = 1 + 0.0075*(self.level - self.base_level)**2
        if self.old_scaling:
            return self.base_shield*f0
        f1 = 1 + 0.02*(self.level - self.base_level)**1.75
        f2 = 1 + 1.6*(self.level - self.base_level)**0.75
        if self.level < 70:
            return self.base_shield*f1
        elif self.level > 80:
            return self.base_shield*f2
        else:
            t = (self.level-self.base_level-70)/10
            s = 3*t**2-2*t**3
            return self.base_shield*f1*(1-s)+f2*s

    def get_scaled_armor(self):
        if self.base_armor <= 0:
            return 0
        f1 = 1 + 0.005*(self.level - self.base_level)**1.75
        if self.old_scaling:
            return self.base_armor*f1
        f2 = 1 + 0.4*(self.level - self.base_level)**0.75
        if self.level < 70:
            return self.base_armor*f1
        elif self.level > 80:
            return self.base_armor*f2
        else:
            t = (self.level-self.base_level-70)/10
            s = 3*t**2-2*t**3
            return self.base_armor*f1*(1-s)+f2*s

    def get_modifier_armor_reduction(self, index):
        armr = self.current_armor * self.corrosive_armor_strip * self.heat_armor_strip
        if int(armr) > 0:
            if index ==14:
                return 1
            else:
                return self.armor_modifiers[index]/(1+(2-self.armor_modifiers[index])*armr/300)
        else:
            return 1
    def get_modified_armor(self):
        return self.current_armor * self.corrosive_armor_strip * self.heat_armor_strip

    def get_all_enemy_multipliers(self):
        #
        return self.innate_damage_reduction *self.body_part_multiplier

    def get_special_damage_reduction(self, applied_dmg, weapon_effect, crit_tier=0):
        if applied_dmg == 0:
            return 1

        #if weapon_effect.trigger == "HELD":
        if False:
            dps = applied_dmg * weapon_effect.dps_multiplier * weapon_effect.multishot_state
        else:
            dps = applied_dmg * weapon_effect.dps_multiplier

        # Weird shotgun mechanic
        if weapon_effect.base_pellets > 1:
            dps = dps/2

        if weapon_effect.weapon.hit_scaling:
            dps = applied_dmg

        if self.enemy_type == 'ET_NORMAL':
            return 1
        elif self.enemy_type == 'ET_DEMOLISHER' or self.enemy_type == 'ET_DEMOLYST'or self.enemy_type == 'ET_DEIMOS_JUGULUS' or self.enemy_type == 'ET_DEIMOS_SAXUM':
            if dps <= 1000:
                return 1
            elif dps >= 1000 and dps <= 2500:
                return 0.8+200/dps
            elif dps >= 2500 and dps <= 5000:
                return 0.7+450/dps
            elif dps >= 5000 and dps <= 10000:
                return 0.4+1950/dps
            elif dps >= 10000 and dps <= 20000:
                return 0.2+3950/dps
            elif dps >= 20000:
                return 0.1+5950/dps
        elif self.enemy_type == 'ET_CONDRIX':
            if dps <= 1000:
                return 1
            elif dps >= 1000 and dps <= 2500:
                return 0.8+200/dps
            elif dps >= 2500 and dps <= 5000:
                return 0.7+450/dps
            elif dps >= 5000 and dps <= 10000:
                return 0.4+1950/dps
            elif dps >= 10000 and dps <= 20000:
                return 0.2+3950/dps
            elif dps >= 20000:
                return 0.1+5950/dps
        elif self.enemy_type == 'ET_EIDOLON':
            crit = self.get_critical_damage_state(weapon_effect, crit_tier)
            tot_damage = applied_dmg * crit
            thresh = 300/(weapon_effect.modded_fire_rate * weapon_effect.modded_pellets)
            res = ((tot_damage-thresh)*0.1+thresh)*0.4
            #print("crit: %.2f, thresh: %.2f, DR: %.4f"%(crit,thresh,res/tot_damage))
            return res/tot_damage
        elif self.enemy_type == 'ET_LEPHANTIS':
            crit = self.get_critical_damage_state(weapon_effect, weapon_effect.current_critical_tier)
            tot_damage = applied_dmg * crit
            damage_cap = self.current_health * 0.1 + 450
            #print("ToT: %.1f, Crit: %.3f, Health: %.1f, Damage Cap: %.1f"%(tot_damage, crit, self.current_health, damage_cap))

            if tot_damage <=450:
                damage_mult = 1
            elif abs(self.time - self.previous_hit_time) < 0.27:
                damage_mult = 0.1
            else:
                damage_mult = 0.1+450/tot_damage

            reduced_damage = tot_damage * damage_mult
            #print(reduced_damage)

            if reduced_damage > damage_cap:
                return damage_cap/applied_dmg
            else:
                return reduced_damage/(applied_dmg*crit)
