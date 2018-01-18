#!/usr/bin/env python
"""
Run this script from inside an agent. You need to first source the agent environment with:
source /data/srv/wmagent/current/apps/wmagent/etc/profile.d/init.sh
"""
from __future__ import print_function

import sys

from WMCore.Services.ReqMgrAux.ReqMgrAux import ReqMgrAux

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python setDrain.py AGENT_NAME STATUS")
        print("  e.g.: python setDrain.py cmsgwms-submit6.fnal.gov True")
        sys.exit(0)

    agentName = sys.argv[1]
    drainStatus = sys.argv[2]

    reqMgrAux = ReqMgrAux("https://cmsweb.cern.ch/reqmgr2")
    reqMgrAux.updateAgentDrainingMode(agentName, drainFlag=drainStatus)
