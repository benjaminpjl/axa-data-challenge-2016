import pandas as pd
from tqdm import tqdm, trange
import tables
from sklearn.linear_model import LinearRegression
from sklearn import cross_validation
import numpy as np
from sklearn.linear_model import SGDRegressor

class Featurizer:
    def __init__(self):
        self.assignments = set()

    def featurize(self, in_filename, out_filename, chunksize=10 ** 6):

        self._learn_structure(in_filename, chunksize)
        dtype = {
            'DATE': object,
            'WEEK_END': int,
            'DAY_WE_DS': str,
            'ASS_ASSIGNMENT': str,
            'CSPL_RECEIVED_CALLS': int
        }

        cols = ['DATE', 'WEEK_END', 'DAY_WE_DS', 'ASS_ASSIGNMENT', 'CSPL_RECEIVED_CALLS']
        chunks = pd.read_csv(in_filename, sep=";", usecols=cols, dtype=dtype, parse_dates=['DATE'], chunksize=chunksize)

        with tables.open_file(out_filename, mode='w') as out:
            atom = tables.Float64Atom()
            i = 0
            arr = None
            for chunk in chunks:
                features = self._featurize_chunk(chunk)
                if i == 0:
                    arr = out.create_earray(out.root, 'features', atom=atom, shape=(0, features.shape[1]))
                arr.append(features.as_matrix())
                i += 1
            out.close()


    def _learn_structure(self, filename, chunksize=10 ** 6):
        self.assignments = set()

        dtype = {'ASS_ASSIGNMENT': str}
        cols = ['ASS_ASSIGNMENT']
        chunks = pd.read_csv(filename, sep=";", usecols=cols, dtype=dtype, chunksize=chunksize)

        for df in tqdm(chunks):
            self.assignments.update(df.ASS_ASSIGNMENT.unique())

        print(self.assignments)

    def _featurize_chunk(self, df):
        features = pd.DataFrame()
        self._featurize_day_of_the_week(df, features)
        self._featurize_time_slot(df, features)
        self._featurize_assignment(df, features)
        self._featurize_number_of_calls(df, features)

        return features

    def _featurize_day_of_the_week(self, df, features):
        print("Featurizing days of the week")

        days = [('monday', 'Lundi'), ('tuesday', 'Mardi'), ('wednesday', 'Mercredi'), ('thursday', 'Jeudi'),
                ('friday', 'Vendredi'), ('saturday', 'Samedi'), ('sunday', 'Dimanche')]

        features['is_week_end'] = df.WEEK_END
        for i in trange(7):
            en, fr = days[i]
            features[en] = (df.DAY_WE_DS == fr).astype(int)

        print()

    def _featurize_time_slot(self, df, features):
        print("Featurizing time slots")

        for h in trange(24):
            for s in range(2):
                features['time_slot_' + str(2 * h + s)] = ((df.DATE.dt.hour == h) & (df.DATE.dt.minute == 30 * s)) \
                    .astype(int)

        print()

    def _featurize_assignment(self, df, features):
        print("Featurizing assignment")
        i = 0
        for assignment in self.assignments:
            features['assignment_' + str(i)] = (df.ASS_ASSIGNMENT == assignment).astype(int)
            i += 1

    def _featurize_number_of_calls(self, df, features):
        features['n_calls'] = df.CSPL_RECEIVED_CALLS

    def linear_regression(self, in_filename, chunksize=10**6):
    	h5_file = tables.open_file(in_filename)
        samples = h5_file.root.features

        clf = SGDRegressor()
        for i in range(0, samples.nrows, chunksize):
        	X = samples[i:i+chunksize, :-1]
        	y = samples[i:i+chunksize, -1]
        	clf.partial_fit(X,y)

        X = samples[:-1,:-1]
        y = samples[:-1, -1]
        y_predicted = clf.predict(X)
        y_predicted = [int(round(x)) if x > 0 else 0 for x in y_predicted]
        diff = (y_predicted - y)**2
        print (sum(diff))

        h5_file.close()

	# print(-scores)

feat = Featurizer()
# feat.featurize('files/train_small.csv', 'files/featurized_small.h5')
feat.linear_regression('files/featurized_france.h5')