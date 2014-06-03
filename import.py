#!/usr/bin/python3
import sys
import os
import re
import pickle

sys.path.insert(0, os.path.abspath("../teapot"))

import sqlalchemy
import sqlalchemy.orm

import lxml.etree as etree

import teapot.timeutils

import priyom.config
priyom.config.base_path = "/var/www/docroot/horazont/projects/priyomdb2"
priyom.config.recalc_paths()

import priyom.api.initializer
import priyom.model

from datetime import timedelta, datetime
from xsltea.namespaces import NamespaceMeta

class pxmlns(metaclass=NamespaceMeta):
    xmlns = "http://api.priyom.org/priyomdb"

dbengine = sqlalchemy.create_engine(
    "mysql+mysqlconnector://priyom2@localhost/priyom2?charset=utf8",
    echo=False,
    encoding="utf8",
    convert_unicode=True)
priyom.model.Base.metadata.create_all(dbengine)
dbsession = sqlalchemy.orm.sessionmaker(bind=dbengine)()

priyom.api.initializer.create_base_data(dbsession)
rootuser = dbsession.query(priyom.model.User).filter(
    priyom.model.User.loginname == "root").one()

def convert_station(node):
    id = node.find(pxmlns.ID).text
    if id in ignore_stations:
        return
    enigma_id = node.find(pxmlns.EnigmaIdentifier).text or ""
    priyom_id = node.find(pxmlns.PriyomIdentifier).text or ""
    try:
        station = dbsession.query(priyom.model.Station).get(station_map[id])
        station.enigma_id = enigma_id
        station.priyom_id = priyom_id
    except KeyError:
        station = priyom.model.Station(
            enigma_id,
            priyom_id)
        dbsession.add(station)
        dbsession.commit()
        assert station.id is not None
        station_map[id] = station.id

    station.nickname = node.find(pxmlns.Nickname).text
    station.description = node.find(pxmlns.Description).text
    station.status = node.find(pxmlns.Status).text
    station.location = node.find(pxmlns.Location).text
    dbsession.commit()
    print("mapped station: {} -> {}".format(
        id, station.id))

def convert_mode(display_name):
    try:
        return dbsession.query(priyom.model.Mode).filter(
            priyom.model.Mode.display_name == display_name).one()
    except sqlalchemy.orm.exc.NoResultFound:
        mode = priyom.model.Mode(display_name)
        dbsession.add(mode)
        dbsession.commit()
        return mode

def convert_broadcast(node):
    id = node.find(pxmlns.ID).text
    if node.find(getattr(pxmlns, "has-transmissions")) is None:
        return

    station = dbsession.query(priyom.model.Station).get(
        station_map[node.find(pxmlns.StationID).text])

    try:
        broadcast = dbsession.query(priyom.model.Event).get(broadcast_map[id])
    except KeyError:
        broadcast = priyom.model.Event()
        dbsession.add(broadcast)

    broadcast.approved = True
    broadcast.start_time = datetime.utcfromtimestamp(
        int(node.find(pxmlns.Start).attrib["unix"]))
    broadcast.end_time = datetime.utcfromtimestamp(
        int(node.find(pxmlns.Start).attrib["unix"]))
    broadcast.event_class = None
    broadcast.station = station
    dbsession.commit()

    new = set(
        (freqnode.attrib["modulation"], int(freqnode.text))
        for freqnode in node.findall(pxmlns.frequency))
    old = {
        (freq.mode.display_name, freq.frequency): freq
        for freq in broadcast.frequencies}
    oldkeys = set(old.keys())

    for k in oldkeys - new:
        obj = old[k]
        broadcast.frequencies.remove(obj)
        dbsession.delete(obj)
        dbsession.commit()

    for newmod, newfreq in new - oldkeys:
        newmod = convert_mode(newmod)
        obj = priyom.model.EventFrequency()
        obj.frequency = newfreq
        obj.mode = newmod
        obj.event_id = broadcast.id
        dbsession.add(obj)
        dbsession.commit()

    broadcast_map[id] = broadcast.id
    print("mapped broadcast: {} -> {}".format(
        id, broadcast.id))

CONTENTS_SPLIT_RE = re.compile(
    "(([^/ ]+)|([^/ ]+)/([^/ ]+):(\w+))( |$)")

def split_contents(s):
    lhs = []
    rhs = []
    alphabet = None
    for _, simple, complex_lhs, complex_rhs, complex_alphabet, _ in \
            CONTENTS_SPLIT_RE.findall(s):
        if complex_alphabet:
            alphabet = complex_alphabet
        if simple:
            lhs.append(simple)
            rhs.append(simple)
            continue
        lhs.append(complex_lhs)
        rhs.append(complex_rhs)
    result = [
        ("la", " ".join(lhs))
    ]
    if rhs != lhs:
        result.insert(0, ("ru", " ".join(rhs)))
    return result

def convert_alphabet(alphabet):
    try:
        alphabet_obj = dbsession.query(
            priyom.model.Alphabet
        ).filter(
            priyom.model.Alphabet.short_name == alphabet
        ).one()
    except sqlalchemy.orm.exc.NoResultFound:
        alphabet_obj = priyom.model.Alphabet(alphabet, alphabet)
        dbsession.add(alphabet_obj)
        dbsession.commit()
    return alphabet_obj

def convert_transmission(node):
    id = node.find(pxmlns.ID).text
    if id in ignore_transmissions:
        return
    if id in transmission_map:
        return

    if not node.find(pxmlns.Contents).text:
        # FIXME: there are some inaudible transmissions with recordings without
        # contents
        return

    broadcast = dbsession.query(priyom.model.Event).get(
        broadcast_map[node.find(pxmlns.BroadcastID).text])

    format = dbsession.query(priyom.model.TransmissionFormat).get(
        format_map[int(node.find(pxmlns.ClassID).text)])

    callsigns_per_alphabet = {}
    for callsign_node in node.findall(pxmlns.Callsign):
        if not callsign_node.text:
            continue
        alphabet = callsign_node.get("lang", "la")
        callsigns_per_alphabet[alphabet] = callsign_node.text

    tmpnode = node.find(pxmlns.Remarks)
    attribution = None if tmpnode is None else tmpnode.text

    destinations = []
    contents_split = split_contents(node.find(pxmlns.Contents).text)
    for alphabet, contents in contents_split:
        if alphabet in callsigns_per_alphabet:
            contents = callsigns_per_alphabet[alphabet] + " " + contents

        alphabet_obj = convert_alphabet(alphabet)

        try:
            contents_obj = format.parse(contents)
        except ValueError as err:
            print("Failed to parse [txid={}]: {}".format(
                id,
                contents))
            for existing in destinations:
                dbsession.delete(existing)
                dbsession.commit()
            return
        # this is a nasty hack
        contents_obj.is_transcribed = (alphabet == "la" and
                                       len(contents_split) > 1)
        contents_obj.attribution = attribution
        contents_obj.event = broadcast
        contents_obj.alphabet = alphabet_obj
        if destinations:
            contents_obj.parent_contents = destinations[0]

        dbsession.add(contents_obj)
        destinations.append(contents_obj)
        dbsession.commit()

    transmission_map[id] = [obj.id for obj in destinations]
    print("mapped transmission: {} -> {}".format(
        id, ", ".join(str(obj.id) for obj in destinations)))


# STATIC DEFINES FOR CONVERSION

format_map = {
    1: 1,
    2: 2,
    6: 3,
    8: 5,
    9: 4,
    3: 7,
    4: 6
}

ignore_stations = {'196', '197', '198'}
ignore_transmissions = {
    '275',
    '292', # malformed foreign part
    '293', # malformed foreign part
    '305', # malformed foreign part
    '312', # malformed message
    '314', # dito
    '315', # dito
    '317', # dito
    '324', # dito
}

# END OF STATIC DEFINES FOR CONVERSION

if __name__ == "__main__":
    try:
        with open("conversion.state", "rb") as f:
            conversion_state = pickle.load(f)
    except OSError:
        conversion_state = ({}, {}, {})

    station_map, broadcast_map, transmission_map = conversion_state

    try:
        with open("export.xml", "rb") as f:
            tree = etree.fromstring(f.read())

        for station_node in tree.find(pxmlns.stations):
            convert_station(station_node)

        for broadcast_node in tree.find(pxmlns.broadcasts):
            convert_broadcast(broadcast_node)

        for transmission_node in tree.find(pxmlns.transmissions):
            convert_transmission(transmission_node)

    finally:
        with open("conversion.state", "wb") as f:
            pickle.dump(conversion_state, f)
