# -*- coding: utf-8 -*-
import re
import copy
import json
import logging

import torch
from torch import tensor
from torch.utils.data import Dataset, DataLoader, TensorDataset
from torch.nn.utils.rnn import pad_sequence

logger = logging.getLogger(__name__)


class NerLstmDataLoader(DataLoader):
    """
    数据加载器
    """
    def __init__(self, dataset, batch_size, shuffle=False, drop_last=False):
        super(NerLstmDataLoader, self).__init__(dataset,
                                            batch_size=batch_size,
                                            shuffle=shuffle,
                                            collate_fn=self._collate_fn,
                                            drop_last=drop_last)

    def _collate_fn(self, data):
        word = pad_sequence([x[0] for x in data], batch_first=True,
                            padding_value=0)
        label = pad_sequence([x[-1] for x in data], batch_first=True,
                             padding_value=0)
        return word, label


class NerLstmDataset(Dataset):
    """
    数据集类
    """
    def __init__(self, data_file, vocab, delimiter="\t"):
        """
        初始化数据集类
        Args:
            data_file(str): 数据集文件路径
            vocab(Vocab): 词典类
            delimiter(str): 分隔符
        Returns: 无
        """
        datas = self._load_bio_file(data_file, delimiter)
        self._data = self._to_features(datas, vocab)
    
    def _load_bio_file(self, data_file, delimiter='\t'):
        """
        加载数据集文件
        Args:
            data_file(str): 数据集文件路径
            vocab(Vocab): 词典类
            delimiter(str): 分隔符
        Returns: 无
        """
        datas = list()
        word_list = list()
        label_list = list()
        with open(data_file, 'r', encoding='utf-8') as rf:
            for line in rf:
                line = line.rstrip()
                if line:
                    word, label = line.split(delimiter)
                    word_list.append(word)
                    label_list.append(label)
                else:
                    if word_list:
                        datas.append([word_list, label_list])
                        word_list = list()
                        label_list = list()
        return datas

    def _to_features(self, datas, vocab):
        """
        加载数据集文件
        Args:
            data_file(str): 数据集文件路径
            vocab(Vocab): 词典类
        Returns: 无
        """
        features = list()
        for (ex_index, data) in enumerate(datas):
            if ex_index < 3:
                print(data)
            word_ids = [vocab.get_word_id(x) for x in data[0]]
            label_ids = [vocab.get_label_id(x) for x in data[1]]
            word_ids = torch.tensor(word_ids, dtype=torch.long)
            label_ids = torch.tensor(label_ids, dtype=torch.long)
            features.append([word_ids, label_ids])
        return features

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        return self._data[idx]


class NerBertDataLoader(DataLoader):
    """
    数据加载器
    """
    def __init__(self, dataset, batch_size, shuffle=False, drop_last=False):
        super(NerBertDataLoader, self).__init__(dataset,
                                                batch_size=batch_size,
                                                shuffle=shuffle,
                                                collate_fn=self._collate_fn,
                                                drop_last=drop_last)

    def _collate_fn(self, features):
        all_input_ids = torch.tensor([f.input_ids for f in features])
        all_input_mask = torch.tensor([f.input_mask for f in features])
        all_segment_ids = torch.tensor([f.segment_ids for f in features])
        all_label_ids = torch.tensor([f.label_ids for f in features])
        all_label_mask = torch.tensor([f.label_mask for f in features])
        all_input_len = torch.tensor([f.input_len for f in features])
        return all_input_ids, all_input_mask, all_segment_ids, all_label_ids, all_label_mask, all_input_len


class NerBertDataset(Dataset):
    """
    数据集类
    """
    def __init__(self, data_file, tokenizer, max_seq_length, file_format="bio", delimiter="\t", do_lower=False):
        """
        初始化数据集类
        Args:
            data_file(str): 数据集文件路径
            vocab(Vocab): 词典类
            delimiter(str): 分隔符
        Returns: 无
        """
        self._do_lower = do_lower
        datas = self._load_file(data_file, file_format, delimiter)
        self._data = self._to_features(datas, file_format=file_format, tokenizer=tokenizer, max_seq_length=max_seq_length)
    
    def _load_file(self, data_file, file_format, delimiter):
        if file_format == "json":
            return self._load_json_file(data_file)
        elif file_format == "split":
            return self._load_split_file(data_file)
        elif file_format == "biaffine":
            return self._load_biaffine_file(data_file)
        elif file_format == "bies":
            return self._load_bies_file(data_file, delimiter)
        else:
            return self._load_conll_file(data_file, delimiter)


    def _load_conll_file(self, data_file, delimiter):
        """
        加载数据集文件
        Args:
            data_file(str): 数据集文件路径
            delimiter(str): 分隔符
        Returns: 无
        """
        datas = list()
        word_list = list()
        tag_list = list()
        label_set = set()
        with open(data_file, 'r', encoding='utf-8') as rf:
            for line in rf:
                line = line.rstrip()
                if line:
                    word, tag = line.split(delimiter)
                    word_list.append(word)
                    tag_list.append(tag)
                    label_set.add(tag)
                else:
                    if word_list:
                        datas.append([word_list, tag_list])
                        word_list = list()
                        tag_list = list()
        self.label_list = ["[PAD]"] + sorted(list(label_set))
        self.label_to_id = {label: idx for idx, label in enumerate(self.label_list)}
        self.contents = list()
        self.offset_lists = list()
        return datas
    
    def _load_bies_file(self, data_file, delimiter):
        """
        加载数据集文件
        Args:
            data_file(str): 数据集文件路径
            delimiter(str): 分隔符
        Returns: 无
        """
        datas = list()
        word_list = list()
        tag_list = list()
        label_set = {"O"}
        with open(data_file, 'r', encoding='utf-8') as rf:
            for line in rf:
                line = line.rstrip()
                if line:
                    word, tag = line.split(delimiter)
                    word_list.append(word)
                    tag_list.append(tag)
                    if len(tag) > 1:
                        tag_name = tag[2:]
                        label_set.add(f"B-{tag_name}")
                        label_set.add(f"I-{tag_name}")
                        label_set.add(f"E-{tag_name}")
                        label_set.add(f"S-{tag_name}")
                else:
                    if word_list:
                        datas.append([word_list, tag_list])
                        word_list = list()
                        tag_list = list()
        self.label_list = ["[PAD]"] + sorted(list(label_set))
        self.label_to_id = {label: idx for idx, label in enumerate(self.label_list)}
        self.contents = list()
        self.offset_lists = list()
        return datas
    
    def _load_json_file(self, data_file):
        """
        加载数据集文件
        Args:
            data_file(str): 数据集文件路径
            delimiter(str): 分隔符
        Returns: 无
        """
        datas = list()
        label_set = set(["O"])
        with open(data_file, 'r', encoding='utf-8') as rf:
            for line in rf:
                line = json.loads(line)
                if not line:
                    continue
                text = line["text"]
                entities = line["labels"]
                tag_list = ["O"] * len(text)
                for entity in entities:
                    start, end, tag = entity
                    label_set.add(f"B-{tag}")
                    label_set.add(f"I-{tag}")
                    tag_list[start] = f"B-{tag}"
                    for i in range(start+1, end):
                        tag_list[i] = f"I-{tag}"
                datas.append([text, tag_list])
        self.label_list = ["[PAD]"] + sorted(list(label_set))
        self.label_to_id = {label: idx for idx, label in enumerate(self.label_list)}
        self.contents = list()
        self.offset_lists = list()
        return datas
    
    def _load_split_file(self, data_file):
        """
        加载数据集文件
        Args:
            data_file(str): 数据集文件路径
        Returns: 无
        """
        datas = list()
        label_set = set(["O"])
        contents = list()
        offset_lists = list()
        with open(data_file, 'r', encoding='utf-8') as rf:
            for line in rf:
                line = json.loads(line)
                if not line:
                    continue
                content = line["text"]
                offsets = line["offsets"]
                contents.append(content)
                offset_lists.append(offsets)
                sents = line["sents"]
                entity_lists = line["label_lists"]
                for sent, entity_list in zip(sents, entity_lists):
                    tag_list = ["O"] * len(sent)
                    for entity in entity_list:
                        start, end, tag = entity
                        label_set.add(f"B-{tag}")
                        label_set.add(f"I-{tag}")
                        tag_list[start] = f"B-{tag}"
                        for i in range(start+1, end):
                            tag_list[i] = f"I-{tag}"
                    datas.append([sent, tag_list])
        self.label_list = ["[PAD]"] + sorted(list(label_set))
        self.label_to_id = {label: idx for idx, label in enumerate(self.label_list)}
        self.contents = contents
        self.offset_lists = offset_lists
        return datas
    
    def _load_biaffine_file(self, data_file):
        """
        加载数据集文件
        Args:
            data_file(str): 数据集文件路径
            delimiter(str): 分隔符
        Returns: 无
        """
        datas = list()
        label_set = set()
        with open(data_file, 'r', encoding='utf-8') as rf:
            for line in rf:
                line = json.loads(line)
                if not line:
                    continue
                text = line["text"]
                entities = line["labels"]
                for entity in entities:
                    label_set.add(entity[-1])
                datas.append([text, entities])
        self.label_list = ["[PAD]"] + sorted(list(label_set))
        self.label_to_id = {label: idx for idx, label in enumerate(self.label_list)}
        self.contents = list()
        self.offset_lists = list()
        return datas

    def get_label_list(self):
        return self.label_list

    def get_label_to_id(self):
        return self.label_to_id

    def get_contents(self):
        return self.contents

    def get_offset_lists(self):
        return self.offset_lists
    
    def tokenize(self, text):
        _tokens = list()
        _offsets = list()
        for c in text:
            if self._do_lower:
                c = c.lower()
            if re.match(r"\s", c):
                _tokens.append("[unused1]")
            else:
                _tokens.append(c)
            _offsets.append(1)
        return _tokens, _offsets

    def _to_features(self, datas, file_format="general", tokenizer=None, max_seq_length=-1,
                     cls_token_at_end=False,cls_token="[CLS]",cls_token_segment_id=0,
                     sep_token="[SEP]",pad_on_left=False,pad_token="[PAD]",pad_token_segment_id=0,
                     sequence_a_segment_id=0,mask_padding_with_zero=True,):
        """ Loads a data file into a list of `InputBatch`s
            `cls_token_at_end` define the location of the CLS token:
                - False (Default, BERT/XLM pattern): [CLS] + A + [SEP] + B + [SEP]
                - True (XLNet/GPT pattern): A + [SEP] + B + [SEP] + [CLS]
            `cls_token_segment_id` define the segment id associated to the CLS token (0 for BERT, 2 for XLNet)
        """
        features = list()
        for (ex_index, data) in enumerate(datas):
            tokens, _ = self.tokenize(data[0])
            if file_format != "biaffine":
                label_ids = [self.label_to_id[x] for x in data[1]]
            # Account for [CLS] and [SEP] with "- 2".
            special_tokens_count = 2
            if len(tokens) > max_seq_length - special_tokens_count:
                tokens = tokens[: (max_seq_length - special_tokens_count)]
                if file_format != "biaffine":
                    label_ids = label_ids[: (max_seq_length - special_tokens_count)]

            # The convention in BERT is:
            # (a) For sequence pairs:
            #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
            #  type_ids:   0   0  0    0    0     0       0   0   1  1  1  1   1   1
            # (b) For single sequences:
            #  tokens:   [CLS] the dog is hairy . [SEP]
            #  type_ids:   0   0   0   0  0     0   0
            #
            # Where "type_ids" are used to indicate whether this is the first
            # sequence or the second sequence. The embedding vectors for `type=0` and
            # `type=1` were learned during pre-training and are added to the wordpiece
            # embedding vector (and position vector). This is not *strictly* necessary
            # since the [SEP] token unambiguously separates the sequences, but it makes
            # it easier for the model to learn the concept of sequences.
            #
            # For classification tasks, the first vector (corresponding to [CLS]) is
            # used as as the "sentence vector". Note that this only makes sense because
            # the entire model is fine-tuned.
            pad_id = self.label_to_id.get(pad_token)
            tokens += [sep_token]
            if file_format != "biaffine":
                label_ids += [pad_id]
            segment_ids = [sequence_a_segment_id] * len(tokens)

            tokens = [cls_token] + tokens
            if file_format != "biaffine":
                label_ids = [pad_id] + label_ids
            segment_ids = [cls_token_segment_id] + segment_ids

            input_ids = tokenizer.convert_tokens_to_ids(tokens)
            # The mask has 1 for real tokens and 0 for padding tokens. Only real
            # tokens are attended to.
            input_mask = [1 if mask_padding_with_zero else 0] * len(input_ids)
            input_len = len(input_ids)
            
            # Zero-pad up to the sequence length.
            padding_length = max_seq_length - len(input_ids)
            input_ids += [pad_id] * padding_length
            input_mask += [0 if mask_padding_with_zero else 1] * padding_length
            segment_ids += [pad_token_segment_id] * padding_length
            if file_format != "biaffine":
                label_ids += [pad_id] * padding_length
            
            if file_format == "biaffine":
                # label_mask还要再看看
                label_mask = [[0 for _ in range(max_seq_length)]]
                for i in range(1, input_len-1):
                    label_mask.append([0 for _ in range(i)] + [1 for _ in range(input_len-i-1)] + [0 for _ in range(max_seq_length-input_len+1)])
                for i in range(input_len-1, max_seq_length):
                    label_mask.append([0 for _ in range(max_seq_length)])
                assert len(label_mask) == len(label_mask[0])
                
                label_ids = list()
                for i in range(max_seq_length):
                    label_ids.append([0 for _ in range(max_seq_length)])
                for entity in data[1]:
                    start, end, tag = entity
                    # 默认第一个字符为[CLS]
                    if end > input_len - 1:
                        print("big")
                        continue
                    label_ids[start+1][end] = self.label_to_id[tag]
            else:
                label_mask = label_ids

            assert len(input_ids) == max_seq_length
            assert len(input_mask) == max_seq_length
            assert len(segment_ids) == max_seq_length
            assert len(label_ids) == max_seq_length
            assert len(label_mask) == max_seq_length
            if ex_index < 3:
                print("*** Example ***")
                print("tokens: ", tokens)
                print("input_ids: ", input_ids)
                print("input_mask: ", input_mask)
                print("input_len: ", input_len)
                print("segment_ids: ", segment_ids)
                print("label_mask: ", label_mask)
                if file_format == "biaffine":
                    print("label_ids: ")
                    for i in range(len(label_ids)):
                        print(label_ids[i])
                else:
                    print("label_ids: ", label_ids)
            features.append(InputFeatures(input_ids=input_ids, input_mask=input_mask, segment_ids=segment_ids, label_ids=label_ids, label_mask=label_mask, input_len=input_len))
        return features

    def save_label(self, label_file):
        with open(label_file, "w", encoding="utf-8") as lf:
            for label in self.label_list:
                lf.write(f"{label}\n")

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        return self._data[idx]

class InputFeatures(object):
    """A single set of features of data."""
    def __init__(self, input_ids, input_mask, segment_ids, label_ids, label_mask, input_len):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_ids = label_ids
        self.label_mask = label_mask
        self.input_len = input_len

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
