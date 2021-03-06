import numpy as np


def get_labels(predictions, references, label_list, input_len, decode_type="general", device="cpu"):
    if device == "cpu":
        y_pred = predictions.detach().clone().numpy()
        y_true = references.detach().clone().numpy()
        input_len = input_len.detach().clone().numpy()
    else:
        y_pred = predictions.detach().cpu().clone().numpy()
        y_true = references.detach().cpu().clone().numpy()
        input_len = input_len.detach().cpu().clone().numpy()
    if decode_type == "general":
        return get_general_labels(y_pred, y_true, label_list, input_len)
    elif decode_type == "biaffine":
        return get_biaffine_labels(y_pred, y_true, label_list, input_len)
    else:
        raise ValueError


def get_general_labels(y_pred, y_true, label_list, input_len):
    preds = list()
    golds = list()
    for pred, gold, max_len in zip(y_pred, y_true, input_len):
        tmp_preds = list()
        tmp_golds = list()
        for i in range(1, max_len):
            p = pred[i]
            g = gold[i]
            if g == 0:
                tmp_golds.append("O")
            else:
                tmp_golds.append(label_list[g])
            if p == 0:
                tmp_preds.append("O")
            else:
                tmp_preds.append(label_list[p])
        preds.append(tmp_preds)
        golds.append(tmp_golds)
    return preds, golds


def get_biaffine_labels(y_pred, y_true, label_list, input_len):
    preds = list()
    golds = list()
    for pred, gold, max_len in zip(y_pred, y_true, input_len):
        pred_entities = list()
        gold_entities = list()

        for i in range(1, max_len):
            for j in range(i, max_len):
                pred_scores = pred[i][j]
                pred_label_id = np.argmax(pred_scores)
                gold_label_id = gold[i][j]
                if gold_label_id > 0:
                    gold_entities.append([i-1, j, label_list[gold_label_id]])
                    if pred_label_id > 0:
                        pred_entities.append([i-1, j, label_list[pred_label_id], pred_scores[pred_label_id]])

        pred_entities = sorted(pred_entities, reverse=True, key=lambda x:x[3])
        new_pred_entities = list()
        for pred_entity in pred_entities:
            start, end, tag, _ = pred_entity
            flag = True
            for new_pred_entity in new_pred_entities:
                new_start, new_end, _ = new_pred_entity
                if start < new_end and new_start < end:
                    #for flat ner nested mentions are not allowed
                    flag = False
                    break
            if flag:
                new_pred_entities.append([start, end, tag])
        pred_entities = new_pred_entities
        tmp_preds = ["O"] * max_len
        tmp_golds = ["O"] * max_len
        for entity in pred_entities:
            start, end, tag = entity
            tmp_preds[start] = f"B-{tag}"
            for i in range(start+1, end):
                tmp_preds[i] = f"I-{tag}"
        for entity in gold_entities:
            start, end, tag = entity
            tmp_golds[start] = f"B-{tag}"
            for i in range(start+1, end):
                tmp_golds[i] = f"I-{tag}"
        preds.append(tmp_preds)
        golds.append(tmp_golds)
    return preds, golds
