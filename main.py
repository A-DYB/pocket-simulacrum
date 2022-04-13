# This Python file uses the following encoding: utf-8
import json
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import os
from pathlib import Path
import random
import sys
import time
import numpy as np
from scipy.optimize import curve_fit

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6 import QtCore, QtWidgets, QtGui

from enemy import Enemy
from weapon import Weapon
from ui_mainwindow import Ui_Window

import statistics
import seaborn as sns
#   pyside6-uic form.ui > ui_mainwindow.py

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.ui=None
        self.load_ui()

        #self.ui = Ui_Window()
        #self.ui.setupUi(self)

        self.fig, (self.ax, self.ax2) = plt.subplots(1,2)
        colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
        # Sort colors by hue, saturation, value and name.
        by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name) for name, color in colors.items())
        self.plot_colors = [name for hsv, name in by_hsv]

        self.elemental_display_labels = [       self.ui.label_e1, self.ui.label_e2, self.ui.label_e3, self.ui.label_e4, self.ui.label_e5, self.ui.label_e6, self.ui.label_e7, 
                                                self.ui.label_e8, self.ui.label_e9, self.ui.label_e10, self.ui.label_e11, self.ui.label_e12, self.ui.label_e13 ]
        self.elemental_display_textboxes = [    self.ui.e_display_textbox_1, self.ui.e_display_textbox_2, self.ui.e_display_textbox_3, self.ui.e_display_textbox_4, 
                                                self.ui.e_display_textbox_5, self.ui.e_display_textbox_6, self.ui.e_display_textbox_7, self.ui.e_display_textbox_8, 
                                                self.ui.e_display_textbox_9, self.ui.e_display_textbox_10, self.ui.e_display_textbox_11, self.ui.e_display_textbox_12, 
                                                self.ui.e_display_textbox_13 ]
        self.elemental_display_textboxes_1 = [  self.ui.e_display_textbox_1_1, self.ui.e_display_textbox_2_1, self.ui.e_display_textbox_3_1, self.ui.e_display_textbox_4_1, 
                                                self.ui.e_display_textbox_5_1, self.ui.e_display_textbox_6_1, self.ui.e_display_textbox_7_1, self.ui.e_display_textbox_8_1, 
                                                self.ui.e_display_textbox_9_1, self.ui.e_display_textbox_10_1, self.ui.e_display_textbox_11_1, self.ui.e_display_textbox_12_1, 
                                                self.ui.e_display_textbox_13_1 ]
        self.elemental_edit_textboxes = [       self.ui.impact_edit_textbox, self.ui.puncture_edit_textbox, self.ui.slash_edit_textbox, self.ui.heat_edit_textbox,
                                                self.ui.cold_edit_textbox, self.ui.electric_edit_textbox, self.ui.toxin_edit_textbox, self.ui.blast_edit_textbox,
                                                self.ui.radiation_edit_textbox, self.ui.gas_edit_textbox, self.ui.magnetic_edit_textbox, self.ui.viral_edit_textbox,
                                                self.ui.corrosive_edit_textbox, self.ui.void_edit_textbox, self.ui.true_edit_textbox ]

        self.ui.edit_secondary_effect_combo.hide()
        self.ui.edit_secondary_effect_text.hide()
        self.ui.edit_secondary_effect_radio.hide()

        self.ui.custom_build_stance_combo.setEnabled(False)
        self.ui.custom_build_stance_combo.hide()
        self.ui.stance_build_label.hide()
        self.ui.custom_build_stance_moveset_combo.setEnabled(False)
        self.ui.custom_build_stance_moveset_combo.hide()
        self.ui.moveset_build_label.hide()
        self.ui.edit_weapon_category_combo.hide()
        self.ui.edit_weapon_category_combo.setEnabled(False)

        self.ui.edit_weapon_stance_label.hide()
        self.ui.edit_weapon_stance_label.setEnabled(False)

        self.ui.custom_build_weapon_combo.currentIndexChanged.connect(self.custom_build_weapon_combo_listener)
        self.ui.custom_build_fire_mode_combo.currentIndexChanged.connect(self.custom_build_fire_mode_combo_listener)
        self.ui.custom_build_weapon_combo.currentIndexChanged.connect(self.update_display_build_table)
        self.ui.custom_build_fire_mode_combo.currentIndexChanged.connect(self.update_display_build_table)
        self.ui.custom_build_stance_moveset_combo.currentIndexChanged.connect(self.update_display_build_table)

        # self.ui.custom_build_mod_table.itemChanged.connect(self.update_display_build_table)
        self.custom_build_mod_list = [
                                        self.ui.base_damage_mod_textbox,
                                        self.ui.multishot_mod_textbox,
                                        self.ui.critical_chance_mod_textbox,
                                        self.ui.critical_damage_mod_textbox,
                                        self.ui.faction_mod_textbox,
                                        self.ui.fire_rate_mod_textbox,

                                        self.ui.status_chance_mod_textbox,
                                        self.ui.status_duration_mod_textbox,

                                        self.ui.heat_mod_textbox,
                                        self.ui.cold_mod_textbox,
                                        self.ui.electric_mod_textbox,
                                        self.ui.toxin_mod_textbox,

                                        self.ui.impact_mod_textbox,
                                        self.ui.puncture_mod_textbox,
                                        self.ui.slash_mod_textbox,

                                        self.ui.reload_speed_mod_textbox,
                                        self.ui.magazine_mod_textbox,
                                        self.ui.ammo_maximum_mod_textbox,

                                        self.ui.critical_damage_multiplier_mod_textbox,
                                        self.ui.damage_multiplier_mod_textbox
                                     ]
        for txtbox in self.custom_build_mod_list:
            txtbox.textChanged.connect(self.update_display_build_table)

        self.ui.corrosive_check_box.stateChanged.connect(self.update_display_build_table)
        self.ui.blast_check_box.stateChanged.connect(self.update_display_build_table)
        self.ui.viral_check_box.stateChanged.connect(self.update_display_build_table)
        self.ui.radiation_check_box.stateChanged.connect(self.update_display_build_table)
        self.ui.magnetic_check_box.stateChanged.connect(self.update_display_build_table)
        self.ui.gas_check_box.stateChanged.connect(self.update_display_build_table)
        self.ui.display_weapon_critical_tier_spinner.valueChanged.connect(self.update_display_build_table)
        self.ui.enemy_select_combo.currentIndexChanged.connect(self.update_display_build_table)
        self.ui.enemy_level_spinner.valueChanged.connect(self.update_display_build_table)
        self.ui.SP_health_buff_spinner.valueChanged.connect(self.update_display_build_table)
        self.ui.SP_shield_buff_spinner.valueChanged.connect(self.update_display_build_table)
        self.ui.SP_armor_buff_spinner.valueChanged.connect(self.update_display_build_table)
        self.ui.old_scaling_checkbox.stateChanged.connect(self.update_display_build_table)

        self.ui.edit_weapon_combo.addItems(get_weapon_list())
        self.ui.custom_build_weapon_combo.addItems(get_weapon_list())
        self.ui.enemy_select_combo.addItems(get_enemy_list())
        self.ui.edit_enemy_combo.addItems(get_enemy_list())
        self.ui.build_select_combo.addItems(get_build_list())

        self.ui.edit_weapon_combo.currentIndexChanged.connect(self.edit_weapon_combo_listener)
        self.ui.edit_fire_mode_radio.toggled.connect(self.edit_fire_mode_radio_listener)
        self.ui.edit_fire_mode_combo.currentIndexChanged.connect(self.edit_fire_mode_combo_listener)
        self.ui.edit_secondary_effect_combo.currentIndexChanged.connect(self.secondary_effects_combo_listener)
        self.ui.custom_build_stance_combo.currentIndexChanged.connect(self.custom_build_stance_combo_listener)
        self.ui.edit_enemy_combo.currentIndexChanged.connect(self.edit_enemy_combo_listener)
        self.ui.edit_weapon_type_combo.currentIndexChanged.connect(self.edit_weapon_type_combo_listener)


        self.ui.edit_enemy_save_button.clicked.connect(self.save_enemy)
        self.ui.edit_weapon_remove_weapon_button.clicked.connect(self.delete_enemy)

        self.ui.edit_weapon_save_component_button.clicked.connect(self.save_weapon)
        self.ui.edit_weapon_remove_component_push_button.clicked.connect(self.delete_component)
        self.ui.edit_weapon_remove_weapon_push_button.clicked.connect(self.delete_weapon)

        self.ui.custom_build_save_button.clicked.connect(self.save_build)
        self.ui.build_select_combo.currentIndexChanged.connect(self.load_build)

        self.ui.save_data_button.clicked.connect(self.save_data)

        self.ui.simulate_button.clicked.connect(self.simulate)
        self.ui.simulate_once_button.clicked.connect(self.simulate_once)
        self.ui.scale_push_button.clicked.connect(self.scale)

        self.ui.find_best_riven_button.clicked.connect(self.simulate_best_riven)

        self.ui.steel_path_conditions_checkbox.clicked.connect(self.apply_steel_path_conditions)

        self.merge_weapon_data()

        '''
        QtCore.QSignalBlocker(self.ui.custom_build_weapon_combo),
        QtCore.QSignalBlocker(self.ui.custom_build_fire_mode_combo),
        QtCore.QSignalBlocker(self.ui.custom_build_stance_combo),
        QtCore.QSignalBlocker(self.ui.custom_build_stance_moveset_combo),
        '''

        self.mod_blockers = [ QtCore.QSignalBlocker( f ) for f in self.custom_build_mod_list ]
        self.blockers = self.mod_blockers + [
                        QtCore.QSignalBlocker(self.ui.corrosive_check_box),
                        QtCore.QSignalBlocker(self.ui.blast_check_box),
                        QtCore.QSignalBlocker(self.ui.viral_check_box),
                        QtCore.QSignalBlocker(self.ui.magnetic_check_box),
                        QtCore.QSignalBlocker(self.ui.radiation_check_box),
                        QtCore.QSignalBlocker(self.ui.gas_check_box)]

        for bl in self.blockers:
            bl.unblock()

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

    def get_dark_palette(self):
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("white"))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("black"))
        palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("white"))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor("white"))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("white"))
        palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor("red"))
        palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("black"))
        return palette

    @QtCore.Slot()
    def simulate(self, enemy_level = None, min_iterations = 100, max_iterations = 200, plot = True):
        times_list = []
        plot_list = []
        plot_list_shield = []
        damage_instance_list = []

        dps = []
        slash_dps =[]
        toxin_dps =[]
        heat_dps = []
        electric_dps =[]
        gas_dps = []

        enemy_name = self.ui.enemy_select_combo.currentText()
        if enemy_level is None:
            enemy_level = self.ui.enemy_level_spinner.value()
        start_time = time.time()
        for i in range(min_iterations):
            enemy = Enemy(enemy_name, enemy_level, self.ui)
            weapon = self.custom_build_init_weapon()
            kill_time, xvals, yvals,shield_time,  shield_prog, armor_time, armor_vals = enemy.kill(weapon)
            plot_list.append( (xvals,yvals) )
            plot_list_shield.append( (shield_time,  shield_prog) )
            times_list.append(kill_time)
            damage_instance_list+= enemy.damage_instance_list

            dps.append( (enemy.max_health+enemy.max_shield)/kill_time )
            slash_dps.append(enemy.slash_proc_manager.total_applied_damage/kill_time)
            toxin_dps.append(enemy.toxin_proc_manager.total_applied_damage/kill_time)
            heat_dps.append(enemy.heat_proc_manager.total_applied_damage/kill_time)
            electric_dps.append(enemy.electric_proc_manager.total_applied_damage/kill_time)
            gas_dps.append(enemy.gas_proc_manager.total_applied_damage/kill_time)

        s_stdev = statistics.stdev(times_list)
        s_mean = sum(times_list)/len(times_list)
        n = (1.96 * s_stdev / max(0.1, 0.05 * s_mean) ) ** 2

        for i in range( min( max(0, int(n)-min_iterations), max(max_iterations-min_iterations,0) ) ):
            enemy = Enemy(enemy_name, enemy_level, self.ui)
            weapon = self.custom_build_init_weapon()
            kill_time, xvals, yvals, shield_time, shield_prog, armor_time, armor_vals = enemy.kill(weapon)
            plot_list.append( (xvals,yvals) )
            plot_list_shield.append( (shield_time,  shield_prog) )
            times_list.append(kill_time)
            damage_instance_list+= enemy.damage_instance_list

            dps.append( (enemy.max_health+enemy.max_shield)/kill_time )
            slash_dps.append(enemy.slash_proc_manager.total_applied_damage/kill_time)
            toxin_dps.append(enemy.toxin_proc_manager.total_applied_damage/kill_time)
            heat_dps.append(enemy.heat_proc_manager.total_applied_damage/kill_time)
            electric_dps.append(enemy.electric_proc_manager.total_applied_damage/kill_time)
            gas_dps.append(enemy.gas_proc_manager.total_applied_damage/kill_time)

            if time.time() - start_time > 5:
                print("Simulation took longer than 5 seconds, ending simulation at %u/%u + %d iterations"%(i+1,max(0, int(n)-min_iterations),min_iterations))
                break

        print("Iterations: %u"%int(i+min_iterations))
        print("AVG TTK: ",sum(times_list)/len(times_list))
        print("Simulation took %f seconds"%(time.time() - start_time))
        avg_ttk = np.average(np.array(times_list))

        self.ui.ttk_mean_textbox.setPlainText("%.2f s"%( avg_ttk ) )
        # self.ui.dps_mean_textbox.setPlainText("%.2f"%( sum(dps)/len(dps) ) )
        self.ui.dps_mean_textbox.setPlainText(f"{sum(dps)/len(dps):,.2f}" )

        self.ui.ttk_std_textbox.setPlainText("%.2f s"%( np.std(times_list) ) )
        self.ui.dps_std_textbox.setPlainText(f"{np.std(dps):,.2f}" )

        # self.ui.slash_dps_mean_textbox.setPlainText("%.2f"%( sum(slash_dps)/len(slash_dps) ) )
        self.ui.slash_dps_mean_textbox.setPlainText(f"{sum(slash_dps)/len(slash_dps):,.2f}" )
        self.ui.toxin_dps_mean_textbox.setPlainText(f"{sum(toxin_dps)/len(toxin_dps):,.2f}" )
        self.ui.electric_dps_mean_textbox.setPlainText(f"{sum(electric_dps)/len(electric_dps):,.2f}" )
        self.ui.heat_dps_mean_textbox.setPlainText(f"{sum(heat_dps)/len(heat_dps):,.2f}" )
        self.ui.gas_dps_mean_textbox.setPlainText(f"{sum(gas_dps)/len(gas_dps):,.2f}" )

        self.ui.slash_dps_percent_textbox.setPlainText(f"{100*sum(slash_dps)/len(slash_dps) / (sum(dps)/len(dps)):,.2f}%" )
        self.ui.toxin_dps_percent_textbox.setPlainText(f"{100*sum(toxin_dps)/len(toxin_dps) / (sum(dps)/len(dps)):,.2f}%" )
        self.ui.electric_dps_percent_textbox.setPlainText(f"{100*sum(electric_dps)/len(electric_dps) / (sum(dps)/len(dps)):,.2f}%" )
        self.ui.heat_dps_percent_textbox.setPlainText(f"{100*sum(heat_dps)/len(heat_dps) / (sum(dps)/len(dps)):,.2f}%" )
        self.ui.gas_dps_percent_textbox.setPlainText(f"{100*sum(gas_dps)/len(gas_dps) / (sum(dps)/len(dps)):,.2f}%" )

        if plot:
            hp_time_s, hp = [], []
            for x,y in plot_list:
                hp_time_s += x
                hp += y

            sp_time_s, sp = [], []
            for x,y in plot_list_shield:
                sp_time_s += x
                sp += y

            if not plt.get_fignums():
                self.fig, (self.ax, self.ax2) = plt.subplots(1,2)

            sns.lineplot(ci='sd',x=hp_time_s, y=hp, ax=self.ax) 
            sns.lineplot(ci='sd',x=sp_time_s, y=sp, ax=self.ax)

            self.ax2.clear()
            data_dict = {"Applied Damage":damage_instance_list}
            sns.countplot(data=data_dict, x="Applied Damage", ax = self.ax2)
            #self.ax2.xticks(rotation=45)
            self.ax2.tick_params(axis='x', labelrotation = 45)
            total = len(damage_instance_list)
            for p in self.ax2.patches:
                percentage = f'{100 * p.get_height() / total:.1f}%\n'
                x = p.get_x() + p.get_width() / 2
                y = p.get_height()
                self.ax2.annotate(percentage, (x, y), ha='center', va='center')

            if avg_ttk > 20:
                if sum(heat_dps) >0:
                    mean_x, mean_y = get_mean( hp_time_s, hp, points =100 )
                    pars, cov = curve_fit(f=poly_fit, xdata=mean_x, ydata=mean_y, p0=[0, 0,enemy.max_health+enemy.max_shield], bounds=(-np.inf, np.inf))
                    x_o = np.roots(pars)
                    x_dummy = np.linspace(start=0, stop=x_o[-1], num=50)

                    self.ax.plot( x_dummy, poly_fit(x_dummy, *pars), '--', c='g')
                    self.ax.plot( mean_x, mean_y, '--', c='g')
                    avg_ttk = x_o[-1]
                else:
                    x= [0,sum(times_list)/len(times_list)]
                    y=[enemy.max_health+enemy.max_shield, 0]
                    self.ax.plot( x, y, '--', c='g')
            
            
            self.ax.text(avg_ttk,0, "---------------%s %s, %.1fs"%(self.ui.custom_build_weapon_combo.currentText(), self.ui.custom_build_fire_mode_combo.currentText(), avg_ttk), rotation=90, ha='center', va='baseline' )
            #self.ax.text(avg_ttk,0, "%.1fs"%(avg_ttk), rotation=90, va='top' )
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Enemy Life Points")
            plt.tight_layout()
            plt.show()
            self.fig.canvas.draw() 
            

        return (enemy_level, sum(times_list)/len(times_list))

    def simulate_once(self):
        enemy_name = self.ui.enemy_select_combo.currentText()
        enemy_level = self.ui.enemy_level_spinner.value()
        start_time = time.time()
        enemy = Enemy(enemy_name, enemy_level, self.ui)
        weapon = self.custom_build_init_weapon()
        kill_time, xvals, yvals, shield_time, shield_prog, armor_time, armor_vals = enemy.kill(weapon)

        self.ui.ttk_mean_textbox.setPlainText("%.2f s"%( kill_time ) )
        self.ui.dps_mean_textbox.setPlainText("%.2f"%( (enemy.max_health+enemy.max_shield)/kill_time ) )
        self.ui.ttk_std_textbox.setPlainText("N/A")
        self.ui.dps_std_textbox.setPlainText("N/A")

        self.ui.slash_dps_mean_textbox.setPlainText("%.2f"%( enemy.slash_proc_manager.total_applied_damage/kill_time ) )
        self.ui.toxin_dps_mean_textbox.setPlainText("%.2f"%( enemy.toxin_proc_manager.total_applied_damage/kill_time ) )
        self.ui.electric_dps_mean_textbox.setPlainText("%.2f"%( enemy.electric_proc_manager.total_applied_damage/kill_time ) )
        self.ui.heat_dps_mean_textbox.setPlainText("%.2f"%( enemy.heat_proc_manager.total_applied_damage/kill_time ) )
        self.ui.gas_dps_mean_textbox.setPlainText("%.2f"%( enemy.gas_proc_manager.total_applied_damage/kill_time ) )

        self.ui.slash_dps_percent_textbox.setPlainText("%.2f%%"%( 100*enemy.slash_proc_manager.total_applied_damage/kill_time / ((enemy.max_health+enemy.max_shield)/kill_time)  ) )
        self.ui.toxin_dps_percent_textbox.setPlainText("%.2f%%"%( 100*enemy.toxin_proc_manager.total_applied_damage/kill_time/ ((enemy.max_health+enemy.max_shield)/kill_time) ) )
        self.ui.electric_dps_percent_textbox.setPlainText("%.2f%%"%( 100*enemy.electric_proc_manager.total_applied_damage/kill_time/ ((enemy.max_health+enemy.max_shield)/kill_time) ) )
        self.ui.heat_dps_percent_textbox.setPlainText("%.2f%%"%( 100*enemy.heat_proc_manager.total_applied_damage/kill_time/ ((enemy.max_health+enemy.max_shield)/kill_time) ) )
        self.ui.gas_dps_percent_textbox.setPlainText("%.2f%%"%( 100*enemy.gas_proc_manager.total_applied_damage/kill_time/ ((enemy.max_health+enemy.max_shield)/kill_time) ) )

        if not plt.get_fignums():
            self.fig, (self.ax, self.ax2) = plt.subplots(1,2)

        sns.lineplot(x=xvals, y=yvals, ci = None, ax=self.ax)
        sns.lineplot(x=shield_time, y=shield_prog, ci = None, ax=self.ax)
        sns.lineplot(x=armor_time, y=armor_vals, ci = None, ax=self.ax)

        self.ax2.clear()
        data_dict = {"Applied Damage":enemy.damage_instance_list}
        sns.countplot(data=data_dict, x="Applied Damage", ax = self.ax2)
        #self.ax2.xticks(rotation=45)
        self.ax2.tick_params(axis='x', labelrotation = 45)
        total = len(enemy.damage_instance_list)
        for p in self.ax2.patches:
            percentage = f'{100 * p.get_height() / total:.1f}%\n'
            x = p.get_x() + p.get_width() / 2
            y = p.get_height()
            self.ax2.annotate(percentage, (x, y), ha='center', va='center')
        
        
        self.ax.text(kill_time,0, "---------------%s %s, %.1fs"%(self.ui.custom_build_weapon_combo.currentText(), self.ui.custom_build_fire_mode_combo.currentText(), kill_time), rotation=90, ha='center', va='baseline' )
        #self.ax.text(avg_ttk,0, "%.1fs"%(avg_ttk), rotation=90, va='top' )
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Enemy Life Points")
        plt.show()
        plt.tight_layout()
        self.fig.canvas.draw() 

        

        '''
        plt.plot(xvals, yvals)
        plt.plot(armor_time, armor_vals)
        plt.show()
        '''
        print("Kill time: %f"%kill_time)

    @QtCore.Slot()
    def scale(self):
        x=[]
        y=[]
        for i in range(1, self.ui.enemy_level_spinner.value(), int(self.ui.enemy_level_spinner.value()/10)):
            lvl, tim = self.simulate(enemy_level = i, min_iterations = 20, plot = False)
            x.append(lvl)
            y.append(tim)
        plt.plot(x,y, label='%s %s %s'%(self.ui.enemy_select_combo.currentText(), self.ui.custom_build_weapon_combo.currentText(), self.ui.custom_build_fire_mode_combo.currentText()))
        plt.legend()
        plt.xlabel("Enemy Level")
        plt.ylabel("Avg Time To Kill (s)")
        plt.show()
        self.fig.canvas.draw() 

    def simulate_best_riven(self):
        num_simu = 10
        # get the slider state
        riven_grade = 0.9+0.2*self.ui.riven_grade_slider.value()/100



        '''
        2 Bonus 0 Negative	0.99	0
        2 Bonus 1 Negative	1.2375	-0.495
        3 Bonus 0 Negative	0.75	0
        3 Bonus 1 Negative	0.9375	-0.75
        '''
        bonus = self.ui.riven_positive_spinner.value()
        neg = self.ui.riven_negative_spinner.value()
        bonus_mul = 0
        neg_mul = 0
        if bonus == 2 and neg == 0:
            bonus_mul = 0.99
            neg_mul = 0
        elif bonus == 2 and neg == 1:
            bonus_mul = 1.2375
            neg_mul = -0.495
        elif bonus == 3 and neg == 0:
            bonus_mul = 0.75
            neg_mul = 0
        elif bonus == 3 and neg == 1:
            bonus_mul = 0.9375
            neg_mul = -0.75

        enemy_name = self.ui.enemy_select_combo.currentText()
        enemy_level = self.ui.enemy_level_spinner.value()
        weapon = self.custom_build_init_weapon()

        total_bonus_mul = weapon.disposition * bonus_mul * riven_grade
        total_neg_mul = weapon.disposition * neg_mul * riven_grade
        bonus_list = [ f*total_bonus_mul for f in weapon.riven_bonus_list]
        neg_list = [ f*total_neg_mul for f in weapon.riven_neg_list]

        total_bonus_mul = weapon.disposition * bonus_mul * riven_grade
        total_neg_mul = weapon.disposition * neg_mul * riven_grade

        stats=[]
        for iter in range(bonus):
            pos_res = [0]*len(bonus_list)
            for i, riven_pos_bonus in enumerate( bonus_list ):
                if riven_pos_bonus != 0 :
                    cur_text = self.custom_build_mod_list[i].toPlainText()
                    if cur_text =='':
                        self.custom_build_mod_list[i].setPlainText( (cur_text+"$%.2f"%riven_pos_bonus) )
                    else:
                        self.custom_build_mod_list[i].setPlainText( (cur_text+"$%.2f"%riven_pos_bonus) if cur_text[-1] == ' ' else (cur_text+" $%.2f"%riven_pos_bonus) )
                    #do simulation
                    for j in range(num_simu):
                        enemy = Enemy(enemy_name, enemy_level, self.ui)
                        weapon = self.custom_build_init_weapon()
                        kill_time,*_ = enemy.kill(weapon)
                        pos_res[i] += kill_time
                    pos_res[i] /= num_simu
                    #save result
                    self.custom_build_mod_list[i].setPlainText( cur_text )
                else:
                    pos_res[i] = 1000
            pos_res = [ (k, v) for k,v in enumerate(pos_res) ]
            pos_res.sort(key=lambda y: y[1])
            best_index, _ = pos_res[0]

            val = bonus_list[best_index]
            cur_text = self.custom_build_mod_list[best_index].toPlainText()
            if cur_text =='':
                self.custom_build_mod_list[best_index].setPlainText( (cur_text+"$%.2f"%val) )
            else:
                self.custom_build_mod_list[best_index].setPlainText( (cur_text+"$%.2f"%val) if cur_text[-1] == ' ' else (cur_text+" $%.2f"%val) )

            stats.append( pos_res )
            bonus_list[best_index] = 0

        for iter in range(neg):
            neg_res = [0]*len(neg_list)
            for i, riven_neg_bonus in enumerate( neg_list ):
                if riven_neg_bonus != 0 :
                    cur_text = self.custom_build_mod_list[i].toPlainText()
                    if cur_text =='':
                        self.custom_build_mod_list[i].setPlainText( (cur_text+"$%.2f"%riven_neg_bonus) )
                    else:
                        self.custom_build_mod_list[i].setPlainText( (cur_text+"$%.2f"%riven_neg_bonus) if cur_text[-1] == ' ' else (cur_text+" $%.2f"%riven_neg_bonus) )
                    #do simulation
                    for j in range(num_simu):
                        enemy = Enemy(enemy_name, enemy_level, self.ui)
                        weapon = self.custom_build_init_weapon()
                        kill_time,*_ = enemy.kill(weapon)
                        neg_res[i] += kill_time
                    neg_res[i] /= num_simu
                    #save result
                    self.custom_build_mod_list[i].setPlainText( cur_text )
                else:
                    neg_res[i] = 1000


            neg_res = [ (k, v) for k,v in enumerate(neg_res) ]
            neg_res.sort(key=lambda y: y[1])
            best_index, _ = neg_res[0]
            val = neg_list[best_index]
            cur_text = self.custom_build_mod_list[best_index].toPlainText()
            if cur_text =='':
                self.custom_build_mod_list[best_index].setPlainText( (cur_text+"$%.2f"%val) )
            else:
                self.custom_build_mod_list[best_index].setPlainText( (cur_text+"$%.2f"%val) if cur_text[-1] == ' ' else (cur_text+" $%.2f"%val) )

        # construct string
        bonus_list = [ f*total_bonus_mul for f in weapon.riven_bonus_list]
        neg_list = [ f*total_neg_mul for f in weapon.riven_neg_list]
        res_string ='Rank                           First                           Second                          Third       \n'
        for i in range(len(pos_res)):
            res_string += "%d               "%i
            for j in range(len(stats)):
                indexx, val_pc = stats[j][i]
                if val_pc < 20:
                    res_string += "%s:%.2f%%:%.2fs                  "%(weapon.riven_buff_name_list[indexx], bonus_list[indexx], val_pc)
                else:
                    res_string += "                                   "
            res_string += "\n"

        self.ui.riven_result_textbox.setPlainText(res_string)

    @QtCore.Slot()
    def edit_weapon_combo_listener(self):
        self.clear_edit_fire_mode_combo()
        name = self.ui.edit_weapon_combo.currentText()
        if name == "New Weapon":
            self.ui.new_weapon_text.show()
            self.ui.edit_fire_mode_radio.toggle()
            self.ui.edit_secondary_effect_radio.setEnabled(False)
            # show weapon type combo
            self.ui.edit_weapon_type_combo.setEnabled(True)
            self.ui.edit_weapon_type_combo.show()
            self.ui.edit_weapon_type_label.show()

        elif name != '':
            #hide new weapon name textbox
            self.ui.new_weapon_text.hide()
            #load list of firemodes
            self.ui.edit_secondary_effect_radio.setEnabled(True)
            self.ui.edit_fire_mode_combo.addItems(get_fire_mode_list(name))

            # hide weapon type combo and reset selection index
            self.ui.edit_weapon_type_combo.setCurrentIndex(0)
            self.ui.edit_weapon_type_combo.setEnabled(False)
            self.ui.edit_weapon_type_combo.hide()
            self.ui.edit_weapon_type_label.hide()

    @QtCore.Slot()
    def edit_weapon_type_combo_listener(self):
        name = self.ui.edit_weapon_type_combo.currentText()
        if name == "Melee":
            self.ui.edit_weapon_stance_label.setEnabled(True)
            self.ui.edit_weapon_stance_label.show()
            # show weapon type combo
            self.ui.edit_weapon_category_combo.setEnabled(True)
            self.ui.edit_weapon_category_combo.show()

        else:
            self.ui.edit_weapon_stance_label.setEnabled(False)
            self.ui.edit_weapon_stance_label.hide()
            self.ui.edit_weapon_category_combo.setEnabled(False)
            self.ui.edit_weapon_category_combo.hide()

    @QtCore.Slot()
    def custom_build_weapon_combo_listener(self):
        weapon_data = get_weapon_data()
        stance_data = get_stance_data()
        self.clear_custom_build_fire_mode_combo()
        name = self.ui.custom_build_weapon_combo.currentText()
        if name != '':
            self.ui.custom_build_fire_mode_combo.addItems(get_fire_mode_list(name))
            if self.get_weapon_type(name) == "Melee":
                #clear stance combos
                self.ui.custom_build_stance_combo.clear()
                self.ui.custom_build_stance_moveset_combo.clear()
                #enable and show stance combos
                self.ui.custom_build_stance_combo.setEnabled(True)
                self.ui.custom_build_stance_combo.show()
                self.ui.stance_build_label.show()
                self.ui.custom_build_stance_moveset_combo.setEnabled(True)
                self.ui.custom_build_stance_moveset_combo.show()
                self.ui.moveset_build_label.show()
                #Load stances
                weapon_type = weapon_data[name]["Fire Modes"][list(weapon_data[name]['Fire Modes'].keys())[0]].get("type","Glaive")
                for stnc, val in stance_data.items():
                    if val["Class"] == weapon_type:
                        self.ui.custom_build_stance_combo.addItem(stnc)
            else:
                #Hide stance stuff
                self.ui.custom_build_stance_combo.setEnabled(False)
                self.ui.custom_build_stance_combo.hide()
                self.ui.stance_build_label.hide()
                self.ui.custom_build_stance_moveset_combo.setEnabled(False)
                self.ui.custom_build_stance_moveset_combo.hide()
                self.ui.moveset_build_label.hide()

    @QtCore.Slot()
    def custom_build_fire_mode_combo_listener(self):
        pass

    @QtCore.Slot()
    def edit_enemy_combo_listener(self):
        enemy_name = self.ui.edit_enemy_combo.currentText()
        if enemy_name != "New Enemy" and enemy_name != "":
            '''
            self.ui.edit_enemy_stats_table.setItem(0, 0, QtWidgets.QTableWidgetItem(str(self.get_enemy_property("base_health", enemy_name ))))
            self.ui.edit_enemy_stats_table.setItem(1, 0, QtWidgets.QTableWidgetItem(str(self.get_enemy_property("base_armor", enemy_name ))))
            self.ui.edit_enemy_stats_table.setItem(2, 0, QtWidgets.QTableWidgetItem(str(self.get_enemy_property("base_shield", enemy_name ))))
            self.ui.edit_enemy_stats_table.setItem(3, 0, QtWidgets.QTableWidgetItem(str(self.get_enemy_property("base_level", enemy_name ))))
            self.ui.edit_enemy_stats_table.setItem(4, 0, QtWidgets.QTableWidgetItem(str(self.get_enemy_property("enemy_type", enemy_name ))))
            '''

            self.ui.health_edit_textbox.setPlainText( "%.0f"%(self.get_enemy_property("base_health", enemy_name )) )
            self.ui.armor_edit_textbox.setPlainText( "%.0f"%(self.get_enemy_property("base_armor", enemy_name )) )
            self.ui.shield_edit_textbox.setPlainText( "%.0f"%(self.get_enemy_property("base_shield", enemy_name )) )
            self.ui.level_edit_textbox.setPlainText( "%.0f"%(self.get_enemy_property("base_level", enemy_name )) )
            self.ui.dr_edit_textbox.setPlainText( "%.2f"%(self.get_enemy_property("base_dr", enemy_name )) )

    @QtCore.Slot()
    def custom_build_stance_combo_listener(self):
        if self.ui.custom_build_stance_combo.currentText() != '':
            weapon_data = get_weapon_data()
            stance_data = get_stance_data()
            self.ui.custom_build_stance_moveset_combo.clear()
            stancename = self.ui.custom_build_stance_combo.currentText()
            self.ui.custom_build_stance_moveset_combo.addItems([f for f in stance_data[stancename]["ComboName"].keys()])

    @QtCore.Slot()
    def edit_fire_mode_radio_listener(self):
        #self.clear_fire_mode_combo()
        if self.ui.edit_fire_mode_combo.currentText() == "New Fire Mode":
            self.ui.edit_fire_mode_radio.toggle()
            self.ui.edit_secondary_effect_radio.setEnabled(False)
        else:
            #load list of firemodes
            self.ui.edit_secondary_effect_radio.setEnabled(True)

        if self.ui.edit_fire_mode_radio.isChecked():
            #disable sec eff selection
            self.ui.edit_secondary_effect_combo.setEnabled(False)
            self.ui.edit_secondary_effect_combo.hide()
            self.ui.edit_secondary_effect_text.setEnabled(False)
            self.ui.edit_secondary_effect_text.hide()
            #enable fire mode combo
            self.ui.edit_fire_mode_combo.setEnabled(True)
            self.ui.edit_fire_mode_combo.show()
            self.ui.new_fire_mode_text.setEnabled(True)
            self.ui.new_fire_mode_text.show()

            self.load_stats()
        else:
            #enable sec eff
            self.ui.edit_secondary_effect_combo.setEnabled(True)
            self.ui.edit_secondary_effect_combo.show()
            self.ui.edit_secondary_effect_text.setEnabled(True)
            self.ui.edit_secondary_effect_text.show()
            self.ui.edit_secondary_effect_radio.setEnabled(True)
            self.ui.edit_secondary_effect_radio.show()
            #enable fire mode combo
            self.ui.new_fire_mode_text.setEnabled(False)
            self.ui.new_fire_mode_text.hide()
            '''
            self.ui.fire_mode_combo.setEnabled(False)
            self.ui.fire_mode_combo.hide()
            self.ui.new_fire_mode_text.setEnabled(False)
            self.ui.new_fire_mode_text.hide()
            '''
    @QtCore.Slot()
    def edit_fire_mode_combo_listener(self):
        self.clear_edit_secondary_effect_combo()
        name = self.ui.edit_weapon_combo.currentText()
        fire_mode = self.ui.edit_fire_mode_combo.currentText()

        if self.ui.edit_fire_mode_combo.currentText() == "New Fire Mode":
            self.ui.edit_fire_mode_radio.toggle()
            self.ui.edit_secondary_effect_combo.setEnabled(False)
            self.ui.edit_secondary_effect_combo.hide()
            self.ui.edit_secondary_effect_text.setEnabled(False)
            self.ui.edit_secondary_effect_text.hide()
            self.ui.edit_secondary_effect_radio.setEnabled(False)
            self.ui.edit_secondary_effect_radio.hide()
        elif self.ui.edit_fire_mode_combo.currentText() != "":
            self.ui.edit_secondary_effect_radio.setEnabled(True)
            self.ui.edit_secondary_effect_radio.show()

            self.ui.edit_secondary_effect_combo.addItems(get_secondary_effects(name, fire_mode))
            if self.ui.edit_fire_mode_radio.isChecked():
                self.ui.edit_secondary_effect_combo.setEnabled(False)
                self.ui.edit_secondary_effect_combo.hide()
                self.ui.edit_secondary_effect_text.setEnabled(False)
                self.ui.edit_secondary_effect_text.hide()
            else:
                self.ui.edit_secondary_effect_combo.setEnabled(True)
                self.ui.edit_secondary_effect_combo.show()
                self.ui.edit_secondary_effect_text.setEnabled(True)
                self.ui.edit_secondary_effect_text.show()
            self.load_stats()

    @QtCore.Slot()
    def secondary_effects_combo_listener(self):
        if self.ui.edit_secondary_effect_combo.isEnabled() and self.ui.edit_secondary_effect_combo.currentText() != "" and self.ui.edit_secondary_effect_combo.currentText() != "New Secondary Effect":
            self.load_stats()

    def custom_build_init_weapon(self):
        if self.ui.custom_build_fire_mode_combo.currentText() != '':
            selected_wep = Weapon(self.ui.custom_build_weapon_combo.currentText(), self.ui.custom_build_fire_mode_combo.currentText(), self.ui)
            selected_wep.get_custom_build_mods(self.ui)
            for effects in selected_wep.weapon_effects:
                if effects is not None:
                    effects.apply_mods(selected_wep)
            return selected_wep

    def clear_edit_fire_mode_combo(self):
        #clear fire_mode_combo
        self.ui.edit_fire_mode_combo.clear()
        self.ui.edit_fire_mode_combo.addItem("New Fire Mode")

    def clear_custom_build_fire_mode_combo(self):
        #clear fire_mode_combo
        self.ui.custom_build_fire_mode_combo.clear()

    def clear_edit_secondary_effect_combo(self):
        #clear fire_mode_combo
        self.ui.edit_secondary_effect_combo.clear()
        self.ui.edit_secondary_effect_combo.addItem("New Secondary Effect")
    def load_stats(self):
        weapon_data = get_weapon_data()

        wep_name = self.ui.edit_weapon_combo.currentText()
        fm_name = self.ui.edit_fire_mode_combo.currentText()

        if self.ui.edit_secondary_effect_combo.currentText() != "New Secondary Effect" and self.ui.edit_secondary_effect_radio.isChecked():
            #load sec eff stats
            se_name = self.ui.edit_secondary_effect_combo.currentText()
            damage = weapon_data[wep_name]["Fire Modes"][fm_name]["Secondary Effects"][se_name].get("damagePerShot")

            self.ui.impact_edit_textbox.setPlainText("%f"%damage[0])
            self.ui.puncture_edit_textbox.setPlainText("%f"%damage[1])
            self.ui.slash_edit_textbox.setPlainText("%f"%damage[2])

            self.ui.heat_edit_textbox.setPlainText("%f"%damage[3])
            self.ui.cold_edit_textbox.setPlainText("%f"%damage[4])
            self.ui.electric_edit_textbox.setPlainText("%f"%damage[5])
            self.ui.toxin_edit_textbox.setPlainText("%f"%damage[6])

            self.ui.blast_edit_textbox.setPlainText("%f"%damage[7])
            self.ui.radiation_edit_textbox.setPlainText("%f"%damage[8])
            self.ui.gas_edit_textbox.setPlainText("%f"%damage[9])
            self.ui.magnetic_edit_textbox.setPlainText("%f"%damage[10])
            self.ui.viral_edit_textbox.setPlainText("%f"%damage[11])
            self.ui.corrosive_edit_textbox.setPlainText("%f"%damage[12])
            self.ui.void_edit_textbox.setPlainText("%f"%damage[13])
            self.ui.true_edit_textbox.setPlainText("%f"%damage[14])

            self.ui.critical_chance_edit_textbox.setPlainText( "%f"%self.get_weapon_property("criticalChance", wep_name, fm_name, se_name ) )
            self.ui.critical_damage_edit_textbox.setPlainText( "%f"%self.get_weapon_property("criticalMultiplier", wep_name, fm_name, se_name ) )
            self.ui.pellet_edit_textbox.setPlainText( "%f"%self.get_weapon_property("multishot", wep_name, fm_name, se_name ) )
            self.ui.status_chance_edit_textbox.setPlainText( "%f"%self.get_weapon_property("procChance", wep_name, fm_name, se_name ) )
            self.ui.fire_rate_edit_textbox.setPlainText( "%f"%self.get_weapon_property("fireRate", wep_name, fm_name, se_name ) )
            self.ui.reload_speed_edit_textbox.setPlainText( "%f"%self.get_weapon_property("reloadTime", wep_name, fm_name, se_name ) )
            self.ui.charge_time_edit_textbox.setPlainText( "%f"%self.get_weapon_property("chargeTime", wep_name, fm_name, se_name ) )
            self.ui.embed_delay_edit_textbox.setPlainText( "%f"%self.get_weapon_property("embedDelay", wep_name, fm_name, se_name ) )
            self.ui.magazine_edit_textbox.setPlainText( "%f"%self.get_weapon_property("magazineSize", wep_name, fm_name, se_name ) )
            self.ui.ammo_edit_textbox.setPlainText( "%f"%self.get_weapon_property("ammo", wep_name, fm_name, se_name ) )
            self.ui.ammo_cost_edit_textbox.setPlainText( "%f"%self.get_weapon_property("ammoCost", wep_name, fm_name, se_name ) )

        elif self.ui.edit_fire_mode_combo.currentText() != "New Fire Mode" and self.ui.edit_fire_mode_radio.isChecked():
            damage = weapon_data[wep_name]["Fire Modes"][fm_name].get("damagePerShot")

            self.ui.impact_edit_textbox.setPlainText("%f"%damage[0])
            self.ui.puncture_edit_textbox.setPlainText("%f"%damage[1])
            self.ui.slash_edit_textbox.setPlainText("%f"%damage[2])

            self.ui.heat_edit_textbox.setPlainText("%f"%damage[3])
            self.ui.cold_edit_textbox.setPlainText("%f"%damage[4])
            self.ui.electric_edit_textbox.setPlainText("%f"%damage[5])
            self.ui.toxin_edit_textbox.setPlainText("%f"%damage[6])

            self.ui.blast_edit_textbox.setPlainText("%f"%damage[7])
            self.ui.radiation_edit_textbox.setPlainText("%f"%damage[8])
            self.ui.gas_edit_textbox.setPlainText("%f"%damage[9])
            self.ui.magnetic_edit_textbox.setPlainText("%f"%damage[10])
            self.ui.viral_edit_textbox.setPlainText("%f"%damage[11])
            self.ui.corrosive_edit_textbox.setPlainText("%f"%damage[12])
            self.ui.void_edit_textbox.setPlainText("%f"%damage[13])
            self.ui.true_edit_textbox.setPlainText("%f"%damage[14])

            self.ui.critical_chance_edit_textbox.setPlainText( "%f"%self.get_weapon_property("criticalChance", wep_name, fm_name ) )
            self.ui.critical_damage_edit_textbox.setPlainText( "%f"%self.get_weapon_property("criticalMultiplier", wep_name, fm_name ) )
            self.ui.pellet_edit_textbox.setPlainText( "%f"%self.get_weapon_property("multishot", wep_name, fm_name ) )
            self.ui.status_chance_edit_textbox.setPlainText( "%f"%self.get_weapon_property("procChance", wep_name, fm_name ) )
            self.ui.fire_rate_edit_textbox.setPlainText( "%f"%self.get_weapon_property("fireRate", wep_name, fm_name ) )
            self.ui.reload_speed_edit_textbox.setPlainText( "%f"%self.get_weapon_property("reloadTime", wep_name, fm_name ) )
            self.ui.charge_time_edit_textbox.setPlainText( "%f"%self.get_weapon_property("chargeTime", wep_name, fm_name ) )
            self.ui.embed_delay_edit_textbox.setPlainText( "%f"%self.get_weapon_property("embedDelay", wep_name, fm_name ) )
            self.ui.magazine_edit_textbox.setPlainText( "%.0f"%self.get_weapon_property("magazineSize", wep_name, fm_name ) )
            self.ui.ammo_edit_textbox.setPlainText( "%.0f"%self.get_weapon_property("ammo", wep_name, fm_name ) )
            self.ui.ammo_cost_edit_textbox.setPlainText( "%.0f"%self.get_weapon_property("ammoCost", wep_name, fm_name ) )

    @QtCore.Slot()
    def update_display_build_table(self):
        weapon = self.custom_build_init_weapon()

        enemy_name = self.ui.enemy_select_combo.currentText()
        enemy = None
        if enemy_name != '' and weapon is not None:
            enemy_level = self.ui.enemy_level_spinner.value()
            enemy = Enemy(enemy_name, enemy_level, self.ui)

            # update enemy display table
            self.ui.enemy_display_textbox.setPlainText(enemy_name)
            self.ui.health_display_textbox.setPlainText(f"{enemy.max_health:,.2f}")
            self.ui.armor_display_textbox.setPlainText(f"{enemy.max_armor:,.2f}")
            self.ui.shield_display_textbox.setPlainText(f"{enemy.max_shield:,.2f}")
            self.ui.ehp_display_textbox.setPlainText(f"{enemy.ehp:,.2f}")
            self.ui.enemy_type_display_textbox.setPlainText(enemy.enemy_type)
            self.ui.level_display_textbox.setPlainText(f"{enemy.level:,.0f}")

            crit_tier = self.ui.display_weapon_critical_tier_spinner.value()

            if weapon.main_effect.trigger == "HELD":
                sh_dmg1, hp_dmg1, of_dmg1 = enemy.get_first_shot_damage( weapon.main_effect.modded_damage, weapon.main_effect, crit_tier, int(weapon.main_effect.modded_pellets))
                sh_dmg2, hp_dmg2, of_dmg2 = enemy.get_first_shot_damage( weapon.main_effect.modded_damage, weapon.main_effect, crit_tier, int(weapon.main_effect.modded_pellets)+1)
                s1 = "(%.0f, %.0f)"%(hp_dmg1 * (int(weapon.main_effect.modded_pellets)), hp_dmg2 * (int(weapon.main_effect.modded_pellets)+1))
                s2 = "(%.0f, %.0f)"%(sh_dmg1 * (int(weapon.main_effect.modded_pellets)), sh_dmg2 * (int(weapon.main_effect.modded_pellets)+1))
                s3 = "(%.0f, %.0f)"%(of_dmg1 * (int(weapon.main_effect.modded_pellets)), of_dmg2 * (int(weapon.main_effect.modded_pellets)+1))

                self.ui.health_damage_display_textbox.setPlainText(s1)
                self.ui.shield_damage_display_textbox.setPlainText(s2)
                self.ui.overflow_damage_display_textbox.setPlainText(s3)
            else:
                sh_dmg, hp_dmg, of_dmg = enemy.get_first_shot_damage( weapon.main_effect.modded_damage, weapon.main_effect, crit_tier)

                self.ui.health_damage_display_textbox.setPlainText(f"{hp_dmg:,.2f}")
                self.ui.shield_damage_display_textbox.setPlainText(f"{sh_dmg:,.2f}")
                self.ui.overflow_damage_display_textbox.setPlainText(f"{of_dmg:,.2f}")

        if weapon is not None:
            if enemy is not None:
                weapon.apply_proc_immunity(enemy.proc_immunity)
            wep_eff = weapon.main_effect

            self.ui.pellets_display_textbox.setPlainText( "%.2f"%wep_eff.modded_pellets )
            self.ui.critical_chance_display_textbox.setPlainText( "%.2f%%"%(wep_eff.modded_critical_chance*100) )
            self.ui.critical_damage_display_textbox.setPlainText( "%.2fx"%wep_eff.modded_critical_multiplier )
            self.ui.fire_rate_display_textbox.setPlainText( "%.2f"%wep_eff.modded_fire_rate )

            self.ui.status_chance_display_textbox.setPlainText( "%.2f%%"%(wep_eff.modded_status_chance*100) )

            self.ui.reload_speed_display_textbox.setPlainText( "%.2f s"%wep_eff.modded_reload )
            self.ui.magazine_size_display_textbox.setPlainText( "%.0f"%wep_eff.modded_magazine )
            self.ui.ammo_max_display_textbox.setPlainText( "%.0f"%wep_eff.modded_ammo )
            self.ui.ammo_cost_display_textbox.setPlainText( "%.2f"%wep_eff.modded_ammo_cost )

            self.ui.charge_time_display_textbox.setPlainText( "%.2f s"%wep_eff.modded_charge_time )
            self.ui.embed_delay_display_textbox.setPlainText( "%.2f s"%wep_eff.modded_embed_delay )

            j=0
            for i, elem in enumerate(wep_eff.modded_damage):
                if elem != 0:
                    self.elemental_display_labels[j].show()
                    self.elemental_display_textboxes[j].show()
                    self.elemental_display_textboxes_1[j].show()
                    self.elemental_display_labels[j].setText( get_type_name(i) )
                    self.elemental_display_textboxes[j].setPlainText( "%.2f"%elem )
                    self.elemental_display_textboxes_1[j].setPlainText( "%.2f%%"%(wep_eff.status_effect_chance[i]*wep_eff.modded_status_chance*100) )
                    j+=1
            for i in range(j, len(self.elemental_display_labels)):
                self.elemental_display_labels[i].hide()
                self.elemental_display_textboxes[i].hide()
                self.elemental_display_textboxes_1[i].hide()
            if j+1 < len(self.elemental_display_labels):
                self.elemental_display_textboxes[j+1].show()
                self.elemental_display_labels[j+1].show()
                self.elemental_display_labels[j+1].setText( "Total Damage" )
                self.elemental_display_textboxes[j+1].setPlainText( "%.2f"%wep_eff.modded_total_damage )

    @QtCore.Slot()
    def save_data(self):
        weapon = self.custom_build_init_weapon()
        weapon_effect = weapon.main_effect

        txt = self.ui.data_text.toPlainText()
        in_game_damage = text_config_to_double(txt)
        with open(weapon.name+'.json', 'r') as data_file:
            save_data = json.load(data_file)

        enemy_name = self.ui.enemy_select_combo.currentText()
        if enemy_name != '' and weapon is not None:
            enemy_level = self.ui.enemy_level_spinner.value()
            enemy = Enemy(enemy_name, enemy_level, self.ui)
            crit_tier = self.ui.display_weapon_critical_tier_spinner.value()
            cd = enemy.get_critical_damage_state(weapon.main_effect, crit_tier)
            cdm = weapon.critical_multiplier_mods

            if weapon.main_effect.trigger == "HELD":
                sh_dmg1, hp_dmg1, sh_dps1, hp_dps1 = enemy.get_unreduced_damage_and_dps( weapon.main_effect.modded_damage, weapon.main_effect, int(weapon.main_effect.modded_pellets))
                sh_dmg2, hp_dmg2, sh_dps2, hp_dps2 = enemy.get_unreduced_damage_and_dps( weapon.main_effect.modded_damage, weapon.main_effect, int(weapon.main_effect.modded_pellets)+1)

                new_data = {
                    "trigger": weapon.main_effect.trigger,
                    "mulishot": weapon.main_effect.modded_pellets,
                    "criticalMultiplier": cd,
                    "baseCriticalMultiplier":weapon_effect.base_critical_multiplier,
                    "criticalMultiplierMods": cdm,
                    "critTier":crit_tier,
                    "enemyName": enemy.name,
                    "enemyArmor": enemy.current_armor,
                    "inGameDamage": in_game_damage,
                    "shieldDamage1": sh_dmg1,
                    "shieldDamage2": sh_dmg2,
                    "healthDamage1": hp_dmg1,
                    "healthDamage2": hp_dmg2,

                    "shieldDPS1": sh_dps1,
                    "shieldDPS2": sh_dps2,
                    "healthDPS1": hp_dps1,
                    "healthDPS2": hp_dps2
                            }
            else:
                sh_dmg, hp_dmg, sh_dps, hp_dps = enemy.get_unreduced_damage_and_dps( weapon.main_effect.modded_damage, weapon.main_effect)

                new_data = {
                    "trigger": weapon.main_effect.trigger,
                    "mulishot": weapon.main_effect.modded_pellets,
                    "criticalMultiplier": cd,
                    "baseCriticalMultiplier":weapon_effect.base_critical_multiplier,
                    "criticalMultiplierMods": cdm,
                    "critTier":crit_tier,
                    "enemyName": enemy.name,
                    "enemyArmor": enemy.current_armor,
                    "inGameDamage": in_game_damage,
                    "shieldDamage1": sh_dmg,
                    "shieldDamage2": sh_dmg,
                    "healthDamage1": hp_dmg,
                    "healthDamage2": hp_dmg,

                    "shieldDPS1": sh_dps,
                    "shieldDPS2": sh_dps,
                    "healthDPS1": hp_dps,
                    "healthDPS2": hp_dps
                            }

        save_data.append(new_data)

        with open(weapon.name+'.json', 'w') as f:
            json.dump(save_data, f)
    def get_weapon_property(self, prop, wepname, fmname, sename = None):
        if sename is not None:
            weapon_data = get_weapon_data()
            return weapon_data[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename].get(prop, 0)
        else:
            weapon_data = get_weapon_data()
            return weapon_data[wepname]["Fire Modes"][fmname].get(prop,0)

    def get_enemy_property(self, prop, enemyname):
        enemy_data = get_enemy_data()
        return enemy_data[enemyname].get(prop, 1)

    def get_weapon_type(self, wepname):
        weapon_data = get_weapon_data()
        return weapon_data[wepname]["Fire Modes"][list(weapon_data[wepname]['Fire Modes'].keys())[0]].get("productCategory", "LongGuns")

    def save_enemy(self):
        enemy_data = get_enemy_data()

        if self.ui.edit_enemy_combo.currentText() == 'New Enemy':
            enemy_name = self.ui.edit_enemy_name_text.toPlainText()
        else:
            enemy_name = self.ui.edit_enemy_combo.currentText()
        enemy_data[enemy_name] = {}

        '''
        enemy_data[enemy_name]['base_health'] = text_config_to_double( convert_widget_item_to_string( self.ui.edit_enemy_stats_table.item(0,0) ) )
        enemy_data[enemy_name]['base_armor'] = text_config_to_double( convert_widget_item_to_string( self.ui.edit_enemy_stats_table.item(1,0) ) )
        enemy_data[enemy_name]['base_shield'] = text_config_to_double( convert_widget_item_to_string( self.ui.edit_enemy_stats_table.item(2,0) ) )
        enemy_data[enemy_name]['base_level'] = text_config_to_double( convert_widget_item_to_string( self.ui.edit_enemy_stats_table.item(3,0) ) )
        '''

        enemy_data[enemy_name]['base_health'] = text_config_to_double( self.ui.health_edit_textbox.toPlainText() )
        enemy_data[enemy_name]['base_armor'] = text_config_to_double( self.ui.armor_edit_textbox.toPlainText() )
        enemy_data[enemy_name]['base_shield'] = text_config_to_double( self.ui.shield_edit_textbox.toPlainText() )
        enemy_data[enemy_name]['base_level'] = text_config_to_double( self.ui.level_edit_textbox.toPlainText() )
        enemy_data[enemy_name]['base_dr'] = text_config_to_double( self.ui.dr_edit_textbox.toPlainText() )

        enemy_data[enemy_name]['health_type'] = self.ui.edit_enemy_health_type_combo.currentText()
        enemy_data[enemy_name]['armor_type'] = self.ui.edit_enemy_armor_combo.currentText()
        enemy_data[enemy_name]['shield_type'] = self.ui.edit_enemy_shield_combo.currentText()
        enemy_data[enemy_name]['enemy_type'] = self.ui.edit_enemy_type_combo.currentText()

        with open('enemy_data.json', 'w') as f:
            json.dump(enemy_data, f)

        self.update_enemy_combos()

    def delete_enemy(self):
        if self.ui.edit_enemy_combo.currentText() == 'New Enemy':
            return
        else:
            enemy_name = self.ui.edit_enemy_combo.currentText()
        with open('enemy_data.json', 'r') as data_file:
            enemy_data = json.load(data_file)

        enemy_data.pop(enemy_name, None)

        with open('enemy_data.json', 'w') as data_file:
            json.dump(enemy_data, data_file)

        self.update_enemy_tables()

    def update_enemy_combos(self):
        self.ui.edit_enemy_combo.clear()
        self.ui.edit_enemy_combo.addItem("New Enemy")
        self.ui.edit_enemy_combo.addItems(get_enemy_list())

        self.ui.enemy_select_combo.clear()
        self.ui.enemy_select_combo.addItems(get_enemy_list())

    def save_weapon(self):
        original = get_weapon_data()
        custom = get_custom_weapon_data()

        # check if it is new weapon
        if self.ui.edit_weapon_combo.currentText() == 'New Weapon':
            wepname = self.ui.new_weapon_text.toPlainText()
            fmname = self.ui.new_fire_mode_text.toPlainText()
            weapontype = self.ui.edit_weapon_type_combo.currentText()

            custom[wepname] = {}
            custom[wepname]["Fire Modes"] = {}
            custom[wepname]["Fire Modes"][fmname] = {}
            custom[wepname]["Fire Modes"][fmname]['productCategory'] = weapontype
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"] = {}

            if weapontype == 'Melee':
                custom[wepname]["Fire Modes"][fmname]['type'] = self.ui.edit_weapon_category_combo.currentText()

            # dpshot = [ text_config_to_double( convert_widget_item_to_string( self.ui.edit_weapon_damage_type_table.item(f,0) ) ) for f in range(15) ]
            dpshot = [ text_config_to_double( f.toPlainText() ) for f in self.elemental_edit_textboxes ]
            for i in range(20-15):
                dpshot.append(0)

            custom[wepname]["Fire Modes"][fmname]["damagePerShot"] = dpshot

            custom[wepname]["Fire Modes"][fmname]["criticalChance"] = text_config_to_double( self.ui.critical_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["criticalMultiplier"] = text_config_to_double( self.ui.critical_damage_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["multishot"] = text_config_to_double( self.ui.pellet_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["procChance"] = text_config_to_double( self.ui.status_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["fireRate"] = text_config_to_double( self.ui.fire_rate_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["reloadTime"] = text_config_to_double( self.ui.reload_speed_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["chargeTime"] = text_config_to_double( self.ui.charge_time_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["embedDelay"] = text_config_to_double( self.ui.embed_delay_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["magazineSize"] = max( text_config_to_double( self.ui.magazine_edit_textbox.toPlainText() ) , 1 )
            custom[wepname]["Fire Modes"][fmname]["ammo"] = text_config_to_double( self.ui.ammo_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["ammoCost"] = text_config_to_double( self.ui.ammo_cost_edit_textbox.toPlainText() )

        # check if new fire mode for existing Weapon
        elif self.ui.edit_fire_mode_combo.currentText() == 'New Fire Mode':
            wepname = self.ui.edit_weapon_combo.currentText()
            fmname = self.ui.new_fire_mode_text.toPlainText()

            custom[wepname]["Fire Modes"][fmname] = {}
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"] = {}

            # custom[wepname]["Fire Modes"][fmname]["damagePerShot"] = [ text_config_to_double( convert_widget_item_to_string( self.ui.edit_weapon_damage_type_table.item(f,0) ) ) for f in range(15) ]
            custom[wepname]["Fire Modes"][fmname]["damagePerShot"] = [ text_config_to_double( f.toPlainText() ) for f in self.elemental_edit_textboxes ]
            for i in range(20-15):
                custom[wepname]["Fire Modes"][fmname]["damagePerShot"].append(0)

            custom[wepname]["Fire Modes"][fmname]["criticalChance"] = text_config_to_double( self.ui.critical_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["criticalMultiplier"] = text_config_to_double( self.ui.critical_damage_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["multishot"] = text_config_to_double( self.ui.pellet_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["procChance"] = text_config_to_double( self.ui.status_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["fireRate"] = text_config_to_double( self.ui.fire_rate_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["reloadTime"] = text_config_to_double( self.ui.reload_speed_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["chargeTime"] = text_config_to_double( self.ui.charge_time_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["embedDelay"] = text_config_to_double( self.ui.embed_delay_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["magazineSize"] = max( text_config_to_double( self.ui.magazine_edit_textbox.toPlainText() ) , 1 )
            custom[wepname]["Fire Modes"][fmname]["ammo"] = text_config_to_double( self.ui.ammo_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["ammoCost"] = text_config_to_double( self.ui.ammo_cost_edit_textbox.toPlainText() )

        # check if edit existing fire mode
        elif self.ui.edit_fire_mode_radio.isChecked():
            wepname = self.ui.edit_weapon_combo.currentText()
            fmname = self.ui.edit_fire_mode_combo.currentText()

            # custom[wepname]["Fire Modes"][fmname]["damagePerShot"] = [ text_config_to_double( convert_widget_item_to_string( self.ui.edit_weapon_damage_type_table.item(f,0) ) ) for f in range(15) ]
            custom[wepname]["Fire Modes"][fmname]["damagePerShot"] = [ text_config_to_double( f.toPlainText() ) for f in self.elemental_edit_textboxes ]
            for i in range(20-15):
                custom[wepname]["Fire Modes"][fmname]["damagePerShot"].append(0)

            custom[wepname]["Fire Modes"][fmname]["criticalChance"] = text_config_to_double( self.ui.critical_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["criticalMultiplier"] = text_config_to_double( self.ui.critical_damage_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["multishot"] = text_config_to_double( self.ui.pellet_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["procChance"] = text_config_to_double( self.ui.status_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["fireRate"] = text_config_to_double( self.ui.fire_rate_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["reloadTime"] = text_config_to_double( self.ui.reload_speed_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["chargeTime"] = text_config_to_double( self.ui.charge_time_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["embedDelay"] = text_config_to_double( self.ui.embed_delay_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["magazineSize"] = max( text_config_to_double( self.ui.magazine_edit_textbox.toPlainText() ) , 1 )
            custom[wepname]["Fire Modes"][fmname]["ammo"] = text_config_to_double( self.ui.ammo_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["ammoCost"] = text_config_to_double( self.ui.ammo_cost_edit_textbox.toPlainText() )

        # check if new secondary effect
        elif self.ui.edit_secondary_effect_combo.currentText() == 'New Secondary Effect':
            wepname = self.ui.edit_weapon_combo.currentText()
            fmname = self.ui.edit_fire_mode_combo.currentText()
            sename = self.ui.edit_secondary_effect_text.toPlainText()

            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename] = {}

            # custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["damagePerShot"] = [ text_config_to_double( convert_widget_item_to_string( self.ui.edit_weapon_damage_type_table.item(f,0) ) ) for f in range(15) ]
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["damagePerShot"] = [ text_config_to_double( f.toPlainText() ) for f in self.elemental_edit_textboxes ]
            for i in range(20-15):
                custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["damagePerShot"].append(0)

            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["criticalChance"] = text_config_to_double( self.ui.critical_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["criticalMultiplier"] = text_config_to_double( self.ui.critical_damage_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["multishot"] = text_config_to_double( self.ui.pellet_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["procChance"] = text_config_to_double( self.ui.status_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["fireRate"] = text_config_to_double( self.ui.fire_rate_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["reloadTime"] = text_config_to_double( self.ui.reload_speed_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["chargeTime"] = text_config_to_double( self.ui.charge_time_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["embedDelay"] = text_config_to_double( self.ui.embed_delay_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["magazineSize"] = max( text_config_to_double( self.ui.magazine_edit_textbox.toPlainText() ) , 1 )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["ammo"] = text_config_to_double( self.ui.ammo_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["ammoCost"] = text_config_to_double( self.ui.ammo_cost_edit_textbox.toPlainText() )

        # last option is edit an existing secondary effect
        else:
            wepname = self.ui.edit_weapon_combo.currentText()
            fmname = self.ui.edit_fire_mode_combo.currentText()
            sename = self.ui.edit_secondary_effect_combo.currentText()

            # custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["damagePerShot"] = [ text_config_to_double( convert_widget_item_to_string( self.ui.edit_weapon_damage_type_table.item(f,0) ) ) for f in range(15) ]
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["damagePerShot"] = [ text_config_to_double( f.toPlainText() ) for f in self.elemental_edit_textboxes ]
            for i in range(20-15):
                custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["damagePerShot"].append(0)

            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["criticalChance"] = text_config_to_double( self.ui.critical_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["criticalMultiplier"] = text_config_to_double( self.ui.critical_damage_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["multishot"] = text_config_to_double( self.ui.pellet_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["procChance"] = text_config_to_double( self.ui.status_chance_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["fireRate"] = text_config_to_double( self.ui.fire_rate_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["reloadTime"] = text_config_to_double( self.ui.reload_speed_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["chargeTime"] = text_config_to_double( self.ui.charge_time_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["embedDelay"] = text_config_to_double( self.ui.embed_delay_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["magazineSize"] = max( text_config_to_double( self.ui.magazine_edit_textbox.toPlainText() ) , 1 )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["ammo"] = text_config_to_double( self.ui.ammo_edit_textbox.toPlainText() )
            custom[wepname]["Fire Modes"][fmname]["Secondary Effects"][sename]["ammoCost"] = text_config_to_double( self.ui.ammo_cost_edit_textbox.toPlainText() )

        # save weapon to custom file
        with open('custom_weapon_data.json', 'w') as f:
            json.dump(custom, f)

        # update main weapon file
        for key, value in custom.items():
            original[key] = value
        with open('weapon_data.json', 'w') as f:
            json.dump(original, f)

        self.update_weapon_combos()

    def delete_component(self):
        wepname = self.ui.edit_weapon_combo.currentText()
        fmname = self.ui.edit_fire_mode_combo.currentText()
        if fmname != 'New Fire Mode':
            original = get_weapon_data()
            custom = get_custom_weapon_data()

            # check if want to delete fire mode
            if self.ui.edit_fire_mode_radio.isChecked():
                custom[wepname]['Fire Modes'].pop(fmname, None)
                original[wepname]['Fire Modes'].pop(fmname, None)
            # remove sec effect
            else:
                sename = self.ui.edit_secondary_effect_combo.currentText()
                custom[wepname]['Fire Modes'][fmname]['Secondary Effects'].pop(sename, None)
                original[wepname]['Fire Modes'][fmname]['Secondary Effects'].pop(sename, None)

            with open('custom_weapon_data.json', 'w') as f:
                json.dump(custom, f)
            with open('weapon_data.json', 'w') as f:
                json.dump(original, f)

            self.update_weapon_combos()

    def delete_weapon(self):
        wepname = self.ui.edit_weapon_combo.currentText()
        if wepname != 'New Weapon':
            original = get_weapon_data()
            custom = get_custom_weapon_data()

            custom.pop(wepname, None)
            original.pop(wepname, None)

            with open('custom_weapon_data.json', 'w') as f:
                json.dump(custom, f)
            with open('weapon_data.json', 'w') as f:
                json.dump(original, f)

            self.update_weapon_combos()

    def update_weapon_combos(self):
        self.ui.custom_build_weapon_combo.clear()
        self.ui.custom_build_weapon_combo.addItems(get_weapon_list())

        self.ui.edit_weapon_combo.clear()
        self.ui.edit_weapon_combo.addItem("New Weapon")
        self.ui.edit_weapon_combo.addItems(get_weapon_list())

    def save_build(self):
        build_data = get_build_data()

        config_name = self.ui.custom_build_save_text.toPlainText()
        wepname = self.ui.custom_build_weapon_combo.currentText()
        fmname = self.ui.custom_build_fire_mode_combo.currentText()
        stance = self.ui.custom_build_stance_combo.currentText()
        moveset = self.ui.custom_build_stance_moveset_combo.currentText()

        build_data[config_name] = {}
        build_data[config_name]["Weapon Name"] = wepname
        build_data[config_name]["Fire Mode"] = fmname
        build_data[config_name]["Stance"] = stance
        build_data[config_name]["Moveset"] = moveset

        build_data[config_name]["Damage Mods"] = self.ui.base_damage_mod_textbox.toPlainText()
        build_data[config_name]["Multishot Mods"] = self.ui.multishot_mod_textbox.toPlainText()
        build_data[config_name]["Critical Chance Mods"] = self.ui.critical_chance_mod_textbox.toPlainText()
        build_data[config_name]["Critical Damage Mods"] = self.ui.critical_damage_mod_textbox.toPlainText()
        build_data[config_name]["Bane Mods"] = self.ui.faction_mod_textbox.toPlainText()
        build_data[config_name]["Multiplier Mods"] = self.ui.damage_multiplier_mod_textbox.toPlainText()
        build_data[config_name]["Fire Rate Mods"] = self.ui.fire_rate_mod_textbox.toPlainText()

        build_data[config_name]["Status Chance Mods"] = self.ui.status_chance_mod_textbox.toPlainText()
        build_data[config_name]["Status Duration Mods"] = self.ui.status_duration_mod_textbox.toPlainText()

        build_data[config_name]["Heat Mods"] = self.ui.heat_mod_textbox.toPlainText()
        build_data[config_name]["Cold Mods"] = self.ui.cold_mod_textbox.toPlainText()
        build_data[config_name]["Electric Mods"] = self.ui.electric_mod_textbox.toPlainText()
        build_data[config_name]["Toxin Mods"] = self.ui.toxin_mod_textbox.toPlainText()

        build_data[config_name]["Impact Mods"] = self.ui.impact_mod_textbox.toPlainText()
        build_data[config_name]["Puncture Mods"] = self.ui.puncture_mod_textbox.toPlainText()
        build_data[config_name]["Slash Mods"] = self.ui.slash_mod_textbox.toPlainText()

        build_data[config_name]["Reload Mods"] = self.ui.reload_speed_mod_textbox.toPlainText()
        build_data[config_name]["Magazine Mods"] = self.ui.magazine_mod_textbox.toPlainText()
        build_data[config_name]["Ammo Mods"] = self.ui.ammo_maximum_mod_textbox.toPlainText()

        build_data[config_name]["Corrosive"] = self.ui.corrosive_check_box.isChecked()
        build_data[config_name]["Blast"] = self.ui.blast_check_box.isChecked()
        build_data[config_name]["Viral"] = self.ui.viral_check_box.isChecked()
        build_data[config_name]["Radiation"] = self.ui.radiation_check_box.isChecked()
        build_data[config_name]["Magnetic"] = self.ui.magnetic_check_box.isChecked()
        build_data[config_name]["Gas"] = self.ui.gas_check_box.isChecked()

        build_data[config_name]["Critical Enhance Mods"] = self.ui.critical_enhance_textbox.toPlainText()

        with open('build_data.json', 'w') as f:
            json.dump(build_data, f)

        self.ui.build_select_combo.clear()
        self.ui.build_select_combo.addItem("New Build")
        self.ui.build_select_combo.addItems(get_build_list())

    def load_build(self):
        build_data = get_build_data()
        build_name = self.ui.build_select_combo.currentText()
        lis =["Damage Mods","Multishot Mods","Critical Chance Mods","Critical Damage Mods","Fire Rate Mods",
        "Bane Mods","Status Chance Mods","Reload Mods","Heat Mods","Cold Mods","Electric Mods","Toxin Mods",
        "Impact Mods","Puncture Mods","Slash Mods","Multiplier Mods","Status Duration Mods","Ammo Mods","Magazine Mods"]

        if build_name != "New Build" and build_name != "":
            for bl in self.blockers:
                bl.reblock()

            self.ui.base_damage_mod_textbox.setPlainText( build_data[build_name]["Damage Mods"] )
            self.ui.multishot_mod_textbox.setPlainText( build_data[build_name]["Multishot Mods"] )
            self.ui.critical_chance_mod_textbox.setPlainText( build_data[build_name]["Critical Chance Mods"] )
            self.ui.critical_damage_mod_textbox.setPlainText( build_data[build_name]["Critical Damage Mods"] )
            self.ui.faction_mod_textbox.setPlainText( build_data[build_name]["Bane Mods"] )
            self.ui.damage_multiplier_mod_textbox.setPlainText( build_data[build_name]["Multiplier Mods"] )
            self.ui.fire_rate_mod_textbox.setPlainText( build_data[build_name]["Fire Rate Mods"] )

            self.ui.status_chance_mod_textbox.setPlainText( build_data[build_name]["Status Chance Mods"] )
            self.ui.status_duration_mod_textbox.setPlainText( build_data[build_name]["Status Duration Mods"] )

            self.ui.heat_mod_textbox.setPlainText( build_data[build_name]["Heat Mods"] )
            self.ui.cold_mod_textbox.setPlainText( build_data[build_name]["Cold Mods"] )
            self.ui.electric_mod_textbox.setPlainText( build_data[build_name]["Electric Mods"] )
            self.ui.toxin_mod_textbox.setPlainText( build_data[build_name]["Toxin Mods"] )

            self.ui.impact_mod_textbox.setPlainText( build_data[build_name]["Impact Mods"] )
            self.ui.puncture_mod_textbox.setPlainText( build_data[build_name]["Puncture Mods"] )
            self.ui.slash_mod_textbox.setPlainText( build_data[build_name]["Slash Mods"] )

            self.ui.reload_speed_mod_textbox.setPlainText( build_data[build_name]["Reload Mods"] )
            self.ui.magazine_mod_textbox.setPlainText( build_data[build_name]["Magazine Mods"] )
            self.ui.ammo_maximum_mod_textbox.setPlainText( build_data[build_name]["Ammo Mods"] )

            self.ui.critical_enhance_textbox.setPlainText( build_data[build_name].get("Critical Enhance Mods", "") )

            ####

            self.set_check_box_state(build_data[build_name]["Corrosive"], self.ui.corrosive_check_box)
            self.set_check_box_state(build_data[build_name]["Blast"], self.ui.blast_check_box)
            self.set_check_box_state(build_data[build_name]["Viral"], self.ui.viral_check_box)
            self.set_check_box_state(build_data[build_name]["Radiation"], self.ui.radiation_check_box)
            self.set_check_box_state(build_data[build_name]["Magnetic"], self.ui.magnetic_check_box)
            self.set_check_box_state(build_data[build_name]["Gas"], self.ui.gas_check_box)

            self.ui.custom_build_weapon_combo.setCurrentIndex(self.ui.custom_build_weapon_combo.findText(build_data[build_name]["Weapon Name"]))
            self.ui.custom_build_fire_mode_combo.setCurrentIndex(self.ui.custom_build_fire_mode_combo.findText(build_data[build_name]["Fire Mode"]))
            self.ui.custom_build_stance_combo.setCurrentIndex(self.ui.custom_build_stance_combo.findText(build_data[build_name]["Stance"]))
            self.ui.custom_build_stance_moveset_combo.setCurrentIndex(self.ui.custom_build_stance_moveset_combo.findText(build_data[build_name]["Moveset"]))

            for bl in self.blockers:
                bl.unblock()
            self.update_display_build_table()

    def merge_weapon_data(self):
        original = get_weapon_data()
        custom = get_custom_weapon_data()

        # update main weapon file
        for key, value in custom.items():
            original[key] = value
        with open('weapon_data.json', 'w') as f:
            json.dump(original, f)

        self.update_weapon_combos()

    def set_check_box_state(self, state, checkbox):
        if state == True:
            if not checkbox.isChecked():
                checkbox.toggle()
        else:
            if checkbox.isChecked():
                checkbox.toggle()
    def apply_steel_path_conditions(self):
        if self.ui.steel_path_conditions_checkbox.isChecked():
            self.ui.SP_health_buff_spinner.setValue(2.50)
            self.ui.SP_shield_buff_spinner.setValue(2.50)
            self.ui.SP_armor_buff_spinner.setValue(2.50)
        else:
            self.ui.SP_health_buff_spinner.setValue(1.00)
            self.ui.SP_shield_buff_spinner.setValue(1.00)
            self.ui.SP_armor_buff_spinner.setValue(1.00)

def get_weapon_list():
    with open('./weapon_data.json') as f:
        weapon_data = json.load(f)
    return sorted(list(weapon_data.keys()))

def get_enemy_list():
    with open('enemy_data.json', 'r') as data_file:
        enemy_data = json.load(data_file)
    return sorted(list(enemy_data.keys()))

def get_fire_mode_list(weapon_name):
    weapon_data = get_weapon_data()
    return list(weapon_data[weapon_name]["Fire Modes"].keys())

def get_build_list():
    build_data = get_build_data()
    return list(build_data.keys())

def get_secondary_effects(weapon_name, fire_mode_name):
    weapon_data = get_weapon_data()
    return list(weapon_data[weapon_name]["Fire Modes"][fire_mode_name]["Secondary Effects"].keys())

def get_weapon_data():
    with open('./weapon_data.json') as f:
        return json.load(f)

def get_stance_data():
    with open('./stance_data.json') as f:
        return json.load(f)

def get_custom_weapon_data():
    with open('./custom_weapon_data.json') as f:
        return json.load(f)

def get_build_data():
    with open('./build_data.json') as f:
        return json.load(f)

def get_enemy_data():
    with open('./enemy_data.json') as f:
        return json.load(f)

def text_config_to_double(txt):
    vals = txt.split(" ")
    tot = 0
    for elem in vals:
        elem.replace("$","")
        elem = elem.split("*")
        if len(elem)>1:
            res = 1
            for multiplicand in elem:
                if isfloat(multiplicand):
                    res *= multiplicand
        else:
            res = elem[0]
        if res == '': res = '0'
        tot += float(res)
    return tot

def convert_widget_item_to_string(itm):
    if itm:
        return itm.text()
    else:
        return ''

def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def get_mean( x, y, points=10 ):
    if points <=0:
        points = 1
    mean_x = np.linspace(start=max(x)/points, stop=max(x), num=points)
    mean_x = mean_x.tolist()
    #mean_x = range(resolution, max(x), resolution)
    mean_y = [0]*points
    prev_elem = 0
    last_mean =0
    for i, range_elem in enumerate(mean_x):
        count = 0
        for j, elem in enumerate(x):
            if elem<=range_elem and elem>prev_elem:
                mean_y[i] += y[j]

                count += 1
        if count>0:
            mean_y[i] /= count
            last_mean = mean_y[i]
        else:
            mean_y[i] = last_mean
        prev_elem = range_elem

    return mean_x, mean_y

def power_fit(x, a, b, c):
    return -a*np.power(x,b)+c

def poly_fit(x,a,b,c):
    return a*np.power(x,2)+b*x+c

def get_type_name(index):
    if index == 0:
        return "Impact"
    elif index == 1:
        return   "Puncture"
    elif index == 2:
        return   "Slash"
    elif index == 3:
        return   "Heat"
    elif index == 4:
        return   "Cold"
    elif index == 5:
        return   "Electric"
    elif index == 6:
        return   "Toxin"
    elif index == 7:
        return   "Blast"
    elif index == 8:
        return   "Radiation"
    elif index == 9:
        return   "Gas"
    elif index == 10:
        return  "Magnetic"
    elif index == 11:
        return  "Viral"
    elif index == 12:
        return  "Corrosive"
    elif index == 13:
        return  "Void"
    else:
        return  ""
if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")

    widget = Window()
    widget.show()

    app.setPalette(widget.get_dark_palette())
    sys.exit(app.exec())
