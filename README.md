# aws_billing

$ sam build
$ sam local invoke -e events/event.json --parameter-overrides SlackWebhookUrl=https://hooks.slack.com/services/hoge
$ sam deploy --parameter-overrides SlackWebhookUrl=https://hooks.slack.com/services/hoge
