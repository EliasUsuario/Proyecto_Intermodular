// LoginScreen.js - pantalla de inicio de sesión

// Alumno: Elías Martínez
// También deja escribir la dirección de la API, porque la IP del ordenador cambia de una wifi a otra y así no hay que tocar el código.

import { useContext, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { SesionContext } from '../sesion';
import { colores, estilos } from '../tema';
import Boton from '../Boton';
import { getUrlBase, login, probarConexion, setToken, setUrlBase, yo } from '../api';
import { guardarUrl } from '../almacen';

export default function LoginScreen() {
  const { iniciarSesion, aviso } = useContext(SesionContext); // funciones de App.js
  const insets = useSafeAreaInsets(); // para no tapar con la barra del móvil

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [url, setUrl] = useState(getUrlBase()); // dirección de la API
  const [verServidor, setVerServidor] = useState(getUrlBase() === ''); // si no hay dirección, enseño el apartado abierto
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState('');
  const [estadoConexion, setEstadoConexion] = useState(null); // { ok: true/false, texto }

  // comprueba que la API responde en la dirección escrita
  async function probar() {
    setEstadoConexion(null);
    setUrlBase(url);
    try {
      const datos = await probarConexion();
      setEstadoConexion({ ok: true, texto: 'Conectado: ' + datos.mensaje });
    } catch (e) {
      setEstadoConexion({ ok: false, texto: e.message });
    }
  }

  async function entrar() {
    setError('');
    if (url.trim() === '') {
      setVerServidor(true);
      setError('Escribe la dirección del servidor.');
      return;
    }
    if (email.trim() === '' || password === '') {
      setError('Escribe tu email y tu contraseña.');
      return;
    }

    setCargando(true);
    try {
      setUrlBase(url); // uso la dirección que haya escrito
      await guardarUrl(getUrlBase()); // y la guardo para la próxima vez
      setToken(null); // por si quedaba un token antiguo

      const datos = await login(email.trim(), password);
      setToken(datos.access_token); // desde aquí todas las peticiones llevan el token
      const perfil = await yo(); // pido mi id de usuario, lo necesitaré más adelante

      await iniciarSesion({
        token: datos.access_token,
        nombre: datos.nombre,
        rol: datos.rol,
        id_usuario: perfil.id_usuario,
      });
    } catch (e) {
      setToken(null);
      setError(e.message); // por ejemplo "Email o contraseña incorrectos"
    } finally {
      setCargando(false);
    }
  }

  return (
    <KeyboardAvoidingView style={estilos.pantalla} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView
        contentContainerStyle={{ flexGrow: 1, padding: 24, paddingTop: insets.top + 48, paddingBottom: insets.bottom + 24 }}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={estilos.titulo}>GestorMaterial</Text>
        <Text style={[estilos.textoSecundario, { marginTop: 8, marginBottom: 32 }]}>
          Inicia sesión para registrar material y herramientas del taller.
        </Text>

        {aviso !== '' && (
          <View style={[estilos.cajaError, { marginBottom: 16 }]}>
            <Text style={estilos.textoError}>{aviso}</Text>
          </View>
        )}

        <Text style={[estilos.texto, { marginBottom: 6 }]}>Email</Text>
        <TextInput
          style={estilos.input}
          value={email}
          accessibilityLabel="Email"
          onChangeText={setEmail}
          placeholder="nombre@gestormaterial.com"
          placeholderTextColor={colores.gris}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
        />

        <Text style={[estilos.texto, { marginTop: 16, marginBottom: 6 }]}>Contraseña</Text>
        <TextInput
          style={estilos.input}
          value={password}
          accessibilityLabel="Contraseña"
          onChangeText={setPassword}
          secureTextEntry
          autoCapitalize="none"
          onSubmitEditing={entrar}
        />

        {error !== '' && (
          <View style={[estilos.cajaError, { marginTop: 16 }]}>
            <Text style={estilos.textoError}>{error}</Text>
          </View>
        )}

        <Boton texto="Entrar" onPress={entrar} cargando={cargando} style={{ marginTop: 24 }} />

        {/* apartado para cambiar la dirección de la API */}
        <Pressable onPress={() => setVerServidor(!verServidor)} style={{ marginTop: 32, paddingVertical: 8 }}>
          <Text style={[estilos.textoSecundario, { textDecorationLine: 'underline' }]}>
            {verServidor ? 'Ocultar el servidor' : 'Servidor: ' + (url === '' ? 'sin configurar' : url)}
          </Text>
        </Pressable>

        {verServidor && (
          <View style={{ marginTop: 8 }}>
            <Text style={[estilos.texto, { marginBottom: 6 }]}>Dirección de la API</Text>
            <TextInput
              style={estilos.input}
              value={url}
              accessibilityLabel="Dirección de la API"
              onChangeText={setUrl}
              placeholder="http://192.168.1.20:8000"
              placeholderTextColor={colores.gris}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
            <Text style={[estilos.textoSecundario, { marginTop: 6 }]}>
              Es la IP del ordenador donde corre la API, no localhost. El móvil tiene que estar en la misma wifi.
            </Text>
            <Boton texto="Probar conexión" tipo="secundario" onPress={probar} style={{ marginTop: 12 }} />
            {estadoConexion !== null && (
              <View style={[estilos.cajaError, { marginTop: 12 }, estadoConexion.ok && { backgroundColor: '#E8F5E9' }]}>
                <Text style={[estilos.textoError, estadoConexion.ok && { color: '#2E7D32' }]}>{estadoConexion.texto}</Text>
              </View>
            )}
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
