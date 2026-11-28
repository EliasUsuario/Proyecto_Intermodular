// EscanerScreen.js - lee un QR con la cámara y enseña qué material o máquina es
// Alumno: Elías Martínez
//
// De momento solo enseña los datos. Los botones de acción (+1 / -1, coger, devolver)
// se añadirán en los siguientes pasos.
// Si la cámara falla (o en el emulador) se puede escribir el código a mano.

import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Keyboard,
  KeyboardAvoidingView,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { buscarPorQr } from '../api';
import Boton from '../Boton';
import { colores, coloresEstado, estilos } from '../tema';
import { etiquetaEstado, formatearFecha } from '../formato';

export default function EscanerScreen() {
  const [permiso, pedirPermiso] = useCameraPermissions(); // permiso de la cámara
  const insets = useSafeAreaInsets();

  const [codigoManual, setCodigoManual] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [resultado, setResultado] = useState(null); // { tipo, datos }
  const [error, setError] = useState('');

  // La cámara lee el mismo QR muchas veces por segundo. Esta variable hace que solo se procese una lectura hasta que el usuario pulse "Escanear otro".
  // (uso useRef porque cambia al momento, sin esperar a que se repinte la pantalla)
  const bloqueo = useRef(false);

  async function buscar(codigo) {
    bloqueo.current = true;
    setBuscando(true);
    setError('');
    setResultado(null);
    try {
      const respuesta = await buscarPorQr(codigo);
      setResultado(respuesta);
    } catch (e) {
      setError(e.message);
    } finally {
      setBuscando(false);
    }
  }

  // la cámara llama a esta función cada vez que lee un QR
  function alEscanear(lectura) {
    if (bloqueo.current) {
      return; // ya estoy procesando uno
    }
    buscar(lectura.data);
  }

  // búsqueda escribiendo el código a mano
  function buscarManual() {
    Keyboard.dismiss();
    if (bloqueo.current || codigoManual.trim() === '') {
      return;
    }
    buscar(codigoManual.trim().toUpperCase()); // los códigos van en mayúsculas
  }

  // vuelve a dejar la cámara lista para otro QR
  function escanearOtro() {
    bloqueo.current = false;
    setResultado(null);
    setError('');
    setCodigoManual('');
  }

  const camaraLista = permiso !== null && permiso.granted;

  return (
    <KeyboardAvoidingView style={estilos.pantalla} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      {/* parte de arriba: la cámara */}
      <View style={propios.camara}>
        {camaraLista ? (
          <>
            <CameraView
              style={StyleSheet.absoluteFill}
              facing="back"
              barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
              onBarcodeScanned={alEscanear}
            />
            {/* marco para saber dónde apuntar */}
            <View style={propios.marco} pointerEvents="none" />
          </>
        ) : (
          <View style={propios.sinCamara}>
            {permiso === null ? (
              <ActivityIndicator color={colores.blanco} />
            ) : (
              <>
                <Text style={propios.textoSinCamara}>
                  Hace falta el permiso de la cámara para leer los códigos QR.
                </Text>
                {permiso.canAskAgain ? (
                  <Boton texto="Dar permiso" tipo="acento" onPress={pedirPermiso} style={{ marginTop: 16 }} />
                ) : (
                  <Boton
                    texto="Abrir los ajustes del móvil"
                    tipo="acento"
                    onPress={() => Linking.openSettings()}
                    style={{ marginTop: 16 }}
                  />
                )}
              </>
            )}
          </View>
        )}
      </View>

      {/* parte de abajo: resultado, error o ayuda (cerca del pulgar) */}
      <ScrollView
        style={propios.panel}
        contentContainerStyle={{ padding: 20, paddingBottom: insets.bottom + 20 }}
        keyboardShouldPersistTaps="handled"
      >
        {buscando && (
          <View style={{ alignItems: 'center', paddingVertical: 24 }}>
            <ActivityIndicator size="large" color={colores.azul} />
            <Text style={[estilos.textoSecundario, { marginTop: 10 }]}>Buscando...</Text>
          </View>
        )}

        {!buscando && error !== '' && (
          <>
            <View style={estilos.cajaError}>
              <Text style={estilos.textoError}>{error}</Text>
            </View>
            <Boton texto="Escanear otro" onPress={escanearOtro} style={{ marginTop: 16 }} />
          </>
        )}

        {!buscando && resultado !== null && (
          <>
            {resultado.tipo === 'consumible' ? (
              <TarjetaConsumible datos={resultado.datos} />
            ) : (
              <TarjetaMaquina datos={resultado.datos} />
            )}
            <Boton texto="Escanear otro" onPress={escanearOtro} style={{ marginTop: 16 }} />
          </>
        )}

        {!buscando && error === '' && resultado === null && (
          <>
            <Text style={estilos.texto}>Apunta al QR del material o de la herramienta.</Text>
            <Text style={[estilos.textoSecundario, { marginTop: 18, marginBottom: 6 }]}>
              ¿No lo lee? Escribe el código (por ejemplo CON-0001).
            </Text>
            <View style={{ flexDirection: 'row', gap: 10 }}>
              <TextInput
                style={[estilos.input, { flex: 1 }]}
                value={codigoManual}
                accessibilityLabel="Código del material"
                onChangeText={setCodigoManual}
                autoCapitalize="characters"
                autoCorrect={false}
                placeholder="CON-0001"
                placeholderTextColor={colores.gris}
                onSubmitEditing={buscarManual}
              />
              <Boton texto="Buscar" onPress={buscarManual} style={{ height: 56, minHeight: 56 }} />
            </View>
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ficha de un consumible: lo importante es cuánto se puede coger
function TarjetaConsumible({ datos }) {
  const stockBajo = datos.stock_actual < datos.stock_minimo;
  return (
    <View style={propios.tarjeta}>
      <Text style={propios.nombre}>{datos.nombre}</Text>
      <Text style={estilos.textoSecundario}>{datos.categoria || 'Sin categoría'}</Text>

      <Text style={propios.cifra}>
        {datos.disponible} <Text style={propios.unidad}>{datos.unidad_medida} disponibles</Text>
      </Text>

      {datos.stock_reservado > 0 && (
        <Text style={estilos.textoSecundario}>
          Hay {datos.stock_actual} en total y {datos.stock_reservado} están reservados por gerencia.
        </Text>
      )}
      {stockBajo && <Etiqueta texto="Stock bajo" color={colores.error} />}
      <Text style={[estilos.textoSecundario, { marginTop: 10, fontSize: 13 }]}>Código {datos.codigo_qr}</Text>
    </View>
  );
}

// ficha de una máquina: lo importante es en qué estado está y quién la tiene
function TarjetaMaquina({ datos }) {
  return (
    <View style={propios.tarjeta}>
      <Text style={propios.nombre}>{datos.nombre}</Text>
      <Text style={estilos.textoSecundario}>{datos.categoria || 'Sin categoría'}</Text>
      {datos.numero_serie ? <Text style={estilos.textoSecundario}>Nº de serie {datos.numero_serie}</Text> : null}

      <Etiqueta texto={etiquetaEstado(datos.estado)} color={coloresEstado[datos.estado] || colores.gris} />

      {datos.estado === 'en_uso' && datos.titular ? (
        <Text style={[estilos.texto, { marginTop: 10 }]}>
          La tiene {datos.titular}
          {formatearFecha(datos.fecha_salida) !== '' ? ' desde el ' + formatearFecha(datos.fecha_salida) : ''}.
        </Text>
      ) : null}
      {datos.estado === 'reservada' ? (
        <Text style={[estilos.texto, { marginTop: 10 }]}>Está reservada por gerencia, no se puede coger.</Text>
      ) : null}
      {datos.estado === 'en_mantenimiento' ? (
        <Text style={[estilos.texto, { marginTop: 10 }]}>Está en mantenimiento hasta que el administrador la revise.</Text>
      ) : null}
      <Text style={[estilos.textoSecundario, { marginTop: 10, fontSize: 13 }]}>Código {datos.codigo_qr}</Text>
    </View>
  );
}

// etiqueta de color (estado, aviso de stock bajo...)
function Etiqueta({ texto, color }) {
  return (
    <View style={[propios.etiqueta, { backgroundColor: color }]}>
      <Text style={propios.textoEtiqueta}>{texto}</Text>
    </View>
  );
}

const propios = StyleSheet.create({
  camara: {
    flex: 1,
    backgroundColor: '#111820',
  },
  sinCamara: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  textoSinCamara: {
    color: colores.blanco,
    fontSize: 17,
    textAlign: 'center',
  },
  marco: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: 220,
    height: 220,
    marginTop: -110,
    marginLeft: -110,
    borderWidth: 4,
    borderColor: colores.amarillo,
    borderRadius: 20,
  },
  panel: {
    flexGrow: 0, // el panel solo ocupa lo que necesita y la cámara el resto
    maxHeight: '60%',
    backgroundColor: colores.fondo,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
  },
  tarjeta: {
    backgroundColor: colores.blanco,
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: colores.borde,
  },
  nombre: {
    fontSize: 24,
    fontWeight: '800',
    color: colores.tinta,
  },
  cifra: {
    fontSize: 44,
    fontWeight: '800',
    color: colores.tinta,
    marginVertical: 8,
  },
  unidad: {
    fontSize: 18,
    fontWeight: '500',
    color: colores.gris,
  },
  etiqueta: {
    alignSelf: 'flex-start',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginTop: 12,
  },
  textoEtiqueta: {
    color: colores.blanco,
    fontSize: 16,
    fontWeight: '700',
  },
});
