import PinYinParts
import pickle
import json
import genanki

pyp = PinYinParts.PinYinParts()

common_char_dict = json.load(open('../data/char_common_detail.json'))
chaizi_map = pickle.load(open('../data/data.pkl','rb'))
pyp = PinYinParts.PinYinParts()

# 'an' is exclude as 'an' and 'ang' are easy to distinct
QIANBI = set(['en', 'in'])

PINGSHE = set(['z', 'c', 's'])
QIAOSHE = set(['zh', 'ch', 'sh'])

def match_bibian(pinyin):
    if pinyin[0] == 'n':
        # 1:biyin
        return(1)
    elif pinyin[0] == 'l':
        # -1: bianyin
        return(-1)
    return(0)

def match_pingqiao(pinyin):
    if pinyin[0] in PINGSHE:
        # 1:pingshe
        return(1)
    elif pinyin[0] in QIAOSHE:
        # 2:qiaoshe
        return(-1)
    return(0)

def match_qianhou(pinyin):
    for item in QIANBI:
        if pinyin[-2].endswith(item):
            # 1:qianbiyin
            return(1)
        elif pinyin[-2].endswith(f'{item}g'):
            # -1:houbiyin
            return(-1)
        return(0)

def update_dict(dict_, vo_type_, arrs, value, check):
    for arr in arrs:
        for key in arr:
            # if the pinyin of key is not representitive, skip it
            if vo_type_ != check(pyp.extract_raw(key)[0][0]):
                continue
            if key not in dict_:
                dict_[key] = set([])
            dict_[key].add(value)
    if value not in dict_:
        dict_[value] = set([])
    dict_[value].add(value)
        
def filter_dict(dict_):
    filtered = {k: v for k, v in dict_.items() if len(v) > 1}
    assert len(filtered) > 0
    return(filtered)

def generate_anki_deck(dict_, name, dst_file):
    # Define the model for the deck
    model = genanki.Model(
        1607392319,
        f'{name}',
        fields=[
            {'name': 'Word'},
            {'name': 'PinYin'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Word}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{PinYin}}',
            },
        ])

    # Define the deck
    deck = genanki.Deck(
        2059400110,
        f'{name}')

    # Define the notes for the deck
    notes = []
    for k, v in dict_.items():
        # this would make the text easy to read.
        note = genanki.Note(
            model=model,
            fields=[k, v])
        notes.append(note)

    # Add the notes to the deck
    deck.notes.extend(notes)

    # Write the deck to a file
    genanki.Package(deck).write_to_file(dst_file)
    
def main():
    biyin_dict = dict()
    bianyin_dict = dict()
    
    pingshe_dict = dict()
    qiaoshe_dict = dict()
    
    qianbi_dict = dict()
    houbi_dict = dict()
    
    for item in common_char_dict:
        chr = item['char']
        pinyin = pyp.extract_raw(chr)[0][0]
        
        bibian = match_bibian(pinyin)
        if chr not in chaizi_map:
            chaizi_map[chr] = [[chr]]
        
        if bibian > 0:
            update_dict(biyin_dict, bibian, chaizi_map[chr], chr, match_bibian)
        elif bibian < 0:
            update_dict(bianyin_dict, bibian, chaizi_map[chr], chr, match_bibian)
            
        pingqiao = match_pingqiao(pinyin)
        if pingqiao > 0:
            update_dict(pingshe_dict, pingqiao, chaizi_map[chr], chr, match_pingqiao)
        elif pingqiao < 0:
            update_dict(qiaoshe_dict, pingqiao, chaizi_map[chr], chr, match_pingqiao)
        
        qianhou = match_qianhou(pinyin)
        if qianhou > 0:
            update_dict(qianbi_dict, qianhou, chaizi_map[chr], chr, match_qianhou)
        elif qianhou < 0:
            update_dict(houbi_dict, qianhou, chaizi_map[chr], chr, match_qianhou)
            
    biyin_dict = filter_dict(biyin_dict)
    bianyin_dict = filter_dict(bianyin_dict)
    
    pingshe_dict = filter_dict(pingshe_dict)
    qiaoshe_dict = filter_dict(qiaoshe_dict)
    
    qianbi_dict = filter_dict(qianbi_dict)
    houbi_dict = filter_dict(houbi_dict)    

    merged_dict = {**biyin_dict, **bianyin_dict, **pingshe_dict, **qiaoshe_dict, **qianbi_dict, **houbi_dict}
    trainset_dict = {}
    testset_dict = {}
    for k, v in merged_dict.items():
        pinyin = ''.join(pyp.extract_raw(k)[0][0])
        v_format = [f"{s}({''.join(pyp.extract_raw(s)[0][0])})" for s in v]
        v_format = f'{pinyin}\n为部首的字有{"、".join(v_format)}'
        trainset_dict[k] = v_format
        for char_ in v:
            testset_dict[char_] = ''.join(pyp.extract_raw(char_)[0][0]) 
        
    generate_anki_deck(trainset_dict, "易混字训练集", "易混字训练集.apkg")
    generate_anki_deck(testset_dict, "易混字测试集", "易混字测试集.apkg")

main()