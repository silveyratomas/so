import random
import time
import threading
import tkinter as tk
from queue import Queue

class Proceso:
    def _init_(self, id_proceso, memoria_solicitada, tiempo_ejecucion):
        self.id_proceso = id_proceso
        self.memoria_solicitada = memoria_solicitada
        self.tiempo_ejecucion = tiempo_ejecucion
        self.estado = "Listo"

class Simulador:
    def _init_(self, memoria_total, interfaz):
        self.memoria_total = memoria_total
        self.memoria_disponible = memoria_total
        self.cola_listos = Queue()
        self.cola_espera = Queue()
        self.lock = threading.Lock()
        self.interfaz = interfaz
        self.simulacion_activa = True  # Indicador para finalizar la simulación

    def solicitar_memoria(self, proceso):
        with self.lock:
            if self.memoria_disponible >= proceso.memoria_solicitada:
                self.memoria_disponible -= proceso.memoria_solicitada
                self.cola_listos.put(proceso)
                self.interfaz.actualizar_estado(proceso, "Listo")
                self.interfaz.actualizar_memoria(self.memoria_disponible)
                self.interfaz.registrar_evento(f"Proceso {proceso.id_proceso} entra en 'Listo' (Solicitó: {proceso.memoria_solicitada} MB)")
            else:
                self.cola_espera.put(proceso)
                self.interfaz.actualizar_estado(proceso, "Bloqueado")
                self.interfaz.registrar_evento(f"Proceso {proceso.id_proceso} en 'Bloqueado' (Solicitó: {proceso.memoria_solicitada} MB, Memoria insuficiente)")

    def liberar_memoria(self, proceso):
        with self.lock:
            self.memoria_disponible += proceso.memoria_solicitada
            self.interfaz.actualizar_memoria(self.memoria_disponible)
            self.interfaz.actualizar_estado(proceso, "Terminado")
            self.interfaz.registrar_evento(f"Proceso {proceso.id_proceso} terminó y liberó {proceso.memoria_solicitada} MB")

    def ejecutar_procesos(self):
        while not self.cola_listos.empty() and self.simulacion_activa:
            proceso = self.cola_listos.get()
            self.interfaz.actualizar_estado(proceso, "Ejecutando")
            self.interfaz.registrar_evento(f"Proceso {proceso.id_proceso} en ejecución")
            time.sleep(proceso.tiempo_ejecucion)  # Simula el tiempo de ejecución del proceso
            self.liberar_memoria(proceso)
            self.verificar_espera()

    def verificar_espera(self):
        with self.lock:
            while not self.cola_espera.empty() and self.memoria_disponible >= self.cola_espera.queue[0].memoria_solicitada:
                proceso = self.cola_espera.get()
                self.solicitar_memoria(proceso)

    def temporizador(self):
        while not self.cola_listos.empty() and self.simulacion_activa:
            proceso = self.cola_listos.queue[0]  # Proceso que está en ejecución
            self.interfaz.actualizar_estado(proceso, "Temporizado")
            self.interfaz.registrar_evento(f"Proceso {proceso.id_proceso} temporizado")
            time.sleep(1)  # Temporización de 1 segundo
            self.cola_listos.put(self.cola_listos.get())  # Mueve el proceso actual al final de la cola

    def finalizar_simulacion(self):
        self.simulacion_activa = False
        self.interfaz.registrar_evento("Simulación finalizada.")

class InterfazSimulador:
    def _init_(self, memoria_total, simulador):
        self.simulador = simulador
        self.root = tk.Tk()
        self.root.title("Simulador de Gestión de Procesos y Memoria")

        self.label_memoria = tk.Label(self.root, text=f"Memoria disponible: {memoria_total} MB")
        self.label_memoria.pack()

        self.label_procesos = tk.Label(self.root, text="Procesos:")
        self.label_procesos.pack()

        self.lista_procesos = tk.Listbox(self.root, width=50)
        self.lista_procesos.pack()

        self.label_historial = tk.Label(self.root, text="Historial de eventos:")
        self.label_historial.pack()

        self.historial = tk.Text(self.root, height=10, width=50, state=tk.DISABLED)
        self.historial.pack()

        self.boton_finalizar = tk.Button(self.root, text="Finalizar Simulación", command=self.finalizar)
        self.boton_finalizar.pack()

        self.procesos = {}

    def actualizar_estado(self, proceso, estado):
        proceso.estado = estado
        self.procesos[proceso.id_proceso] = proceso
        self.actualizar_lista_procesos()

    def actualizar_memoria(self, memoria_disponible):
        self.label_memoria.config(text=f"Memoria disponible: {memoria_disponible} MB")

    def actualizar_lista_procesos(self):
        self.lista_procesos.delete(0, tk.END)
        for proceso in self.procesos.values():
            self.lista_procesos.insert(tk.END, f"Proceso {proceso.id_proceso}: {proceso.estado}, Memoria: {proceso.memoria_solicitada} MB")

    def registrar_evento(self, mensaje):
        self.historial.config(state=tk.NORMAL)
        self.historial.insert(tk.END, mensaje + "\n")
        self.historial.config(state=tk.DISABLED)
        self.historial.see(tk.END)

    def finalizar(self):
        self.simulador.finalizar_simulacion()

    def iniciar(self):
        self.root.mainloop()


def main():
    memoria_total = 100  # Memoria total del sistema en MB
    interfaz = InterfazSimulador(memoria_total, None)
    simulador = Simulador(memoria_total, interfaz)
    interfaz.simulador = simulador

    # Creando procesos con solicitudes de memoria y tiempos de ejecución aleatorios
    for i in range(1, 6):
        memoria_solicitada = random.randint(10, 40)  # Memoria solicitada entre 10 y 40 MB
        tiempo_ejecucion = random.randint(2, 5)  # Tiempo de ejecución entre 2 y 5 segundos
        proceso = Proceso(id_proceso=i, memoria_solicitada=memoria_solicitada, tiempo_ejecucion=tiempo_ejecucion)
        simulador.solicitar_memoria(proceso)

    # Ejecutar procesos con temporización
    thread_ejecutar = threading.Thread(target=simulador.ejecutar_procesos)
    thread_temporizar = threading.Thread(target=simulador.temporizador)

    thread_ejecutar.start()
    thread_temporizar.start()

    interfaz.iniciar()

    thread_ejecutar.join()
    thread_temporizar.join()

if _name_ == "_main_":
    main()
