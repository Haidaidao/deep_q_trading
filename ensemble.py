# #Copyright (C) 2020 Salvatore Carta, Anselmo Ferreira, Alessandro Sebastian Podda, Diego Reforgiato Recupero, Antonio Sanna. All rights reserved.

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from itertools import product
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import global_config
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
import global_config
import json
from Evaluation import Evaluation

config = json.load(open('plotResultsConf.json', 'r'))

ensembleFolder = global_config.ensembleFolder
threshold = global_config.label_threshold

iteration = 'iteration' + str(config['epoch']-1)


# Get the results in the log file of the week that contains that day.
def getActionWeek(weeksFrame, date):
    date = datetime.strptime(date,"%m/%d/%Y")

    for i in range(0, len(weeksFrame)):
        week =  datetime.strptime(str(weeksFrame.index[i]),"%m/%d/%Y")
        if week>date:
            return  weeksFrame['ensemble'][i-1]
    return 0

def ensemble_y_true(feature, stats, threshold):

    labels = []
    last_action = 0
    skip = 0
    
    for index, _ in feature.iterrows():
        if index not in stats.index:
            labels.append(last_action)
            skip += 1
            continue
        
        close = stats.loc[index, 'Close']
        open = stats.loc[index, 'Open']
        
        action = 0
        changes = (close - open) / open

        if changes >= threshold or (last_action > 0 and changes >= 0 and changes < threshold):
            last_action = 1
            action = 1
        elif changes < -threshold or (last_action < 0 and changes < 0 and changes >= -threshold):
            last_action = -1
            action = -1
        else:
            last_action = 0

        labels.append(action)
            
    return labels




# ================================================ XGBoots
def XGBoostEnsemble(numWalks,type,numDel):
    
    current_balance_sum=0
    net_profit_sum=0
    winning_trade_number_sum=0
    losing_trade_number_sum=0
    profit_factor_sum=0
    percent_profitable_sum=0
    average_profit_per_trade_sum=0

    columns = ["From","To", "Wins", "Closes", "Profit"]

    values = []

    dax=pd.read_csv("./datasets/"+ global_config.MK +"Day.csv",index_col='Date')

    type_train = "train"

    xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42)

    for j in range(0, numWalks):

        # Train
        df1 = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Hour" + str(j) + "ensemble_" + type_train+ ".csv",
                          index_col='Date')
        df2 = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Day" + str(j) + "ensemble_" + type_train + ".csv",
                          index_col='Date')
        df3 = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Week" + str(j) + "ensemble_" + type_train + ".csv",
                          index_col='Date')

        for deleted in range(1, numDel):
            del df1['iteration' + str(deleted)]
            del df2['iteration' + str(deleted)]
            del df3['iteration' + str(deleted)]

        df1 = pd.DataFrame(df1[iteration])
        df1.rename(columns={iteration: 'ensemble'}, inplace=True)

        df2.index = pd.to_datetime(df2.index)
        df2.index = df2.index.strftime('%m/%d/%Y')
        df2.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3.index = pd.to_datetime(df3.index)
        df3.index = df3.index.strftime('%m/%d/%Y')
        df3.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3_temp = pd.DataFrame(index=df2.index).assign(ensemble=0)
        for k in range(0,len(df3_temp)):
            df3_temp['ensemble'][k] = getActionWeek(df3,df3_temp.index[k])

        list_combine_train = np.empty((0, 3))

        for k in range(0,len(df1)):
            list_combine_train = np.append(list_combine_train, [[df1['ensemble'][k], df2['ensemble'][k], df3_temp['ensemble'][k]]], axis=0)
      
        y_train = ensemble_y_true(df1, dax, threshold)

        le = LabelEncoder()
        y_train = le.fit_transform(y_train)
        # xgb_model = xgb.XGBClassifier(n_estimators=100, random_state=42)
        xgb_model.fit(list_combine_train, y_train)

        # Predict
        for deleted in range(1,numDel):
            del df['iteration'+str(deleted)]

        df = pd.DataFrame(columns=['ensemble'])
        df = df.set_index(pd.Index([], name='date'))

        df1_result = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Hour" + str(j) + "ensemble_" + type + ".csv",
                          index_col='Date')
        df2_result = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Day" + str(j) + "ensemble_" + type + ".csv",
                          index_col='Date')
        df3_result = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Week" + str(j) + "ensemble_" + type + ".csv",
                          index_col='Date')

        from_date=str(df2_result.index[0])
        to_date=str(df2_result.index[len(df2_result)-1])

        for deleted in range(1, numDel):
            del df1_result['iteration' + str(deleted)]
            del df2_result['iteration' + str(deleted)]
            del df3_result['iteration' + str(deleted)]

        df1_result = pd.DataFrame(df1_result[iteration])
        df1_result.rename(columns={iteration: 'ensemble'}, inplace=True)

        df2_result.index = pd.to_datetime(df2_result.index)
        df2_result.index = df2_result.index.strftime('%m/%d/%Y')
        df2_result.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3_result.index = pd.to_datetime(df3_result.index)
        df3_result.index = df3_result.index.strftime('%m/%d/%Y')
        df3_result.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3_temp = pd.DataFrame(index=df2_result.index).assign(ensemble=0)
        for k in range(0,len(df3_temp)):
            df3_temp['ensemble'][k] = getActionWeek(df3_result,df3_temp.index[k])

        # print(df1)
        # print("=======")
        # print(df2)
        # print("=======")
        # print(df3)
        # print("--------------")

        for k in range(0,len(df1_result)):
            if(df1_result.index[k] in df2_result.index):
                new_data = np.array([[df1_result['ensemble'][k], df2_result['ensemble'][k], df3_temp['ensemble'][k]]])
                predicted_result = xgb_model.predict(new_data)
                df.loc[df1_result.index[k]] = predicted_result[0]
        
        df['close'] = 0
        df['close'] = df.index.map(dax['Close'])
        df['high'] = df.index.map(dax['High'])
        df['low'] = df.index.map(dax['Low'])
        # print(df)
        # print("=================")
        test = Evaluation(df)
       
        wins, loses, profit = test.evaluate()
       
        #values.append([from_date, to_date,str(round(current_balance,2)),str(round(net_profit,2)),str(round(winning_trade_number,2)),str(round(losing_trade_number,2)),str(round(profit_factor,2)),str(round(percent_profitable,2)) + '%', str(round(average_profit_per_trade,2))])

        # current_balance_sum+=current_balance
        # net_profit_sum+=net_profit
        # winning_trade_number_sum+=winning_trade_number
        # losing_trade_number_sum+=losing_trade_number
        # profit_factor_sum+=profit_factor
        # percent_profitable_sum+=percent_profitable
        # average_profit_per_trade_sum+=average_profit_per_trade

    values.append([' ','Sum',str(round(wins,2)),str(round(loses,2)),str(round(profit,2))])
    # print(values)
    return values,columns
# ================================================ Random Forest
def RandomForestEnsemble(numWalks,type,numDel):
    
    wins_number = 0
    loses_number = 0
    profit_number = 0

    columns = ["From","To", "Wins", "Closes", "Profit"]

    values = []

    dax=pd.read_csv("./datasets/"+ global_config.MK +"Day.csv",index_col='Date')

    type_train = "train"

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)

    for j in range(0, numWalks):
        # Train
        df1 = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Hour" + str(j) + "ensemble_" + type_train+ ".csv",
                          index_col='Date')
        df2 = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Day" + str(j) + "ensemble_" + type_train + ".csv",
                          index_col='Date')
        df3 = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Week" + str(j) + "ensemble_" + type_train + ".csv",
                          index_col='Date')

        for deleted in range(1, numDel):
            del df1['iteration' + str(deleted)]
            del df2['iteration' + str(deleted)]
            del df3['iteration' + str(deleted)]

        df1 = pd.DataFrame(df1[iteration])
        df1.rename(columns={iteration: 'ensemble'}, inplace=True)

        df2.index = pd.to_datetime(df2.index)
        df2.index = df2.index.strftime('%m/%d/%Y')
        df2.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3.index = pd.to_datetime(df3.index)
        df3.index = df3.index.strftime('%m/%d/%Y')
        df3.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3_temp = pd.DataFrame(index=df2.index).assign(ensemble=0)
        for k in range(0,len(df3_temp)):
            df3_temp['ensemble'][k] = getActionWeek(df3,df3_temp.index[k])

        list_combine_train = np.empty((0, 3))

        for k in range(0,len(df1)):
            list_combine_train = np.append(list_combine_train, [[df1['ensemble'][k], df2['ensemble'][k], df3_temp['ensemble'][k]]], axis=0)

        y_train = ensemble_y_true(df1, dax, threshold)

        # rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(list_combine_train, y_train)

        # Predict
        for deleted in range(1,numDel):
            del df['iteration'+str(deleted)]

        df = pd.DataFrame(columns=['ensemble'])
        df = df.set_index(pd.Index([], name='date'))

        df1_result = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Hour" + str(j) + "ensemble_" + type + ".csv",
                          index_col='Date')
        df2_result = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Day" + str(j) + "ensemble_" + type + ".csv",
                          index_col='Date')
        df3_result = pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk" + "Week" + str(j) + "ensemble_" + type + ".csv",
                          index_col='Date')

        from_date=str(df2_result.index[0])
        to_date=str(df2_result.index[len(df2_result)-1])

        for deleted in range(1, numDel):
            del df1_result['iteration' + str(deleted)]
            del df2_result['iteration' + str(deleted)]
            del df3_result['iteration' + str(deleted)]

        df1_result = pd.DataFrame(df1_result[iteration])
        df1_result.rename(columns={iteration: 'ensemble'}, inplace=True)
    
        df2_result.index = pd.to_datetime(df2_result.index)
        df2_result.index = df2_result.index.strftime('%m/%d/%Y')
        df2_result.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3_result.index = pd.to_datetime(df3_result.index)
        df3_result.index = df3_result.index.strftime('%m/%d/%Y')
        df3_result.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3_temp = pd.DataFrame(index=df2_result.index).assign(ensemble=0)
        for k in range(0,len(df3_temp)):
            df3_temp['ensemble'][k] = getActionWeek(df3_result,df3_temp.index[k])

        for k in range(0,len(df1_result)):
            if(df1_result.index[k] in df2_result.index):
                new_data = np.array([[df1_result['ensemble'][k], df2_result['ensemble'][k], df3_temp['ensemble'][k]]])
                predicted_result = rf_model.predict(new_data)
                df.loc[df1_result.index[k]] = predicted_result[0]
        print(df['ensemble'])
        print("==================")

        df['close'] = 0
        df['close'] = df.index.map(dax['Close'])
        df['high'] = df.index.map(dax['High'])
        df['low'] = df.index.map(dax['Low'])
        # print(df)
        # print("=================")
        test = Evaluation(df)
       
        wins, loses, profit = test.evaluate()
       
        values.append([from_date, to_date,str(round(wins,2)),str(round(loses,2)),str(round(profit,2))])

        wins_number+=wins
        loses_number+=loses
        profit_number+=profit
        # current_balance_sum+=current_balance
        # net_profit_sum+=net_profit
        # winning_trade_number_sum+=winning_trade_number
        # losing_trade_number_sum+=losing_trade_number
        # profit_factor_sum+=profit_factor
        # percent_profitable_sum+=percent_profitable
        # average_profit_per_trade_sum+=average_profit_per_trade

    values.append([' ','Sum',str(round(wins_number,2)),str(round(loses_number,2)),str(round(profit_number,2))])
    return values,columns
# ================================================ Base-rule

def normalized(a):
    if a > 0:
        return 1
    elif a < 0:
        return -1
    return 0

def SimpleEnsemble(numWalks,type,numDel):
    dollSum=0
    rewSum=0
    posSum=0
    negSum=0
    covSum=0
    numSum=0

    columns = ["From","To", "Reward%", "#Wins", "#Losses", "Dollars", "Coverage", "Accuracy"]

    values=[]

    dax = pd.read_csv("./datasets/" + global_config.MK + "Day.csv", index_col='Date')

    for j in range(0,numWalks):

        df1=pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk"+"Hour"+str(j)+"ensemble_"+type+".csv",index_col='Date')
        df2=pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk"+"Day"+str(j)+"ensemble_"+type+".csv",index_col='Date')
        df3=pd.read_csv(f"./Output/ensemble/{ensembleFolder}/walk"+"Week"+str(j)+"ensemble_"+type+".csv",index_col='Date')

        from_date=str(df2.index[0])
        to_date=str(df2.index[len(df2)-1])

        for deleted in range(1,numDel):
            del df1['iteration'+str(deleted)]
            del df2['iteration'+str(deleted)]
            del df3['iteration'+str(deleted)]

            
        df1 = pd.DataFrame(df1[iteration])
        df1.rename(columns={iteration: 'ensemble'}, inplace=True)

        df2.index = pd.to_datetime(df2.index)
        df2.index = df2.index.strftime('%m/%d/%Y')
        df2.rename(columns={'trend': 'ensemble'}, inplace=True)

        df3.index = pd.to_datetime(df3.index)
        df3.index = df3.index.strftime('%m/%d/%Y')
        df3.rename(columns={'trend': 'ensemble'}, inplace=True)

        for deleted in range(1,numDel):
            del df['iteration'+str(deleted)]

        df = pd.DataFrame(columns=['ensemble'])
        df = df.set_index(pd.Index([], name='date'))

        for k in range(0,len(df1)):
            if(df1.index[k] in df2.index):
                if df1['ensemble'][k] == 0:
                    df.loc[df1.index[k]] = 0
                else:
                    Sh = normalized(df1['ensemble'][k])
                    Sw = normalized(getActionWeek(df3, df2.index[k]))
                    Sd = normalized(df2.loc[df1.index[k],'ensemble'])
                    
                    if Sh == 1:
                        if Sw + Sd >= 1:
                            df.loc[df1.index[k]] = 1
                    elif Sh == -1: 
                        if Sw + Sd <= -1:
                            df.loc[df1.index[k]] = -1
                    else:
                        df.loc[df1.index[k]] = 0
 
        num=0
        rew=0
        pos=0
        neg=0
        doll=0
        cov=0
        for date, i in df.iterrows():
            num+=1

            if date in dax.index:
                if (i['ensemble']==1):
                    pos+= 1 if (dax.at[date,'Close']-dax.at[date,'Open'])/dax.at[date,'Open'] > 0 else 0

                    neg+= 0 if (dax.at[date,'Close']-dax.at[date,'Open'])/dax.at[date,'Open'] > 0 else 1
                    rew+=(dax.at[date,'Close']-dax.at[date,'Open'])/dax.at[date,'Open']
                    doll+=(dax.at[date,'Close']-dax.at[date,'Open'])*50
                    cov+=1
                elif (i['ensemble']==-1):

                    neg+= 0 if -(dax.at[date,'Close']-dax.at[date,'Open'])/dax.at[date,'Open'] > 0 else 1
                    pos+= 1 if -(dax.at[date,'Close']-dax.at[date,'Open'])/dax.at[date,'Open'] > 0 else 0
                    rew+=-(dax.at[date,'Close']-dax.at[date,'Open'])/dax.at[date,'Open']
                    cov+=1
                    doll+=-(dax.at[date,'Close']-dax.at[date,'Open'])*50

        values.append([from_date, to_date,str(round(rew,2)),str(round(pos,2)),str(round(neg,2)),str(round(doll,2)),str(round(cov/num,2)),(str(round(pos/cov,2)) if (cov>0) else "None")])

        dollSum+=doll
        rewSum+=rew
        posSum+=pos
        negSum+=neg
        covSum+=cov
        numSum+=num


    values.append([' ','Sum',str(round(rewSum,2)),str(round(posSum,2)),str(round(negSum,2)),str(round(dollSum,2)),str(round(covSum/numSum,2)),(str(round(posSum/covSum,2)) if (covSum>0) else "None")])
    # print(values)
    return values,columns

