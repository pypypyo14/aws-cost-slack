import boto3
import json
import os
import requests
import datetime
import calendar
from dateutil.relativedelta import relativedelta

SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
TODAY = datetime.date.today()


def post_slack(message):
    payload = {
        'text': message
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        print(e)
    else:
        print(response.status_code)


def create_aws_sessions(region):
    sts = boto3.client('sts', region_name=region)
    ce = boto3.client('ce', region_name=region)
    return sts, ce


def query_account_id(sts):
    return sts.get_caller_identity()['Account']


def query_total_cost(ce):
    start = str(get_first_day(TODAY))
    end = str(get_first_day(TODAY + relativedelta(months=1)))

    res = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start,
            'End': end
        },
        Granularity='MONTHLY',
        Metrics=[
            'UnblendedCost'
        ]
    )
    return res['ResultsByTime'][0]['Total']['UnblendedCost']


def query_service_cost(ce):
    start = str(get_first_day(TODAY))
    end = str(get_first_day(TODAY + relativedelta(months=1)))

    res = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start,
            'End': end
        },
        Granularity='MONTHLY',
        Metrics=[
            'UnblendedCost'
        ],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )

    billings = []
    for item in res['ResultsByTime'][0]['Groups']:
        cost = item['Metrics']['UnblendedCost']['Amount']
        billings.append({
            'service':  item['Keys'][0],
            'billing':  cost
        })

    return billings


def get_first_day(date):
    return date.replace(day=1)


def get_last_day(date):
    return date.replace(day=calendar.monthrange(date.year, date.month)[1])


def generate_message(accound_id, total_cost, services_cost):
    unit = total_cost['Unit']
    total = round(float(total_cost['Amount']), 2)

    title = f'今月のAWS請求額は {total:.2f} {unit}です。'
    id = f'アカウントID: {accound_id}'
    messages = [title, id]
    for item in services_cost:
        service = item['service']
        billing = round(float(item['billing']), 2)
        if billing != 0.00:
            messages.append(f' ・{service}: {billing:.2f} {unit}')

    return '\n'.join(messages)


def lambda_handler(event, context):
    sts, ce = create_aws_sessions('us-east-1')
    accound_id = query_account_id(sts)
    total_cost = query_total_cost(ce)
    services_cost = query_service_cost(ce)
    message = generate_message(accound_id, total_cost, services_cost)

    post_slack(message)


'''
accountId: 
x月分のAWS請求額は ${full_cost}です。
'''
