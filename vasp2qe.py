#!/home/zpc/miniconda3/envs/gpaw/bin/python
# -*- coding: utf-8 -*-
"""
vasp2qe.py - VASP to Quantum ESPRESSO Input Converter

用法:
    python vasp2qe.py <poscar> [output_file]
    
    参数:
        vasp_poscar_file : VASP坐标文件路径 (如 POSCAR, CONTCAR)
        output_file      : 输出QE文件名 (默认为 opt.in)
"""

import sys
import os
import numpy as np

# ============================================================================
# QE 输入文件模板
# 注意: {nat}, {ntyp}, {cell_parameters}, {atomic_species}, {atomic_positions}
#       为占位符，将被脚本自动替换
# ============================================================================
QE_TEMPLATE = """#QE input
&CONTROL
  calculation = 'relax'
  prefix = 'mycalc'
  verbosity = 'high'
!  restart_mode = 'restart'
  pseudo_dir = "/home/zpc/QE/SSSP"
  outdir = "./"
/
&SYSTEM
  ibrav       = 0
  nat         = {nat}
  ntyp        = {ntyp}
  ecutwfc     = 50.0
!  nbnd =
!  nspin = 2
!  starting_magnetization(ityp) = 0.5
!  occupations = 'smearing'
!  smearing = 'gauss'
!  degauss = 0.01
/
&ELECTRONS
  electron_maxstep = 101
  conv_thr = 1.0d-6
  mixing_beta = 0.7
!  startingpot = 'file'
!  startingwfc = 'file'
/
&IONS
/
&CELL
/

ATOMIC_SPECIES
#H    1.008   H.pbe-rrkjus_psl.1.0.0.UPF
#C    12.011  C.pbe-n-kjpaw_psl.1.0.0.UPF
#O    15.999  O.pbe-n-kjpaw_psl.0.1.UPF
#N    14.007  N.pbe-n-radius_5.UPF
{atomic_species}

K_POINTS automatic
1 1 1 0 0 0

CELL_PARAMETERS angstrom
{cell_parameters}

ATOMIC_POSITIONS ({pos_type})
{atomic_positions}

"""


def parse_poscar(filename):
    """
    解析VASP POSCAR/CONTCAR文件
    
    Returns:
        dict: 包含以下键:
            - scale: 全局缩放因子
            - lattice: 3x3 晶格矢量矩阵 (Å)
            - elements: 元素符号列表
            - counts: 每种元素的原子数列表
            - nat: 总原子数
            - ntyp: 原子类型数
            - positions: Nx3 坐标数组
            - cartesian: bool, True=笛卡尔坐标, False=分数坐标
    """
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    
    # 第1行: 注释
    # 第2行: 全局缩放因子
    scale = float(lines[1])
    
    # 第3-5行: 晶格矢量
    lattice = np.array([
        [float(x) for x in lines[i].split()] for i in range(2, 5)
    ]) * scale
    
    # 第6行: 元素符号 (VASP 5+格式)
    # 如果第6行全是数字，则为VASP 4格式(无元素名)，此处假设VASP 5+
    try:
        elements = lines[5].split()
        counts_line_idx = 6
    except ValueError:
        raise ValueError("无法解析元素行，请确认是VASP 5+格式的POSCAR")
    
    # 第7行: 各元素原子数
    counts = [int(x) for x in lines[counts_line_idx].split()]
    nat = sum(counts)
    ntyp = len(elements)
    
    # 判断坐标类型: Selective Dynamics 或直接坐标标记
    coord_line_idx = counts_line_idx + 1
    selective_dynamics = False
    if lines[coord_line_idx][0].lower() == 's':
        selective_dynamics = True
        coord_line_idx += 1
    
    # 坐标类型标识: C/c/K/k = Cartesian, 其他(D/d/F/f等) = Fractional
    coord_type_char = lines[coord_line_idx][0].lower()
    is_cartesian = coord_type_char in ('c', 'k')
    
    # 读取原子坐标
    pos_start = coord_line_idx + 1
    positions = []
    for i in range(nat):
        parts = lines[pos_start + i].split()
        pos = [float(parts[j]) for j in range(3)]
        positions.append(pos)
    
    positions = np.array(positions)
    
    # 如果是笛卡尔坐标且scale!=1，需要乘以scale
    # (VASP中笛卡尔坐标也受全局scale影响)
    if is_cartesian and scale != 1.0:
        positions *= scale
    
    return {
        'scale': scale,
        'lattice': lattice,
        'elements': elements,
        'counts': counts,
        'nat': nat,
        'ntyp': ntyp,
        'positions': positions,
        'cartesian': is_cartesian
    }


def generate_qe_input(poscar_data, output_file='opt.in'):
    """
    根据解析的VASP数据和内置模板生成QE输入文件
    
    Args:
        poscar_data: parse_poscar()返回的字典
        output_file: 输出文件名
    """
    # --- 构建 ATOMIC_SPECIES 块 ---
    # 使用占位质量1.0，用户需根据实际赝势修改
    species_lines = []
    for elem in poscar_data['elements']:
        # 默认原子质量设为1.0作为占位符，提醒用户检查
        species_lines.append(f"  {elem:<4s}  1.0000  {elem}.UPF")
    atomic_species = "\n".join(species_lines)
    
    # --- 构建 ATOMIC_POSITIONS 块 ---
    # 根据VASP坐标类型决定QE中使用 angstrom 还是 crystal
    if poscar_data['cartesian']:
        pos_type = "angstrom"
    else:
        pos_type = "crystal"
    
    pos_lines = []
    # 按元素分组写入，保持与ATOMIC_SPECIES一致的顺序
    idx = 0
    for elem, count in zip(poscar_data['elements'], poscar_data['counts']):
        for _ in range(count):
            x, y, z = poscar_data['positions'][idx]
            pos_lines.append(f"  {elem:<4s}  {x:18.14f}  {y:18.14f}  {z:18.14f}")
            idx += 1
    atomic_positions = "\n".join(pos_lines)
    
    # --- 构建 CELL_PARAMETERS 块 (始终使用angstrom单位) ---
    cell_lines = []
    for vec in poscar_data['lattice']:
        cell_lines.append(f"  {vec[0]:18.14f}  {vec[1]:18.14f}  {vec[2]:18.14f}")
    cell_parameters = "\n".join(cell_lines)
    
    # --- 填充模板 ---
    content = QE_TEMPLATE.format(
        nat=poscar_data['nat'],
        ntyp=poscar_data['ntyp'],
        pos_type=pos_type,
        atomic_species=atomic_species,
        atomic_positions=atomic_positions,
        cell_parameters=cell_parameters
    )
    
    # --- 写入文件 ---
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"[✓] QE输入文件已生成: {output_file}")
    print(f"    nat={poscar_data['nat']}, ntyp={poscar_data['ntyp']}")
    print(f"    坐标类型: {pos_type}")
    print(f"    元素: {', '.join(poscar_data['elements'])}")
    print(f"[!] 请检查并修改 ATOMIC_SPECIES 中的原子质量和赝势文件名!")


def main():
    """主入口函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("错误: 请提供VASP坐标文件路径")
        print("用法: python vasp2qe.py <POSCAR> [opt.in]")
        sys.exit(1)
    
    vasp_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'opt.in'
    
    if not os.path.exists(vasp_file):
        print(f"错误: 文件不存在 - {vasp_file}")
        sys.exit(1)
    
    print(f"[i] 读取VASP文件: {vasp_file}")
    data = parse_poscar(vasp_file)
    generate_qe_input(data, output_file)


if __name__ == '__main__':
    main()

