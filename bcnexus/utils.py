import os
import shutil
from pathlib import Path
from typing import Any, List, Optional

import ipywidgets as widgets
import numpy as np
import pandas as pd
import yaml
from colorama import Fore, Style
from IPython.display import display

from bcnexus import constants as bcnexus_const
from bcnexus.clews import model_structure


def print_update(level: int=None,
                 message: str="--",
                 alert:Optional[bool]=False):
    if alert:
            level=level or 2
            color = Fore.RED
            prefix=" └ ❌ "
    elif level is not None:
        if level == 1:
            color = Fore.YELLOW
            prefix="└"
        elif level == 2:
            color = Fore.CYAN
            prefix=" └"
        elif level == 3:
            color = Fore.LIGHTWHITE_EX + Style.DIM
            prefix="  └"
        elif level > 3:
            color = Fore.LIGHTBLACK_EX + Style.DIM
            prefix="  └─"
    else:
        color = Fore.LIGHTMAGENTA_EX + Style.DIM
        prefix=" ─"
    
    print(f"{color}{prefix}> {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED} └ ❌ > {message}{Style.RESET_ALL}")

def print_module_title(text, Length_Char_inLine=100):
    print(f"{Fore.LIGHTCYAN_EX}{Length_Char_inLine * '_'}{Style.RESET_ALL}\n"
          f"{Fore.LIGHTGREEN_EX}{5 * ' '}{text}{Style.RESET_ALL}\n"
          f"{Fore.LIGHTCYAN_EX}{Length_Char_inLine * '_'}{Style.RESET_ALL}")
    
def print_banner(message: str):
    line = "*" * len(message)
    print(f"{Fore.GREEN}{Style.BRIGHT}{line}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}{line}{Style.RESET_ALL}")

def print_info(info:str):
    print(f"{Fore.LIGHTBLACK_EX}{Style.BRIGHT}ℹ️  {info}{Style.RESET_ALL}")

def print_warning(info: str):
    print(f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}⚠️  {info}{Style.RESET_ALL}")
    
def check_machine_cores():
    import psutil
    n_physical_cores = psutil.cpu_count(logical=False)
    n_logical_cores = psutil.cpu_count(logical=True)
    print_info(f"Your machine has {n_physical_cores} physical cores and {n_logical_cores} logical cores.")
    if n_physical_cores < 8:
        print_warning(f"Warning: Your machine has only {n_physical_cores} physical cores. \n Model building and runs may be slow. Consider using a machine with at least 4 physical cores for better performance.")
    return n_physical_cores, n_logical_cores
def _inject_ui_css(accent: str = "#0e7c86", accent_dark: str = "#22e0c8") -> None:
    """One-time CSS for the notebook widgets, themed for dark and light.

    Everything is scoped to the `.bcx-ui` container that build_scenario_ui
    adds, so it never leaks into other notebook output. Dark styling applies
    when the container also carries `.bcx-dark` (toggled by the theme button).
    """
    from IPython.display import HTML
    display(HTML(f"""
    <style>
    /* ---------- container ---------- */
    .bcx-ui{{padding:14px 16px;border-radius:12px;border:1px solid #e2e8f0;
        background:#ffffff;}}
    .bcx-ui.bcx-dark{{background:#0f1621;border-color:#2d3a4f;}}
    .bcx-ui h4{{color:#1a202c;}}
    .bcx-ui.bcx-dark h4{{color:#e2e8f0;}}
    .bcx-ui.bcx-dark .widget-label,
    .bcx-ui.bcx-dark label,
    .bcx-ui.bcx-dark .widget-html-content{{color:#cbd5e1 !important;}}
    .bcx-ui.bcx-dark .widget-readout{{color:#e2e8f0 !important;
        background:#1a2332 !important;border-color:#2d3a4f !important;}}
    .bcx-ui.bcx-dark .widget-slider .noUi-target{{background:#1a2332 !important;}}

    /* ---------- storage ToggleButtons ---------- */
    .bcnexus-tg .widget-toggle-button{{
        border:1.5px solid #cbd5e1 !important;border-radius:8px !important;
        margin-right:6px !important;font-weight:600 !important;
        color:#334155 !important;background:#fff !important;}}
    .bcnexus-tg .widget-toggle-button:hover{{border-color:{accent} !important;}}
    .bcnexus-tg .widget-toggle-button.mod-active{{
        background:{accent} !important;color:#fff !important;
        border-color:{accent} !important;
        box-shadow:0 0 10px rgba(14,124,134,.45) !important;}}
    .bcx-dark .bcnexus-tg .widget-toggle-button{{
        background:#1a2332 !important;color:#94a3b8 !important;
        border-color:#2d3a4f !important;}}
    .bcx-dark .bcnexus-tg .widget-toggle-button.mod-active{{
        background:transparent !important;color:{accent_dark} !important;
        border:2px solid {accent_dark} !important;
        box-shadow:0 0 12px rgba(34,224,200,.55) !important;}}

    /* ---------- generic button groups (solver, compiler) ---------- */
    .bcx-btn button, button.bcx-btn{{
        border:1.5px solid #cbd5e1 !important;border-radius:8px !important;
        font-weight:600 !important;color:#94a3b8 !important;
        background:#f8fafc !important;box-shadow:none !important;}}
    .bcx-btn-on button, button.bcx-btn-on{{
        background:{accent} !important;color:#fff !important;
        border:1.5px solid {accent} !important;
        box-shadow:0 0 10px rgba(14,124,134,.45) !important;}}
    .bcx-btn-off button, button.bcx-btn-off{{
        background:#f1f5f9 !important;color:#cbd5e1 !important;
        border:1.5px dashed #e2e8f0 !important;cursor:not-allowed !important;}}
    .bcx-dark .bcx-btn button, .bcx-dark button.bcx-btn{{
        background:#1a2332 !important;color:#8b9bb3 !important;
        border-color:#2d3a4f !important;}}
    .bcx-dark .bcx-btn-on button, .bcx-dark button.bcx-btn-on{{
        background:transparent !important;color:{accent_dark} !important;
        border:2px solid {accent_dark} !important;
        box-shadow:0 0 12px rgba(34,224,200,.5) !important;}}
    .bcx-dark .bcx-btn-off button, .bcx-dark button.bcx-btn-off{{
        background:#141c28 !important;color:#3f4c60 !important;
        border:1.5px dashed #2d3a4f !important;}}

    /* ---------- theme switch ---------- */
    .bcx-theme button{{border:1px solid #cbd5e1 !important;border-radius:8px !important;
        background:transparent !important;color:#475569 !important;font-weight:600 !important;
        box-shadow:none !important;}}
    .bcx-dark .bcx-theme button{{border-color:#2d3a4f !important;color:#cbd5e1 !important;}}
    </style>"""))


def button_select(options: list,
                  default: str = None,
                  disabled: list = None,
                  note: str = "",
                  width: str = "96px"):
    """Single-choice button group where *all* options stay visible.

    Unlike ipywidgets ToggleButtons, individual options can be disabled
    (rendered greyed and unclickable) - used for solvers/compilers that the
    workflow does not yet support.

    Returns a widgets.VBox with a plain `.value` attribute holding the
    selected option string (read it in the run loop).
    """
    disabled = list(disabled or [])
    default = default or next((o for o in options if o not in disabled), options[0])

    buttons = []
    for opt in options:
        b = widgets.Button(description=opt,
                           disabled=opt in disabled,
                           tooltip=(f"{opt} - not supported yet"
                                    if opt in disabled else opt),
                           layout=widgets.Layout(width=width, height='32px',
                                                 margin='0px 6px 0px 0px'))
        buttons.append(b)

    row = widgets.HBox(buttons, layout=widgets.Layout(flex_flow='row wrap'))
    children = [row]
    if note:
        children.append(widgets.HTML(
            f"<span style='font-size:11.5px;color:#64748b;'>{note}</span>"))
    box = widgets.VBox(children, layout=widgets.Layout(padding='2px 0px'))
    box.value = default
    box.buttons = buttons

    def _paint():
        for b in buttons:
            for c in ('bcx-btn', 'bcx-btn-on', 'bcx-btn-off'):
                b.remove_class(c)
            if b.disabled:
                b.add_class('bcx-btn-off')
            elif b.description == box.value:
                b.add_class('bcx-btn-on')
            else:
                b.add_class('bcx-btn')

    def _on_click(btn):
        if btn.disabled:
            return
        box.value = btn.description
        _paint()

    for b in buttons:
        b.on_click(_on_click)
    _paint()
    return box


def build_scenario_ui(scenarios_cfg: dict = None,
                      default_hour_grouping: int = 4,
                      default_clusters: int = 4,
                      default_scenarios: list = ['Base_CNZ_noCCS'],
                      default_storage: str = 'Kotzur',
                      default_solver: str = 'Gurobi',
                      default_compiler: str = 'Glpk',
                      default_threads: int = 16,
                      theme: str = 'light',
                      guide_url: str = 'docs/resources/temporal_resolution_explorer.html'):
    """Scenario/temporal configuration UI for the BCNexus notebook.

    Returns
    -------
    scenarios_box : widgets.VBox
        Multi-select checkbox panel. Use `get_selected_scenarios(scenarios_box)`
        (or `scenarios_box.value`) to get the list of ticked scenario names —
        drive a run loop with it.
    storage_algo_tg : widgets.ToggleButtons
        Kotzur / Niet, both visible, exactly one selectable (`.value`).
    h_grouping_dd, n_clusters_dd : sliders (`.value`)
    timeslices_label : widgets.HTML  live "Timeslices: N" readout
    solver_bg : button group (`.value`) - Gurobi | Cplex | CBC | Glpk | HiGHS
    compiler_bg : button group (`.value`) - Glpk (Mosox visible, disabled)
    threads_bg : button group (`.value`, string) - solver threads 4..32;
        cast with int(threads_bg.value) when passing to RunModel.run().

    NOTE: returns 8 items now (solver, compiler, threads appended at the end).
    Panel theme defaults to dark; switch live with the button in the panel's
    top-right, or pass theme='light'.

    Backwards note: element 0 used to be a single-value Dropdown; it is now a
    checkbox panel exposing `.value` as a LIST of scenarios.
    """
    _inject_ui_css()
    scenarios_cfg = scenarios_cfg or load_config(model_structure.clews_scenario_cfg_path)
    scenario_names = list((scenarios_cfg.get('SCENARIOS') or {}).keys())
    default_scenarios = default_scenarios or (scenario_names[:1] if scenario_names else [])

    # ---------------- scenarios: multi-select checkboxes
    checkboxes = []
    for name in scenario_names:
        cb = widgets.Checkbox(value=name in default_scenarios, description=name,
                              indent=False,
                              layout=widgets.Layout(width='auto', margin='0px 18px 2px 0px'))
        cb.style.description_width = 'initial'
        checkboxes.append(cb)

    count_lbl = widgets.HTML()
    select_all = widgets.Button(description='All', button_style='',
                                layout=widgets.Layout(width='58px', height='26px'))
    clear_all = widgets.Button(description='None',
                               layout=widgets.Layout(width='58px', height='26px'))

    grid = widgets.GridBox(checkboxes,
        layout=widgets.Layout(grid_template_columns='repeat(3, minmax(180px, 1fr))',
                              padding='4px 0px'))
    scenarios_box = widgets.VBox([
        widgets.HBox([select_all, clear_all, count_lbl],
                     layout=widgets.Layout(align_items='center', gap='8px')),
        grid])

    def _selected():
        return [cb.description for cb in checkboxes if cb.value]

    def _refresh(_=None):
        sel = _selected()
        scenarios_box.value = sel               # list of ticked scenarios
        count_lbl.value = (f"<span style='font-size:12px;color:#475569;'>"
                           f"<b>{len(sel)}</b> of {len(checkboxes)} selected</span>")

    for cb in checkboxes:
        cb.observe(_refresh, names='value')
    select_all.on_click(lambda _: [setattr(cb, 'value', True) for cb in checkboxes])
    clear_all.on_click(lambda _: [setattr(cb, 'value', False) for cb in checkboxes])
    scenarios_box.checkboxes = checkboxes
    _refresh()

    # ---------------- storage algorithm: both visible, one selectable
    storage_algo_tg = widgets.ToggleButtons(
        options=['Kotzur', 'Niet'],
        value=default_storage if default_storage in ('Kotzur', 'Niet') else 'Kotzur',
        description='',
        tooltips=['Kotzur et al. typical-period storage (inter-period linking)',
                  'Niet storage formulation'],
        layout=widgets.Layout(width='auto'))
    storage_algo_tg.style.button_width = '110px'
    storage_algo_tg.add_class('bcnexus-tg')          # styled by _inject_ui_css()

    # ---------------- solver: all visible, Gurobi is the supported path
    solver_bg = button_select(
        options=['Gurobi', 'Cplex', 'CBC', 'Glpk', 'HiGHS'],
        default=default_solver,
        note="Current workflow optimized for Gurobi.")

    # ---------------- GMPL compiler: Mosox visible but not selectable
    compiler_bg = button_select(
        options=['Glpk', 'Mosox'],
        default=default_compiler,
        disabled=['Mosox'],
        note="Optimized for Glpk; other compilers still in testing.")

    # ---------------- solver threads (4-32); machine cores shown for reference
    try:
        import os as _os
        _cores = _os.cpu_count() or 0
    except Exception:
        _cores = 0
    threads_bg = button_select(
        options=['4', '8', '12', '16', '24', '32'],
        default=str(default_threads),
        width='62px',
        note=("<span style='color:#e05252;font-weight:600;'>&#9888; Check your "
              "machine's physical cores and adjust the threads accordingly; "
              "8 threads recommended as minimum.</span>"
              + (f"<br><span style='color:#64748b;'>This machine reports "
                 f"<b>{_cores}</b> logical CPU(s).</span>" if _cores else "")))

    # ---------------- clustering sliders
    h_grouping_dd = display_range_slider(
        1, 24, description='Hour grouping:', description_width=120,
        default=default_hour_grouping, autodisplay=False)
    n_clusters_dd = display_range_slider(
        1, 10, description='Clusters:', description_width=120,
        default=default_clusters, autodisplay=False)

    timeslices_label = widgets.HTML(
        value="<b>Timeslices:</b> --",
        layout=widgets.Layout(width='230px', padding='5px 0px'))

    def update_timeslices(change=None):
        h, k = h_grouping_dd.value, n_clusters_dd.value
        if h > 0:
            ts = (24 // h) * k
            cost = 'light' if ts <= 24 else ('moderate' if ts <= 96 else 'heavy')
            colour = {'light': '#2e7d32', 'moderate': '#b26a00', 'heavy': '#c62828'}[cost]
            timeslices_label.value = (
                f"<b>Timeslices:</b> {ts} &nbsp;"
                f"<span style='color:{colour};font-size:12px;'>({cost} solve)</span>")
        else:
            timeslices_label.value = "<b>Timeslices:</b> —"

    h_grouping_dd.observe(update_timeslices, names='value')
    n_clusters_dd.observe(update_timeslices, names='value')
    update_timeslices()

    hint = widgets.HTML(
        "<span style='font-size:12px;color:#64748b;'>"
        "Hour grouping = hours merged per representative day (24/h brackets per day) · "
        "Clusters = representative day types · Timeslices = (24 / hour grouping) x clusters"
        "</span>")

    ui = widgets.VBox([
        widgets.HTML("<h4 style='margin-bottom:3px;'>Scenarios <span style='font-weight:400;"
                     "font-size:12px;color:#64748b;'>(tick one or more to run)</span></h4>"),
        scenarios_box,
        widgets.HBox([
            widgets.VBox([
                widgets.HTML("<h4 style='margin:15px 0px 3px;'>Storage Algorithm</h4>"),
                storage_algo_tg],
                layout=widgets.Layout(margin='0px 40px 0px 0px')),
            widgets.VBox([
                widgets.HTML("<h4 style='margin:15px 0px 3px;'>Solver</h4>"),
                solver_bg]),
            widgets.VBox([
                widgets.HTML("<h4 style='margin:15px 0px 3px;'>GMPL Compiler</h4>"),
                compiler_bg],
                layout=widgets.Layout(margin='0px 40px 0px 40px')),
            widgets.VBox([
                widgets.HTML("<h4 style='margin:15px 0px 3px;'>Threads</h4>"),
                threads_bg]),
        ], layout=widgets.Layout(align_items='flex-start', flex_flow='row wrap')),
        widgets.HTML(
            "<h4 style='margin:15px 0px 3px;display:flex;align-items:center;"
            "gap:10px;flex-wrap:wrap;'>Temporal Resolution"
            f"<a href='{guide_url}' target='_blank' style='font-size:12px;"
            "font-weight:600;text-decoration:none;color:#0e7c86;border:1px solid "
            "#0e7c86;border-radius:6px;padding:3px 9px;white-space:nowrap;'>"
            "&#9432; Check visual guide on timeslice configuration</a></h4>"),
        widgets.HBox([h_grouping_dd, n_clusters_dd, timeslices_label],
                     layout=widgets.Layout(justify_content='flex-start',
                                           align_items='center', gap='30px')),
        hint,
    ], layout=widgets.Layout(width='90%', padding='10px 0px'))

    ui.add_class('bcx-ui')
    if str(theme).lower() == 'dark':
        ui.add_class('bcx-dark')

    def _toggle_theme(_btn):
        if 'bcx-dark' in getattr(ui, '_dom_classes', ()):
            ui.remove_class('bcx-dark')
            _btn.description = '\u25d0 Dark'
        else:
            ui.add_class('bcx-dark')
            _btn.description = '\u2600 Light'

    theme_btn = widgets.Button(
        description=('\u2600 Light' if str(theme).lower() == 'dark' else '\u25d0 Dark'),
        tooltip='Switch panel theme',
        layout=widgets.Layout(width='96px', height='28px'))
    theme_btn.add_class('bcx-theme')
    theme_btn.on_click(_toggle_theme)
    ui.children = (widgets.HBox([theme_btn],
                   layout=widgets.Layout(justify_content='flex-end')),) + ui.children

    display(ui)
    return (scenarios_box, storage_algo_tg, h_grouping_dd, n_clusters_dd,
            timeslices_label, solver_bg, compiler_bg, threads_bg)


def get_selected_scenarios(scenarios_box) -> list:
    """List of ticked scenario names from build_scenario_ui()'s first return."""
    if hasattr(scenarios_box, 'checkboxes'):
        return [cb.description for cb in scenarios_box.checkboxes if cb.value]
    return list(getattr(scenarios_box, 'value', []) or [])


def display_dropdown(
    options: List[Any],
    description: str = "Selection:",
    description_width:int=110,
    default: Optional[Any] = None,
    disabled: bool = False,
    autodisplay: bool = True,
) -> widgets.Dropdown:
    """
    Create a modern, flexible dropdown widget in Jupyter Notebook.

    Args:
        options (List[Any]): Items to display in the dropdown.
        description (str): Label shown before dropdown. Default: 'Selection:'.
        default (Any, optional): Initial selected value. If not provided, first element is used.
        disabled (bool): Whether the dropdown is interactive. Default: False.
        auto_display (bool): If True, displays immediately in notebook. Otherwise returns widget without display.

    Returns:
        widgets.Dropdown: The created Dropdown widget.
    """
    if not isinstance(options, list) or not options:
        raise ValueError("options must be a non-empty list.")

    if default is not None and default not in options:
        raise ValueError("default value must be one of the options.")

    dropdown = widgets.Dropdown(
        options=options,
        description=description,
        value=default or options[0],
        disabled=disabled,
        layout=widgets.Layout(width='50%'),  # Optional: adds nice styling
        style={'description_width': f'{description_width}px'}  # control label width
    )
    
    if autodisplay:
        display(dropdown)
    return dropdown

def display_range_slider(min_val: int, 
                         max_val: int, 
                         default:int=None,
                         description: str = 'None',
                         description_width:int=110,
                         autodisplay: bool = True) -> widgets.IntSlider:
    slider = widgets.IntSlider(
        value=default if default is not None else (min_val + max_val) // 2,
        min=min_val,
        max=max_val,
        step=1,
        description=description if description else 'Select:',
        layout=widgets.Layout(width='70%'),   # control slider width
        style={'description_width': f'{description_width}px'}  # control label width
    )
    if autodisplay:
        display(slider)
    return slider



def copy_csv_files(
    src_folder: str, 
    dest_folder: str,
    all_files:bool=False
    ) -> None:
    """
    Copies only missing CSV files from the source folder to the destination folder.

    Args:
        src_folder (str): Path to the source folder containing CSV files.
        dest_folder (str): Path to the destination folder where CSV files will be copied.
        all_files (bool) : If True, copies all files, otherwise copies the missing files only.

    Returns:
        None: The function does not return any value.
    """
    # Convert paths to Path objects
    src_path = Path(src_folder)
    dest_path = ensure_path(dest_folder)
    if all_files:
        print_update(level=2,message=f"Copying all CSV files : '{src_path}' >> '{dest_path}'")
    else:
        print_update(level=2,message=f"Copying missing CSV files : '{src_path}' >> '{dest_path}'")

    # Iterate through all CSV files in the source folder
    for src_file in src_path.glob("*.csv"):
        # Destination file path
        dest_file = dest_path / src_file.name
        if all_files:
            shutil.copy(src_file, dest_file)
            print_update(level=3,message=f"Copied: {src_file.name}")
        else:
            # Copy only if the file is missing in the destination folder
            if not dest_file.exists():
                shutil.copy(src_file, dest_file)
                print_update(level=4,message=f"Copied: {src_file.name}")
            else:
                pass
                print_update(level=4,message=f"Skipped (already exists): {src_file.name}")
                
def ensure_path(path: str | Path) -> Path:
    p = Path(path)

    # If path has a suffix (like .txt, .yaml, .csv) → it's a file
    if p.suffix:
        # Make sure the directory exists
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # Otherwise, treat as directory
    p.mkdir(parents=True, exist_ok=True)
    return p

    
def process_demand_data(scenario:str,
                        AccumulatedAnnualDemand_scenario_filepath:str|Path,
                        SpecificAnnualDemand_scenario_filepath:str|Path,
                        ):
    """
    This function loads the demand data for a given scenario and processes it.
    It reads the accumulated and specific annual demand data from CSV files,
    merges them, and adds helper columns for plotting.
    Args:
        AccumulatedAnnualDemand_scenario_filepath (str|Path): Path to the accumulated annual demand CSV file.
        SpecificAnnualDemand_scenario_filepath (str|Path): Path to the specific annual demand CSV file.
        scenario (str): The scenario name.
    """

    annual_demand_CZ = pd.read_csv(Path(AccumulatedAnnualDemand_scenario_filepath))
    specific_demand_CZ = pd.read_csv(Path(SpecificAnnualDemand_scenario_filepath))
    total_demand_CZ = pd.concat([specific_demand_CZ, annual_demand_CZ], ignore_index=True)

    
    # Initialize the column with default values
    total_demand_CZ['sector'] = total_demand_CZ['FUEL'].str[:3]
    total_demand_CZ['end_use_fuel'] = total_demand_CZ['FUEL'].str[3:]
    total_demand_CZ['scenario'] = scenario

    # Overwrite with None where 'FUEL' contains 'LND', 'CRP', or 'PUB'
    mask = total_demand_CZ['FUEL'].str.contains('LND|CRP|PUB')
    total_demand_CZ.loc[mask, 'end_use_fuel'] = None
    # total_demand_CZ.loc[mask, 'sector'] = None
    
    # Helper function to get the columns needed for plotting
    return total_demand_CZ

def parse_data_value(value):
    """
    Attempts to convert strings that represent lists (e.g. '[100, 200, 300]')
    into actual lists. If not possible, returns the value as-is.
    """
    if isinstance(value, str):
        try:
            value = eval(value)
        except (SyntaxError, NameError):
            # If eval fails, keep the original string
            pass
    return value


def load_config(config_file):
    '''
    This function loads the configuration file for PyPSA_BC
    config_file: Path + filename of the configuration file. (i.e. ../config/config.yaml)
    '''
    with open(config_file, 'r') as file:
        cfg = yaml.safe_load(file)
    return cfg

def create_folder(folder):
    '''
    This functions creates a folder if not already created.
    If the folder is already created it takes no action
    folder: Path + folder name.
    '''
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder @ {folder}")

def write_pickle(data_dict, filepath):
    '''
    Write a pickle file based on a dictionary.
    '''
    with open(filepath,"wb") as f:
        pd.to_pickle(data_dict, f)
    f.close()
    print(f'Wrote pickle file {filepath}')

def read_pickle(filepath):
    '''
    Read a json file based on a dictionary.
    '''
    with open(filepath, 'rb') as f:
        data_dict = pd.read_pickle(f) 
    return data_dict

def fix_df_ts_index(
    df:pd.DataFrame, 
    start_date:str='2021-01-01 00:00:00', 
    end_date:str='2021-12-31 23:00:00'):
    '''
    This function hardcodes and fixes the timeseries to be an 8760 timeseries
    beginning in 2021-01-01.
    '''
    new_indices = pd.date_range(start = start_date, end = end_date, freq='h')
    
    df.index = new_indices

    return df

global det_col
global color_dict
det_col = None
color_dict = None

def add_power_tech_labels(df:pd.DataFrame,
                          tech_key:str):
    # Assign power_techs and filter
    df.loc[:, 'power_techs'] = df['TECHNOLOGY'].apply(
        lambda x: 'BATTERY_STORAGE' if (x == 'BATTERY_STORAGE' and (tech_key == 'capacity' or tech_key == 'energy')) else (
            x[:6] if x[:6] in bcnexus_const.technologies[tech_key] else None
        )
    )
    df.loc[:, 'power_techs_labels'] = df['power_techs'].map(bcnexus_const.legend_labels)
    return df

def df_years(df, years):
    new_df = pd.DataFrame()
    new_df['y'] = years
    new_df['y'] = new_df['y'].astype(int)
    df['y'] = df['y'].astype(int)
    new_df = pd.merge(new_df, df, how='outer', on='y').fillna(0)
    return new_df

    
def get_PJ_to_GWh_conversion_factor(timeslices_in_a_year: int = None) -> float:
    """
    Returns the conversion factor to convert energy in PJ (Petajoules) to 
    GWh (Gigawatt-hours), either total or average per timeslice.

    Parameters:
    - timeslices_in_a_year (int, optional): Number of equal-length timeslices in a year.
      If None, returns the direct conversion factor: 1 PJ = 277.778 GWh.
      If provided, returns the factor for average GWh per timeslice.

    Returns:
    - float: Conversion factor (multiply PJ by this factor to get GWh or average GWh per timeslice)
    """
    
    
    PJ_TO_GWh = 277.778 #GWh  # 1 PJ=277.778 GWh=277,778MWh

    if timeslices_in_a_year is None:
        return PJ_TO_GWh
    else:
        return PJ_TO_GWh / timeslices_in_a_year

def get_labels(df:pd.DataFrame):

    df.loc[:,'sector'] = np.where(
        df['TECHNOLOGY'].str.contains("CCS"),
        None,
        df['TECHNOLOGY'].str[3:6]
    )
    
    df.loc[:,'end_use_fuel']= np.where(
        df['TECHNOLOGY'].str.contains("CCS"),
        None,
        df['TECHNOLOGY'].str[6:9])

    df['end_use_fuel_label'] = df['end_use_fuel'].map(model_structure.NamingConvention)
    df['sector_label'] = df['sector'].map(model_structure.NamingConvention)
    return df