The dashboard will be created vide the visualization inside the [Snakemake workflow](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow). However, you can review the dashboard locally as well :

## **Deploy Local Dashboard App**: 
* Go to the repository root directory i.e. _BC-CLEWS-Model _and type the following bash commands:

```
bash dashboard.sh deploy
```

You will get this in your bash CLI 
```
Dash is running on http://127.0.0.1:8050/
 * Serving Flask app 'app'
 * Debug mode: on
or, you can execute the dashboard deployment rule :
```
* Now you can check the dashboard app in your browser or IDE (e.g. VSCODE)

* **Alternatively**: You can run the snakemake rule for local dash app deployment
```
snakemake -c all deploy_dashboard -f --rerun-incomplete
```

## Dashboards
* [Interactive Dashboard](https://bc-clews-model.onrender.com) - *test server
* [Static Dashboard](https://deltae.github.io/BC-CLEWS-Model)


----
<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" href="http://purl.org/dc/dcmitype/Text" property="dct:title" rel="dct:type">BC-Nexus Model Workflow</span> by <a xmlns:cc="http://creativecommons.org/ns#" href="https://www.linkedin.com/in/eliasinul/" property="cc:attributionName" rel="cc:attributionURL">Md Eliasinul Islam</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.<br />Based on a work at <a xmlns:dct="http://purl.org/dc/terms/" href="https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow" rel="dct:source">https://github.com/DeltaE/BC-CLEWS-Model/tree/main/workflow</a>.