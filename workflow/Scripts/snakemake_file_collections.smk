# Snakemake rule to run the shell command
rule COLLECT_DATA_FILES:
    output:
        directory('data')
    shell:
        "python ./Scripts/organize_files.py"
