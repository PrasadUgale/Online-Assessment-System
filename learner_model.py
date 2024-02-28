from fileinput import filename
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pickle
from flask import url_for


# Importing the dataset
df = pd.read_csv(r'/home/prasad/pybox/LOGIN/static/project_data.csv')
#print(df)
#-----------------------------------------------------------------------------------#

#Converting to categorical value
categorical_d = {'yes': 1, 'no': 0}
df['schoolsup'] = df['schoolsup'].map(categorical_d)
df['famsup'] = df['famsup'].map(categorical_d)

df['activities'] = df['activities'].map(categorical_d)
df['nursery'] = df['nursery'].map(categorical_d)
df['higher'] = df['higher'].map(categorical_d)
df['internet'] = df['internet'].map(categorical_d)


categorical_d = {'F': 1, 'M': 0}
df['gender'] = df['gender'].map(categorical_d)

# map the address data


# map the famili size data
categorical_d = {'LE3': 1, 'GT3': 0}
df['famsize'] = df['famsize'].map(categorical_d)

# map the parent's status


# map the parent's job
categorical_d = {'teacher': 0, 'health': 1, 'services': 2,'at_home': 3,'other': 4}
df['Mjob'] = df['Mjob'].map(categorical_d)
df['Fjob'] = df['Fjob'].map(categorical_d)

# map the guardian data
categorical_d = {'mother': 0, 'father': 1, 'other': 2}
df['guardian'] = df['guardian'].map(categorical_d)



X = df.drop('Learner_type',axis=1)
y = df.Learner_type
X_train, X_test, y_train, y_test = train_test_split(X,y, test_size = 0.20, random_state=20)
reg = DecisionTreeClassifier()
reg.fit(X_train,y_train)
filename = "learner_type.sav"
pickle.dump(reg, open(filename, 'wb'))

####################################################################################

