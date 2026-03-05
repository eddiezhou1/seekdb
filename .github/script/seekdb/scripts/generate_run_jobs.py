# coding: utf-8

import sys
import os
import requests
import yaml
import traceback
import re


def check_run_job(ocenbase_code_path, job, default_value):
    akfarm_path = os.path.join(ocenbase_code_path, ".akfarm")
    if os.path.isfile(akfarm_path):
        with open(akfarm_path, "r") as f:
            akfarm_contents = f.readlines()
            for akfarm_content in akfarm_contents:
                akfarm_content = akfarm_content.strip("\n")
                if akfarm_content == job:
                    return True
                elif akfarm_content == "!{}".format(job):
                    return False
            return default_value
    else:
        return default_value


def need_ce_test_parallel(ocenbase_code_path, branch):
    if os.path.isfile(os.path.join(ocenbase_code_path, ".4_ce")) and (branch == "master" or branch == "4_0_0_release" or branch == "4_1_0_release" or branch == "4_2_0_release" or branch == "strip2ce_pro"):
        return True
    return False

def need_oci_ut(ocenbase_code_path, branch):
    if branch in ["3_2_3_release", "3_2_x_release"]:
        return True
    if os.path.isfile(os.path.join(ocenbase_code_path, "tools", "deploy", "ocitest_version")):
        return True
    return False
    
def need_jdbctest(ocenbase_code_path):
    if os.path.isfile(os.path.join(ocenbase_code_path, "tools", "deploy", "jdbctest_target_version")):
        return True
    return False


def is_cmake(ocenbase_code_path):
    if os.path.isfile(os.path.join(ocenbase_code_path, "CMakeLists.txt")):
        return True
    return False


def need_split_obtest_cases(ocenbase_code_path):
    cases_file = os.path.join(ocenbase_code_path, "tools", "obtest", "farm", "quick_quick.cases")
    if not os.path.isfile(cases_file):
        return False
    with open(cases_file, "r") as f:
        cases_count = len(f.readlines())
        if cases_count >= 3:
            return True
        return False
    
def need_split_restore_cases(ocenbase_code_path):
    if os.path.isfile(os.path.join(ocenbase_code_path, "tools", "obtest", "farm", "restore.cases")):
        return True
    return False

def need_split_compat2_cases(ocenbase_code_path):
    if os.path.isfile(os.path.join(ocenbase_code_path, "tools", "obtest", "farm", "compat2.cases")):
        return True
    return False

def is_release_mode(ocenbase_code_path, branch):
    return True
    release_mode=False
    if os.path.isfile(os.path.join(ocenbase_code_path, "test", "farm.yaml")):
        try:
            build_target = yaml.load(os.path.join(ocenbase_code_path, "test", "farm.yaml")).get("build_target")
            if build_target == "release":
                release_mode = True
        except:
            pass
    if not release_mode:
        # 临时用这个文件作为开启release mode的标志位
        if os.path.isfile(os.path.join(ocenbase_code_path, "test", "pretest", "pretest.conf")):
            release_mode = True
        
        # 对于4.0额外做一个兼容判断
        if branch == "4_0_0_release":
            if os.path.isfile(os.path.join(ocenbase_code_path, "test", "static", "stack", ".whitelist_release")):
                release_mode = True
            else:
                release_mode = False
    return release_mode
    
def can_split_mittest_cases(ocenbase_code_path):
    if os.path.isdir(os.path.join(ocenbase_code_path, "mittest")):
        return True
    return False

def generate_the_runjobs(ocenbase_code_path, branch, output_path, run_user=None, auto_related=False, fork_commit=None, current_commit=None, test_name="farm", daily_regression=False):
    # 首先基于分支生成需要运行的cases列表
    # 然后基于 .akfarm文件进行过滤
    
    jobs = {
        "compile": True,
        "mysqltest": True,
        "pretest": True, # 这里还是叫pretest,
    }
    
    
    if need_oci_ut(ocenbase_code_path, branch):
        jobs.update(
            {
                "ocitest": True
            }
        )  
        
    
    if need_jdbctest(ocenbase_code_path):
        jobs.update(
            {
                "jdbctest": True
            }
        )  
            
    with open(os.path.join(output_path, "jobargs.output"), "a+") as f:
        if is_cmake(ocenbase_code_path):
            f.writelines("++is_cmake++\n")
        else:
            f.writelines("")
            
        if is_release_mode(ocenbase_code_path, branch):
            f.writelines("++release_mode++\n")
        else:
            f.writelines("")

        if check_run_job(ocenbase_code_path, "restore", jobs.get("restore")):
            f.writelines("++need_agentserver++\n")
        
        for job in [
            "compat",
            "compat2",
            "compat_ce",
            "restore",
            "mittest",
            "pretest"
        ]:
            if check_run_job(ocenbase_code_path, job, jobs.get(job)):
                f.writelines("++need_liboblog++\n")
                f.writelines("++need_libobserver_so++\n")    
                break
            
    with open(os.path.join(output_path, "run_jobs.output"), "a+") as f:
        for job, default_value in jobs.items():
            if check_run_job(ocenbase_code_path, job, default_value):
                
                if job == "mittest":
                    if can_split_mittest_cases(ocenbase_code_path):
                        job = "mittest_multiple"
                    else:
                        job = "mittest_single"
                elif job == "pretest":
                    if is_cmake(ocenbase_code_path):
                        job = "unittest_single"
                    else:
                        job = "unittest_multiple"
                elif job == "obtest":
                    if need_split_obtest_cases(ocenbase_code_path):
                        job = "obtest_multiple"
                    else:
                        job = "obtest"
                elif job == "restore":
                    if need_split_restore_cases(ocenbase_code_path):
                        job = "restore_multiple"
                    else:
                        job = "restore"  
                elif job == "compat2":
                    if need_split_compat2_cases(ocenbase_code_path):
                        job = "compat2_multiple"
                    else:
                        job = "compat2"  
                print(job) 
                f.writelines(
                    "++{}++\n".format(job)
                )


if __name__ == '__main__':
    args = sys.argv[1:]
    res = generate_the_runjobs(*args)
    

