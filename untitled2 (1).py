# -*- coding: utf-8 -*-
"""Untitled2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RWduRELOWHPsuk_ug2EYLX0-YyEcSVKF
"""

# Commented out IPython magic to ensure Python compatibility.
import re
import nltk
import string
import warnings
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
pd.set_option("display.max_colwidth",200)
warnings.filterwarnings("ignore",category=DeprecationWarning)
# %matplotlib inline

from google.colab import files
uploaded = files.upload()

import io
df2 = pd.read_csv(io.BytesIO(uploaded['covid19_tweets.csv']))
# Dataset is now stored in a Pandas Dataframe
train=df2
test=df2

train[train['hashtags']=='COVID19'].head(10)
train[train['hashtags']!='COVID19'].head(10)


train["hashtags"].value_counts()

length_train=train['text'].str.len()
length_test=test['text'].str.len()
plt.hist(length_train,bins=20,label="train_tweets")
plt.hist(length_train,bins=20,label="test_tweets")
plt.legend()
plt.show()

combine=train.append(test,ignore_index=True)
combine.shape

def remove_pattern(input_txt,pattern):
  r=re.findall(pattern,input_txt)
  for i in r:
    input_txt=re.sub(i,'',input_txt)
  return input_txt

combine['c_tweet']=np.vectorize(remove_pattern)(combine['text'],"@[\w]*")
combine.head()

combine['c_tweet']=combine['c_tweet'].str.replace("[^a-zA-Z#]"," ")
combine.head(10)

combine['c_tweet']=combine['c_tweet'].apply(lambda x: ' '.join([w for w in x.split() if len(w)>3]))
combine.head()

token_tweet=combine['c_tweet'].apply(lambda x: x.split())
token_tweet.head()

from nltk.stem.porter import *
stemmer= PorterStemmer()
token_tweet=token_tweet.apply(lambda x: [stemmer.stem(i) for i in x])

for i in range(len(token_tweet)):
  token_tweet[i]=' '.join(token_tweet[i])
combine['c_tweet']=token_tweet

#visualize

all_words=' '.join([text for text in combine['c_tweet']]) 
from wordcloud import WordCloud
wordcloud= WordCloud(width=800, height=500,random_state=21,max_font_size=110).generate(all_words)
plt.figure(figsize=(10,7))
plt.imshow(wordcloud,interpolation="bilinear") 
plt.axis('off')
plt.show()

#hastags

def hashtag_extract(x):
  hashtags=[]
  for i in x:
    ht=re.findall(r"#(\w+)",i)
    hashtags.append(ht)
  return hashtags    

regular_tag=hashtag_extract(combine['c_tweet'][combine['text']=='COVID19'])
unwant_tag=hashtag_extract(combine['c_tweet'][combine['text']!='COVID19'])
regular_tag=sum(regular_tag,[]) 
unwant_tag=sum(unwant_tag,[])

a=nltk.FreqDist(regular_tag)
d=pd.DataFrame({'Hashtag': list(a.keys()), 'Count': list(a.values())})
d=d.nlargest(columns="Count",n=20)
plt.figure(figsize=(16,5))
ax=sns.barplot(data=d,x="Hashtag",y="Count") 
ax.set(ylabel="Count") 
plt.show()

b=nltk.FreqDist(unwant_tag)
e=pd.DataFrame({'Hashtag': list(b.keys()), 'Count': list(b.values())})
e=e.nlargest(columns="Count",n=20)
plt.figure(figsize=(16,5))
ax=sns.barplot(data=d,x="Hashtag",y="Count") 
ax.set(ylabel="Count") 
plt.show()

!pip install scikit-learn==0.13
from sklearn.feature_extraction.text import *
import gensim

bow_vectorizer=CountVectorizer(max_df=0.90,min_df=2,max_features=1000,stop_words='english')
bow=bow_vectorizer.fit_transform(combine['c_tweet'])
bow.shape

tfidf_vectorizer=TfidVectorizer(max_df=0.90,min_df=2,max_features=1000,stop_words='english')
tfid=tfidf_vectorizer.fit_transform(combine['c_tweet'])
bow.shape

'''
token_tweet=combine['c_tweet'].apply(lambda x: x.split())
model_w2v=gensim.models.Word2Vec(
    token_tweet,size=200,window=5,min_count=2,sg=1,hs=0,negative=10,workers=2,seed=34
)
model_w2v.train(token_tweet,total_examples=len(combine['c_tweet']),epochs=20)
'''

def word_vector(tokens,size):
  vec=np.zeros(size).reshape((1,size))
  count=0
  for word in tokens:
    try:
      vec+=model_w2v[word].reshape((1,size))
      count+=1
    except KeyError:
      continue
  if count!=0:
    vec/=count
  return vec

wordvec_arrays=np.zeros((len(token_tweet),200))
for i in range(len(token_tweet)):
  wordvec_arrays[i,:]=word_vector(token_tweet[i],200)
  wordvec_df=pd.DataFrame(wordvec_arrays)
  wordvec.shape

from tqdm import tqdm tqdm.pandas(desc="progress-bar")
from gensim.models.doc2vec import LabeledSentence

def add_label(twt):
  output=[]
  for i,s in zip(twt.index,twt):
    output=[]
    for i,s in zip(twt.index,twt):
      output.append(LabeledSentence(s,["tweet_"+str(i)]))
    return output
labeled_tweets=add_label(tokenized_tweet)
labeled_tweet[:6]

model_d2v=gensim.models.Doc2Vec(dm=1,dm_mean=1,size=200,window=5,negative=7,min_count=5,workers=3,alpha=0.1,seed=23)
model_d2v.build_vocab([i for i in tqdm(labeled_tweets)])
model_d2v.train(labeled_tweets,total_examples=len(combine['c_tweet']), epochs=15)

docvec_arrays=np.zeros((len(tokenized_tweet),200))
for i in range(len(combine)):
  docvec_arrays[i,:]=model_d2v.docvecs[i].reshape((1,200))
docvec_df=pd.DataFrame(docvec_arrays)
docvec_df.shape

from sklearn.linear_model import LogisticRegression 
from sklearn.model_selection import train_test_split 
from sklearn.metrics import f1_score

train_bow=bow[:31962,:]
test_bow=bow[31962:,:]
xtrain_bow,xvalid_bow,ytrain,yvalid=train_test_split(train_bow,train['label'],random_state=42,test_size=0.3)
lreg=LogisticRegression()
lreg.fit(xtrain_bow,ytrain)
prediction=lreg.predict_proba(xvalid_bow)
prediction_int=prediction[:,1]>=0.3
prediction_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

test_pred=lreg.predict_proba(test_bow)
test_pred_int=test_pred[:,1]>=0.3
test_pred_int=test_pred_int.astype(np.int)
test['hashtags']=test_pred_int 
submission=test[['hashtags']]
submission.to_csv('sub_lreg_bow.csv',index=False)

train_tfidf=tfidf[:31962,:]
test_tfidf=tfidf[31962:,:]
xtrain_tfidf=train_tfidf[ytrain.index]
xvalid_tfidf=train_tfidf[yvalid.index]

lreg.fit(xtrain_tfidf,ytrain)
prediction=lreg.predict_proba(xvalid_tfidf)
prediction_int=prediction[:,1]>=0.3
prediction_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

train_w2v=woedvec_df.iloc[:31962,:]
test_w2v=wordvec_df.iloc[31962:,:]
xtrain_w2v=train.w2v.iloc[ytrain.index,:]
xvalid_w2v=train_w2v.iloc[yvalid.index,:]

lreg.fit(xtrain_w2v,ytrain)
prediction=lreg.predict_proba(xvalid_w2v)
prediction_int=prediction[:,1]>=0.3
prediction_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

train_d2v=docvec_df.iloc[:31962,:]
test_d2v=docvec_df.iloc[31962:,:]
xtrain_d2v=train_d2v.iloc[ytrain.index,:]
xvalid_d2v=train_d2v.iloc[yvalid.index,:]

lreg.fit(xtrain_d2v,ytrain)
prediction=lreg.predict_proba(xvalid_d2v)
prediction_int=prediction[:,1]>=0.3
prediction_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

from sklearn import svm

svc=svm.SVC(kernel='linear',C=1,probability=True).fit(xtrain_bow,ytrain)
prediction=svc.predcit_proba(xvalid_bow)
prediction_int=prediction[:,1]>=0.3
prediction_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

test_pred=svc.predict_proba(test_bow)
test_pred_int=test_pred[:,1]>=0.3
test_pred_int=test_pred_int.astype(np.int)
test['hashtags']=test_pred_int
submission=test[['hashtags']]
submission.to_csv('sub_svm_bow.csv',index=False)

svc=svm.SVC(kernel='linear',C=1,probability=True).fit(xtrain_tfidf,ytrain)
prediction=svc.predict_proba(xvalid_tfidf)
prediction_int=prediction[:,1]>=0.3
predcition_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

svc=svm.SVC(kernel='linear',C=1,probability=True).fit(xtrain_w2v,ytrain)
prediction=svc.predict_proba(xvalid_w2v)
prediction_int=prediction[:,1]>=0.3
predcition_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

svc=svm.SVC(kernel='linear',C=1,probability=True).fit(xtrain_d2v,ytrain)
prediction=svc.predict_proba(xvalid_d2v)
prediction_int=prediction[:,1]>=0.3
predcition_int=prediction_int.astype(np.int)
f1_score(yvalid,prediction_int)

from sklearn.esemble import RandomForestClassifier

rf=RandomForestClassifier(n_estimators=400,random_State=11).fit(xtrain_bow,ytrain)
prediction=rf.predict(xvalid_bow)
f1_score(yvalid,prediction)

test_pred=rf.predict(test_bow)
test['hashtags']=test_pred
submission=test[['hashtags']]
submission.to_csv('sub_rf_bow.csv',index=False)

rf=RandomForestClassifier(n_estimators=400,random_State=11).fit(xtrain_tfidf,ytrain)
prediction=rf.predict(xvalid_tfidf)
f1_score(yvalid,prediction)

rf=RandomForestClassifier(n_estimators=400,random_State=11).fit(xtrain_w2v,ytrain)
prediction=rf.predict(xvalid_w2v)
f1_score(yvalid,prediction)

rf=RandomForestClassifier(n_estimators=400,random_State=11).fit(xtrain_d2v,ytrain)
prediction=rf.predict(xvalid_d2v)
f1_score(yvalid,prediction)

from xgboost import XGBClassifier

xgb_model=XGBClassifier(max_depth=6,n_estimators=1000).fit(xtrain_bow,ytrain)
prediction=xgb_model.predict(xvalid_bow)
f1_score(yvalid,prediction)

test_pred=xgb_model.predict(test_bow)
test['hashtags']=test_pred
submission=test[["hashtags"]]
submission.to_csv('sub_xgb_bow.csv',index=False)

xgb=XGBClassifier(max_depth=6,n_estimators=1000).fit(xtrain_tfidf,ytrain)
prediction=xgb_model.predict(xvalid_tfidf)
f1_score(yvalid,prediction)

xgb=XGBClassifier(max_depth=6,n_estimators=1000).fit(xtrain_w2v,ytrain)
prediction=xgb_model.predict(xvalid_w2v)
f1_score(yvalid,prediction)

xgb=XGBClassifier(max_depth=6,n_estimators=1000).fit(xtrain_d2v,ytrain)
prediction=xgb_model.predict(xvalid_d2v)
f1_score(yvalid,prediction)

import xgboost as xgb

dtrain=xgb.DMatrix(xtrain_w2v,label=ytrain)
dvalid=xgb.DMatrix(xvalid_w2v,label=yvalid)
dtest=xgb.DMatrix(test_w2v)

params={
    'objective':'binary:logistic',
    'max_depth':6,
    'min_child_weight':1,
    'eta':.3,
    'subsample':1,
    'colsample_bytree':1
}

def custom_eval(preds,dtrain):
  labels=dtrain.get_label().astype(np.int)
  preds=(preds>=0.3).astype(np,int)
  return [('f1_score',f1_score(labels,preds))]

gridsearch_params=[
                   (max_depth,min_child_weight)
                   for max_depth in range(6,10)
                   for min_child_weight in range(5,8)
]

max_f1=0
best_params=None
for max_Depth,min_child_weight in gridsearch_params:
  print("CV with max_depth={}, min_child_weight={}".format(
      max_depth,min_child_weight
  ))
  params['max_depth']=max_depth
  params['min_child_Weight']=min_child_weight

  cv_results=xgb.cv(params,dtrain,fevel=custom_eval,num_boost_round=200,maximize=True,seed=16,nfold=5,early_stopping_rounds=10)

  mean_f1=cv_results['test-f1_score-mean'].max()

  boost_rounds=cv_results['test=f1_score-mean'].argmax()
  print("\tF1 Score {} for {} rounds".format(mean_f1,boost_rounds))
  if mean_f1>max_f1:
    max_f1=mean_f1
    best_params=(max_depth,min_child_weight)

 print("Best params: {},{}, F1 Score: {}".format(best_params[0],best_params[1],max_f1))

params['max_depth']=8
params['min_child_weight']=6

gridsearch_params=[
                   (subsample,colsample)
                   for subsample in [i/10. for i in range(5,10)]
                   for colsample in [i/10. for i in range(5,10)]
]
max_f1=0.
best_params=None
for subsample,colsample in gridsearch_params:
  print("CV with subsample={}, colsample={}".format(
      subsample,colsample)
  )

  params['colsample']=colsample
  params['subsample']=subsample
  cv_results=xgb.cv(
      params,dtrain,
      feval=custom_eval,
      num_boost_round=200,
      maximize=True,
      seed=16,
      nfold=5,
      early_stopping_rounds=10
  )

  mean_f1=cv_results['test-f1_score-mean'].max()

  boost_rounds=cv_results['test=f1_score-mean'].argmax()
  print("\tF1 Score {} for {} rounds".format(mean_f1,boost_rounds))
  if mean_f1>max_f1:
    max_f1=mean_f1
    best_params=(max_depth,min_child_weight)

 print("Best params: {},{}, F1 Score: {}".format(best_params[0],best_params[1],max_f1))

params['eta']=.1

params
{
    'colsample':0.9,
 'colsample_bytree':0.5,'eta':0.1,
 'max_depth':8,'min_child_weight':6,
 'objective':'binary:logistic',
 'subsample':0.9
}


xgb_model=xgb.train(
    params,
    dtrain,
    feval=custom_eval,
    num_boost_round=1000,
    maximize=True,
    evals=[(dvalid,"Validation")],
    early_stopping_rounds=10
)

test_pred=xgb_model.predict(dtest)
test['hashtags']=(test_pred>=0.3).astype(np.int)
submission=test[['hashtags']]
submission.to_csv('sub_xgb_w2v_finetune.csv',index=False)