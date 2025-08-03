"""
bscat.py
Scans in Boundary Condition to generate wavefunctions with various energies
"""
#-----------------------------------------------------------------------
import numpy as np
#-----------------------------------------------------------------------
from utility import utility_t
from deck import deck_t,GenerateOptFile
from wavefunction import wavefunction_t
#-----------------------------------------------------------------------
"""
---
Single Channel Logic
---
1. Assume that core/target is optimized
2. Move A-1 parameters into A body input deck
3. Optimize with inital bscat
4. Initialize scan log
5. Optimize with +- initial_delta_bscat
6. Update log with +-
7. Compute db/de (central finite difference)
8. Scan Increasing bscat from initial
9. Scan Decreasing bscat from initial
---
Scan Logic
---
1. direction = +-
2. bscat_next = bscat_inital + direction * |db_de| * de
3. optimize with bscat_next
4. update log
5. update db_de (foward/backward finite difference)
6. check bounds, emin,emax,db_de_max
7. todo: if db_de > db_de_max and e_current < emax => node_count+=1 bscat = 2.5
   ***care needed in wse search
---
Optimize Logic
---
1. INPUT: bscat + deck + spatial symmetry index, logname
2. Scan WSE for the Spatial Symmetry (defualt: delta=0.5,num_walks=5,samples_per_walk=5)
3. Optimize correlations that only affect pairs/triples that include scattering nucleon (without wse)
4. Optimize correlations that only affect pairs/triples that include scattering nucleon (with wse)

    wse_corr, _ = zero_var_params(
        param_file,
        deck_file,
        ss,
        correlation_groups=[
            {'params': ['wse'], 'mode': 'set', 'value': WSE_OPT_VALUE}
        ]
    )
    spu_corrs, _ = zero_var_params(
        param_file,
        deck_file,
        ss,
        correlation_groups=[
            {'params': ['qssp1', 'qssp2'], 'mode': 'scale', 'value': OPT_SCALE},
            {'params': ['spu', 'spv', 'spr', 'spa', 'spb', 'spc', 'spk', 'spl'], 'mode': 'scale', 'value': OPT_SCALE},
            {'params': ['wsr', 'wsa'], 'mode': 'scale', 'value': OPT_SCALE}
        ]
    )
    all_corrs, _ = zero_var_params(
        param_file,
        deck_file,
        ss,
        correlation_groups=[
            {'params': ['wse'], 'mode': 'set', 'value': WSE_OPT_VALUE},
            {'params': ['qssp1', 'qssp2'], 'mode': 'scale', 'value': OPT_SCALE},
            {'params': ['spu', 'spv', 'spr', 'spa', 'spb', 'spc', 'spk', 'spl'], 'mode': 'scale', 'value': OPT_SCALE},
            {'params': ['wsr', 'wsa'], 'mode': 'scale', 'value': OPT_SCALE}
        ]
    )
        results.append({
            "bscat": b_next,
            "E_rel": E_next,
            "variance": var_next,
            "deck_path": path_next,
            "wse": wse_next
        })
    # --- Save Results ---
    results_sorted = sorted(results, key=lambda r: r["E_rel"])
    with open("optimized_decks.json", "w") as f:
        json.dump(results_sorted, f, indent=2)
"""
#-----------------------------------------------------------------------
def SingleChannelScan(work_dir:str, label:str, scatter:wavefunction_t,ssi:int, ecore:float,vcore:float):
#-----------------------------------------------------------------------
    scan=[]
    OPT_SCALE=0.2
    opt_wse_file_name=f"\'{work_dir}opt/wse.opt\'"
    wse_i=[{"ss":True,"ss_idx":ssi,"key":"WSE","scale":0, "flat":0.5}]
#-----------------------------------------------------------------------
    instructions=[{"ss":True,"ss_idx":ssi,"key":"QSSP1","scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"QSSP2","scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"SPU"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"SPV"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"SPA"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"SPB"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"SPC"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"SPK"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"SPL"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"WSR"  ,"scale":OPT_SCALE, "flat":0.0}\
                 ,{"ss":True,"ss_idx":ssi,"key":"WSA"  ,"scale":OPT_SCALE, "flat":0.0}]
#-----------------------------------------------------------------------
    instructions_all=instructions+wse_i
#-----------------------------------------------------------------------
    opt_wse=GenerateOptFile(scatter.PARAMS, scatter.DK, opt_wse_file_name,wse_i)
#-----------------------------------------------------------------------
    num_samples=scatter.CTRL.NUM_OPT_SAMPLES
#-----------------------------------------------------------------------
    bscat=float(scatter.DK.SS[ssi].BSCAT)
    print(f"BSCAT = {bscat:.4f}")
    dk_name=f"\'{work_dir}dk/{label}.{bscat:.4f}.dk\'"
    scatter.CTRL.INPUT_BRA.DECK_FILE=scatter.DK.FILE_NAME
    log=f"{work_dir}logs/{label}.start.{bscat:.4f}"
    print(f"BEGIN INITIAL EVALUATION: {log}.energy")
    e,v=scatter.Evaluate(True,log)
    e_start=e-ecore
    v_start=np.sqrt(v**2+vcore**2)
    print(f"EREL = {e_start:.4f} +- {v_start:.4f}")
#-----------------------------------------------------------------------
    scatter.CTRL.NUM_OPT_SAMPLES="5"
    scatter.CTRL.NUM_OPT_WALKS="5"
    log=f"{work_dir}logs/{label}.wse.{bscat:.4f}"
    print(f"BEGIN WSE SCAN: {log}.optimize")
    e,v=scatter.Optimize(opt_wse,dk_name,True,log)
    wse_erel=e-ecore
    wse_vrel=np.sqrt(v**2+vcore**2)
    print(f"OPTIMAL WSE = {float(scatter.DK.SS[ssi].WSE):.4f}")
    print(f"EREL = {wse_erel:.4f} +- {wse_vrel:.4f}")
    print(f"WSE OPTIMIZATION LOWERED ENERGY BY: {wse_erel-e_start:.4f} MeV")
#-----------------------------------------------------------------------
    scatter.CTRL.NUM_OPT_SAMPLES=num_samples
    scatter.CTRL.NUM_OPT_WALKS="1"
    log=f"{work_dir}logs/{label}.corr.{bscat:.4f}"
    print(f"BEGIN CORRELATION OPTIMIZATION: {log}.optimize")
    opt_corr_file_name=f"\'{work_dir}opt/{label}.corr.{bscat:.4f}.opt\'"
    opt_corr=GenerateOptFile(scatter.PARAMS, scatter.DK, opt_corr_file_name,instructions)
    e,v=scatter.Optimize(opt_corr,dk_name,True,log)
    corr_erel=e-ecore
    corr_vrel=np.sqrt(v**2+vcore**2)
    print(f"EREL = {corr_erel:.4f} +- {corr_vrel:.4f}")
    print(f"CORRELATION OPTIMIZATION LOWERED ENERGY BY: {corr_erel-wse_erel:.4f} MeV")