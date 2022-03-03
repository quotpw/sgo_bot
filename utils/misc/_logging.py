import logging

import configcatclient

from config import cat_keys


def set_logging_level():
    logging.basicConfig(
        format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
        level=eval(f'logging.{config.get_value("debug_level", "DEBUG")}')
    )


config = configcatclient.create_client_with_auto_poll(
    cat_keys.CODE,
    on_configuration_changed_callback=set_logging_level
)
