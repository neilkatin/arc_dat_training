#!/usr/bin/env python

import os
import re
import sys
import logging
import argparse
import datetime
import json
import io
import zipfile
import base64

import requests
import xlrd
import vobject

import neil_tools
import neil_tools.spreadsheet_tools as spreadsheet_tools
import message

import config as config_static

import arc_o365
#from O365_local.excel import WorkBook as o365_WorkBook
import O365
from O365.excel import WorkBook as o365_WorkBook



NOW = datetime.datetime.now().astimezone()
DATESTAMP = NOW.strftime("%Y-%m-%d")
TIMESTAMP = NOW.strftime("%Y-%m-%d %H:%M:%S %Z")
FILESTAMP = NOW.strftime("%Y-%m-%d %H-%M-%S %Z")
EMAILSTAMP = NOW.strftime("%Y-%m-%d %H-%M")


def main():
    args = parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    log.debug("running...")

    config = neil_tools.init_config(config_static, ".env")

    for dr_id in args.dr_id:
        contents = message.fetch_dr_roster(config, dr_id)

        filename = f"{ FILESTAMP }-roster.vcf"
        with open(filename, "w") as fd:
            make_vcard_from_roster(contents, fd, dr_id)


def make_vcard_from_roster(contents, fd, dr_id):
    """ produce a vcard file from the roster """

    wb = xlrd.open_workbook(file_contents=contents)
    ws = wb.sheet_by_index(0)

    title = ws.cell_value(0, 0)
    dr = ws.cell_value(2, 0)

    log.debug(f"title '{ title }' dr '{ dr }'")

    nrows = ws.nrows
    ncols = ws.ncols

    title_row = 5   # origin zero

    assert nrows >= title_row + 2   # must be at least 2 rows: title row and at least one person

    # gather all the data
    matrix = []
    for index in range(title_row, nrows):
        matrix.append( ws.row_values(index) )

    # convert to object array
    objects = spreadsheet_tools.matrix_to_object_array(matrix)

    categories = [ f"DR{ dr_id }" ]

    for o in objects:
        s_name = o['Name']
        s_cell = o['Cell phone']
        s_email = o['Email']


        last_name, _, first_name = s_name.partition(',')

        log.debug(f"user { s_name } first { first_name } last { last_name }")

        vcard = vobject.vCard()

        vcard.add('n')
        vcard.n.value  = vobject.vcard.Name(family=last_name, given=first_name)

        vcard.add('fn')
        vcard.fn.value = f"{ first_name } { last_name }"

        if s_cell != None and s_cell != "":
            vcard.add('tel')
            vcard.tel.value = s_cell
            vcard.tel.type_param = "CELL"

        if s_email != None and s_email != "":
            vcard.add('email')
            vcard.email.value = s_email
            vcard.email.type_param = 'INTERNET'

        vcard.add('categories')
        vcard.categories.value = categories

        print(vcard.serialize(), file=fd)



def parse_args():
    parser = argparse.ArgumentParser(
            description="Check training completion for DAT responders",
            allow_abbrev=False)
    parser.add_argument("--debug", help="turn on debugging output", action="store_true")
    parser.add_argument("--positions", help="copy of VC position data for DAT team", required=True)

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    neil_tools.init_logging(__name__)
    log = logging.getLogger(__name__)
    main()
else:
    log = logging.getLogger(__name__)

