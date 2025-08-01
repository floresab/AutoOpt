"""
bscat.py
Scans in Boundary Condition to generate wavefunctions with various energies
"""
#-----------------------------------------------------------------------
from copy import deepcopy
#-----------------------------------------------------------------------
from utility import utility_t
from deck import deck_t
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
def SingleChannelScan(util: utility_t, target: wavefunction_t, scatter: wavefunction_t):
#-----------------------------------------------------------------------
    scan=[]
    opt_wse=GenerateOptFile(scatter.PARAMS, scatter.DK, "opt/wse.opt", \
        [{"ss":True,"ss_idx":util.SS_IDX,"key":"WSE","scale":0, "flat":0.5}])
#-----------------------------------------------------------------------
    scatter.CTRL.INPUT_BRA.DECK_FILE=scatter.DK.FILE_NAME
    opt_dk_file=f"{util.WORKING_DIR}/dk/init_{util.INITIAL_BSCAT:4f}.dk"
    print(f"\n🔁 bscat = {util.INITIAL_BSCAT:.4f}")
    #e,v=scatter.Optimize(opt_wse,,True,f"{util.WORKING_DIR}/log/initial_bscat.log")
    #e_target,v_target=[-23.75,0.]
    #erel=e_target-e
    #vrel=v_target**2+v**2
    #print(erel,vrel)




