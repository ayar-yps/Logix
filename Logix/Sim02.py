# -*- coding: utf-8 -*-
"""
SIMULACIÓN DE OPERACIONES LOGÍSTICAS EN ALPASUR S.A. - KEMFA S.A.
@author: Ayar Yuman Paco Sanizo
@version: 2.0
@summary: Simulación de operaciones logísticas en un centro de transbordo y almacenamiento.
"""

import simpy
import random


class Camion(object):
    """Clase para el modelado de camiones presentes en el sistema"""

    def __init__(self, entorno, nombre):
        """
        Define las propiedades principales de la clase camion
        :type entorno: simpy.Environment
        :type nombre: int
        """
        productos = ["Harina de Soya - Hi Pro", "Harina de Soya - Full Fat", "Torta de Soya",
                     "Torta de Girasol", "Aceite de Soya", "Pellet de Soya", "Grano de Soya",
                     "Azucar", "Fierro", "Contenedor 20", "Contenedor 40"]

        self.nombre = nombre
        self.carga = random.choice(productos)
        self.peso = 28
        if random.random() <= 0.5:
            self.tipo = "Descarga"
        else:
            self.tipo = "Carga"
        self.historial_eventos = {"Proceso de ingreso": entorno.event,
                                  "Proceso de Manipuleo": entorno.event,
                                  "Proceso de salida": entorno.event}

    @staticmethod
    def llega_a_instalacion(entorno):  # TODO Análizar si convertir en un metodo normal
        """Generador la llegada del camion
        :type entorno: simpy.Environment
        """
        tell = random.uniform(2, 5)  # TODO Modificar con información real
        yield entorno.timeout(tell)


class Operacion(object):
    """Clase para el modelado de las operaciones presentes en el sistema."""

    def __init__(self, nombre, recurso, ts_distrib, parametros):
        """
        Define las características principales de la clase operación.
        :type nombre: str
        :type recurso: simpy.Resource
        :type ts_distrib: str
        :type parametros: list
        """
        self.nombre = nombre
        self.recurso = recurso
        self.ts_distrib = ts_distrib
        self.parametros = parametros

    def tiempo_de_servicio(self):  # TODO Incluir distribuciones de probabilidad
        """Genera el tiempo de servicio de la operación"""
        if self.ts_distrib == "uniforme":
            ts = random.uniform(*self.parametros)
        elif self.ts_distrib == "triangular":
            ts = random.triangular(*self.parametros)
        else:
            print "Error, distribución no reconocida"
            ts = None
        return round(ts, 2)

    def atencion_operacion(self, entorno, camion):
        """Simula la ejecución de la operación registrando y mostrando datos de la atención.
        :type entorno: simpy.Environment
        :type camion: Camion.
        """
        arribo = entorno.now
        with self.recurso.request() as turno:
            yield turno
            inicio = round(entorno.now, 2)
            espera = round(inicio - arribo, 2)
            yield entorno.timeout(self.tiempo_de_servicio())
            salida = round(entorno.now, 2)
            print [camion.nombre, camion.carga, camion.peso, self.nombre, inicio, espera, salida]


class SistemaLogistico(object):
    def __init__(self, entorno):

        self.camion = []

        # Definición de Recursos
        self.recursos = {"Ventanilla Recepcion": simpy.Resource(entorno, capacity=1),
                         "Ventanilla Despacho": simpy.Resource(entorno, capacity=1),
                         "Balanza 2": simpy.Resource(entorno, capacity=1),
                         "Estacion Volcadora": simpy.Resource(entorno, capacity=1),
                         "Estacion Tolva": simpy.Resource(entorno, capacity=1),
                         "Pala Mecanica": simpy.Resource(entorno, capacity=1),
                         "Cuadrilla de Estibaje": simpy.Resource(entorno, capacity=3),
                         "Cabina de Recepcion": simpy.Resource(entorno, capacity=2),
                         "Cabina de Despacho": simpy.Resource(entorno, capacity=2),
                         "Grua": simpy.Resource(entorno, capacity=1)}

        # Definicion de Operaciones # TODO Ingresar datos reales
        operaciones_descarga = {"Descarga con volcadora": Operacion("Descarga con volcadora",
                                                                    self.recursos["Estacion Volcadora"],
                                                                    "uniforme", [14, 20]),
                                "Descarga a pulso - Sacos": Operacion("Descarga a pulso - Sacos",
                                                                      self.recursos["Cuadrilla de Estibaje"],
                                                                      "uniforme", [30, 45]),
                                "Descarga a pulso - Granos": Operacion("Descarga a pulso - Granos",
                                                                       self.recursos["Cuadrilla de Estibaje"],
                                                                       "uniforme", [40, 60]),
                                "Descarga con bombas electricas": Operacion("Descarga con bombas electricas",
                                                                            self.recursos["Cabina de Recepcion"],
                                                                            "uniforme", [40, 50]),
                                "Descarga con grua": Operacion("Descarga con grua",
                                                               self.recursos["Grua"],
                                                               "uniforme", [15, 20])}

        operaciones_carga = {"Carga con tolva": Operacion("Carga con tolva",
                                                          self.recursos["Estacion Tolva"],
                                                          "uniforme", [14, 20]),
                             "Carga con pala mecanica": Operacion("Carga con pala mecanica",
                                                                  self.recursos["Pala Mecanica"],
                                                                  "uniforme", [18, 30]),
                             "Carga a pulso - Sacos": Operacion("Carga a pulso - Sacos",
                                                                self.recursos["Cuadrilla de Estibaje"],
                                                                "uniforme", [45, 70]),
                             "Carga a pulso - Granos": Operacion("Carga a pulso - Granos",
                                                                 self.recursos["Cuadrilla de Estibaje"],
                                                                 "uniforme", [60, 90]),
                             "Carga con bombas electricas": Operacion("Carga con bombas electricas",
                                                                      self.recursos["Cabina de Despacho"],
                                                                      "uniforme", [45, 60]),
                             "Carga con grua": Operacion("Carga con grua",
                                                         self.recursos["Grua"],
                                                         "uniforme", [15, 22])}

        operaciones_transbordo = {"Transbordo en sistema mecanizado (D)": Operacion("Transbordo en sistema mecanizado",
                                                                                    self.recursos["Estacion Volcadora"],
                                                                                    "uniforme", [14, 20]),
                                  "Transbordo en sistema mecanizado (C)": Operacion("Transbordo en sistema mecanizado",
                                                                                    self.recursos["Estacion Tolva"],
                                                                                    "uniforme", [14, 20]),
                                  "Transbordo a pulso - Sacos": Operacion("Transbordo a pulso - Sacos",
                                                                          self.recursos["Cuadrilla de Estibaje"],
                                                                          "uniforme", [40, 60]),
                                  "Transbordo a pulso - Granos": Operacion("Transbordo a pulso - Sacos",
                                                                           self.recursos["Cuadrilla de Estibaje"],
                                                                           "uniforme", [45, 65]),
                                  "Transbordo con grua": Operacion("Transbordo con grua",
                                                                   self.recursos["Grua"],
                                                                   "uniforme", [15, 20])}

        operaciones_complementarias = {"Atencion recepcion 1": Operacion("Atencion recepcion 1",
                                                                         self.recursos["Ventanilla Recepcion"],
                                                                         "uniforme", [2, 5]),
                                       "Atencion despacho 1": Operacion("Atencion despacho 1",
                                                                        self.recursos["Ventanilla Despacho"],
                                                                        "uniforme", [2, 5]),
                                       "Primer pesaje": Operacion("Primer pesaje",
                                                                  self.recursos["Balanza 2"],
                                                                  "uniforme", [3, 6]),
                                       "Segundo pesaje": Operacion("Segundo pesaje",
                                                                   self.recursos["Balanza 2"],
                                                                   "uniforme", [3, 6]),
                                       "Atencion recepcion 2": Operacion("Atencion recepcion 2",
                                                                         self.recursos["Ventanilla Recepcion"],
                                                                         "uniforme", [4, 8]),
                                       "Atencion despacho 2": Operacion("Atencion despacho 2",
                                                                        self.recursos["Ventanilla Despacho"],
                                                                        "uniforme", [2, 5])}

        # Diccionario general de operaciones
        self.operaciones = {"Operaciones descarga": operaciones_descarga,
                            "Operaciones carga": operaciones_carga,
                            "Operaciones transbordo": operaciones_transbordo,
                            "Operaciones complementarias": operaciones_complementarias}

    def simular(self, entorno):
        """Genera camiones en el entorno de simulación
        :type entorno: simpy.Environment
        """
        print('Simulación de Operaciones Logísticas en ALPASUR S.A. - KEMFA S.A.')

        camiones_conjuntos = {"Harina de Soya - Hi Pro": {"Descarga": [], "Carga": []},
                              "Harina de Soya - Full Fat": {"Descarga": [], "Carga": []},
                              "Torta de Soya": {"Descarga": [], "Carga": []},
                              "Torta de Girasol": {"Descarga": [], "Carga": []},
                              "Aceite de Soya": {"Descarga": [], "Carga": []},
                              "Pellet de Soya": {"Descarga": [], "Carga": []},
                              "Grano de Soya": {"Descarga": [], "Carga": []},
                              "Azucar": {"Descarga": [], "Carga": []},
                              "Fierro": {"Descarga": [], "Carga": []},
                              "Contenedor 20": {"Descarga": [], "Carga": []},
                              "Contenedor 40": {"Descarga": [], "Carga": []}}
        lista_procesos = []
        nombres = []
        i = 0

        while True:
            # Genera camion y su llegada
            nombre = i + 1
            self.camion.append(Camion(entorno, nombre))
            camiones_conjuntos[self.camion[i].carga][self.camion[i].tipo].append(self.camion[i])  # TODO Analizar uso

            yield entorno.process(self.camion[i].llega_a_instalacion(entorno))
            # Atención del camion
            entorno.process(self.atencion_camion(entorno, self.camion[i], lista_procesos, nombres))
            i += 1

    def atencion_camion(self, entorno, camion, lista_procesos, nombres):
        """Simula el proceso de atencion de camiones dividiendolo en 3 etapas:
        - Operaciones complementarias preliminares
        - Operaciones de manipuleo
        - Operaciones complementarias posterores

        :type entorno: simpy.Environment
        :type camion: Camion
        :type nombres: list
        """
        # Llegada de camion


        # Operaciones Complementarias Ingreso
        p_ingreso = entorno.process(self.atencion_ingreso(entorno, camion, self.operaciones))
        lista_procesos.append(p_ingreso)
        nombres.append(camion.nombre)

        yield p_ingreso

        yield entorno.process(self.espera_transbordo(entorno, camion, self.operaciones, lista_procesos, nombres))

        # Manipuleo
        yield entorno.process(self.programar_manipuleo(camion, self.operaciones).ejecutar(entorno,camion))

        # Operaciones Complementarias Salida
        yield entorno.process(self.atencion_salida(entorno, camion, self.operaciones))

    def programar_manipuleo(self, camion, operaciones):  # TODO Asignar operación como en el sist. real
        """Programa la operacion de manipuleo en relacion al tipo de carga, la disponibilidad de camiones
        para realizar transbordos y las colas de espera en las estaciones de manipuleo.

        :param camion: Camion a ser atentido
        :param operaciones: Conjunto de operaciones de manipuleo
        """

        if camion.tipo != "Carga":

            if camion.carga in ["Grano de Soya", "Harina de Soya - Hi Pro", "Pellet de Soya"]:

                if random.random() <= 0.5:
                    op = operaciones["Operaciones descarga"][random.choice(["Descarga con volcadora",
                                                                            "Descarga a pulso - Granos"])]
                else:
                    op = operaciones["Operaciones transbordo"][random.choice(["Transbordo en sistema mecanizado (D)",
                                                                              "Transbordo a pulso - Granos"])]

            elif camion.carga in ["Harina de Soya - Full Fat", "Torta de Soya", "Torta de Girasol", "Azucar"]:

                if random.random() <= 0.5:
                    op = operaciones["Operaciones descarga"]["Descarga a pulso - Sacos"]
                else:
                    op = operaciones["Operaciones transbordo"]["Transbordo a pulso - Sacos"]

            elif camion.carga == "Aceite de Soya":
                op = operaciones["Operaciones descarga"]["Descarga con bombas electricas"]

            elif camion.carga in ["Contenedor 20", "Contenedor 40"]:
                op = operaciones["Operaciones descarga"]["Descarga con grua"]

            elif camion.carga == "Fierro":
                op = operaciones["Operaciones transbordo"]["Transbordo con grua"]

            else:
                print "Error, carga no reconcida"
                op = None

        else:

            if camion.carga in ["Grano de Soya", "Harina de Soya - Hi Pro", "Pellet de Soya"]:

                if random.random() <= 0.5:
                    op = operaciones["Operaciones carga"][random.choice(["Carga con tolva", "Carga a pulso - Granos",
                                                                         "Carga con pala mecanica"])]
                else:
                    op = operaciones["Operaciones transbordo"][random.choice(["Transbordo en sistema mecanizado (C)",
                                                                              "Transbordo a pulso - Granos"])]

            elif camion.carga in ["Harina de Soya - Full Fat", "Torta de Soya", "Torta de Girasol", "Azucar"]:

                if random.random() <= 0.5:
                    op = operaciones["Operaciones carga"]["Carga a pulso - Sacos"]
                else:
                    op = operaciones["Operaciones transbordo"]["Transbordo a pulso - Sacos"]

            elif camion.carga == "Aceite de Soya":
                op = operaciones["Operaciones carga"]["Carga con bombas electricas"]

            elif camion.carga in ["Contenedor 20", "Contenedor 40"]:
                op = operaciones["Operaciones carga"]["Carga con grua"]

            elif camion.carga == "Fierro":
                op = operaciones["Operaciones transbordo"]["Transbordo con grua"]

            else:
                print "Error, carga no reconcida"
                op = None

        return op

    def atencion_ingreso(self, entorno, camion, operaciones):
        if camion.tipo == "Descarga":
            yield entorno.process(operaciones["Operaciones complementarias"]["Atencion recepcion 1"])
        else:
            yield entorno.process(operaciones["Operaciones complementarias"]["Atencion despacho 1"])

        if camion.carga not in ["Contenedor 20", "Contenedor 40"]:
            yield entorno.process(operaciones["Operaciones complementarias"]["Primer pesaje"])

    def atencion_salida(self, entorno, camion, operaciones):
        if camion.carga not in ["Contenedor 20", "Contenedor 40"]:
            yield entorno.process(operaciones["Operaciones complementarias"]["Segundo pesaje"])

        if camion.tipo == "Descarga":
            yield entorno.process(operaciones["Operaciones complementarias"]["Atencion recepcion 2"])
        else:
            yield entorno.process(operaciones["Operaciones complementarias"]["Atencion despacho 2"])

    def espera_transbordo(self, entorno, camion, operaciones, lista_procesos, nombres):
        espera = entorno.timeout(10)
        camion_dos_listo = lista_procesos[camion.nombre - 1]
        # print len(lista_procesos)
        # print nombres
        # print round(entorno.now,2)

        # for proceso in lista_procesos:
        #    print proceso.value
        # x for x in lista_procesos if x.value != camion.nombre

        yield espera | camion_dos_listo

        if camion_dos_listo.triggered:
            print "Transbordo " + str(round(entorno.now, 2)) + " " + str(camion_dos_listo)
            print camion.nombre
            print camion_dos_listo.value
        else:
            print "Carga o descarga"
            print camion.nombre


# Simulación
# if __name__ == "__main__":
random.seed(42)
sim=4*60
env = simpy.Environment
sistemaLogistico = SistemaLogistico(env)
env.process(sistemaLogistico.simular(env))
env.run(until=sim)
