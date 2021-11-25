# calculate coefficient and intercept of the (body-forehead) difference line by linear regression

import openpyxl
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

df = pd.read_excel('temp.xlsx', sheet_name='export', engine='openpyxl')

ambient  = df[['ambient']]
body     = df['body']
forehead = df['forehead']
diff     = body - forehead

model_lr = LinearRegression()
model_lr.fit(ambient, diff)

print('corf =', model_lr.coef_[0])
print('intercept =', model_lr.intercept_)

plt.plot(ambient, diff, 'o')
plt.plot(ambient, model_lr.predict(ambient), linestyle='solid')
plt.show()
