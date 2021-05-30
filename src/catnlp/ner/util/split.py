import re


def cut(text, tags, max_len, overlap_len):
    sents = re.split(r'([。？?，,；;！!]|(?<!\d)\.(?!\d))', text)
    sents_len = len(sents)
    offset_list = list()
    i = 0
    end_idx = 0
    sent_list = list()
    tag_lists = list()
    while i < sents_len:
        sent = sents[i]
        sent_len = len(sent)
        end_idx += sent_len
        if not sent or re.match(r'([。？?，,；;！!]|(?<!\d)\.(?!\d))', sent):
            i += 1
            continue
        # 搜索前缀
        pre_list = list()
        pre_list_len = 0
        j = i - 1
        while j >= 0:
            sent_j = sents[j]
            sent_j_len = len(sent_j)
            if pre_list_len + sent_j_len < overlap_len:
                pre_list.append(sent_j)
                pre_list_len += sent_j_len
            else:
                break
            j -= 1
        pre_idx = 0
        pre_list = pre_list[::-1]
        for tmp_sent in pre_list:
            if not tmp_sent or re.match(r'([。？?，,；;！!]|(?<!\d)\.(?!\d))', tmp_sent):
                pre_idx += 1
                pre_list_len -= len(tmp_sent)
            else:
                break
        pre_list = pre_list[pre_idx:]

        # 搜索后缀
        post_list = list()
        post_list_len = 0
        j = i + 1
        while j < sents_len:
            sent_j = sents[j]
            sent_j_len = len(sent_j)
            if pre_list_len + sent_len + post_list_len < max_len:
                post_list.append(sent_j)
                post_list_len += sent_j_len
            else:
                break
            j += 1
        
        # 拼接
        sent = "".join(pre_list + [sent] + post_list)
        sent_list.append(sent)
        end_idx += post_list_len
        start_idx = end_idx - len(sent)
        offset_list.append(start_idx)
        tag_list = tags[start_idx: end_idx]
        tag_lists.append(tag_list)
        i = j

    if valid(text, sent_list, offset_list):
        return sent_list, tag_lists, offset_list
    else:
        raise ValueError


def recover(tag_lists, offset_list):
    new_entity_list = list()
    for tag_list, offset in zip(tag_lists, offset_list):
        entity_list = get_entity_list(tag_list)
        for entity in entity_list:
            start, end, tag = entity
            new_entity_list.append([start+offset, end+offset, tag])
    return new_entity_list


def get_entity_list(tag_list):
    entity_list = list()
    pre_label = "O"
    for idx, tag in enumerate(tag_list):
        if tag[0] != "O":
            tag_name = tag[2:]
            if tag[0] == "B":
                entity_list.append([idx, idx+1, tag_name])
            elif pre_label == tag_name:
                entity_list[-1][1] += 1
            else:
                entity_list.append([idx, idx+1, tag_name])
            pre_label = tag_name
        else:
            pre_label = "O"
    return entity_list


def valid(text, sent_list, offset_list):
    for offset, sent in zip(offset_list, sent_list):
        sent_len = len(sent)
        start = offset
        end = offset + sent_len
        if text[start: end] != sent:
            print("---")
            print(text[start: end])
            print(sent)
            return False
    return True


if __name__ == "__main__":
    text = "，，s.d,fsdfdsf.dsfdsfdfd,...s.,fk,js,sd,kfj,sd,f,，，k,d,sf,sdfk,sl,d,jfk,ds,s。d。k,，，fs,jdk,f,dfd,dsfs,sdfsdf,sdfsdf"
    tag_list = ["O"] * len(text)
    sent_list, tag_lists, end_idx_list = cut(text, tag_list, 20, 8)
    print(sent_list)
    print(tag_lists)
    print(end_idx_list)
