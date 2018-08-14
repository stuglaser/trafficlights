# ART

## Local Dev

Note this is only really tested on mac/linux (including WSL).

1) You will need automake and libtool and this repository
2) Run `make devenv`
3) Activate the virtualenv with `. devenv/bin/activate`
4) Try running in simulation mode `python traffic.py -f`
5) If you feel fancy try running a secondary light in simulation mode `python traffic.py -f -m localhost`

## Install on a pi

These instructions should work on any recentish raspian

1) Make sure you can SSH into the pi
2) Activate the virtualenv with `. devenv/bin/activate`
3) Install deps with fabric with `fab -H 1.2.3.4 -u pi --initial-password-prompt setup` or some variant
4) "Deploy" the traffic lights with `fab -H 1.2.3.4 -u pi --initial-password-prompt deploy` - note the initscript is disabled for now
