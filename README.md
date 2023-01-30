# Remote Jupyter Session Management Tool

![a screenshot of the rjy command line tool](https://github.com/vsbuffalo/remote_jupyter/blob/main/screenshot.png?raw=true)


`rjy` manages SSH tunneling for working with Jupyter 
notebooks and lab instances over SSH. First, create a remote 
Jupyter session on a server with,

    $ jupyter lab --no-browser --port=8904

where 8904 is a random high port number.

Then, copy the link it provides and use it with `rjy new <link>` *and your 
remote server hostname* to register this session with your local computer,

    $ rjy new http://localhost:8904/lab?token=b1fc6[...]b7a40 remote
    INFO:rjy:connected new session remote:8904

You could use an IP address too, but I **strongly** recommend if you 
interact with servers a lot over SSH, you add them to your `~/.ssh/config` 
file (see [this page](https://linuxhandbook.com/ssh-config-file/), for example)
and refer to them by their hostnames.

Then, we can see this Jupyter session is "registered" and the SSH tunneling
is with `rjy list`:

    $ rjy list
    key            pid  host      port  status    link
    -----------  -----  ------  ------  --------  -------------------------------------------
    sesame:8904  37041  remote    8904  conected  http://localhost:8904?token=b1fc6[...]b7a40
    
Most good terminals will allow you to directly click this link (e.g.
in iTerm2 on Mac, if you hold `⌘` and hover over a link, it will
become clickable).

This will also display unregistered sessions (those not registered in 
`~/remote_jupyter/sessions.json`), which were created by other applications 
outside of `rjy`.

We can disconnect a session with `rjy dc <key>`, where the key is 
that in the list output.

    $ rjy dc remote:8904
    [INFO] disconnecting 35657 for remote:8904

Now we can see it's disconnected:

    $ rjy list

    key          pid    host    port    status        link
    -----------  -----  ------  ------  ------------  -------------------------------------------
    sesame:8904                         disconnected  http://localhost:None?token=b1fc6[...]b7a40
    
We can reconnect with `rjy rc`. Without a key, everything registered is 
reconnected. With a key, only that session is.

    $ rjy rc remote:8904
    [INFO] reconnected session remote:8904

Now if we check,

    $ rjy list

    key            pid  host      port  status    link
    -----------  -----  ------  ------  --------  -------------------------------------------
    sesame:8904  37162  sesame    8904  conected  http://localhost:8904?token=b1fc6[...]b7a40
    
it's reconnected as expected. Finally, to drop a session from the registered cache,
use `rjy drop <key>`:

    $ rjy drop remote:8904
    [INFO] dropping session remote:8904 from registration

See the built-in instructions with `rjy --help` for more information.

## Warnings

Use at your own risk. This stores the token Jupyter creates in 
`~/.remote_jupyter/sessions.json`, and this could, in principle, 
be read with anyone with access to hijack the session. 

This is not much less secure than having the token in shell history,
but caution is still warranted. I make no guarantees about this software.

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
