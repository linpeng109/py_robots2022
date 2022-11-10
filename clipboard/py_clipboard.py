import base64
import json
import time
from threading import Thread

import requests

import py_pyperclip
from py_config import ConfigFactory
from py_logging import LoggerFactory

# 剪贴板监听器


class ClipboardListen:
    # 初始化
    def __init__(self, config: ConfigFactory, logger: LoggerFactory):
        self.config = config
        self.logger = logger
        self.ROBOTS = config.get('robots', 'keywords').split(';')
        self.ROBOT_URL = config.get('robots', 'robot_url')
        self.CHROME_DRIVER = config.get('robots', 'chrome_driver')

    # 清空剪贴板
    def __clipboard_clean(self):
        py_pyperclip.copy('')

    # 获取临时脚本
    def wget_script(self, script_name: str):
        try:
            # 获取脚本文本
            res = requests.get(self.ROBOT_URL+script_name)
            script_json = res.json()
            if script_json is not None:
                # base64解码
                script_bytes = base64.b64decode(script_json['data'])
                script_string = script_bytes.decode('utf-8')
                # self.logger.debug(script_string)
        except requests.exceptions.ConnectionError as error:
            self.logger.error(error)

        # 返回response
        return script_string

    # 监听剪贴板的变化
    def __listen(self):

        # 进入监听循环
        while True:
            # 获取剪贴板内容
            clip_txt = py_pyperclip.waitForPaste()

            # 循环检测关键词
            for robot in self.ROBOTS:

                # 如包含关键词
                if robot in clip_txt:

                    # 清空剪贴板内容
                    self.__clipboard_clean()

                    # 获取机器人类别
                    robot_type = clip_txt.split('%%')[1]
                    self.logger.debug('robot type:%s' % robot_type)

                    # 获取机器人参数
                    robot_params = str(clip_txt.replace(robot, '')).split(';')

                    try:
                        # 机器人参数检查
                        if len(robot_params) == 0 or robot_params[0].strip() == '':
                            error = Exception('软件机器人参数缺失')
                            raise error

                        # 兼容旧版的robot部分
                        if robot_type == r'robot':
                            robot_script = self.wget_script(robot_params[0])
                            exec(robot_script)

                        # 兼容旧版的chrom部分
                        elif robot_type == r'chrome':
                            robot_script = self.wget_script('chrome')
                            exec(robot_script, {'url': robot_params[0]})

                        # 新版机器人调用
                        elif robot_type == r'iamrobot':
                            robot_name = robot_params[0]
                            self.logger.debug('robot name: %s' % robot_name)
                            robot_script = self.wget_script(robot_name)
                            self.logger.debug('robot params : %s' %
                                              robot_params)
                            exec(robot_script, json.loads(robot_params[1]))

                    # 异常处理
                    except Exception as error:
                        self.logger.error(error)
            # 延时0.2
            time.sleep(0.2)

    # 启动子线程调用监听器
    def start(self):
        self.logger.info("The clipboard listen is running....")
        t = Thread(target=self.__listen)
        t.start()


if __name__ == '__main__':
    config = ConfigFactory(config_file='py_clipboard.ini').get_config()
    logger = LoggerFactory(config_factory=config).get_logger()

    clipboard_listen = ClipboardListen(config=config, logger=logger)
    clipboard_listen.start()
