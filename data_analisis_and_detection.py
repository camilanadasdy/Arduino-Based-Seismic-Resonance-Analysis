import serial
import pandas as pd
import time
# ==================================
# CONFIGURACION
# ==================================
PUERTO = "COM9"      # CAMBIAR
BAUDRATE = 115200
# ==================================
# CONEXION
# ==================================
arduino = serial.Serial(
    PUERTO,
    BAUDRATE,
    timeout=1)
# Esperar reinicio del Arduino
time.sleep(3)
# Vaciar buffer serial
arduino.reset_input_buffer()
# ==================================
# PARAMETROS DEL EXPERIMENTO
# ==================================
print("\n=== EXPERIMENTO DE RESONANCIA ===")
frecuencia = float(
    input(
        "Ingrese frecuencia objetivo [1 - 10 Hz]: "))
while frecuencia < 1 or frecuencia > 10:
    frecuencia = float(
        input(
            "Ingrese una frecuencia valida [1 - 10 Hz]: "))
duracion = int(
    input(
        "Duracion del ensayo [s]: "))
nombre = input(
    "Nombre del archivo: ")
# ==================================
# CONVERSION Hz -> PWM
# ==================================
PWM_MIN = 0
PWM_MAX = 255
FREC_MIN = 1
FREC_MAX = 10
pwm = int(
    PWM_MIN +
    (frecuencia - FREC_MIN)
    * (PWM_MAX - PWM_MIN)
    / (FREC_MAX - FREC_MIN))
print(f"\nPWM estimado: {pwm}")
# ==================================
# ENVIAR PWM
# ==================================
comando = f"PWM:{pwm}\n"
arduino.write(comando.encode()) 
print(f"Enviando: {comando}")
# ==================================
# ADQUISICION DE DATOS
# ==================================
datos = []
inicio = time.time()
while time.time() - inicio < duracion:
    linea = (
        arduino.readline()
        .decode(
            "utf-8",
            errors="ignore")
        .strip())
    columnas = linea.split(",")
    if len(columnas) == 5:
        tiempo_ms, ax, ay, az, pwm_rx = columnas
        datos.append([
            frecuencia,
            tiempo_ms,
            ax,
            ay,
            az,
            pwm_rx])
# ==================================
# DETENER MOTOR
# ==================================
arduino.write(b"PWM:0\n")
time.sleep(1)
arduino.close()
# ==================================
# GUARDAR CSV
# ==================================
df = pd.DataFrame(
    datos,
    columns=[
        "frecuencia_objetivo_hz",
        "tiempo_ms",
        "ax_g",
        "ay_g",
        "az_g",
        "pwm"])
archivo = f"{nombre}.csv"
df.to_csv(
    archivo,
    index=False)
print("\nExperimento finalizado.")
print(f"Archivo guardado: {archivo}")
print(f"Total de muestras: {len(df)}")
\end{lstlisting}
\subsection{Código Procesamiento de Datos}
\begin{lstlisting}
# ============================================================
#  LIBRERIAS
# ============================================================
import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
# ============================================================
#  RUTA DE LA CARPETA CON LOS CSV
# ============================================================
ruta = r"C:\Users\USER\Documents\archivos CAMILA\ESPOCH\5to Semestre\Waves & Optics\Final Project\Arduino_codigo_1\Python_cod_ex\CSV_validos"
# Buscar todos los archivos CSV dentro de la carpeta
files = sorted(glob.glob(os.path.join(ruta, "*.csv")))
print(f"Se encontraron {len(files)} archivos.\n")
# ============================================================
#  LISTA PARA GUARDAR LOS DATAFRAMES PROCESADOS
# ============================================================
datos_procesados = []
# ============================================================
#  RECORRER CADA CSV
# ============================================================
for file in files:
    # --------------------------------------------------------
    #  Leer archivo
    # --------------------------------------------------------
    df = pd.read_csv(file)

    # --------------------------------------------------------
    #  Verificar que el archivo no este vacio
    # --------------------------------------------------------
    if df.empty:
        print(f"Archivo vacio: {os.path.basename(file)}")
        continue
    # --------------------------------------------------------
    #  Verificar columnas necesarias
    # --------------------------------------------------------
    columnas_requeridas = [
        "frecuencia_objetivo_hz",
        "tiempo_ms",
        "ax_g",
        "ay_g",
        "az_g",
        "pwm"]
    if not all(col in df.columns for col in columnas_requeridas):
        print(f"Faltan columnas en: {os.path.basename(file)}")
        continue
    # --------------------------------------------------------
    #  Convertir tiempo: ms -> s
    # --------------------------------------------------------
    df["tiempo_s"] = df["tiempo_ms"] / 1000
    # --------------------------------------------------------
    #  Convertir aceleraciones: g -> m/s^2
    # --------------------------------------------------------
    g = 9.81
    df["ax_ms2"] = df["ax_g"] * g
    df["ay_ms2"] = df["ay_g"] * g
    df["az_ms2"] = df["az_g"] * g
    # --------------------------------------------------------
    #  Guardar dataframe procesado
    # --------------------------------------------------------
    datos_procesados.append(df)
    # --------------------------------------------------------
    #  Informacion rapida
    # --------------------------------------------------------
    frecuencia = df["frecuencia_objetivo_hz"].iloc[0]
    print(
        f"{os.path.basename(file)} "
        f"| f = {frecuencia} Hz "
        f"| muestras = {len(df)}")
print("\nProcesamiento inicial completado.")
# ============================================================
#  FILTRADO Y LIMPIEZA DE DATOS
# ============================================================
for i, df in enumerate(datos_procesados):
    # --------------------------------------------------------
    #  Extraer aceleraciones en m/s^2
    # --------------------------------------------------------
    ax = df["ax_ms2"].values
    ay = df["ay_ms2"].values
    az = df["az_ms2"].values
    # --------------------------------------------------------
    #  Eliminar offset de cada eje
    # --------------------------------------------------------
    # Esto elimina:
    # - gravedad residual
    # - inclinacion del sensor
    # - offset electronico
    # - deriva lenta
    ax_clean = ax - np.mean(ax)
    ay_clean = ay - np.mean(ay)
    az_clean = az - np.mean(az)
    # --------------------------------------------------------
    #  Calcular aceleracion total
    # --------------------------------------------------------
    a_total = np.sqrt(
        ax_clean**2 +
        ay_clean**2 +
        az_clean**2)
    # --------------------------------------------------------
    #  Eliminar componente continua residual
    # --------------------------------------------------------
    a_total_clean = a_total - np.mean(a_total)
    # --------------------------------------------------------
    #  Guardar resultados en el DataFrame
    # --------------------------------------------------------   
    df["ax_clean"] = ax_clean
    df["ay_clean"] = ay_clean
    df["az_clean"] = az_clean
    df["a_total"] = a_total
    df["a_total_clean"] = a_total_clean
    # --------------------------------------------------------
    #  Informacion de control
    # --------------------------------------------------------
    frecuencia = df["frecuencia_objetivo_hz"].iloc[0]
    print(
        f"Ensayo {i+1:02d} | "
        f"f = {frecuencia} Hz | "
        f"media(a_total_clean) = "
        f"{np.mean(a_total_clean):.3e}")
print("\nFiltrado y limpieza completados.")
# ============================================================
#  ORDENAR ENSAYOS POR FRECUENCIA
# ============================================================
datos_ordenados = sorted(
    datos_procesados,
    key=lambda df: df["frecuencia_objetivo_hz"].iloc[0])
frecuencias = [
    df["frecuencia_objetivo_hz"].iloc[0]
    for df in datos_ordenados]
print("Frecuencias ordenadas:")
print(frecuencias)
# ============================================================
#  CARPETA DE SALIDA
# ============================================================
ruta_salida = r"C:\Users\USER\Documents\archivos CAMILA\ESPOCH\5to Semestre\Waves & Optics\Final Project\graficos"
os.makedirs(ruta_salida, exist_ok=True)
# ============================================================
#  MOSAICO AX - AY - AZ
# ============================================================
n = len(datos_ordenados)
fig, axes = plt.subplots(
    nrows=n,
    ncols=1,
    figsize=(12, 3*n),
    constrained_layout=True)
if n == 1:
    axes = [axes]
for ax_plot, df in zip(axes, datos_ordenados):
    t = df["tiempo_s"]
    f = df["frecuencia_objetivo_hz"].iloc[0]
    ax_plot.plot(t, df["ax_clean"],
                 label="Ax",
                 color="#1f3b4d",
                 linewidth=1)
    ax_plot.plot(t, df["ay_clean"],
                 label="Ay",
                 color="#4c6a92",
                 linewidth=1)
    ax_plot.plot(t, df["az_clean"],
                 label="Az",
                 color="#8aa6c1",
                 linewidth=1)
    ax_plot.set_title(f"{f} Hz")
    ax_plot.set_xlabel("Tiempo (s)")
    ax_plot.set_ylabel("Aceleracion (m/s^2)")
    ax_plot.legend(loc="upper right")
fig.suptitle(
    "Aceleraciones triaxiales",
    fontsize=16)
plt.savefig(
    os.path.join(ruta_salida, "mosaico_xyz.png"),
    dpi=300,
    bbox_inches="tight")
plt.show()
# ============================================================
#  MOSAICO AX - AY
# ============================================================
fig, axes = plt.subplots(
    nrows=n,
    ncols=1,
    figsize=(12, 3*n),
    constrained_layout=True)
if n == 1:
    axes = [axes]
for ax_plot, df in zip(axes, datos_ordenados):
    t = df["tiempo_s"]
    f = df["frecuencia_objetivo_hz"].iloc[0]
    ax_plot.plot(t, df["ax_clean"],
                 label="Ax",
                 color="#2b6855",
                 linewidth=1)
    ax_plot.plot(t, df["ay_clean"],
                 label="Ay",
                 color="#6f4c92",
                 linewidth=1)
    ax_plot.set_title(f"{f} Hz")
    ax_plot.set_xlabel("Tiempo (s)")
    ax_plot.set_ylabel("Aceleracion (m/s^2)")
    ax_plot.legend(loc="upper right")
fig.suptitle(
    "Aceleraciones en el plano XY",
    fontsize=16)
plt.savefig(
    os.path.join(ruta_salida, "mosaico_xy.png"),
    dpi=300,
    bbox_inches="tight")
plt.show()
# ============================================================
#  MOSAICO ACELERACION TOTAL
# ============================================================
fig, axes = plt.subplots(
    nrows=n,
    ncols=1,
    figsize=(12, 3*n),
    constrained_layout=True)
if n == 1:
    axes = [axes]
for ax_plot, df in zip(axes, datos_ordenados):
    t = df["tiempo_s"]
    f = df["frecuencia_objetivo_hz"].iloc[0]
    ax_plot.plot(
        t,
        df["a_total_clean"],
        color="#48698e",
        linewidth=1)
    ax_plot.set_title(f"{f} Hz")
    ax_plot.set_xlabel("Tiempo (s)")
    ax_plot.set_ylabel("Aceleracion (m/s^2)")
fig.suptitle(
    "Aceleracion total",
    fontsize=16)
plt.savefig(
    os.path.join(ruta_salida, "mosaico_atotal.png"),
    dpi=300,
    bbox_inches="tight")
plt.show()
# ============================================================
#  LIBRERIAS NECESARIAS
# ============================================================
from scipy.fft import fft, fftfreq
# ============================================================
#  LISTAS PARA RESULTADOS GLOBALES
# ============================================================
frecuencias_exc = []
picos_fft = []
amplitudes_pico = []
rms_list = []
# ============================================================
#  FFT DE CADA ENSAYO
# ============================================================
for df in datos_ordenados:
    # --------------------------------------------------------
    #  SENAL EN EL TIEMPO
    # --------------------------------------------------------
    t = df["tiempo_s"].values
    a = df["a_total_clean"].values
    # --------------------------------------------------------
    #  VERIFICAR CANTIDAD DE DATOS
    # --------------------------------------------------------
    N = len(a)
    if N < 2:
        print("Archivo omitido: muy pocos datos")
        continue
    # --------------------------------------------------------
    #  PASO TEMPORAL
    # --------------------------------------------------------
    dt = np.mean(np.diff(t))
    # frecuencia de muestreo
    fs = 1 / dt
    # --------------------------------------------------------
    #  FFT
    # --------------------------------------------------------
    yf = fft(a)
    xf = fftfreq(N, dt)
    # --------------------------------------------------------
    #  CONSERVAR SOLO FRECUENCIAS POSITIVAS
    # --------------------------------------------------------
    idx = xf > 0
    xf = xf[idx]
    # normalizacion de amplitud
    yf = (2 / N) * np.abs(yf[idx])
    # --------------------------------------------------------
    #  DETECCION DEL PICO PRINCIPAL
    # --------------------------------------------------------
    peak_index = np.argmax(yf)
    peak_freq = xf[peak_index]
    peak_amp = yf[peak_index]
    # --------------------------------------------------------
    #  RMS DE LA SENAL
    # --------------------------------------------------------
    rms = np.sqrt(np.mean(a**2))
    # --------------------------------------------------------
    #  GUARDAR RESULTADOS EN EL DATAFRAME
    # --------------------------------------------------------
    df.attrs["dt"] = dt
    df.attrs["fs"] = fs
    df.attrs["frecuencias_fft"] = xf
    df.attrs["amplitudes_fft"] = yf
    df.attrs["peak_freq"] = peak_freq
    df.attrs["peak_amp"] = peak_amp
    df.attrs["rms"] = rms
    # --------------------------------------------------------
    #  GUARDAR RESULTADOS GLOBALES
    # --------------------------------------------------------
    f_exc = df["frecuencia_objetivo_hz"].iloc[0]

    frecuencias_exc.append(f_exc)
    picos_fft.append(peak_freq)
    amplitudes_pico.append(peak_amp)
    rms_list.append(rms)
    # --------------------------------------------------------
    #  INFORMACION DE CONTROL
    # --------------------------------------------------------
    print("===================================")
    print(f"Frecuencia de excitacion: {f_exc:.1f} Hz")
    print(f"Frecuencia pico FFT:      {peak_freq:.2f} Hz")
    print(f"Amplitud pico:            {peak_amp:.4f} m/s^2")
    print(f"RMS:                      {rms:.4f} m/s^2")
    print(f"Frecuencia de muestreo:   {fs:.2f} Hz")
    print("===================================\n")
os.makedirs(ruta_salida, exist_ok=True)
# ============================================================
#  MOSAICO FFT
# ============================================================
n = len(datos_ordenados)
fig, axes = plt.subplots(
    nrows=n,
    ncols=1,
    figsize=(12, 3*n),
    constrained_layout=True)
if n == 1:
    axes = [axes]
for ax_plot, df in zip(axes, datos_ordenados):
    xf = df.attrs["frecuencias_fft"]
    yf = df.attrs["amplitudes_fft"]
    f_exc = df["frecuencia_objetivo_hz"].iloc[0]
    peak_freq = df.attrs["peak_freq"]
    ax_plot.plot(
        xf,
        yf,
        color="#5C4681",
        linewidth=1.2)
    ax_plot.axvline(
        peak_freq,
        color="#C05A4D",
        linestyle="--",
        alpha=0.8,
        label=f"Pico: {peak_freq:.2f} Hz" )
    ax_plot.set_xlim(0, max(xf))
    ax_plot.set_title(f"{f_exc} Hz")
    ax_plot.set_xlabel("Frecuencia (Hz)")
    ax_plot.set_ylabel("Amplitud")
    ax_plot.legend(loc="upper right")
fig.suptitle(
    "Espectros FFT para todas las frecuencias de excitacion",
    fontsize=16)
plt.savefig(
    os.path.join(ruta_salida, "mosaico_fft.png"),
    dpi=300,
    bbox_inches="tight")
plt.show()
# ============================================================
#  CURVA DE RESONANCIA USANDO LAS FRECUENCIAS DEL FFT
# ============================================================
# ============================================================
#  CONVERTIR A ARRAYS
# ============================================================
peak_freq_array = np.array(peak_freq_list)
peak_amp_array = np.array(fft_peak_list)
# verificar que existan datos
if len(peak_freq_array) == 0:
    print("\n No se generaron datos para la curva de resonancia.")
else:
    # --------------------------------------------------------
    #  ORDENAR POR FRECUENCIA
    # --------------------------------------------------------
    orden = np.argsort(peak_freq_array)
    peak_freq_array = peak_freq_array[orden]
    peak_amp_array = peak_amp_array[orden]
    # --------------------------------------------------------
    #  FRECUENCIA DE RESONANCIA
    # --------------------------------------------------------
    indice_resonancia = np.argmax(peak_amp_array)
    f_res = peak_freq_array[indice_resonancia]
    amp_res = peak_amp_array[indice_resonancia]
    # --------------------------------------------------------
    #  CURVA DE RESONANCIA
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.plot(
        peak_freq_array,
        peak_amp_array,
        'o-',
        color="#4c6a92",
        linewidth=2,
        markersize=8)
    plt.scatter(
        f_res,
        amp_res,
        s=120,
        color="#b22222",
        zorder=5,
        label=f"Resonancia ~= {f_res:.2f} Hz")
    plt.xlabel("Frecuencia dominante del FFT (Hz)")
    plt.ylabel("Amplitud maxima del FFT")
    plt.title("Curva de resonancia experimental")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()
    # --------------------------------------------------------
    #  RESULTADOS
    # --------------------------------------------------------
    print("\n======================================")
    print(f"Frecuencia de resonancia estimada: {f_res:.2f} Hz")
    print(f"Amplitud maxima: {amp_res:.4f}")
    print("======================================")
