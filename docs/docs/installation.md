Installation and Requirements
=========

## Installation

The easiest way to install Jaide is through pip, which comes loaded with version 2.7.9 of [python](http://www.python.org/). If you don't have pip installed, you should follow their [instructions](https://pip.pypa.io/en/latest/installing.html). Once you have pip installed, jaide and all it's requirements can be installed via the following command (admin/root access might be necessary):  

	> pip install jaide  

Manual installation can be accomplished by downloading the source code and running the following command (don't forget sudo if needed):  

	> python setup.py install  

## Python Requirements:

Jaide is unfortunately only available on Python version 2.7, due to a required package being Python 2.7 only compatible.

Pip should handle retrieving any necessary requirements, but we list them here for verbosity. The versions of these packages below are the ones that we've tested with.  

[NCCLIENT >=0.4.2](https://github.com/leopoul/ncclient/)  -  https://github.com/leopoul/ncclient/  
[PARAMIKO >=1.14.0](https://github.com/paramiko/paramiko)  -  https://github.com/paramiko/paramiko   
[SCP >=0.8.0](https://github.com/jbardin/scp.py)  -  https://github.com/jbardin/scp.py  
[COLORAMA >=0.3.3](https://pypi.python.org/pypi/colorama) - https://pypi.python.org/pypi/colorama  
[CLICK >=3.3](http://click.pocoo.org/3/) - http://click.pocoo.org/3/  