import sys
import os
import time

from KafNafParserPy import *

beginpoint = ''
versionnr = '0.1'

def update_match_dict(myhead, myvalue, mydict):

    myhead = myhead.lstrip().rstrip()
    if myhead in mydict:
        known_strings = mydict.get(myhead)
        #all values for a specific head word are sorted based on their length (longest match first principle)
        if len(myvalue) in known_strings:
            known_strings[len(myvalue)].append(myvalue)
        else:
            known_strings[len(myvalue)] = [myvalue]
    else:
        new_dict = {}
        new_dict[len(myvalue)] = [myvalue]
        mydict[myhead] = new_dict

def update_match_dictionaries(inputfile, string_match, lemma_match):

    for line in open(inputfile, 'r'):
        parts = line.rstrip().split('\t')
        if len(parts) < 5:
            print('Problem, cannot parse', line, file=sys.stderr)
        else:
            #create list of tokens
            string_value = parts[0].split()
            #append identifier
            string_value.append(parts[4].lstrip().rstrip())
            #update string match dict
            update_match_dict(parts[2], string_value, string_match)

            #same steps for lemmas
            lemma_value = parts[1].split()
            lemma_value.append(parts[4].lstrip().rstrip())
            update_match_dict(parts[3], lemma_value, lemma_match)


def get_tok_dictionary(nafobj):

    tok2id = {}
    for tok in nafobj.get_tokens():
        text = tok.get_text().lower()
        if text in tok2id:
            tok2id[text].append(tok.get_id())
        else:
            tok2id[text] = [tok.get_id()]

    return tok2id


def get_term_dictionary(nafobj):

    term2id = {}
    for term in nafobj.get_terms():
        lemma = term.get_lemma()
        if lemma in term2id:
            term2id[lemma].append(term.get_id())
        else:
            term2id[lemma] = [term.get_id()]

    return term2id


def create_next_ids(idlist):

    next_ids = set()
    for cid in idlist:
        if cid.startswith('w'):
            number = int(cid.lstrip('w')) + 1
            next_ids.add('w' + str(number))
        elif cid.startswith('t_'):
            number = int(cid.lstrip('t_')) + 1
            next_ids.add('t_' + str(number))
    return next_ids


def find_longest_match(foundMatches, tok2id, descriptions):

    match=False
    for des in sorted(descriptions, reverse=True):
        if match==True:
            break
        myvals = descriptions.get(des)
        for val in myvals:
            next_ids = set()
            identifier = val.pop()
            match = True
            for word in val:
                if word in tok2id:
                    myids = tok2id.get(word)
                    if len(next_ids) == 0:
                        next_ids = create_next_ids(myids)
                    else:
                        if len(set(myids) & next_ids) > 0:
                            joint_ids = set(myids) & next_ids
                            next_ids = create_next_ids(joint_ids)
                        else:
                            match = False
                            next_ids=set()
                            break
                else:
                    match = False
                    next_ids=set()
                    break
            if match==True:
                myinfo = [next_ids, val]
                if identifier in foundMatches:
                    foundMatches[identifier].append(myinfo)
                else:
                    foundMatches[identifier] = [myinfo]
                break

    return foundMatches


def create_combined_outcome(nafobj, foundStringMatches, foundTermMatches):

    mappings = {}
    for k, v in foundTermMatches.items():
        for val in v:
            for tId in val[0]:
                term = nafobj.get_term(tId)
                wId = term.get_span().get_span_ids()[0]
                mappings[wId] = [k, val[1]]
    for k, v in foundStringMatches.items():
        for val in v:
            for wId in val[0]:
                #TODO: also check if no conflicting k values
                if wId in mappings:
                    mapval = mappings.get(wId)
                    if len(mapval[1]) < len(val[1]):
                        mappinps[wId] = [k, val[1]]
                else:
                    mappings[wId] = [k, val[1]]
    return mappings


def get_expression_span(following_id, items):

    id_nr = int(following_id.lstrip('w'))
    span_ids = []
    for item in items:
        id_nr -= 1
        span_ids.insert(0, 'w' + str(id_nr))
    mySpan = Cspan()
    mySpan.create_from_ids(span_ids)
    return mySpan



def update_naf(mynaf, foundStringMatches, foundTermMatches):
   
    foundItems = create_combined_outcome(mynaf, foundStringMatches, foundTermMatches)

    mark_id = 1
    for k, v in foundItems.items():
        hiscoId = v[0]
        myMark = Cmarkable()
        #set Id and update
        myMark.set_id('m' + str(mark_id))
        mark_id += 1
        #create and set span
        span = get_expression_span(k, v[1])
        myMark.set_span(span)
        #create and add external reference
        myExRef = CexternalReference()
        #TODO: turn this into correct identifier
        myExRef.set_resource('hisco:')
        myExRef.set_reference(hiscoId)
        myMark.add_external_reference(myExRef)
        myMark.set_lemma(" ".join(v[1]))
        mynaf.add_markable(myMark)




def identify_profession_mentions(mynaf, string_match, lemma_match):

    tok2id = get_tok_dictionary(mynaf)
    term2id = get_term_dictionary(mynaf)
    foundStringMatches = {}
    foundTermMatches = {}
    if len(set(tok2id.keys()) & set(string_match.keys())) > 0:
        jointSet = set(tok2id.keys()) & set(string_match.keys())
        for profWord in jointSet:
            descriptions = string_match.get(profWord)
            find_longest_match(foundStringMatches, tok2id, descriptions)
    if len(set(term2id.keys()) & set(lemma_match.keys())) > 0:
        jointSet = set(term2id.keys()) & set(lemma_match.keys())
        for lemma in jointSet:
            descriptions = lemma_match.get(lemma)
            foundTermMatches = find_longest_match(foundTermMatches, term2id, descriptions)
    update_naf(mynaf, foundStringMatches, foundTermMatches)

#foundTermMatches = find_longest_match_terms(mynaf, term2id, descriptions)

def add_header_information(nafobj):

    global beginpoint, versionnr
    endtime = time.strftime('%Y-%m-%dT%H:%M:%S%Z')
    lp = Clp(name="vua-ontology-tagger",version=versionnr,btimestamp=beginpoint,etimestamp=endtime)
    nafobj.add_linguistic_processor('markables', lp)




def tag_strings_from_resource(nafdir, outdir, resource_files):

    global beginpoint
    beginpoint = time.strftime('%Y-%m-%dT%H:%M:%S%Z')
    string_match = {}
    lemma_match = {}
    for f in resource_files:
        update_match_dictionaries(f, string_match, lemma_match)

    for f in os.listdir(nafdir):
        if f.endswith('xml') or f.endswith('naf'):
            mynaf = KafNafParser(nafdir + f)
            identify_profession_mentions(mynaf, string_match, lemma_match)
            add_header_information(mynaf)
            mynaf.dump(outdir + f)

def main():

    #FIXME: setup proper usage function, options, etc.
    #in principle file structure is: full_string, lemma_variation, head_word_surface, head_word_lemma, identifier
    #TODO: option with or without lemmas, option set resource (ontology link)
    #TODO: option on one file or on directory
    if len(sys.argv) < 4:
        print('Error: please provide the naf directory, output directory and at least one resource file')
    else:
        tag_strings_from_resource(sys.argv[1], sys.argv[2], sys.argv[3:])


if __name__ == '__main__':
    main()