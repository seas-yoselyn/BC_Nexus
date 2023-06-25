rule CREATE_CONDA_ENV:
    input:
        snakemake_env='envs/snakemake.yaml'
    output:
        conda_env='snakemake_BCNexus'
    shell:
        '''
        conda env create -f {input.snakemake_env} --prefix {output.conda_env}
        conda activate './'+{output.conda_env}
        '''
