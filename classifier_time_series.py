import pandas as pd
from tqdm import tqdm, trange
import tables
from sklearn.linear_model import LinearRegression, SGDRegressor
from sklearn import cross_validation
import numpy as np
from sklearn.metrics import mean_squared_error
from featurizer import *
from pandas.tseries.offsets import *
import math
import matplotlib.pyplot as plt
import sys

def execute(n):
	training_df = load_training_set("files/train_groupedby.csv")
	training_df = training_df.set_index('DATE', drop=False)

	submission_df = load_submission("files/submission_test02.txt")
	submission_df = submission_df.set_index('DATE', drop=False)

	y_true = submission_df.as_matrix()[:, -1]
	y_pred = np.zeros(len(y_true))

	assignments = learn_structure("files/train_groupedby.csv")
	ass_df = {}
	for ass in assignments:
		local_df = load_training_set('files/assign/train_'+str(ass)+'.csv')
		local_df = local_df.set_index('DATE', drop=False)
		local_df['time'] = local_df.index.time
		local_df['rolling_mean'] = pd.rolling_mean(local_df['CSPL_RECEIVED_CALLS'], window=3, min_periods=1)
		local_df['exp_mean'] = pd.ewma(local_df['CSPL_RECEIVED_CALLS'], span=10)
		ass_df[ass] = local_df

	submission_df = submission_df.set_index(['DAY_WE_DS', 'DATE', 'ASS_ASSIGNMENT'], drop=False)

	for i in trange(0, submission_df.shape[0]):
		(day, datetime, assignment) = submission_df.index[i]
		time = datetime.time()

		local_df = ass_df[assignment]
		local_df = local_df[local_df.DAY_WE_DS == day]
		local_df = local_df[local_df.time == time]
		local_df = local_df[local_df.DATE < (datetime - DateOffset(days=3))]
		local_df = local_df.tail(int(n))
		
		# local_df = local_df[(datetime - DateOffset(years=1, days=3) < local_df.DATE) & (local_df.DATE < (datetime - DateOffset(years=1)))]

		# print y_true[i]
		# if (local_df['rolling_mean'].mean() > 5):
			# ax = local_df.plot(x=local_df.index, y='rolling_mean', style='o', legend=False)
			# local_df.plot(x=local_df.index, y='CSPL_RECEIVED_CALLS', style='o', legend=False, ax = ax)
			# plt.show()
		# print local_df
		# median = local_df['CSPL_RECEIVED_CALLS'].median()

		# recent = local_df['rolling_mean'].tail(1).as_matrix()[0]
		# if (recent < 1):
			# y_pred[i] = 0
		# else:
		y_pred[i] = local_df['CSPL_RECEIVED_CALLS'].mean()
		# local_df['exp_mean'] = pd.ewma(local_df['CSPL_RECEIVED_CALLS'], span=10)
		# y_pred[i] = y_pred[i] = local_df['exp_mean'].tail(1)
		# y_pred[i] = local_df['rolling_mean'].tail(1)

	y_pred_round = y_pred

	y_pred_round = [int(round(x)) if x > 0 else 0 for x in y_pred]
	# print(y_pred_round)

	x = range(len(y_pred))
	plt.plot(x, y_pred, x, y_true)
	submission_df.prediction = y_pred_round
	submission_df = submission_df.set_index('DATE', drop=False)
	submission_df['DATE'] = submission_df.index.strftime('%Y-%m-%d %H:%M:%S.000')
	# print submission_df

	submission_df[['DATE', 'ASS_ASSIGNMENT', 'prediction']].to_csv('results/submission_test06.txt', sep='\t', index=False)

	print('MSE round: '),
	print(mean_squared_error(y_true, y_pred_round))

	print('MSE not round: '),
	print(mean_squared_error(y_true, y_pred))

if __name__ == "__main__":
    execute(sys.argv[1])