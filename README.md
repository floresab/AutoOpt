# nQMCC Parameter Optimization Framework

This project automates variational Monte Carlo (VMC) optimizations for He4+n scattering using the nQMCC framework.

## Modules

### `control.py`

Parses `.ctrl` input files used to control QMC simulations.

- Uses the `Control` class to:
  - Read/write simulation control files.
  - Store all simulation parameters in a Python dictionary for easy lookup.
  - Write updated control files with new paths, optimization inputs, etc.
- Internally uses:
  - `WavefunctionInputs` – a helper class to manage wavefunction-specific parameters like deck/param paths.

---

### `wavefunction_input.py`

Parses wavefunction blocks present in QMC deck files. Supports different wavefunction types via subclasses.

- **`WavefunctionInput`** *(abstract base class)*  
  Base framework for handling groups of wavefunction parameters, including reading, setting, and writing parameter blocks. Params stored as Python attributes.

- **`VariationalWavefunctionInput`**  
  Parses standard variational wavefunction input sections, including param and deck files plus parameter groups.

- **`ProductWavefunctionInput`**  
  Supports product-type wavefunctions with multiple param and deck files and parameter groups.

- **`DeuteronWavefunctionInput`**  
  Minimal subclass for deuteron wavefunction input where no parameter blocks are required.

- Used internally by `control.py`.

---

### `parameters.py`

Parses `.params` files which define structural layout for decks.

- Provides `Parameters` class used throughout `deck.py` and `zero_params.py`.
- Params stored as Python attributes

---

### `deck.py`

Parses and writes QMC `.dk` (deck) files containing variational parameters.

- Uses the `Deck` class to:
  - Read scalar, array, and symmetry-based parameters (stored in Python dictionary).
  - Track grouped parameter lines for correct output formatting.
  - Automatically detect and parse spatial symmetries.

- Internally uses:
  - `Parameters` (from `parameters.py`) for deck layout info.
  - `read_spatial_symmetries()` from `spatial_symmetry.py`.

- Provides:
  - `read_params_and_deck()` – loads both `.params` and `.dk` files into a `Deck`.

---

### `spatial_symmetry.py`

Parses spatial symmetry blocks present in QMC deck files.

- Spatial symmetry related parameters stored as Python attributes.
- Provides `read_spatial_symmetries()` to extract group-structured float parameters.
- Used internally by `deck.py`.

---

### `zero_params.py`

Provides tools to zero or scale variational parameters before optimization.

- `zero_var_params()` zeros or scales specific correlation groups (e.g. `spu`, `spv`, etc.)
- `save_opt_file()` saves modified decks (.opt) for use in optimization.

---

### `optimize_inputs.py`

Automates optimization of a scattering system (He⁴+n):

- **Step 1:** Optimizes the bound target (He⁴).
- **Step 2:** Copies target parameters into the scattering deck.
- **Step 3:** Searches `bscat` values to find initial relative energy near 3 MeV.
- **Step 4:** Iteratively adjusts `bscat` to explore energy dependence.
- **Step 5:** Saves optimized decks and results to CSV for analysis.

Outputs include optimized `.dk` files and a CSV summary of results with `bscat`, `E_rel`, and variance.