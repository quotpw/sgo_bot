from . import configurator

BOT_TOKEN = configurator.get_data('telegram', 'token')

MYSQL_DATA = {
    'host': configurator.get_data('MySQL', 'host'),
    'port': int(configurator.get_data('MySQL', 'port')),
    'user': configurator.get_data('MySQL', 'user'),
    'password': configurator.get_data('MySQL', 'password'),
    'db_name': configurator.get_data('MySQL', 'database')
}
