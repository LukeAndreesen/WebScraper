import json
import smart_queue
import processor
import sys
import boto3
import os
import csv
import datetime
import time
import logging
import requests

from processor import Processor
from smart_queue import SmartQueue

#logging.basicConfig(filename='warn.log', level=logging.WARN)
SQS_PROFILE = 'SQS-consume-html-queue-550716682872'
SQS_SESSION = boto3.Session(profile_name = SQS_PROFILE)
QUEUE_NAME = 'html-update-queue'

S3_PROFILE = 'S3-website-crawler-550716682872'
S3_SESSION = boto3.Session(profile_name = S3_PROFILE)
BUCKET_NAME = 'website-crawler'

RETRY_CODES = [408, 409, 413, 415, 417, 421, 451]


def get_message():

    sqs = SQS_SESSION.resource('sqs')
    sqs_queue = sqs.get_queue_by_name(QueueName = QUEUE_NAME)
    #wait_time = 10
   # max_number= 10  # max is 10

    for message in sqs_queue.receive_messages(MessageAttributeNames=['All']):
        return message

def get_metadata(domain, metadata):
    current_datetime = datetime.datetime.now()
    formatted_date = current_datetime.strftime("%Y-%m-%d")
    s3 = S3_SESSION.resource('s3')
    try:
        # Object found in success directory
        object = s3.Object(BUCKET_NAME, ('metadata/success' + domain + '.json'))
        data = object.get()
        json_string = json.loads(json.loads(['Body'].read().decode('utf-8')))
        json_string[formatted_date] = metadata
        return (json_string, 'success')
    except:
        try:
        # Object found in low_count directory
            object = s3.Object(BUCKET_NAME, ('metadata/failure' + domain + '.json'))
            data = object.get()
            json_string = json.loads(json.loads(['Body'].read().decode('utf-8')))
            json_string[formatted_date] = metadata
            return (json_string, 'fail')
        except:
            try:
            # Object found in failure directory
                object = s3.Object(BUCKET_NAME, ('metadata/low_count' + domain + '.json'))
                data = object.get()
                json_string = json.loads(json.loads(['Body'].read().decode('utf-8')))
                json_string[formatted_date] = metadata
                return (json_string, 'low_count')
            except:
                json_string = {formatted_date: metadata}

def get_attempts():
    s3 = S3_SESSION.resource('s3')                                              
    bucket = s3.Bucket(BUCKET_NAME) 
# check metadata/success and metadata/failure, if not in either, attempts = 0
# otherwise, attempts = attempts + 1 

def retry(code):
    if (int(code) >= 500) or (int(code) in RETRY_CODES):
      return True
    return False

def main(sqs_name, number_links):
    # Create loggers for standard output and error
    start_time = time.time()
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H:%M:%S")
    formatted_date = current_datetime.strftime("%Y-%m-%d")

    subdirectory_name = "scraper_results"
    directory_path = os.path.join(os.getcwd(), subdirectory_name, formatted_date)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        os.makedirs(os.path.join(directory_path, "results"))
        os.makedirs(os.path.join(directory_path, "processes"))
        os.makedirs(os.path.join(directory_path, "errors"))

 #   stdout_logger = logging.getLogger('stdout')
    
    
#    results_file = os.path.join(directory_path, "results", f"{formatted_datetime}.txt")
    process_file = os.path.join(directory_path, "processes", f"{formatted_datetime}.txt")
    error_file = os.path.join(directory_path, "errors", f"{formatted_datetime}.txt")
    master_file = os.path.join(os.getcwd(), subdirectory_name, "master.csv")
    

    word_counts = {}
    check_files = []

    sqs = SQS_SESSION.resource('sqs')
    sqs_queue = sqs.get_queue_by_name(QueueName = QUEUE_NAME)
    s3 = S3_SESSION.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)

    try:
        with open(process_file, 'w') as log_file:
            with open(error_file, 'w') as error_file:
#      save          sys.stdout = log_file
# save     sys.stderr = error_file
                link_count = 0
                tst = s3.Object(BUCKET_NAME, 'html_data/360advanced.com.json')
                print(tst["domain"])
                while(link_count < number_links):
                    url = ''
                    message = None
                    status = "success"
                    try:
                        message = get_message()
                        url = 'http://' + message.message_attributes['domain']['StringValue']
                        response = requests.get(url)
                        code = response.status_code
                        f = open(master_file, "w")
                        f.write(url + ',')
                        f.write(',')
                        f.close

                        link_count += 1
                        #print(url)
                        try:
                # for row in reader:
                            #link_count += 1
                            queue = SmartQueue(url)
                           # results_file = os.path.join(directory_path, "results", queue.result_file)
                            queue.run_all()
                            word_counts[queue.root] = queue.total_words
                            if queue.total_words < 500:
                                check_files.append(queue.root)
                            p = Processor(queue)#, results_file)
                            text = p.get_text()
                            
                            data = {
                                    "domain": queue.root,
                                    "date": formatted_datetime,
                                    "count": queue.total_words, #this will need to be updated
                                    "html": text
                            }
                            error_data = {
                                        "url": url,
                                        "date": formatted_datetime,
                                        "response_code": code
                            }
                            json_data = json.dumps(data, indent = 2)
# Case 1: No words found 
                            if queue.total_words == 0:
                                status = "fail"
                                json_error_data = json.dumps(error_data, indent = 2)
                                json_metadata = json.dumps(metadata, indent = 2)
    # Case 1a: Code is worth retrying
                                if retry(code):
                                  bucket.put_object(Body = json.dumps(json_error_data), Key = ('flagged_links/redirects/' + queue.home_domain + 'json'))
    # Case 1b: Code is not worth retrying
                                else:
                                  bucket.put_object(Body = json.dumps(json_error_data), Key = ('flagged_links/error_links/' + queue.home_domain + '.json'))
# Case 2: < 500 words found 
                            elif queue.total_words < 500:
                                status = "low_count"
                                bucket.put_object(Body = json.dumps(json_data), Key = ('flagged_links/low_count/' + queue.home_domain + '.json'))
                            else:
# Case 3: Successful link
                                bucket.put_object(Body = json.dumps(json_data), Key = ('html_data/' + queue.home_domain + '.json'))
                            message.delete()
                            metadata = {
                                    "domain": queue.root,
                                    "response_code": code,
                                    "word_count": queue.total_words,
                                    "status": status
                            }
# Upload metadata
                            json_string, current_bucket = get_metadata(queue.home_domain, metadata)
# Add metadata to metadata/fail, remove from previous bucket if necessary
                            if status == "fail":
                                bucket.put_object(Body = json.dumps(json_metadata), Key = (f'metadata/fail/{queue.home_domain}.json'))
                                if (current_bucket != "fail") and (current_bucket is not None):
                                    s3.Object(BUCKET_NAME, (f'metadata/{current_bucket}/{queue.home_domain}.json')).delete()
                            if status == "low_count":
                                bucket.put_object(Body = json.dumps(json_metadata), Key = (f'metadata/low_count{queue.home_domain}.json'))
                                if (current_bucket != "low_count") and (current_bucket is not None):
                                    s3.Object(BUCKET_NAME, (f'metadata/{current_bucket}/{queue.home_domain}.json')).delete()
                            else:
                                bucket.put_object(Body = json.dumps(json_metadata), Key = (f'metadata/success/{queue.home_domain}.json'))
                                if (current_bucket != "success") and (current_bucket is not None):
                                    s3.Object(BUCKET_NAME, (f'metadata/{current_bucket}/{queue.home_domain}.json')).delete()
                        except Exception as scraper_error:
                            error_file.write(str(scraper_error))
                            check_files.append(url)
                            error_data = {
                                    "url": url,
                                    "date": formatted_datetime
                            }
                            json_error_data = json.dumps(error_data, indent = 2)
                            bucket.put_object(Body = json.dumps(json_error_data), Key = ('flagged_links/error_links/' + queue.home_domain + '.json'))
                            message.delete() # remove bad link from queue, but save it in bucket
                    except Exception as sqs_error:
                        logging.error(f"An error with sqs occurred at {formatted_datetime}: {str(sqs_error)}\n\n\n\n\n", exc_info=True)
                        error_data = {
                                "url": url,
                                "date": formatted_datetime
                        }
                        # procedures here to kill the process, recover server
                        json_error_data = json.dumps(error_data, indent = 2)
                        bucket.put_object(Body = json.dumps(json_error_data), Key = ('flagged_links/error_links/' + queue.home_domain + '.json'))
                        if (len(url) > 0) and (message is not None):
                            message.delete()


            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Script completed in {elapsed_time:.2f} seconds for {link_count} links")
            print(f"Average time per link: {(elapsed_time/link_count):.2f} seconds")
            print(f"Links to check:")
            if len(check_files) == 0:
                print(f"None")
            else:
                for filename in check_files:
                    print(f"{filename}")
            print(f"\n Word Counts")
            for key, value in word_counts.items():
                print(f"{key}, {value}")
    except Exception as e:
        logging.error(f"An error occurred at {formatted_datetime}: {str(e)}", exc_info=True)



        
if __name__ == "__main__":
    number_links = sys.argv[1]
    main('html-update-queue', int(number_links))
