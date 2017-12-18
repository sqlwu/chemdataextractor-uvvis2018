# -*- coding: utf-8 -*-
"""
chemdataextractor.doc.table
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Table processing.

:copyright: Copyright 2016 by Matt Swain.
:license: MIT, see LICENSE file for more details.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
from collections import defaultdict

from ..model import Compound, ModelList
from ..parse.table import CompoundHeadingParser, CompoundCellParser, UvvisAbsHeadingParser, UvvisAbsCellParser, \
    QuantumYieldHeadingParser, QuantumYieldCellParser, UvvisEmiHeadingParser, UvvisEmiCellParser, ExtinctionCellParser, \
    ExtinctionHeadingParser, ExtinctionDisallowedHeadingParser, FluorescenceLifetimeHeadingParser, FluorescenceLifetimeCellParser, \
    ElectrochemicalPotentialHeadingParser, ElectrochemicalPotentialCellParser, IrHeadingParser, IrCellParser, \
    SolventCellParser, SolventHeadingParser, SolventInHeadingParser, UvvisAbsEmiQuantumYieldHeadingParser, \
    UvvisAbsEmiQuantumYieldCellParser, MeltingPointHeadingParser, MeltingPointCellParser, TempInHeadingParser, \
    UvvisAbsDisallowedHeadingParser, UvvisEmiQuantumYieldHeadingParser, UvvisEmiQuantumYieldCellParser, VocHeadingParser, \
    VocCellParser, UvvisAbsAndExtinctionHeadingParser, UvvisAbsAndExtinctionCellParser
# TODO: Sort out the above import... import module instead
from ..nlp.tag import NoneTagger
from ..nlp.tokenize import FineWordTokenizer
from ..utils import memoized_property
from .element import CaptionedElement
from .text import Sentence

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)



class Table(CaptionedElement):

    #: Table cell parsers
    parsers = [
        (CompoundHeadingParser(), CompoundCellParser()),
        (UvvisAbsEmiQuantumYieldHeadingParser(), UvvisAbsEmiQuantumYieldCellParser()),
        (UvvisEmiQuantumYieldHeadingParser(), UvvisEmiQuantumYieldCellParser()),
        (UvvisEmiHeadingParser(), UvvisEmiCellParser()),
        (UvvisAbsHeadingParser(), UvvisAbsCellParser(), UvvisAbsDisallowedHeadingParser()),
        (ExtinctionHeadingParser(), ExtinctionCellParser(), ExtinctionDisallowedHeadingParser()),
        (IrHeadingParser(), IrCellParser()),
        (QuantumYieldHeadingParser(), QuantumYieldCellParser()),
        (FluorescenceLifetimeHeadingParser(), FluorescenceLifetimeCellParser()),
        (ElectrochemicalPotentialHeadingParser(), ElectrochemicalPotentialCellParser()),
        (MeltingPointHeadingParser(), MeltingPointCellParser()),
        (SolventHeadingParser(), SolventCellParser()),
        (SolventInHeadingParser(),),
        (TempInHeadingParser(),)
        #(VocHeadingParser(), VocCellParser())
    ]

    def __init__(self, caption, label=None, headings=None, rows=None, footnotes=None, **kwargs):
        super(Table, self).__init__(caption=caption, label=label, **kwargs)
        self.headings = headings if headings is not None else []  # list(list(Cell))
        self.rows = rows if rows is not None else []  # list(list(Cell))
        self.footnotes = footnotes if footnotes is not None else []
        print("Table Headings look like:")
        print(self.headings)

    @property
    def document(self):
        return self._document

    @document.setter
    def document(self, document):
        self._document = document
        self.caption.document = document
        for row in self.headings:
            for cell in row:
                cell.document = document
        for row in self.rows:
            for cell in row:
                cell.document = document

    def serialize(self):
        """Convert Table element to python dictionary."""
        data = {
            'type': self.__class__.__name__,
            'caption': self.caption.serialize(),
            'headings': [[cell.serialize() for cell in hrow] for hrow in self.headings],
            'rows': [[cell.serialize() for cell in row] for row in self.rows],
        }
        return data

    def _repr_html_(self):
        html_lines = ['<table class="table">']
        html_lines.append(self.caption._repr_html_  ())
        html_lines.append('<thead>')
        for hrow in self.headings:
            html_lines.append('<tr>')
            for cell in hrow:
                html_lines.append('<th>' + cell.text + '</th>')
        html_lines.append('</thead>')
        html_lines.append('<tbody>')
        for row in self.rows:
            html_lines.append('<tr>')
            for cell in row:
                html_lines.append('<td>' + cell.text + '</td>')
        html_lines.append('</tbody>')
        html_lines.append('</table>')
        return '\n'.join(html_lines)

    @property
    def records(self):
        """Chemical records that have been parsed from the table."""
        caption_records = self.caption.records
        # Parse headers to extract contextual data and determine value parser for the column
        value_parsers = {}
        header_compounds = defaultdict(list)
        table_records = ModelList()
        seen_compound_col = False
        log.debug('Parsing table headers')
        log.debug(self.headings)
        joint_parser_indices = []

        compound_cell_parser = CompoundCellParser()

        for i, col_headings in enumerate(zip(*self.headings)):
            # log.debug('Considering column %s' % i)
            uvvis_header, ext_header = False, False
            for parsers in self.parsers:
                log.debug(parsers)
                heading_parser = parsers[0]
                value_parser = parsers[1] if len(parsers) > 1 else None
                disallowed_parser = parsers[2] if len(parsers) > 2 else None
                allowed = False
                disallowed = False
                for cell in col_headings:
                    log.info(cell.tagged_tokens)
                    results = list(heading_parser.parse(cell.tagged_tokens))
                    if results:
                        print("cell tagged tokens are:")
                        print(results)
                        print(results[0].serialize())
                        allowed = True
                        log.info(cell.tagged_tokens)
                        log.info('Heading column %s: Match %s: %s' % (i, heading_parser.__class__.__name__, [c.serialize() for c in results]))
                    # Results from every parser are stored as header compounds
                        if( heading_parser.__class__.__name__ == "UvvisAbsHeadingParser"):
                            print("Header contains a Uvvis object")
                            uvvis_header = True
                        if( heading_parser.__class__.__name__ == "ExtinctionHeadingParser"):
                            print("Header contains a Extinction object")
                            ext_header = True
                        if uvvis_header==True and ext_header==True:
                            joint_parser_indices.append(i)
                        print(results[0].serialize())
                        print(heading_parser.__class__.__name__)
                        header_compounds[i].extend(results)
                    #if results

                    # Referenced footnote records are also stored
                    for footnote in self.footnotes:
                        # print('%s - %s - %s' % (footnote.id, cell.references, footnote.id in cell.references))
                        if footnote.id in cell.references:
                            log.debug('Adding footnote %s to column %s: %s' % (footnote.id, i, [c.serialize() for c in footnote.records]))
                            # print('Footnote records: %s' % [c.to_primitive() for c in footnote.records])
                            header_compounds[i].extend(footnote.records)
                    # Check if the disallowed parser matches this cell
                    if disallowed_parser and list(disallowed_parser.parse(cell.tagged_tokens)):
                        log.debug('Column %s: Disallowed %s' % (i, heading_parser.__class__.__name__))
                        disallowed = True
                # If heading parser matches and disallowed parser doesn't, store the value parser
                if allowed and not disallowed and value_parser and i not in value_parsers:
                    if isinstance(value_parser, CompoundCellParser):
                        # Only take the first compound col
                        if seen_compound_col:
                            continue
                        seen_compound_col = True
                    log.debug('Column %s: Value parser: %s' % (i, value_parser.__class__.__name__))
                    value_parsers[i] = value_parser
                 # Stop after value parser is assigned?
        log.info("Uvvis and extinction parsers found in columns " + str(joint_parser_indices))
        for index in joint_parser_indices:
            value_parsers[index] = UvvisAbsAndExtinctionCellParser()
        print(value_parsers)

            #Add logic here to check if headers for uvvis and extinction were found in the same column?
            #if UvvisAbsCellParser and value_parsers

        # for hrow in self.headings:
        #     for i, cell in enumerate(hrow):
        #         log.debug(cell.tagged_tokens)
        #         for heading_parser, value_parser in self.parsers:
        #             results = list(heading_parser.parse(cell.tagged_tokens))
        #             if results:
        #                 log.debug('Heading column %s: Match %s: %s' % (i, heading_parser.__class__.__name__, [c.to_primitive() for c in results]))
        #             # Results from every parser are stored as header compounds
        #             header_compounds[i].extend(results)
        #             if results and value_parser and i not in value_parsers:
        #                 if isinstance(value_parser, CompoundCellParser):
        #                     # Only take the first compound col
        #                     if seen_compound_col:
        #                         continue
        #                     seen_compound_col = True
        #                 value_parsers[i] = value_parser
        #                 break  # Stop after first heading parser matches
        #         # Referenced footnote records are also stored
        #         for footnote in self.footnotes:
        #             # print('%s - %s - %s' % (footnote.id, cell.references, footnote.id in cell.references))
        #             if footnote.id in cell.references:
        #                 log.debug('Adding footnote %s to column %s: %s' % (footnote.id, i, [c.to_primitive() for c in footnote.records]))
        #                 # print('Footnote records: %s' % [c.to_primitive() for c in footnote.records])
        #                 header_compounds[i].extend(footnote.records)

        # If no parsers, skip processing table
        if value_parsers:
            # If no CompoundCellParser() in value_parsers and value_parsers[0] == [] then set CompoundCellParser()
            if not seen_compound_col and 0 not in value_parsers:
                log.debug('No compound column found in table, assuming first column')
                value_parsers[0] = CompoundCellParser()

            for n, row in enumerate(self.rows):
                row_compound = Compound()
                # Keep cell records that are contextual to merge at the end
                contextual_cell_compounds = []
                for i, cell in enumerate(row):
                    log.debug(cell.tagged_tokens)
                    if i in value_parsers:
                        #print(value_parsers[i])
                        log.info(cell.tagged_tokens)
                        results = list(value_parsers[i].parse(cell.tagged_tokens))
                        print(results)
                        if results:
                            log.info('Cell column %s: Match %s: %s' % (i, value_parsers[i].__class__.__name__, [c.serialize() for c in results]))
                        # For each result, merge in values from elsewhere
                        for result in results:
                            # Merge each header_compounds[i]
                            for header_compound in header_compounds[i]:
                                if header_compound.is_contextual:
                                    result.merge_contextual(header_compound)
                            # Merge footnote compounds
                            for footnote in self.footnotes:
                                if footnote.id in cell.references:
                                    for footnote_compound in footnote.records:
                                        result.merge_contextual(footnote_compound)
                            if result.is_contextual:
                                # Don't merge cell as a value compound if there are no values
                                contextual_cell_compounds.append(result)
                            else:
                                row_compound.merge(result)

                # Merge contextual information from cell
                for contextual_cell_compound in contextual_cell_compounds:
                    row_compound.merge_contextual(contextual_cell_compound)

                #Merge peak data from the same row
                log.info("Merging separate uvvis value and extinction coeff. data")
                if row_compound.uvvis_spectra:
                    print(row_compound.uvvis_spectra[0].serialize())


                #
                #This section attempts to merge uvvis/extinction objects together
                #Currently support cases where:
                #  extinctions are uvvis objects and values are peak objects
                #  both extinctions and peaks are uvvis objects
                #

                #Merging related uvvis objects
                value_indices, ext_indices = [], []
                for i, uvvis_obj in enumerate(row_compound.uvvis_spectra):
                    if uvvis_obj.justValue():
                        value_indices.append(i)
                    if uvvis_obj.justExtinction():
                        ext_indices.append(i)

                #Merging internal value peaks with extinction peaks
                for uvvis_obj in row_compound.uvvis_spectra:
                    if uvvis_obj.peaks != None:
                        #Identifying which peak objects are just values or extinctions
                        value_peak_indices, ext_peak_indices = [], []
                        for i, peak in enumerate(uvvis_obj.peaks):
                            if peak.justValue():
                                value_peak_indices.append(i)
                            if peak.justExtinction():
                                ext_peak_indices.append(i)
                        #Merging these peaks if criteria are met
                        if value_peak_indices != [] and ext_peak_indices != [] \
                            and len(value_peak_indices) == len(ext_peak_indices):

                            for (v, e) in zip(value_peak_indices, ext_peak_indices):
                                print(uvvis_obj.peaks)
                                print(v, e)
                                print("Merging two peak level compounds")
                                uvvis_obj.mergePeaks(v,e)

                            #Removing the contextual extinction object
                            k = 0
                            for e in ext_peak_indices:
                                print("Deleting extinction coefficient record")
                                del uvvis_obj.peaks[e - k]
                                k = k + 1



                #Merging value peaks with uvvis extinctions
                for index in value_indices:
                    if len(row_compound.uvvis_spectra[index].peaks) == len(ext_indices) and len(ext_indices) > 1:
                        row_compound.uvvis_spectra[index].mergePeaksAndUvvis(row_compound.uvvis_spectra, ext_indices)

                        j = 0
                        for e in ext_indices:
                            print("Deleting extinction coefficient record")
                            del row_compound.uvvis_spectra[e - j]
                            j = j + 1


                print(value_indices, ext_indices)
                if value_indices != []  and ext_indices != [] and len(value_indices) == len(ext_indices):
                    for (v,e) in zip(value_indices, ext_indices):
                        print(row_compound.uvvis_spectra)
                        print(v,e)
                        print("Entered loop for merging")
                        row_compound.uvvis_spectra[v].mergeUvvis(row_compound.uvvis_spectra[e])

                    k=0
                    for e in ext_indices:
                        print("Deleting extinction coefficient record")
                        del row_compound.uvvis_spectra[e-k]
                        k=k+1

                #Check previous row for uvvis data if this row is all extinctions
                value_indices_prev =[]
                if value_indices == [] and ext_indices !=[] and table_records:
                    log.info("Using compound from previous row")
                    prev = table_records[-1]
                    for i, uvvis_obj in enumerate(prev.uvvis_spectra) :
                        if uvvis_obj.justValue():
                            value_indices_prev.append(i)
                        print(value_indices_prev)

                    if len(value_indices_prev) == len(ext_indices):
                        for (v, e) in zip(value_indices_prev, ext_indices):
                            print("Entered loop for merging")
                            prev.uvvis_spectra[v].mergeUvvis(row_compound.uvvis_spectra[e])

                        l = 0
                        for e in ext_indices:
                            print("Deleting extinction coefficient record")
                            del row_compound.uvvis_spectra[e - l]
                            l = l + 1


                    print(len(prev.uvvis_spectra))
                    print(len(row_compound.uvvis_spectra))
                    print("CASE FOUND" +str(len( prev.uvvis_spectra)))

                   # print([v.peaks[0].extinction for v in prev_row.uvvis_spectra])



                #elif value_indices != []  and ext_indices != [] and len()

                # If there's still no name/label, try running compound_cell_parser on first row cell
                if not row_compound.names and not row_compound.labels:
                    print(table_records)
                    print("There was no label detected.")
                    first_cell = row[0]
                    compound_guess = list(compound_cell_parser.parse(first_cell.tagged_tokens))
                    if table_records:
                        log.info("Using compound from previous row")
                        prev = table_records[-1]
                        row_compound.names = prev.names
                        row_compound.labels = prev.labels

                    elif len(compound_guess) is not 0:
                        log.info("No compound found in previous row. Trying first row")
                        print(compound_guess[0].serialize())
                        row_compound.merge(compound_guess[0])

                    #NOTE: have switched around the presidence of these two loops

                    #elif table_records:
                     #   log.info("No compound found in first row, using compound from previous row.")
                      #  prev = table_records[-1]
                       # row_compound.names = prev.names
                        #row_compound.labels = prev.labels

                #NB: This is Matt's original name/label loop (changed to account for lack of compound labelling
                # If no compound name/label, try take from previous row
                #if not row_compound.names and not row_compound.labels and table_records:
                 #   prev = table_records[-1]
                  #  row_compound.names = prev.names
                   # row_compound.labels = prev.labels

#                    row_compound.merge(compound_guess)

                    #LOGIC - if first_cell matches a simple label, make this the label.


                # Merge contextual information from caption into the full row
                for caption_compound in caption_records:
                    if caption_compound.is_contextual:
                        row_compound.merge_contextual(caption_compound)
                # And also merge from any footnotes that are referenced from the caption
                for footnote in self.footnotes:
                    if footnote.id in self.caption.references:
                        # print('Footnote records: %s' % [c.to_primitive() for c in footnote.records])
                        for fn_compound in footnote.records:
                            row_compound.merge_contextual(fn_compound)

                log.debug(row_compound.serialize())
                if row_compound.serialize():
                    table_records.append(row_compound)

        # TODO: If no rows have name or label, see if one is in the caption

        # Include non-contextual caption records in the final output
        caption_records = [c for c in caption_records if not c.is_contextual]
        table_records += caption_records
        return table_records

    # TODO: extend abbreviations property to include footnotes
    # TODO: Resolve footnote records into headers


class Cell(Sentence):
    word_tokenizer = FineWordTokenizer()
    # pos_tagger = NoneTagger()
    ner_tagger = NoneTagger()

    @memoized_property
    def abbreviation_definitions(self):
        """Empty list. Abbreviation detection is disabled within table cells."""
        return []

    @property
    def records(self):
        """Empty list. Individual cells don't provide records, this is handled by the parent Table."""
        return []