import json
from types import SimpleNamespace
from random import random
import constant
import numpy as np
import proc_manager as pm

class Enemy:
    def __init__(self, name, level, ui):
        self.modifiers = self.Modifier()
        self.name = name
        self.level = level
        
        self.old_scaling = ui.old_scaling_checkbox.isChecked()
        self.SP_armor_buff = ui.SP_armor_buff_spinner.value()
        self.SP_health_buff = ui.SP_health_buff_spinner.value()
        self.SP_shield_buff = ui.SP_shield_buff_spinner.value()

        self.get_stats()
        
        self.impact_proc_manager = pm.ImpactProcManager(self)
        self.puncture_proc_manager = pm.PunctureProcManager(self)
        self.slash_proc_manager = pm.SlashProcManager(self)
        self.heat_proc_manager = pm.HeatProcManager(self)
        self.cold_proc_manager = pm.ColdProcManager(self)
        self.electric_proc_manager = pm.ElectricProcManager(self)
        self.toxin_proc_manager = pm.ToxinProcManager(self)
        self.blast_proc_manager = pm.BlastProcManager(self)
        self.radiation_proc_manager = pm.RadiationProcManager(self)
        self.gas_proc_manager = pm.GasProcManager(self)
        self.magnetic_proc_manager = pm.MagneticProcManager(self)
        self.viral_proc_manager = pm.ViralProcManager(self)
        self.corrosive_proc_manager = pm.CorrosiveProcManager(self)
        self.void_proc_manager = pm.VoidProcManager(self)

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
        self.critical_headshot_bonus = 2 if ui.critical_headshot_bonus_checkbox.isChecked() else 1

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
        self.damage_instance_list = []

        self.health_event_list = [(-1e-3,self.current_health)]
        self.shield_event_list = [(-1e-3,self.current_shield)]
        self.armor_event_list = [(-1e-3,self.current_armor)]

        self.kill_time = 9999

    def get_stats(self):
        with open('./enemy_data.json') as f:
            data = json.load(f)
        e = data[self.name]
        e = json.dumps(e)
        enemy_data = json.loads(e, object_hook=lambda d: SimpleNamespace(**d))
        
        self.health_type = enemy_data.health_type
        self.shield_type = enemy_data.shield_type
        self.armor_type = enemy_data.armor_type

        self.base_health = enemy_data.base_health
        self.base_shield = enemy_data.base_shield
        self.base_armor = enemy_data.base_armor
        self.base_level = enemy_data.base_level

        self.enemy_type = enemy_data.enemy_type

        self.level = self.base_level if self.level < self.base_level else self.level

        self.health_modifiers = self.modifiers.get_modifier(self.health_type)
        self.shield_modifiers = self.modifiers.get_modifier(self.shield_type)
        self.armor_modifiers = self.modifiers.get_modifier(self.armor_type)

        self.armor_debuff = 1
        self.health_debuff = 1
        self.armor_debuff = 1

        self.max_health = self.get_scaled_health() * self.SP_health_buff
        self.max_shield = self.get_scaled_shield() * self.SP_shield_buff
        self.max_armor = self.get_scaled_armor() * self.SP_armor_buff

        self.ehp = self.max_health*(1+self.max_armor/300)+self.max_shield

        self.current_health = self.max_health
        self.current_shield = self.max_shield
        self.current_armor = self.max_armor

    def reset(self):
        self.current_health = self.max_health
        self.current_shield = self.max_shield
        self.current_armor = self.max_armor

        self.previous_hit_time = 0
        self.time = 0
        self.total_unreduced_damage = 0
        self.damage_instance_list = []

        self.health_event_list = [(-1e-3,self.current_health)]
        self.shield_event_list = [(-1e-3,self.current_shield)]
        self.armor_event_list = [(-1e-3,self.current_armor)]

        self.kill_time = 9999

        self.magnetic_multiplier = 1
        self.viral_multiplier = 1
        self.corrosive_armor_strip = 1
        self.heat_armor_strip = 1

        for pm in self.proc_managers:
            pm.reset()

    def kill(self, weapon):
        weapon.apply_proc_immunity(self.proc_immunity)
        event_list = weapon.weapon_effects+self.proc_managers
        while self.current_health > 0:
            # find event to execute
            mindex = min(range(len(event_list)), key=lambda i: event_list[i].get_next_event_time())
            self.set_time(event_list[mindex].get_next_event_time())
            event_list[mindex].execute(self)

            # enemy state logging
            if self.get_modified_armor() != self.armor_event_list[-1][1]:
                self.armor_event_list.append((self.time-1e-3, self.armor_event_list[-1][1]))
                self.armor_event_list.append((self.time, self.get_modified_armor()))
            if self.current_health != self.health_event_list[-1][1]:
                self.health_event_list.append((self.time-1e-3, self.health_event_list[-1][1]))
                self.health_event_list.append((self.time, self.current_health))
            if self.current_shield != self.shield_event_list[-1][1]:
                self.shield_event_list.append((self.time-1e-3, self.shield_event_list[-1][1]))
                self.shield_event_list.append((self.time, self.current_shield))

            if self.time >20:
                self.kill_time = (self.max_health+self.max_shield) * self.time/(self.max_health-self.current_health+self.max_shield-self.current_shield)
                return 
        self.kill_time = max(0.001, self.time)

    def apply_damage(self, dmg, weapon_effect, proc=False):
        self.total_unreduced_damage += sum(dmg)
        dmg = np.array(dmg)
        applied_shield_damage = 0
        applied_health_damage = 0
        total_applied_damage = self.current_health+self.current_shield
        if self.current_shield > 0:
            applied_shield_damage += np.sum(multi_dot([dmg , self.shield_modifiers , constant.SHIELD_MASK])) * self.get_all_enemy_multipliers(constant.VT_SHIELD)
            applied_health_damage += np.sum(multi_dot([dmg , self.health_modifiers , constant.SHIELDED_HEALTH_MASK , self.get_armor_reduction()])) * self.get_all_enemy_multipliers(constant.VT_HEALTH)
        else:
            applied_health_damage += np.sum(multi_dot([dmg , self.health_modifiers , self.get_armor_reduction()])) * self.get_all_enemy_multipliers(constant.VT_HEALTH)

        self.current_shield -= self.get_special_damage_reduction(applied_shield_damage, weapon_effect, proc=proc)
        self.current_health -= self.get_special_damage_reduction(applied_health_damage, weapon_effect, proc=proc)

        if not (proc and dmg[3]) and not proc:
            self.damage_instance_list.append(round(total_applied_damage - (self.current_health+self.current_shield),0))

        applied_health_damage = 0
        if self.current_shield < 0 and self.current_health>0:
            ratio = abs(self.current_shield/applied_shield_damage)
            applied_health_damage += np.sum(multi_dot([dmg , self.health_modifiers , self.get_armor_reduction()]))* self.get_all_enemy_multipliers(constant.VT_HEALTH) * ratio
            self.current_health -= self.get_special_damage_reduction(applied_health_damage, weapon_effect, proc=proc)
            self.current_shield = 0

        if weapon_effect.weapon.mod_config.shattering_impact and dmg[0]:
            self.base_armor -= 6
            self.current_armor = self.get_scaled_armor()*self.SP_armor_buff
        if weapon_effect.weapon.mod_config.amalgam_argonak_metal_auger:
            self.base_armor -= 6
            self.current_armor = self.get_scaled_armor()*self.SP_armor_buff

        if self.current_health <0:
            self.current_health = 0
        total_applied_damage -= (self.current_health+self.current_shield)
        return total_applied_damage

    def set_time(self, t):
        self.previous_hit_time = self.time
        self.time = t

    def apply_status(self, weapon_effect):
        # apply guaranteed status effects (>100% sc)
        for i in range( int(weapon_effect.status_chance.modded) ):
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.proc_managers[i].add_proc(weapon_effect)
                    break
                proc_roll -= sts

        # apply remaining status chance
        if weapon_effect.weapon_state.status_proc:
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.proc_managers[i].add_proc(weapon_effect)
                    break
                proc_roll -= sts

    def apply_beam_status(self, weapon_effect):
        # apply guaranteed status effects (>100% sc)
        for i in range( int(weapon_effect.status_chance.modded * weapon_effect.weapon_state.multishot_state[0]) ):
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.proc_managers[i].add_proc(weapon_effect)
                    break
                proc_roll -= sts

        # apply remaining status chance
        if random()<( (weapon_effect.status_chance.modded*weapon_effect.weapon_state.multishot_state[0])%1 ):
            proc_roll = random()
            for i, sts in enumerate(weapon_effect.status_effect_chance):
                if proc_roll <= sts:
                    self.proc_managers[i].add_proc(weapon_effect)
                    break
                proc_roll -= sts

    def get_critical_damage_state(self, weapon_effect, tier=None):
        if tier is not None:
            if tier != 0:
                tier = tier + weapon_effect.weapon_state.crit_enhance_proc
            return (tier) * (weapon_effect.critical_multiplier.modded * self.critical_headshot_bonus-1) +1
        else:
            if weapon_effect.weapon_state.critical_proc:
                return (weapon_effect.min_critical_tier + 1 + weapon_effect.weapon_state.crit_enhance_proc) * (weapon_effect.critical_multiplier.modded * self.critical_headshot_bonus-1)+1
            else:
                return (weapon_effect.min_critical_tier + weapon_effect.weapon_state.crit_enhance_proc) * (weapon_effect.critical_multiplier.modded * self.critical_headshot_bonus-1)+1

    def get_first_shot_damage(self, dmg, weapon_effect, crit_tier, multi_madness = 1):
        dmg = np.array(dmg)
        applied_shield_damage = 0
        applied_health_damage = 0
        if self.current_shield > 0:
            applied_shield_damage += np.sum(multi_dot([dmg , self.shield_modifiers , constant.SHIELD_MASK])) * self.get_all_enemy_multipliers(constant.VT_SHIELD)
            applied_health_damage += np.sum(multi_dot([dmg , self.health_modifiers , constant.SHIELDED_HEALTH_MASK , self.get_armor_reduction()])) * self.get_all_enemy_multipliers(constant.VT_HEALTH)
        else:
            applied_health_damage += np.sum(multi_dot([dmg , self.health_modifiers , self.get_armor_reduction()])) * self.get_all_enemy_multipliers(constant.VT_HEALTH)

        applied_shield_damage = self.get_special_damage_reduction(applied_shield_damage * multi_madness, weapon_effect, crit_tier) 
        applied_health_damage = self.get_special_damage_reduction(applied_health_damage * multi_madness, weapon_effect, crit_tier)

        overflow_health_damage = 0
        if self.current_shield < 0:
            ratio = abs(self.current_shield/applied_shield_damage)
            overflow_health_damage += np.sum(multi_dot([dmg , self.health_modifiers , self.get_armor_reduction()]))* self.get_all_enemy_multipliers(constant.VT_HEALTH) * ratio
            overflow_health_damage = self.get_special_damage_reduction(overflow_health_damage * multi_madness, weapon_effect, crit_tier)

        return ( (applied_shield_damage), (applied_health_damage), (overflow_health_damage) )

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
        - Unused types -
        15  Tau
        16  Cinematic
        17  Shield Drain
        18  Health Drain
        19  Energy Drain
        20  Suicide
        21  Physical
        22  Base Elemental
        23  Compound Elemental
        24  Any
        25  Invalid
        '''
        def __init__(self):
            self.ferrite =          [1.00, 1.50, 0.85, 1.00, 1.00, 1.00, 1.25, 0.75, 1.00, 1.00, 1.00, 1.00, 1.75, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.alloy =            [1.00, 1.15, 0.50, 1.00, 1.25, 0.50, 1.00, 1.00, 1.75, 1.00, 0.50, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.infested_sinew =   [1.00, 1.25, 1.00, 1.00, 1.25, 1.00, 1.00, 0.50, 1.50, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]

            self.proto_shield =     [1.15, 0.50, 1.00, 0.50, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.75, 1.00, 0.50, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.shield =           [1.50, 0.80, 1.00, 1.00, 1.50, 1.00, 1.00, 1.00, 0.75, 1.00, 1.75, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.eidolon_shield =   [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]

            self.infested =         [1.00, 1.00, 1.25, 1.25, 1.00, 1.00, 1.00, 1.00, 0.50, 1.75, 1.00, 0.50, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.robotic =          [1.00, 1.25, 0.75, 1.00, 1.00, 1.50, 0.75, 1.00, 1.25, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.cloned_flesh =     [0.75, 1.00, 1.25, 1.25, 1.00, 1.00, 1.00, 1.00, 1.00, 0.50, 1.00, 1.75, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.infested_flesh =   [1.00, 1.00, 1.50, 1.50, 0.50, 1.00, 1.00, 1.00, 1.00, 1.50, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.flesh =            [0.75, 1.00, 1.25, 1.00, 1.00, 1.00, 1.50, 1.00, 1.00, 0.75, 1.00, 1.50, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.fossilized =       [1.00, 1.00, 1.15, 1.00, 0.75, 1.00, 0.50, 1.50, 0.25, 1.00, 1.00, 1.00, 1.75, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
            self.machinery =        [1.25, 1.00, 1.00, 1.00, 1.00, 1.50, 0.75, 1.75, 1.00, 1.00, 1.00, 0.75, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]

            self.tenno_shield =     [0.75]*20
            self.tenno_health =     [1]*20
            self.tenno_armor =      [1]*20

            self.none =             [0]*20

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
    
    def get_armor_reduction(self):
        armr = self.current_armor * self.corrosive_armor_strip * self.heat_armor_strip
        if int(armr) > 0:
            arr = np.multiply(self.armor_modifiers, np.reciprocal(((np.array(self.armor_modifiers)*(-1)+2)*(armr/300)+1)))
            arr[14]=1
            return arr
        else:
            return np.array([1]*20)
        
    def get_modified_armor(self):
        return self.current_armor * self.corrosive_armor_strip * self.heat_armor_strip

    def get_all_enemy_multipliers(self, vulnerability_type=None):
        if vulnerability_type == constant.VT_SHIELD:
            return self.innate_damage_reduction * self.body_part_multiplier * self.magnetic_multiplier
        elif vulnerability_type == constant.VT_HEALTH:
            return self.innate_damage_reduction * self.body_part_multiplier * self.viral_multiplier
        else:
            return self.innate_damage_reduction * self.body_part_multiplier

    def get_special_damage_reduction(self, applied_dmg, weapon_effect, crit_tier=-1, proc=False):
        crit_damage = self.get_critical_damage_state(weapon_effect,crit_tier) if crit_tier!= -1 else self.get_critical_damage_state(weapon_effect)
        total_dmg = applied_dmg*crit_damage if not proc else applied_dmg

        if applied_dmg == 0:
            return 0

        # Weird shotgun mechanic
        dps = applied_dmg*weapon_effect.dps_multiplier/2 if weapon_effect.pellets.base > 1 else applied_dmg*weapon_effect.dps_multiplier

        if self.enemy_type == 'ET_NORMAL':
            return total_dmg
        elif self.enemy_type == 'ET_DEMOLISHER' or self.enemy_type == 'ET_DEMOLYST'or self.enemy_type == 'ET_DEIMOS_JUGULUS' or self.enemy_type == 'ET_DEIMOS_SAXUM' or self.enemy_type == 'ET_CONDRIX':
            if dps <= 1000:
                return total_dmg
            elif dps >= 1000 and dps <= 2500:
                return (0.8+200/dps)*total_dmg
            elif dps >= 2500 and dps <= 5000:
                return (0.7+450/dps)*total_dmg
            elif dps >= 5000 and dps <= 10000:
                return (0.4+1950/dps)*total_dmg
            elif dps >= 10000 and dps <= 20000:
                return (0.2+3950/dps)*total_dmg
            elif dps >= 20000:
                return (0.1+5950/dps)*total_dmg
        elif self.enemy_type == 'ET_EIDOLON':
            thresh = 300/(weapon_effect.fire_rate.modded * weapon_effect.pellets.modded)
            return ((total_dmg-thresh)*0.1+thresh)*0.4
        elif self.enemy_type == 'ET_LEPHANTIS':
            crit = self.get_critical_damage_state(weapon_effect, weapon_effect.weapon_state.current_critical_tier)
            tot_damage = applied_dmg * crit
            damage_cap = self.current_health * 0.1 + 450

            if tot_damage <=450:
                damage_mult = 1
            elif abs(self.time - self.previous_hit_time) < 0.27:
                damage_mult = 0.1
            else:
                damage_mult = 0.1+450/tot_damage

            reduced_damage = tot_damage * damage_mult

            if reduced_damage > damage_cap:
                return damage_cap/applied_dmg
            else:
                return reduced_damage/(applied_dmg*crit)

def multi_dot(array_list):
    res = array_list[0]
    for i in range(1, len(array_list)):
        res=np.multiply(res, array_list[i])
    return res
