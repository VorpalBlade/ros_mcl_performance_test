# Performance testing suit for ROS MCL implementations

This repository implements some CPU usage and memory usage tests for Monte Carlo
Localisation in ROS.

[AMCL][amcl] and [QuickMCL][quickmcl] are supported for testing, but more
implementations could be added.

*If you are just interested in the results, see [this blog post][results].*

## Dependencies

Python 3 is required, and obviously [ROS][ros]

For running the tests:
```
pip3 install psutil
```

For [Jupyter Notebook](analysis/analysis.ipynb) for analysis:
```
pip3 install numpy pandas scipy matplotlib scikit-learn ipython jupyterlab
```

[amcl]: <https://wiki.ros.org/amcl>
[quickmcl]: <https://github.com/VorpalBlade/quickmcl>
[ros]: <http://www.ros.org/>
[results]: <https://vorpal.se/posts/2019/apr/07/quickmcl-vs-amcl-performance/>
