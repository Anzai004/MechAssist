import numpy as np
import pandas as pd
import os

np.random.seed(42)
N = 30000

def generate_beam_samples(n):
    b = np.random.uniform(0.02, 0.2, n)
    h = np.random.uniform(0.05, 0.4, n)
    L = np.random.uniform(0.5, 5.0, n)
    M = np.random.uniform(1e3, 1e6, n)
    V = np.random.uniform(1e2, 1e5, n)
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    I = (b * h**3) / 12
    y = h / 2
    sigma = (M * y) / I
    tau = (1.5 * V) / (b * h)
    sigma_vm = np.sqrt(sigma**2 + 3 * tau**2)
    return sigma, tau, sigma_vm, Sy, Su, ['beam'] * n

def generate_shaft_samples(n):
    d = np.random.uniform(0.02, 0.2, n)
    M = np.random.uniform(1e3, 1e6, n)
    T = np.random.uniform(1e3, 1e6, n)
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    r = d / 2
    I = np.pi * r**4 / 4
    J = np.pi * r**4 / 2
    sigma = (M * r) / I
    tau = (T * r) / J
    sigma_vm = np.sqrt(sigma**2 + 3 * tau**2)
    return sigma, tau, sigma_vm, Sy, Su, ['shaft'] * n

def generate_column_samples(n):
    b = np.random.uniform(0.02, 0.2, n)
    h = np.random.uniform(0.02, 0.2, n)
    L = np.random.uniform(0.5, 5.0, n)
    P = np.random.uniform(1e3, 1e7, n)
    E = np.random.uniform(70e9, 210e9, n)
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    A = b * h
    I = (b * h**3) / 12
    sigma = P / A
    P_cr = (np.pi**2 * E * I) / (L**2)
    sigma_vm = sigma
    tau = np.zeros(n)
    return sigma, tau, sigma_vm, Sy, Su, P, P_cr, ['column'] * n

def generate_near_boundary_samples(n, member_type):
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    sigma_vm = Sy * np.random.uniform(0.88, 1.12, n)
    sigma = sigma_vm
    tau = np.zeros(n)
    return sigma, tau, sigma_vm, Sy, Su, [member_type] * n

def generate_extreme_overload_samples(n, member_type):
    Sy = np.random.uniform(200e6, 800e6, n)
    Su = Sy * np.random.uniform(1.2, 1.8, n)
    sigma_vm = Su * np.random.uniform(0.95, 3.0, n)
    sigma = sigma_vm * np.random.uniform(0.7, 1.0, n)
    tau = np.sqrt(np.maximum((sigma_vm**2 - sigma**2) / 3, 0))
    return sigma, tau, sigma_vm, Sy, Su, [member_type] * n

def generate_safe_samples(n, member_type):
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    sigma_vm = Sy * np.random.uniform(0.05, 0.28, n)
    sigma = sigma_vm * np.random.uniform(0.7, 1.0, n)
    tau = np.sqrt(np.maximum((sigma_vm**2 - sigma**2) / 3, 0))
    return sigma, tau, sigma_vm, Sy, Su, [member_type] * n

def generate_fatigue_samples(n, member_type):
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    sigma_vm = Sy * np.random.uniform(0.31, 0.55, n)
    sigma = sigma_vm * np.random.uniform(0.7, 1.0, n)
    tau = np.sqrt(np.maximum((sigma_vm**2 - sigma**2) / 3, 0))
    return sigma, tau, sigma_vm, Sy, Su, [member_type] * n

def generate_yield_samples(n, member_type):
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    sigma_vm = Sy * np.random.uniform(1.01, 1.4, n)
    sigma = sigma_vm * np.random.uniform(0.7, 1.0, n)
    tau = np.sqrt(np.maximum((sigma_vm**2 - sigma**2) / 3, 0))
    return sigma, tau, sigma_vm, Sy, Su, [member_type] * n

def generate_low_sy_boundary_samples(n, member_type):
    Sy = np.random.uniform(200e6, 500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)
    sigma_vm = Sy * np.random.uniform(0.92, 1.08, n)
    sigma = sigma_vm
    tau = np.zeros(n)
    return sigma, tau, sigma_vm, Sy, Su, [member_type] * n

def label_sample(sigma_vm, Sy, Su, member_type, P=None, P_cr=None):
    labels = []
    for i in range(len(sigma_vm)):
        if member_type[i] == 'column' and P is not None and P_cr is not None:
            if P[i] >= P_cr[i]:
                labels.append('Buckling Risk')
            elif sigma_vm[i] >= Su[i]:
                labels.append('Fracture Risk')
            elif sigma_vm[i] >= Sy[i]:
                labels.append('Yield Risk')
            elif sigma_vm[i] >= 0.5 * Su[i]:
                labels.append('Fracture Risk')
            elif sigma_vm[i] >= 0.4 * Sy[i]:
                labels.append('Fatigue Risk')
            else:
                labels.append('Safe')
        else:
            if sigma_vm[i] >= Su[i]:
                labels.append('Fracture Risk')
            elif sigma_vm[i] >= Sy[i]:
                labels.append('Yield Risk')
            elif sigma_vm[i] >= 0.85 * Su[i]:
                labels.append('Fracture Risk')
            elif sigma_vm[i] >= 0.3 * Sy[i]:
                labels.append('Fatigue Risk')
            else:
                labels.append('Safe')
    return labels

def label_near_boundary(sigma_vm, Sy):
    return ['Safe' if sigma_vm[i] < Sy[i] else 'Yield Risk' for i in range(len(sigma_vm))]

def label_extreme_overload(sigma_vm, Su):
    return ['Fracture Risk' for _ in range(len(sigma_vm))]

def generate():
    n_each = N // 3

    s1, t1, vm1, sy1, su1, mt1 = generate_beam_samples(n_each)
    labels1 = label_sample(vm1, sy1, su1, mt1)

    s2, t2, vm2, sy2, su2, mt2 = generate_shaft_samples(n_each)
    labels2 = label_sample(vm2, sy2, su2, mt2)

    s3, t3, vm3, sy3, su3, p3, pcr3, mt3 = generate_column_samples(n_each)
    labels3 = label_sample(vm3, sy3, su3, mt3, P=p3, P_cr=pcr3)

    nb_s_beam, nb_t_beam, nb_vm_beam, nb_sy_beam, nb_su_beam, nb_mt_beam = generate_near_boundary_samples(1500, 'beam')
    nb_labels_beam = label_near_boundary(nb_vm_beam, nb_sy_beam)

    nb_s_shaft, nb_t_shaft, nb_vm_shaft, nb_sy_shaft, nb_su_shaft, nb_mt_shaft = generate_near_boundary_samples(1500, 'shaft')
    nb_labels_shaft = label_near_boundary(nb_vm_shaft, nb_sy_shaft)

    eo_s_beam, eo_t_beam, eo_vm_beam, eo_sy_beam, eo_su_beam, eo_mt_beam = generate_extreme_overload_samples(500, 'beam')
    eo_labels_beam = label_extreme_overload(eo_vm_beam, eo_su_beam)

    eo_s_shaft, eo_t_shaft, eo_vm_shaft, eo_sy_shaft, eo_su_shaft, eo_mt_shaft = generate_extreme_overload_samples(500, 'shaft')
    eo_labels_shaft = label_extreme_overload(eo_vm_shaft, eo_su_shaft)

    sf_s_beam, sf_t_beam, sf_vm_beam, sf_sy_beam, sf_su_beam, sf_mt_beam = generate_safe_samples(1000, 'beam')
    sf_s_shaft, sf_t_shaft, sf_vm_shaft, sf_sy_shaft, sf_su_shaft, sf_mt_shaft = generate_safe_samples(1000, 'shaft')

    ft_s_beam, ft_t_beam, ft_vm_beam, ft_sy_beam, ft_su_beam, ft_mt_beam = generate_fatigue_samples(1200, 'beam')
    ft_s_shaft, ft_t_shaft, ft_vm_shaft, ft_sy_shaft, ft_su_shaft, ft_mt_shaft = generate_fatigue_samples(1200, 'shaft')

    yr_s_beam, yr_t_beam, yr_vm_beam, yr_sy_beam, yr_su_beam, yr_mt_beam = generate_yield_samples(1000, 'beam')
    yr_s_shaft, yr_t_shaft, yr_vm_shaft, yr_sy_shaft, yr_su_shaft, yr_mt_shaft = generate_yield_samples(2000, 'shaft')

    ls_s_beam, ls_t_beam, ls_vm_beam, ls_sy_beam, ls_su_beam, ls_mt_beam = generate_low_sy_boundary_samples(1000, 'beam')
    ls_labels_beam = label_near_boundary(ls_vm_beam, ls_sy_beam)

    ls_s_shaft, ls_t_shaft, ls_vm_shaft, ls_sy_shaft, ls_su_shaft, ls_mt_shaft = generate_low_sy_boundary_samples(2500, 'shaft')
    ls_labels_shaft = label_near_boundary(ls_vm_shaft, ls_sy_shaft)

    sf_labels_beam  = ['Safe'] * 1000
    sf_labels_shaft = ['Safe'] * 1000
    ft_labels_beam  = ['Fatigue Risk'] * 1200
    ft_labels_shaft = ['Fatigue Risk'] * 1200
    yr_labels_beam  = ['Yield Risk'] * 1000
    yr_labels_shaft = ['Yield Risk'] * 2000

    df = pd.DataFrame({
        'member_type': mt1 + mt2 + mt3 + nb_mt_beam + nb_mt_shaft + eo_mt_beam + eo_mt_shaft + sf_mt_beam + sf_mt_shaft + ft_mt_beam + ft_mt_shaft + yr_mt_beam + yr_mt_shaft + ls_mt_beam + ls_mt_shaft,
        'sigma': np.concatenate([s1, s2, s3, nb_s_beam, nb_s_shaft, eo_s_beam, eo_s_shaft, sf_s_beam, sf_s_shaft, ft_s_beam, ft_s_shaft, yr_s_beam, yr_s_shaft, ls_s_beam, ls_s_shaft]),
        'tau': np.concatenate([t1, t2, t3, nb_t_beam, nb_t_shaft, eo_t_beam, eo_t_shaft, sf_t_beam, sf_t_shaft, ft_t_beam, ft_t_shaft, yr_t_beam, yr_t_shaft, ls_t_beam, ls_t_shaft]),
        'sigma_vm': np.concatenate([vm1, vm2, vm3, nb_vm_beam, nb_vm_shaft, eo_vm_beam, eo_vm_shaft, sf_vm_beam, sf_vm_shaft, ft_vm_beam, ft_vm_shaft, yr_vm_beam, yr_vm_shaft, ls_vm_beam, ls_vm_shaft]),
        'Sy': np.concatenate([sy1, sy2, sy3, nb_sy_beam, nb_sy_shaft, eo_sy_beam, eo_sy_shaft, sf_sy_beam, sf_sy_shaft, ft_sy_beam, ft_sy_shaft, yr_sy_beam, yr_sy_shaft, ls_sy_beam, ls_sy_shaft]),
        'Su': np.concatenate([su1, su2, su3, nb_su_beam, nb_su_shaft, eo_su_beam, eo_su_shaft, sf_su_beam, sf_su_shaft, ft_su_beam, ft_su_shaft, yr_su_beam, yr_su_shaft, ls_su_beam, ls_su_shaft]),
        'label': labels1 + labels2 + labels3 + nb_labels_beam + nb_labels_shaft + eo_labels_beam + eo_labels_shaft + sf_labels_beam + sf_labels_shaft + ft_labels_beam + ft_labels_shaft + yr_labels_beam + yr_labels_shaft + ls_labels_beam + ls_labels_shaft
    })

    os.makedirs('data/module2', exist_ok=True)
    df.to_csv('data/module2/stress_data.csv', index=False)
    print(f"Generated {len(df)} samples")
    print(df['label'].value_counts())

generate()