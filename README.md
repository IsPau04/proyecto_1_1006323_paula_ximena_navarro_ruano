# Inventario de productos de supermercado

**Estudiante:** Paula Ximena Navarro Ruano  
**Carné:** 1006323  
**Curso:** Virtualización  
**Proyecto:** 1

## Descripción

Esta aplicación permite registrar, consultar, editar y eliminar productos
de un supermercado. Cada producto contiene nombre, precio y cantidad
disponible en inventario.

El proyecto utiliza cuatro contenedores administrados con Docker Compose:
frontend en Vue, backend en Python con Flask, base de datos MongoDB y un
gateway Nginx que permite acceder mediante HTTPS.

## Arquitectura

| Servicio | Contenedor | IP fija | Puerto interno |
|---|---|---|---|
| Gateway Nginx | proyecto1-gateway | 192.168.162.12 | 80 y 443 |
| Frontend Vue | proyecto1-frontend | 192.168.162.13 | 80 |
| Backend Flask | proyecto1-backend | 192.168.162.14 | 5000 |
| MongoDB | mongodb | 192.168.162.15 | 27017 |

- Red Docker: `proyecto_network`.
- Subred: `192.168.162.0/27`.
- Puerta de enlace de la red: `192.168.162.1`.
- Volumen de datos: `proyecto1_mongo_data`, montado en `/data/db`.

Solo el gateway publica puertos en el equipo:
- `http://localhost:8082`: redirige a HTTPS.
- `https://localhost:8443`: acceso a la aplicación.

Nginx envía las solicitudes `/api/` al backend y las demás al frontend.
El backend consulta y modifica los datos almacenados en MongoDB.
El cifrado HTTPS termina en el gateway; la comunicación hacia frontend
y backend utiliza HTTP dentro de la red Docker.

## Archivos principales

| Ruta | Contenido |
|---|---|
| `backend/` | Código Flask, dependencias y Dockerfile |
| `frontend/` | Código Vue y Dockerfile |
| `nginx/nginx.conf` | Proxy inverso y configuración HTTPS |
| `nginx/certs/openssl.cnf` | Configuración para generar el certificado |
| `docker-compose.yml` | Servicios, red, volumen y comprobaciones de salud |
| `.env.example` | Ejemplo de variables de entorno |
| `documentacion/` | Carpeta destinada a documentación y evidencias |

## Requisitos

- Docker Desktop iniciado y configurado para contenedores Linux.
- Docker Compose con soporte para `--wait`.
- Git Bash en Windows para ejecutar los comandos de esta guía.
- OpenSSL y curl disponibles.
- Internet para descargar imágenes y dependencias.
- Puertos locales 8082 y 8443 disponibles.

No es necesario instalar Python ni Node.js en el equipo para ejecutar
la aplicación con Docker.

## Instalación en otra computadora

Descargar o clonar el repositorio y abrir Git Bash en la carpeta que
contiene `docker-compose.yml`.

### 1. Configurar las variables

Si todavía no existe `.env`, crearlo a partir del ejemplo:

```bash
cp -n .env.example .env
```

Su contenido debe incluir:

```dotenv
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DATABASE=proyecto1_db
```

### 2. Preparar la red y el volumen externos

Consultar si ya existen:

```bash
docker network ls
docker volume ls
```

Si no existe `proyecto_network`, crearla:

```bash
docker network create \
  --driver bridge \
  --subnet 192.168.162.0/27 \
  --gateway 192.168.162.1 \
  proyecto_network
```

Si ya existe, comprobar que su subred y gateway coincidan:

```bash
docker network inspect proyecto_network --format '{{json .IPAM.Config}}'
```

La subred no debe superponerse con otras redes utilizadas en el equipo.

Si no existe el volumen de datos, crearlo:

```bash
docker volume create proyecto1_mongo_data
```

Ambos recursos están declarados como externos en Compose, por lo que
deben existir antes de iniciar los servicios.

### 3. Generar el certificado HTTPS

En una instalación nueva, generar el certificado y su llave usando
la configuración incluida:

```bash
openssl req \
  -config nginx/certs/openssl.cnf \
  -x509 \
  -nodes \
  -days 365 \
  -newkey rsa:2048 \
  -sha256 \
  -keyout nginx/certs/server.key \
  -out nginx/certs/server.crt
```

Si ya se dispone de un certificado y su llave correspondiente vigentes,
no es necesario regenerarlos.

Verificar el certificado:

```bash
openssl x509 \
  -in nginx/certs/server.crt \
  -noout -subject -dates -ext subjectAltName
```

El certificado incluye `localhost` y `127.0.0.1`.
La llave privada y `.env` están excluidos de Git.

### 4. Iniciar la aplicación

Validar la configuración:

```bash
docker compose config --quiet
```

Construir las imágenes e iniciar los servicios:

```bash
docker compose up -d --build --wait
```

Consultar su estado:

```bash
docker compose ps
```

MongoDB y backend deben mostrar estado `healthy`.
Frontend y gateway deben estar activos.

### 5. Abrir la aplicación

Ingresar a:

https://localhost:8443

El navegador puede mostrar una advertencia porque el certificado es
autofirmado. Para esta instalación local, comprobar la dirección y
utilizar la opción de continuar en la configuración avanzada.

## Verificaciones

Comprobar la redirección HTTP a HTTPS:

```bash
curl -I http://localhost:8082
```

Resultado esperado: código `301` y redirección a
`https://localhost:8443/`.

Consultar los productos mediante HTTPS:

```bash
curl --cacert nginx/certs/server.crt \
  -i https://localhost:8443/api/productos
```

Resultado esperado: código `200 OK` y una lista JSON.
En una instalación con un volumen nuevo, la lista puede estar vacía.

## Prueba de CRUD y persistencia

1. Crear un producto desde la interfaz.
2. Consultarlo en la lista.
3. Editar su stock y guardar.
4. Detener y eliminar los contenedores:

```bash
docker compose down
```

5. Iniciar nuevamente:

```bash
docker compose up -d --wait
```

6. Recargar la página y comprobar que el producto conserva sus datos.
7. Eliminar el producto desde la interfaz y confirmar que desaparece.

Los datos permanecen en `proyecto1_mongo_data` aunque se recreen los
contenedores. El volumen pertenece al equipo donde se ejecuta Docker:
copiar el código a otra computadora no copia los productos registrados.

## Comandos de administración

Detener temporalmente:

```bash
docker compose stop
```

Iniciar los servicios:

```bash
docker compose up -d --wait
```

Reconstruir después de modificar el código:

```bash
docker compose up -d --build --wait
```

Consultar registros:

```bash
docker compose logs --tail=100 backend gateway
```

Validar Nginx con el gateway activo:

```bash
docker compose exec gateway nginx -t
```

## Alcance

Proyecto académico para ejecución local. Incluye CRUD de productos,
persistencia en MongoDB, variables de entorno, IP fijas, comprobaciones
de salud y acceso HTTPS mediante un gateway.