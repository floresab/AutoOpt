class SpatialSymmetry:
    def __init__(self):
        self.correlations = []
        self.correlation_groups = [] # list of lists for related parameters
    
    # helper function to set parameters
    def set_param(self, name, value):
        setattr(self, name, value)
        self.correlations.append(name)
    
    def set_group(self, fields, values):
        for name, val in zip(fields, values):
            self.set_param(name, val)
        self.correlation_groups.append(fields)


# Read the spatial symmetry correlations
def read_spatial_symmetries(lines, start_line, nbeta, nppart, ndpart, phi_type):
    symmetries = []
    i = start_line  

    for m in range(nbeta):
        ss = SpatialSymmetry()

        # BLS name (label line)
        ss.set_param('blsname', lines[i].split()[0]); i += 1
        ss.correlation_groups.append(['blsname'])

        if phi_type != 0:
            # CORE and SDSH values
            core_fields = ['l_core', 's_core', 'j_core', 't_core', 'tz_core']
            core_vals = map(float, lines[i].split()[:5]); i += 1
            ss.set_group(core_fields, core_vals)
            sdsh_fields = ['l_sdsh', 's_sdsh', 'j_sdsh', 't_sdsh', 'tz_sdsh']
            sdsh_vals = map(float, lines[i].split()[:5]); i += 1
            ss.set_group(sdsh_fields, sdsh_vals)
        
        ss.set_param('beta', lines[i].split()[0]); i += 1
        ss.correlation_groups.append(['beta'])

        # SPU line
        spu_fields = ['lfcsp', 'spu', 'spv', 'spr', 'spa', 'spb', 'spc', 'spk', 'spl']
        values = list(map(float, lines[i].split()[:9])); i += 1
        ss.set_group(spu_fields, values)

        # PPU line (if NPPART >= 2)
        if nppart >= 2:
            ppu_fields = ['lfcpp', 'ppu', 'ppv', 'ppr', 'ppa', 'ppb', 'ppc', 'ppk', 'ppl']
            values = list(map(float, lines[i].split()[:9])); i += 1
            for name, val in zip(ppu_fields, values):
                ss.set_param(name, int(val) if name == 'lfcpp' else val)
            ss.correlation_groups.append(ppu_fields)

        # LFSP etc
        lfsp_fields = ['lfsp', 'e_or_v', 'lscat', 'lmu1', 'lmu2', 'lqnum', 'lnodes']
        values = list(map(int, lines[i].split()[:7])); i += 1
        ss.set_group(lfsp_fields, values)

        # Optional bscat
        if ss.lscat == 1:
            ss.set_param('bscat', float(lines[i].split()[0])); i += 1
            ss.correlation_groups.append(['bscat'])

        # WSE, WSV, etc.
        ws_fields = ['wse', 'wsv', 'wsr', 'wsa', 'wbr', 'wba']
        values = list(map(float, lines[i].split()[:6])); i += 1
        ss.set_group(ws_fields, values)

        symmetries.append(ss)

        # NDPART block
        if ndpart != 0:

            msd = m + nbeta
            ss_dep = SpatialSymmetry()

            # SDU line
            sdu_fields = ['lfcsd', 'sdu', 'sdv', 'sdr', 'sda', 'sdb', 'sdc', 'sdk', 'sdl']
            values = list(map(float, lines[i].split()[:9])); i += 1
            ss_dep.set_group(sdu_fields, values)

            # PDU line
            pdu_fields = ['lfcpd', 'pdu', 'pdv', 'pdr', 'pda', 'pdb', 'pdc', 'pdk', 'pdl']
            values = list(map(float, lines[i].split()[:9])); i += 1
            for name, val in zip(pdu_fields, values):
                ss_dep.set_param(name, int(val) if name == 'lfcpd' else val)
            ss_dep.correlation_groups.append(pdu_fields)

            if ndpart >= 2:
                ddu_fields = ['lfcdd', 'ddu', 'ddv', 'ddr', 'dda', 'ddb', 'ddc', 'ddk', 'ddl']
                values = list(map(float, lines[i].split()[:9])); i += 1
                for name, val in zip(ddu_fields, values):
                    ss_dep.set_param(name, int(val) if name == 'lfcdd' else val)
                ss_dep.correlation_groups.append(ddu_fields)

            # Extra lfsp/e_or_v/… for MSD
            values = list(map(int, lines[i].split()[:7])); i += 1
            ss_dep.set_group(lfsp_fields, values)

            if ss_dep.lscat == 1:
                ss_dep.set_param('bscat', float(lines[i].split()[0])); i += 1
                ss_dep.correlation_groups.append(['bscat'])

            values = list(map(float, lines[i].split()[:6])); i += 1
            ss_dep.set_group(ws_fields, values)

            symmetries.insert(msd, ss_dep)

    return symmetries

