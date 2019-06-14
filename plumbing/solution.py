#!/usr/bin/env python3
import os
import argparse
import datetime
import time
import json
import hashlib

import githash


def gen_sha_string(treehash, parenthash, adm_tstamp, com_tstamp, message):
    """Reference: https://gist.github.com/masak/2415865

    """
    sha_string = (
        "tree {}\n"
        "parent {}\n"
        "author admin <admin@example.com> {}\n"
        "committer admin <admin@example.com> {}\n"
        "\n{}\n".format(
            treehash, parenthash, adm_tstamp, com_tstamp, message
        )
    )

    final_sha_string = "commit {}\0{}".format(len(sha_string), sha_string)
    return final_sha_string


def brute_force(output_dir, commits, maxrange, initial_parent_hash):
    # These argparse args are expected by githash
    parser = argparse.ArgumentParser('compute git hashes')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-k', '--keep-dot-git', action='store_true')
    parser.add_argument('path', nargs='+')
    args = parser.parse_args(['./'])
    args.depth = -1

    flag = ""
    last_parent_hash = initial_parent_hash
    utc_offset = 3600
    for commit in reversed(commits[:-1]):
        for i in range(1, maxrange):
            with open('{}/flag.txt'.format(output_dir), 'w') as flag_file:
                flag_file.write("{}{}".format(flag, i))

            th = githash.tree_hash('{}'.format(output_dir), args).hexdigest()

            date, date_ts = commit["date"].split('+')
            date = time.mktime(
                datetime.datetime.strptime(date.strip(), "%c").timetuple()
            ) - utc_offset

            sha_string = gen_sha_string(
                treehash=th,
                parenthash=last_parent_hash,
                adm_tstamp="{} +{}".format(int(date), date_ts),
                com_tstamp="{} +{}".format(int(date), date_ts),
                message=commit["message"],
            )
            commit_hash = hashlib.sha1(sha_string.encode()).hexdigest()

            if commit_hash == commit["commit"]:
                flag += str(i)
                last_parent_hash = commit_hash
                print("Found: {}".format(commit_hash))
                print("adding: " + str(i) + " => " + flag)
                break
        else:
            print("found nothing.")
    return flag


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Script to brute force adding a number until the correct'
                    'git hash is found as documented by a json file'
    )
    parser.add_argument(
        '-m', '--maxrange', type=int, required=True,
        help="recommended not to go above 1000000")
    parser.add_argument(
        '-j', '--json-file', type=str,
        default="./gitlog.json",
        help="location of file holding json data")
    parser.add_argument(
        '-o', '--output', type=str,
        default="/tmp/plumbing/",
        help="working directory for bruteforcing.")
    parser.add_argument(
        '-p', '--parent-hash', type=str,
        default="947322239b13ea1e7705981f41f4b40980788e2b",
        help="initial hash of parent commit")
    args = parser.parse_args()

    with open(args.json_file) as json_data:
        commits = json.load(json_data)

    if not os.path.exists(args.output):
        print("creating directory: {}...".format(args.output))
        os.makedirs(args.output)

    final_flag = brute_force(
        args.output,
        commits,
        args.maxrange,
        args.parent_hash
    )
    print("Flag is: \n{}".format(final_flag))


if __name__ == '__main__':
    main()
