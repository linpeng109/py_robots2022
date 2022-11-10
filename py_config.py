import configparser
from configparser import ConfigParser


class ConfigFactory(ConfigParser):
    def __init__(self, config_file: str):
        super(ConfigFactory, self).__init__()
        self.config = config_file
        self.parser = ConfigParser
        self._interpolation = None

    # 在配置文件中使用变量调用
    def optionxform(self, option_str):
        return option_str

    def set_config(self, section, option, value):
        self.read(self.config, 'utf-8')
        self.set(section=section, option=option, value=value)
        with open(self.config, 'w') as config_file:
            self.write(config_file)

    def get_config(self):
        # 在配置文件中使用变量调用
        self._interpolation = configparser.ExtendedInterpolation()
        self.read(filenames=self.config, encoding='utf-8')
        return self
