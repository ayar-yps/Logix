# -*- coding: utf-8 -*-
"""
SIMULACIÓN DE OPERACIONES LOGÍSTICAS EN ALPASUR S.A. - KEMFA S.A.
@author: Ayar Yuman Paco Sanizo
@version: 2.0
@summary: Simulación de operaciones logísticas en un centro de transbordo y almacenamiento.
"""

import os
import simpy
import random
import csv


class Camion(object):
    """Clase para el modelado de camiones presentes en el sistema"""

    def __init__(self, entorno, nombre):
        """
        Define las propiedades principales de la clase Camion

        :type entorno: simpy.Environment
        :type nombre: int
        """
        productos = ["Harina de Soya - Hi Pro", "Harina de Soya - Full Fat", "Torta de Soya",
                     "Torta de Girasol", "Aceite de Soya", "Pellet de Soya", "Grano de Soya",
                     "Azucar", "Fierro", "Contenedor 20", "Contenedor 40"]

        self.nombre = nombre
        # TODO modificar con datos reales
        self.carga = random.choice(productos)

        if random.random() <= 0.5:
            self.tipo = "Descarga"
            self.peso = 28
        else:
            self.peso = 0
            self.tipo = "Carga"

        self.trailer = MedioDeAlmacenamiento(entorno, str(self.nombre), 28, self.peso)

        self.manipulado = entorno.event()

    @staticmethod
    def llega_a_instalacion(entorno):
        """
        Genera la llegada del camion

        :type entorno: simpy.Environment
        """
        tell = random.uniform(1, 2)  # TODO Modificar con información real

        yield entorno.timeout(round(tell, 0))

    def espera(self, entorno, tespera):
        """
        Simula la espera del camion para realizar transbordo
        Finalizada la espera se procede con una operacion de carga o descarga
        Sin embargo, si otro camion llega se interrumpe la espera y se procede con un transbordo

        :type entorno: simpy.Environment
        :type tespera: int
        """
        try:

            print "%d\t%s %s\t inicia espera en %d" % (self.nombre, self.tipo, self.carga, round(entorno.now, 0))
            yield entorno.timeout(tespera)
            print str(self.nombre) + " termino espera en " + str(entorno.now)

            entorno.exit({"Resultado": "Termino espera", "Interrupcion": None})

        except simpy.Interrupt as interrupcion:

            print str(self.nombre) + " espera interrumpida por " + str(interrupcion.cause.nombre) + " en " + str(
                entorno.now)
            entorno.exit({"Resultado": "Espera interrumpida", "Interrupcion": interrupcion.cause})

    def interrumpe(self, proceso):
        """
        Interrumpe la espera de otro camion para realizar un transbordo.
        Al interrumpir, el camion pasa a comportarse como medio de origen o destino de carga

        :type proceso: simpy.events.Process
        """
        proceso.interrupt(self)

    def espera_o_interrumpe(self, entorno, listas_de_espera):
        """
        Permite que un camion espere o interrumpa la espera de otro para realizar un transbordo

        :type entorno: simpy.Environment
        :type self: Camion
        :type listas_de_espera: dict
        """

        if self.tipo == "Carga":
            tipo_camion_en_esp = "Descarga"
        else:
            tipo_camion_en_esp = "Carga"

        if len(listas_de_espera[self.carga][tipo_camion_en_esp]) != 0:

            print str(self.nombre) + " " + str(self.tipo) + " " + str(self.carga) + " llego en " + str(entorno.now)

            camion_en_espera = listas_de_espera[self.carga][tipo_camion_en_esp][0][0]
            espera_en_proceso = listas_de_espera[self.carga][tipo_camion_en_esp][0][1]

            self.interrumpe(espera_en_proceso)

            listas_de_espera[self.carga][tipo_camion_en_esp] = listas_de_espera[self.carga][tipo_camion_en_esp][1:]
            camion_interrumpido = camion_en_espera

            yield camion_interrumpido.manipulado

            entorno.exit({"Resultado": "Interrumpio espera", "Interrupcion": None})

        else:

            if self.carga == "Fierro":
                tespera = 480
            else:
                tespera = 100

            espera = entorno.process(self.espera(entorno, tespera))
            listas_de_espera[self.carga][self.tipo].append([self, espera])

            resultado_espera = yield espera

            if resultado_espera["Resultado"] == "Termino espera":
                listas_de_espera[self.carga][self.tipo] = listas_de_espera[self.carga][self.tipo][1:]

            entorno.exit(resultado_espera)

    def espera_producto(self, entorno, operacion, medio_de_origen_o_destino, tpaciencia_p):

        espera_p = 0

        if self.tipo == "Carga":

            operacion.recurso.camiones_esperando_carga.append(self.nombre)

            while espera_p < tpaciencia_p:
                if self.nombre == 19:
                    print "WTF!!" + str(operacion.recurso.camiones_esperando_carga[0])

                if medio_de_origen_o_destino.level >= 28 \
                        and self.nombre in operacion.recurso.camiones_esperando_carga[0:operacion.recurso.capacity]:
                    print str(self.nombre) + " deja espera " + str(entorno.now)
                    break
                yield entorno.timeout(1)
                espera_p += 1

            if medio_de_origen_o_destino.level >= 28 and espera_p <= tpaciencia_p and self.nombre in \
                    operacion.recurso.camiones_esperando_carga[0:operacion.recurso.capacity]:
                entorno.exit(["Inicia", espera_p])
                print str(self.nombre) + " Inicia " + str(entorno.now)
            else:
                entorno.exit(["No inicia", espera_p])

        else:

            espacio = medio_de_origen_o_destino.capacity - medio_de_origen_o_destino.level
            operacion.recurso.camiones_esperando_carga.append(self.nombre)

            while espera_p < tpaciencia_p:

                if espacio >= 28 and self.nombre in operacion.recurso.camiones_esperando_carga[
                                                    0:operacion.recurso.capacity]:
                    print str(self.nombre) + " deja espera " + str(entorno.now)
                    break
                yield entorno.timeout(1)
                espera_p += 1
                espacio = medio_de_origen_o_destino.capacity - medio_de_origen_o_destino.level

            if espacio >= 28 and espera_p <= tpaciencia_p \
                    and self.nombre in operacion.recurso.camiones_esperando_carga[0:operacion.recurso.capacity]:
                entorno.exit(["Inicia", espera_p])
                print operacion.recurso.camiones_esperando_carga
                print str(self.nombre) + " Inicia " + str(entorno.now)
            else:
                entorno.exit(["No inicia", espera_p])


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
        # self.camiones_c_esperando_carga = []
        # self.camiones_d_esperando_carga = []

    def tiempo_de_servicio(self):  # TODO Incluir distribuciones de probabilidad
        """Genera el tiempo de servicio de la operación"""

        if self.ts_distrib == "uniforme":
            ts = random.uniform(*self.parametros)
        elif self.ts_distrib == "triangular":
            ts = random.triangular(*self.parametros)
        else:
            print "Error, distribución no reconocida"
            ts = None
        return round(ts, 0)

    def ejecutar(self, entorno, camion, tpaciencia_r=None, tpaciencia_p=None, medio_de_origen_o_destino=None):
        """
        Simula la ejecución de la operación registrando y mostrando datos de la atención.

        :type entorno: simpy.Environment
        :type camion: Camion.
        :type tpaciencia_r: int
        :type tpaciencia_p: int
        :type medio_de_origen_o_destino: MedioDeAlmacenamiento
        """

        arribo = entorno.now
        with self.recurso.request() as turno:
            yield turno
            inicio = entorno.now
            espera_r = inicio - arribo
            ts = self.tiempo_de_servicio()
            yield entorno.timeout(ts)
            salida = entorno.now
            fila_de_datos = [camion.nombre, camion.carga, camion.tipo, camion.peso, self.nombre,
                             arribo, espera_r, "-", "-", inicio, salida, "-", "-"]
            self.datos.append(fila_de_datos)


class OperacionManipuleo(Operacion):
    """Clase para el modelado de las operaciones de manipuleo presentes en el sistema."""

    def __init__(self, nombre, recurso, ts_distrib, parametros, datos):
        """
        Define las características principales de la clase operación manipuleo.

        :type nombre: str
        :type recurso: Recurso
        :type ts_distrib: str
        :type parametros: list
        """
        super(OperacionManipuleo, self).__init__(nombre, recurso, ts_distrib, parametros, datos)

    def ejecutar(self, entorno, camion, tpaciencia_r=None, tpaciencia_p=None, medio_de_origen_o_destino=None):
        """
        Modela la ejecución de la operación de manipuleo.

        :type entorno: simpy.Environment
        :type camion:  Camion
        :type tpaciencia_r: int
        :type tpaciencia_p: int
        :type medio_de_origen_o_destino: MedioDeAlmacenamiento
        """

        if medio_de_origen_o_destino is not None:

            arribo = entorno.now
            print str(camion.nombre) + " arribo a op en " + str(arribo)

            espera_producto = yield entorno.process(
                camion.espera_producto(entorno, self, medio_de_origen_o_destino, tpaciencia_p))

            print str(camion.nombre) + " " + espera_producto[0]
            if espera_producto[0] == "Inicia":

                espera_p = espera_producto[1]

                with self.recurso.request() as turno:

                    ingreso = entorno.now

                    yield turno | entorno.timeout(tpaciencia_r)

                    if turno.triggered:
                        inicio = entorno.now
                        print str(camion.nombre) + " inicio en " + str(inicio)
                        espera_r = inicio - ingreso
                        ts = self.tiempo_de_servicio()
                        print str(camion.nombre) + " ts=" + str(ts)
                        atencion = entorno.timeout(ts)

                        yield atencion

                        if camion.tipo == "Carga":
                            medio_de_origen_o_destino.get(28) & camion.trailer.put(28)
                        else:
                            medio_de_origen_o_destino.put(camion.peso) & camion.trailer.get(camion.peso)

                        if len(self.recurso.camiones_esperando_carga) != 0 and camion.nombre in \
                                self.recurso.camiones_esperando_carga[0:self.recurso.capacity]:
                            self.recurso.camiones_esperando_carga.remove(camion.nombre)
                            print str(camion.nombre) + " SALE DE COLA EN " + str(entorno.now)
                        elif len(self.recurso.camiones_esperando_carga) != 0 and camion.nombre in \
                                self.recurso.camiones_esperando_carga[0:self.recurso.capacity]:
                            self.recurso.camiones_esperando_carga.remove(camion.nombre)
                            print str(camion.nombre) + " SALE DE COLA EN " + str(entorno.now)

                        camion.peso = camion.trailer.level

                        salida = entorno.now
                        camion.manipulado.succeed()

                        fila_de_datos = [camion.nombre, camion.carga, camion.tipo, camion.peso, self.nombre,
                                         arribo, espera_r, ingreso, espera_p, inicio, salida,
                                         medio_de_origen_o_destino.nombre, medio_de_origen_o_destino.level]
                        self.datos.append(fila_de_datos)

                        # print fila_de_datos
                        entorno.exit("Ejecutada")

                    else:

                        print "%d %s %s %s NO EJECUTADA POR RECURSO" % (
                            camion.nombre, camion.tipo, self.nombre, camion.carga)
                        entorno.exit("No ejecutada por recurso")

            else:

                if len(self.recurso.camiones_esperando_carga) != 0 and camion.nombre in \
                        self.recurso.camiones_esperando_carga:
                    self.recurso.camiones_esperando_carga.remove(camion.nombre)
                elif len(self.recurso.camiones_esperando_carga) != 0 and camion.nombre in \
                        self.recurso.camiones_esperando_carga:
                    self.recurso.camiones_esperando_carga.remove(camion.nombre)

                print "%d %s %s %s NO EJECUTADA POR PRODUCTO" % (camion.nombre, camion.tipo, self.nombre, camion.carga)
                print medio_de_origen_o_destino.nombre + " " + str(medio_de_origen_o_destino.level)
                entorno.exit("No ejecutada por producto")

        else:
            print "Camion " + str(camion.nombre) + " - Error, no se definió el medio de origen o destino"


class Recurso(simpy.Resource):
    def __init__(self, env, capacity=1):
        super(Recurso, self).__init__(env, capacity)
        self.camiones_esperando_carga = []


class MedioDeAlmacenamiento(simpy.Container):
    def __init__(self, env, nombre, capacity=float('inf'), init=0):
        """
        Define las caracteristicas del medio de almacenamiento

        :type nombre: str
        """
        super(MedioDeAlmacenamiento, self).__init__(env, capacity, init)
        self.nombre = nombre


def generar_camiones(entorno, operaciones, recursos):
    """
    Genera camiones en el entorno de simulación

    :type entorno: simpy.Environment
    :type operaciones: dict
    :type recursos: dict
    """

    camiones = {
        "Harina de Soya - Hi Pro":
            {"Descarga": [], "Carga": []},
        "Harina de Soya - Full Fat":
            {"Descarga": [], "Carga": []},
        "Torta de Soya":
            {"Descarga": [], "Carga": []},
        "Torta de Girasol":
            {"Descarga": [], "Carga": []},
        "Aceite de Soya":
            {"Descarga": [], "Carga": []},
        "Pellet de Soya":
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

    listas_de_espera = {
        "Harina de Soya - Hi Pro":
            {"Descarga": [], "Carga": []},
        "Harina de Soya - Full Fat":
            {"Descarga": [], "Carga": []},
        "Torta de Soya":
            {"Descarga": [], "Carga": []},
        "Torta de Girasol":
            {"Descarga": [], "Carga": []},
        "Aceite de Soya":
            {"Descarga": [], "Carga": []},
        "Pellet de Soya":
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
        camion = Camion(entorno, i + 1)
        camiones[camion.carga][camion.tipo].append(camion)

        yield entorno.process(camion.llega_a_instalacion(entorno))
        entorno.process(atender_camion(entorno, camion, operaciones, listas_de_espera, recursos))

        i += 1


def atender_camion(entorno, camion, operaciones, listas_de_espera, recursos):
    """
    Simula el proceso de atención de camiones dividiendolo en 3 etapas:
    - Operaciones complementarias preliminares
    - Operaciones de manipuleo
    - Operaciones complementarias posterores

    :type entorno: simpy.Environment
    :type camion: Camion
    :type operaciones: dict
    :type listas_de_espera: dict
    :type recursos: dict
    """

    # Operaciones Complementarias Ingreso
    yield entorno.process(atencion_ingreso(entorno, camion, operaciones["Operaciones complementarias"]))

    # Manipuleo
    yield entorno.process(atencion_manipuleo(entorno, camion, operaciones["Operaciones manipuleo"],
                                             listas_de_espera, recursos))

    # Operaciones Complementarias Salida
    yield entorno.process(atencion_salida(entorno, camion, operaciones["Operaciones complementarias"]))


def atencion_manipuleo(entorno, camion, operaciones, listas_de_espera, recursos):
    if camion.carga in ["Harina de Soya - Hi Pro", "Pellet de Soya", "Grano de Soya"]:

        yield entorno.process(manipular_granos(
            entorno, camion, operaciones, listas_de_espera, recursos))

    elif camion.carga in ["Harina de Soya - Full Fat", "Torta de Soya", "Torta de Girasol", "Azucar"]:

        yield entorno.process(manipular_sacos(
            entorno, camion, operaciones, listas_de_espera, recursos))

    elif camion.carga in ["Aceite de Soya"]:

        yield entorno.process(manipular_liquidos(
            entorno, camion, operaciones, recursos))

    elif camion.carga in ["Contenedor 20", "Contenedor 40"]:

        yield entorno.process(manipular_contedenor(
            entorno, camion, operaciones, recursos))

    elif camion.carga in ["Fierro"]:

        yield entorno.process(manipular_carga_general(
            entorno, camion, operaciones, listas_de_espera))


def manipular_granos(entorno, camion, operaciones, listas_de_espera, recursos):
    # Manipuleo de camion por cargar
    if camion.tipo == "Carga":

        # Manipuleo de carga a granel seca en almacenes propios
        if camion.carga in ["Harina de Soya - Hi Pro", "Pellet de Soya"]:

            # Se carga a partir de un transbordo en sistema mecanizado
            transbordo = operaciones["Transbordo en sistema mecanizado (C)"]
            ejecucion_transbordo = yield entorno.process(
                transbordo.ejecutar(entorno, camion, 0, 0, recursos["Tolva"]))

            # Si no se ejecuta el transbordo se carga con pala mecánica
            if ejecucion_transbordo in ["No ejecutada por recurso", "No ejecutada por producto"]:

                carga = operaciones["Carga con pala mecanica"]
                ejecucion_carga = yield entorno.process(
                    carga.ejecutar(entorno, camion, 200, 100, recursos["Almacen 1"]))

                # Si no se ejecuta la carga espera camion para realizar transbordo o interrumpe la espera de otro
                if ejecucion_carga in ["No ejecutada por recurso", "No ejecutada por producto"]:

                    ejecucion_espera_o_interrumpe = yield entorno.process(
                        camion.espera_o_interrumpe(entorno, listas_de_espera))

                    # Si el camion espera procede con un tranbordo o carga a pulso
                    if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":

                        transbordo = operaciones["Transbordo a pulso - Granos"]
                        carga = operaciones["Carga a pulso - Granos"]

                        transborda_o_carga = yield entorno.process(transbordar_o_cargar_descargar(
                            entorno, camion, ejecucion_espera_o_interrumpe,
                            transbordo, 100, 100,
                            carga, recursos["Almacen 1"], 100, 100))

                        # Si no se ejecuta el transbordo o carga a pulso, se carga con tolva
                        if transborda_o_carga in ["No ejecutada por recurso", "No ejecutada por producto"]:
                            carga = operaciones["Carga con tolva"]
                            yield entorno.process(
                                carga.ejecutar(entorno, camion, 100, 100, recursos["Almacen 1"]))

        # Manipuleo de carga a granel seca en almacenes externos
        elif camion.carga in ["Grano de Soya"]:

            # Se carga con pala mecanica
            carga = operaciones["Carga con pala mecanica"]
            ejecucion_carga = yield entorno.process(
                carga.ejecutar(entorno, camion, 200, 400, recursos["Almacen Ext"]))

            # Si no se ejecuta la carga, espera camion para realizar transbordo o interrumpe la espera de otro
            if ejecucion_carga in ["No ejecutada por recurso", "No ejecutado por producto"]:

                ejecucion_espera_o_interrumpe = yield entorno.process(
                    camion.espera_o_interrumpe(entorno, listas_de_espera))

                # Si el camion espera procede con un tranbordo o carga a pulso
                if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                    transbordo = operaciones["Transbordo a pulso - Granos"]
                    carga = operaciones["Carga a pulso - Granos"]

                    yield entorno.process(transbordar_o_cargar_descargar(
                        entorno, camion, ejecucion_espera_o_interrumpe,
                        transbordo, 100, 100,
                        carga, recursos["Almacen Ext"], 100, 100))

    # Manipuleo de camion por descargar
    elif camion.tipo == "Descarga":

        # Manipuleo de carga a granel en almacenes propios
        if camion.carga in ["Pellet de Soya", "Harina de Soya - Hi Pro"]:

            # Se descarga a partir de un transbordo en sistema mecanizado
            transbordo = operaciones["Transbordo en sistema mecanizado (D)"]
            ejecucion_transbordo = yield entorno.process(
                transbordo.ejecutar(entorno, camion, 100, 20, recursos["Tolva"]))

            # Si no se ejecuta el transbordo por disp. de recurso espera camion para realizar transbordo
            # a pulso o interrumpe la espera de otro
            if ejecucion_transbordo == "No ejecutada por recurso":

                ejecucion_espera_o_interrumpe = yield entorno.process(
                    camion.espera_o_interrumpe(entorno, listas_de_espera))

                # Si el camion espera procede con un tranbordo o descarga a pulso
                if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                    transbordo = operaciones["Transbordo a pulso - Granos"]
                    descarga = operaciones["Descarga a pulso - Granos"]

                    yield entorno.process(transbordar_o_cargar_descargar(
                        entorno, camion, ejecucion_espera_o_interrumpe,
                        transbordo, 100, 100,
                        descarga, recursos["Almacen 1"], 100, 100))

            # Si no se ejecuta el transbordo por nivel de producto se descarga en almacenes propios
            elif ejecucion_transbordo == "No ejecutada por producto":

                descarga = operaciones["Descarga con volcadora"]
                yield entorno.process(descarga.ejecutar(entorno, camion, 0, 100, recursos["Almacen 1"]))

        # Manipuleo de carga a granel en almacenes externos
        elif camion.carga in ["Grano de Soya"]:

            # Espera camion para realizar transbordo o interrumpe la espera de otro
            ejecucion_espera_o_interrumpe = yield entorno.process(
                camion.espera_o_interrumpe(entorno, listas_de_espera))

            # Si el camion espera procede con un tranbordo o descarga a pulso
            if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
                transbordo = operaciones["Transbordo a pulso - Granos"]
                descarga = operaciones["Descarga a pulso - Granos"]

                yield entorno.process(transbordar_o_cargar_descargar(
                    entorno, camion, ejecucion_espera_o_interrumpe,
                    transbordo, 100, 100,
                    descarga, recursos["Almacen Ext"], 100, 100))


def manipular_sacos(entorno, camion, operaciones, listas_de_espera, recursos):
    # Manipuleo de camion por cargar
    if camion.tipo == "Carga":

        # Espera camion para realizar transbordo o interrumpe la espera de otro
        ejecucion_espera_o_interrumpe = yield entorno.process(
            camion.espera_o_interrumpe(entorno, listas_de_espera))

        # Si el camion espera procede con un tranbordo o carga a pulso
        if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
            transbordo = operaciones["Transbordo a pulso - Sacos"]
            carga = operaciones["Carga a pulso - Sacos"]

            yield entorno.process(transbordar_o_cargar_descargar(
                entorno, camion, ejecucion_espera_o_interrumpe,
                transbordo, 100, 100,
                carga, recursos["Almacen 2"], 100, 100))

    # Manipuleo de camion por descargar
    elif camion.tipo == "Descarga":

        # Espera camion para realizar transbordo o interrumpe la espera de otro
        ejecucion_espera_o_interrumpe = yield entorno.process(
            camion.espera_o_interrumpe(entorno, listas_de_espera))

        # Si el camion espera procede con un tranbordo o descarga a pulso
        if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
            transbordo = operaciones["Transbordo a pulso - Sacos"]
            descarga = operaciones["Descarga a pulso - Sacos"]

            yield entorno.process(transbordar_o_cargar_descargar(
                entorno, camion, ejecucion_espera_o_interrumpe,
                transbordo, 100, 100,
                descarga, recursos["Almacen 2"], 100, 100))


def manipular_liquidos(entorno, camion, operaciones, recursos):
    # Manipuleo de camiones por cargar
    if camion.tipo == "Carga":

        carga = operaciones["Carga con bombas electricas"]
        yield entorno.process(carga.ejecutar(entorno, camion, 100, 100, recursos["Tanque 1"]))

    # Manipuleo de camiones por descargar
    elif camion.tipo == "Descarga":

        descarga = operaciones["Descarga con bombas electricas"]
        yield entorno.process(descarga.ejecutar(entorno, camion, 100, 100, recursos["Tanque 1"]))


def manipular_contedenor(entorno, camion, operaciones, recursos):
    # Manipuleo de camiones por cargar
    if camion.tipo == "Carga":

        carga = operaciones["Carga con grua"]
        yield entorno.process(carga.ejecutar(entorno, camion, 100, 100, recursos["Patio de Contenedores"]))

    # Manipuleo de camiones por descargar
    elif camion.tipo == "Descarga":

        descarga = operaciones["Descarga con grua"]
        yield entorno.process(descarga.ejecutar(entorno, camion, 100, 100, recursos["Patio de Contenedores"]))


def manipular_carga_general(entorno, camion, operaciones, listas_de_espera):
    # Manipuleo de camiones por cargar/descargar

    # Espera camion para realizar transbordo o interrumpe la espera de otro
    ejecucion_espera_o_interrumpe = yield entorno.process(
        camion.espera_o_interrumpe(entorno, listas_de_espera))

    # Si el camion espera procede con un tranbordo
    if ejecucion_espera_o_interrumpe["Resultado"] != "Interrumpio espera":
        transbordo = operaciones["Transbordo con grua"]

        yield entorno.process(transbordar_o_cargar_descargar(
            entorno, camion, ejecucion_espera_o_interrumpe,
            transbordo, 400, 100))


def transbordar_o_cargar_descargar(entorno, camion, ejecucion_espera_o_interrumpe,
                                   transbordo, tpaciencia_r_t, tpaciencia_p_t,
                                   carga_o_descarga=None, recurso_cd=None, tpaciencia_r_cd=None, tpaciencia_p_cd=None):
    # Se concluyo la espera, se procede con la carga o descarga
    if ejecucion_espera_o_interrumpe["Resultado"] == "Termino espera":

        yield entorno.process(
            carga_o_descarga.ejecutar(entorno, camion, tpaciencia_r_cd, tpaciencia_p_cd, recurso_cd))

    # Se interrumpio la espera, se procede con el transbordo
    # elif ejecucion_espera_o_interrumpe["Resultado"] == "Espera interrumpida":
    elif ejecucion_espera_o_interrumpe["Resultado"] == "Espera interrumpida":
        recurso_t = ejecucion_espera_o_interrumpe["Interrupcion"].trailer
        yield entorno.process(
            transbordo.ejecutar(entorno, camion, tpaciencia_r_t, tpaciencia_p_t, recurso_t))


def atencion_ingreso(entorno, camion, operaciones):
    """
    Modela el proceso de ingreso de camiones previo al manipuleo

    :type entorno: simpy.Environment
    :type camion: Camion
    :type operaciones: dict
    """
    if camion.tipo == "Descarga":
        yield entorno.process(operaciones["Atencion recepcion 1"]
                              .ejecutar(entorno, camion))
    else:
        yield entorno.process(operaciones["Atencion despacho 1"]
                              .ejecutar(entorno, camion))

    if camion.carga not in ["Contenedor 20", "Contenedor 40"]:
        yield entorno.process(operaciones["Primer pesaje"]
                              .ejecutar(entorno, camion))
    entorno.exit(camion.nombre)


def atencion_salida(entorno, camion, operaciones):
    """
    Modela el proceso de salida de camiones posterior al manipuleo

    :type entorno: simpy.Environment
    :type camion: Camion
    :type operaciones: dict
    """
    if camion.carga not in ["Contenedor 20", "Contenedor 40"]:
        yield entorno.process(operaciones["Segundo pesaje"]
                              .ejecutar(entorno, camion))

    if camion.tipo == "Descarga":
        yield entorno.process(operaciones["Atencion recepcion 2"]
                              .ejecutar(entorno, camion))
    else:
        yield entorno.process(operaciones["Atencion despacho 2"]
                              .ejecutar(entorno, camion))


def guardar_datos(datos, archivo):
    with open(archivo, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow(
            ["Camion", "Carga", "Tipo", "Peso Final", "Operacion",
             "Arribo", "Espera R", "Ingreso", "Espera P.", "Inicio", "Fin",
             "Medio de Almacenamiento", "Nivel"])
        for linea in datos:
            writer.writerow(linea)


# Procedimiento principal para la ejecucion de la simulacion
def principal():
    # DATOS DE SIMULACION

    # Entorno
    env = simpy.Environment()

    datos = []
    # Definición de Recursos
    recursos = {
        "Ventanilla Recepcion":
            Recurso(env, capacity=1),
        "Ventanilla Despacho":
            Recurso(env, capacity=1),
        "Balanza 2":
            Recurso(env, capacity=1),
        "Estacion Volcadora":
            Recurso(env, capacity=1),
        "Estacion Tolva":
            Recurso(env, capacity=1),
        "Pala Mecanica":
            Recurso(env, capacity=1),
        "Cuadrilla de Estibaje":
            Recurso(env, capacity=3),
        "Cabina de Recepcion":
            Recurso(env, capacity=2),
        "Cabina de Despacho":
            Recurso(env, capacity=2),
        "Grua":
            Recurso(env, capacity=1),
        "Tolva":
            MedioDeAlmacenamiento(env, "Tolva", 400),
        "Almacen 1":
            MedioDeAlmacenamiento(env, "Almacen 1", 2500, 200),
        "Almacen 2":
            MedioDeAlmacenamiento(env, "Almacen 2", 1500),
        "Almacen Ext":
            MedioDeAlmacenamiento(env, "Almacen Ext", 1500),
        "Tanque 1":
            MedioDeAlmacenamiento(env, "Tanque 1", 400),
        "Tanque 2":
            MedioDeAlmacenamiento(env, "Tanque 2", 500),
        "Patio de Contenedores":
            MedioDeAlmacenamiento(env, "Patio de Contenedores", 2500, 500)}

    # cabinas_recepcion = simpy.FilterStore(env, 2)
    # cabinas_despacho = simpy.FilterStore(env, 2)
    # Cabina_recepcion= namedtuple("Cabina Recepcion","Tanque, duracion")

    # Definicion de Operaciones # TODO Ingresar datos reales
    operaciones_manipuleo = {
        "Descarga con volcadora":
            OperacionManipuleo("Descarga con volcadora",
                               recursos["Estacion Volcadora"],
                               "uniforme", [14, 20],
                               datos),
        "Descarga a pulso - Sacos":
            OperacionManipuleo("Descarga a pulso - Sacos",
                               recursos["Cuadrilla de Estibaje"],
                               "uniforme", [30, 45],
                               datos),
        "Descarga a pulso - Granos":
            OperacionManipuleo("Descarga a pulso - Granos",
                               recursos["Cuadrilla de Estibaje"],
                               "uniforme", [40, 60],
                               datos),
        "Descarga con bombas electricas":
            OperacionManipuleo("Descarga con bombas electricas",
                               recursos["Cabina de Recepcion"],
                               "uniforme", [40, 50],
                               datos),
        "Descarga con grua":
            OperacionManipuleo("Descarga con grua",
                               recursos["Grua"],
                               "uniforme", [15, 20],
                               datos),
        "Carga con tolva":
            OperacionManipuleo("Carga con tolva",
                               recursos["Estacion Tolva"],
                               "uniforme", [14, 20],
                               datos),
        "Carga con pala mecanica":
            OperacionManipuleo("Carga con pala mecanica",
                               recursos["Pala Mecanica"],
                               "uniforme", [18, 30],
                               datos),
        "Carga a pulso - Sacos":
            OperacionManipuleo("Carga a pulso - Sacos",
                               recursos["Cuadrilla de Estibaje"],
                               "uniforme", [45, 70],
                               datos),
        "Carga a pulso - Granos":
            OperacionManipuleo("Carga a pulso - Granos",
                               recursos["Cuadrilla de Estibaje"],
                               "uniforme", [60, 90],
                               datos),
        "Carga con bombas electricas":
            OperacionManipuleo("Carga con bombas electricas",
                               recursos["Cabina de Despacho"],
                               "uniforme", [45, 60],
                               datos),
        "Carga con grua":
            OperacionManipuleo("Carga con grua",
                               recursos["Grua"],
                               "uniforme", [15, 22],
                               datos),
        "Transbordo en sistema mecanizado (D)":
            OperacionManipuleo("Transbordo en sistema mecanizado",
                               recursos["Estacion Volcadora"],
                               "uniforme", [14, 25],
                               datos),
        "Transbordo en sistema mecanizado (C)":
            OperacionManipuleo("Transbordo en sistema mecanizado",
                               recursos["Estacion Tolva"],
                               "uniforme", [14, 25],
                               datos),
        "Transbordo a pulso - Sacos":
            OperacionManipuleo("Transbordo a pulso - Sacos",
                               recursos["Cuadrilla de Estibaje"],
                               "uniforme", [40, 60],
                               datos),
        "Transbordo a pulso - Granos":
            OperacionManipuleo("Transbordo a pulso - Sacos",
                               recursos["Cuadrilla de Estibaje"],
                               "uniforme", [45, 65],
                               datos),
        "Transbordo con grua":
            OperacionManipuleo("Transbordo con grua",
                               recursos["Grua"],
                               "uniforme", [15, 20],
                               datos)}

    operaciones_complementarias = {
        "Atencion recepcion 1":
            Operacion("Atencion recepcion 1",
                      recursos["Ventanilla Recepcion"],
                      "uniforme", [2, 10],
                      datos),
        "Atencion despacho 1":
            Operacion("Atencion despacho 1",
                      recursos["Ventanilla Despacho"],
                      "uniforme", [2, 10],
                      datos),
        "Primer pesaje":
            Operacion("Primer pesaje",
                      recursos["Balanza 2"],
                      "uniforme", [3, 6],
                      datos),
        "Segundo pesaje":
            Operacion("Segundo pesaje",
                      recursos["Balanza 2"],
                      "uniforme", [3, 6],
                      datos),
        "Atencion recepcion 2":
            Operacion("Atencion recepcion 2",
                      recursos["Ventanilla Recepcion"],
                      "uniforme", [4, 8],
                      datos),
        "Atencion despacho 2":
            Operacion("Atencion despacho 2",
                      recursos["Ventanilla Despacho"],
                      "uniforme", [2, 5],
                      datos)}

    # Diccionario general de operaciones
    operaciones = {
        "Operaciones manipuleo":
            operaciones_manipuleo,
        "Operaciones complementarias":
            operaciones_complementarias}

    print('Simulación de Operaciones Logísticas en ALPASUR S.A. - KEMFA S.A.')

    tsim = 10 * 60  # Tiempo de simulación
    random.seed(50)
    env.process(generar_camiones(env, operaciones, recursos))
    env.run(until=tsim)  # Simulación

    archivo = "C:\Users\AYAR\Documentos\Ingenieria Industrial\Documentos Tesis\Avances\Modelo de Simulacion\datos.csv"

    guardar_datos(datos, archivo)
    os.startfile(archivo)


if __name__ == "__main__":
    principal()
