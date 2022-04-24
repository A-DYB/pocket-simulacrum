import json
from random import random
import re
import constant
import numpy as np

class Weapon:
    def __init__(self, name, fire_mode_name, ui):
        self.ui = ui
        self.name = name
        self.fire_mode_name = fire_mode_name
        self.weapon_effects = []
        self.disposition = 1
        self.riven_type = 'Rifle'

        self.mod_config = ModConfig(ui)
        self.initialize_fire_mode(fire_mode_name)

    def initialize_fire_mode(self, fire_mode_name):
        self.weapon_effects.clear()
        with open('./weapon_data.json') as f:
            weapon_data = json.load(f)

        self.riven_type = weapon_data[self.name]["Fire Modes"][list(weapon_data[self.name]["Fire Modes"].keys())[0]].get("rivenType", "Rifle")
        self.disposition = weapon_data[self.name]["Fire Modes"][list(weapon_data[self.name]["Fire Modes"].keys())[0]].get("omegaAttenuation",1)

        we = WeaponEffect(self)
        self.weapon_effects.append(we)
        for se_name in weapon_data[self.name]["Fire Modes"][fire_mode_name]['Secondary Effects'].keys():
            we = WeaponEffect(self, se_name)
            self.weapon_effects.append(we)

    def apply_proc_immunity(self, proc_immunity):
        for eff in self.weapon_effects:
            eff.proc_immunity = np.array(proc_immunity)
            eff.apply_mods()

    def reset(self):
        for eff in self.weapon_effects:
            eff.reset()

    def reset_mods(self):
        self.mod_config = ModConfig(self.ui)
        for wepeff in self.weapon_effects:
            wepeff.apply_mods()

class WeaponEffect:
    def __init__(self, weapon, se_name=None):
        self.weapon = weapon
        self.fire_mode_name = weapon.fire_mode_name
        self.se_name = se_name

        self.proc_immunity = np.array([1]*20)

        self.initialize_properties()
        self.weapon_state = self.WeaponState(self)
        self.apply_mods()
        self.weapon_state.roll_multishot()
        self.weapon_state.roll_crit_and_status()
        self.delay = 0 if se_name is None else constant.SECONDARY_EFFECT_DELAY
        self.next_event = self.charge_time.modded + self.embed_delay.modded + self.delay

    def initialize_properties(self):
        if self.weapon.mod_config.stance_equipped:
            with open('./stance_data.json') as f:
                stance_data = json.load(f)
            stance_dict = stance_data[self.weapon.mod_config.stance_name]['ComboName'][self.weapon.mod_config.stance_moveset]
            self.stance_multiplier_list = stance_dict.get('Multipliers', [1])
            self.stance_proc_list = stance_dict.get('Procs', [0])
            self.stance_time = stance_dict.get('Time', [0])/len(self.stance_multiplier_list)

        with open('./weapon_data.json') as f:
            weapon_data = json.load(f)
        fm = weapon_data[self.weapon.name]["Fire Modes"][self.fire_mode_name]
        se = fm["Secondary Effects"]

        self.trigger = fm.get("trigger", "AUTO")

        self.base_damage = self.WeaponProperty( np.array(self.get_base_property(fm, se, "damagePerShot", default_val=np.zeros((20)))) )
        self.total_base_damage = self.WeaponProperty( np.sum(self.base_damage.base))
        self.critical_chance = self.WeaponProperty( self.get_base_property(fm, se, "criticalChance", default_val=0) )
        self.critical_multiplier = self.WeaponProperty( self.get_base_property(fm, se, "criticalMultiplier", default_val=1) )
        self.pellets = self.WeaponProperty( self.get_base_property(fm, se, "multishot", default_val=1) )
        self.fire_rate = self.WeaponProperty( self.get_base_property(fm, se, "fireRate", default_val=1) )
        self.status_chance = self.WeaponProperty( self.get_base_property(fm, se, "procChance", default_val=0) )
        self.reload_speed = self.WeaponProperty( self.get_base_property(fm, se, "reloadTime", default_val=0) )
        self.magazine_size = self.WeaponProperty( self.get_base_property(fm, se, "magazineSize", default_val=1) )
        self.ammo_capacity = self.WeaponProperty( self.get_base_property(fm, se, "ammo", default_val=1) )
        self.charge_time = self.WeaponProperty( self.get_base_property(fm, se, "chargeTime", default_val=1) )
        self.embed_delay = self.WeaponProperty( self.get_base_property(fm, se, "embedDelay", default_val=1) )
        self.ammo_cost = self.WeaponProperty( self.get_base_property(fm, se, "ammoCost", default_val=1) )
        self.headshot_bonus = self.WeaponProperty( 1 )

    def get_base_property(self, fm, se, key, default_val=0):
        if self.se_name is not None:
            return se[self.se_name].get(key, fm.get(key, default_val))
        else:
            return fm.get(key, default_val)

    def apply_mods(self):
        self.base_damage.modded =           self.base_damage.base * self.weapon.mod_config.base_damage * self.weapon.mod_config.faction_damage * self.weapon.mod_config.misc_multiplier * self.weapon_state.stance_multiplier
        self.base_damage.modded =           self.base_damage.modded.clip(min=0)
        self.total_base_damage.modded =     np.sum(self.base_damage.modded)
        self.quantum =                      self.total_base_damage.modded/16 if self.total_base_damage.modded>0 else 1/16
        self.base_damage.modded[0] =        self.base_damage.modded[0] * self.weapon.mod_config.impact_damage * self.weapon_state.stance_impact_damage
        self.base_damage.modded[1] =        self.base_damage.modded[1] * self.weapon.mod_config.puncture_damage * self.weapon_state.stance_puncture_damage
        self.base_damage.modded[2] =        self.base_damage.modded[2] * self.weapon.mod_config.slash_damage * self.weapon_state.stance_slash_damage
        self.base_damage.modded[3]+=        self.total_base_damage.modded * self.weapon.mod_config.heat_damage 
        self.base_damage.modded[4]+=        self.total_base_damage.modded * self.weapon.mod_config.cold_damage 
        self.base_damage.modded[5]+=        self.total_base_damage.modded * self.weapon.mod_config.electric_damage 
        self.base_damage.modded[6]+=        self.total_base_damage.modded * self.weapon.mod_config.toxin_damage 
        self.base_damage.modded =           self.base_damage.modded.clip(min=0)

        self.critical_chance.modded =       max(0, self.critical_chance.base * self.weapon.mod_config.critical_chance)
        self.critical_multiplier.modded =   max(0, self.critical_multiplier.base * self.weapon.mod_config.critical_multiplier * self.weapon.mod_config.critical_damage_multiplier)
        self.pellets.modded =               max(0, self.pellets.base * self.weapon.mod_config.multishot if self.se_name is None else self.pellets.base)
        self.fire_rate.modded =             max(1/20, self.fire_rate.base * self.weapon.mod_config.fire_rate)
        self.status_chance.modded =         max(0, self.status_chance.base * self.weapon.mod_config.status_chance)
        self.reload_speed.modded =          self.reload_speed.base / max( 0.05, (self.weapon.mod_config.reload_speed) )
        self.magazine_size.modded =         max( 1, self.magazine_size.base * self.weapon.mod_config.magazine_size )
        self.ammo_capacity.modded =         max( 0, self.ammo_capacity.base * self.weapon.mod_config.ammo_capacity )
        self.charge_time.modded =           self.charge_time.base/max( 0.05, self.weapon.mod_config.fire_rate)
        self.embed_delay.modded =           self.embed_delay.base/max( 0.05, self.weapon.mod_config.fire_rate)
        self.headshot_bonus.modded =        1
        self.ammo_cost.modded =             max( 0, self.ammo_cost.base )

        self.current_magazine = self.magazine_size.modded
        self.min_critical_tier = int(self.critical_chance.modded)
        self.dps_multiplier = self.pellets.modded * self.fire_rate.modded

        if self.weapon.mod_config.corrosive_ordering:
            self.base_damage.modded[12] = self.base_damage.modded[12] + self.base_damage.modded[5] + self.base_damage.modded[6]
            self.base_damage.modded[5] = 0 #electric
            self.base_damage.modded[6] = 0 #toxin
        if self.weapon.mod_config.blast_ordering:
            self.base_damage.modded[7] = self.base_damage.modded[7] + self.base_damage.modded[3] + self.base_damage.modded[4]
            self.base_damage.modded[3] = 0 #heat
            self.base_damage.modded[4] = 0 #cold
        if self.weapon.mod_config.viral_ordering:
            self.base_damage.modded[11] = self.base_damage.modded[11] + self.base_damage.modded[6] + self.base_damage.modded[4]
            self.base_damage.modded[4] = 0 #cold
            self.base_damage.modded[6] = 0 #toxin
        if self.weapon.mod_config.radiation_ordering:
            self.base_damage.modded[8] = self.base_damage.modded[8] + self.base_damage.modded[5] + self.base_damage.modded[3]
            self.base_damage.modded[5] = 0 #electric
            self.base_damage.modded[3] = 0 #heat
        if self.weapon.mod_config.magnetic_ordering:
            self.base_damage.modded[10] = self.base_damage.modded[10] + self.base_damage.modded[5] + self.base_damage.modded[4]
            self.base_damage.modded[5] = 0 #electric
            self.base_damage.modded[4] = 0 #cold
        if self.weapon.mod_config.gas_ordering:
            self.base_damage.modded[9] = self.base_damage.modded[9] + self.base_damage.modded[3] + self.base_damage.modded[6]
            self.base_damage.modded[3] = 0 #heat
            self.base_damage.modded[6] = 0 #toxin

        # apply uncombined elemental bonuses
        self.base_damage.modded[3]+=        self.total_base_damage.modded * self.weapon.mod_config.uncombinable_heat_damage 
        self.base_damage.modded[4]+=        self.total_base_damage.modded * self.weapon.mod_config.uncombinable_cold_damage 
        self.base_damage.modded[5]+=        self.total_base_damage.modded * self.weapon.mod_config.uncombinable_electric_damage 
        self.base_damage.modded[6]+=        self.total_base_damage.modded * self.weapon.mod_config.uncombinable_toxin_damage 
        self.base_damage.modded =           self.base_damage.modded.clip(min=0)

        self.modded_total_damage = np.sum(self.base_damage.modded)
        status_proportions = np.multiply(self.base_damage.modded, self.proc_immunity)
        self.status_effect_chance =  np.array([0]*20) if np.sum(status_proportions) == 0 else status_proportions/np.sum(status_proportions)

        # quantize
        self.base_damage.modded = np.round(self.base_damage.modded/self.quantum, 0)*self.quantum

    def execute(self, enemy):
        plts = self.weapon_state.multishot_state[0]
        if self.se_name is None:
            if self.trigger == 'HELD':
                enemy.apply_damage( self.base_damage.modded*plts, self)
                enemy.apply_beam_status(self)
                self.weapon_state.roll_crit_and_status()
            else:
                for i in range(plts):
                    enemy.apply_damage(self.base_damage.modded, self)
                    enemy.apply_status(self)
                    self.weapon_state.roll_crit_and_status()
            for seff in self.weapon.weapon_effects:
                if seff.se_name is not None:
                    seff.weapon_state.multishot_state.append(plts)
        else:
            if self.trigger == 'HELD':
                enemy.apply_damage( self.base_damage.modded*plts, self)
                enemy.apply_beam_status(self)
                self.weapon_state.roll_crit_and_status()
            else:
                # loop over primary effect multishot state and then secondary effect multishot state
                for i in range(plts):
                    for i in range(int(self.pellets.base)):
                        enemy.apply_damage(self.base_damage.modded, self)
                        enemy.apply_status(self)
                        self.weapon_state.roll_crit_and_status()
                self.weapon_state.multishot_state.pop(0)

        if self.weapon_state.stance_proc:
            self.apply_proc(2)
        self.end_fire_event()

    # refresh next event
    def end_fire_event(self):
        #   Secondary effects inherit the charge and embed delay of primary effect. This is how it schedules things. If the secondary effect somehow has a charge time and/or an embed delay
        #   it will have to be user defined to account for the primary fire charge/embed delay as well. The only requirement is the secondary effect should have at least the same charge/embed as main effect
        if self.current_magazine - self.ammo_cost.modded > 0:
            self.current_magazine -= self.ammo_cost.modded
            self.next_event += 1/self.fire_rate.modded + self.charge_time.modded + self.embed_delay.modded
        #   Reload
        else:
            self.current_magazine = self.magazine_size.modded
            self.next_event += max(self.reload_speed.modded, 1/self.fire_rate.modded) + self.charge_time.modded + self.embed_delay.modded

        self.weapon_state.roll_multishot()

        if self.weapon.mod_config.stance_equipped:
            self.weapon_state.stance_index = self.weapon_state.stance_index+1 if self.weapon_state.stance_index <= len(self.stance_multiplier_list)-2 else 0
            self.weapon_state.stance_multiplier = self.stance_multiplier_list[self.weapon_state.stance_index]
            self.weapon_state.stance_proc = self.stance_proc_list[self.weapon_state.stance_index]
            self.apply_mods()
    
    def reset(self):
        self.next_event = self.charge_time.modded + self.embed_delay.modded + self.delay
        self.weapon_state.reset()
        
    def get_next_event_time(self):
        return self.next_event

    class WeaponProperty():
        def __init__(self, base) -> None:
            self.base = base
            self.modded = base

    class WeaponState():
        def __init__(self, weapon_effect) -> None:
            self.weapon_effect = weapon_effect
            self.critical_proc = 0
            self.current_critical_tier = 0
            self.crit_enhance_proc = 0
            self.status_proc = 0
            self.multishot_state = [self.weapon_effect.pellets.base]

            self.stance_index = 0
            self.stance_multiplier = self.weapon_effect.stance_multiplier_list[self.stance_index] if self.weapon_effect.weapon.mod_config.stance_equipped else 1
            self.stance_proc = self.weapon_effect.stance_proc_list[self.stance_index] if self.weapon_effect.weapon.mod_config.stance_equipped else 0
            self.stance_impact_damage = 1
            self.stance_puncture_damage = 1
            self.stance_slash_damage = 1

        def roll_multishot(self):
            if self.weapon_effect.se_name is None:
                if random() < self.weapon_effect.pellets.modded%1:
                    self.multishot_state[0] = int(self.weapon_effect.pellets.modded+1)
                else:
                    self.multishot_state[0] = int(self.weapon_effect.pellets.modded)

        def roll_crit_and_status(self):
            self.critical_proc = random() < (self.weapon_effect.critical_chance.modded-int(self.weapon_effect.critical_chance.modded))
            self.crit_enhance_proc = 1 if random() < self.weapon_effect.weapon.mod_config.critical_enhancement else 0
            if self.critical_proc:
                self.current_critical_tier = self.weapon_effect.min_critical_tier+1+self.crit_enhance_proc
            else:
                self.current_critical_tier = self.weapon_effect.min_critical_tier if self.weapon_effect.min_critical_tier==0 else self.weapon_effect.min_critical_tier+self.crit_enhance_proc
            self.status_proc = random()<(self.weapon_effect.status_chance.modded%1)
        
        def reset(self):
            self.critical_proc = 0
            self.current_critical_tier = 0
            self.crit_enhance_proc = 0
            self.status_proc = 0
            self.multishot_state = [1]

            self.stance_index = 0
            self.stance_multiplier = self.weapon_effect.stance_multiplier_list[self.stance_index] if self.weapon_effect.weapon.mod_config.stance_equipped else 1
            self.stance_proc = self.weapon_effect.stance_proc_list[self.stance_index] if self.weapon_effect.weapon.mod_config.stance_equipped else 0
            self.stance_impact_damage = 1
            self.stance_puncture_damage = 1
            self.stance_slash_damage = 1

            self.roll_multishot()
            self.roll_crit_and_status()

class ModConfig():
    def __init__(self, ui) -> None:
        self.stance_name = ui.custom_build_stance_combo.currentText()
        self.stance_moveset = ui.custom_build_stance_moveset_combo.currentText()
        self.stance_equipped= False if self.stance_name=='' or self.stance_moveset=='' else True

        self.base_damage = parse_text(ui.base_damage_mod_textbox.toPlainText())
        self.critical_chance = parse_text(ui.critical_chance_mod_textbox.toPlainText())
        self.critical_multiplier = parse_text(ui.critical_damage_mod_textbox.toPlainText())
        self.critical_damage_multiplier = parse_text( ui.critical_damage_multiplier_mod_textbox.toPlainText(), mod_type=constant.T_MULTIPLIER )
        self.multishot = parse_text(ui.multishot_mod_textbox.toPlainText())
        self.fire_rate = parse_text(ui.fire_rate_mod_textbox.toPlainText())
        self.status_chance = parse_text(ui.status_chance_mod_textbox.toPlainText())
        self.reload_speed = parse_text(ui.reload_speed_mod_textbox.toPlainText())
        self.magazine_size = parse_text(ui.magazine_mod_textbox.toPlainText())
        self.ammo_capacity = parse_text(ui.ammo_maximum_mod_textbox.toPlainText())

        self.faction_damage = parse_text(ui.faction_mod_textbox.toPlainText())

        self.heat_damage = parse_text(ui.heat_mod_textbox.toPlainText(), base=0)
        self.uncombinable_heat_damage = parse_text(ui.heat_mod_textbox.toPlainText(), base=0, mod_type=constant.T_UNCOMBINED)
        self.cold_damage = parse_text(ui.cold_mod_textbox.toPlainText(), base=0)
        self.uncombinable_cold_damage = parse_text(ui.cold_mod_textbox.toPlainText(), base=0, mod_type=constant.T_UNCOMBINED)
        self.electric_damage = parse_text(ui.electric_mod_textbox.toPlainText(), base=0)
        self.uncombinable_electric_damage = parse_text(ui.electric_mod_textbox.toPlainText(), base=0, mod_type=constant.T_UNCOMBINED)
        self.toxin_damage = parse_text(ui.toxin_mod_textbox.toPlainText(), base=0)
        self.uncombinable_toxin_damage = parse_text(ui.toxin_mod_textbox.toPlainText(), base=0, mod_type=constant.T_UNCOMBINED)

        self.impact_damage = parse_text(ui.impact_mod_textbox.toPlainText())
        self.puncture_damage = parse_text(ui.puncture_mod_textbox.toPlainText())
        self.slash_damage = parse_text(ui.slash_mod_textbox.toPlainText())

        self.misc_multiplier = parse_text(ui.damage_multiplier_mod_textbox.toPlainText(), mod_type=constant.T_MULTIPLIER)
        self.headshot_multiplier = parse_text("")
        
        # vigilante set mods
        self.critical_enhancement = parse_text(ui.critical_enhance_textbox.toPlainText(), base=0)

        self.status_duration = parse_text(ui.status_duration_mod_textbox.toPlainText(), base=0)

        # elemental mod order
        self.corrosive_ordering = ui.corrosive_check_box.isChecked()
        self.blast_ordering = ui.blast_check_box.isChecked()
        self.viral_ordering = ui.viral_check_box.isChecked()
        self.radiation_ordering = ui.radiation_check_box.isChecked()
        self.magnetic_ordering = ui.magnetic_check_box.isChecked()
        self.gas_ordering = ui.gas_check_box.isChecked()

        self.shattering_impact = ui.shattering_impact_check_box.isChecked()
        self.amalgam_argonak_metal_auger = ui.amalgam_argonak_metal_auger_checkbox.isChecked()


'''Text Modifier:  "ue" prefix - uncombinable elemental, only applies to elemental groups Ex: ue100.0'''
def parse_text(txt, base=1, mod_type=constant.T_BASE):
    if mod_type == constant.T_BASE:
        return base+sum([float(i) for i in re.findall(constant.BASE_RULE, txt)])/100
    elif mod_type == constant.T_UNCOMBINED:
        return base+sum([float(i) for i in re.findall(constant.UNCOMBINED_RULE, txt)])/100
    elif mod_type == constant.T_MULTIPLIER:
        str_list = re.findall(constant.BASE_RULE, txt)
        if len(str_list)>0:
            return np.prod(np.array([float(i) for i in str_list]))
        else:
            return 1
    return None