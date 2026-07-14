## DOT:

You might get errors like "DOT missing in path". This is a common error if the environment installation haven't been able to handle the graphviz installation correctly. Please run the following:
```
sudo apt install graphviz   # if on Ubuntu
conda install graphviz      # if using conda
```
To check that graphviz installed correctly, run dot -V to check the version:
```
$ dot -V
dot - graphviz version 2.43.0 (0)
```