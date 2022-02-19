from configparser import ConfigParser

path_to_config = 'data/config.ini'


def get_config_parser():
    parser = ConfigParser()
    parser.read(path_to_config)
    return parser


def get_data(section, option):
    parser = get_config_parser()
    return parser.get(section, option)


def set_data(section, option, value):
    parser = get_config_parser()
    parser.set(section, option, value)
    with open(path_to_config, 'w') as config_file:
        parser.write(config_file)
