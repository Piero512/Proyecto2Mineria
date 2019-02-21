import json

lista = []

with open('vzla_fechas.json') as f:
	lista = json.load(f)

print(len(lista))
print(len(list(filter(lambda x : x is not None ,map(lambda x : x["fecha"],lista)))))
