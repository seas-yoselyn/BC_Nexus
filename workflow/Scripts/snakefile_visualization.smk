# import os
# from pathlib import Path

# if not os.path.isdir('docs/Results_plots'):
#     os.makedirs('docs/Results_plots')

rule Visualization:
    input:
        'Scripts/TotalAnnualCapacity_PLOT.py'
    output:
        directory('docs/Results_plots')
    shell:
        'python {input}'