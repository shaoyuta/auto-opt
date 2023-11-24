import re
import os
import pandas as pd
import argparse


def check_and_create_dir(path):
    """
    check dir and create new dir
    """
    try:
        os.makedirs(path)
    except FileExistsError:
        return False

def parse_log_name(log_file):
    """
    parse log's name and return precison core and batch_size values
    """
    logfile_result = {}
    logfile_info = os.path.splitext(log_file)[0].split('_')
    logfile_result['core'] = logfile_info[1]
    logfile_result['precision'] = logfile_info[2]
    logfile_result['batch_size'] = logfile_info[3]
    return logfile_result

def parse_to_excel(platform, report_path, log_file_name):
    """
    parse log to excel
    """
    logfile_result = parse_log_name(log_file_name)
    logfile_fullpath = os.path.join(report_path,log_file_name)
    single_file_dict = {}
    #Read output log file
    with open(logfile_fullpath, 'r') as ds_log:
        lines = ds_log.readlines()
        for line in lines:
            # Get latency
            if re.search("Inference latency:", line):
                single_loop_list = []
                latency=re.findall('\d+\.\d+', line)[0]
                single_loop_list.append(latency)
                print("latency:", float(latency))
            # Get first_token
            if re.search("First token average latency:", line):
                first_token=re.findall('\d+\.\d+', line)[0]
                single_loop_list.append(first_token)
                print("first_token:", float(first_token))
            if re.search("Average 2... latency:", line):
                second_token=re.findall('\d+\.\d+', line)[0]
                single_loop_list.append(second_token)
                print("second_token:",float(second_token))
            if re.search("Current\s+\d+-\d+-\w+.*", line):
                loop_time=re.findall('([0-9])', line)[0]
                current_frequency=re.findall('\d.\dGhz', line)[0]
                print("loop_time and current_frequency:", loop_time, current_frequency)
                single_file_dict[current_frequency] = single_loop_list
    
    logfile_result['kpi'] = single_file_dict
    return logfile_result

def save(index_tuples, data):
    """
    Save single dataframe
    Args:
        df_data (_type_): the require format of dataframe

    Returns:
        _type_: return dataframe instance
    """
    multi_index = pd.MultiIndex.from_tuples(index_tuples)                                
             
    cols = pd.MultiIndex.from_tuples([("Avg",), ("1st",), ("2nd",)], names=['fre'])
                       
    df = pd.DataFrame(data, columns=cols, index=multi_index)
    df.to_excel("3.xlsx")
    return df 


parser = argparse.ArgumentParser('Auto run the specify WL case', add_help=False)
parser.add_argument("--platform", "--p", default="SPR", type=str, help="hardware platform")

pass_args = parser.parse_args()
platform = pass_args.platform

base_path='/home/yangkun/lab/auto-opt/utils/report'

if platform.lower() == "spr":
    report_path='{0}/{1}'.format(base_path,'spr')
elif platform.lower() == "emr":
    report_path='{0}/{1}'.format(base_path,'emr')  
else:
    exit(1)

check_and_create_dir(os.path.join(report_path,"output"))

last_re = []
for file in os.listdir(report_path):
    if os.path.isfile(os.path.join(report_path,file)):
        single = parse_to_excel( platform, report_path, file)
        last_re.append(single)

with pd.ExcelWriter('2.xlsx') as writer:
    for value in last_re:
        result_df = list(value['kpi'].values())
        sun = list(value['kpi'].keys())
        index_tuples = [(i,) for i in sun]
        sheet_name = '{0}_{1}_{2}'.format(value['core'], value['precision'], value['batch_size'])
        save(index_tuples, result_df).to_excel(writer, sheet_name=sheet_name)
        
