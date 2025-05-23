# -*- coding: utf-8 -*-
"""project_QSAR.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1beydrhvrJDjLW1XnINJXRl6bYdVcdug4

## QSPR на основе детерменированных цифровых представлений структуры

#### **Сдача стандартного итогового проекта:**
* Назовите файл по шаблону project_Ivanov_Ivan.ipynb, подставив свою фамилию и имя.  Выполненную работу нужно отправить на почту ivan.s.zlobin@gmail.com, указав в теме письма "Хемометрика и Хемоинформатика, Иванов Иван, 3 курс", подставив свою фамилию, имя и номер курса. **Работы, присланные иным способом, не принимаются.**
* Прислать нужно **ноутбук в формате `ipynb`**.
* Для выполнения задания **используйте этот ноутбук в качестве основы, ничего не удаляя из него**. Можно добавлять необходимое количество ячеек.
* Комментарии к решению пишите в markdown-ячейках.
* **Код из рассказанных на занятиях ноутбуков** (и из интернета, без злоупотреблений) можно использовать без ограничений.

**Дедлайн по заданию**: 23:59 21 декабря

**Работы, присланные после дедлайна, не проверяются.**

---

**Баллы за задание:**

Баллы выставляются в соответствии с критериями проверки итогового проекта, указанными в ПУД. Данный проект представляет собой учебную исследовательскую задачу - отнеситесь к этому именно как к научному проекту. Наибольший вес в оценке будут иметь именно выводы из исследования, их содержательность и подкрепленность фактическими наблюдениями (например, графиками или качеством построенных моделей).

Максимальная оценка за данный проект - 9
"""

!pip install rdkit

#все это у вас должно быть установлено с предыдущих домашек
import numpy as np
import pandas as pd
import seaborn as sns


from rdkit import Chem
from rdkit.Chem.Draw import IPythonConsole
from rdkit.Chem import Draw
IPythonConsole.ipython_useSVG=True

from rdkit.Chem import PandasTools
from rdkit.Chem.Draw import IPythonConsole

"""Одной из любимых задач хемоинформатиков является разработка разного рода молекулярных представлений и алгоритмов обработки химической информации. Как правило, для проверки подобных моделей, требуются некоторые большие и грамотно составленные датасеты, на которых еще и можно будет сравнивать результаты своего интеллектуального труда с показателями коллег (т.е. использовать в качестве бенчмарка). К сожалению для нас и к радости БМов большинство таких датасетов собраны в первую очередь в смежных с фармакологией и биохимией областях - подобная информация там всегда документировалась и заносилась в базы еще до бума ML.

Но и нам иногда перепадает что-то интересное - мы возьмем QM9, датасет собранный и полученный вот тут https://arxiv.org/abs/1703.00564. Он содержит более 130 тысяч молекул, для которых при помощи инструментов квантовой химии рассчитаны различные энергетические характеристики (энергии HOMO и LUMO, колебательные постоянные, энтальпия и т.д.).

Внутри "сырых" данных есть два нужных нам файла - gdb9.sdf, где хранятся все структуры в sdf формате (напомню, что это такое расширенное представление, похожее на формат .mol) и gdb9.sdf.csv, где перечислены свойства соответствующих веществ. Организуем из этого добра датасет:
"""

!unzip QM9.zip

df = pd.read_csv('QM9/raw/gdb9.sdf.csv')

new_df = PandasTools.LoadSDF('QM9/raw/gdb9.sdf', embedProps=True, molColName=None, smilesName='smiles')
#RDKit умеет корректно открывать sdf файлы, еще и превращать их в датафрейм со SMILES, если указать такие параметры в функции
#не пугайтесь ошибкам - какие-то из соединений "по-простому" не получится распарсить - мы их пока выкинем

df

new_df

"""Теперь объединим эти два датафрейма. Можно, конечно, было бы это сделать тупым добавлением столбцов, но мы хотим убедиться, что смайлсы будут записаны в _df_ для нужных ID соединений, поэтому сделаем это более надежным способом:"""

df = df.rename(columns={"mol_id": "ID"}) #переназовем столбец в df, чтобы название совпадало с new_df
df = pd.merge(df, new_df, on="ID") #корректно объединим датафреймы по столбцу с ID соединений
df
#и вот теперь у нас есть датасет, готовый к работе

"""Пока что упростим себе задачу и будем воспринимать в качестве таргетов _alpha_, то бишь изотропную поляризуемость молекулы, _cv_ (молярную теплоемкость при постоянном объеме) и _gap_ (ширину запрещенной зоны). Отпечатки Моргана молекулы возьмем в качестве фичей."""

subset_df = df.sample(n=15000, random_state=42) # Для оптимизации расчет уменьшили количество молекул до 15 тысяч

target_df = subset_df[['alpha', 'cv', 'gap']].copy()
smiles_df = subset_df[['smiles']].copy()

"""## Задача 0

Дополните SMILES-БД отпечатками Моргана в виде битного вектора. Данная БД будет выступать в качестве фичей алгоритма регрессии в дальнейших задачах
"""

# Функция для генерации отпечатков Моргана
def generate_morgan_fingerprint(smiles, radius=4, n_bits=2048):
    mol = Chem.MolFromSmiles(smiles)
    fp = Chem.AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    return list(fp)

# Генерация отпечатков и добавление их в бд
smiles_df['morgan_fingerprint'] = smiles_df['smiles'].apply(generate_morgan_fingerprint)

smiles_df

"""## Задача 1

Цель этой задачи - проверить полезность PCA для решения задач QSPR (Quantitative Structure-Property Relationship). В связи с тем, что мы будем сравнивать между собой несколько моделей и способов представления, не забудьте корректно организовать исследование (провести разбиение на трейн и тест в самом начале, зафиксировать random state для воспроизводимости результатов при перезапусках, подобрать логичные метрики для оценки качества).

Подберите и обучите регресионную модель для предсказания описанных выше таргетов при помощи битного векторам отпечатков Моргана (радиус и количество битов в векторе советую подобрать, исходя из метрик регрессии, но без лишнего фанатизма).

На наилучших из подобранных отпечатков проведите понижение размерности при помощи PCA до стольки компонент, сколько сочтете нужным, и снова обучите регрессионную модель на низкоразмерных данных. Запишите, что получилось и насколько полезным показался вам такой способ.

Заметим, что для корректных выводов задание требует целиком оформить пайплайн для решения регрессии - нужно создать набор потенциальных моделей, набора гиперпараметров и пользоваться этим набором для обучения каждого отдельного предиктора для каждого таргета - вспомните про GridSearchCV (или HalvingGridSearchCV, если долго считается) или воспользуйтесь чем-то более продвинутым вроде pipeline из scikit-learn или optuna.

_Если вашему компьютеру станет туго, выделите из исходных баз меньшее подмножество (например, 15 тыс молекул), выбрав его рандомно с зафиксированным random_state_
"""

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.experimental import enable_halving_search_cv
from sklearn.model_selection import HalvingGridSearchCV

# X - входные данные, y - целевая переменная
X = smiles_df
y = target_df.to_numpy()

# Разделение на тренировочные и тестовые данные
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X_train_fingerprints = np.vstack(X_train['morgan_fingerprint'])
X_test_fingerprints = np.vstack(X_test['morgan_fingerprint'])

# Ridge без PCA
pipe_ridge = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', Ridge())
])
param_grid_ridge = {
    'regressor__alpha': [0.1, 10, 15, 20, 35]
}

# Подбор параметров с помощью GridSearchCV
grid_search_ridge = GridSearchCV(pipe_ridge, param_grid_ridge, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)

grid_search_ridge.fit(X_train_fingerprints, y_train)

# Оценка
y_pred_ridge = grid_search_ridge.best_estimator_.predict(X_test_fingerprints)
mse_ridge = mean_squared_error(y_test, y_pred_ridge)
r2_ridge = r2_score(y_test, y_pred_ridge)

print("Ridge без PCA")
print(f"Лучшие параметры: {grid_search_ridge.best_params_}")
print(f"MSE: {mse_ridge}")
print(f"R^2: {r2_ridge}")

# RandomForestRegressor без PCA
pipe_rf = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor(random_state=42))
])

param_grid_rf = {
    'regressor__n_estimators': [50, 100],
    'regressor__max_depth': [10]
}

# Для данной модели было принято решение использовать HalvingGridSearchCV, так как она обучалась намного дольше Ridge
# Это немного снизило точность, но применив HalvingGridSearchCV для каждого варианта с RandomForestRegressor, можно все еще адекватно сравнить результаты
halving_search_rf = HalvingGridSearchCV(
    estimator=pipe_rf_pca,
    param_grid=param_grid_rf,
    cv=5,
    scoring='neg_mean_squared_error',
    n_jobs=-1,
    verbose=3,
    min_resources=500,
    factor=2
)

halving_search_rf.fit(X_train_fingerprints, y_train)

# Оценка
y_pred_rf = halving_search_rf.best_estimator_.predict(X_test_fingerprints)
mse_rf = mean_squared_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)

print("RandomForest без PCA")
print(f"Лучшие параметры: {halving_search_rf.best_params_}")
print(f"MSE: {mse_rf}")
print(f"R^2: {r2_rf}")

# Ridge с PCA
pipe = Pipeline([
    ('pca', PCA(n_components=0.95)),
    ('scaler', StandardScaler()),
    ('regressor', Ridge())
])

grid_search = GridSearchCV(pipe, param_grid_ridge, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)

grid_search.fit(X_train_fingerprints, y_train)

# Оценка
y_pred = grid_search.best_estimator_.predict(X_test_fingerprints)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Ridge с PCA")
print(f"Лучшие параметры: {grid_search.best_params_}")
print(f"MSE на тестовых данных: {mse}")
print(f"R^2 на тестовых данных: {r2}")

# RandomForestRegressor с PCA
pipe_rf_pca = Pipeline([
    ('pca', PCA(n_components=0.95)),
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor(random_state=42))
])

halving_search_rf.fit(X_train_fingerprints, y_train)

# Оценка
y_pred_rf_pca = halving_search_rf.best_estimator_.predict(X_test_fingerprints)
mse_rf_pca = mean_squared_error(y_test, y_pred_rf_pca)
r2_rf_pca = r2_score(y_test, y_pred_rf_pca)

print("RandomForest с PCA")
print(f"Лучшие параметры: {halving_search_rf.best_params_}")
print(f"MSE: {mse_rf_pca}")
print(f"R^2: {r2_rf_pca}")

"""_Ваш анализ результатов работы алгоритмов и выводы касательно отпечатков Моргана и PCA для решения QSAR-задач для различных таргетов будет здесь_

**Вывод:** Для начала были проведены эксперименты с обучением моделей на отпечатках Моргана без РСА. Были протестированы разные отпечатки Моргана, разные комбинации радиуса и размера отпечатков, при установлении размера 2048 и радиуса 4, метрики хорошо возросли. Я также попробовала увеличить радиус до 5, но рост метрик был не таким большим, чтобы увеличение нагрузок того стоило.

Насчет полезности использования РСА при обучении. По результатам расчетов на разных моделях, я не заметила сильного преимущества РСА в данной задаче. В некоторых случаях обучение могло пройти чуть быстрее при использовании РСА, но само качество обучения, а именно значения метрик, падало(MSE повышалось, R^2 понижалось) . Например, при обычном обучении Ridge MSE≈9,8, R^2≈0,7, а при обучении Ridge после использования РСА MSE≈11,2, R^2≈0,67.

## Задача 2

Проведите аналогичный анализ, пользуясь альтернативным способом представления SMILES - в виде дескрипторов RDKit и/или Mordred (см код Descriptors and FPs). Если в прошлой задаче вам удалось хорошо задать пайплайн работы**, от вас потребуется только изменить набор входных признаков и, возможно, добавить отбор значащих признаков

** Повторного разделения на трейн и тест здесь происходить не должно! Для корректного сравнения моделей и представлений нужны __одинаковые__ обучающий и тестовый наборы
"""

from rdkit.Chem import Descriptors
from rdkit.ML.Descriptors import MoleculeDescriptors

from sklearn.feature_selection import VarianceThreshold

def RDkit_descriptors(smiles):
    mols = [Chem.MolFromSmiles(i) for i in smiles]
    calc = MoleculeDescriptors.MolecularDescriptorCalculator([x[0] for x in Descriptors._descList])
    desc_names = calc.GetDescriptorNames()

    Mol_descriptors = []
    for mol in mols:
        mol = Chem.AddHs(mol)
        descriptors = calc.CalcDescriptors(mol)
        Mol_descriptors.append(descriptors)

    return pd.DataFrame(Mol_descriptors, columns=desc_names)

X_train_descriptor = RDkit_descriptors(X_train['smiles']).fillna(0)
X_test_descriptor = RDkit_descriptors(X_test['smiles']).fillna(0)

# отбор значащих признаков
X_train_descriptor = VarianceThreshold(threshold=0.01).fit_transform(X_train_descriptor.values)
X_test_descriptor = VarianceThreshold(threshold=0.01).fit_transform(X_test_descriptor.values)

# Обучение Ridge без РСА
grid_search_ridge.fit(X_train_descriptor, y_train)

# Оценка
y_pred_ridge = grid_search_ridge.best_estimator_.predict(X_test_descriptor)
mse_ridge = mean_squared_error(y_test, y_pred_ridge)
r2_ridge = r2_score(y_test, y_pred_ridge)

print("Ridge без PCA")
print(f"Лучшие параметры: {grid_search_ridge.best_params_}")
print(f"MSE: {mse_ridge}")
print(f"R^2: {r2_ridge}")

# Обучение RandomForestRegressor без PCA
grid_search_rf.fit(X_train_descriptor, y_train)

# Оценка
y_pred_rf = grid_search_rf.best_estimator_.predict(X_test_descriptor)
mse_rf = mean_squared_error(y_test, y_pred_rf)
r2_rf = r2_score(y_test, y_pred_rf)

print("RandomForest без PCA")
print(f"Лучшие параметры: {grid_search_rf.best_params_}")
print(f"MSE: {mse_rf}")
print(f"R^2: {r2_rf}")

# Обучение Ridge с PCA
grid_search.fit(X_train_descriptor, y_train)

# Оценка
y_pred = grid_search.best_estimator_.predict(X_test_descriptor)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Ridge с PCA")
print(f"Лучшие параметры: {grid_search.best_params_}")
print(f"MSE на тестовых данных: {mse}")
print(f"R^2 на тестовых данных: {r2}")

# Обучение RandomForestRegressor с PCA
grid_search_rf_pca.fit(X_train_descriptor, y_train)

# Оценка
y_pred_rf_pca = grid_search_rf_pca.best_estimator_.predict(X_test_descriptor)
mse_rf_pca = mean_squared_error(y_test, y_pred_rf_pca)
r2_rf_pca = r2_score(y_test, y_pred_rf_pca)

print("RandomForest с PCA")
print(f"Лучшие параметры: {grid_search_rf_pca.best_params_}")
print(f"MSE: {mse_rf_pca}")
print(f"R^2: {r2_rf_pca}")

"""_Ваш анализ результатов работы алгоритмов и выводы касательно эффективности выбранных дескрипторов для решения QSAR-задач для различных таргетов будет здесь_

**Вывод:** Сначала я попробовала выбрать дескрипторы Mordred, но их там было слишком много, настолько, что при попытке как-то их отфильтровать сеанс в гугл колабе сбрасывался из-за недостатка памяти. Поэтому я решила всё же взять для анализа дескрипторы RDKit, так как там их было примерно в 6 раз меньше.

В сравнении с обучением на отпечатках Моргана для решения QSAR-задачи, на дескрипторах обучение проходило намного быстрее. Однако R^2 метрики в данном случае были меньше, кроме варианта RandomForestRegressor без PCA -- он внезапно показал себя наиболее эффективным достигнув MSE=1.53 и R^2=0.81. Можно заметить, что для отпечатков Моргана наилучшей оказалась модель Ridge, а здесь модель RandomForestRegressor. Значит, в зависимости от признаков для обучения, могут быть эффективны разные модели.

Использование РСА здесь тоже не показало себя особо полезным, оно немного увеличило скорость обучения, но значительно снизило его качество, хотя он и должен был выбрать самостоятельно наиболее эффективное количество компонент. Тут либо произошла какая-то ошибка по их выбору, либо данный метод действительно не может здесь сделать ничего лучше.
"""