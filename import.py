#!/usr/bin/python3
import logging
import os
import pickle
import re
import sys

sys.path.insert(0, os.path.abspath("../teapot"))

import sqlalchemy
import sqlalchemy.orm

import lxml.etree as etree

import teapot.timeutils

import priyom.model
import priyom.config

from datetime import timedelta, datetime
from xsltea.namespaces import NamespaceMeta

class pxmlns(metaclass=NamespaceMeta):
    xmlns = "http://api.priyom.org/priyomdb"

_dbengine = sqlalchemy.create_engine(
    priyom.config.database_url,
    echo=False,
    encoding="utf8",
    convert_unicode=True)
dbsession = sqlalchemy.orm.sessionmaker(bind=_dbengine)()

logger = logging.getLogger()

E07_FORMAT = re.compile(r"\d{3}\s+\d{1,3}")
E07A_FORMAT = re.compile(r"\d{3}\s+\d{1,3}\s+\d{5}")

class F:
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)

def prefilter_contents_text(s):
    return s.replace("&nbsp;", " ").replace("&nbsp", " ")

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
    logger.info(F("mapped station: {} -> {}", id, station.id))

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
    logger.info(F("mapped broadcast: {} -> {}", id, broadcast.id))

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
            lhs.append(prefilter_contents_text(simple))
            rhs.append(prefilter_contents_text(simple))
            continue
        lhs.append(prefilter_contents_text(complex_lhs))
        rhs.append(prefilter_contents_text(complex_rhs))
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

    try:
        format_handler = override_format_handler[id]
    except KeyError:
        try:
            format_handler = format_handler_map[int(node.find(pxmlns.ClassID).text)]
        except KeyError as err:
            logger.error(F(
                "cannot convert transmission (txid={}): "
                "missing format map entry for format id {}",
                id,
                err))
            return

    tmpnode = node.find(pxmlns.Remarks)
    attribution = None if tmpnode is None else tmpnode.text

    try:
        contents = override_contents[id]
    except KeyError:
        contents = [node.find(pxmlns.Contents).text]

    try:
        destinations = list(format_handler(broadcast, contents, node))
    except ValueError as err:
        print("while converting tx (id={}): {}".format(id, err.args[0].format(*err.args[1:])))
        raise
    for dest in destinations:
        dest.attribution = attribution

    transmission_map[id] = [obj.id for obj in destinations]
    print("mapped transmission: {} -> {}".format(
        id, ", ".join(str(obj.id) for obj in destinations)))


# STATIC DEFINES FOR CONVERSION

def parse_split_contents(broadcast, fmt, contents_split):
    destinations = []
    for alphabet, contents in contents_split:
        alphabet_obj = convert_alphabet(alphabet)

        try:
            contents_nodes = list(fmt.parse(contents))
        except ValueError as err:
            for existing in destinations:
                dbsession.delete(existing)
                dbsession.commit()
            raise ValueError("Failed to parse contents: {!r} (error: {})",
                             contents,
                             str(err))
        else:
            contents_obj = priyom.model.StructuredContents("text/plain", fmt)
            contents_obj.nodes.extend(contents_nodes)
        # this is a nasty hack
        contents_obj.is_transcribed = (alphabet == "la" and
                                       len(contents_split) > 1)
        contents_obj.event = broadcast
        contents_obj.alphabet = alphabet_obj
        if destinations:
            contents_obj.parent_contents = destinations[0]

        dbsession.add(contents_obj)
        destinations.append(contents_obj)
        dbsession.commit()
    return destinations

def simple_format_handler(format_id):
    fmt = dbsession.query(priyom.model.Format).get(format_id)
    def handle_simple_format(broadcast, contents, node):
        callsigns_per_alphabet = {}
        for callsign_node in node.findall(pxmlns.Callsign):
            if not callsign_node.text:
                continue
            alphabet = callsign_node.get("lang", "la")
            if alphabet == "la":
                try:
                    callsigns_per_alphabet[alphabet] = callsign_map[callsign_node.text]
                except KeyError:
                    pass
                else:
                    continue
            callsigns_per_alphabet[alphabet] = callsign_node.text

        try:
            latin_callsign = callsigns_per_alphabet["la"]
        except KeyError:
            pass
        else:
            try:
                substitute_ru_callsign = la_ru_callsign_map[latin_callsign]
            except KeyError:
                pass
            else:
                callsigns_per_alphabet.setdefault("ru", substitute_ru_callsign)


        for content in contents:
            contents_split = split_contents(content)
            yield from parse_split_contents(broadcast, fmt, [
                (alphabet, ("" if alphabet not in callsigns_per_alphabet else
                            (callsigns_per_alphabet[alphabet] + " ")) + contents)
                for alphabet, contents in contents_split
            ])
    return handle_simple_format

def fmt_5figure_groups(with_callsign, without_callsign, e07a_format, e07_format):
    with_callsign = simple_format_handler(with_callsign)
    without_callsign = simple_format_handler(without_callsign)
    e07 = simple_format_handler(e07_format)
    e07a = simple_format_handler(e07a_format)
    def handle_5figure_format(broadcast, contents, node):
        logger.debug("5fig disambiguator")
        callsign_node = node.find(pxmlns.Callsign)
        if callsign_node is not None and callsign_node.text:
            callsign_text = callsign_node.text.replace("/", " ")
            if callsign_text.strip() == contents[0].strip():
                logger.debug("callsign matches message, stripping")
                callsign_node.text = None
                return without_callsign(broadcast, contents, node)
            callsign_node.text = callsign_text
            if E07A_FORMAT.match(callsign_text):
                logger.debug("using e07a")
                return e07a(broadcast, contents, node)
            prev_err = None
            try:
                if E07_FORMAT.match(callsign_text):
                    logger.debug("trying e07")
                    return e07(broadcast, contents, node)
            except ValueError as err:
                logger.debug(F("failed with {}, continuing with normal", err))
                prev_err = err
            try:
                logger.debug("trying normal, incl. callsign")
                return with_callsign(broadcast, contents, node)
            except ValueError as err:
                if prev_err:
                    raise prev_err
                else:
                    raise
        else:
            return without_callsign(broadcast, contents, node)
    return handle_5figure_format

def dlya_format_handler(format_id):
    fmt = dbsession.query(priyom.model.Format).get(format_id)
    simple_handler = simple_format_handler(format_id)
    def handle_dlya_format(broadcast, contents, node):
        callsign_node = list(node.findall(pxmlns.Callsign))
        for node in callsign_node:
            text = node.text
            if text is None:
                continue
            text = text.lower()
            if text in {"dyla", "dlya"}:
                node.getparent().remove(node)

        return simple_handler(broadcast, contents, node)
    return handle_dlya_format

def fmt_4figure_groups(plain_4figure, with_3figure_callsign):
    plain_4figure = simple_format_handler(plain_4figure)
    with_3figure_callsign = simple_format_handler(with_3figure_callsign)
    def handle_4figure_format(broadcast, contents, node):
        logger.debug("4fig disambiguator")
        callsign_node = node.find(pxmlns.Callsign)
        if callsign_node is not None and callsign_node.text:
            return with_3figure_callsign(broadcast, contents, node)
        else:
            return plain_4figure(broadcast, contents, node)

    return handle_4figure_format


_5fig_handler = fmt_5figure_groups(with_callsign=2,
                                   without_callsign=6,
                                   e07a_format=8,
                                   e07_format=9) # 5 figure groups (with callsign)

format_handler_map = {
    1: simple_format_handler(1), # monolyth
    2: _5fig_handler,
    3: dlya_format_handler(3), # dlya (w/o numbers)
    4: dlya_format_handler(4), # dlya (w/ numbers)
    6: _5fig_handler,
    8: simple_format_handler(10),
    9: fmt_4figure_groups(plain_4figure=11,
                          with_3figure_callsign=12)
}

ignore_stations = {'196', '197', '198'}
ignore_transmissions = {
    '263', # malformed message (fixed in live db)
    '275', # malformed message (fixed in live db)
    '305', # malformed foreign part (fixed in live db)
    '314', # format not recognized by live db, retranscription in pad
    '315', # format not recognized by live db, retranscription in pad
    '317', # format not recognized by live db, retranscription in pad
    '324', # format not recognized by live db, retranscription in pad
    '380', # malformed foreign part (fixed in live db)
    '381', # malformed foreign part (fixed in live db)
    '396', # format not recognized by live db, retranscription in pad
    '411', # horribly broken (fixed in live db)
    '414', # malformed foreign part (fixed in live db)
    '418', # malformed foreign part (fixed in live db)
    '595', # incorrect “callsign” (fixed in live db)
    '596', # incorrect data (fixed in live db)
    '662', # incorrect data (fixed in live db)
    '664', # incorrect “callsign” (fixed in live db)
    '738', # bogus callsign (fixed in live db)
    '806', # messed up, retranscription in pad
    '1091', # format not recognized by live db, retranscription in pad
    '1092', # format not recognized by live db, retranscription in pad
    '1268', # incorrect callsign (fixed in live db)
    '1286', # incorrect callsign, retranscription in pad
    '1287', # format not recognized by live db, retranscription in pad
    '1313', # incorrect callsign (fixed in live db)
    '1326', # incorrect callsign (fixed in live db)
    '1355', # incorrect callsign (fixed in live db)
    '1356', # incorrect callsign (fixed in live db)
    '1397', # partial log, retranscription in pad
    '1398', # incorrect callsign (fixed in live db)
}

override_contents = {
    '292': ["60 582 37 817 GLADYRJ/ГЛАДІРЙ:ru 30 53 41 11 GLADAK/ГЛАДАК:ru 41 10 19 56"],
    '293': ["60 582 37 817 GLADYRJ/ГЛАДІРЙ:ru 30 53 41 11 GLADAK/ГЛАДАК:ru 41 10 19 56"],
    '312': ["44 875 KORIDORNYJ/КОРИДОРНЫЙ:ru 12 88",
            "14 328 PORKAS/ПОКРАС:ru 27 89"],
    '409': ["67 234 10 324 SIMVOLIKA/СИМВОЛИКА:ru 06 50 32 02 CIMBIDIUM/ЦИМБИДИУМ:ru 85 03 58 40 GIL'DIN/ГИЛЬДИН:ru 52 14 46 54 DIL'DRIN/ДИЛЬДРИН:ru 37 46 77 11"],
    '410': ["67 234 10 324 SIMVOLIKA/СИМВОЛИКА:ru 06 50 32 02 CIMBIDIUM/ЦИМБИДИУМ:ru 85 03 58 40 GIL'DIN/ГИЛЬДИН:ru 52 14 46 54 DIL'DRIN/ДИЛЬДРИН:ru 37 46 77 11"],
}

override_format_handler = {
    '312': simple_format_handler(7) # monolyth with 2 digit groups
}

callsign_map = {
    "Al'fa 45": "Al'fa45"
}

la_ru_callsign_map = {
    "KZJT LNR4": "КЗЙТ ЛНР4",
    "Al'fa45": "АЛЬФА45",
    "8S1Shch": "8С1Щ",
    "MDZhB": "МДЖБ",
    "5J7Shch": "5Й7Щ"
}

# END OF STATIC DEFINES FOR CONVERSION

if __name__ == "__main__":
    try:
        with open("conversion.state", "rb") as f:
            conversion_state = pickle.load(f)
    except OSError:
        conversion_state = ({}, False, {}, False, {})

    logging.basicConfig(
        level=logging.DEBUG,
    )

    (station_map, stations_complete,
     broadcast_map, broadcasts_complete,
     transmission_map) = conversion_state

    try:
        with open("export.xml", "rb") as f:
            tree = etree.fromstring(f.read())

        if not stations_complete:
            for station_node in tree.find(pxmlns.stations):
                convert_station(station_node)
            stations_complete = True
        else:
            logger.info("skipping station import (state claims to be complete)")

        if not broadcasts_complete:
            for broadcast_node in tree.find(pxmlns.broadcasts):
                convert_broadcast(broadcast_node)
            broadcasts_complete = True
        else:
            logger.info("skipping broadcast import (state claims to be complete)")

        for transmission_node in tree.find(pxmlns.transmissions):
            convert_transmission(transmission_node)

    finally:
        conversion_state = (station_map, stations_complete,
                            broadcast_map, broadcasts_complete,
                            transmission_map)
        with open("conversion.state", "wb") as f:
            pickle.dump(conversion_state, f)
