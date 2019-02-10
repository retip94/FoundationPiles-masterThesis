# region ////////////////////////////////////////LIBS/////////////////////////////////////////////////////////////
# import itertools
# import math
# from collections import namedtuple

# import ssConstants
import itertools
import math
import numpy as np
from collections import namedtuple

import ssConstants
from dnBaseLib import *

# endregion
# region ////////////////////////////////////////TABLES ETC///////////////////////////////////////////////////////

ribbed_d = {  # m
    0.006: 0.008,
    0.008: 0.009,
    0.01: 0.011,
    0.012: 0.014,
    0.014: 0.016,
    0.016: 0.018,
    0.020: 0.026,
    0.025: 0.028,
    0.028: 0.032,
    0.032: 0.036,
    0.040: 0.045,
}

r_phis = {'fi 6': 6, 'fi 8': 8, 'fi 10': 10, 'fi 12': 12, 'fi 14': 14, 'fi 16': 16, 'fi 20': 20, 'fi 25': 25}
opts = {"outline": 'black', "width": 2, "tags": (soMetricCanvas.TAB_MOVE, soMetricCanvas.TAB_ROTATE, soMetricCanvas.TAB_SCALE, soMetricCanvas.TAB_FIT_TO_VIEW)}
dot = 0.001

## Interpolation of K_c coefficien or K_q
# wartosci na osi x
x_tab = [0., 2., 4., 6., 8., 10., 12., 14., 16., 18., 20.]

# K_c
# wartosci y (od K_c)
y_K_c_tab = [2., 4., 6., 8., 10., 20., 40., 60., 80., 100., 200.]
# tabela przeciec z osiami
K_c = [
    [0., 4., 13., 25., 30., 40., 50., 60., 75., 90., 110.],  # 0
    [0., 0., 1., 8., 15., 28., 37., 42., 45., 50., 70.],  # 2
    [0., 0., 0., 4., 10., 23., 32., 37., 40., 43., 50.],  # 4
    [0., 0., 0., 2., 8., 21., 30., 35., 38., 40., 47.],  # 6
    [0., 0., 0., 1., 7., 20., 29., 34., 37., 38., 45.],  # 8
    [0., 0., 0., 0., 6., 20., 28., 33., 36., 38., 44.],  # 10
    [0., 0., 0., 0., 5., 19., 28., 33., 35., 37., 43.],  # 12
    [0., 0., 0., 0., 5., 19., 27., 32., 35., 37., 43.],  # 14
    [0., 0., 0., 0., 5., 19., 27., 32., 34., 37., 42.],  # 16
    [0., 0., 0., 0., 5., 18., 27., 31., 34., 36., 41.],  # 18
    [0., 0., 0., 0., 5., 18., 27., 31., 33., 36., 41.],  # 20
]
# K_q
# wartosci y (od K_q)
y_K_q_tab = [0.4, 0.6, 0.8, 1., 2., 4., 6., 8., 10., 20., 40., 60., 80.]
# tabela przeciec z osiami
K_q = [
    [5., 7., 8., 10., 18., 27., 32., 36., 38., 45., 60., 70., 80., 100.],
    [4., 6., 7., 9., 15., 23., 28., 32., 35., 42., 50., 55., 65, ],
    [4., 5., 7., 8., 13., 20., 25., 29., 32., 040., 46., 48., 55.],
    [4., 5., 6., 8., 13., 20., 24., 27., 31., 38., 45., 47., 50.],
    [4., 5., 6., 8., 12., 19., 24., 27., 30., 37., 43., 46., 49.],
    [3., 4., 6., 8., 12., 18., 23., 26., 29., 35., 42., 46., 48.],
    [2., 4., 5., 7., 12., 18., 22., 25., 28., 35., 41., 45., 47.],
    [2., 4., 5., 7., 11., 17., 22., 25., 28., 34., 41., 44., 46.],
    [2., 4., 5., 7., 11., 17., 22., 25., 27., 34., 40., 43., 46.],
    [2., 3., 5., 6., 11., 17., 21., 24., 27., 34., 40., 43., 45.],
    [2., 3., 5., 6., 11., 17., 21., 24., 27., 34., 40., 43., 45.],
]

# wartosci wspolczynnikow A_y, B_y, A_f, B_f

# [h_prim, (A_y, B_y, A_f, B_f)]
table_A_B_displacement_coeff = [
    [2.0, (4.7, 3.4, 3.4, 3.2)],
    [2.2, (4.0, 2.7, 2.7, 2.5)],
    [2.4, (3.5, 2.3, 2.3, 2.2)],
    [2.6, (3.2, 2.0, 2.0, 2.0)],
    [2.8, (2.9, 1.8, 1.8, 1.9)],
    [3.0, (2.7, 1.7, 1.7, 1.8)],
    [3.2, (2.6, 1.7, 1.7, 1.8)],
    [3.4, (2.5, 1.7, 1.7, 1.8)],
    [3.6, (2.4, 1.7, 1.7, 1.8)],
    [3.8, (2.4, 1.7, 1.7, 1.8)],
    [4.0, (2.4, 1.7, 1.7, 1.8)],
    [4.5, (2.4, 1.6, 1.6, 1.8)],
    [5.0, (2.4, 1.6, 1.6, 1.8)]
]

# z_prim (A_m, B_m) h_prim <= 3.0, = 3.5, >= 5.0
table_A_B_bending_calculations = [
    [0.0, (0.0, 1.0), (0.0, 1.0), (0.0, 1.0)],
    [0.25, (0.30, 0.99), (0.27, 0.99), (0.27, 0.99)],
    [0.5, (0.48, 0.98), (0.46, 0.98), (0.46, 0.98)],
    [0.75, (0.60, 0.94), (0.60, 0.94), (0.60, 0.95)],
    [1.0, (0.67, 0.85), (0.70, 0.86), (0.70, 0.88)],
    [1.25, (0.70, 0.73), (0.75, 0.77), (0.78, 0.78)],
    [1.5, (0.65, 0.58), (0.73, 0.63), (0.77, 0.63)],
    [1.75, (0.60, 0.46), (0.67, 0.50), (0.71, 0.50)],
    [2.0, (0.51, 0.32), (0.59, 0.38), (0.62, 0.38)],
    [2.5, (0.29, 0.10), (0.31, 0.17), (0.41, 0.20)],
    [3.0, (0.0, 0.0), (0.10, 0.03), (0.22, 0.07)],
    [3.5, (0.0, 0.0), (0.0, 0.0), (0.08, 0.0)],
    [4.0, (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
]

# z_prim (A_pH, B_pM) h_prim <= 3.0, = 3.5, >= 5.0
table_A_B_side_calculations = [
    [0.0, (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)],
    [0.25, (0.66, 0.34), (0.59, 0.35), (0.59, 0.35)],
    [0.5, (0.91, 0.42), (0.84, 0.45), (0.80, 0.46)],
    [0.75, (1.06, 0.46), (0.99, 0.45), (0.94, 0.43)],
    [1.0, (1.1, 0.44), (1.02, 0.39), (0.95, 0.35)],
    [1.25, (1., 0.30), (0.9, 0.25), (0.85, 0.23)],
    [1.5, (0.8, 0.15), (0.73, 0.11), (0.71, 0.07)],
    [1.75, (0.53, 0.02), (0.54, 0.0), (0.52, 0.0)],
    [2.0, (0.2, 0.0), (0.30, 0.0), (0.27, 0.0)],
    [2.5, (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
]
# MPa, epsilon[promile]
concrete_dict = {'C12/15': {'f_ck': 12., 'f_ck_cube': 16., 'f_cm': 20., 'f_ctm': 1.6, 'f_ctk_005': 1.1, 'f_ctk_095': 2.0, 'E_cm': 27000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C16/20': {'f_ck': 16., 'f_ck_cube': 20., 'f_cm': 24., 'f_ctm': 1.9, 'f_ctk_005': 1.3, 'f_ctk_095': 2.5, 'E_cm': 29000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C20/25': {'f_ck': 20., 'f_ck_cube': 25., 'f_cm': 28., 'f_ctm': 2.2, 'f_ctk_005': 1.5, 'f_ctk_095': 2.9, 'E_cm': 30000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C25/30': {'f_ck': 25., 'f_ck_cube': 30., 'f_cm': 33., 'f_ctm': 2.6, 'f_ctk_005': 1.8, 'f_ctk_095': 3.3, 'E_cm': 31000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C30/37': {'f_ck': 30., 'f_ck_cube': 37., 'f_cm': 38., 'f_ctm': 2.9, 'f_ctk_005': 2.0, 'f_ctk_095': 3.8, 'E_cm': 32000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C35/40': {'f_ck': 35., 'f_ck_cube': 40., 'f_cm': 43., 'f_ctm': 3.2, 'f_ctk_005': 2.2, 'f_ctk_095': 4.2, 'E_cm': 34000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C40/50': {'f_ck': 40., 'f_ck_cube': 50., 'f_cm': 48., 'f_ctm': 3.5, 'f_ctk_005': 2.5, 'f_ctk_095': 4.6, 'E_cm': 35000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C45/55': {'f_ck': 45., 'f_ck_cube': 55., 'f_cm': 53., 'f_ctm': 3.8, 'f_ctk_005': 2.7, 'f_ctk_095': 4.9, 'E_cm': 36000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C50/60': {'f_ck': 50., 'f_ck_cube': 60., 'f_cm': 58., 'f_ctm': 4.1, 'f_ctk_005': 2.9, 'f_ctk_095': 5.3, 'E_cm': 37000., 'e_c3': 1.75, 'e_cu3': 3.5},
                 'C55/67': {'f_ck': 55., 'f_ck_cube': 67., 'f_cm': 63., 'f_ctm': 4.2, 'f_ctk_005': 3.0, 'f_ctk_095': 5.5, 'E_cm': 38000., 'e_c3': 1.80, 'e_cu3': 3.1},
                 'C60/75': {'f_ck': 60., 'f_ck_cube': 75., 'f_cm': 68., 'f_ctm': 4.4, 'f_ctk_005': 3.1, 'f_ctk_095': 5.7, 'E_cm': 39000., 'e_c3': 1.90, 'e_cu3': 2.9},
                 'C70/85': {'f_ck': 70., 'f_ck_cube': 85., 'f_cm': 78., 'f_ctm': 4.6, 'f_ctk_005': 3.2, 'f_ctk_095': 6.0, 'E_cm': 41000., 'e_c3': 2.00, 'e_cu3': 2.7},
                 'C80/95': {'f_ck': 80., 'f_ck_cube': 95., 'f_cm': 99., 'f_ctm': 4.8, 'f_ctk_005': 3.4, 'f_ctk_095': 6.3, 'E_cm': 42000., 'e_c3': 2.20, 'e_cu3': 2.6},
                 'C90/105': {'f_ck': 90., 'f_ck_cube': 105., 'f_cm': 98., 'f_ctm': 5.0, 'f_ctk_005': 3.5, 'f_ctk_095': 6.6, 'E_cm': 44000., 'e_c3': 2.30, 'e_cu3': 2.6},
                 }


# endregion
# region ////////////////////////////////////////INTERPOLATION_GETTING_DATA/////////////////////////////////////////////////////

def linear_interpolation(x, data):
    if x <= sorted(data)[0][0]:
        return sorted(data)[0][1]
    elif x >= sorted(data)[-1][0]:
        return sorted(data)[-1][1]
    else:
        for item in sorted(data):
            if item[0] > x:
                (_x2, _q2) = item
                break
            (_x1, _q1) = item
        return _q1 + (x - _x1) * (_q2 - _q1) / (_x2 - _x1)


# z/D_p, z/B_p
def bilinear_interpolation(x_tab, y_tab, K, z_D, phi):
    # zwraca wiersze dla danego kwadratu w ktorym jestesmy i wartosci x-ow

    if z_D >= 20.:
        z_D = 19.9999

    for i in range(len(x_tab)):
        if x_tab[i] > z_D:
            values = K[i - 1], K[i]
            x_values = x_tab[i - 1], x_tab[i]
            break
    # zwraca wartosci Q do interpolacji
    coeff = []

    for i in range(len(values[0])):
        if values[0][i] > phi:
            coeff.append(values[0][i])
            coeff.append(values[0][i - 1])
            coeff.append(values[1][i])
            coeff.append(values[1][i - 1])
            y_values = y_tab[i], y_tab[i - 1]
            break

    # przyporzadkowanie zmiennych do odpowiednich zmiennych do liczenia

    Q_12, Q_11, Q_22, Q_21 = coeff
    x_1, x_2 = x_values
    y_2, y_1 = y_values
    x = z_D
    P = phi

    # bilinear interpolation
    R_1 = (x_2 - x) / (x_2 - x_1) * Q_11 + (x - x_1) / (x_2 - x_1) * Q_21
    R_2 = (x_2 - x) / (x_2 - x_1) * Q_12 + (x - x_1) / (x_2 - x_1) * Q_22

    # zmiana wzoru tak aby otrzymac K_c/q
    y = (P * (y_2 - y_1) - R_1 * y_2 + R_2 * y_1) / (R_2 - R_1)

    return y


def get_data_from_table(col, z_prim, table):
    A, B = 0, 0

    if z_prim >= max(table)[0]:
        A, B = 0, 0
    else:
        for i in range(len(table)):
            row = table[i]
            if row[0] >= z_prim:
                A = row[col][0]
                B = row[col][1]
                break
    return A, B


def get_A_B_displacement_coeff(h_prim, table):
    A_y, B_y, A_f, B_f = 0, 0, 0, 0

    if h_prim <= table[0][0]:
        A_y, B_y, A_f, B_f = table[0][1]
    else:
        for i in range(len(table)):
            row = table[i]
            if row[0] >= h_prim:
                row_0 = table[i - 1]
                row_1 = table[i]
                list_t = [0., 0., 0., 0.]
                for j in range(len(list_t)):
                    list_t[j] = row_1[1][j] + (row_0[1][j] - row_1[1][j]) / (row_1[0] - row_0[0]) * (h_prim - row_0[0])
                A_y, B_y, A_f, B_f = list_t
                break
    return A_y, B_y, A_f, B_f


# endregion
# region ////////////////////////////////////////GETTING DATA/////////////////////////////////////////////////////
def get_soil_parameters(comp_object, profile_id):
    z1 = 0.0
    soil_layers = []
    for layer in comp_object.getModelManager().getSoilProfileManager().getSoilProfiles()[profile_id].getLayers():
        params = layer.getSoil().params
        param_list = {
            'isCohesive': layer.getSoil().isCohesive(),
            'rho_s': params['PARAM_RHO_S'],
            'w_n': params['PARAM_W_N'],
            'rho': params['PARAM_RHO_N'],
            'rho_d': 100 * params['PARAM_RHO_S'] / (params['PARAM_W_N'] + 100),
            'fi_k': params['PARAM_PHI'],
            'c_k': params['PARAM_C_U'],
            't_k': params['COEFF_T'],
            'q_k': params['COEFF_Q'],
            'coeff_m': params['COEFF_M'],
            'alpha_i': params['ALPHA_I'],
            'z0': z1,
            'saturation': layer.saturation,
            'coeff_Ss': params['COEFF_Ss'],
            'coeff_Sp': params['COEFF_Sp'],
            'param_m0': params['PARAM_M_0'],
        }
        param_list['n'] = (params['PARAM_RHO_S'] - param_list['rho_d']) / params['PARAM_RHO_S']
        param_list['gamma_k_prim'] = params['PARAM_RHO_PRIM'] * 10 if layer.saturation else params['PARAM_RHO_N'] * 10
        z1 += layer.getHeight()
        param_list['z1'] = z1
        param_list['colour'] = layer.getSoil().getColour()
        if param_list['isCohesive'] is True:
            param_list['i_l'] = params['PARAM_I_L']
        else:
            param_list['i_d'] = params['PARAM_I_D']
        soil_layers.append(param_list)
    return soil_layers


def get_water_level(comp_object, profile_id):
    n = comp_object.getModelManager().getSoilProfileManager().getSoilProfiles()[profile_id].water_level
    z = 0.
    for i in range(n):
        z += comp_object.getModelManager().getSoilProfileManager().getSoilProfiles()[profile_id].getLayers()[i].getHeight()
    return z


def get_soils_names(comp_object, profile_id):
    names = []
    i = 1
    for layer in comp_object.getModelManager().getSoilProfileManager().getSoilProfiles()[profile_id].getLayers():
        names.append(str(i) + '. ' + layer.getSoil().getName())
        i += 1
    return names


def get_profiles_list(comp_object):
    profiles = []
    for id in comp_object.getModelManager().getSoilProfileManager().getSoilProfiles():
        profiles.append(comp_object.getModelManager().getSoilProfileManager().getSoilProfileById(id).name)

    return profiles


# endregion
# region ////////////////////////////////////////CALCULATIONS/////////////////////////////////////////////////////
def stress_displacements(soils, piles, z_w, V):
    V_stem_c = stem_weight(piles['L_stem'], piles['B_stem'], piles['d_stem'], z_w, piles['h_grunt'])  # kN ciezar wlasny trzonu char
    V_plat_c = plate_weigth(piles['L_f'], piles['B_f'], z_w, piles['h_grunt'], piles['H_f'])  # kN ciezar wlasny plyty fund
    V_pile_c = pile_weight(piles['L'], piles['D'], z_w, piles['h_grunt'], piles['H_f'])  # kN ciezar wlasny pala
    piles_quant = piles['n_s'] * piles['n_r']
    F_k = V + V_stem_c + V_plat_c + V_pile_c * piles_quant
    f_k = F_k / piles['B_f'] / piles['L_f']
    L_rem = piles['L'] + piles['H_f'] + piles['h_grunt']
    sig_v0zk = 0
    sig_layers = []
    for layer in soils:
        h = layer['z1'] - layer['z0']
        if L_rem > h:
            L_rem -= h
            sig_v0zk += h * layer['gamma_k_prim']
            z1 = layer['z1']
        elif L_rem < h and L_rem != 0:
            sig_v0zk += L_rem * layer['gamma_k_prim']
            z1 = layer['z0'] + L_rem
            L_rem = 0
        sig_layers.append({'z0': layer['z0'], 'z1': z1, 'sig': sig_v0zk})
    z = 0
    i = 0
    s = 0
    eta_layers = [{'z': 0, 'eta_s': 1, 'sig_v0zk': sig_v0zk, 'sig_vdzk': f_k, 's': 0}]
    temp_index = get_index_layer_from_deep_value(piles['L'] + piles['h_grunt'] + piles['H_f'], soils)
    M_0c = soils[temp_index]['param_m0']

    while True:
        i += 1
        z += 2
        it1 = z / piles['B_f']  # wlasne parametry skracajace
        it2 = piles['L_f'] / piles['B_f']
        eta_s = 2. / math.pi * (math.atan(it2 / (it1 * (1. + it2 ** 2. + it1 ** 2.) ** 0.5)) + it1 / it2 * ((1. + it1 ** 2.) ** 0.5 + (it2 ** 2. + it1 ** 2.) ** 0.5 - (1. + it2 ** 2. + it1 ** 2.) ** 0.5 - it1))
        sig_v0zk += 2 * soils[len(soils) - 1]['gamma_k_prim']
        sig_vdzk = f_k * eta_s
        sig_vdik = (sig_vdzk + eta_layers[i - 1]['sig_vdzk']) / 2
        s += sig_vdik * 2 / M_0c
        eta_layers.append({'z': z, 'eta_s': eta_s, 'sig_v0zk': sig_v0zk, 'sig_vdzk': sig_vdzk, 'sig_vdik': sig_vdik, 's': s})
        if sig_vdzk < 0.2 * sig_v0zk:
            break
    # for i in eta_layers:
    return {'stresses': sig_layers, 'stresses_under': eta_layers}



def plate_weigth(L_f, B_f, z_w, h_grunt, H_f):  # kN
    gamma_concrete = 24.53  # kN/m3 ciezar betonu
    gamma_concrete_prim = gamma_concrete - 10.  # kN/m3 ciezar betonu pod wyporem wody
    if h_grunt > z_w:  # woda powyzej plyty
        return L_f * B_f * H_f * gamma_concrete_prim
    elif (h_grunt + H_f) < z_w:  # woda ponizej plyty
        return L_f * B_f * H_f * gamma_concrete
    else:  # woda w plycie
        return L_f * B_f * ((z_w - h_grunt) * gamma_concrete + (H_f + h_grunt - z_w) * gamma_concrete_prim)


def pile_weight(L, D, z_w, h_grunt, H_f):  # kN
    gamma_concrete = 24.53  # kN/m3 ciezar betonu
    gamma_concrete_prim = gamma_concrete - 10.  # kN/m3 ciezar betonu pod wyporem wody
    A = math.pi * (D / 2.) ** 2.
    if (h_grunt + H_f) > z_w:  # woda powyzej pali
        return A * L * gamma_concrete_prim
    elif (h_grunt + H_f + L) < z_w:
        return A * L * gamma_concrete
    else:
        return A * ((h_grunt + H_f - z_w) * gamma_concrete + (h_grunt + H_f + L - z_w) * gamma_concrete_prim)


def stem_weight(L_stem, B_stem, d_stem, z_w, h_grunt):  # kN
    gamma_concrete = 24.53  # kN/m3 ciezar betonu
    gamma_concrete_prim = gamma_concrete - 10.  # kN/m3 ciezar betonu pod wyporem wody
    H_stem = h_grunt
    if h_grunt > z_w:  # slup caly w wodzie
        return (2. * B_stem + 2. * L_stem) * d_stem * H_stem * gamma_concrete_prim
    elif z_w > h_grunt:  # slup caly bez wody
        return (2 * B_stem + 2. * L_stem) * d_stem * H_stem * gamma_concrete
    else:
        return (2. * B_stem + 2. * z_w) * d_stem * H_stem * gamma_concrete + (2. * B_stem + 2. * (L_stem - z_w)) * d_stem * H_stem * gamma_concrete_prim



# def get_r_phi(r_phi_text):
#     return r_phis[r_phi_text]


def check_utilization(a, b):
    if a <= b:
        check_value = True
    else:
        check_value = False
    utilization_factor = a / b
    utilization_factor_percent = int(round(a / b, 2) * 100)
    return check_value, utilization_factor, utilization_factor_percent


def get_min_reinforced_area(A_c):
    if A_c <= 0.5:
        return 0.005 * A_c
    elif A_c <= 1.:
        return 0.0025
    else:
        return 0.0025 * A_c


def check_spacing_bars(n, D_axis_phi):
    # a = 1 / n * 2 * math.pi * D_axis_phi / 20
    if a >= 10. and a <= 40.:
        return a
    else:
        raise Exception('Too big/small spacing between bars')


def check_spiral_bars(r_phi, r_phi_sp, a_sp, a_sp_upper):
    if r_phi_sp >= 0.006 and r_phi_sp >= 0.25 * r_phi:
        pass
    else:
        raise Exception('Too small diameter of spiral rods')
    if a_sp >= 0.1 and a_sp <= 0.4:
        pass
    else:
        raise Exception('Too small spacing under foundation slab')
    if a_sp_upper >= 0.1 and a_sp_upper <= 0.4:
        pass
    else:
        raise Exception('Too small spacing in foundation slab')
    return True


def check_stiffening_bars(r_phi, r_phi_p, a_p):
    if r_phi_p >= r_phi:
        pass
    else:
        raise Exception('Too small diameter of stiffening rods')
    if a_p <= 4.:
        return True
    else:
        raise Exception('Too big spacing between stiffening rods')


def check_distance_insert():
    if d_w < d_ext_int / 2:
        return True
    else:
        raise Exception('Too big diameter of distance insert')


def calculate_polynomial(coeff):
    x = sorted(np.roots(coeff))  # w m
    return x[-1]


def concrete_compression_calculation(N_Ed, M_Ed, b, a, f_cd, f_yd, E_s, c_class):
    N_Ed = abs(N_Ed)
    eta = 1.
    h = b
    d = h - a
    lambda_concr = 0.8
    e_cu3 = concrete_dict[c_class]['e_cu3'] / 1000.
    e_c3 = concrete_dict[c_class]['e_c3'] / 1000.
    a_1 = a
    a_2 = a
    e = abs(M_Ed / N_Ed)
    e_s1 = e + 0.5 * h - a_1
    e_s2 = e - 0.5 * h + a_2
    x_min_neg_yd = e_cu3 * a_2 / (e_cu3 + f_yd / E_s)
    x_min_yd = e_cu3 * a_2 / (e_cu3 - f_yd / E_s)
    x_0 = (1. - e_c3 / e_cu3) * h
    x_lim = e_cu3 * d / (e_cu3 + f_yd / E_s)
    x = N_Ed / (lambda_concr * eta * f_cd * b)
    e_yd = e_cu3 * (d - x) / x
    x_yd_max = (e_yd * x_0 - e_c3 * a_2) / (e_yd - e_c3)
    if x <= x_lim:
        # print('x<=x_lim')
        sigma_s1 = f_yd

        if x < x_min_yd:
            # print('x < x_min_yd')
            A = lambda_concr * (f_yd - e_cu3 * E_s)
            B = -2. * (f_yd * d - e_cu3 * E_s * a_2 * (1. + 0.5 * lambda_concr))
            C = 2. * (N_Ed * (f_yd * e_s1 - e_cu3 * E_s * e_s2) / (lambda_concr * eta * f_cd * b) - e_cu3 * E_s * a_2 ** 2)
            D = 2. * N_Ed / (lambda_concr * eta * f_cd * b) * (e_cu3 * E_s * a_2 * e_s2)
            coeff = [A, B, C, D]
            x = calculate_polynomial(coeff)
            if x <= x_min_neg_yd:
                # print('x <= x_min_neg_yd')
                sigma_s2 = -f_yd

                x = ((d + a_2) - ((d + a_2) ** 2. - 4. * N_Ed * (e_s1 + e_s2) / (eta * f_cd * b)) ** 0.5) / (2. * lambda_concr)
            else:
                # print('x > x_min_neg_yd')
                sigma_s2 = e_cu3 * (x - a_2) / x * E_s
        else:
            # print('x > x_min_yd')
            sigma_s2 = f_yd

    # lewa odnoga
    else:
        # print "x>x_lim"
        sigma_s2 = f_yd
        A = lambda_concr * (f_yd + e_cu3 * E_s)
        B = -2. * (f_yd * a_2 + e_cu3 * E_s * d * (1. + 0.5 * lambda_concr))
        C = 2. * (N_Ed * (f_yd * e_s2 + e_cu3 * E_s * e_s1) / (lambda_concr * eta * f_cd * b) + e_cu3 * E_s * d ** 2.)
        D = -2. * N_Ed / (lambda_concr * eta * f_cd * b) * e_cu3 * E_s * d * e_s1

        coeff = [A, B, C, D]
        x = calculate_polynomial(coeff)
        # print x
        if x > h:
            # print "x>h"
            A = lambda_concr * (f_yd + e_c3 * E_s)
            B = -2. * (f_yd * (a_2 + 0.5 * lambda_concr * x_0) + e_c3 * E_s * d * (1. + 0.5 * lambda_concr))
            C = 2. * (N_Ed * (f_yd * e_s2 + e_c3 * E_s * e_s1) / (lambda_concr * eta * f_cd * b) + e_c3 * E_s * d ** 2. + f_yd * a_2 * x_0)
            D = -2. * N_Ed / (lambda_concr * eta * f_cd * b) * (e_c3 * E_s * d * e_s1 + f_yd * x_0 * e_s2)

            coeff = [A, B, C, D]
            x = calculate_polynomial(coeff)

            if x > h / lambda_concr:
                F_1 = N_Ed * e_s1 - eta * f_cd * b * h * (0.5 * h - a_1)
                F_2 = N_Ed * e_s2 - eta * f_cd * b * h * (0.5 * h - a_2)
                x = (e_c3 * E_s * d * F_1 + f_yd * x_0 * F_2) / (e_c3 * E_s * F_1 + f_yd * F_2)
                if x > h / lambda_concr and x < x_yd_max:
                    pass
                else:
                    F_1 = N_Ed * (e_s1 * d + e_s2 * a_2) + eta * f_cd * b * h * 0.5 * ((a_1 - a_2) * (d + a_2) - (d - a_2) ** 2.)
                    F_2 = N_Ed * (e_s1 + e_s2) + eta * f_cd * b * h * (a_1 - a_2)
                    x = F_1 / F_2
            sigma_s1 = e_c3 * (d - x) * E_s / (x - x_0)
            sigma_s2 = e_c3 * (x - a_2) * E_s / (x - x_0)
        else:
            # print "x<H"
            sigma_s1 = e_cu3 * (d - x) * E_s / x
    # print N_Ed, e_s2, eta, f_cd, b, lambda_concr, x, lambda_concr, x, a_2, sigma_s1, d, a_2
    A_s = (N_Ed * e_s2 + eta * f_cd * b * lambda_concr * x * (0.5 * lambda_concr * x - a_2)) / (sigma_s1 * (d - a_2))
    return A_s


# Nosnosc elementu na scinanie bez zbrojenia
def shear_resistance(N_Ed, b, a, r_phi, n, f_cd, f_ck):
    h = b
    d = h - a
    gamma_conc = 1.427
    C_Rd_c = 0.18 / gamma_conc
    d = d  # z przypadku a-a, w m
    k = min(1 + (0.2 / d) ** 0.5, 2.)
    # pole przekroju rozciaganego
    A_sl = n / 2. * math.pi * r_phi ** 2. / 4.
    # stopien zbrojenia przekroju
    rho_l = min(A_sl / (b * d), 0.02)
    # naprezenia sciskajace w przekroju
    sigma_cp = min(N_Ed / b ** 2., 0.2 * f_cd)
    v_min = 0.035 * k ** (1.5) * (f_ck / 10 ** 6) ** 0.5
    # Wartosc obliczeniowa nosnosci na scinanie
    return max((C_Rd_c * k * (100. * rho_l * f_ck / 10. ** 6.) ** (1. / 3.) + 0.15 * sigma_cp / 10. ** 6.) * b * d, (v_min + 0.15 * sigma_cp / 10. ** 6.) * b * d) * 10. ** 6.


# Dlugosc zakotwienia granicznego naprezenia przyczepnosci dla pretow zebrowych
def anchorage_length():
    # wspolczynnik zalezny od jakosci warunkow przyczepnosci i pozycji w czasie betonowania
    eta_1 = 1.
    # wspolczynnik zalezny od srednicy preta
    eta_2 = 1. if r_phi <= 0.032 else (0.132 - r_phi) * 10.
    # obliczeniowa wytrzymalosc betonu na rozciaganie
    f_ctd = 0.5 * f_ctm
    # wartosc obliczeniowa granicznego naprezenia przyczepnosci dla pretow zebrowwanych
    f_bd = 2.25 * eta_1 * eta_2 * f_ctd
    # minimalna dlugosc zakladu
    return r_phi * f_yd / (4. * f_bd)


def weight_soil_above(B_f, L_f, h_soil_above, soils):
    V_soil_c = 0.
    for layer in soils:
        if h_soil_above <= layer['z1']:
            V_soil_c += B_f * L_f * (h_soil_above - layer['z0']) * layer['gamma_k_prim']
            break
        elif h_soil_above >= layer['z1']:
            V_soil_c += B_f * L_f * (layer['z1'] - layer['z0']) * layer['gamma_k_prim']
    return V_soil_c


def calculate_vertical_forces(B_f, L_f, H_f, L, D, n, h_soil_above, soils, z_w, L_stem, B_stem, d_stem, V_G_c, V_Q_c):
    gamma_G = 1.35  # for constant forces
    gamma_Q = 1.5  # for variables forces

    # weight of ground above slab
    V_soil_c = weight_soil_above(B_f, L_f, h_soil_above, soils)
    # weight of stem
    V_stem_c = stem_weight(L_stem, B_stem, d_stem, z_w, h_soil_above)

    # weight of slab
    V_slab_c = plate_weigth(L_f, B_f, z_w, h_soil_above, H_f)

    # weight of pile
    V_pile_c = pile_weight(L, D, z_w, h_soil_above, H_f)

    # design force of vertical stable forces
    V_G_d = gamma_G * (V_G_c + n * V_pile_c + V_slab_c + V_stem_c + V_soil_c)

    # design force of vertical variable forces
    V_Q_d = gamma_Q * V_Q_c
    return V_soil_c + V_stem_c + V_slab_c + V_pile_c + V_G_c + V_Q_c, V_G_d + V_Q_d, V_G_d, V_Q_d


def calculate_forces(G_c, Q_c):
    gamma_G = 1.35  # for constant forces
    gamma_Q = 1.5  # for variables forces

    # design force of stable forces
    G_d = G_c * gamma_G

    # design force of variable forces
    Q_d = Q_c * gamma_Q

    return G_c + Q_c, G_d + Q_d


def calculate_critical_depth(D):
    h_ci = 10. * (D / 0.4) ** 0.5
    return h_ci, 1.3 * h_ci


def calculate_comp_level_load_bearing_loads(z_olbs, soils, load_bearing_layer):
    h_z_V = 0.
    gamma_k = soils[load_bearing_layer]['gamma_k_prim']
    for layer in soils:
        h_z_V += (layer['z1'] - layer['z0']) * layer['gamma_k_prim']
        if layer['z1'] >= z_olbs:
            break
    return 0.65 * h_z_V / gamma_k


# get properieties of layer from depth value
def get_layer_from_deep_value(x, soils):
    for layer in soils:
        if x <= layer['z1']:
            return layer
    if x > soils[-1]['z1']:
        return soils[-1]


# get index of layer from depth value
def get_index_layer_from_deep_value(x, soils):
    for i in range(len(soils)):
        if x <= soils[i]['z1']:
            return i
    if x > soils[-1]['z1']:
        return len(soils)


def calculate_q_k(soils, h_ci, h_ci_prim, z_colbs_V, depth_of_foundation):
    layer = get_layer_from_deep_value(depth_of_foundation, soils)
    q_c = layer['q_k']
    coeff_Sp = soils[get_index_layer_from_deep_value(depth_of_foundation, soils)]['coeff_Sp']

    if (10. + z_colbs_V) >= depth_of_foundation:
        return q_c * coeff_Sp
    else:
        return q_c - (q_c - 10. * q_c / h_ci) * (h_ci_prim -
                                                depth_of_foundation +
                                                z_colbs_V) / (h_ci_prim - 10.)


def area_of_pile(D):
    return math.pi * (D / 2.) ** 2.  # [m2]


def area_of_piles_side(D, h):
    return 2 * math.pi * (D / 2.) * h  # [m2]


def calculate_load_capacity_under_pile(q_b_c, D):
    A = area_of_pile(D)
    gamma_b = 1.1
    return A * q_b_c / gamma_b


# coefficient taking into account the number of piles in the parallel row to the direction of bending
def get_coeff_K(n_r, r_0, D):
    K = 0.8

    if r_0 <= 3 * D:
        if n_r == 2:
            K = 0.9
        elif n_r == 3:
            K = 0.85
        elif n_r == 4:
            K = 0.8
        elif n_r == 5:
            K = 0.75
        elif n_r >= 6:
            K = 0.70
    else:
        if n_r == 2:
            K = 0.95
        elif n_r == 3:
            K = 0.9
        elif n_r == 4:
            K = 0.85
        elif n_r == 5:
            K = 0.8
        elif n_r >= 6:
            K = 0.75

    return K


def get_coeff_m1(r, R):
    # wspolczynnik redukcyjny uwzgledniajacy nakladanie sie na siebie stref naprezen wokol poszczegolnych palli
    r_R = r / R

    # wartosc wspolczynnika korekcyjnego
    if r_R >= 1.85:
        m_1 = 1
    elif r_R >= 1.55:
        m_1 = 0.95
    elif r_R >= 1.3:
        m_1 = 0.9
    elif r_R >= 1.0:
        m_1 = 0.8
    elif r_R >= 0.7:
        m_1 = 0.65
    else:
        m_1 = 0.45

    return m_1


# returns
def get_layer_with_positive_friction(load_bearing_layer, soils, depth_of_foundation):
    selected_soils = []
    z_load_bearing = soils[load_bearing_layer]['z0']

    for layer in soils:
        if layer['z0'] >= z_load_bearing:
            if layer['z1'] < depth_of_foundation:
                selected_soils.append(
                    {'z0': layer['z0'], 'z1': layer['z1'], 't_k': layer['t_k'],
                     'coeff_Ss': layer['coeff_Ss'],
                     'coeff_Sp': layer['coeff_Sp'], })
            else:
                selected_soils.append(
                    {'z0': layer['z0'], 'z1': depth_of_foundation,
                     't_k': layer['t_k'], 'coeff_Ss': layer['coeff_Ss'],
                     'coeff_Sp': layer['coeff_Sp'], })
        if layer['z1'] >= depth_of_foundation:
            break

    return selected_soils


def calculate_load_capacity_along_side_of_pile(load_bearing_layer, soils, D, z_colbs_V, depth_of_foundation):
    gamma_s = 1.1
    selected_soils = get_layer_with_positive_friction(load_bearing_layer, soils, depth_of_foundation)

    # przypadek kiedy pal jest krotszy niz poczatek 1 gruntu nosnego
    if selected_soils >= depth_of_foundation:
        return 0.

    temp_z = 5. + z_colbs_V - selected_soils[0]['z0']
    data = []

    for layer in selected_soils:
        if layer['z0'] < z_colbs_V + 5.:
            if temp_z > 0:
                if temp_z >= (layer['z1'] - layer['z0']):
                    h_s = layer['z1'] - layer['z0']
                    temp_z -= h_s
                    data.append({
                        't_c': (0.5 * layer['t_k'] * (1. + 0.2 * (layer['z0'] - z_colbs_V))),
                        'coeff_Ss': layer['coeff_Ss'],
                        'coeff_Sp': layer['coeff_Sp'],
                        'x0': layer['z0'],
                        'x1': layer['z1'],
                    })
                else:
                    h_s = temp_z

                    data.append({
                        't_c': (0.5 * layer['t_k'] * (1. + 0.2 * (layer['z0'] - z_colbs_V))),
                        'coeff_Ss': layer['coeff_Ss'],
                        'coeff_Sp': layer['coeff_Sp'],
                        'x0': layer['z0'],
                        'x1': (layer['z0'] + temp_z),
                    })

                    temp_z -= h_s

                    x_0 = data[-1]['x1']
                    data.append({
                        't_c': layer['t_k'],
                        'coeff_Ss': layer['coeff_Ss'],
                        'coeff_Sp': layer['coeff_Sp'],
                        'x0': x_0,
                        'x1': layer['z1'],
                    })

            elif temp_z <= 0.:
                x_0 = data[-1]['x1']
                data.append({
                    't_c': layer['t_k'],
                    'coeff_Ss': layer['coeff_Ss'],
                    'coeff_Sp': layer['coeff_Sp'],
                    'x0': x_0,
                    'x1': layer['z1'],
                })
        elif layer['z0'] >= z_colbs_V + 5.:
            data.append({
                't_c': layer['t_k'],
                'coeff_Ss': layer['coeff_Ss'],
                'coeff_Sp': layer['coeff_Sp'],
                'x0': layer['z0'],
                'x1': layer['z1'],
            })

    for i in range(len(data)):
        data[i]['q_s_c'] = (data[i]['t_c'] * data[i]['coeff_Ss'])
        data[i]['A_s'] = math.pi * D * (data[i]['x1'] - data[i]['x0'])


    R_s_c = 0.
    for i in range(len(data)):
        R_s_c += data[i]['q_s_c'] * data[i]['A_s']

    R_s_d = R_s_c / gamma_s

    return R_s_d


# zwraca grunty z tarciem ujemnym
def get_layers_with_negative_friction(load_bearing_layer, soils, H_f, h_soil_above):
    z_load_bearing = soils[load_bearing_layer]['z0']
    beginning_of_piles = h_soil_above + H_f

    first_negative_layer = get_index_layer_from_deep_value(beginning_of_piles,
                                                           soils)
    selected_soils = []

    for i in range(len(soils)):
        if soils[i]['z0'] > z_load_bearing:
            break
        elif i >= first_negative_layer:
            if soils[i]['z0'] <= beginning_of_piles:
                if soils[i]['z1'] <= z_load_bearing:
                    selected_soils.append(
                        {'z0': beginning_of_piles,
                         'z1': soils[i]['z1'],
                         't_k': soils[i]['t_k'],
                         'gamma_k_prim': soils[i]['gamma_k_prim'],
                         'alpha_i': soils[i]['alpha_i'],
                         'coeff_Ss': soils[i]['coeff_Ss'],
                         'coeff_Sp': soils[i]['coeff_Sp'], })

                else:
                    selected_soils.append(
                        {'z0': beginning_of_piles,
                         'z1': z_load_bearing,
                         't_k': soils[i]['t_k'],
                         'gamma_k_prim': soils[i]['gamma_k_prim'],
                         'alpha_i': soils[i]['alpha_i'],
                         'coeff_Ss': soils[i]['coeff_Ss'],
                         'coeff_Sp': soils[i]['coeff_Sp'], })

            else:
                if soils[i]['z1'] <= z_load_bearing:
                    selected_soils.append(
                        {'z0': soils[i]['z0'],
                         'z1': soils[i]['z1'],
                         't_k': soils[i]['t_k'],
                         'gamma_k_prim': soils[i]['gamma_k_prim'],
                         'alpha_i': soils[i]['alpha_i'],
                         'coeff_Ss': soils[i]['coeff_Ss'],
                         'coeff_Sp': soils[i]['coeff_Sp'], })

                elif soils[i]['z1'] > z_load_bearing:
                    selected_soils.append(
                        {'z0': soils[i]['z0'],
                         'z1': z_load_bearing,
                         't_k': soils[i]['t_k'],
                         'gamma_k_prim': soils[i]['gamma_k_prim'],
                         'alpha_i': soils[i]['alpha_i'],
                         'coeff_Ss': soils[i]['coeff_Ss'],
                         'coeff_Sp': soils[i]['coeff_Sp'], })

    return selected_soils


# calculation only negative friction
def calculate_negative_friction(load_bearing_layer, soils, D, H_f, h_soil_above):
    gamma_G = 1.35

    selected_soils = get_layers_with_negative_friction(load_bearing_layer, soils, H_f, h_soil_above)

    T_n_d = 0.
    index_t = 0

    for layer in reversed(selected_soils):
        if layer['z1'] - layer['z0'] > 0.001:
            if index_t == 0:
                h_s = layer['z1'] - layer['z0']
                A_s = math.pi * D * h_s
                T_n_d += A_s * layer['t_k']
                index_t = 1
            else:
                h_s = layer['z1'] - layer['z0']
                A_s = math.pi * D * h_s
                T_n_d += A_s * layer['t_k'] * layer['coeff_Ss'] * gamma_G

    return T_n_d


# calculation of center of mass for foundations slab with piles
def calculate_center_of_mass(D, r, n_s, r_kr, L_f):
    x = []

    for i in range(n_s):
        if i == range(n_s)[0]:
            x.append(-(L_f / 2 - D / 2 - r_kr))
        elif i == range(n_s)[-1]:
            x.append((L_f / 2 - D / 2 - r_kr))
        else:
            x.append(x[i - 1] + r)

    return x


# calculation of maximum force for 1 pile (vertical forces)
def calculate_piles_resistance_vertical(D, n, r, n_s, r_kr, L_f, V_all_d, M_all_d):
    try:
        x_gecen = calculate_center_of_mass(D, r, n_s, r_kr, L_f)
    except:
        x_gecen[0] = 1

    if x_gecen[0] <= 0:
        x_gecen[0] = 1

    F_c_d = []
    # wartosc obliczeniowa osiowego obciazenia pala wciskanego
    for i in range(n_s):
        F_c_d.append((V_all_d / n) + (M_all_d * x_gecen[i] / sum(map(lambda x: x * x, x_gecen))))

    F_c_d = max(F_c_d)

    return F_c_d


# calculation of weight of surroadings ground
def calculate_weight_cooperative_ground(load_bearing_layer, soils, h_soil_above, H_f, L_f, B_f, r_kr):
    Q_T_n_c = 0

    selected_soils = get_layers_with_negative_friction(load_bearing_layer, soils, H_f, h_soil_above)

    try:
        alpha = math.radians(selected_soils[0]['alpha_i'])

        h_1 = 0.
        for layer in selected_soils[:-2]:  ### CZEMU TO TAK GLUPIO ZWRACA - SPYTAJ SIE
            h_1 += layer['z1'] - layer['z0']

        B_T_n = B_f - 2 * r_kr + 2 * h_1 * math.tan(alpha)  # szerokosc gruntu wspolpracujacego
        L_T_n = L_f - 2 * r_kr + 2 * h_1 * math.tan(alpha)  # dlugosc gruntu wspolpracujacego

        for layer in selected_soils:
            Q_T_n_c += B_T_n * L_T_n * layer['gamma_k_prim'] * (layer['z1'] - layer['z0'])
    except:
        pass

    if Q_T_n_c <=0.:
        Q_T_n_c = 0.1

    return Q_T_n_c


def calculate_load_bearing_capacity_of_one_pile(L, D, r, z_w, B_f, L_f, H_f, h_soil_above, soils, R_c_d_cal):
    gamma_G = 1.35

    # calculate weight of elements in the range of r
    V_ground_c = weight_soil_above(B_f, L_f, h_soil_above, soils) * r ** 2
    V_slab_c = plate_weigth(L_f, B_f, z_w, h_soil_above, H_f) * r ** 2
    # weight of pile
    V_pile_c = pile_weight(L, D, z_w, h_soil_above, H_f)

    # obliczeniowa nosnosc pojedycznego pala pomniejszona o ciezar wlasny
    R_c_d_cal_1 = R_c_d_cal - (V_ground_c + V_slab_c + V_pile_c) * gamma_G

    return R_c_d_cal_1


def calculate_load_bearing_capacity_of_group_of_piles(load_bearing_layer, soils, r, D, n, depth_of_foundation, h_z_V, R_b_d, R_s_d, T_n_d):
    E_cm = 32000000.  # [kPa]
    # promien strefy naprezen
    R = D / 2.

    selected_soils = []
    z_load_bearing = soils[load_bearing_layer]['z0']
    for layer in soils:
        if layer['z1'] >= h_z_V:
            if layer['z0'] >= z_load_bearing:
                if layer['z1'] < depth_of_foundation:
                    selected_soils.append(
                        {'z0': layer['z0'],
                         'z1': layer['z1'],
                         'alpha_i': layer['alpha_i'],
                         'coeff_Ss': layer['coeff_Ss'],
                         'coeff_Sp': layer['coeff_Sp'], })
                else:
                    selected_soils.append(
                        {'z0': layer['z0'],
                         'z1': depth_of_foundation,
                         'alpha_i': layer['alpha_i'],
                         'coeff_Ss': layer['coeff_Ss'],
                         'coeff_Sp': layer['coeff_Sp'], })
            else:
                if layer['z1'] < depth_of_foundation:
                    selected_soils.append(
                        {'z0': h_z_V,
                         'z1': layer['z1'],
                         'alpha_i': layer['alpha_i'],
                         'coeff_Ss': layer['coeff_Ss'],
                         'coeff_Sp': layer['coeff_Sp'], })
                else:
                    selected_soils.append(
                        {'z0': h_z_V,
                         'z1': depth_of_foundation,
                         'alpha_i': layer['alpha_i'],
                         'coeff_Ss': layer['coeff_Ss'],
                         'coeff_Sp': layer['coeff_Sp'], })
        if layer['z1'] >= depth_of_foundation:
            break

    for layer in selected_soils:
        R += (layer['z1'] - layer['z0']) * math.tan(math.radians(layer['alpha_i']))

    m_1 = get_coeff_m1(r, R)

    # load bearing capacity of group of piles
    R_c_d_PG = n * ((R_b_d + m_1 * R_s_d - T_n_d))

    return R_c_d_PG


# calculate stiffness of pile
def get_stiffness_of_pile(D):
    # sieczny modul sprezystosci betonu
    E_cm = 32.  # [GPa]
    # moment bezwladnosci przekroju poprzecznego pala
    J = math.pi * (D * 100.) ** 4. / 64.

    # sztywnosc przekroju poprzecznego
    EJ = E_cm * 10. ** 6. * J * 10. ** (-8.)

    return EJ


def calculate_deformation_alpha(soils, depth_of_foundation, D, r, n_r, z_colbs_H):
    r_0 = r  # rozstaw pali w kierunku rownoleglym do zginania
    r_90 = r  # rozstaw pali w kierunku prostopadlym do zginania

    K = get_coeff_K(n_r, r_0, D)

    # obliczeniowa srednica pala
    D_p = []
    if D <= 1.:
        D_p.append(0.9 * (1.5 * D + 0.5))
    else:
        D_p.append(0.9 * (D + 1.) * K)
    D_p.append(r_90)

    D_p = min(D_p)

    h_w = 2. * (D_p + 1.)
    z_hw = z_colbs_H + h_w

    z_index = get_index_layer_from_deep_value(depth_of_foundation, soils)

    if soils[z_index]['z0'] >= depth_of_foundation or soils[z_index]['z0'] <= z_colbs_H:
        m = soils[z_index]['coeff_m']
    else:
        if z_hw > soils[z_index]['z0']:
            # w obrebie glebokosci hw wystepuja warstwy o roznej odksztalcalnosci
            h_above = soils[z_index]['z0'] - z_colbs_H
            # wspolczynnik odksztalcalnosci gornej warstwy gruntu
            m_above = soils[z_index - 1]['coeff_m']
            m_under = soils[z_index]['coeff_m']
            m = (m_above * h_above * (2. * h_w - h_above) + m_under * (h_w - h_above) ** .2) / (h_w) ** 2.
        else:
            m = soils[z_index]['coeff_m']

    EJ = get_stiffness_of_pile(D)
    alpha_deformation = (m * D_p / EJ) ** (1. / 5.)  # [1/m]

    return z_hw, D_p, alpha_deformation


def calculate_displacement(n, D, H_all_c, H_all_d, z_colbs_H, h_soil_above, H_f, h_prim, h_constr, alpha_deformation):

    H_1_c = H_all_c / n  # [kN]
    H_1_d = H_all_d / n  # [kN]

    h_H = z_colbs_H - (h_soil_above + H_f)

    M_1_c = H_1_c * h_H
    M_1_d = H_1_d * h_H

    A_y, B_y, A_f, B_f = get_A_B_displacement_coeff(h_prim, table_A_B_displacement_coeff)

    EJ = get_stiffness_of_pile(D)

    # przemieszczenia poziome na wysokosci obliczeniowego poziomu stropu gruntow nosnych
    y_0 = (A_y * H_1_c) / (alpha_deformation ** 3. * EJ) + (B_y * M_1_c) / (alpha_deformation ** 2. * EJ)

    # kat obrotu osi pala na wysokosci obliczeniowego poziomu stropu gruntow nosnych
    phi_0 = (A_f * H_1_c) / (alpha_deformation ** 2. * EJ) + (B_f * M_1_c) / (alpha_deformation * EJ)
    # przemieszczeni poziome glowicy slupa
    y_constr = y_0 + (h_H + h_constr) * phi_0
    return y_0, phi_0, y_constr, H_1_d, h_H


def calculate_first_sigma_cohesive(z_load_bearing, soils):
    first_sigma = 0.
    for layer in soils:
        if layer['z1'] <= z_load_bearing:
            first_sigma += (layer['z1'] - layer['z0']) * layer['gamma_k_prim']
        else:
            first_sigma += (z_load_bearing - layer['z0']) * layer['gamma_k_prim']
        if layer['z1'] >= z_load_bearing:
            break

    return first_sigma


def calculate_first_sigma_noncohesive(z, z_colbs_H, z_load_bearing, soils):
    first_sigma = 0.
    for layer in soils:
        if layer['z1'] <= z_load_bearing:
            first_sigma += (layer['z1'] - layer['z0']) * layer['gamma_k_prim']
        else:
            first_sigma += (z_colbs_H + z - layer['z0']) * layer['gamma_k_prim']
        if layer['z1'] >= z_load_bearing + z:
            break

    return first_sigma


def calculate_moment_side_pressure(soils, load_bearing_layer, depth_of_foundation, z_colbs_H, D_p, H_1_d, h_H, alpha_deformation, h_prim, z_hw):
    list_z_prim = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    coeff_S_n = 0.9

    index_t_1 = 0
    index_t_2 = 0

    z_load_bearing = soils[load_bearing_layer]['z0']

    data = []

    for i in range(len(list_z_prim)):
        z_prim = list_z_prim[i]
        z = z_prim / alpha_deformation
        if h_prim <= 3.0:
            col = 1
        elif h_prim < 5.0:
            col = 2
        else:
            col = 3
        A_m, B_m = get_data_from_table(col, z_prim, table_A_B_bending_calculations)
        A_pH, B_pM = get_data_from_table(col, z_prim, table_A_B_side_calculations)

        soil_layer = get_layer_from_deep_value(z_load_bearing + z + 0.001, soils)
        if soil_layer['isCohesive'] is True:
            coeff_beta = 0.7
        else:
            coeff_beta = 0.8

        z_Dp = z / D_p
        phi_k = soil_layer['fi_k']
        coeff_K_c = bilinear_interpolation(x_tab, y_K_c_tab, K_c, z_Dp, phi_k)
        coeff_K_q = bilinear_interpolation(x_tab, y_K_q_tab, K_q, z_Dp, phi_k)

        param_c = soil_layer['c_k']

        if param_c > 0:
            if index_t_1 == 0:
                sigma_v_0_z_c = calculate_first_sigma_cohesive(z_load_bearing, soils)
                index_t_1 = 1
            else:
                try:
                    sigma_v_0_z_c = data[-1]['sigma_v_0_z_c'] + (z - data[-1]['z']) * soil_layer['gamma_k_prim']
                except:
                    print('blad 1.1 - side pressure')
        else:
            if index_t_2 == 0:
                sigma_v_0_z_c = calculate_first_sigma_noncohesive(z, z_colbs_H, z_load_bearing, soils)
                index_t_2 = 1
            else:
                try:
                    sigma_v_0_z_c = data[-1]['sigma_v_0_z_c'] + (z - data[-1]['z']) * soil_layer['gamma_k_prim']
                except:
                    print('blad 2.1 - side pressure')

        M_1_d = H_1_d * (h_H + z)  # TODO: SPRAWDZ JEDNOSTKI
        p_z_d = (A_pH * H_1_d * alpha_deformation) / D_p + (B_pM * M_1_d * alpha_deformation ** 2) / D_p
        r_z_d = coeff_beta * coeff_S_n * (sigma_v_0_z_c * coeff_K_q + param_c * coeff_K_c)
        p_zd_r_d = p_z_d / r_z_d * 100.  # [%]
        M_z_d = (A_m * H_1_d) / alpha_deformation + B_m * M_1_d

        data.append({
            'z_prim': z_prim,
            'z': z,
            'A_m': A_m,
            'B_m': B_m,
            'A_pH': A_pH,
            'B_pM': B_pM,
            'coeff_beta': coeff_beta,
            'z_Dp': z_Dp,
            'phi_k': phi_k,
            'coeff_K_c': coeff_K_c,
            'coeff_K_q': coeff_K_q,
            'param_c': param_c,
            'sigma_v_0_z_c': sigma_v_0_z_c,
            'M_1_d': M_1_d,
            'p_z_d': p_z_d,
            'r_z_d': r_z_d,
            'p_zd_r_d': p_zd_r_d,
            'M_z_d': M_z_d,
        })

    M_z_d_max = max([x['M_z_d'] for x in data])
    seq = [x['p_zd_r_d'] for x in data]
    p_zd_r_d_max = max(seq)
    temp_index = seq.index(p_zd_r_d_max)
    r_z_d_max = data[temp_index]['r_z_d']

    return M_z_d_max, p_zd_r_d_max, r_z_d_max


# endregion
# region ////////////////////////////////////////CALCULATING REINFORCEMENT OF SLAB//////////////////////////////////////


def calculate_area_reinforcement(A_s, spacing):
    return math.pi * (A_s / 2.) ** 2. / spacing


# endregion
# region ////////////////////////////////////////CHECKING//////////////////////////////////////////////////////////
def check_minimal_degree_reinforcement(r_phi, n, D):
    #przyjecie powierzchni przekroju jako kwadrat
    B = D / 2. ** (0.5)
    A_c = B**2.  # m2
    A_s_min = get_min_reinforced_area(A_c)
    A_s_prov = n * math.pi * r_phi ** 2. / 4.
    return A_s_prov >= A_s_min, round(A_s_prov * 10000., 2), round(A_s_min * 10000., 2)


def check_piles_spacing():
    pass


def check_piles_length():
    pass


def check_piles_place_in_supporting_layer():
    pass


# endregion
# region ////////////////////////////////////////DRAWING//////////////////////////////////////////////////////////


def draw_pile_section(canvas, piles):
    coord = piles['D'] * 100 / 2.
    coord2 = piles['D'] * 120 / 2.
    canvas.create_rectangle(-coord2, -coord2, coord2, coord2, fill='', outline='', tags=(soMetricCanvas.TAB_EXTERIOR_BOUNDARY, soMetricCanvas.TAB_FIT_TO_VIEW))

    if piles['is_D_f']:
        coord3 = piles['D_f'] * 100/2.
        canvas.create_oval(-coord3, -coord3, coord3, coord3, fill='grey', **opts)
        canvas.create_oval(-coord, -coord, coord, coord, dash=(10, 20), **opts)
    else:
        canvas.create_oval(-coord, -coord, coord, coord, fill='grey', **opts)
    draw_bars(canvas, piles)
    canvas.draw_dimension(0, -coord, 0, coord, 0, "D", end_dot_size=dot)


def draw_bars(canvas, piles):
    n = piles['reinf_n']
    if n > 0.:
        scale = 100.
        r_phi = piles['r_phi'] * scale
        if piles['is_D_f']:
            D = piles['D_f'] * scale
        else:
            D = piles['D'] * scale
        c = piles['c'] * scale
        r_phi_s = piles['r_phi_s'] * scale
        r = D / 2. - c - r_phi_s - r_phi / 2.
        # strzemiona outter
        canvas.create_oval(-r - r_phi_s, -r - r_phi_s, r + r_phi_s, r + r_phi_s, fill='grey',**opts)
        # strzemiona inner
        canvas.create_oval(-r, -r, r, r, fill='grey', **opts)
        alfa = 360. / n
        r -= r_phi / 2.
        for i in range(int(n)):
            beta = (i) * (alfa) + alfa / 2.
            x = r * math.cos(math.radians(beta))
            y = r * math.sin(math.radians(beta))
            canvas.create_oval(x - r_phi / 2., y + r_phi / 2., x + r_phi / 2., y - r_phi / 2., fill='grey', **opts)


def draw_soils(canvases, soils, x_size, y_size):
    for canvas in canvases:
        canvas.create_rectangle(-x_size / 2., y_size / 2., x_size / 2. + 5., y_size / 2. - 100., fill='sky blue')
        scale = 10.
        x0 = -x_size / 2.
        y0 = y_size / 2. - 100.
        for layer in soils:
            canvas.create_rectangle(x0, y0 - layer['z0'] * scale, x_size / 2. + 5, y0 - layer['z1'] * scale, fill=layer['colour'])


def draw_piles_view(canvas1, canvas2, piles, y_size):
    scale = 10.
    B_f = piles['B_f'] * scale
    L_f = piles['L_f'] * scale
    r_kr = piles['r_kr'] * scale
    r = piles['r'] * scale
    D = piles['D'] * scale
    H_f = piles['H_f'] * scale
    L = piles['L'] * scale
    h_grunt = piles['h_grunt'] * scale
    L_stem = piles['L_stem'] * scale
    B_stem = piles['B_stem'] * scale
    d_stem = piles['d_stem'] * scale
    y0 = y_size / 2. - 100.
    # piles.update((x, y * 10.) for x, y in piles.items())    #multiply everything by scale
    canvas1.create_rectangle(-B_stem / 2., y0 - h_grunt, B_stem / 2., y0 - h_grunt + d_stem, fill='grey')
    canvas1.create_rectangle(-B_f / 2., y0 - h_grunt, B_f / 2., y0 - h_grunt - H_f, fill='grey')
    for i in range(int(piles['n_r'])):
        x1 = -B_f / 2. + r_kr + i * r
        x2 = -B_f / 2. + r_kr + i * r + D
        canvas1.create_rectangle(x1, y0 - h_grunt - H_f, x2, y0 - h_grunt - H_f - L, fill='grey')
    my_dimension(canvas1, -B_f / 2., y0 - h_grunt - H_f, -B_f / 2., y0 - h_grunt - H_f - L, 15, "L", 5)
    my_dimension(canvas1, -B_f / 2., y0 - h_grunt, -B_f / 2., y0 - h_grunt - H_f, 15, "H_f", 5)
    my_dimension(canvas1, -B_f / 2., y0, -B_f / 2., y0 - h_grunt, 15, "h_g", 5)

    canvas2.create_rectangle(-L_stem / 2., y0 - h_grunt, L_stem / 2., y0 - h_grunt + d_stem, fill='grey')
    canvas2.create_rectangle(-L_f / 2., y0 - h_grunt, L_f / 2., y0 - h_grunt - H_f, fill='grey')
    for i in range(int(piles['n_s'])):
        x1 = -L_f / 2. + r_kr + i * r
        x2 = -L_f / 2. + r_kr + i * r + D
        canvas2.create_rectangle(x1, y0 - h_grunt - H_f, x2, y0 - h_grunt - H_f - L, fill='grey')
    my_dimension(canvas2, -L_f / 2., y0 - h_grunt - H_f, -L_f / 2., y0 - h_grunt - H_f - L, 10, "L", 5)
    my_dimension(canvas2, -L_f / 2., y0 - h_grunt, -L_f / 2., y0 - h_grunt - H_f, 15, "H_f", 5)
    if h_grunt:
        my_dimension(canvas2, -L_f / 2., y0, -L_f / 2., y0 - h_grunt, 15, "h_g", 5)

def my_dimension(canvas,x0,y0,x1,y1,dist, text,size):
    canvas.create_line(x0,y0,x1,y1)
    canvas.create_line(x0-size,y0,x0+size,y0)
    canvas.create_line(x0-size,y1,x0+size,y1)
    canvas.create_text(x0-dist, (y0+y1)/2., text=text)


def draw_levels_in_view(canvases, soils, z_w, x_size, y_size):
    y_size2 = y_size - z_w * 20.
    for canvas in canvases:
        # poziom 0
        canvas.create_line(x_size / 2. - 25., y_size / 2. - 85., x_size / 2. - 25., y_size / 2. - 100.)
        canvas.create_line(x_size / 2. - 25., y_size / 2. - 100., x_size / 2. - 33., y_size / 2. - 93.)
        canvas.create_line(x_size / 2. - 33., y_size / 2. - 93., x_size / 2. - 5, y_size / 2. - 93.)
        canvas.create_text(x_size / 2. - 21., y_size / 2. - 93., anchor='sw', text='0.0')
        # poziom wody

        canvas.create_line(-x_size / 2. + 25., y_size2 / 2. - 85., -x_size / 2. + 25., y_size2 / 2. - 100., fill='blue')
        canvas.create_line(-x_size / 2. + 25., y_size2 / 2. - 100., -x_size / 2. + 17., y_size2 / 2. - 93., fill='blue')
        canvas.create_line(-x_size / 2. + 17., y_size2 / 2. - 93., -x_size / 2. + 45, y_size2 / 2. - 93., fill='blue')
        canvas.create_text(-x_size / 2. + 29., y_size2 / 2. - 93., anchor='sw', text=str(z_w), fill='white')


def draw_stresses(canvas, piles, stresses, y_size):
    y_1 = y_size / 2 - 100.
    x_1 = 0
    x_2 = 0
    x_3 = 0
    for layer in stresses['stresses']:
        x1 = -layer['sig'] / 10.
        y1 = y_1 - (layer['z1'] - layer['z0']) * 10
        canvas.create_line(x_1, y_1, x1, y1, fill='red')
        x_1 = x1
        y_1 = y1
    for layer in stresses['stresses_under']:
        x1 = -layer['sig_v0zk'] / 10.
        x2 = -layer['sig_vdzk'] / 10.
        x3 = -layer['s'] * 100.
        y1 = y_1 - 20.
        canvas.create_line(x_1, y_1, x1, y1, fill='red')
        canvas.create_line(x_2, y_1, x2, y1, fill='blue')
        canvas.create_line(x_3, y_1, x3, y1, fill='green')
        x_1 = x1
        x_2 = x2
        x_3 = x3
        y_1 = y1


def draw_piles_plan(canvas, piles):
    B_f = piles['B_f'] * 10.
    L_f = piles['L_f'] * 10.
    r_kr = piles['r_kr'] * 10.
    r = piles['r'] * 10.
    D = piles['D'] * 10.
    # piles.update((x, y * 10.) for x, y in piles.items())  # multiply everything by scale
    B_f = 2. * r_kr + (piles['n_r'] - 1.) * r + D
    L_f = 2. * r_kr + (piles['n_s'] - 1.) * r + D
    canvas.create_rectangle(-B_f * 1.3 / 2., L_f * 1.3 / 2., B_f * 1.3 / 2., -L_f * 1.3 / 2., fill='', outline='', tags=(soMetricCanvas.TAB_EXTERIOR_BOUNDARY, soMetricCanvas.TAB_FIT_TO_VIEW))
    canvas.create_rectangle(-B_f / 2., L_f / 2., B_f / 2., -L_f / 2., fill='grey', **opts)
    coords = []
    x0 = -B_f / 2. + r_kr + D / 2
    y0 = L_f / 2. - r_kr - D / 2
    for i in range(int(piles['n_r'])):
        for j in range(int(piles['n_s'])):
            coords.append([x0 + i * r, y0 - j * r])
    for coord in coords:
        canvas.create_oval(coord[0] - D / 2., coord[1] + D / 2., coord[0] + D / 2., coord[1] - D / 2., **opts)
    canvas.draw_dimension(B_f/2.-r_kr, L_f / 2., B_f/2., L_f / 2., -r_kr/2., "r_kr", end_dot_size=dot)
    if len(coords)>1:
        canvas.draw_dimension(coords[0][0], coords[0][1], coords[1][0], coords[1][1], 13, "r", end_dot_size=dot)

# endregion
