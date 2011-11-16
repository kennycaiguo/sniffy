#!/usr/bin/env python2
# Copyright 2011 Tom Vincent <http://tlvince.com/contact/>

"""Sniff video hosting URLs for flash-free consumption."""

import pcap
import re
import logging
import os.path
import subprocess

def handles():
    """Format quvi's supported hosts."""
    # Get all hosts
    hosts = subprocess.check_output(["quvi", "--support"]).split("\n")[:-1]
    # Filter query formats
    hosts = [h.split("\t")[0] for h in hosts]
    # Replace weird sub-strings
    for pattern in [("%", ""), (".w+", ".com")]:
        original, replacement = pattern
        hosts = [h.replace(original, replacement) for h in hosts]
    # XXX: Split related websites
    related = []
    for i in hosts:
        related.extend(i.split("|"))
    return related

def handler(host, path, known_hosts, parser):
    """URL handler."""
    # Ignore root paths
    if len(path) == 1:
        return
    # XXX: can 'in' be greedier?
    if host.startswith("www."):
        host = host[4:]
    if host in known_hosts:
        url = "http://{0}{1}".format(host, path)
        cmd = parser + [url]
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    """Start execution of flashback."""
    mplayer = "mplayer -fs -really-quiet"
    quvi = "quvi --quiet --format=best --exec"
    parser = quvi.split(" ")
    parser.append("{0} %u".format(mplayer))

    known_hosts = handles()

    # Setup logging
    logging.basicConfig(format="%(name)s: %(levelname)s: %(message)s")
    logger = logging.getLogger(os.path.basename(__file__))

    pattern = re.compile("GET (.*) HTTP.*\nHost: ([^\r\n]*)")
    try:
        pc = pcap.pcap(name="eth0", snaplen=1500)
        pc.setfilter("tcp and dst port 80")
        for timestamp, packet in pc:
            regex = pattern.search(packet)
            if regex:
                handler(regex.group(2), regex.group(1), known_hosts, parser)
    except OSError:
        logger.error("must be run as root")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(e)

if __name__ == "__main__":
    main()
