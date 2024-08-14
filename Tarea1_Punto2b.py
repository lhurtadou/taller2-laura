#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 18:29:46 2024

@author: laurasofiahurtadourrego
"""
import matplotlib.pyplot as plt
import pandas as pd
from gurobipy import Model,GRB

#Datos
file_name = 'ddd.xlsx'
conjuntos= pd.read_excel(io= file_name,sheet_name="Conjuntos")

#Conjuntos
P =[i for i in conjuntos["Productos"] if not pd.isna(i)]
E =[j for j in conjuntos["Estaciones"] if not pd.isna(j)]
F =[f for f in conjuntos["Productos"] if not pd.isna(f)]

#-----------------
#PARAMETROS

#Tiempos
t= pd.read_excel(io= file_name,sheet_name="Tiempos", index_col=[0,1]).squeeze()
#Secuencia de los productos
secuencia_producto = {
    1: ["Corte", "Pulido"],  
    2: ["Moldeo", "Corte", "Pulido"],  
    3: ["Pulido", "Corte", "Moldeo"], 
}

#Modelo de optimizacion
m = Model("Tiempos")
M = 3000

#Variables
x = m.addVars(P,E, vtype = GRB.INTEGER, name = "x")
y = m.addVars(P,F,E, vtype = GRB.BINARY, name = "y")
z = m.addVar(vtype = GRB.INTEGER, name = "z")

#Restricciones

# Garantizar la secuencialidad

#-------------------PRODUCTO-1-------------------------------------------------

m.addConstr(x[1, "Corte"] + 30 <= x[1, 'Pulido'])
    
#-------------------PRODUCTO-2-------------------------------------------------

m.addConstr(x[2, 'Moldeo'] + 20 <= x[2, 'Corte'])
m.addConstr(x[2, 'Corte'] + 10 <= x[2, 'Pulido'])

#-------------------PRODUCTO-3-------------------------------------------------

m.addConstr(x[3, 'Pulido'] + 12 <= x[3, 'Corte'])
m.addConstr(x[3, 'Corte'] + 17 <= x[3, 'Moldeo'])

#Que la última tarea de cada producto se complete antes de la finalización de la jornada de producción

m.addConstr(x[1, "Pulido"] + 15 <= z)
m.addConstr(x[2, "Pulido"] + 34 <= z)
m.addConstr(x[3, "Moldeo"] + 28 <= z)

# No simultaneidad en una máquina

# M1 (Moldeo)
m.addConstr(x[2, 'Moldeo'] + 20 - x[3, 'Moldeo'] <= M * (1 - y[3,2,'Moldeo']))
m.addConstr(x[3, 'Moldeo'] + 28 - x[2, 'Moldeo'] <= M * y[3,2,'Moldeo'])

# M2 (Corte)
m.addConstr(x[1, 'Corte'] + 30 - x[2, 'Corte'] <= M * (1 - y[2,1,"Corte"]))
m.addConstr(x[2, 'Corte'] + 10 - x[1, 'Corte'] <= M * (y[2,1,"Corte"]))

m.addConstr(x[1, 'Corte'] + 30 - x[3, 'Corte'] <= M * (1 - y[3,1,"Corte"]))
m.addConstr(x[3, 'Corte'] + 17 - x[1, 'Corte'] <= M * (y[3,1,"Corte"]))

m.addConstr(x[2, 'Corte'] + 10 - x[3, 'Corte'] <= M * (1 - y[3,2,"Corte"]))
m.addConstr(x[3, 'Corte'] + 17 - x[2, 'Corte'] <= M * (y[3,2,"Corte"]))

# M3 (Pulido)
m.addConstr(x[1, 'Pulido'] + 15 - x[2, 'Pulido'] <= M * (1 - y[2,1,"Pulido"]))
m.addConstr(x[2, 'Pulido'] + 34 - x[1,"Pulido"] <= M*(y[2,1,"Pulido"]))

m.addConstr(x[1, 'Pulido'] + 15 - x[3, 'Pulido'] <= M * (1 - y[3,1,"Pulido"]))
m.addConstr(x[3, 'Pulido'] + 12 - x[1,"Pulido"] <= M*(y[3,1,"Pulido"]))

m.addConstr(x[2, 'Pulido'] + 34 - x[3, 'Pulido'] <= M * (1 - y[3,2,"Pulido"]))
m.addConstr(x[3, 'Pulido'] + 12 - x[2,"Pulido"] <= M*(y[3,2,"Pulido"]))

#Funcion Objetivo
m.setObjective(z,GRB.MINIMIZE)
#Optimizar
m.update()
m.optimize()

#Mostrar valor optimo
w = m.getObjective().getValue()

# Imprimir resultados de las variables de decisión x
for i in P:
    for j in E:
        print(f"x[{i}, {j}] = {x[i, j].x}")

# Imprimir resultados de las variables de decisión y
for i in P:
    for f in F:
        for j in E:
            print(f"y[{i}, {f}, {j}] = {y[i, f, j].x}")

# Imprimir resultado de la variable de decisión z
print(f"z = {z.x}")

# Función para obtener los tiempos de inicio y finalización de cada tarea en cada estación para cada producto
def obtener_tiempos(x):
    tiempos = {}
    for i in P:
        for j in E:
            inicio = x[i, j].x
            fin = t[j, i]
            tiempos[(i, j)] = (inicio, fin)
    return tiempos

tiempos = obtener_tiempos(x)

# DataFrame para el diagrama de Gantt
df_gantt = pd.DataFrame(tiempos.values(), index=tiempos.keys(), columns=['Inicio', 'Fin'])

# Ajustar los tiempos de finalización para que terminen en el tiempo z
df_gantt['Fin'] = df_gantt['Fin'].apply(lambda x: z.x if x > z.x else x)

# Crear diagrama de Gantt
fig, ax = plt.subplots(figsize=(10, 5))

for i, estacion in enumerate(E):
    ax.broken_barh(df_gantt[df_gantt.index.get_level_values(1) == estacion].values, 
                    (i - 0.4, 0.8), 
                    facecolors=('tab:pink', 'tab:blue', 'tab:green'))

ax.set_yticks(range(len(E)))
ax.set_yticklabels(E)
ax.set_xlabel('Tiempo')
ax.set_title('Diagrama de Gantt')

plt.show()
