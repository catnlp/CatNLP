## CatNLP

👋项目聚焦于NLP技术，包括不限于命名实体识别，实体关系抽取，文本相似度，实体链接等技术

### 索引

### 目录结构

```
📦catnlp
 ┣ 📂callback
 ┃ ┣ 📂optimizer
 ┣ 📂common
 ┃ ┣ 📜load_file.py
 ┣ 📂data
 ┃ ┣ 📂config
 ┃ ┣ 📂dataset
 ┃ ┣ 📂embed
 ┃ ┣ 📂log
 ┃ ┗ 📂output
 ┣ 📂layer
 ┃ ┣ 📂cnn
 ┃ ┣ 📂decoder
 ┃ ┃ ┣ 📜crf.py
 ┃ ┣ 📂rnn
 ┃ ┣ 📂transformer
 ┣ 📂ner
 ┃ ┣ 📂model
 ┃ ┃ ┣ 📜bilstm.py
 ┃ ┃ ┣ 📜bilstm_crf.py
 ┃ ┣ 📂util
 ┃ ┃ ┣ 📜clean.py
 ┃ ┃ ┣ 📜data.py
 ┃ ┃ ┣ 📜embed.py
 ┃ ┃ ┣ 📜merge.py
 ┃ ┃ ┣ 📜progressbar.py
 ┃ ┃ ┣ 📜score.py
 ┃ ┃ ┣ 📜vocab.py
 ┃ ┣ 📜format.py
 ┃ ┣ 📜train.py
```

### 命名实体识别（NER）
