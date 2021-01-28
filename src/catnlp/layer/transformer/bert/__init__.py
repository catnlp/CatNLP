__version__ = "2.1.1"

# Work around to update TensorFlow's absl.logging threshold which alters the
# default Python logging output behavior when present.
# see: https://github.com/abseil/abseil-py/issues/99
# and: https://github.com/tensorflow/tensorflow/issues/26691#issuecomment-500369493
try:
    import absl.logging
    absl.logging.set_verbosity('info')
    absl.logging.set_stderrthreshold('info')
    absl.logging._warn_preinit_stderr = False
except:
    pass

import logging

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Files and general utilities
from ..util.file import (TRANSFORMERS_CACHE, PYTORCH_TRANSFORMERS_CACHE, PYTORCH_PRETRAINED_BERT_CACHE,
                         cached_path, add_start_docstrings, add_end_docstrings,
                         WEIGHTS_NAME, TF2_WEIGHTS_NAME, TF_WEIGHTS_NAME, CONFIG_NAME,
                         is_tf_available, is_torch_available)

# Tokenizers
from ..util.token import PreTrainedTokenizer
from .token import BertTokenizer, BasicTokenizer, WordpieceTokenizer

# Configurations
from ..util.config import PretrainedConfig
from .config import BertConfig, BERT_PRETRAINED_CONFIG_ARCHIVE_MAP

# Modeling
if is_torch_available():
    from ..util.model import (PreTrainedModel, prune_layer, Conv1D)

    from .model import (BertPreTrainedModel, BertModel, BertForPreTraining,
                        BertForMaskedLM, BertForNextSentencePrediction,
                        BertForSequenceClassification, BertForMultipleChoice,
                        BertForTokenClassification, BertForQuestionAnswering,
                        load_tf_weights_in_bert, BERT_PRETRAINED_MODEL_ARCHIVE_MAP)

if not is_tf_available() and not is_torch_available():
    logger.warning("Neither PyTorch nor TensorFlow >= 2.0 have been found."
                   "Models won't be available and only tokenizers, configuration"
                   "and file/data utilities can be used.")
