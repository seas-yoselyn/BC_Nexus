import bcnexus.utils as utils
import sys
from bcnexus.vis import plot_results_BC_Nexus

def get_nexus_scenarios(config_path:str='config/scenarios_bcnexus.yaml')->dict:
    cfg=utils.load_config(config_path)
    nexus_scenarios:dict=cfg.get('SCENARIOS')
    return nexus_scenarios


def show_nexus_scenarios(config_path:str='config/scenarios_bcnexus.yaml'):
    nexus_scenarios=get_nexus_scenarios(config_path)
    
    utils.print_module_title("Available Nexus Scenarios from 'config/scenarios_bcnexus.yaml' ")
    for scenario_key in nexus_scenarios:
        utils.print_update(level=2,message=f"{scenario_key}")
        for key in nexus_scenarios[scenario_key]:
            if key=='remarks':
                utils.print_update(level=3,message=f"{nexus_scenarios[scenario_key]['remarks']}")

def get_nexus_plots_pipeline(config_path:str='config/config.yaml'):
    nexus_scenarios=get_nexus_scenarios(config_path)
    for scenario in nexus_scenarios:
        plot_results_BC_Nexus.main(nexus_scenario=scenario,
                                  timeslices=24)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        utils.print_update(level=1, message="Usage: python bccm_pipelines.py <action>")
        utils.print_update(level=2, message="Available actions:")
        utils.print_update(level=3, message="'show_nexus_scenarios'")
        utils.print_update(level=3, message="'get_nexus_plots_pipeline'")
        sys.exit(1)
    
    action = sys.argv[1]
    if action=="show_nexus_scenarios":
        show_nexus_scenarios()
    if action=="get_nexus_plots_pipeline":
        get_nexus_plots_pipeline()

        
        