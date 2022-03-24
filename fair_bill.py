#!/usr/bin/python3

import re
import time
import logging
import sys
from datetime import datetime


def get_user_session_details(hosted_app_log):
    active_users = {}
    user_completed_sessions = {}
    log_end_time = None
    log_start_time = None

    patternString = r"^(\d\d:\d\d:\d\d) ([a-zA-Z]+\w+) (Start|End)$"
    pattern = re.compile(patternString)

    with open(hosted_app_log) as app_logs:

        for line in app_logs:
            matcher = pattern.findall(line.strip())

            user = None
            session_status = None
            session_time = None

            if not matcher:
                logging.info("Invalid_line - " + line)
                continue

            try:
                session_time = datetime.strptime(matcher[0][0], "%H:%M:%S")
                if log_start_time is None:
                    log_start_time = session_time

                user = matcher[0][1]
                session_status = matcher[0][2]
                log_end_time = session_time
            except Exception as e:
                logging.info("Invalid data - " + line + repr(e))
                continue

            user_session = active_users.get(user, None)

            if user_session is None:
                active_users[user] = []

            if session_status == "Start":
                active_users[user].append({session_status: session_time})
            else:
                session_times = get_completed_session_times(user, active_users,
                                                            log_start_time,
                                                            session_time)

                update_completed_sessions(user, session_times,
                                          user_completed_sessions)

    logging.debug(active_users, log_end_time)
    update_remaining_active_users(active_users, log_end_time,
                                  user_completed_sessions)
    print()
    return user_completed_sessions


def update_remaining_active_users(active_users, log_end_time,
                                  user_completed_sessions):
    """session times for remaining "Start" status."""
    active_usernames = [k for k, v in active_users.items() for vi in v
                        if 'Start' in vi]
    for username in active_usernames:
        while len(active_users[username]) > 0:
            user_session = active_users[username].pop()
            # if 'Start' not in user_session:
            #     logging.info("Some")
            session_times = (user_session['Start'], log_end_time)
            update_completed_sessions(username, session_times,
                                      user_completed_sessions)


def update_completed_sessions(user, session_times, user_completed_sessions):
    completed_sessions = user_completed_sessions.get(user, [])
    completed_sessions.append(session_times)
    user_completed_sessions[user] = completed_sessions


def get_completed_session_times(user, active_users, log_start_time,
                                session_end_time):
    """session times for all "End" status."""
    session_times = None

    if len(active_users[user]) <= 0:
        session_times = (log_start_time, session_end_time)
    else:
        while len(active_users[user]) > 0:
            user_session = active_users[user].pop()

            if 'Start' in user_session:
                session_times = (user_session['Start'], session_end_time)
                break
            else:
                continue

    return session_times


def show_report(user_completed_sessions):
    """Final User Session results"""
    print()
    for k, v in sorted(user_completed_sessions.items()):
        total_sec = 0
        total_sec = sum([int((vi[1] - vi[0]).total_seconds()) for vi in v])

        print(k, len(v), total_sec)


def setup_logging():

    log_file = "./fair_bill_"
    log_file += time.strftime("%d-%b-%Y")
    log_file += ".log"

    open(log_file, "a+")

    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s -"
                        " %(funcName)s - %(message)s - %(lineno)d")


def get_session_log_file_path():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('file_name')
    args, unknown = parser.parse_known_args()
    logging.info("app_log_file " + str(args.file_name))
    from os.path import exists as file_exists

    if file_exists(args.file_name):
        return args.file_name
    else:
        logging.info("File Not Found -" + args.file_name)
        logging.info("Bye")
        sys.exit(1)


setup_logging()

if __name__ == "__main__":
    session_log_file_path = get_session_log_file_path()
    user_completed_sessions = get_user_session_details(session_log_file_path)
    show_report(user_completed_sessions)
