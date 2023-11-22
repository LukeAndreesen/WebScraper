
import boto3
queue_name = 'html-update-queue'

sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName=queue_name)
wait_time = 10
max_number= 10  # max is 10

messages = queue.receive_messages(
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=wait_time
        )

print(messages)
