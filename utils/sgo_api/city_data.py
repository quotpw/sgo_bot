import json
import pathlib
import re

from config.sgo import MATCH_SENSORE


def delete_censored_symbols(text):
    return re.sub(MATCH_SENSORE, '', text)


states = json.loads(
    delete_censored_symbols(
        open(str(pathlib.Path(__file__).parent.resolve()) + '/city_data.json', 'r', encoding='utf-8').read()
    )
)

states_name = [state['name'] for state in states]


def search_state(value: str):
    value = delete_censored_symbols(value.lower())
    for state in states:
        if value in str(state['name']).lower():
            return state


def get_city_names(state_name):
    return [city['name'] for city in search_state(state_name)['cities']]


def search_city(value: str):
    value = delete_censored_symbols(value.lower())
    ret = []
    for state in states:
        for city in state['cities']:
            if value in city['name'].lower():
                ret.append({'state_id': state['id'], 'city': city})
    return ret


def search_orgs_by_city(city: dict, org_name: str):
    org_name = delete_censored_symbols(org_name.lower())
    for orgs in city['oo_types']:
        if org_name in orgs['name'].lower():
            return {'id': orgs['id'], 'orgs': orgs['organizations']}


def search_schools(organizations: dict, value):
    ret = []
    if isinstance(value, str):
        value = delete_censored_symbols(value.lower())
        for organization in organizations:
            if value in organization['name'].lower():
                ret.append(organization)
    elif isinstance(value, int):
        for organization in organizations:
            if value == organization['id']:
                ret.append(organization)
    return ret
