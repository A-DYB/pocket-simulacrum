import json
from random import random
from collections import deque

class Weapon:
    def __init__(self, name, fire_mode_name, ui):

        self.name = name
        self.fire_mode_name = fire_mode_name
        self.main_effect = WeaponEffect(self)
        self.weapon_effects = []
        self.disposition = 1
        self.riven_type = 'Rifle'

        self.stance_name = ui.custom_build_stance_combo.currentText()
        self.stance_moveset = ui.custom_build_stance_moveset_combo.currentText()

        self.damage_mods = 1
        self.critical_chance_mods = 1
        self.critical_multiplier_mods = 1
        self.pellets_mods = 1
        self.fire_rate_mods = 1
        self.status_chance_mods = 1
        self.reload_mods = 1
        self.magazine_mods = 1
        self.ammo_mods = 1

        self.bane_mods = 1

        self.heat_mods = 1
        self.cold_mods = 1
        self.electric_mods = 1
        self.toxin_mods = 1

        self.heat_u_mods = 1
        self.cold_u_mods = 1
        self.electric_u_mods = 1
        self.toxin_u_mods = 1

        self.damage_type_mods = [0]*20

        self.impact_mods = 1
        self.puncture_mods = 1
        self.slash_mods = 1

        self.multiplier_mods = 1
        self.headshot_multiplier_mods = 1
        self.critical_enhance_mods = 0

        self.status_duration_mods = 1
        self.ammo_mods = 1
        self.magazine_mods = 1

        self.corrosive = False
        self.blast = False
        self.viral = False
        self.radiation = False
        self.magnetic = False
        self.gas = False

        ### RVIENS
        self.riven_buff_damage_mods = 0
        self.riven_buff_critical_chance_mods = 0
        self.riven_buff_critical_multiplier_mods = 0
        self.riven_buff_pellets_mods = 0
        self.riven_buff_fire_rate_mods = 0
        self.riven_buff_status_chance_mods = 0
        self.riven_buff_reload_mods = 0
        self.riven_buff_magazine_mods = 0
        self.riven_buff_ammo_mods = 0
        self.riven_buff_bane_mods = 0
        self.riven_buff_heat_mods = 0
        self.riven_buff_cold_mods = self.riven_buff_heat_mods
        self.riven_buff_electric_mods = self.riven_buff_heat_mods
        self.riven_buff_toxin_mods = self.riven_buff_heat_mods
        self.riven_buff_impact_mods = 0
        self.riven_buff_puncture_mods = self.riven_buff_impact_mods
        self.riven_buff_slash_mods = self.riven_buff_impact_mods
        self.riven_buff_status_duration_mods = 0

        self.riven_curse_damage_mods = 0
        self.riven_curse_critical_chance_mods = 0
        self.riven_curse_critical_multiplier_mods =0
        self.riven_curse_pellets_mods = 0
        self.riven_curse_fire_rate_mods = 0
        self.riven_curse_status_chance_mods = 0
        self.riven_curse_reload_mods = 0
        self.riven_curse_magazine_mods = 0
        self.riven_curse_ammo_mods =0
        self.riven_curse_bane_mods = 0
        self.riven_curse_heat_mods = 0
        self.riven_curse_cold_mods = self.riven_curse_heat_mods
        self.riven_curse_electric_mods = self.riven_curse_heat_mods
        self.riven_curse_toxin_mods = self.riven_curse_heat_mods
        self.riven_curse_impact_mods = 0
        self.riven_curse_puncture_mods = self.riven_curse_impact_mods
        self.riven_curse_slash_mods = self.riven_curse_impact_mods
        self.riven_curse_status_duration_mods = 0



        ###

        self.hit_scaling = ui.hit_scaling_checkbox.isChecked()

        self.initialize_fire_mode(fire_mode_name)
        self.get_custom_build_mods(ui)

        self.main_effect.apply_mods(self)
        self.main_effect.next_event = self.main_effect.modded_charge_time + self.main_effect.modded_embed_delay
        self.main_effect.refresh_state()
        for we in self.weapon_effects:
            if we:
                we.apply_mods(self)
                we.next_event = we.modded_charge_time + we.modded_embed_delay
                we.refresh_state()

        self.load_riven_stats_from_file()

    def initialize_fire_mode(self, fire_mode_name):
        self.weapon_effects.clear()
        with open('./weapon_data.json') as f:
            weapon_data = json.load(f)

        self.riven_type = weapon_data[self.name]["Fire Modes"][list(weapon_data[self.name]["Fire Modes"].keys())[0]].get("rivenType", "Rifle")

        we = WeaponEffect(self)
        we.load_effect_from_file(self.name, fire_mode_name)
        self.main_effect = we

        for se_name in weapon_data[self.name]["Fire Modes"][fire_mode_name]['Secondary Effects'].keys():
            we = WeaponEffect(self, True)
            we.load_effect_from_file(self.name, fire_mode_name, se_name)
            self.weapon_effects.append( we)

    def load_riven_stats_from_file(self):
        with open('./riven_stats.json') as f:
            riven_data = json.load(f)

        build = riven_data[self.riven_type]['Buff']
        curse = riven_data[self.riven_type]['Curse']

        self.riven_buff_damage_mods = (build.get("Damage", 0))
        self.riven_buff_critical_chance_mods = (build.get("Critical Chance", 0))
        self.riven_buff_critical_multiplier_mods = (build.get("Critical Damage", 0))
        self.riven_buff_pellets_mods = (build.get("Multishot", 0))
        self.riven_buff_fire_rate_mods = (build.get("Fire Rate", 0))
        self.riven_buff_status_chance_mods = (build.get("Status Chance", 0))
        self.riven_buff_reload_mods = (build.get("Reload Speed", 0))
        self.riven_buff_magazine_mods = (build.get("Magazine Capacity", 0))
        self.riven_buff_ammo_mods = (build.get("Ammo Maximum", 0))
        self.riven_buff_bane_mods = (build.get("Damage to Faction", 0))
        self.riven_buff_heat_mods = (build.get("Elemental Damage", 0))
        self.riven_buff_cold_mods = self.riven_buff_heat_mods
        self.riven_buff_electric_mods = self.riven_buff_heat_mods
        self.riven_buff_toxin_mods = self.riven_buff_heat_mods
        self.riven_buff_impact_mods = (build.get("Physical Damage", 0))
        self.riven_buff_puncture_mods = self.riven_buff_impact_mods
        self.riven_buff_slash_mods = self.riven_buff_impact_mods
        self.riven_buff_status_duration_mods = (build.get("Status Duration", 0))

        self.riven_curse_damage_mods = self.riven_buff_damage_mods if curse.get("Critical Chance", False) else 0
        self.riven_curse_critical_chance_mods = self.riven_buff_critical_chance_mods if (curse.get("Critical Chance", 0)) else 0
        self.riven_curse_critical_multiplier_mods = self.riven_buff_critical_multiplier_mods if (curse.get("Critical Damage", 0)) else 0
        self.riven_curse_pellets_mods = self.riven_buff_pellets_mods if (curse.get("Multishot", 0)) else 0
        self.riven_curse_fire_rate_mods = self.riven_buff_fire_rate_mods if (curse.get("Fire Rate", 0)) else 0
        self.riven_curse_status_chance_mods = self.riven_buff_status_chance_mods if (curse.get("Status Chance", 0)) else 0
        self.riven_curse_reload_mods = self.riven_buff_reload_mods if (curse.get("Reload Speed", 0)) else 0
        self.riven_curse_magazine_mods = self.riven_buff_magazine_mods if (curse.get("Magazine Capacity", 0)) else 0
        self.riven_curse_ammo_mods = self.riven_buff_ammo_mods if (curse.get("Ammo Maximum", 0)) else 0
        self.riven_curse_bane_mods = self.riven_buff_bane_mods if (curse.get("Damage to Faction", 0)) else 0
        self.riven_curse_heat_mods = self.riven_buff_heat_mods if (curse.get("Elemental Damage", 0)) else 0
        self.riven_curse_cold_mods = self.riven_curse_heat_mods
        self.riven_curse_electric_mods = self.riven_curse_heat_mods
        self.riven_curse_toxin_mods = self.riven_curse_heat_mods
        self.riven_curse_impact_mods = self.riven_buff_impact_mods if (curse.get("Physical Damage", 0)) else 0
        self.riven_curse_puncture_mods = self.riven_curse_impact_mods
        self.riven_curse_slash_mods = self.riven_curse_impact_mods
        self.riven_curse_status_duration_mods = self.riven_buff_status_duration_mods if (curse.get("Status Duration", 0)) else 0

        # keep same form as main: custom_build_mod_list
        self.riven_bonus_list = [
                                    self.riven_buff_damage_mods,
                                    self.riven_buff_pellets_mods,
                                    self.riven_buff_critical_chance_mods,
                                    self.riven_buff_critical_multiplier_mods,
                                    self.riven_buff_bane_mods,
                                    self.riven_buff_fire_rate_mods,

                                    self.riven_buff_status_chance_mods,
                                    self.riven_buff_status_duration_mods,

                                    self.riven_buff_heat_mods,
                                    self.riven_buff_cold_mods,
                                    self.riven_buff_electric_mods,
                                    self.riven_buff_toxin_mods,

                                    self.riven_buff_impact_mods,
                                    self.riven_buff_puncture_mods,
                                    self.riven_buff_slash_mods,

                                    self.riven_buff_reload_mods,
                                    self.riven_buff_magazine_mods,
                                    self.riven_buff_ammo_mods
                                ]
        self.riven_buff_name_list = [
                                         "Base Damage",
                                         "Multishot",
                                         "Critical Chance",
                                         "Critical Damage",
                                         "Faction Damage",
                                         "Fire Rate",

                                         "Status Chance",
                                         "Status Duration",

                                         "Heat Damage",
                                         "Cold Damage",
                                         "Electric Damage",
                                         "Toxin Damage",

                                         "Impact Damage",
                                         "Puncture Damage",
                                         "Slash Damage",

                                         "Reload Speed",
                                         "Magazine Capacity",
                                         "Ammo Capacity"
                                    ]
        self.riven_neg_list =   [
                                    self.riven_curse_damage_mods,
                                    self.riven_curse_pellets_mods,
                                    self.riven_curse_critical_chance_mods,
                                    self.riven_curse_critical_multiplier_mods,
                                    self.riven_curse_bane_mods,
                                    self.riven_curse_fire_rate_mods,

                                    self.riven_curse_status_chance_mods,
                                    self.riven_curse_status_duration_mods,

                                    self.riven_curse_heat_mods,
                                    self.riven_curse_cold_mods,
                                    self.riven_curse_electric_mods,
                                    self.riven_curse_toxin_mods,

                                    self.riven_curse_impact_mods,
                                    self.riven_curse_puncture_mods,
                                    self.riven_curse_slash_mods,

                                    self.riven_curse_reload_mods,
                                    self.riven_curse_magazine_mods,
                                    self.riven_curse_ammo_mods
                                ]

    def get_custom_build_mods(self, ui):

        self.damage_mods = text_config_to_double( ui.base_damage_mod_textbox.toPlainText() )
        self.pellets_mods = text_config_to_double( ui.multishot_mod_textbox.toPlainText() )
        self.critical_chance_mods = text_config_to_double( ui.critical_chance_mod_textbox.toPlainText() )
        self.critical_multiplier_mods = text_config_to_double( ui.critical_damage_mod_textbox.toPlainText() )
        self.critical_damage_multiplier_mods = text_config_to_double( ui.critical_damage_multiplier_mod_textbox.toPlainText(), multiplier = True )
        self.bane_mods = text_config_to_double( ui.faction_mod_textbox.toPlainText() )
        self.multiplier_mods = text_config_to_double( ui.damage_multiplier_mod_textbox.toPlainText(), multiplier=True )
        self.fire_rate_mods = text_config_to_double( ui.fire_rate_mod_textbox.toPlainText() )

        self.status_chance_mods = text_config_to_double( ui.status_chance_mod_textbox.toPlainText() )
        self.status_duration_mods = text_config_to_double( ui.status_duration_mod_textbox.toPlainText() )

        '''
        self.heat_mods = text_config_to_double( ui.heat_mod_textbox.toPlainText() )
        self.cold_mods = text_config_to_double( ui.cold_mod_textbox.toPlainText() )
        self.electric_mods = text_config_to_double( ui.electric_mod_textbox.toPlainText() )
        self.toxin_mods = text_config_to_double( ui.toxin_mod_textbox.toPlainText() )
        '''

        self.heat_mods, self.heat_u_mods = element_text_config_to_double( ui.heat_mod_textbox.toPlainText() )
        #print(self.heat_mods, self.heat_u_mods)
        self.cold_mods, self.cold_u_mods = element_text_config_to_double( ui.cold_mod_textbox.toPlainText() )
        #print(self.cold_mods, self.cold_u_mods)
        self.electric_mods, self.electric_u_mods = element_text_config_to_double( ui.electric_mod_textbox.toPlainText() )
        #print(self.electric_mods, self.electric_u_mods)
        self.toxin_mods, self.toxin_u_mods = element_text_config_to_double( ui.toxin_mod_textbox.toPlainText() )
        #+5print(self.toxin_mods, self.toxin_u_mods)

        self.impact_mods = text_config_to_double( ui.impact_mod_textbox.toPlainText() )
        self.puncture_mods = text_config_to_double( ui.puncture_mod_textbox.toPlainText() )
        self.slash_mods = text_config_to_double( ui.slash_mod_textbox.toPlainText() )

        self.reload_mods = text_config_to_double( ui.reload_speed_mod_textbox.toPlainText() )
        self.magazine_mods = text_config_to_double( ui.magazine_mod_textbox.toPlainText() )
        self.ammo_mods = text_config_to_double( ui.ammo_maximum_mod_textbox.toPlainText() )

        self.headshot_multiplier_mods = text_config_to_double( "1" )

        self.critical_enhance_mods = text_config_to_double( ui.critical_enhance_textbox.toPlainText())/100

        self.damage_type_mods = [self.impact_mods,self.puncture_mods,self.slash_mods,self.heat_mods,self.cold_mods,self.electric_mods,self.toxin_mods,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.damage_type_u_mods = [self.impact_mods,self.puncture_mods,self.slash_mods,self.heat_u_mods,self.cold_u_mods,self.electric_u_mods,self.toxin_u_mods,0,0,0,0,0,0,0,0,0,0,0,0,0]

        self.corrosive = ui.corrosive_check_box.isChecked()
        self.blast = ui.blast_check_box.isChecked()
        self.viral = ui.viral_check_box.isChecked()
        self.radiation = ui.radiation_check_box.isChecked()
        self.magnetic = ui.magnetic_check_box.isChecked()
        self.gas = ui.gas_check_box.isChecked()

        self.shattering_impact = ui.shattering_impact_check_box.isChecked()
        self.amalgam_argonak_metal_auger = ui.amalgam_argonak_metal_auger_checkbox.isChecked()

    def apply_proc_immunity(self, proc_immunity):
        self.main_effect.proc_immunity = proc_immunity
        self.main_effect.apply_mods(self)
        for eff in self.weapon_effects:
            eff.proc_immunity = proc_immunity
            eff.apply_mods(self)

    def convert_widget_item_to_string(self, itm):
        if itm:
            return itm.text()
        else:
            return ''
class WeaponEffect:
    def __init__(self, parent, is_secondary_effect = False):
        self.weapon = parent

        self.name = ''
        self.base_damage = [0]*20
        self.base_total_damage = 0
        self.base_critical_chance = 0
        self.base_critical_multiplier = 0
        self.base_pellets = 0
        self.base_fire_rate = 0
        self.base_status_chance = 0
        self.base_reload = 0
        self.base_magazine = 0
        self.base_ammo = 0
        self.base_charge_time = 0
        self.base_embed_delay = 0
        self.base_ammo_cost = 0
        self.base_headshot_bonus = 1

        self.modded_base_damage = [0]*20
        self.modded_total_base_damage = 0
        self.modded_damage = [0]*20
        self.modded_total_damage = 0
        self.modded_critical_chance = 0
        self.modded_critical_multiplier = 0
        self.modded_pellets = 0
        self.modded_fire_rate = 0
        self.modded_status_chance = 0
        self.modded_reload = 0
        self.modded_magazine = 0
        self.modded_ammo = 0
        self.modded_charge_time = 0
        self.modded_embed_delay = 0
        self.modded_ammo_cost = 0
        self.modded_headshot_bonus = 1

        self.status_effect_chance = [0]*20

        self.quantum = 0

        self.dps_multiplier = 1

        self.is_secondary_effect = is_secondary_effect

        self.current_magazine = 0
        self.next_event = 0

        self.critical_proc = False
        self.current_critical_tier = 0
        self.status_proc = False
        self.multishot_state = 1

        self.trigger = 'AUTO'
        self.multishot_history = deque([])

        self.stance_multipliers = [1]
        self.stance_procs = [0]
        self.stance_time = 1
        self.current_stance_multiplier = 1
        self.current_stance_proc = 0
        self.stance_index = 0

        self.min_critical_tier = 0

        self.proc_immunity = [1]*20

    def load_effect_from_file(self, weapon_name, fire_mode_name, secondary_effect_name = None):
        if self.weapon.stance_name != '' and self.weapon.stance_moveset != '':
            with open('./stance_data.json') as f:
                stance_data = json.load(f)
            stance_dict = stance_data[self.weapon.stance_name]['ComboName'][self.weapon.stance_moveset]
            self.stance_multipliers = stance_dict.get('Multipliers', [1])
            self.stance_procs = stance_dict.get('Procs', [0])
            self.stance_time = stance_dict.get('Time', [0])/len(self.stance_multipliers)

        with open('./weapon_data.json') as f:
            weapon_data = json.load(f)

        fm = weapon_data[weapon_name]["Fire Modes"][fire_mode_name]
        se = fm["Secondary Effects"]

        self.name = weapon_name
        self.base_damage = fm.get("damagePerShot", self.base_damage)
        self.base_total_damage = sum(self.base_damage)
        self.base_critical_chance = fm.get("criticalChance", 0)
        self.base_critical_multiplier = fm.get("criticalMultiplier", 1)
        self.base_pellets = fm.get("multishot", 1)
        self.base_fire_rate = fm.get("fireRate", 1)
        self.base_status_chance = fm.get("procChance", 0)
        self.base_reload = fm.get("reloadTime", 0)
        self.base_magazine = fm.get("magazineSize", 10000)
        self.base_ammo = fm.get("ammo", 540)
        self.base_charge_time = fm.get("chargeTime", 0)
        self.base_embed_delay = fm.get("embedDelay", 0)
        self.base_ammo_cost = fm.get("ammoCost", 1)
        self.base_headshot_bonus = 1
        self.trigger = fm.get("trigger", "AUTO")

        if secondary_effect_name is not None:
            fm = se[secondary_effect_name]
            self.base_damage = fm.get("damagePerShot", self.base_damage)
            self.base_total_damage = sum(self.base_damage)
            self.base_critical_chance = fm.get("criticalChance", self.base_critical_chance)
            self.base_critical_multiplier = fm.get("criticalMultiplier", self.base_critical_multiplier)
            self.base_pellets = fm.get("multishot", self.base_pellets)
            self.base_fire_rate = fm.get("fireRate", self.base_fire_rate)
            self.base_status_chance = fm.get("procChance", self.base_status_chance)
            self.base_reload = fm.get("reloadTime", self.base_reload)
            self.base_magazine = fm.get("magazineSize", self.base_magazine)
            self.base_ammo = fm.get("ammo", self.base_ammo)
            self.base_charge_time = fm.get("chargeTime", self.base_charge_time)
            self.base_embed_delay = fm.get("embedDelay", self.base_embed_delay)+0.0001
            self.base_ammo_cost = fm.get("ammoCost", self.base_ammo_cost)
            self.base_headshot_bonus = 1
            self.trigger = fm.get("trigger", "AUTO")

    def apply_mods(self, parent):
        self.modded_base_damage = [max( 0, i * (1+parent.damage_mods) * (1+parent.bane_mods) * (parent.multiplier_mods) * self.current_stance_multiplier) for i in self.base_damage]
        # print(self.modded_base_damage)
        self.modded_total_base_damage = sum(self.modded_base_damage)
        self.quantum = (self.modded_total_base_damage)/16
        self.modded_critical_chance = max( 0, self.base_critical_chance * (1+parent.critical_chance_mods) )
        self.modded_critical_multiplier = max( 0, self.base_critical_multiplier * (1+parent.critical_multiplier_mods) * parent.critical_damage_multiplier_mods )
        if self.is_secondary_effect:
            self.modded_pellets = max( 0, self.base_pellets )
        else:
            self.modded_pellets = max( 0, self.base_pellets * (1+parent.pellets_mods) )
        self.modded_fire_rate = max( 0.1, (1/self.stance_time) * self.base_fire_rate * (1+parent.fire_rate_mods) )
        self.modded_status_chance = max( 0, self.base_status_chance * (1+parent.status_chance_mods) )
        self.modded_reload = self.base_reload / max( 0.1, (1+parent.reload_mods) )
        self.modded_magazine = max( 0, self.base_magazine * (1+parent.magazine_mods) )
        self.current_magazine = self.modded_magazine
        self.modded_ammo = max( 0, self.base_ammo * (1+parent.ammo_mods) )
        self.modded_charge_time = self.base_charge_time/max( 0.1, (1+parent.fire_rate_mods))
        self.modded_embed_delay = self.base_embed_delay/max( 0.1, (1+parent.fire_rate_mods))
        self.modded_headshot_bonus = 1
        self.modded_ammo_cost = max( 0, self.base_ammo_cost )
        self.min_critical_tier = int(self.modded_critical_chance)


        self.modded_damage[0] = max( 0, self.modded_base_damage[0] * ( 1 + parent.damage_type_mods[0] ) )
        self.modded_damage[1] = max( 0, self.modded_base_damage[1] * ( 1 + parent.damage_type_mods[1] ) )
        self.modded_damage[2] = max( 0, self.modded_base_damage[2] * ( 1 + parent.damage_type_mods[2] ) )

        for i in range(3, len(self.modded_damage)):
            self.modded_damage[i] = max( 0, self.modded_total_base_damage * parent.damage_type_mods[i] + self.modded_base_damage[i] )

        self.modded_total_damage = sum(self.modded_damage)


        self.dps_multiplier = self.modded_pellets * self.modded_fire_rate
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
        '''
        if parent.corrosive:
            self.modded_damage[12] = self.modded_damage[12] + self.modded_damage[5] + self.modded_damage[6]
            self.modded_damage[5] = 0 #electric
            self.modded_damage[6] = 0 #toxin
        if parent.blast:
            self.modded_damage[7] = self.modded_damage[7] + self.modded_damage[3] + self.modded_damage[4]
            self.modded_damage[3] = 0 #heat
            self.modded_damage[4] = 0 #cold
        if parent.viral:
            self.modded_damage[11] = self.modded_damage[11] + self.modded_damage[6] + self.modded_damage[4]
            self.modded_damage[4] = 0 #cold
            self.modded_damage[6] = 0 #toxin
        if parent.radiation:
            self.modded_damage[8] = self.modded_damage[8] + self.modded_damage[5] + self.modded_damage[3]
            self.modded_damage[5] = 0 #electric
            self.modded_damage[3] = 0 #heat
        if parent.magnetic:
            self.modded_damage[10] = self.modded_damage[10] + self.modded_damage[5] + self.modded_damage[4]
            self.modded_damage[5] = 0 #electric
            self.modded_damage[4] = 0 #cold
        if parent.gas:
            self.modded_damage[9] = self.modded_damage[9] + self.modded_damage[3] + self.modded_damage[6]
            self.modded_damage[3] = 0 #heat
            self.modded_damage[6] = 0 #toxin

        # apply uncombined elemental bonuses
        for i in range(3, len(self.modded_damage)):
            self.modded_damage[i] += self.modded_total_base_damage * parent.damage_type_u_mods[i]

        status_proportions = [ f*i for f,i in list(zip(self.modded_damage, self.proc_immunity))]

        if sum(status_proportions) == 0:
            self.status_effect_chance =  [0]*20
        else:
            # normalize
            self.status_effect_chance =  [f/sum(status_proportions) for f in status_proportions]

        # quantize
        self.modded_damage = [round(f/self.quantum,0)*self.quantum for f in self.modded_damage]

    def refresh_next_event(self):
        #   Secondary effects inherit the charge and embed delay of primary effect. This is how it schedules things. If the secondary effect somehow has a charge time and/or an embed delay
        #   it will have to be user defined to account for the primary fire charge/embed delay as well
        if self.current_magazine - self.modded_ammo_cost > 0:
            self.current_magazine -= self.modded_ammo_cost
            self.next_event += 1/self.modded_fire_rate + self.modded_charge_time + self.modded_embed_delay
        #   Reload
        else:
            self.current_magazine = self.modded_magazine
            self.next_event += max(self.modded_reload, 1/self.modded_fire_rate) + self.modded_charge_time + self.modded_embed_delay

        self.refresh_state()

        if self.is_secondary_effect:
            self.multishot_history.popleft()


    def refresh_state(self):
        if self.weapon.stance_name != '' and self.weapon.stance_moveset != '':
            self.current_stance_multiplier = self.stance_multipliers[self.stance_index]
            self.current_stance_proc - self.stance_procs[self.stance_index]
            self.stance_index += 1
            if self.stance_index > len(self.stance_multipliers)-1:
                self.stance_index = 0

            self.apply_mods(self.weapon)

        self.critical_proc = random() < (self.modded_critical_chance-int(self.modded_critical_chance))
        crit_enhance_proc = 1 if random() < self.weapon.critical_enhance_mods else 0
        if self.critical_proc:
            self.current_critical_tier = self.min_critical_tier+1+crit_enhance_proc
        else:
            self.current_critical_tier = self.min_critical_tier if self.min_critical_tier==0 else self.min_critical_tier+crit_enhance_proc
        self.status_proc = random()<(self.modded_status_chance%1)


class ModConfig():
    def __init__(self) -> None:
        self.damage_mods = 1
        self.critical_chance_mods = 1
        self.critical_multiplier_mods = 1
        self.pellets_mods = 1
        self.fire_rate_mods = 1
        self.status_chance_mods = 1
        self.reload_mods = 1
        self.magazine_mods = 1
        self.ammo_mods = 1

        self.bane_mods = 1

        self.heat_mods = 1
        self.cold_mods = 1
        self.electric_mods = 1
        self.toxin_mods = 1

        self.heat_u_mods = 1
        self.cold_u_mods = 1
        self.electric_u_mods = 1
        self.toxin_u_mods = 1

        self.damage_type_mods = [0]*20

        self.impact_mods = 1
        self.puncture_mods = 1
        self.slash_mods = 1

        self.multiplier_mods = 1
        self.headshot_multiplier_mods = 1
        self.critical_enhance_mods = 0

        self.status_duration_mods = 1
        self.ammo_mods = 1
        self.magazine_mods = 1

        self.corrosive = False
        self.blast = False
        self.viral = False
        self.radiation = False
        self.magnetic = False
        self.gas = False

def text_config_to_double(txt, multiplier = False):
    space_separated = txt.split(" ")
    tot = 0
    if not multiplier:
        for mod in space_separated:
            mod = mod.replace("$","")
            mod = mod.split("*")

            res = mod[0]
            if isfloat(res):
                res = float(res)
                for i in range(1,len(mod)):
                    if isfloat(mod[i]):
                        res *= float(mod[i])
                tot += float(res)
        return tot / 100
    else:
        tot = 1
        for mod in space_separated:
            if "$" in mod:
                mod = mod.replace("$","")
            if isfloat(mod):
                tot *= float(mod)
        if tot == 0:
            return 1
        else:
            return tot

def element_text_config_to_double(txt):
    space_separated = txt.split(" ")
    tot = 0
    u_tot = 0

    for mod in space_separated:
        if mod != "":
            mod = mod.replace("$","")
            mod = mod.split("*")

            res = mod[0]
            # uncombined type : ie. volt shield
            if res[0] == 'u':
                res = res.replace("u","")
                if isfloat(res):
                    res = float(res)
                    for i in range(1,len(mod)):
                        if isfloat(mod[i]):
                            res *= float(mod[i])
                    u_tot += float(res)
            else:
                if isfloat(res):
                    res = float(res)
                    for i in range(1,len(mod)):
                        if isfloat(mod[i]):
                            res *= float(mod[i])
                    tot += float(res)


    return tot / 100 , u_tot / 100


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False
