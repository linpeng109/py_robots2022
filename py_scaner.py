import time
from py_config import ConfigFactory
from py_logging import LoggerFactory
from paramiko import Transport

# 自动扫描机器人
class Scanner():
    def __init__(self, config, logger) -> None:
        self.config = config
        self.logger = logger
        self.hostname = self.config.get('kali', 'hostname')
        self.username = self.config.get('kali', 'username')
        self.password = self.config.get('kali', 'password')
        self.port = self.config.getint('kali', 'port')
        self.buffersize = 40960

    # 等待
    def waiting(self) -> None:
        for i in range(5):
            for ch in ['-', '\\', '|', '/']:
                print('\b%s' % ch, end='', flush=True)
                time.sleep(0.1)
        print('\b', end='', flush=True)

    # SSH命令执行器
    def ssh_command_excutor(self, cmd):
        client = Transport((self.hostname, self.port))
        client.connect(username=self.username, password=self.password)
        stdout_data = []
        stderr_data = []
        session = client.open_channel(kind='session')
        session.exec_command(cmd)
        while True:
            if session.recv_ready():
                stdout_data.append(session.recv(self.buffersize))
            if session.recv_stderr_ready():
                stderr_data.append(session.recv_stderr(self.buffersize))
            if session.exit_status_ready():
                break
            self.waiting()
        session.close()
        client.close()
        return stdout_data, stderr_data

    # 关键字检查
    def keyword_check(self, input_data) -> list:
        script_list = []
        for line in input_data:
            line = line.decode('utf-8').lower()
            # 从配置文件中获取对应表
            keyword_scripts = self.config.items('keyword_script')
            for script, keyword in keyword_scripts:
                if (keyword.lower() in line.lower()):
                    script_list.append(script)
        # 脚本列表去除重复
        script_list = list(set(script_list))
        return script_list

    # nmap端口扫描:构造nmap指令并处理返回结果
    def nmap(self, ip: str, port: int) -> list:
        nmap_cmd = self.config.get('commanders', 'nmap_cmd') % (port, ip)
        self.logger.info('nmap_cmd:%s' % nmap_cmd)
        stdout_data, stderr_data = self.ssh_command_excutor(cmd=nmap_cmd)
        self.logger.debug(stderr_data)
        for line in stdout_data:
            self.logger.info(line.decode('utf-8'))
        script_list = self.keyword_check(input_data=stdout_data)
        return script_list

    # gobuster目录扫描:构造gobuster指令并处理返回结果
    def gobuster(self, ip: str, port: int):
        gobuster_result = []
        gobuster_cmd = self.config.get(
            'commanders', 'gobuster_cmd') % (ip, port)
        self.logger.info('gobuster_cmd: %s' % gobuster_cmd)
        stdout_data, stderr_data = self.ssh_command_excutor(cmd=gobuster_cmd)

        if len(stdout_data) > 0:
            lines = stdout_data[0].decode('utf-8')
            line_list = lines.split('\n\r')
            for line in line_list:
                temp = line.replace(' ', '').replace('\r', '')
                end = temp.index('(Status:200)')
                temp = temp[:end]
                gobuster_result.append(temp)
        return gobuster_result

    # curl网页扫描:构造curl指令并处理返回结果
    def curl(self, ip: str, port: int, url_path_list):
        curl_cmd = self.config.get('commander', 'curl_cmd') % (ip, port)
        for url_path in url_path_list:
            stdout_data, stderr_data = self.ssh_command_excutor(
                cmd=curl_cmd+url_path)
            print(stdout_data)
            result_list = self.keyword_check(input_data=stdout_data)
            if len(result_list) > 0:
                break
        return result_list


if __name__ == '__main__':
    config = ConfigFactory(config_file='py_robot202.ini').get_config()
    logger = LoggerFactory(config_factory=config).get_logger()

    # 初始化
    scanner = Scanner(config=config, logger=logger)

    # 使用nmap扫描端口
    nmap_result = scanner.nmap(ip='172.22.225.228', port=18080)
    print(nmap_result)

    # 使用gobuster扫描目录
    # gobuster_result = scanner.gobuster(ip='192.168.33.238', port=18080)
    # print(gobuster_result)

    # 使用curl扫描网页
    # paths = ['/index.html', '/jobs', '/overview', '/assets', '/config', '/libs', '/datasets']
    # curl_result = scanner.curl(
    #     curl_cmd=r'curl http://192.168.33.238:18080', url_path_list=paths)
    # print(curl_result)
