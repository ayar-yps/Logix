# -*- coding: utf-8 -*-
"""
SIMULACIÓN DE OPERACIONES LOGÍSTICAS EN ALPASUR S.A. - KEMFA S.A.
@author: Ayar Yuman Paco Sanizo
@version: 1.2
@summary: Simulación de operaciones logísticas en un centro de transbordo y almacenamiento.
"""

import os
import simpy
import random
import csv


class Sistema(simpy.Environment):
    """
    Clase para el modelado del sistema logístico
    Subclase de simpy.Environment
    """

    def __init__(self):
        """
        Definicion del sistema de forma predeterminada en su estado original
        """
        super(Sistema, self).__init__()

        self.datos = []

        self.productos = ["Harina de Soya - Hi Pro/Pellet de Soya", "Harina de Soya - Full Fat", "Torta de Soya",
                          "Torta de Girasol", "Aceite de Soya", "Grano de Soya",
                          "Azucar", "Fierro", "Contenedor 20", "Contenedor 40"]

        self.colas_espera_transbordo = {
            "Harina de Soya - Full Fat":
                {"Descarga": [], "Carga": []},
            "Torta de Soya":
                {"Descarga": [], "Carga": []},
            "Torta de Girasol":
                {"Descarga": [], "Carga": []},
            "Grano de Soya":
                {"Descarga": [], "Carga": []},
            "Azucar":
                {"Descarga": [], "Carga": []},
            "Fierro":
                {"Descarga": [], "Carga": []}
        }

        self.camiones_en_sistema = []

        # Definición de Recursos
        niv_tolva = {
            "Harina de Soya - Hi Pro/Pellet de Soya": 0
        }
        niv_almacen_1 = {
            "Harina de Soya - Hi Pro/Pellet de Soya": 500
        }
        niv_almacen_2 = {
            "Harina de Soya - Full Fat": 100,
            "Torta de Soya": 100,
            "Torta de Girasol": 100,
            "Azucar": 100
        }
        niv_almacen_ext = {
            "Grano de Soya": 0
        }
        niv_tanque_1 = {
            "Aceite de Soya": 0
        }
        niv_tanque_2 = {
            "Aceite de Soya": 0
        }
        niv_patio_cont = {
            "Contenedor 20": 0,
            "Contenedor 40": 0
        }

        horarios = {
            "horario 1": {"L-V": {"Ingreso": 7.5, "I. Descanso": 13.0, "F. Descanso": 14.0, "Salida": 16.5},
                          "SAB": {"Ingreso": 8.5, "Salida": 12.5}},
            "horario 2": {"L-V": {"Ingreso": 8.0, "I. Descanso": 12.0, "F. Descanso": 13.0, "Salida": 17.0},
                          "SAB": {"Ingreso": 8.5, "Salida": 12.5}}
        }

        self.recursos = {
            "Ventanilla Recepcion":
                Recurso(self, "Ventanilla Recepcion",
                        horarios["horario 1"],
                        capacity=1),
            "Ventanilla Despacho":
                Recurso(self, "Ventanilla Despacho",
                        horarios["horario 1"],
                        capacity=1),
            "Balanza 2":
                Recurso(self, "Balanza 2",
                        horarios["horario 1"],
                        capacity=1),
            "Estacion Volcadora":
                Recurso(self, "Estación Volacdora",
                        horarios["horario 2"],
                        capacity=1),
            "Estacion Tolva":
                Recurso(self, "Estación Tolva",
                        horarios["horario 2"],
                        capacity=1),
            "Pala Mecanica":
                Recurso(self, "Pala Mecánica",
                        horarios["horario 2"],
                        capacity=1),
            "Cuadrilla de Estibaje":
                Recurso(self, "Cuadrillas de Estibaje",
                        horarios["horario 2"],
                        capacity=3),
            "Cabina de Recepcion - T1":
                Recurso(self, "Cabina de Recepción - T1",
                        horarios["horario 2"],
                        capacity=1),
            "Cabina de Despacho - T1":
                Recurso(self, "Cabina de Despacho - T1",
                        horarios["horario 2"],
                        capacity=1),
            "Cabina de Recepcion - T2":
                Recurso(self, "Cabina de Recepción - T2",
                        horarios["horario 2"],
                        capacity=1),
            "Cabina de Despacho - T2":
                Recurso(self, "Cabina de Despacho - T2",
                        horarios["horario 2"],
                        capacity=1),
            "Grua":
                Recurso(self, "Grua",
                        horarios["horario 2"],
                        capacity=1),
            "Tolva":
                MedioDeAlmacenamiento(self, "Tolva", 2, niv_tolva, 400),
            "Almacen 1":
                MedioDeAlmacenamiento(self, "Almacen 1", 3, niv_almacen_1, 2500),
            "Almacen 2":
                MedioDeAlmacenamiento(self, "Almacen 2", 1, niv_almacen_2, 1500),
            "Almacen Ext":
                MedioDeAlmacenamiento(self, "Almacen Ext", 3, niv_almacen_ext, 1500),
            "Tanque 1":
                MedioDeAlmacenamiento(self, "Tanque 1", 2, niv_tanque_1, 400),
            "Tanque 2":
                MedioDeAlmacenamiento(self, "Tanque 2", 2, niv_tanque_2, 500),
            "Patio de Contenedores":
                MedioDeAlmacenamiento(self, "Patio de Contenedores", 1, niv_patio_cont, 2500)}

        self.medios_de_almacenamiento = {
            "Tolva":
                MedioDeAlmacenamiento(self, "Tolva", 2, niv_tolva, 400),
            "Almacen 1":
                MedioDeAlmacenamiento(self, "Almacen 1", 3, niv_almacen_1, 2500),
            "Almacen 2":
                MedioDeAlmacenamiento(self, "Almacen 2", 1, niv_almacen_2, 1500),
            "Almacen Ext":
                MedioDeAlmacenamiento(self, "Almacen Ext", 3, niv_almacen_ext, 1500),
            "Tanque 1":
                MedioDeAlmacenamiento(self, "Tanque 1", 2, niv_tanque_1, 400),
            "Tanque 2":
                MedioDeAlmacenamiento(self, "Tanque 2", 2, niv_tanque_2, 500),
            "Patio de Contenedores":
                MedioDeAlmacenamiento(self, "Patio de Contenedores", 1, niv_patio_cont, 2500)
        }

        # TODO borrar
        self.almacenes_por_producto = {
            "Harina de Soya - Hi Pro/Pellet de Soya":
                [self.recursos["Almacen 1"]],
            "Harina de Soya - Full Fat":
                [self.recursos["Almacen 2"]],
            "Torta de Soya":
                [self.recursos["Almacen 2"]],
            "Torta de Girasol":
                [self.recursos["Almacen 2"]],
            "Aceite de Soya":
                [self.recursos["Tanque 1"], self.recursos["Tanque 2"]],
            "Grano de Soya":
                [self.recursos["Almacen Ext"]],
            "Azucar":
                [self.recursos["Almacen 2"]],
            "Fierro":
                [],
            "Contenedor 20":
                [self.recursos["Patio de Contenedores"]],
            "Contenedor 40":
                [self.recursos["Patio de Contenedores"]]
        }

        # Definicion de Operaciones # TODO Ingresar datos reales
        operaciones_manipuleo = {
            "Descarga con volcadora":
                OperacionManipuleo("Descarga con volcadora",
                                   self.recursos["Estacion Volcadora"],
                                   "uniforme", [14, 20],
                                   self.datos),
            "Descarga a pulso - Sacos":
                OperacionManipuleo("Descarga a pulso - Sacos",
                                   self.recursos["Cuadrilla de Estibaje"],
                                   "uniforme", [30, 45],
                                   self.datos),
            "Descarga a pulso - Granos":
                OperacionManipuleo("Descarga a pulso - Granos",
                                   self.recursos["Cuadrilla de Estibaje"],
                                   "uniforme", [40, 60],
                                   self.datos),
            "Descarga con bombas electricas - T1":
                OperacionManipuleo("Descarga con bombas electricas",
                                   self.recursos["Cabina de Recepcion - T1"],
                                   "uniforme", [40, 50],
                                   self.datos),
            "Descarga con bombas electricas - T2":
                OperacionManipuleo("Descarga con bombas electricas",
                                   self.recursos["Cabina de Recepcion - T2"],
                                   "uniforme", [40, 50],
                                   self.datos),
            "Descarga con grua":
                OperacionManipuleo("Descarga con grua",
                                   self.recursos["Grua"],
                                   "uniforme", [15, 20],
                                   self.datos),
            "Carga con tolva":
                OperacionManipuleo("Carga con tolva",
                                   self.recursos["Estacion Tolva"],
                                   "uniforme", [14, 20],
                                   self.datos),
            "Carga con pala mecanica":
                OperacionManipuleo("Carga con pala mecanica",
                                   self.recursos["Pala Mecanica"],
                                   "uniforme", [18, 30],
                                   self.datos),
            "Carga a pulso - Sacos":
                OperacionManipuleo("Carga a pulso - Sacos",
                                   self.recursos["Cuadrilla de Estibaje"],
                                   "uniforme", [45, 70],
                                   self.datos),
            "Carga a pulso - Granos":
                OperacionManipuleo("Carga a pulso - Granos",
                                   self.recursos["Cuadrilla de Estibaje"],
                                   "uniforme", [60, 90],
                                   self.datos),
            "Carga con bombas electricas - T1":
                OperacionManipuleo("Carga con bombas electricas",
                                   self.recursos["Cabina de Despacho - T1"],
                                   "uniforme", [45, 60],
                                   self.datos),
            "Carga con bombas electricas - T2":
                OperacionManipuleo("Carga con bombas electricas",
                                   self.recursos["Cabina de Despacho - T2"],
                                   "uniforme", [45, 60],
                                   self.datos),
            "Carga con grua":
                OperacionManipuleo("Carga con grua",
                                   self.recursos["Grua"],
                                   "uniforme", [15, 22],
                                   self.datos),
            "Transbordo en sistema mecanizado (D)":
                OperacionManipuleo("Transbordo en sistema mecanizado",
                                   self.recursos["Estacion Volcadora"],
                                   "uniforme", [14, 25],
                                   self.datos),
            "Transbordo en sistema mecanizado (C)":
                OperacionManipuleo("Transbordo en sistema mecanizado",
                                   self.recursos["Estacion Tolva"],
                                   "uniforme", [14, 25],
                                   self.datos),
            "Transbordo a pulso - Sacos":
                OperacionManipuleo("Transbordo a pulso - Sacos",
                                   self.recursos["Cuadrilla de Estibaje"],
                                   "uniforme", [40, 60],
                                   self.datos),
            "Transbordo a pulso - Granos":
                OperacionManipuleo("Transbordo a pulso - Sacos",
                                   self.recursos["Cuadrilla de Estibaje"],
                                   "uniforme", [45, 65],
                                   self.datos),
            "Transbordo con grua":
                OperacionManipuleo("Transbordo con grua",
                                   self.recursos["Grua"],
                                   "uniforme", [15, 20],
                                   self.datos)}

        operaciones_complementarias = {
            "Atencion recepcion 1":
                Operacion("Atencion recepcion 1",
                          self.recursos["Ventanilla Recepcion"],
                          "uniforme", [2, 10],
                          self.datos),
            "Atencion despacho 1":
                Operacion("Atencion despacho 1",
                          self.recursos["Ventanilla Despacho"],
                          "uniforme", [2, 10],
                          self.datos),
            "Primer pesaje":
                Operacion("Primer pesaje",
                          self.recursos["Balanza 2"],
                          "uniforme", [3, 6],
                          self.datos),
            "Segundo pesaje":
                Operacion("Segundo pesaje",
                          self.recursos["Balanza 2"],
                          "uniforme", [3, 6],
                          self.datos),
            "Atencion recepcion 2":
                Operacion("Atencion recepcion 2",
                          self.recursos["Ventanilla Recepcion"],
                          "uniforme", [4, 8],
                          self.datos),
            "Atencion despacho 2":
                Operacion("Atencion despacho 2",
                          self.recursos["Ventanilla Despacho"],
                          "uniforme", [2, 5],
                          self.datos)}

        # Diccionario general de operaciones
        self.operaciones = {
            "Operaciones manipuleo":
                operaciones_manipuleo,
            "Operaciones complementarias":
                operaciones_complementarias}

    def generar_camiones(self):
        """
        Genera camiones en el entorno de simulación
        """

        camiones = {
            "Harina de Soya - Hi Pro/Pellet de Soya":
                {"Descarga": [], "Carga": []},
            "Harina de Soya - Full Fat":
                {"Descarga": [], "Carga": []},
            "Torta de Soya":
                {"Descarga": [], "Carga": []},
            "Torta de Girasol":
                {"Descarga": [], "Carga": []},
            "Aceite de Soya":
                {"Descarga": [], "Carga": []},
            "Grano de Soya":
                {"Descarga": [], "Carga": []},
            "Azucar":
                {"Descarga": [], "Carga": []},
            "Fierro":
                {"Descarga": [], "Carga": []},
            "Contenedor 20":
                {"Descarga": [], "Carga": []},
            "Contenedor 40":
                {"Descarga": [], "Carga": []}}

        i = 0

        while True:
            camion = Camion(self, i + 1)
            camiones[camion.carga][camion.tipo].append(camion)

            yield self.process(camion.llega_a_instalacion(self))
            self.process(self.atender_camion(camion))

            i += 1

    def atender_camion(self, camion):
        """
        Simula el proceso de atención de camiones dividiendolo en 3 etapas:
        - Operaciones complementarias preliminares
        - Operaciones de manipuleo
        - Operaciones complementarias posterores

        :type camion: Camion
        """

        # Operaciones Complementarias Ingreso
        yield self.process(
            self.atencion_ingreso(camion))

        # Manipuleo
        yield self.process(
            self.atencion_manipuleo(camion))

        # Operaciones Complementarias Salida
        yield self.process(
            self.atencion_salida(camion))

    def atencion_manipuleo(self, camion):
        """
        Simula la atención de operaciones de manipuleo divididas en:
        - Atención granos
        - Atención sacos
        - Atención líquidos
        - Atención contenedores
        - Atención carga general

        :type camion: Camion
        """

        # Atención granos
        if camion.carga in ["Harina de Soya - Hi Pro/Pellet de Soya", "Grano de Soya"]:
            yield self.process(self.manipular_granos(camion))

        # Atención sacos
        elif camion.carga in ["Harina de Soya - Full Fat", "Torta de Soya", "Torta de Girasol", "Azucar"]:
            yield self.process(self.manipular_sacos(camion))

        # Atención líquidos
        elif camion.carga in ["Aceite de Soya"]:
            yield self.process(self.manipular_liquidos(camion))

        # Atención contenedores
        elif camion.carga in ["Contenedor 20", "Contenedor 40"]:
            yield self.process(self.manipular_contedenor(camion))

        # Atención carga general
        elif camion.carga in ["Fierro"]:
            yield self.process(self.manipular_carga_general(camion))

    def manipular_granos(self, camion):
        """
        Simula el manipuleo de granos

        :type camion: Camion
        """
        operaciones = self.operaciones["Operaciones manipuleo"]

        # Manipuleo de camion por cargar
        if camion.tipo == "Carga":

            # Manipuleo de carga a granel seca en almacenes propios
            if camion.carga in ["Harina de Soya - Hi Pro/Pellet de Soya"]:

                # Se carga a partir de un transbordo en sistema mecanizado
                transbordo = operaciones["Transbordo en sistema mecanizado (C)"]
                ejecucion_transbordo = yield self.process(
                    transbordo.ejecutar(self, camion, 0, self.recursos["Tolva"]))

                # Si no se ejecuta el transbordo se carga con pala mecánica
                if ejecucion_transbordo in ["No ejecutada por recurso", "No ejecutada por producto"]:

                    carga = operaciones["Carga con pala mecanica"]
                    ejecucion_carga = yield self.process(
                        carga.ejecutar(self, camion, 300, self.recursos["Almacen 1"]))

                    # Si no se ejecuta la carga espera camion para realizar transbordo o interrumpe la espera de otro
                    if ejecucion_carga in ["No ejecutada por recurso", "No ejecutada por producto"]:

                        ejecucion_espera_o_interrumpe = yield self.process(
                            camion.espera_transbordo_o_interrumpe(self))

                        # Si el camion espera procede con un tranbordo o carga a pulso
                        if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":

                            transbordo = operaciones["Transbordo a pulso - Granos"]
                            carga = operaciones["Carga a pulso - Granos"]

                            transborda_o_carga = yield self.process(self.transbordar_o_cargar_descargar(
                                camion, ejecucion_espera_o_interrumpe,
                                transbordo, 200,
                                carga, self.recursos["Almacen 1"], 200))

                            # Si no se ejecuta el transbordo o carga a pulso, se carga con tolva
                            if transborda_o_carga in ["No ejecutada por recurso", "No ejecutada por producto"]:
                                carga = operaciones["Carga con tolva"]
                                yield self.process(
                                    carga.ejecutar(self, camion, 200, self.recursos["Almacen 1"]))

            # Manipuleo de carga a granel seca en almacenes externos
            elif camion.carga in ["Grano de Soya"]:

                # Se carga con pala mecanica
                carga = operaciones["Carga con pala mecanica"]
                ejecucion_carga = yield self.process(
                    carga.ejecutar(self, camion, 600, self.recursos["Almacen Ext"]))

                # Si no se ejecuta la carga, espera camion para realizar transbordo o interrumpe la espera de otro
                if ejecucion_carga in ["No ejecutada por recurso", "No ejecutado por producto"]:

                    ejecucion_espera_o_interrumpe = yield self.process(
                        camion.espera_transbordo_o_interrumpe(self))

                    # Si el camion espera procede con un tranbordo o carga a pulso
                    if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                        transbordo = operaciones["Transbordo a pulso - Granos"]
                        carga = operaciones["Carga a pulso - Granos"]

                        yield self.process(self.transbordar_o_cargar_descargar(
                            camion, ejecucion_espera_o_interrumpe,
                            transbordo, 200,
                            carga, self.recursos["Almacen Ext"], 200))

        # Manipuleo de camion por descargar
        elif camion.tipo == "Descarga":

            # Manipuleo de carga a granel en almacenes propios
            if camion.carga in ["Harina de Soya - Hi Pro/Pellet de Soya"]:

                # Se descarga a partir de un transbordo en sistema mecanizado
                transbordo = operaciones["Transbordo en sistema mecanizado (D)"]
                ejecucion_transbordo = yield self.process(
                    transbordo.ejecutar(self, camion, 120, self.recursos["Tolva"]))

                # Si no se ejecuta el transbordo por disp. de recurso espera camion para realizar transbordo
                # a pulso o interrumpe la espera de otro
                if ejecucion_transbordo == "No ejecutada por recurso":

                    ejecucion_espera_o_interrumpe = yield self.process(
                        camion.espera_transbordo_o_interrumpe(self))

                    # Si el camion espera procede con un tranbordo o descarga a pulso
                    if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                        transbordo = operaciones["Transbordo a pulso - Granos"]
                        descarga = operaciones["Descarga a pulso - Granos"]

                        yield self.process(self.transbordar_o_cargar_descargar(
                            camion, ejecucion_espera_o_interrumpe,
                            transbordo, 200,
                            descarga, self.recursos["Almacen 1"], 200))

                # Si no se ejecuta el transbordo por nivel de producto se descarga en almacenes propios
                elif ejecucion_transbordo == "No ejecutada por producto":

                    descarga = operaciones["Descarga con volcadora"]
                    yield self.process(descarga.ejecutar(self, camion, 100, self.recursos["Almacen 1"]))

            # Manipuleo de carga a granel en almacenes externos
            elif camion.carga in ["Grano de Soya"]:

                # Espera camion para realizar transbordo o interrumpe la espera de otro
                ejecucion_espera_o_interrumpe = yield self.process(
                    camion.espera_transbordo_o_interrumpe(self))

                # Si el camion espera procede con un tranbordo o descarga a pulso
                if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                    transbordo = operaciones["Transbordo a pulso - Granos"]
                    descarga = operaciones["Descarga a pulso - Granos"]

                    yield self.process(self.transbordar_o_cargar_descargar(
                        camion, ejecucion_espera_o_interrumpe,
                        transbordo, 200,
                        descarga, self.recursos["Almacen Ext"], 200))

    def manipular_sacos(self, camion):
        """
        Simula el manipuleo de sacos

        :type camion: Camion
        """
        operaciones = self.operaciones["Operaciones manipuleo"]

        # Manipuleo de camion por cargar
        if camion.tipo == "Carga":

            # Espera camion para realizar transbordo o interrumpe la espera de otro
            ejecucion_espera_o_interrumpe = yield self.process(
                camion.espera_transbordo_o_interrumpe(self))

            # Si el camion espera procede con un tranbordo o carga a pulso
            if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                transbordo = operaciones["Transbordo a pulso - Sacos"]
                carga = operaciones["Carga a pulso - Sacos"]

                yield self.process(self.transbordar_o_cargar_descargar(
                    camion, ejecucion_espera_o_interrumpe,
                    transbordo, 200,
                    carga, self.recursos["Almacen 2"], 200))

        # Manipuleo de camion por descargar
        elif camion.tipo == "Descarga":

            # Espera camion para realizar transbordo o interrumpe la espera de otro
            ejecucion_espera_o_interrumpe = yield self.process(
                camion.espera_transbordo_o_interrumpe(self))

            # Si el camion espera procede con un tranbordo o descarga a pulso
            if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                transbordo = operaciones["Transbordo a pulso - Sacos"]
                descarga = operaciones["Descarga a pulso - Sacos"]

                yield self.process(self.transbordar_o_cargar_descargar(
                    camion, ejecucion_espera_o_interrumpe,
                    transbordo, 200,
                    descarga, self.recursos["Almacen 2"], 200))

    def manipular_liquidos(self, camion):  # TODO Mejorar implementacion
        """
        Simula el manipuleo de líquidos, permitiendo la elección de tanques a conveniencia

        :type camion: Camion
        """
        operaciones = self.operaciones["Operaciones manipuleo"]

        # Manipuleo de camiones por cargar
        if camion.tipo == "Carga":

            if len(self.recursos["Cabina de Despacho - T1"].cola) \
                    <= len(self.recursos["Cabina de Despacho - T2"].cola):

                if not camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 1"]) \
                        and camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 2"]):
                    print "T2"
                    carga = operaciones["Carga con bombas electricas - T2"]
                    yield self.process(carga.ejecutar(self, camion, 200, self.recursos["Tanque 2"]))
                else:
                    print "T1"
                    carga = operaciones["Carga con bombas electricas - T1"]
                    yield self.process(carga.ejecutar(self, camion, 200, self.recursos["Tanque 1"]))
            else:
                if not camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 2"]) \
                        and camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 1"]):
                    print "T1"
                    carga = operaciones["Carga con bombas electricas - T1"]
                    yield self.process(carga.ejecutar(self, camion, 200, self.recursos["Tanque 1"]))
                else:
                    print "T2"
                    carga = operaciones["Carga con bombas electricas - T2"]
                    yield self.process(carga.ejecutar(self, camion, 200, self.recursos["Tanque 2"]))

        # Manipuleo de camiones por descargar
        elif camion.tipo == "Descarga":

            if len(self.recursos["Cabina de Recepcion - T1"].cola) \
                    <= len(self.recursos["Cabina de Recepcion - T2"].cola):
                if not camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 1"]) \
                        and camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 2"]):
                    print "T2"
                    descarga = operaciones["Descarga con bombas electricas - T2"]
                    yield self.process(descarga.ejecutar(self, camion, 200, self.recursos["Tanque 2"]))
                else:
                    print "T1"
                    descarga = operaciones["Descarga con bombas electricas - T1"]
                    yield self.process(descarga.ejecutar(self, camion, 200, self.recursos["Tanque 1"]))
            else:
                if not camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 2"]) \
                        and camion.dispone_producto_espacio_medio_almacenamiento(self.recursos["Tanque 1"]):
                    print "T1"
                    descarga = operaciones["Descarga con bombas electricas - T1"]
                    yield self.process(descarga.ejecutar(self, camion, 200, self.recursos["Tanque 1"]))
                else:
                    print "T2"
                    descarga = operaciones["Descarga con bombas electricas - T2"]
                    yield self.process(descarga.ejecutar(self, camion, 200, self.recursos["Tanque 2"]))

    def manipular_contedenor(self, camion):
        """
        Simula el manipuleo de contenedores

        :param camion:
        """
        operaciones = self.operaciones["Operaciones manipuleo"]

        # Manipuleo de camiones por cargar
        if camion.tipo == "Carga":

            carga = operaciones["Carga con grua"]
            yield self.process(carga.ejecutar(self, camion, 300, self.recursos["Patio de Contenedores"]))

        # Manipuleo de camiones por descargar
        elif camion.tipo == "Descarga":

            descarga = operaciones["Descarga con grua"]
            yield self.process(descarga.ejecutar(self, camion, 300, self.recursos["Patio de Contenedores"]))

    def manipular_carga_general(self, camion):
        """
        Simula el manipuleo de carga general

        :type camion: Camion
        """
        operaciones = self.operaciones["Operaciones manipuleo"]

        # Manipuleo de camiones por cargar/descargar
        # Espera camion para realizar transbordo o interrumpe la espera de otro
        ejecucion_espera_o_interrumpe = yield self.process(
            camion.espera_transbordo_o_interrumpe(self))

        # Si el camion espera procede con un tranbordo
        if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
            transbordo = operaciones["Transbordo con grua"]

            yield self.process(self.transbordar_o_cargar_descargar(
                camion, ejecucion_espera_o_interrumpe,
                transbordo, 500))

    def transbordar_o_cargar_descargar(self, camion, ejecucion_espera_o_interrumpe,
                                       transbordo, tpaciencia_t,
                                       carga_o_descarga=None, recurso_cd=None, tpaciencia_cd=None):
        """
        Modelado de ejecucíón de carga/descarga finalizado el tiempo de espera
        o transbordo arribo/interrupción de un camion

        :param camion:
        :param ejecucion_espera_o_interrumpe:
        :param transbordo:
        :param tpaciencia_t:
        :param carga_o_descarga:
        :param recurso_cd:
        :param tpaciencia_cd:
        """
        # TODO analizar nueva ubicación en otra clase

        # Se concluyo la espera, se procede con la carga o descarga
        if ejecucion_espera_o_interrumpe["Resultado"] == "Termino espera":

            yield self.process(
                carga_o_descarga.ejecutar(self, camion, tpaciencia_cd, recurso_cd))

        # Se interrumpio la espera, se procede con el transbordo
        elif ejecucion_espera_o_interrumpe["Resultado"] == "Espera interrumpida":
            recurso_t = ejecucion_espera_o_interrumpe["Interrupcion"].trailer
            yield self.process(
                transbordo.ejecutar(self, camion, tpaciencia_t, recurso_t))

    def atencion_ingreso(self, camion):
        """
        Simula el proceso de ingreso de camiones previo al manipuleo

        :type camion: Camion
        """

        operaciones = self.operaciones["Operaciones complementarias"]

        if camion.tipo == "Descarga":
            yield self.process(operaciones["Atencion recepcion 1"]
                               .ejecutar(self, camion))
        else:
            yield self.process(operaciones["Atencion despacho 1"]
                               .ejecutar(self, camion))

        if camion.carga not in ["Contenedor 20", "Contenedor 40"]:
            yield self.process(operaciones["Primer pesaje"]
                               .ejecutar(self, camion))
        self.exit(camion.nombre)

    def atencion_salida(self, camion):
        """
        Simula el proceso de salida de camiones posterior al manipuleo

        :type camion: Camion
        """
        operaciones = self.operaciones["Operaciones complementarias"]

        if camion.carga not in ["Contenedor 20", "Contenedor 40"]:
            yield self.process(operaciones["Segundo pesaje"]
                               .ejecutar(self, camion))

        if camion.tipo == "Descarga":
            yield self.process(operaciones["Atencion recepcion 2"]
                               .ejecutar(self, camion))
        else:
            yield self.process(operaciones["Atencion despacho 2"]
                               .ejecutar(self, camion))

    def guardar_datos(self, archivo):
        """
        Guarda datos en un archivo .csv

        :type archivo: str
        """
        with open(archivo, "wb") as csv_file:
            writer = csv.writer(csv_file, delimiter=';')
            writer.writerow(
                ["Camion", "Carga", "Tipo", "Peso Final", "Operacion",
                 "Arribo", "Espera M. O/D", "Espera R", "Espera P.", "Espera T.", "Inicio", "Fin",
                 "Medio de Almacenamiento", "Nivel"])
            for linea in self.datos:
                writer.writerow(linea)

    def simular(self):
        """
        Ejecuta la simulación del sistema.
        """

        print('Simulación de Operaciones Logísticas en ALPASUR S.A. - KEMFA S.A.')

        # Tiempo de simulación
        tsim = 24 * 60

        # Semilla de aleatoriedad
        random.seed(55)

        self.process(self.generar_camiones())
        self.run(until=tsim)

        archivo = "C:\Users\AYAR\Documentos\Ingenieria Industrial" + \
                  "\Documentos Tesis\Avances\Modelo de Simulacion\datos.csv"

        self.guardar_datos(archivo)
        os.startfile(archivo)


class Camion(object):
    """Clase para el modelado de camiones presentes en el sistema"""

    def __init__(self, sistema, nombre):
        """
        Define las propiedades principales de la clase Camion

        :type sistema: Sistema
        :type nombre: int
        """
        productos = sistema.productos

        self.nombre = nombre
        # TODO modificar con datos reales
        self.carga = random.choice(productos)

        if random.random() <= 0.5:
            self.tipo = "Descarga"
            self.peso = 28  # TODO analizar eliminación
        else:
            self.peso = 0
            self.tipo = "Carga"

        niveles = {self.carga: self.peso}

        self.trailer = MedioDeAlmacenamiento(sistema, str(self.nombre), 1, niveles, 28, self.peso)

        self.manipulado = sistema.event()
        self.transbordo = "No"

    def __repr__(self):
        """
        Define la forma de representación de entidades de la clase Camion
        """

        cod = ""

        if self.carga == "Harina de Soya - Hi Pro/Pellet de Soya":
            cod = "HP"
        elif self.carga == "Harina de Soya - Full Fat":
            cod = "FF"
        elif self.carga == "Torta de Soya":
            cod = "TS"
        elif self.carga == "Torta de Girasol":
            cod = "TS"
        elif self.carga == "Aceite de Soya":
            cod = "AS"
        elif self.carga == "Grano de Soya":
            cod = "GS"
        elif self.carga == "Azucar":
            cod = "AZ"
        elif self.carga == "Fierro":
            cod = "FI"
        elif self.carga == "Contenedor 20":
            cod = "C2"
        elif self.carga == "Contenedor 40":
            cod = "C4"
        else:
            print "ERROR CARGA DESCONOCIDA: " + self.carga

        return str(self.nombre) + self.tipo[0] + cod

    @staticmethod
    def llega_a_instalacion(sistema):
        """
        Genera la llegada del camion

        :type sistema: Sistema
        """
        tell = random.uniform(1, 2)  # TODO Modificar con información real

        yield sistema.timeout(int(round(tell, 0)))

    def espera_transbordo(self, sistema, tespera):
        """
        Simula la espera por un camion para realizar transbordo
        Finalizada la espera se procede con una operacion de carga o descarga
        Sin embargo, si otro camion llega se interrumpe la espera y se procede con un transbordo

        :type sistema: Sistema
        :type tespera: int
        """
        # Inicia espera de camion para realizar transbordo
        try:

            print "%s inicia espera Transbordo - Hora: %d" % (self, sistema.now)
            yield sistema.timeout(tespera)

            # Consluida la espera verifica si hay producto o espacio disponible en almacenes.
            prod_o_esp_disp = self.dispone_producto_espacio_medios_almacenamiento(sistema.recursos)

            # Si producto o esapacio, termina su espera para realizar una carga o descarga
            if prod_o_esp_disp:

                print str(self) + " termino espera - Hora: " + str(sistema.now)

            # De lo contrario continua esperando mientras no haya producto o espacio en almacenes
            else:

                print str(self) + " continua espera Producto/Espacio no disponible - Hora:" + str(sistema.now)
                while not prod_o_esp_disp:
                    yield sistema.timeout(1)
                    prod_o_esp_disp = self.dispone_producto_espacio_medios_almacenamiento(sistema.recursos)

            sistema.exit({"Resultado": "Termino espera", "Interrupcion": None})

        # En caso que un camion llega, interrumpe la espera para proceder con el transbordo
        except simpy.Interrupt as interrupcion:

            print str(self) + " espera interrumpida por " + str(interrupcion.cause) + " - Hora: " + str(
                sistema.now)
            self.transbordo = "Si"
            sistema.exit({"Resultado": "Espera interrumpida", "Interrupcion": interrupcion.cause})

    def interrumpe_espera_transbordo(self, proceso):
        """
        Interrumpe la espera de otro camion para realizar un transbordo.
        Al interrumpir, el camion pasa a comportarse como medio de origen o destino de carga

        :type proceso: simpy.events.Process
        """
        proceso.interrupt(self)

    def espera_transbordo_o_interrumpe(self, sistema):  # TODO Cambiar de nombre
        """
        Permite que un camion espere o interrumpa la espera de otro para realizar un transbordo

        :type sistema: Sistema
        :type self: Camion
        """

        if self.tipo == "Carga":
            tipo_camion_en_esp = "Descarga"
        else:
            tipo_camion_en_esp = "Carga"

        # Si hay un camion esperando con el que se puede realizar un transbordo, se interrumpe su espera
        if len(sistema.colas_espera_transbordo[self.carga][tipo_camion_en_esp]) != 0:

            print str(self) + " Interrumpe espera  - Hora: " + str(sistema.now)

            camion_en_espera = sistema.colas_espera_transbordo[self.carga][tipo_camion_en_esp][0][0]
            espera_en_proceso = sistema.colas_espera_transbordo[self.carga][tipo_camion_en_esp][0][1]

            self.interrumpe_espera_transbordo(espera_en_proceso)

            sistema.colas_espera_transbordo[self.carga][tipo_camion_en_esp].pop(0)  # TODO revisar
            camion_interrumpido = camion_en_espera

            yield camion_interrumpido.manipulado

            sistema.exit({"Resultado": "Interrumpio espera", "Interrupcion": None})

        # Si no hay camiones esperando entonces el camion espera
        else:

            if self.carga == "Fierro":
                tespera = float("Inf")  # TODO permitir una espera infinita
            else:
                tespera = 100

            espera_transbordo = sistema.process(self.espera_transbordo(sistema, tespera))
            sistema.colas_espera_transbordo[self.carga][self.tipo].append([self, espera_transbordo])

            resultado_espera = yield espera_transbordo

            # Si el camion concluyo la espera, sale de la cola
            if resultado_espera["Resultado"] == "Termino espera":
                sistema.colas_espera_transbordo[self.carga][self.tipo].pop(0)  # TODO revisar

            sistema.exit(resultado_espera)

    def espera_operacion_manipuleo(self, sistema, operacion, medio_de_almacenamiento, tpaciencia_t):
        """
        Simula la espera por disponibilidad de:
        - Espacios de atencion en medios de almacenamiento
        - Recursos de ejecución
        - Producto o espacio en medios de origen/destino

        :type sistema: Sistema
        :type operacion: OperacionManipuleo
        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        :type tpaciencia_t: int
        """
        espera_p_e = 0
        espera_r_a = 0
        espera_m_a = 0
        espera_t = 0

        while espera_t < tpaciencia_t:

            if self.entre_primeros_cola_medio_de_almacenamiento(medio_de_almacenamiento):

                if self.entre_primeros_cola_recurso(operacion.recurso):

                    if self.dispone_producto_espacio_medio_almacenamiento(medio_de_almacenamiento):
                        break
                    else:
                        self.intenta_adelantar_camion_manipuleo(sistema, operacion, medio_de_almacenamiento)
                        espera_p_e += 1
                else:
                    self.intenta_adelantar_camion_manipuleo(sistema, operacion, medio_de_almacenamiento)

                    if self.dispone_producto_espacio_medios_almacenamiento(sistema.recursos):
                        espera_r_a += 1
                    else:
                        espera_r_a += 1
                        espera_p_e += 1
            else:

                if self.entre_primeros_cola_recurso(operacion.recurso):
                    self.intenta_adelantar_camion_manipuleo(sistema, operacion, medio_de_almacenamiento)

                    if self.dispone_producto_espacio_medios_almacenamiento(sistema.recursos):
                        espera_m_a += 1
                    else:
                        espera_m_a += 1
                        espera_p_e += 1
                else:

                    if self.dispone_producto_espacio_medios_almacenamiento(sistema.recursos):
                        espera_r_a += 1
                        espera_m_a += 1
                    else:
                        espera_r_a += 1
                        espera_m_a += 1
                        espera_p_e += 1

            espera_t += 1
            yield sistema.timeout(1)

        if self.dispone_producto_espacio_medio_almacenamiento(medio_de_almacenamiento) and espera_t <= tpaciencia_t \
                and self.entre_primeros_cola_recurso(operacion.recurso) \
                and self.entre_primeros_cola_medio_de_almacenamiento(medio_de_almacenamiento):

            if sistema.now < operacion.recurso.horario["L-V"]["Ingreso"] * 60:
                yield sistema.timeout(operacion.recurso.horario["L-V"]["Ingreso"] * 60 - sistema.now)
            elif operacion.recurso.horario["L-V"]["I. Descanso"] * 60 \
                    <= sistema.now <= operacion.recurso.horario["L-V"]["F. Descanso"] * 60:
                yield sistema.timeout(operacion.recurso.horario["L-V"]["F. Descanso"] * 60 - sistema.now)
            elif sistema.now >= operacion.recurso.horario["L-V"]["Salida"] * 60:
                print str(self) + " llego tarde, sale del sistema sin atención"
                yield sistema.timeout(24 * 60 - sistema.now)

            sistema.exit(["Inicia", espera_r_a, espera_p_e, espera_m_a, espera_t])

        else:

            sistema.exit(["No inicia", espera_r_a, espera_p_e, espera_m_a, espera_t])

    def espera_operacion(self, sistema, operacion):

        espera = 0
        while True:
            if self.entre_primeros_cola_recurso(operacion.recurso):

                if self.manipulado.triggered or operacion.recurso.nombre == "Balanza 2":
                    break

                elif self.dispone_producto_espacio_sistema(sistema):
                    break

                else:
                    self.intenta_adelantar_camion_operacion(sistema, operacion)
                    pass
            espera += 1
            yield sistema.timeout(1)

        if sistema.now < operacion.recurso.horario["L-V"]["Ingreso"] * 60:
            yield sistema.timeout(operacion.recurso.horario["L-V"]["Ingreso"] * 60 - sistema.now)
        elif operacion.recurso.horario["L-V"]["I. Descanso"] * 60 \
                <= sistema.now < operacion.recurso.horario["L-V"]["F. Descanso"] * 60:
            yield sistema.timeout(operacion.recurso.horario["L-V"]["F. Descanso"] * 60 - sistema.now)
        elif sistema.now >= operacion.recurso.horario["L-V"]["Salida"] * 60:
            print str(self) + " llego tarde, sale del sistema sin atención"
            yield sistema.timeout(24 * 60 - sistema.now)

    def intenta_adelantar_camion_operacion(self, sistema, operacion):

        if any(c.dispone_producto_espacio_sistema(sistema) or c.manipulado.triggered
               for c in operacion.recurso.cola_detras_de_camion(self)):
            camion_adelantado = [c for c in operacion.recurso.cola_detras_de_camion(self)
                                 if c.dispone_producto_espacio_sistema(sistema) or c.manipulado.triggered][0]

            operacion.recurso.cola.remove(camion_adelantado)
            operacion.recurso.cola = \
                operacion.recurso.cola[0:operacion.recurso.cola.index(self)] \
                + [camion_adelantado] + operacion.recurso.cola[operacion.recurso.cola.index(self):]

            print str(camion_adelantado) + " adelantado bajo criterio de " + str(self) + " " + str(sistema.now)
            print "\t" + str(operacion.recurso.nombre) + ": " \
                  + str(operacion.recurso.cola) + " Hora: " + str(sistema.now)

    def solicita_adelanto(self, entorno, operacion, medio_de_almacenamiento):
        """
        Permite la solicitud de adelanto cuando un camion arriba a una operacion

        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        :type operacion: Operacion
        :type entorno: Sistema
        """

        primeros_cola_r_a = operacion.recurso.cola[0:operacion.recurso.capacity]
        primeros_cola_m_a = medio_de_almacenamiento.cola[0:medio_de_almacenamiento.espacios_de_atencion]

        primeros_cola_r_a_disponen_p_e = \
            all(camion.dispone_producto_espacio_medios_almacenamiento(entorno.recursos)
                for camion in primeros_cola_r_a)

        primeros_cola_m_a_disponen_p_e = \
            all(camion.dispone_producto_espacio_medios_almacenamiento(entorno.recursos)
                for camion in primeros_cola_m_a)

        primeros_cola_r_a_entre_primeros_colas_m_a = \
            all(camion.entre_primeros_colas_medios_almacenamiento(entorno.recursos)
                for camion in primeros_cola_r_a)

        if operacion.nombre == "Transbordo en sistema mecanizado":
            pass

        elif self.dispone_producto_espacio_medio_almacenamiento(medio_de_almacenamiento):

            if self.entre_primeros_cola_medio_de_almacenamiento(medio_de_almacenamiento) \
                    and (not primeros_cola_r_a_disponen_p_e or not primeros_cola_r_a_entre_primeros_colas_m_a):
                primeros_cola_r_a[operacion.recurso.count].adelanta_camion(
                    entorno, operacion, medio_de_almacenamiento, self, "Operacion")

            if self.entre_primeros_cola_recurso(operacion.recurso) and not primeros_cola_m_a_disponen_p_e:
                primeros_cola_m_a[medio_de_almacenamiento.espacios_en_uso].adelanta_camion(
                    entorno, operacion, medio_de_almacenamiento, self, "Almacen")

    def adelanta_camion(self, entorno, operacion, medio_de_origen_o_destino, camion, tipo):
        """
        Permite que el camion adelante a otro que este por detras en la cola del medio de almacenamiento
        y/o del recurso de atencion

        :type tipo: str
        :type medio_de_origen_o_destino: MedioDeAlmacenamiento
        :type entorno: Sistema
        :type operacion: Operacion
        :type camion: Camion
        """
        # TODO mejorar implementacion

        if tipo == "Operacion":

            operacion.recurso.cola.remove(camion)
            operacion.recurso.cola = \
                operacion.recurso.cola[0:operacion.recurso.cola.index(self)] \
                + [camion] + operacion.recurso.cola[operacion.recurso.cola.index(self):]

            print str(camion) + " adelantado bajo criterio de " + str(self) + " " + str(entorno.now)
            print "\tEn sistema: " + str(operacion.recurso.cola) + " Hora: " + str(entorno.now)

            if self in medio_de_origen_o_destino.cola and camion in medio_de_origen_o_destino.cola:
                medio_de_origen_o_destino.cola.remove(camion)
                medio_de_origen_o_destino.cola = \
                    medio_de_origen_o_destino.cola[0:medio_de_origen_o_destino.cola.index(self)] + [camion] \
                    + medio_de_origen_o_destino.cola[medio_de_origen_o_destino.cola.index(self):]

                print "NO BORRAR SI AUN SE LEE"
                print "\t" + medio_de_origen_o_destino.nombre + ":" \
                      + str(medio_de_origen_o_destino.cola) + " Hora: " + str(entorno.now)

        elif tipo == "Almacen":

            medio_de_origen_o_destino.cola.remove(camion)
            medio_de_origen_o_destino.cola = \
                medio_de_origen_o_destino.cola[0:medio_de_origen_o_destino.cola.index(self)] \
                + [camion] + medio_de_origen_o_destino.cola[medio_de_origen_o_destino.cola.index(self):]

            print str(camion) + " adelantado bajo criterio de " + str(self) + " " + str(entorno.now)
            print "\t" + medio_de_origen_o_destino.nombre + ":" \
                  + str(medio_de_origen_o_destino.cola) + " Hora: " + str(entorno.now)

    def intenta_adelantar_camion_manipuleo(self, sistema, operacion, medio_de_almacenamiento):
        """
        Simula el intento de adelantar camiones por detras siempre que sea factible y conveniente

        :type sistema: Sistema
        :type operacion: Operacion
        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        """

        entre_primeros_cola_m_a = \
            self.entre_primeros_cola_medio_de_almacenamiento(medio_de_almacenamiento)

        entre_primeros_cola_r_a = \
            self.entre_primeros_cola_recurso(operacion.recurso)

        # El camion verifica si puede adelantar algun camion por detras en la cola del
        # medio de almacenamiento que disponga producto/espacio y este por detras en la
        # cola del recurso de atención
        if entre_primeros_cola_m_a and entre_primeros_cola_r_a and \
                any(c.dispone_producto_espacio_medios_almacenamiento(sistema.recursos) and
                    c.atras_de_camion_en_cola_recurso(self, operacion.recurso)
                    for c in medio_de_almacenamiento.cola_detras_de_camion(self)):
            c_adelantado = [ca for ca in medio_de_almacenamiento.cola_detras_de_camion(self)
                            if ca.dispone_producto_espacio_medios_almacenamiento(sistema.recursos) and
                            ca.atras_de_camion_en_cola_recurso(self, operacion.recurso)][0]

            self.adelanta_camion(sistema, operacion, medio_de_almacenamiento, c_adelantado, "Almacen")

        # El camion verifica si puede adelantar algun camion por detras en la cola del
        # medio de almacenamiento que disponga producto/espacio y esta entre los primeros
        # en alguna cola de recursos de atención
        if entre_primeros_cola_m_a and \
                any(c.dispone_producto_espacio_medios_almacenamiento(sistema.recursos) and
                    c.entre_primeros_colas_recursos(sistema.recursos)
                    for c in medio_de_almacenamiento.cola_detras_de_camion(self)):
            c_adelantado = [ca for ca in medio_de_almacenamiento.cola_detras_de_camion(self)
                            if ca.dispone_producto_espacio_medios_almacenamiento(sistema.recursos) and
                            ca.entre_primeros_colas_recursos(sistema.recursos)][0]

            self.adelanta_camion(sistema, operacion, medio_de_almacenamiento, c_adelantado, "Almacen")

        # El camion verifica si puede adelantar algun camion por detras en la cola del
        # recurso de atención que disponga producto/espacio y este entre los primeros
        # en alguna cola de medios de almacenamiento
        if entre_primeros_cola_r_a and \
                any(c.dispone_producto_espacio_medios_almacenamiento(sistema.recursos) and
                    c.entre_primeros_colas_medios_almacenamiento(sistema.recursos)
                    for c in operacion.recurso.cola_detras_de_camion(self)):
            c_adelantado = [ca for ca in operacion.recurso.cola_detras_de_camion(self)
                            if ca.dispone_producto_espacio_medios_almacenamiento(sistema.recursos) and
                            ca.entre_primeros_colas_medios_almacenamiento(sistema.recursos)][0]

            self.adelanta_camion(sistema, operacion, medio_de_almacenamiento, c_adelantado, "Operacion")

    def dispone_producto_espacio_sistema(self, sistema):

        camiones_comparables_a_cargar = 0
        camiones_comparables_a_descargar = 0

        if self.tipo == "Carga":
            camiones_comparables_a_cargar += \
                sum(1 for c in sistema.camiones_en_sistema
                    if c.carga == self.carga and c.tipo == "Carga" and not c.manipulado.triggered)
            camiones_comparables_a_descargar += \
                sum(1 for c in sistema.camiones_en_sistema
                    if c.carga == self.carga and c.tipo == "Descarga" and not c.manipulado.triggered)
        else:
            camiones_comparables_a_cargar += \
                sum(1 for c in sistema.camiones_en_sistema
                    if sistema.almacenes_por_producto[self.carga] == sistema.almacenes_por_producto[c.carga] and
                    c.tipo == "Carga" and not c.manipulado.triggered)
            camiones_comparables_a_descargar += \
                sum(1 for c in sistema.camiones_en_sistema
                    if sistema.almacenes_por_producto[self.carga] == sistema.almacenes_por_producto[c.carga] and
                    c.tipo == "Descarga" and not c.manipulado.triggered)

        producto_espacio_disponible = 0

        for almacen in sistema.almacenes_por_producto[self.carga]:

            if self.tipo == "Carga":
                producto_espacio_disponible += almacen.niveles[self.carga]
            else:
                producto_espacio_disponible += almacen.espacio

        if self.tipo == "Carga":
            if producto_espacio_disponible + 28 * (camiones_comparables_a_descargar - camiones_comparables_a_cargar) \
                    >= 28:
                return True
            else:
                return False
        else:
            if self.carga == "Fierro":
                return True
            elif producto_espacio_disponible + 28 * (camiones_comparables_a_cargar - camiones_comparables_a_descargar) \
                    >= 28:
                return True
            else:
                return False

    def dispone_producto_espacio_medios_almacenamiento(self, recursos):
        """
        Permite identificar si se dispone producto o espacio en algun medio de almacenamiento para atender al camion.

        :type recursos: dict
        """
        medios_de_almacenamiento = [recursos["Almacen 2"], recursos["Almacen 1"],
                                    recursos["Almacen Ext"], recursos["Patio de Contenedores"],
                                    recursos["Tanque 1"], recursos["Tanque 2"]]

        prod_o_esp_dip = False

        if self.transbordo == "Si" or (self.tipo == "Descarga" and self.carga == "Fierro"):
            prod_o_esp_dip = True
        elif any(self.carga in ma.niveles.keys() and self.dispone_producto_espacio_medio_almacenamiento(ma)
                 for ma in medios_de_almacenamiento):
            prod_o_esp_dip = True

        return prod_o_esp_dip

    def dispone_producto_espacio_medio_almacenamiento(self, medio_de_almacenamiento):
        """
        Permite identificar si se dispone producto o espacio en el medio de almacenamiento para atender al camion.

        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        """

        prod_o_esp_dip = False

        if self in medio_de_almacenamiento.cola:
            if self.tipo == "Carga":
                camiones_comparables = \
                    sum(1 for c in medio_de_almacenamiento.cola[0:medio_de_almacenamiento.cola.index(self)]
                        if c.carga == self.carga and c.tipo == self.tipo and c.transbordo == "No")
            else:
                camiones_comparables = \
                    sum(1 for c in medio_de_almacenamiento.cola[0:medio_de_almacenamiento.cola.index(self)]
                        if c.tipo == self.tipo and c.transbordo == "No")
        else:
            if self.tipo == "Carga":
                camiones_comparables = \
                    sum(1 for c in medio_de_almacenamiento.cola
                        if c.carga == self.carga and c.tipo == self.tipo and c.transbordo == "No")
            else:
                camiones_comparables = \
                    sum(1 for c in medio_de_almacenamiento.cola
                        if c.tipo == self.tipo and c.transbordo == "No")

        if self.tipo == "Carga" and medio_de_almacenamiento.niveles[self.carga] >= 28 * (1 + camiones_comparables):
            prod_o_esp_dip = True
        elif self.tipo == "Descarga" and medio_de_almacenamiento.espacio >= 28 * (1 + camiones_comparables):
            prod_o_esp_dip = True

        return prod_o_esp_dip

    def entre_primeros_colas_medios_almacenamiento(self, recursos):
        """
        Identifica si el camion esta entre los primeros camiones en alguna cola de medios de
        almacenamiento relevantes en el sistema

        :type recursos: dict
        """

        almacenes = [recursos["Almacen 2"], recursos["Almacen 1"],
                     recursos["Almacen Ext"], recursos["Patio de Contenedores"],
                     recursos["Tanque 1"], recursos["Tanque 2"]]
        entre_primeros = False

        if self.transbordo == "Si":
            entre_primeros = True
        elif any(self.carga in almacen.niveles.keys() and self.entre_primeros_cola_medio_de_almacenamiento(almacen)
                 for almacen in almacenes):
            entre_primeros = True
        return entre_primeros

    def entre_primeros_colas_recursos(self, recursos):
        """
        Identifica si el camion esta entre los primeros camiones en alguna cola de recursos
        de manipuleo en el sistema

        :type recursos: dict
        """

        entre_primeros = False
        recursos_manipuleo = [
            recursos["Estacion Volcadora"],
            recursos["Estacion Tolva"],
            recursos["Pala Mecanica"],
            recursos["Cuadrilla de Estibaje"],
            recursos["Cabina de Recepcion - T1"],
            recursos["Cabina de Despacho - T1"],
            recursos["Cabina de Recepcion - T2"],
            recursos["Cabina de Despacho - T2"],
            recursos["Grua"]]

        if any(self.entre_primeros_cola_recurso(recurso)
               for recurso in recursos_manipuleo):
            entre_primeros = True
        return entre_primeros

    def entre_primeros_cola_medio_de_almacenamiento(self, medio_de_almacenamiento):
        """
        Identifica si el camion esta entre los primeros camiones de la cola del medio de almacenamiento

        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        """

        if self in medio_de_almacenamiento.cola[0:medio_de_almacenamiento.espacios_de_atencion]:
            return True
        else:
            return False

    def entre_primeros_cola_recurso(self, recurso):
        """
        Identifica si el camion esta entre los primeros camiones de la cola del recurso de atencion

        :type recurso: Recurso
        """

        if self in recurso.cola[0:recurso.capacity]:
            return True
        else:
            return False

    def atras_de_camion_en_cola_medio_almacenamiento(self, camion_ref, medio_de_almacenamiento):
        """
        Identifica si el camion esta detras de otro en la cola del medio de almacenamiento

        :type camion_ref: Camion
        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        """

        if self in medio_de_almacenamiento.cola[medio_de_almacenamiento.cola.index(camion_ref) + 1:]:
            return True
        else:
            return False

    def atras_de_camion_en_cola_recurso(self, camion_ref, recurso):
        """
        Identifica si el camion esta detras de otro en la cola del recurso de atención

        :type camion_ref: Camion
        :type recurso: Recurso
        """

        if self in recurso.cola[recurso.cola.index(camion_ref) + 1:]:
            return True
        else:
            return False


class Operacion(object):
    """Clase para el modelado de las operaciones presentes en el sistema."""

    def __init__(self, nombre, recurso, ts_distrib, parametros, datos):
        """
        Define las características principales de la clase operación.

        :type nombre: str
        :type recurso: Recurso
        :type ts_distrib: str
        :type parametros: list
        :type datos: list
        """
        self.nombre = nombre
        self.recurso = recurso
        self.ts_distrib = ts_distrib
        self.parametros = parametros
        self.datos = datos

    def tiempo_de_servicio(self):  # TODO Incluir distribuciones de probabilidad
        """
        Genera el tiempo de servicio de la operación
        """

        if self.ts_distrib == "uniforme":
            ts = random.uniform(*self.parametros)
        elif self.ts_distrib == "triangular":
            ts = random.triangular(*self.parametros)
        else:
            print "Error, distribución no reconocida"
            ts = None
        return int(round(ts, 0))

    def ejecutar(self, sistema, camion, tpaciencia_t=float("Inf"), medio_de_almacenamiento=None):
        """
        Simula la ejecución de la operación registrando y mostrando datos de la atención.

        :type sistema: Sistema
        :type camion: Camion.
        :type tpaciencia_t: int
        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        """

        arribo = sistema.now
        self.recurso.cola.append(camion)

        # Camion solicita adelanto ingreso
        yield sistema.process(
            camion.espera_operacion(sistema, self))

        with self.recurso.request() as turno:

            yield turno

            # Al ingresar a las primeras operaciones, el camion ingresa al sistema
            if self.nombre in ["Atencion recepcion 1", "Atencion despacho 1"]:
                sistema.camiones_en_sistema.append(camion)

            inicio = sistema.now
            espera_r = inicio - arribo
            print str(camion) + " Inicio " + self.nombre + " - Hora: " + str(inicio)
            ts = self.tiempo_de_servicio()

            yield sistema.timeout(ts)
            self.recurso.cola.remove(camion)

            salida = sistema.now

            print str(camion) + " SALE DE SISTEMA - HORA: " + str(sistema.now)

            # Al salir de las últimas operaciones, el camion sale del sistema
            if self.nombre in ["Atencion recepcion 2", "Atencion despacho 2"]:
                sistema.camiones_en_sistema.remove(camion)

            fila_de_datos = [camion.nombre, camion.carga, camion.tipo, camion.peso, self.nombre,
                             arribo, "-", espera_r, "-", "-", inicio, salida, "-", "-"]

            self.datos.append(fila_de_datos)


class OperacionManipuleo(Operacion):
    """
    Clase para el modelado de las operaciones de manipuleo presentes en el sistema.
    Subclase de Operacion
    """

    def __init__(self, nombre, recurso, ts_distrib, parametros, datos):
        """
        Define las características principales de la clase operación manipuleo.

        :type nombre: str
        :type recurso: Recurso
        :type ts_distrib: str
        :type parametros: list
        """
        super(OperacionManipuleo, self).__init__(nombre, recurso, ts_distrib, parametros, datos)

    def ejecutar(self, sistema, camion, tpaciencia_t=float("Inf"), medio_de_almacenamiento=None):
        """
        Modela la ejecución de la operación de manipuleo.

        :type sistema: Sistema
        :type camion:  Camion
        :type tpaciencia_t: int
        :type medio_de_almacenamiento: MedioDeAlmacenamiento
        """

        if medio_de_almacenamiento is not None:

            arribo = sistema.now
            print str(camion) + " arribo a - " + self.nombre + " - Hora: " + str(arribo)

            self.recurso.cola.append(camion)
            medio_de_almacenamiento.cola.append(camion)

            if not camion.entre_primeros_cola_recurso(self.recurso) \
                    or not camion.entre_primeros_cola_medio_de_almacenamiento(medio_de_almacenamiento):
                camion.solicita_adelanto(sistema, self, medio_de_almacenamiento)

            espera_manipuleo = yield sistema.process(
                camion.espera_operacion_manipuleo(sistema, self, medio_de_almacenamiento, tpaciencia_t))

            if espera_manipuleo[0] == "Inicia":

                espera_r = espera_manipuleo[1]
                espera_p = espera_manipuleo[2]
                espera_m_od = espera_manipuleo[3]
                espera_t = espera_manipuleo[4]

                with self.recurso.request() as turno:

                    yield turno

                    if turno.triggered:
                        inicio = sistema.now
                        print str(camion) + " Inicio " + self.nombre + " - Hora: " + str(inicio)
                        ts = self.tiempo_de_servicio()
                        print str(camion) + " ts=" + str(ts)

                        # Inicia uso de estacion disp. en medio de origen/destino
                        medio_de_almacenamiento.espacios_en_uso += 1

                        atencion = sistema.timeout(ts)
                        yield atencion

                        if camion.tipo == "Carga":
                            medio_de_almacenamiento.cargar_producto(camion, camion.carga)
                        else:
                            medio_de_almacenamiento.descargar_producto(camion, camion.carga)

                        # Concluye uso de estacion disp. en medio de origen/destino
                        medio_de_almacenamiento.espacios_en_uso -= 1

                        self.recurso.cola.remove(camion)
                        medio_de_almacenamiento.cola.remove(camion)

                        print str(camion) + " SALE DE SISTEMA - HORA: " + str(sistema.now)

                        print "\tEn sistema: " + str(self.recurso.cola)
                        print "\t" + medio_de_almacenamiento.nombre + ":" \
                              + str(medio_de_almacenamiento.cola)

                        camion.peso = camion.trailer.level

                        salida = sistema.now
                        camion.manipulado.succeed()

                        fila_de_datos = [camion.nombre, camion.carga, camion.tipo, camion.peso, self.nombre,
                                         arribo, espera_m_od, espera_r, espera_p, espera_t, inicio, salida,
                                         medio_de_almacenamiento.nombre,
                                         medio_de_almacenamiento.niveles[camion.carga]]

                        self.datos.append(fila_de_datos)

                        sistema.exit("Ejecutada")

                    else:

                        medio_de_almacenamiento.cola.remove(camion)
                        self.recurso.cola.remove(camion)
                        print "%s NO EJECUTADA POR RECURSO" % camion
                        sistema.exit("No ejecutada por recurso")

            else:

                medio_de_almacenamiento.cola.remove(camion)
                self.recurso.cola.remove(camion)
                print str(camion) + " SALE DE SISTEMA SIN EJECUCIÓN - HORA: " + str(sistema.now)
                print "%s NO EJECUTADA POR PRODUCTO" % camion
                print "\t" + medio_de_almacenamiento.nombre + " " \
                      + str(medio_de_almacenamiento.niveles[camion.carga])
                sistema.exit("No ejecutada por producto")

        else:
            print "Camion " + str(camion.nombre) + " - Error, no se definió el medio de origen o destino"


class Recurso(simpy.Resource):
    """
    Clase para el modelado de recursos para la ejecucion de operaciones
    Subclase de simpy.Resource
    Los recursos pueden ser:
    - Mano de obra
    - Maquinaria
    """

    def __init__(self, sistema, nombre, horario, capacity=1):
        """
        Define las características principales de la clase recurso.

        :type sistema: Sistema
        :type nombre: str
        :type horario: dict
        :type capacity: int
        """
        super(Recurso, self).__init__(sistema, capacity)
        self.nombre = nombre
        self.cola = []
        self.horario = horario

    def cola_detras_de_camion(self, camion):

        if camion in self.cola:
            return self.cola[self.cola.index(camion) + 1:]
        else:
            print "ERROR: " + str(camion) + " no esta en la cola de " + self.nombre


class MedioDeAlmacenamiento(simpy.Container):
    """
    Clase para el modelado de medios de almacenamiento.
    Subclase de simpy.Container.
    """

    def __init__(self, sistema, nombre, espacios_de_atencion, niveles=None, capacity=float('inf'), init=0):
        """
        Define las caracteristicas del medio de almacenamiento

        :type sistema: Sistema
        :type nombre: str
        :type espacios_de_atencion: int
        :type niveles: dict
        :type capacity: float
        :type init: int
        """

        super(MedioDeAlmacenamiento, self).__init__(sistema, capacity, init)
        self.nombre = nombre
        self.espacios_de_atencion = espacios_de_atencion
        self.espacios_en_uso = 0
        self.cola = []

        if niveles is not None:
            self.niveles = niveles
            if sum(self.niveles.values()) > 0:
                self.get(sum(self.niveles.values()))
            self.espacio = self.capacity - self.level

    def cargar_producto(self, camion, producto):
        """
        Simula la carga de producto del almacen a un camión

        :param camion:
        :param producto:
        """
        if self.niveles[producto] >= 28:
            self.get(28) & camion.trailer.put(28)
            self.niveles[producto] -= 28
            self.espacio += 28
        else:
            print "****ERROR EN CARGA, PRODUCTO NO DISPONIBLE**** " + str(camion)

    def descargar_producto(self, camion, producto):
        """
        Simula la descarga de producto de un camion al almacén

        :param camion:
        :param producto:
        """
        if (self.capacity - self.level) >= 28:
            self.put(camion.peso) & camion.trailer.get(camion.peso)
            self.niveles[producto] += 28
            self.espacio -= 28
        else:
            print "****ERROR DESCARGA, ESPACIO NO DISPONIBLE**** " + str(camion)

    def cola_detras_de_camion(self, camion):

        if camion in self.cola:
            return self.cola[self.cola.index(camion) + 1:]
        else:
            print "ERROR: " + str(camion) + " no esta en la cola de " + self.nombre


if __name__ == "__main__":
    self = Sistema()
    self.simular()
