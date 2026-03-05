#!/bin/sh

export HOME=$_CONDOR_JOB_IWD


function run(){
    [[ -f $HOME/scripts/generate_run_jobs.py ]] && python3 $HOME/scripts/generate_run_jobs.py $HOME/oceanbase $BRANCH $HOME xxx 0 $FORK_COMMIT $COMMIT || python3 $HOME/generate_run_jobs.py $HOME/oceanbase $BRANCH $HOME xxx 0 $FORK_COMMIT $COMMIT
}

source $HOME/scripts/frame.sh && main