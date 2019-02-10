# -*- coding: cp1250 -*-
import sdSoilEditor
import sdSoil
from dnBaseLib import *
import os
import copy

# design modules
import dnConstants
import dnComponent
import dnComponentDlg
from dnFoundationPilesLib import *

# soldis
import sdConstants
import sdRTFReport

import soTranslator
import PyRTF
from Tkinter import *
from pprint import pprint


def trans(exp):
    import dnFoundationPiles_EN
    return soTranslator.trans(exp, {
        soConstants.ENGLISH: dnFoundationPiles_EN.data,
    })


# CONSTANTS


# HERE DEFINE DESIGN SUBJECTS
EXTREMAL_VERTICAL_RATIO = trans(u'Pojedyńczy pal na siłę pionową')
EXTREMAL_VERTICAL_GROUP_RATIO = trans(u'Grupa pali na siłę pionową')
EXTREMAL_NEGATIVE_FRICTION_RATIO = trans(u'Tarcie negatywne z gruntem współpracującym')
EXTREMAL_HORIZONTAL_DIS_RATIO = trans(u'Przemieszenie poziome pali')
EXTREMAL_ROTATION_DIS_RATIO = trans(u'Obrót pali')
EXTREMAL_CONSTRUCTION_DIS_RATIO = trans(u'Przemieszczenie konstrukcji')
EXTREMAL_SIDE_PRESSURE_RATIO = trans(u'Boczny docisk gruntu')
EXTREMAL_COMPACTION_RATIO = trans(u'Osiadanie pali')
EXTREMAL_PILE_REINFORCEMENT_RATIO = trans(u'Zbrojenie pala')
EXTREMAL_SLAB_REINFORCEMENT_RATIO = trans(u'Zbrojenie oczepu')


# this are some helpful functions too
def merge_dict(x, y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z


def find_extremum(comb_data_list, force):
    _min_data, _max_data = None, None
    for comb_data in comb_data_list:
        if _min_data is None or comb_data['section_forces'][force] < _min_data['section_forces'][force]:
            _min_data = comb_data
        if _max_data is None or comb_data['section_forces'][force] > _max_data['section_forces'][force]:
            _max_data = comb_data
    return _min_data, _max_data


def results_dict(data):
    results = {}
    results['comb_name'] = data['name']
    comb_data = {}
    comb_data['section_forces'] = {'Ned': data['section_forces']['N'],
                                   'Ved': data['section_forces']['Tz'],
                                   'Med': data['section_forces']['My']}
    results['load_groups'] = data['load_groups']
    results['comb_data'] = comb_data
    return results


def _max_comb_condition(results, condition):
    max = None
    data_comb = None
    for data in results:
        ratio = results[data][1]['ratio'][condition]
        if ratio >= max:
            max = ratio
            data_comb = results[data][0]['data']
    return {'data': data_comb, 'ratio': max}


# this is your main dlg class
class FoundationPilesDlg(dnComponentDlg.ComponentContextNodeDlg):
    controlWidth = 12

    def __init__(self, parent, compObj, **kw):

        # init base class
        dnComponentDlg.ComponentContextNodeDlg.__init__(self, parent, compObj, **kw)

        # register tabs
        # to register tab you need to provide its create and update functions
        self.registerTab('results_joint',
                         image=self._createImage('detailed_results_icon.png'),
                         disableImage=self._createImage('detailed_results_icon_disabled.png'),
                         createFunc=self.createTab_results,
                         updateFun=self.updateTab_results,
                         subjectId=1)

        # permanent panel will be always visible on the right side of window
        self.registerPermamentPanel(createFun=self.createPermamentPanel, updateFun=self.updatePermamentPanel)

        # some additional buttons
        self.registerCalcSavingOptButton()
        self.registerRaportGeneratorButton()

        # set your only tab as the default one
        self.setDefaultTab('results_joint')

        # this builds the window according to tabs you registered
        self.build()

    def setVars(self):
        # all you add here must be defined in Component.setDefault function, this vars are accesible in both
        # component and dlg
        # these can be for example steel f_u, that you want to be passed by user and that will be used for your component

        self.addVar('load_N_Q_c', type='DoubleVar')  # sila normalna
        self.addVar('load_V_Q_c', type='DoubleVar')  # sila tnaca
        self.addVar('load_M_Q_c', type='DoubleVar')  # moment
        self.addVar('additional_load', type='IntVar')  # additional_load_checkbox
        self.addVar('D', type='DoubleVar')  # srednica pala
        self.addVar('D_f', type='DoubleVar')  # srednica pala
        self.addVar('n_r', type='IntVar')  # liczba pali w rzedzie
        self.addVar('n_s', type='IntVar')  # liczba pali w szeregu
        self.addVar('r', type='DoubleVar')  # rozstaw pali
        self.addVar('L', type='DoubleVar')  # dlugosc pala
        self.addVar('H_f', type='DoubleVar')  # wysokosc plyty fundamentowej
        self.addVar('h_grunt', type='DoubleVar')  # wysokosc gruntu nad fundamentem
        self.addVar('r_kr', type='DoubleVar')  # odleglosc pala od oczepu
        self.addVar('first_bearing_soil', type='IntVar')  # pierwszy nosny grunt
        self.addVar('first_bearing_soil_text', type='StringVar')
        self.addVar('soil_profile', type='IntVar')  # profil gruntu
        self.addVar('soil_profile_text', type='StringVar')
        self.addVar('r_phi', type='IntVar')  # srednica zbrojenia
        self.addVar('r_phi_text', type='StringVar')
        self.addVar('r_phi_s', type='IntVar')  # srednica zbrojenia
        self.addVar('r_phi_s_text', type='StringVar')
        self.addVar('c', type='IntVar')  # otulina
        self.addVar('reinf_n', type='IntVar')  # liczba pretow
        self.addVar('B_stem', type='DoubleVar')  # szerokosc trzonu
        self.addVar('L_stem', type='DoubleVar')  # dlugosc trzonu
        self.addVar('d_stem', type='DoubleVar')  # grubosc scian trzonu
        self.addVar('h_constr', type='DoubleVar')  # wysokość kontrukcji nad ziemią
        self.addVar('concrete', type='StringVar')  # klasa betonu
        self.addVar('formwork_boolean', type='IntVar')  # dodatkowe deskowanie
        self.addVar('phi_slab_x', type='IntVar') # średnica prętów oczepu po kierunku x
        self.addVar('phi_slab_y', type='IntVar') # średnica prętów oczepu po kierunku y
        self.addVar('slab_spacing_x', type='IntVar') # rozstaw prętów oczepu po kierunku x
        self.addVar('slab_spacing_y',type='IntVar')  # rozstaw prętów oczepu po kierunku y

    # this is some helpful function ;)
    def find_the_worst(self, res_data):
        max_ratio = 0.
        max_ratio_data = None

        for comb_name, comb_data in res_data.items():
            r = comb_data['ratio']
            if r >= max_ratio:
                max_ratio = r
                max_ratio_data = comb_data

        return max_ratio_data

    def soil_manager_popup(self):
        pm = self.getCompObj().getModelManager().getSoilProfileManager()
        manager = sdSoilEditor.SoilEditorDlg(self, pm, self.getCompObj().standardType)

        def ok():
            ## update
            self.updateTab_results()
            self.getCompObj().doCustomCheck()
            try:
                print "-->On OK"
                self.getCompObj().doBeforeCalculate()
                self.getCompObj().doCalculate()
            except:
                print "error w ok()"
            self.updateTab_results()
            self.updatePermamentPanel()

            return True

        manager.onOk = ok
        manager.show()
        return

    def update_bearing_soil_box(self):
        try:
            print "update_bearing_list"
            self.soils_list_box = get_soils_names(self.getCompObj(), self.var_soil_profile.get())
            self.bearing_soil_box['values'] = self.soils_list_box
            if self.var_first_bearing_soil.get() > (len(self.soils_list_box) - 1):
                self.var_first_bearing_soil.set(0)
                self.bearing_soil_box.set(self.soils_list_box[0])
        except:
            print "error update_bearing_soil_box()"

    def update_profiles_list(self):
        try:
            print "update_profiles_list"
            self.profiles_list = get_profiles_list(self.getCompObj())
            self.profiles_box['values'] = self.profiles_list
            if self.var_soil_profile.get() > len(self.profiles_list):
                self.var_soil_profile.set(1)
                self.profiles_box.set(self.profiles_list[1])
        except:
            print "error w update_profiles_list()"

    def test(self):
        print "--------------------------------------"
        for layer in self.getCompObj().getModelManager().getSoilProfileManager().getSoilProfiles()[1].getLayers():
        #     print layer.getHeight()
        #     print layer.getSoil().getName()
            print layer.getSoil().params
        #     print layer.getSoil().getColour()
        #     print layer.getSoil().isCohesive()
        #     print layer.saturation

    # create side panel
    def createPermamentPanel(self, parent):

        # main frame to hold all content of panel
        joint_frame = soFrame(parent)
        joint_frame.pack()

        # region canvas
        # the notebook is a little frame with tabs you can register
        canvas_notebook = soNoteBook(joint_frame)
        canvas_notebook.grid(row=1, column=1, sticky=S + N + W + E, padx=2, pady=0)
        # 1 frame
        canvas_scheme_1_tab = soFrame(canvas_notebook)
        canvas_notebook.add(canvas_scheme_1_tab, text=trans(u'Przekrój'))
        # 2 frame
        canvas_scheme_2_tab = soFrame(canvas_notebook)
        canvas_notebook.add(canvas_scheme_2_tab, text=trans(u'Rzut'))
        # 3 frame
        canvas_scheme_3_tab = soFrame(canvas_notebook)
        canvas_notebook.add(canvas_scheme_3_tab, text=trans(u'Widok1'))
        # 4 frame
        canvas_scheme_4_tab = soFrame(canvas_notebook)
        canvas_notebook.add(canvas_scheme_4_tab, text=trans(u'Widok2'))

        # you need to create canvas for each tab, even though only one is visible at a time
        self.cC1_size = 207, 207
        self.cC3_size = 207, 500
        self.cC1 = soMetricCanvas(canvas_scheme_1_tab, width=self.cC1_size[0], height=self.cC1_size[1], bg='sienna4',
                                  bd=2,
                                  relief=GROOVE)
        self.cC1.grid(row=1, column=1, sticky=S + N + W + E, padx=1, pady=1)
        self.cC2 = soMetricCanvas(canvas_scheme_2_tab, width=self.cC1_size[0], height=self.cC1_size[1], bg='sienna4',
                                  bd=2,
                                  relief=GROOVE)
        self.cC2.grid(row=1, column=1, sticky=S + N + W + E, padx=1, pady=1)
        self.cC3 = soMetricCanvas(canvas_scheme_3_tab, width=self.cC3_size[0], height=self.cC3_size[1], bg='sienna4',
                                  bd=2,
                                  relief=GROOVE)
        self.cC3.grid(row=1, column=1, sticky=S + N + W + E, padx=1, pady=1)
        self.cC4 = soMetricCanvas(canvas_scheme_4_tab, width=self.cC3_size[0], height=self.cC3_size[1], bg='sienna4',
                                  bd=2,
                                  relief=GROOVE)
        self.cC4.grid(row=1, column=1, sticky=S + N + W + E, padx=1, pady=1)
        # endregion
        # region parameters
        parameters_notebook = soFrame(joint_frame)
        parameters_notebook.grid(row=2, column=1, sticky=S + N + W + E, padx=2, pady=0)
        # endregion


        self.addUpdatePermanentPanelFunctions([
            # add update functions for permanent panel here
        ])

    # create main tab
    def createTab_results(self, tab):
        # use this to keep padding consistent
        tab_opts = {"padx": 5, "pady": 2, "sticky": NSEW}
        frame_opts = {"padx": 0, "pady": 0, "sticky": NSEW}

        # create some frames

        main_frame = soFrame(tab)
        main_frame.grid(row=0, column=0, **frame_opts)
        minor_frame = soFrame(main_frame)
        minor_frame.grid(row=0, column=0, **frame_opts)
        input_tab_frame = soFrame(minor_frame)
        input_tab_frame.grid(row=2, column=0, **frame_opts)

        extremal_load_comb_frame = soLabelFrame(minor_frame, text=trans(u'Najbardziej niekorzystna kombinacja obciążeń'))
        extremal_load_comb_frame.grid(row=0, column=0, **frame_opts)

        additional_load_frame = soLabelFrame(minor_frame, text=trans(u'Dodatkowe obciążenie zmienne'))
        additional_load_frame.grid(row=1, column=0, **frame_opts)

        piles_tab_frame = soFrame(input_tab_frame)
        piles_tab_frame.grid(row=0, column=0, **frame_opts)

        reinforcement_tab_frame = soLabelFrame(input_tab_frame, text=trans(u'Zbrojenie'))
        reinforcement_tab_frame.grid(row=0, column=2, **frame_opts)

        slab_tab_frame = soLabelFrame(input_tab_frame, text=trans(u'Geometria oczepu [m]'))
        slab_tab_frame.grid(row=0, column=1, **frame_opts)

        soils_tab_frame = soLabelFrame(main_frame, text=trans(u'Grunty'))
        soils_tab_frame.grid(row=0, column=1, **frame_opts)


        self.extremal_load_comb_N_frame = soFrame(extremal_load_comb_frame)
        self.extremal_load_comb_N_frame.grid(row=0, column=0, **frame_opts)
        self.extremal_load_comb_N = dnComponentDlg.ResultValue(self.extremal_load_comb_N_frame,
                                                               lImage=self._createImage('load_N'),
                                                               rImage=self._createImage('unit_kN'), format='%3.1f')
        self.extremal_load_comb_N.pack(padx=2, pady=0)

        self.extremal_load_comb_V_frame = soFrame(extremal_load_comb_frame)
        self.extremal_load_comb_V_frame.grid(row=0, column=1, **frame_opts)
        self.extremal_load_comb_V = dnComponentDlg.ResultValue(self.extremal_load_comb_V_frame,
                                                               lImage=self._createImage('load_V'),
                                                               rImage=self._createImage('unit_kN'), format='%3.1f')
        self.extremal_load_comb_V.pack(padx=2, pady=0)

        self.extremal_load_comb_M_frame = soFrame(extremal_load_comb_frame)
        self.extremal_load_comb_M_frame.grid(row=0, column=2, **frame_opts)
        self.extremal_load_comb_M = dnComponentDlg.ResultValue(self.extremal_load_comb_M_frame,
                                                               lImage=self._createImage('load_M'),
                                                               rImage=self._createImage('unit_kNm'), format='%3.1f')
        self.extremal_load_comb_M.pack(padx=2, pady=0)

        self.change_extremal_load_comb_checkbutton = soButton(extremal_load_comb_frame,
                                                              image=self._createImage('soldis_load.png'))
        self.change_extremal_load_comb_checkbutton.grid(row=0, column=4, padx=0, pady=0, sticky=E)

        def min_max_N_validate(x):
            try:
                x = float(x)
            except:
                return self.var_load_N.get()
            if x < -99999.:
                x = -99999.
            if x > 99999.:
                x = 99999.
            return x

        self.enter_N_frame = soFrame(additional_load_frame)
        self.enter_N_frame.grid(row=0, column=0, **frame_opts)
        self.enter_N_control = soControl(self.enter_N_frame,
                                         image=self._createImage('N_Qc'),
                                         variable=self.var_load_N_Q_c,
                                         step=1.,
                                         allowempty=False,
                                         validatecmd=min_max_N_validate,
                                         selectmode='normal',
                                         width=8,
                                         state=DISABLED)
        self.enter_N_control.pack(padx=2, pady=0, side=RIGHT)

        def min_max_V_validate(x):
            try:
                x = float(x)
            except:
                return self.var_load_V.get()
            if x < -99999.:
                x = -99999.
            if x > 99999.:
                x = 99999.
            return x

        self.enter_V_frame = soFrame(additional_load_frame)
        self.enter_V_frame.grid(row=0, column=1, **frame_opts)
        self.enter_V_control = soControl(self.enter_V_frame,
                                         image=self._createImage('V_Qc'),
                                         variable=self.var_load_V_Q_c,
                                         step=1.,
                                         allowempty=False,
                                         validatecmd=min_max_V_validate,
                                         selectmode='normal',
                                         width=8,
                                         state=DISABLED)
        self.enter_V_control.pack(padx=2, pady=0, side=RIGHT)

        def min_max_M_validate(x):
            try:
                x = float(x)
            except:
                return self.var_load_M.get()
            if x < -99999.:
                x = -99999.
            if x > 99999.:
                x = 99999.
            return x

        self.enter_M_frame = soFrame(additional_load_frame)
        self.enter_M_frame.grid(row=0, column=2, **frame_opts)
        self.enter_M_control = soControl(self.enter_M_frame,
                                         image=self._createImage('M_Qc'),
                                         variable=self.var_load_M_Q_c,
                                         step=1.,
                                         allowempty=False,
                                         validatecmd=min_max_M_validate,
                                         selectmode='normal',
                                         width=8,
                                         state=DISABLED)
        self.enter_M_control.pack(padx=2, pady=0, side=RIGHT)

        #
        def on_check_additional_load():
            if self.var_additional_load.get():
                self.enter_N_control['state'] = NORMAL
                self.enter_V_control['state'] = NORMAL
                self.enter_M_control['state'] = NORMAL
            else:
                self.enter_N_control['state'] = DISABLED
                self.enter_V_control['state'] = DISABLED
                self.enter_M_control['state'] = DISABLED

        self.additional_load_checkbutton = soCheckbutton(additional_load_frame,
                                                         image=self._createImage('pencil.png'),
                                                         variable=self.var_additional_load,
                                                         command=on_check_additional_load)
        self.additional_load_checkbutton.grid(row=0, column=4, padx=0, pady=0, sticky=E)

        # def getLoadGroups():
        #     rObj = self.getCompObj().getResults().getResult('summary_results')
        #     if rObj['extremal_load_group_USL']:
        #         return rObj['extremal_load_group_USL']
        #     else:
        #         return None
        #
        # extremal_combLoadGroups = self.insertCombLoadGroupsInfo(extremal_load_comb_frame,
        #                                                         getLoadGroupsFun=getLoadGroups)
        # extremal_combLoadGroups.grid(row=1, column=4, padx=0, sticky=W)
        #
        for i in range(3):
            extremal_load_comb_frame.columnconfigure(i, minsize=140)
            additional_load_frame.columnconfigure(i, minsize=140)

        self.addUpdateTabFunctions('results_joint', updateFunc=[ ])
        # you can do it automatically, like so:
        widgets = [
            # next widget #
            {"type": soButton,
             "frame": soils_tab_frame,
             "options": {"text": trans(u"Grunty"), "command": self.soil_manager_popup},
             "position": {"row": 0, "column": 0}},
            {"type": soButton,
             "frame": soils_tab_frame,
             "options": {"text": trans(u"-"), "command": self.test},
             "position": {"row": 1, "column": 0}}
        ]

        # just copy this loop and widgets to use throughout, you can just fill the data in widgets
        for widget in widgets:
            widget['type'](widget['frame'], **widget['options']).grid(**merge_dict(widget['position'], tab_opts))

        # or manually:

        def round_var(var):
            try:
                return int(var)
            except:
                return var

        # region input
        support1_frame = soFrame(piles_tab_frame)
        support1_frame.grid(row=0, column=0, **frame_opts)

        piles_frame = soLabelFrame(piles_tab_frame, text=trans(u'Geometria pala [m]'))
        piles_frame.grid(row=0, column=0, **frame_opts)

        def validate_D(var):
            if self.var_D_f.get() >= (var-0.1):
                self.var_D_f.set(var-0.1)
            return var

        self.D_control = soControl(piles_frame,
                                   image=self._createImage('D'),
                                   variable=self.var_D,
                                   step=0.1,
                                   round=1,
                                   max=1.8,
                                   min=0.4,
                                   showscale=False,
                                   selectmode='normal',
                                   width=6,
                                   allowempty=False,
                                   validatecmd = validate_D)

        self.D_control.grid(row=0, column=0, **tab_opts)

        self.L_control = soControl(piles_frame,
                                   image=self._createImage('L'),
                                   variable=self.var_L,
                                   step=0.05,
                                   round=2,
                                   max=100.,
                                   min=2.,
                                   showscale=False,
                                   selectmode='normal',
                                   width=6,
                                   allowempty=False)
        self.L_control.grid(row=0, column=1, **tab_opts)

        piles_quant_frame = soLabelFrame(piles_tab_frame, text=trans(u'Liczba pali:'))
        piles_quant_frame.grid(row=1, column=0, **frame_opts)
        support3_frame = soFrame(piles_quant_frame)
        support3_frame.pack()
        self.n_r_control = soControl(support3_frame,
                                     variable=self.var_n_r,
                                     step=1,
                                     max=10,
                                     min=2,
                                     validatecmd=round_var,
                                     showscale=False,
                                     selectmode='normal',
                                     width=6,
                                     allowempty=False)
        self.n_r_control.pack(side=LEFT)

        self.n_s_control = soControl(support3_frame,
                                     label="   x   ",
                                     variable=self.var_n_s,
                                     step=1,
                                     max=10,
                                     min=2,
                                     validatecmd=round_var,
                                     showscale=False,
                                     selectmode='normal',
                                     width=6,
                                     allowempty=False)
        self.n_s_control.pack(side=LEFT)

        stem_frame = soLabelFrame(piles_tab_frame, text=trans(u'Geometria trzonu [m]'))
        stem_frame.grid(row=2, column=0, **frame_opts)
        self.d_stem_control = soControl(stem_frame,
                                        image=self._createImage('d_s'),
                                        variable=self.var_d_stem,
                                        step=0.1,
                                        round=1,
                                        max=5.,
                                        min=0.,
                                        showscale=False,
                                        selectmode='normal',
                                        width=6,
                                        allowempty=False)
        self.d_stem_control.grid(row=0, column=0, **tab_opts)

        self.L_stem_control = soControl(stem_frame,
                                        image=self._createImage('L_s'),
                                        variable=self.var_L_stem,
                                        step=0.1,
                                        round=1,
                                        max=4.,
                                        min=0.3,
                                        showscale=False,
                                        selectmode='normal',
                                        width=6,
                                        allowempty=False)
        self.L_stem_control.grid(row=0, column=1, **tab_opts)

        self.B_stem_control = soControl(stem_frame,
                                        image=self._createImage('B_s'),
                                        variable=self.var_B_stem,
                                        step=0.1,
                                        round=1,
                                        max=4.,
                                        min=0.3,
                                        showscale=False,
                                        selectmode='normal',
                                        width=6,
                                        allowempty=False)
        self.B_stem_control.grid(row=1, column=0, **tab_opts)

        formwork_frame = soLabelFrame(piles_tab_frame, text=trans(u'Deskowanie w warstwie \u000dnienośnej? [m]'))
        formwork_frame.grid(row=3, column=0, **frame_opts)

        def on_formwork_change():
            if self.var_formwork_boolean.get():
                self.Df_control['state'] = 'normal'
            else:
                self.Df_control['state'] = DISABLED

        def validate_Df(var):
            if var >= (self.var_D.get()-0.1):
                var = self.var_D.get()-0.1
            return var

        self.Df_control = soControl(formwork_frame,
                                    image=self._createImage('D_f'),
                                    variable=self.var_D_f,
                                    step=0.1,
                                    round=1,
                                    max=1.7,
                                    min=0.2,
                                    state=DISABLED,
                                    showscale=False,
                                    selectmode='normal',
                                    width=6,
                                    allowempty=False,
                                    validatecmd = validate_Df)
        self.Df_control.grid(row=0, column=0, **tab_opts)

        self.formwork_checkbutton = soCheckbutton(formwork_frame,
                                                  variable=self.var_formwork_boolean,
                                                  command=on_formwork_change)
        self.formwork_checkbutton.grid(row=0, column=1, padx=0, pady=0, sticky=E)

        self.r_control = soControl(slab_tab_frame,
                                   image=self._createImage('r'),
                                   variable=self.var_r,
                                   step=0.1,
                                   round=1,
                                   max=5.,
                                   min=1.,
                                   showscale=False,
                                   selectmode='normal',
                                   width=6,
                                   allowempty=False)
        self.r_control.grid(row=2, column=0, padx=5, pady=5, sticky=E)

        self.H_f_control = soControl(slab_tab_frame,
                                     image=self._createImage('H_f'),
                                     variable=self.var_H_f,
                                     step=0.1,
                                     round=1,
                                     max=5.,
                                     min=0.8,
                                     showscale=False,
                                     selectmode='normal',
                                     width=6,
                                     allowempty=False)
        self.H_f_control.grid(row=0, column=0, padx=5, pady=5, sticky=E)

        self.h_grunt_control = soControl(slab_tab_frame,
                                         image=self._createImage('h_g'),
                                         variable=self.var_h_grunt,
                                         step=0.1,
                                         round=1,
                                         max=10.,
                                         min=0.,
                                         showscale=False,
                                         selectmode='normal',
                                         width=6,
                                         allowempty=False)
        self.h_grunt_control.grid(row=1, column=0, padx=5, pady=5, sticky=E)

        self.r_kr_control = soControl(slab_tab_frame,
                                      image=self._createImage('r_kr'),
                                      variable=self.var_r_kr,
                                      step=0.1,
                                      round=1,
                                      max=2.,
                                      min=0.2,
                                      showscale=False,
                                      selectmode='normal',
                                      width=6,
                                      allowempty=False)
        self.r_kr_control.grid(row=3, column=0, padx=5, pady=5, sticky=E)

        r_phi_list_box = ['6', '8', '10', '12', '14', '16', '20', '25', '28', '32', '40']

        def on_r_phi_change(i):
            try:
                self.var_r_phi.set(int(i))
            except:
                print "error in on_r_phi_change"

        reinf_frame_0 = soFrame(reinforcement_tab_frame)
        reinf_frame_0.pack(fill=X)

        def on_concrete_change(i):
            try:
                self.var_concrete.set(i)
            except:
                print "error in on_concrete_change"

        concrete_label = soLabel(reinf_frame_0, text=trans(u' Klasa betonu:'))
        concrete_label.grid(row=0, column=0, padx=0, pady=0, sticky=NSEW)
        self.concrete_box = dnComponentDlg.soComboBox(reinf_frame_0,
                                                      text='klasa',
                                                      state='readonly',
                                                      width=15, values=sorted(
                concrete_dict.keys()), textvariable=self.var_concrete)
        self.concrete_box.grid(row=1, column=0, padx=5, pady=5, sticky=NSEW)
        self.concrete_box.setOnSelectCommand(on_concrete_change)
        self.concrete_box.set(str(self.var_concrete.get()) or 'C30/37')

        reinf_frame_1 = soFrame(reinforcement_tab_frame)
        reinf_frame_1.pack(fill=X)

        pile_reinf_frame = soLabelFrame(reinf_frame_1, text=trans(u'Zbrojenie pala:'))
        pile_reinf_frame.grid(row=0, column=0, **frame_opts)


        r_phi_label = soLabel(pile_reinf_frame, text=trans(u' Pręty główne:'))
        r_phi_label.grid(row=0, column=0, padx=0, pady=0, sticky=NSEW)
        self.r_phi_box = dnComponentDlg.soComboBox(pile_reinf_frame,
                                                   text='r_phi',
                                                   state='readonly',
                                                   width=4,
                                                   values=r_phi_list_box,
                                                   textvariable=self.var_r_phi_text)
        self.r_phi_box.grid(row=1, column=0, **tab_opts)
        self.r_phi_box.setOnSelectCommand(on_r_phi_change)
        self.r_phi_box.set(str(self.var_r_phi.get()) or '12')

        reinf_n_label = soLabel(pile_reinf_frame, text=trans(u'  Liczba:'))
        reinf_n_label.grid(row=0, column=1, padx=0, pady=0, sticky=NSEW)
        self.reinf_n_control = soControl(pile_reinf_frame,
                                         label='',
                                         variable=self.var_reinf_n,
                                         step=1,
                                         max=30,
                                         min=4,
                                         validatecmd=round_var,
                                         showscale=False,
                                         selectmode='normal',
                                         width=4,
                                         allowempty=False)
        self.reinf_n_control.grid(row=1, column=1, **tab_opts)

        r_phi_s_list_box = ['6', '8', '10', '12', '14', '16', '20', '25']

        def on_r_phi_s_change(i):
            try:
                self.var_r_phi_s.set(int(i))
            except:
                print "error in on_r_phi_s_change"

        r_phi_s_label = soLabel(pile_reinf_frame, text=trans(u' Pręty spirali:'))
        r_phi_s_label.grid(row=2, column=0, padx=0, pady=0, sticky=NSEW)
        self.r_phi_s_box = dnComponentDlg.soComboBox(pile_reinf_frame,
                                                     text='r_phi_s',
                                                     state='readonly',
                                                     width=4,
                                                     values=r_phi_s_list_box,
                                                     textvariable=self.var_r_phi_s_text
                                                     )
        self.r_phi_s_box.grid(row=3, column=0, **tab_opts)
        self.r_phi_s_box.setOnSelectCommand(on_r_phi_s_change)
        self.r_phi_s_box.set(str(self.var_r_phi_s.get()) or '6')

        c_label = soLabel(pile_reinf_frame, text=trans(u'  Otulina:'))
        c_label.grid(row=2, column=1, padx=0, pady=0, sticky=NSEW)
        self.c_control = soControl(pile_reinf_frame,
                                   variable=self.var_c,
                                   step=1,
                                   max=70,
                                   min=5,
                                   validatecmd=round_var,
                                   showscale=False,
                                   selectmode='normal',
                                   width=4,
                                   allowempty=False)
        self.c_control.grid(row=3, column=1, **tab_opts)


        slab_reinf_frame = soLabelFrame(reinf_frame_1, text=trans(u'Zbrojenie oczepu:'))
        slab_reinf_frame.grid(row=1, column=0, **frame_opts)

        def on_phi_slab_x_change(i):
            try:
                self.var_phi_slab_x.set(int(i))
            except:
                print "error in on_phi_slab_x_change"


        phi_slab_x_label = soLabel(slab_reinf_frame, text=trans(u' Pręty po kier. X:'))
        phi_slab_x_label.grid(row=0, column=0, padx=0, pady=0, sticky=NSEW)
        self.phi_slab_x_box = dnComponentDlg.soComboBox(slab_reinf_frame,
                                                   text='phi_slab_x',
                                                   state='readonly',
                                                   width=4,
                                                   values=r_phi_list_box,
                                                   textvariable=self.var_r_phi_text)
        self.phi_slab_x_box.grid(row=1, column=0, **tab_opts)
        self.phi_slab_x_box.setOnSelectCommand(on_phi_slab_x_change)
        self.phi_slab_x_box.set(str(self.var_r_phi.get()) or '20')


        slab_spacing_x_label = soLabel(slab_reinf_frame, text=trans(u'  Rozstaw:'))
        slab_spacing_x_label.grid(row=0, column=1, padx=0, pady=0, sticky=NSEW)
        self.slab_spacing_x_control = soControl(slab_reinf_frame,
                                         variable=self.var_slab_spacing_x,
                                         step=1,
                                         max=25,
                                         min=5,
                                         validatecmd=round_var,
                                         showscale=False,
                                         selectmode='normal',
                                         width=4,
                                         allowempty=False)
        self.slab_spacing_x_control.grid(row=1, column=1, **tab_opts)


        def on_phi_slab_y_change(i):
            try:
                self.var_phi_slab_y.set(int(i))
            except:
                print "error in on_phi_slab_y_change"


        phi_slab_y_label = soLabel(slab_reinf_frame, text=trans(u' Pręty po kier. Y:'))
        phi_slab_y_label.grid(row=2, column=0, padx=0, pady=0, sticky=NSEW)
        self.phi_slab_y_box = dnComponentDlg.soComboBox(slab_reinf_frame,
                                                   text='phi_slab_y',
                                                   state='readonly',
                                                   width=4,
                                                   values=r_phi_list_box,
                                                   textvariable=self.var_r_phi_text)
        self.phi_slab_y_box.grid(row=3, column=0, **tab_opts)
        self.phi_slab_y_box.setOnSelectCommand(on_phi_slab_y_change)
        self.phi_slab_y_box.set(str(self.var_r_phi.get()) or '28')


        slab_spacing_y_label = soLabel(slab_reinf_frame, text=trans(u'  Rozstaw:'))
        slab_spacing_y_label.grid(row=2, column=1, padx=0, pady=0, sticky=NSEW)
        self.slab_spacing_y_control = soControl(slab_reinf_frame,
                                         variable=self.var_slab_spacing_y,
                                         step=1,
                                         max=25,
                                         min=5,
                                         validatecmd=round_var,
                                         showscale=False,
                                         selectmode='normal',
                                         width=4,
                                         allowempty=False)
        self.slab_spacing_y_control.grid(row=3, column=1, **tab_opts)

        def on_profiles_change(i=None):
            try:
                i = i or self.profiles_box.get()
                self.profiles_list = get_profiles_list(self.getCompObj())
                self.var_soil_profile.set(self.profiles_list.index(i) + 1)
            except:
                print "error w on_profile_change()"

        profiles_list = get_profiles_list(self.getCompObj())
        self.profiles_box = dnComponentDlg.soComboBox(soils_tab_frame,
                                                      state='readonly',
                                                      width=15,
                                                      values=profiles_list,
                                                      textvariable=self.var_soil_profile_text
                                                      )
        self.profiles_box.grid(row=2, column=0, **tab_opts)
        self.profiles_box.setOnSelectCommand(on_profiles_change)
        self.profiles_box.set(self.var_soil_profile_text.get() or profiles_list[0])

        def on_bearing_soil_change(i=None):
            try:
                i = i or self.bearing_soil_box.get()
                self.soils_list_box = get_soils_names(self.getCompObj(), self.var_soil_profile.get())
                self.var_first_bearing_soil.set(self.soils_list_box.index(i))
            except:
                print "error w on_bearing_soil_change"

        soil_names = get_soils_names(self.getCompObj(), self.var_soil_profile.get())
        self.bearing_soil_box = dnComponentDlg.soComboBox(soils_tab_frame,
                                                          state='readonly',
                                                          width=15,
                                                          # postcommand = self.update_bearing_soil_box(),
                                                          values=soil_names,
                                                          textvariable=self.var_first_bearing_soil_text,
                                                          )
        self.bearing_soil_box.grid(row=3, column=0, **tab_opts)
        self.bearing_soil_box.setOnSelectCommand(on_bearing_soil_change)
        try:
            self.bearing_soil_box.set(self.var_first_bearing_soil_text.get() or soil_names[0])
        except:
            print "nie ma gruntów"

        # self.h_constr_control = soControl(soils_tab_frame,
        #                                   label="h_constr = ",
        #                                   variable=self.var_h_constr,
        #                                   step=0.1,
        #                                   round=1,
        #                                   max=15.,
        #                                   min=0.,
        #                                   showscale=False,
        #                                   selectmode='normal',
        #                                   width=6,
        #                                   allowempty=False)
        # self.h_constr_control.grid(row=4, column=0, **tab_opts)


        results_notebook = soNoteBook(tab)
        results_notebook.grid(row=2, column=0, sticky=S + N + W + E, padx=2, pady=0)

        results_1_tab = soFrame(results_notebook)
        results_notebook.add(results_1_tab, text=trans(u'Pale'))
        results_3_tab = soFrame(results_notebook)
        results_notebook.add(results_3_tab, text=trans(u'Tarcie negatywne'))
        results_4_tab = soFrame(results_notebook)
        results_notebook.add(results_4_tab, text=trans(u'Stan użytkowania'))
        # results_5_tab = soFrame(results_notebook)
        # results_notebook.add(results_5_tab, text=trans(u'Obrót'))
        # results_6_tab = soFrame(results_notebook)
        # results_notebook.add(results_6_tab, text=trans(u'Przem. konstrukcji'))
        results_7_tab = soFrame(results_notebook)
        results_notebook.add(results_7_tab, text=trans(u'Boczny docisk'))
        results_8_tab = soFrame(results_notebook)
        results_notebook.add(results_8_tab, text=trans(u'Osiadanie pala'))
        results_9_tab = soFrame(results_notebook)
        results_notebook.add(results_9_tab, text=trans(u'Zbrojenie pala'))
        results_10_tab = soFrame(results_notebook)
        results_notebook.add(results_10_tab, text=trans(u'Zbrojenie oczepu'))

        # results_notebook.update()
        # print "results_notebook:       ",results_notebook.winfo_width(), " x ", results_notebook.winfo_height()
        # main_frame.update()
        # print "main_frame:       ",main_frame.winfo_width(), " x ", main_frame.winfo_height()
        # soils_tab_frame.update()
        # print "soils_tab_frame:       ", soils_tab_frame.winfo_width(), " x ", soils_tab_frame.winfo_height()
        # minor_frame.update()
        # print "minor_frame:       ", minor_frame.winfo_width(), " x ", minor_frame.winfo_height()

        vertical_comparison_frame = soLabelFrame(results_1_tab, text=trans(u'Pojedyńczy pal na wciskanie'))
        vertical_comparison_frame.grid(row=0, column=0, **frame_opts)
        self.vertical_comparison = dnComponentDlg.Comparison(vertical_comparison_frame,
                                                              lImage=self._createImage('f_c_d'),
                                                              rImage=self._createImage('r_c_d_cal'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.vertical_comparison.grid(row=0, column=0, **tab_opts)


        results_notebook.update()
        for child in results_notebook.winfo_children():
            child.columnconfigure(0, minsize=300)
            child.columnconfigure(1, minsize=300)
            child.rowconfigure(0, minsize=100)
            child.rowconfigure(1, minsize=100)


        vertical_group_comparison_frame = soLabelFrame(results_1_tab, text=trans(u'Grupa pali na wciskanie'),
                                                 height = 200)
        vertical_group_comparison_frame.grid(row=0, column=1, **frame_opts)
        self.vertical_group_comparison = dnComponentDlg.Comparison(vertical_group_comparison_frame,
                                                              lImage=self._createImage('f_c_d'),
                                                              rImage=self._createImage('r_c_d_GP'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.vertical_group_comparison.pack(fill=BOTH, anchor=CENTER, expand = True)


        negative_friction_comparison_frame = soLabelFrame(results_3_tab,text=trans(u'Tarcie ujemne'))
        negative_friction_comparison_frame.grid(row=0, column=0, **frame_opts)

        self.negative_friction_comparison = dnComponentDlg.Comparison(negative_friction_comparison_frame,
                                                              lImage=self._createImage('tn_k'),
                                                              rImage=self._createImage('q_Tn_k'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.negative_friction_comparison.grid(row=0, column=0, **tab_opts)

        disp_comparison_frame =soFrame(results_4_tab)
        disp_comparison_frame.grid(row=0, column=0, **frame_opts)
        horizontal_disp_comparison_frame = soLabelFrame(disp_comparison_frame,text=trans(u'Przemieszczenia poziome'))
        horizontal_disp_comparison_frame.grid(row=0, column=0, **frame_opts)

        self.horizontal_disp_comparison = dnComponentDlg.Comparison(horizontal_disp_comparison_frame,
                                                              lImage=self._createImage('y_0'),
                                                              rImage=self._createImage('y_0_dop'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.horizontal_disp_comparison.grid(row=0, column=0, **tab_opts)

        rotation_disp_comparison_frame = soLabelFrame(disp_comparison_frame,text=trans(u'Obrót pala'))
        rotation_disp_comparison_frame.grid(row=0, column=1, **frame_opts)

        self.rotation_disp_comparison = dnComponentDlg.Comparison(rotation_disp_comparison_frame,
                                                              lImage=self._createImage('phi_0'),
                                                              rImage=self._createImage('phi_0_dop'),
                                                              lFormat='%.4f',
                                                              rFormat='%.4f')
        self.rotation_disp_comparison.grid(row=0, column=0, **tab_opts)


        construction_disp_comparison_frame = soLabelFrame(disp_comparison_frame,text=trans(u'Przemieszczenia konstrukcji'))
        construction_disp_comparison_frame.grid(row=1, column=0, **frame_opts)

        self.construction_disp_comparison = dnComponentDlg.Comparison(construction_disp_comparison_frame,
                                                              lImage=self._createImage('y_kon'),
                                                              rImage=self._createImage('y_kon_dop'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.construction_disp_comparison.grid(row=0, column=0, **tab_opts)


        side_pressure_comparison_frame = soLabelFrame(results_7_tab,text=trans(u'Boczny docisk'))
        side_pressure_comparison_frame.grid(row=0, column=0, **frame_opts)

        self.side_pressure_comparison = dnComponentDlg.Comparison(side_pressure_comparison_frame,
                                                              lImage=self._createImage('p_z_d'),
                                                              rImage=self._createImage('r_z_d'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.side_pressure_comparison.grid(row=0, column=0, **tab_opts)


        compaction_comparison_frame = soLabelFrame(results_8_tab,text=trans(u'Osiadanie pala'))
        compaction_comparison_frame.grid(row=0, column=0, **frame_opts)

        self.compaction_comparison = dnComponentDlg.Comparison(compaction_comparison_frame,
                                                              lImage=self._createImage('s_sr'),
                                                              rImage=self._createImage('s_sr_dop'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.compaction_comparison.grid(row=0, column=0, **tab_opts)


        pile_reinforcement_comparison_frame = soLabelFrame(results_9_tab,text=trans(u'Zbrojenie pala'))
        pile_reinforcement_comparison_frame.grid(row=0, column=0, **frame_opts)

        self.pile_reinforcement_comparison = dnComponentDlg.Comparison(pile_reinforcement_comparison_frame,
                                                              lImage=self._createImage('A_s_pile_req'),
                                                              rImage=self._createImage('A_s_pile_prov'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.pile_reinforcement_comparison.grid(row=0, column=0, **tab_opts)


        slab_reinforcement_comparison_frame = soLabelFrame(results_10_tab,text=trans(u'Zbrojenie oczepu'))
        slab_reinforcement_comparison_frame.grid(row=0, column=0, **frame_opts)

        self.slab_reinforcement_comparison = dnComponentDlg.Comparison(slab_reinforcement_comparison_frame,
                                                              lImage=self._createImage('V_Ed'),
                                                              rImage=self._createImage('V_Rd'),
                                                              lFormat='%.2f',
                                                              rFormat='%.2f')
        self.slab_reinforcement_comparison.grid(row=0, column=0, **tab_opts)

        self.addUpdateTabFunctions('results_joint', updateFunc=[])


    def updatePermamentPanel(self):
        print "UpdatePermanentPanel"
        # update permanent panel
        self.updateCanvas()

    def updateCanvas(self):
        print "updateCanvas"
        # in this function, you basically draw anything on your canvases

        # erase everything
        self.cC1.delete(ALL)
        self.cC1.set_default()
        self.cC2.delete(ALL)
        self.cC2.set_default()
        self.cC3.delete(ALL)
        self.cC3.set_default()
        self.cC4.delete(ALL)
        self.cC4.set_default()

        #
        # HERE YOU DRAW ALL STUFF
        if self.getCompObj().getResults().isCalculated():
            draw = self.getCompObj().getResults().getResult('input_data')
            stresses_results = self.getCompObj().getResults().getResult('stresses_results')
            draw_pile_section(self.cC1, draw['piles'])
            draw_piles_plan(self.cC2, draw['piles'])
            draw_soils([self.cC3, self.cC4], draw['soils'], self.cC3_size[0], self.cC3_size[1])
            draw_piles_view(self.cC3, self.cC4, draw['piles'], self.cC3_size[1])
            draw_levels_in_view([self.cC3, self.cC4], draw['piles'], draw['z_w'], self.cC3_size[0], self.cC3_size[1])
            draw_stresses(self.cC3, draw['piles'], stresses_results, self.cC3_size[1])

            # this fits drawings to your canvases
            self.cC1.fit_to_view()
            self.cC2.fit_to_view()
            self.cC3.fit_to_view()
            self.cC4.fit_to_view()
        print "koniec updateCanvas"

    def updateTab_results(self):
        print "UpdateTabResult"
        # here you update main tab
        self.update_profiles_list()
        self.update_bearing_soil_box()


        comp_obj = self.getCompObj()
        r_obj = comp_obj.getResults()  # <<<< this and r_obj form component is literally the same thing
        comb_forces = None
        # check if results are calculated
        if r_obj.isCalculated():
            # get data for your subjects
            comb_forces = r_obj.getResult('comb_forces')
            if comb_forces is not None:
                self.extremal_load_comb_M.setValue(comb_forces['M'])
                self.extremal_load_comb_V.setValue(comb_forces['V'])
                self.extremal_load_comb_N.setValue(comb_forces['N'])

        # there you will load results to use
        vertical_comb_data = None
        vertical_group_comb_data = None
        negative_friction_comb_data = None
        horizontal_disp_comb_data = None
        rotation_disp_comb_data = None
        construction_disp_comb_data = None
        side_pressure_comb_data = None
        compaction_comb_data = None
        pile_reinforcement_comb_data = None
        slab_reinforcement_comb_data = None



        if r_obj.isCalculated():
            vertical_res = r_obj.getResult(EXTREMAL_VERTICAL_RATIO)
            vertical_group_res = r_obj.getResult(EXTREMAL_VERTICAL_GROUP_RATIO)
            negative_friction_res = r_obj.getResult(EXTREMAL_NEGATIVE_FRICTION_RATIO)
            horizontal_disp_res = r_obj.getResult(EXTREMAL_HORIZONTAL_DIS_RATIO)
            rotation_disp_res = r_obj.getResult(EXTREMAL_ROTATION_DIS_RATIO)
            construction_disp_res = r_obj.getResult(EXTREMAL_CONSTRUCTION_DIS_RATIO)
            side_pressure_res = r_obj.getResult(EXTREMAL_SIDE_PRESSURE_RATIO)
            compaction_res = r_obj.getResult(EXTREMAL_COMPACTION_RATIO)
            pile_reinforcement_res = r_obj.getResult(EXTREMAL_PILE_REINFORCEMENT_RATIO)
            slab_reinforcement_res = r_obj.getResult(EXTREMAL_SLAB_REINFORCEMENT_RATIO)

            if vertical_res is not None:
                vertical_comb_data = self.find_the_worst(vertical_res)
            if vertical_group_res is not None:
                vertical_group_comb_data = self.find_the_worst(vertical_group_res)
            if negative_friction_res is not None:
                negative_friction_comb_data = self.find_the_worst(negative_friction_res)
            if horizontal_disp_res is not None:
                horizontal_disp_comb_data = self.find_the_worst(horizontal_disp_res)
            if rotation_disp_res is not None:
                rotation_disp_comb_data = self.find_the_worst(rotation_disp_res)
            if construction_disp_res is not None:
                construction_disp_comb_data = self.find_the_worst(construction_disp_res)
            if side_pressure_res is not None:
                side_pressure_comb_data = self.find_the_worst(side_pressure_res)
            if compaction_res is not None:
                compaction_comb_data = self.find_the_worst(compaction_res)
            if pile_reinforcement_res is not None:
                pile_reinforcement_comb_data = self.find_the_worst(pile_reinforcement_res)
            if slab_reinforcement_res is not None:
                slab_reinforcement_comb_data = self.find_the_worst(slab_reinforcement_res)

        if vertical_comb_data is not None:
            self.vertical_comparison.setValues(vertical_comb_data['loading'], vertical_comb_data['resistance'])
        if vertical_group_comb_data is not None:
            self.vertical_group_comparison.setValues(vertical_group_comb_data['loading'], vertical_group_comb_data['resistance'])
        if negative_friction_comb_data is not None:
            self.negative_friction_comparison.setValues(negative_friction_comb_data['loading'], negative_friction_comb_data['resistance'])
        if horizontal_disp_comb_data is not None:
            self.horizontal_disp_comparison.setValues(horizontal_disp_comb_data['loading'], horizontal_disp_comb_data['resistance'])
        if rotation_disp_comb_data is not None:
            self.rotation_disp_comparison.setValues(rotation_disp_comb_data['loading'], rotation_disp_comb_data['resistance'])
        if construction_disp_comb_data is not None:
            self.construction_disp_comparison.setValues(construction_disp_comb_data['loading'], construction_disp_comb_data['resistance'])
        if side_pressure_comb_data is not None:
            self.side_pressure_comparison.setValues(side_pressure_comb_data['loading'], side_pressure_comb_data['resistance'])
        if compaction_comb_data is not None:
            self.compaction_comparison.setValues(compaction_comb_data['loading'], compaction_comb_data['resistance'])
        if pile_reinforcement_comb_data is not None:
            self.pile_reinforcement_comparison.setValues(pile_reinforcement_comb_data['loading'], pile_reinforcement_comb_data['resistance'])
        if slab_reinforcement_comb_data is not None:
            self.slab_reinforcement_comparison.setValues(slab_reinforcement_comb_data['loading'], slab_reinforcement_comb_data['resistance'])
        # check if results are calculated
        print "koniec UpdateTabResult"

    def updateTabsStatus(self):
        print "updateTabsStatus"
        # sometimes you to fill this function

    def getSize(self):
        # size of CompDlg in px
        return (860, 650)


# this is your main component, here you perform all of your calculations
class FoundationPiles(dnComponent.NodeComponent):
    print "FoundationPiles"
    ### FILL THIS CAREFULY ###
    type = dnConstants.COMP_USER_APP
    name = trans(u'Pale fundamentowe')
    description = trans(u'Wymiarowanie pali fundamentowych')
    dirPath = os.path.join(dnConstants.LIB_DIR_PATH, 'components/node/FoundationPiles/')
    iconPath = os.path.join(dnConstants.LIB_DIR_PATH,
                            'components/node/FoundationPiles/img/icon.gif')
    languages = [soConstants.ENGLISH]
    standardType = soConstants.EUROCODE_STANDARD
    summarySubjects = [
        EXTREMAL_VERTICAL_RATIO,
        EXTREMAL_VERTICAL_GROUP_RATIO,
        EXTREMAL_NEGATIVE_FRICTION_RATIO,
        EXTREMAL_HORIZONTAL_DIS_RATIO,
        EXTREMAL_ROTATION_DIS_RATIO,
        EXTREMAL_CONSTRUCTION_DIS_RATIO,
        EXTREMAL_SIDE_PRESSURE_RATIO,
        EXTREMAL_COMPACTION_RATIO,
        EXTREMAL_PILE_REINFORCEMENT_RATIO,
        EXTREMAL_SLAB_REINFORCEMENT_RATIO
    ]

    ###

    # you dont need to specify anything here
    def __init__(self, parent, itemId):

        dnComponent.NodeComponent.__init__(self, parent, itemId)

    # here you set default values for all of your variables
    def setDefault(self):
        print "setDefault"

        dnComponent.NodeComponent.setDefault(self)
        # here you init params for dlg parameters that are registered in setVars function of dlg component
        # self. means that they will be accessible thought the PipeSpliceConnection class and is neccessary to use
        self.load_N_Q_c = 0.
        self.load_V_Q_c = 0.
        self.load_M_Q_c = 0.
        self.additional_load = 0
        self.D = 1.
        self.D_f = 1.
        self.n_r = 3.
        self.n_s = 4
        self.r = 3.2
        self.L = 14.1
        self.H_f = 1.7
        self.h_grunt = 1.2
        self.r_kr = 0.5
        self.first_bearing_soil = 0.
        self.first_bearing_soil_text = ''
        self.soil_profile = 1.
        self.soil_profile_text = ''
        self.L_stem = 1.9
        self.B_stem = 1.7
        self.d_stem = 1.2
        self.r_phi = 32.
        self.r_phi_text = '32'
        self.r_phi_s = 12.
        self.r_phi_s_text = '12'
        self.c = 40
        self.reinf_n = 30.
        self.h_constr = 8.
        self.concrete = 'C30/37'
        self.formwork_boolean = 0

        self.phi_slab_x = 20.  # [mm] srednica pretow po kierunku x
        self.phi_slab_y = 28.  # [mm] srednica pretow po kierunku y
        ### MAX SPACING IS 0.25 m
        self.slab_spacing_x = 18.  # [cm] rozstaw pretow po kierunku x
        self.slab_spacing_y = 18.  # [cm] rozstaw pretow po kierunku y

    def doCustomCheck(self):
        print "doCustomCheck"

        def error(text):
            self.getMessageManager().addMessage(trans(text), type=dnComponent.MSG_TYPE_ERROR)

        A_s_temporary = check_minimal_degree_reinforcement(self.r_phi / 1000., self.reinf_n, self.D)
        if not A_s_temporary[0]:
            error(trans(u"Za mała powierzchnia zbrojenia") + "  (" + str(A_s_temporary[1]) + " < " + str(A_s_temporary[2]) + " cm2)")
            return False

        if not self.getModelManager().getSoilProfileManager().getSoilProfiles()[self.soil_profile].getLayers():
            error(trans(u"Nie zdefiniowano podłoża gruntowego"))
            return False

        # check_spiral_bars(self.r_phi/1000., self.r_phi_s/1000., self.a_sp/1000., self.a_sp_upper/1000.)
        # check_stiffening_bars(self.r_phi/1000., self.r_phi_p/1000., self.a_p/1000.)
        return True

    def doBeforeCalculate(self):
        print "doBeforeCalculate"
        if self.first_bearing_soil > len(get_soils_names(self, self.soil_profile)) - 1:
            self.first_bearing_soil = 0
        if self.soil_profile > len(get_profiles_list(self)):
            self.soil_profile = 1

        return True

    def doCalculate(self, soft=False):

        # get results obj
        r_obj = self.getResults()
        ratio_lists = {k: [] for k in self.summarySubjects}

        # slowniki do przechowywania danych dla wszystkich kombinacji
        # example_subject_res_data = {}  # create result data dict to store results of your calculations in ALL combs

        vertical_res_data = {}
        vertical_group_piles_res_data = {}
        negative_friction_res_data = {}
        horizontal_disp_res_data = {}
        rotation_disp_res_data = {}
        contruction_disp_res_data = {}
        side_pressure_res_data = {}
        compaction_res_data = {}
        pile_reinforecemnt_res_data = {}
        slab_reinforecemnt_res_data = {}

        print "doCalculate"
        # if soft, the model is recalculated
        # considered_node = self.getItem()
        # binded_elements = self.considered_node.getElements(node='both')
        # selected_beam = self.getItem()
        params = {'D': self.D,
                  'D_f': self.D_f,
                  'is_D_f': self.formwork_boolean,
                  'D_w': self.D - 0.1,
                  'r': self.r,
                  'L': self.L,
                  'H_f': self.H_f,
                  'h_grunt': self.h_grunt,
                  'r_kr': self.r_kr,
                  'n_r': self.n_r,
                  'n_s': self.n_s,
                  'B_f': self.r * (self.n_r - 1) + 2 * self.r_kr + self.D,
                  'L_f': self.r * (self.n_s - 1) + 2 * self.r_kr + self.D,
                  'r_phi': self.r_phi / 1000.,
                  'r_phi_s': self.r_phi_s / 1000.,
                  'reinf_n': self.reinf_n,
                  'c': self.c / 1000.,
                  'L_stem': self.L_stem,
                  'B_stem': self.B_stem,
                  'd_stem': self.d_stem,
                  'h_constr': self.h_constr}
        soils = get_soil_parameters(self, self.soil_profile)
        soils[-1]['z1'] = 200.  # wydluzenie ostatniej warstwy
        print(soils)
        z_w = get_water_level(self, self.soil_profile)
        input_data = {'piles': params,
                      'soils': soils,
                      'z_w': z_w, }

        self.getResults().setResults({'input_data': input_data})

        # tu pobieramy kombinacje
        column = self.getItem().getElements(node='both')[0]
        ord = 0 if column.getNodes()[0] == self.getItem() else 1
        if not soft:
            print "not soft"
            self._combination_data_USL = self._prepareCombinations(self.getItem().getElements(node='both')[0], ord,
                                                                   loadCombinationType=sdConstants.LOAD_COMB_TYPE_USL_BASIC_EC)
            self._combination_data_SLS = self._prepareCombinations(self.getItem().getElements(node='both')[0], ord,
                                                                   loadCombinationType=sdConstants.LOAD_COMB_TYPE_SLS_BASIC_EC)
        else:
            print "soft"

        #####################################################

        M_G_c = 0.
        V_G_c = 0.
        N_G_c = 0.
        M_Q_c = 0.
        V_Q_c = 0.
        N_Q_c = 0.
        # THIS IS THE MAIN LOOP, here you perform calculations for every load combination
        for comb_data in self._combination_data_USL:
            comb_name = comb_data['name']
            # print "comb_name:", comb_data['name']
            load_groups = comb_data['load_groups']
            M_G_c = comb_data['section_forces']['My'] # Nm
            V_G_c = comb_data['section_forces']['Tz']  # N
            N_G_c = comb_data['section_forces']['N']  # N
            #next 2 lines are there to show forces in UI
            comb_forces = {'M': round(M_G_c,1), 'N': round(N_G_c,1), 'V': round(V_G_c,1)}
            self.getResults().setResults({'comb_forces': comb_forces})
            if self.additional_load:
                print "additional loading"
                M_Q_c = self.load_M_Q_c  # Nm
                V_Q_c = self.load_V_Q_c  # N
                N_Q_c = self.load_N_Q_c  # N
            stresses_results = stress_displacements(soils, params, z_w, V_G_c)
            self.getResults().setResults({'stresses_results': stresses_results})
            D = self.D  # [m] - diameter
            D_f = self.D_f # [m] - diameter (w zwezeniu)
            D_w = self.D - 0.1  # [m] - inner diameter
            r = self.r  # [m] - distance between piles
            L = self.L  # [m] - pile length
            H_f = self.H_f  # [m] - height of foundation slab
            h_soil_above = self.h_grunt  # [m] - size of layer above foundation slab
            B_f = self.r * (self.n_r - 1) + 2 * self.r_kr + self.D
            L_f = self.r * (self.n_s - 1) + 2 * self.r_kr + self.D
            L_stem = self.L_stem
            B_stem = self.B_stem
            d_stem = self.d_stem
            n_r = self.n_r
            n_s = self.n_s
            r_kr = self.r_kr
            n = self.n_r * self.n_s
            depth_of_foundation = L + H_f + h_soil_above
            h_constr = self.h_constr
            conc_class = self.concrete

            gamma_G = 1.35
            phi_slab_x = self.phi_slab_x / 1000. #[m]
            phi_slab_y = self.phi_slab_y / 1000. #[m]
            bar_spacing_slab_x = self.slab_spacing_x / 100. #[m]
            bar_spacing_slab_y = self.slab_spacing_y / 100. #[m]

            # zbrojenie
            r_phi = self.r_phi / 1000.
            reinf_n = self.reinf_n

            load_bearing_layer = int(self.first_bearing_soil)
            z_olbs = soils[load_bearing_layer]['z0']  # layer of the load-bearing soil

            ## computational level of load-bearing layer
            # because of vertical stresses
            h_z_V = calculate_comp_level_load_bearing_loads(z_olbs, soils, load_bearing_layer)
            z_colbs_V = z_olbs - h_z_V  # [m] rzedna obliczeniowa poziomu stropu gruntow nosnych z uwagi na sily pionowe
            # because of horizontal stresses
            z_colbs_H = z_olbs + D * 1.5  # [m] rzedna obliczeniowa poziomu stropu gruntow nosnych z uwagi na sily poziome
            concrete_ro = 2500.  # concrete density [kg/m3]

            ## ALL FORCES
            V_all_c, V_all_d, V_G_d, V_Q_d = calculate_vertical_forces(B_f, L_f, H_f, L, D, n, h_soil_above, soils, z_w, L_stem, B_stem, d_stem, V_G_c, V_Q_c)  # [kN]
            N_c, N_d = calculate_forces(N_G_c, N_Q_c)  # [kN]
            M_c, M_d = calculate_forces(M_G_c, M_Q_c)  # [kNm]

            h_ci, h_ci_prim = calculate_critical_depth(D)  # [m]
            q_b_c = calculate_q_k(soils, h_ci, h_ci_prim, z_colbs_V, depth_of_foundation)  # [kPa]
            # load bearing capacity under pile
            R_b_d = calculate_load_capacity_under_pile(q_b_c, D)  # [kN]
            # load bearing capapcity along the side of pile
            R_s_d = calculate_load_capacity_along_side_of_pile(load_bearing_layer, soils, D, z_colbs_V, depth_of_foundation)  # [kN]
            # negative friction for layer above load bearing level
            T_n_d = calculate_negative_friction(load_bearing_layer, soils, D, H_f, h_soil_above)  # [kN]
            R_c_d = R_s_d + R_b_d

            R_c_d_cal = R_b_d + R_s_d - T_n_d

            F_c_d = calculate_piles_resistance_vertical(D, n, r, n_s, r_kr, L_f, V_all_d, M_d)  # [kN]

            Q_T_n_c = calculate_weight_cooperative_ground(load_bearing_layer, soils, h_soil_above, H_f, L_f, B_f, r_kr)  # [kN]
            T_n_c = T_n_d / gamma_G

            # check the load bearing capacity of group of piles
            # obliczeniowa nosnosc pojedycznego pala pomniejszona o ciezar wlasny
            R_c_d_cal_1 = calculate_load_bearing_capacity_of_one_pile(L, D, r, z_w, B_f, L_f, H_f, h_soil_above, soils, R_c_d_cal)
            # obliczeniowa sila pionowa od obciazen zewnetrznych
            V_Ed = gamma_G * V_G_c + V_Q_d

            # minimalna liczba pali
            n_min = V_Ed / R_c_d_cal_1

            # check the load bearing capacity of group of piles
            R_c_d_GP = calculate_load_bearing_capacity_of_group_of_piles(load_bearing_layer, soils, r, D, n, depth_of_foundation, h_z_V, R_b_d, R_s_d, T_n_d)

            # wartosc obliczeniowa osiowego obciazenia grupy pali
            F_c_d_GP = V_G_d + V_Q_d

            # check load bearing capacity due to horizontal forces

            z_hw, D_p, alpha_deformation = calculate_deformation_alpha(soils, depth_of_foundation, D, r, n_r, z_colbs_H)
            # wysokosc zastepcza dlugosci pala z uwagi na sily poziome
            h_prim = alpha_deformation * (depth_of_foundation - z_colbs_H)
            # calculate displacement
            y_0, phi_0, y_constr, H_1_d, h_H = calculate_displacement(n, D, N_c, N_d, z_colbs_H, h_soil_above, H_f, h_prim, h_constr, alpha_deformation)
            # max displacement
            y_0_limit = 0.01
            phi_0_limit = 0.002
            y_constr_limit = 0.05

            M_z_d, p_z_d, r_z_d = calculate_moment_side_pressure(soils, load_bearing_layer, depth_of_foundation, z_colbs_H, D_p, H_1_d, h_H, alpha_deformation, h_prim, z_hw)



            ### CALCULATION OF REINFORCE
            f_ck = concrete_dict[conc_class]['f_ck'] * 10 ** 6  # Pa
            f_cd = f_ck / 1.4

            f_yk = 500000000.  # Pa
            f_yd = f_yk / 1.15
            E_s = 200000000000.  # Pa

            #przyjecie srednicy pala
            D = self.D_f if self.formwork_boolean else self.D
            # oszacowanie bezpieczne
            B = D / 2. ** (0.5)
            ## otulina zbrojenia
            c = self.c / 1000.  # m
            ## zbrojenie podluzne
            # pole przekroju betonowego
            # dlugosc zakotwienia
            l_bd = 30. * r_phi         *10.  # m
            # srednica pretow spirali
            r_phi_s = self.r_phi_s / 1000.  # m
            # rzeczywista srednica pretow zbrojenia spirali
            r_phi_s_rib = ribbed_d[r_phi_s]
            # # rozstaw pretow spirali pod plyta fundamentowa
            # a_sp = 0.3  # m
            # # rozsta pretow spirali w plycie fundamentowej
            # a_sp_upper = 0.2  # m

            ### dodatkowe wymiary pala ###
            D_ext_sp = D - 2. * c
            # srednica wewnetrzna zbrojenia spiralnego
            D_int_sp = D_ext_sp - 2. * r_phi_s_rib

            # projektowanie przekroju zelbetowego - przekroj mimosrodowo sciskany
            a = c + r_phi / 2.  # [m]

            A_s_pile = concrete_compression_calculation(N_d*1000., M_d*1000., B, a, f_cd, f_yd, E_s, conc_class)
            # nosnosc na scinanie bez zbrojenia
            V_Rd_c_pile = shear_resistance(N_d*1000., B, a, r_phi, reinf_n, f_cd, f_ck)

            A_s_prov = (reinf_n * math.pi * r_phi ** 2. / 4.) * 10000.
            A_s_needed = max(A_s_pile, get_min_reinforced_area(B ** 2.)) * 10000.


            ### CALCULATE REINFORCEMENT FOR SLAB

            A_s_prov_slab_x = calculate_area_reinforcement(phi_slab_x, bar_spacing_slab_x)
            A_s_prov_slab_y = calculate_area_reinforcement(phi_slab_y, bar_spacing_slab_y)

            s_slab_max = 0.25  # [m] maksymalny rostaw pretow w obu kierunkach
            c_min_dur = 0.025  # [m] otulina zbrojenia ze wzgledu na trwalosc
            c_min_b = 0.028  # [m] otulina zbroja ze wzgledu na przyczepnosc

            c_min = max(c_min_b, c_min_dur, 0.010)  # [m] otulenie minimalne
            delta_c = 0.010  # [m] odchylka wykonawcza

            c_nom = max(c_min + delta_c, 0.040)  # [m] otulenie minimalne

            d_slab_x = H_f - c_nom - phi_slab_x / 2.
            d_slab_y = d_slab_x - phi_slab_y

            R_slab_c_d = R_c_d * 1000.  # [N]
            M_slab_x_d = R_slab_c_d * r  # wartosc obliczeniowa momenty zginajacego w plycie w stodku rozpietosci po kierunku x
            M_slab_y_d = R_slab_c_d * 2 * r

            Z_x = M_slab_x_d / d_slab_x
            Z_y = M_slab_y_d / d_slab_y

            A_s_slab_x = Z_x / f_yd
            A_s_slab_y = Z_y / f_yd
            A_s_min_slab_x = Z_x / A_s_slab_x  # [m2 / m]
            A_s_min_slab_y = Z_y / A_s_slab_y  # [m2 / m]

            # do sprawdzenia z A_s_prov
            V_Ed_slab = V_Q_d + gamma_G * (
                    V_G_c + plate_weigth(L_f, B_f, z_w, h_soil_above, H_f) + pile_weight(L, D, z_w, h_soil_above, H_f) + stem_weight(L_stem, B_stem, d_stem, z_w, h_soil_above) + weight_soil_above(B_f, L_f,
                                                                                                                                                                                                    h_soil_above,
                                                                                                                                                                                                    soils))
            M_Ed_slab = M_d

            # naprezenia w plycie wywolane przez dzialajacy na fundament
            p = (gamma_G * V_G_c + V_Q_d) / (B_f * L_f)  # [MPa]


            ## SPRAWDZENIE PRZEBICIA
            # wymiary trzonu
            c_1 = L_stem  # [m]
            c_2 = B_stem  # [m]

            # wspolczynnik do przebicia (zalezny od stosunku c1/c2)
            table_coeff_k_rectangle = [[0.5, 0.45], [1.0, 0.6], [2.0, 0.7],
                                       [3.0, 0.8]]

            k = linear_interpolation(c_1 / c_2, table_coeff_k_rectangle)

            # srednia wysokosc uzyteczna stopu fundamentowej
            d_eff_slab = (d_slab_x + d_slab_x) / 2.

            # rozklad naprezen stycznych
            W_1 = 0.5 * (c_1) ** 2. + c_1 * c_2 + 4. * c_2 * d_eff_slab + 16. * d_eff_slab ** 2. + 2. * math.pi * d_eff_slab * c_1

            # obwod kontrolny - lico slupa
            u_0 = 2. * (c_1 + c_2)  # [m] obwod
            A_0 = c_1 * c_2  # [m2] obwod

            delta_V_Ed_slab = p * A_0
            V_Ed_red_slab = V_Ed_slab - delta_V_Ed_slab  # wartosc obliczeniowa sily pionowej netto

            v_Ed_slab = V_Ed_red_slab * (1 + (k * M_Ed_slab * u_0) / (V_Ed_red_slab * W_1)) / (u_0 * d_eff_slab)

            ni = 0.6 * (1 - f_ck / 1000000. / 250.)  # f_ck MUSI BY W MPa (tutaj podstawione w PA)

            V_Rd_max_slab = 0.5 * ni * f_cd / 1000.


            # obwod kontrolny - 2d_eff od lica slupa

            a_slab = 2. * d_eff_slab
            u_0_2 = 2. * c_1 + 2. * c_2 + 2. * math.pi * d_eff_slab
            A_0_2 = c_1 * c_2 + 2. * c_1 * 2 * d_eff_slab + 2. * c_2 * 2. * d_eff_slab + math.pi * (2. * d_eff_slab) ** 2.

            delta_V_Ed_slab_2 = p * A_0_2
            V_Ed_red_slab_2 = V_Ed_slab - delta_V_Ed_slab_2
            v_Ed_slab_2 = V_Ed_red_slab_2 * (1 + (k * M_Ed_slab * u_0_2) / (V_Ed_red_slab_2 * W_1)) / (u_0_2 * d_eff_slab)

            gamma_C = 1.4  # [-]
            c_Rd_c = 0.18 / gamma_C  # [-]
            coeff_k_2 = min(1 + (200 / d_eff_slab * 1000) ** 0.5, 2)  # [-]

            ro_l_x_slab = A_s_slab_x / (B_f * d_slab_x)  # [-]
            ro_l_y_slab = A_s_slab_y / (B_f * d_slab_y)  # [-]

            ro_l_slab = min((ro_l_x_slab * ro_l_y_slab) ** 0.5, 0.02)  # [-]

            v_min_slab = 0.035 * coeff_k_2 ** (3. / 2.) * f_ck ** 0.5

            v_Rd_slab = max(c_Rd_c * coeff_k_2 * (100. * ro_l_slab * f_ck) ** (1 / 3.) * 2 * d_eff_slab / a_slab, v_min_slab * 2 * d_eff_slab / a_slab)


            # v_Ed_slab < v_Rd_slab


            # # get your comb name and load groups
            # comb_name = comb_data['name']
            # # load_groups = comb_data['load_groups']
            # load_groups = [1,2]
            # # DO SOME CALCULATIONS for EXAMPLE_SUBJECT
            # resistance = self.test1 * self.test2 * self.test3  ## example bearing
            # # loading = comb_data['section_forces']['N']  # this is how you acquire section forces
            # loading = 123
            # ratio =1
            #
            #     #save your calculations results for the given comb
            #     example_subject_comb_data = {
            #         'resistance': resistance,
            #         'loading': loading,
            #         'ratio': ratio,
            #         'load_groups': load_groups,
            #     }
            #
            #     # use comb name as a key to save informations and append ratio
            #     example_subject_res_data[comb_name] = example_subject_comb_data
            #     ratios_list[example_subject_comb_data].append(ratio)

            vertical_resistance_comb_data = {
                'loading': F_c_d/1000.,
                'resistance': R_c_d_cal/1000.,
                'ratio': F_c_d / R_c_d_cal
            }
            vertical_res_data[comb_name] = vertical_resistance_comb_data
            ratio_lists[EXTREMAL_VERTICAL_RATIO].append(F_c_d / R_c_d_cal)

            vertical_resistance_group_of_piles_comb_data = {
                'loading': F_c_d_GP/1000.,
                'resistance': R_c_d_GP/1000.,
                'ratio': F_c_d_GP / R_c_d_GP
            }
            vertical_group_piles_res_data[comb_name] = vertical_resistance_group_of_piles_comb_data
            ratio_lists[EXTREMAL_VERTICAL_GROUP_RATIO].append(F_c_d_GP / R_c_d_GP)

            negative_friction_comb_data = {
                'loading': T_n_c,
                'resistance': Q_T_n_c,
                'ratio': T_n_c / Q_T_n_c
            }
            negative_friction_res_data[comb_name] = negative_friction_comb_data
            ratio_lists[EXTREMAL_NEGATIVE_FRICTION_RATIO].append(T_n_c / Q_T_n_c)

            horizontal_displacement_comb_data = {
                'loading': y_0,
                'resistance': y_0_limit,
                'ratio': y_0 / y_0_limit
            }
            horizontal_disp_res_data[comb_name] = horizontal_displacement_comb_data
            ratio_lists[EXTREMAL_HORIZONTAL_DIS_RATIO].append(y_0 / y_0_limit)

            rotation_displacement_comb_data = {
                'loading': phi_0,
                'resistance': phi_0_limit,
                'ratio': phi_0 / phi_0_limit
            }
            rotation_disp_res_data[comb_name] = rotation_displacement_comb_data
            ratio_lists[EXTREMAL_ROTATION_DIS_RATIO].append(phi_0 / phi_0_limit)

            construction_disp_comb_data = {
                'loading': y_constr,
                'resistance': y_constr_limit,
                'ratio': y_constr / y_constr_limit
            }

            contruction_disp_res_data[comb_name] = construction_disp_comb_data
            ratio_lists[EXTREMAL_CONSTRUCTION_DIS_RATIO].append(y_constr / y_constr_limit)

            side_pressure_comb_data = {
                'loading': p_z_d,
                'resistance': r_z_d,
                'ratio': p_z_d / r_z_d
            }
            side_pressure_res_data[comb_name] = side_pressure_comb_data
            ratio_lists[EXTREMAL_SIDE_PRESSURE_RATIO].append(p_z_d / r_z_d)

            # [cm]
            compaction_comb_data = {
                'loading': stresses_results['stresses_under'][-1]['s'],
                'resistance': 0.02,
                'ratio': stresses_results['stresses_under'][-1]['s'] / 0.02
            }
            compaction_res_data[comb_name] = compaction_comb_data
            ratio_lists[EXTREMAL_COMPACTION_RATIO].append(stresses_results['stresses_under'][-1]['s'] / 0.02)


            pile_reinforcement_comb_data = {
                'loading': A_s_needed,
                'resistance': A_s_prov,
                'ratio': A_s_needed / A_s_prov
            }
            pile_reinforecemnt_res_data[comb_name] = pile_reinforcement_comb_data
            ratio_lists[EXTREMAL_PILE_REINFORCEMENT_RATIO].append(A_s_needed / A_s_prov)

            slab_reinforcement_comb_data = {
                'loading': v_Ed_slab,
                'resistance': V_Rd_max_slab,
                'ratio': v_Ed_slab / V_Rd_max_slab}
            slab_reinforecemnt_res_data[comb_name] = slab_reinforcement_comb_data
            ratio_lists[EXTREMAL_SLAB_REINFORCEMENT_RATIO].append(v_Ed_slab / V_Rd_max_slab)

        # you went through all combs, now collect data for all conditions
        result_data = {}
        ratio_data = {}

        # # set max ratio to be displayed in dlg left side
        # ratio_data[example_subject_comb_data] = max(ratios_list[example_subject_comb_data])
        # # save results data
        # result_data[example_subject_comb_data] = example_subject_res_data

        ratio_data[EXTREMAL_VERTICAL_RATIO] = max(ratio_lists[EXTREMAL_VERTICAL_RATIO])
        result_data[EXTREMAL_VERTICAL_RATIO] = vertical_res_data

        ratio_data[EXTREMAL_VERTICAL_GROUP_RATIO] = max(ratio_lists[EXTREMAL_VERTICAL_GROUP_RATIO])
        result_data[EXTREMAL_VERTICAL_GROUP_RATIO] = vertical_group_piles_res_data

        ratio_data[EXTREMAL_NEGATIVE_FRICTION_RATIO] = max(ratio_lists[EXTREMAL_NEGATIVE_FRICTION_RATIO])
        result_data[EXTREMAL_NEGATIVE_FRICTION_RATIO] = negative_friction_res_data

        ratio_data[EXTREMAL_HORIZONTAL_DIS_RATIO] = max(ratio_lists[EXTREMAL_HORIZONTAL_DIS_RATIO])
        result_data[EXTREMAL_HORIZONTAL_DIS_RATIO] = horizontal_disp_res_data

        ratio_data[EXTREMAL_ROTATION_DIS_RATIO] = max(ratio_lists[EXTREMAL_ROTATION_DIS_RATIO])
        result_data[EXTREMAL_ROTATION_DIS_RATIO] = rotation_disp_res_data

        ratio_data[EXTREMAL_CONSTRUCTION_DIS_RATIO] = max(ratio_lists[EXTREMAL_CONSTRUCTION_DIS_RATIO])
        result_data[EXTREMAL_CONSTRUCTION_DIS_RATIO] = contruction_disp_res_data

        ratio_data[EXTREMAL_SIDE_PRESSURE_RATIO] = max(ratio_lists[EXTREMAL_SIDE_PRESSURE_RATIO])
        result_data[EXTREMAL_SIDE_PRESSURE_RATIO] = side_pressure_res_data

        ratio_data[EXTREMAL_COMPACTION_RATIO] = max(ratio_lists[EXTREMAL_COMPACTION_RATIO])
        result_data[EXTREMAL_COMPACTION_RATIO] = compaction_res_data

        ratio_data[EXTREMAL_PILE_REINFORCEMENT_RATIO] = max(ratio_lists[EXTREMAL_PILE_REINFORCEMENT_RATIO])
        result_data[EXTREMAL_PILE_REINFORCEMENT_RATIO] = pile_reinforecemnt_res_data

        ratio_data[EXTREMAL_SLAB_REINFORCEMENT_RATIO] = max(ratio_lists[EXTREMAL_SLAB_REINFORCEMENT_RATIO])
        result_data[EXTREMAL_SLAB_REINFORCEMENT_RATIO] = slab_reinforecemnt_res_data


        # this will save your results and set ratios in dlg
        r_obj.setResults(result_data)
        r_obj.setSummary(
            [[h, ratio_data[h]] for h in self.summarySubjects if h in result_data]
        )

        # add message about ratio
        if self.getResults().getUseRatio() > 1.:
            self.getMessageManager().addMessage(trans(u'!!!Nośność elementu przekroczona!!!.'),
                                                type=dnComponent.MSG_TYPE_ERROR)
        else:
            self.getMessageManager().addMessage(trans(u'Element zaprojektowany poprawnie.'),
                                                type=dnComponent.MSG_TYPE_IMPORTANT)

        return True

    def insertRTFReport(self, docObj, sectionObj):
        # here you create rtf report
        pass

    def getDlgClass(self):
        import dnFoundationPilesLib

        if self.getApp().isMsgMode():
            reload(dnFoundationPilesLib)

        return FoundationPilesDlg

    # other functions you need
    @property
    # def check_node(self):
    #     if self.selected_beam.getNodes()[0] == self.considered_node:
    #         self.binded_node = 0.
    #     else:
    #         self.binded_node = 1.
    #     return self.binded_node

    def _insertDesignCondHeading(self, rtf_report_methods,
                                 subject, results, title=True, title_prefix='', detail_data=True, suffix=''):

        ratio = results['ratio']
        ratio_exceeded = ratio > 1.0
        comb_data = results['comb_data']
        comb_name = results['comb_name']

        if title:
            rtf_report_methods.insertSubTitle(
                title_prefix + subject.encode('cp1250') + ' (%.1f ' % (float(ratio) * 100.) + '%)' + \
                ['', trans(' - Warunek przekroczony!!!')][ratio_exceeded],
                highlighted=ratio_exceeded)

        if detail_data:
            lg_data_str = ''
            lg_data = results['load_groups']
            if lg_data is not None and len(lg_data):
                lg_data_str = ' (%s)' % ''.join(['%s,' % lg for lg in lg_data])

            r_data = ''
            section_forces = comb_data['section_forces']

            for n, unit in [
                ['Ned', 'kN'],
                ['Ved', 'kN'],
                ['Med', 'kNm'],
            ]:
                r_data += '%s=%.1f%s, ' % (n, section_forces[n], unit)
            r_data = r_data[:-2]
            comb_name.encode('cp1250'),
            rtf_report_methods.insertText(trans('Komb: %s %s %s %s%s') %
                                          (comb_name, lg_data_str, r'\u8594\'3f', r_data, suffix),
                                          spaceAfter=150, fontEffect='italic')
