## About the jupyternotebook and folders:

The jupyternotebook file is self-explanatory and briefly it does the following things :

1. Copy the latest results from Linking Tool (solar, wind sites' spatial, temporal and technical data) and dumps it to '__results__' folder.
2. Defines the seasonal configuration to downsample the 8760hrs timeseries of the sites from linking tool
3. Create downsampled timeslices compatible for BCNexus datafields and saves to '__new_sites__' and '__new_sites_timeslice__' folders.

These data are to be plugged in to BCNexus datafiles.
