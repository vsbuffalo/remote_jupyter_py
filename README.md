# Remote Jupyter

Remote jupyter manages SSH tunneling for working with Jupyter 
notebooks and lab instances over SSH. We create a new SSH tunnel
for a Jupyter notebook already started on the remote server by 
copying the link it provides and using it with `rjy new <link>`,

    $ rjy new http://localhost:8904/lab?token=b1fc6[...]b7a40 remote_server

    $ # or with an IP address

    $ rjy new http://localhost:8904/lab?token=b1fc6[...]b7a40 192.168.1.251
    INFO:rjy:connected new session sesame:8904

Then, we can see this Jupyter session is "registered" with `rjy list`:

    $ rjy list

    key            pid  remote      port  status    link
    -----------  -----  --------  ------  --------  -------------------------------------------
    sesame:8904  35160  sesame      8904  connected  http://localhost:8904?token=b1fc6[...]b7a40
    
    status types:
    
      - connected: a registered session is currently connected
      - disconnected: a session is registered, but currently connected
      - unregistered: a session is connected, but not registered with rjy

This will also display unregistered sessions (those not registered in 
`~/remote_jupyter/sessions.json`), which were created by other applications 
outside of `rjy`.

We can disconnect a session with `rjy dc <key>`, where the key is 
that in the list output.

    $ rjy dc sesame:8904
    [INFO] disconnecting 35657 for sesame:8904

Now we can see it's disconnected:

    $ rjy list
    
    key          pid    remote    port    status        link
    -----------  -----  --------  ------  ------------  ------------------------------------------
    sesame:8904                           disconnected  http://localhost:None?token=b1fc6[...]b7a40
    
    status types:
    
      - connected: a registered session is currently connected
      - disconnected: a session is registered, but currently connected
      - unregistered: a session is connected, but not registered with rjy

We can reconnect with `rjy rc`. Without a key, everything registered is 
reconnected. With a key, only that session is.

    $ rjy rc sesame:8904
    [INFO] reconnected session sesame:8904

Now if we check,

    $ rjy list
    
    key            pid  remote      port  status    link
    -----------  -----  --------  ------  --------  -------------------------------------------
    sesame:8904  35798  sesame      8904  connected  http://localhost:8904?token=b1fc6[...]b7a40
    
    status types:
    
      - connected: a registered session is currently connected
      - disconnected: a session is registered, but currently connected
      - unregistered: a session is connected, but not registered with rjy

it's reconnected as expected. Finally, to drop a session from the registered cache,
use `rjy drop <key>`:

    $ rjy drop sesame:8904
    [INFO] dropping session sesame:8904 from registration

See the built-in instructions with `rjy --help` for more information.
    

## Install
    
    git clone git://github.com/vsbuffalo/remote_jupyter
    cd remote_jupyter
    python setup.py install


## Contributing and Developer Environment

Please contribute! Some ideas:

 - shorter key names

Copy and paste this if you want to build a conda environment to tinker with this.

    $ conda create -s remote_jupyter
    $ conda activate remote_jupyter
    $ mamba install --yes --file requirements.txt

Developing with `setuptools` is easiest with:

    $ python setup.py develop
