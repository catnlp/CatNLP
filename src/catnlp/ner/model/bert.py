# -*- coding: utf-8 -*-

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    BertModel,
    BertPreTrainedModel
)
from torch.nn import CrossEntropyLoss
from torch.nn.utils.rnn import pad_sequence
from ...layer.decoder.crf import CRF


class BertSoftmax(BertPreTrainedModel):

    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.model = BertModel(config, add_pooling_layer=False)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)
        self.loss_func = CrossEntropyLoss()
        self.init_weights()

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        token_type_ids=None,
        position_ids=None,
        head_mask=None,
        inputs_embeds=None,
        labels=None,
        label_mask=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):

        outputs = self.model(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]

        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)

        if labels is not None:
            output = self.loss_func(logits.view(-1, self.num_labels), labels.view(-1))
        else:
            output = logits.argmax(dim=-1)

        return output


class BertCrf(BertPreTrainedModel):
    def __init__(self, config, label_size):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.model = BertModel(config, add_pooling_layer=False)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)
        self.crf = CRF(num_tags=label_size, batch_first=True)
        self.init_weights()

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        token_type_ids=None,
        position_ids=None,
        head_mask=None,
        inputs_embeds=None,
        labels=None,
        label_mask=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):
        outputs = self.model(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]

        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)

        if labels is not None:
            output = -self.crf(emissions=logits, tags=labels, mask=attention_mask.byte())
        else:
            output = self.crf.decode(emissions=logits, mask=attention_mask.byte())
            output = pad_sequence([torch.tensor(o) for o in output], batch_first=True)

        return output


class BertBiaffine(BertPreTrainedModel):
    def __init__(self, config, label_size):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.model = BertModel(config, add_pooling_layer=False)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        hidden_size = config.hidden_size
        self.start_layer = torch.nn.Sequential(torch.nn.Linear(in_features=hidden_size, out_features=128),
                                            torch.nn.ReLU())
        self.end_layer = torch.nn.Sequential(torch.nn.Linear(in_features=hidden_size, out_features=128),
                                            torch.nn.ReLU())
        self.biaffne_layer = biaffine(128, config.num_labels)
        self.loss_func = CrossEntropyLoss(reduction="none")
        self.init_weights()

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        token_type_ids=None,
        position_ids=None,
        head_mask=None,
        inputs_embeds=None,
        labels=None,
        label_mask=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):
        outputs = self.model(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        sequence_output = outputs[0]

        sequence_output = self.dropout(sequence_output)

        start_logits = self.start_layer(sequence_output) 
        end_logits = self.end_layer(sequence_output) 

        span_logits = self.biaffne_layer(start_logits,end_logits)
        span_logits = span_logits.contiguous()

        if labels is not None:
            labels = labels.view(size=(-1,))
            span_logits = span_logits.view(size=(-1, self.num_labels))
            span_loss = self.loss_func(input=span_logits, target=labels)
            label_mask = label_mask.view(size=(-1,))
            span_loss *= label_mask
            output = torch.sum(span_loss) / label_mask.size()[0]
        else:
            output = nn.functional.softmax(span_logits, dim=-1)
            # output = torch.argmax(output, dim=-1)

        return output


class biaffine(nn.Module):
    def __init__(self, in_size, out_size, bias_x=True, bias_y=True):
        super().__init__()
        self.bias_x = bias_x
        self.bias_y = bias_y
        self.out_size = out_size
        self.U = torch.nn.Parameter(torch.randn(in_size + int(bias_x),out_size,in_size + int(bias_y)))
        # self.U1 = self.U.view(size=(in_size + int(bias_x),-1))
        #U.shape = [in_size,out_size,in_size]  
    def forward(self, x, y):
        if self.bias_x:
            x = torch.cat((x, torch.ones_like(x[..., :1])), dim=-1)
        if self.bias_y:
            y = torch.cat((y, torch.ones_like(y[..., :1])), dim=-1)
        
        """
        batch_size,seq_len,hidden=x.shape
        bilinar_mapping=torch.matmul(x,self.U)
        bilinar_mapping=bilinar_mapping.view(size=(batch_size,seq_len*self.out_size,hidden))
        y=torch.transpose(y,dim0=1,dim1=2)
        bilinar_mapping=torch.matmul(bilinar_mapping,y)
        bilinar_mapping=bilinar_mapping.view(size=(batch_size,seq_len,self.out_size,seq_len))
        bilinar_mapping=torch.transpose(bilinar_mapping,dim0=2,dim1=3)
        """
        bilinar_mapping = torch.einsum('bxi,ioj,byj->bxyo', x, self.U, y)
        return bilinar_mapping
