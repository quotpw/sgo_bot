import json
import pathlib

states = json.loads(
    open(str(pathlib.Path(__file__).parent.resolve()) + '/city_data.json', 'r', encoding='utf-8').read())

states_name = [state['name'] for state in states]


def search_state(value: str):
    value = value.lower()
    for state in states:
        if value in str(state['name']).lower():
            return state


def get_city_names(state_name):
    return [city['name'] for city in search_state(state_name)['cities']]


def search_city(value: str):
    value = value.lower()
    ret = []
    for state in states:
        for city in state['cities']:
            if value in city['name'].lower():
                ret.append({'state_id': state['id'], 'city': city})
    return ret


def search_orgs_by_city(city: dict, org_name: str):
    org_name = org_name.lower()
    for orgs in city['oo_types']:
        if org_name in orgs['name'].lower():
            return {'id': orgs['id'], 'orgs': orgs['organizations']}


def search_schools(organizations: dict, value):
    ret = []
    if isinstance(value, str):
        value = value.lower()
        for organization in organizations:
            if value in organization['name'].lower():
                ret.append(organization)
    elif isinstance(value, int):
        for organization in organizations:
            if value == organization['id']:
                ret.append(organization)
    return ret

# city = search_city("Краснод")
# print(city)
# org = search_orgs_by_city(city['city'], "Обще")
# print(org)
# print(find_school(org['orgs'], '№95'))
