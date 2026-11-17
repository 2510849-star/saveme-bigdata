"""Compara três documentos com o CSV, sem escrever no MongoDB."""

from contextlib import closing
import json
from pathlib import Path

from bson import BSON

from carga_mongodb import BANCO, COLECAO, conectar
from pipeline_tratamento import iterar_documentos


def diferencas(esperado, atual, caminho=""):
    resultado = []
    if type(esperado) is not type(atual):
        resultado.append({"campo": caminho, "tipo_esperado": type(esperado).__name__,
                          "tipo_atual": type(atual).__name__})
    if isinstance(esperado, dict) and isinstance(atual, dict):
        if list(esperado) != list(atual):
            resultado.append({"campo": caminho, "ordem_esperada": list(esperado), "ordem_atual": list(atual)})
        for chave in esperado.keys() | atual.keys():
            if chave not in esperado or chave not in atual:
                resultado.append({"campo": caminho + "." + chave, "campo_ausente": True})
            else:
                resultado.extend(diferencas(esperado[chave], atual[chave], caminho + "." + chave))
    elif isinstance(esperado, list) and isinstance(atual, list):
        if len(esperado) != len(atual):
            resultado.append({"campo": caminho, "tamanhos_diferentes": True})
        for i, (a, b) in enumerate(zip(esperado, atual)):
            resultado.extend(diferencas(a, b, f"{caminho}[{i}]"))
    elif esperado != atual:
        resultado.append({"campo": caminho, "valor_diferente": True})
    return resultado


def main():
    cliente = conectar()
    relatorio = []
    try:
        colecao = cliente[BANCO][COLECAO]
        with closing(iterar_documentos(Path("data/games_march2025_cleaned.csv"))) as documentos:
            for esperado in documentos:
                persistido = colecao.find_one({"appid": esperado["appid"]})
                if persistido is None:
                    raise RuntimeError("Documento esperado não encontrado")
                sem_id = {k: v for k, v in persistido.items() if k != "_id"}
                com_id_final = {**esperado, "_id": persistido["_id"]}
                com_id_inicio = {"_id": persistido["_id"], **esperado}
                relatorio.append({"appid": esperado["appid"],
                                  "campos_persistidos": list(persistido),
                                  "diferencas_sem_id": diferencas(esperado, sem_id),
                                  "bson_sem_id_identico": BSON.encode(esperado) == BSON.encode(sem_id),
                                  "bson_id_inicio_identico": BSON.encode(com_id_inicio) == BSON.encode(persistido),
                                  "bson_id_final_identico": BSON.encode(com_id_final) == BSON.encode(persistido)})
                if len(relatorio) == 3:
                    break
    finally:
        cliente.close()
    destino = Path("outputs/mongodb/diagnostico_idempotencia.json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
