# DistScrappy

Es un módulo para realizar scrapping simple a URLs.

## Cliente

Es la parte encargada de consumir el servicio, debido a la arquitectura del sistema requiere que se le pasen las direcciones de los servidores centrales a los cuales puede conectarse para completar sus tareas. La princial tarea que realiza es pedir URLs al sistema, la comunicación entre el cliente y el sistema se realiza mediante HTTP.

### Formato del cuerpo de Request-Response

El request se hace con el método GET y tiene en el cuerpo un JSON con el siguiente formato:

```json
{
    "urls":["URL1", "URL2", "..."]
}
```

El response del sistema contiene en su cuerpo un JSON con el siguiente formato:

```json
{
    "urls": {
        "URL1": "HTML1",
        "URL2": "HTML2",
        "...": "..."
    },
    "errors":{
        "URL1": "ERROR SCRAPPING URL1",
        "URL1": "ERROR SCRAPPING URL2",
        "...": "..."
    }
}
```

### Uso

Se realizaron tres niveles built-in de consumo:

- Clase: *client.client.DistScrappyClient*, para su uso por otros programas al intanciar la clase.
- Consola: *init_console_client.py*, crea una consola en la cual se puede interactuar con el sistema de forma directa. Para ejecutarlo correr el script según la ayuda brindada por este
- Streamlit: *init_streamlit_client*, para poder ver directamente los resultados. Para ejecutarlo correr `streamlit run init_streamlit_client` en una consola.

Al usar HTTP es muy fácil consumir el servicio brindado por **DistScrappy** sin el uso explícito de la API brindada, realizando un HTTP request con el formato especificado a la dirección de los servidores.

## Servidor

Parte encargada del funcionamiento del sistema distribuido.

### Montar el sistema

En el archivo *config.py* se encuentran las direcciones defecto de los nodos, estos se pueden modificar de acuerdo a dónde se vayan a encuentrar los nodos.

Como mínimo el sistema debe de poder localizar un nodo central al cual conectarse.

Para iniciar los nodos centrales se tienen dos scripts:

- *simple_centrals.py* Crea los servidores especificados en *config.py*.
- *init_central.py* Más general y permite la creación más personalizada de un nodo central.

Como mínimo el sistema debe de poder localizar un nodo trabajador al cual conectarse y que realice las labores pedidas por el cliente.

Para iniciar los nodos trabajadores se tienen dos scripts:

- *simple_rings.py* Crea los trabajadores especificados en *config.py*
- *init_ring.py* Más general y permite la creación más personalizada de un nodo trabajador.

Estos dos elementos son imprescindibles para el funcionamiento de **DistScrappy**.

El sistema posee la capacidad de tener guardado del contenido de los nodos, para esto es necesario correr el nodo de almacenamiento.

Para esto se tiene el script:

- *init_storage.py* Permite la creación de un nodo de almacenamiento.

Para una prueba local rápida se puede usar *simple_setup.py* el cual monta el sistema en las direcciones por defecto.

### Arquitectura

La arquitectura de **DistScrappy** se conforma principalmente de dos partes, un conjunto de servidores centrales con direcciones bien conocidas por los clientes y un conjunto distribuido de nodos desconocidos por los clientes los cuales se encargan de distribuir las tareas pedidas al sistema.

### Comunicación

**DistScrappy** usa tres protocolos de comunicación. El primero de estos es HTTP, el cual se usa a la hora de brindar el servicio a los clientes. Otro protocolo es el usado por **zmq** el cual se encarga principalmente de la comunicación entre los nodos centrales del sistema. Por último se encuentra el usado por **Pyro**, es el que más predomina ya que es el encargado de la comunicación nodos centrales-nodos trabajadores, nodos trabajadores-nodos trabajadores, nodo almacenamiento-nodos trabajadores.

#### Nodos Centrales

Para el correcto funcionamiento del sistema al menos uno de estos servidores tiene que estar activo, en caso contrario no será posible la comunicación entre y con el sistema.

Funciones:

- Puente entre los clientes y los nodos encargados de procesar el pedido.
- Servidores de nombrado para el sistema.
- Sincronizar relojes en los nodos trabajadores.

##### Manejo de Request-Response

Para el manejo de los pedidos de los clientes en cada nodo central se crea un servidor HTTP multihilos para su manejo concurrente.

##### Nombrado

**DistScrappy** posee un sistema de nombrado en la que se guardan las direcciones de los objetos reales asociados a un nombre previamente dado que los identifica en el sistema, ejemplo de los nombres que se guardan son el de los trabajadores del sistema. Para el nombrado de los componentes del sistema distribuido se utliza como base la implementación de name servers de Pyro4.

Cada nodo central posee un name server para replicar la información para así prevenir fallas cuando se caiga alguno. La consistencia de este se logra gracias al proceso de sincronización entre name servers y al manejo dinámico de los objetos activos, garantizando que eventualmente los name servers estén consistentes.

##### Sincronización

Debido a que **DistScrappy** utiliza un sistema basado en el tiempo relativo hace falta mantener a los nodos de acuerdo con el tiempo del sistema, para esto se utiliza el algoritmo de Berkeley.

Otros tipos de sincronización son logrados por mediante el uso de mutex y llamados RPC como es el caso del nodo de almacenamiento *server.storage.StorageNode*.

##### Coordinación

Entre los nodos centrales se mantiene un coordinador, el cual es el encargado de realizar tareas de mantenimiento en el sistema como la de sincronización de los name servers y del tiempo en los nodos. Este coordinador es seleccionado mediante el algoritmo Bully y se mantiene vigilancia sobre él y en caso de fallos se reelige otro nuevo.

#### Nodos Trabajadores

Para el correcto funcionamiento del sistema al menos uno de estos nodos tiene que estar activo, en caso contrario no será posible utilizar el sistema ya que no habrá quien realice el trabajo.

Funciones:

- Descargar las URLs pedidas.
- Cachear las URLs descargadas.

Estos nodos se basan en el protocolo Chord para crear un sistema en forma de anillo encargado de realizar las tareas previamente dichas. En esta DHT formada se guarda la información necesaria para mantener la validez de los HTML descargados.

##### Descargar

Cada nodo es responsable por descargar las URLs que le corresponde guardar según el hash asignado a este. Así es posible impedir de que más de un nodo esté descargando la misma URL impidiendo que se consuman recursos innecesariamente. En caso de que se pida una URL que está siendo descargada el sistema lo detecta y devuelve el resultado de la descarga en proceso. Para la descarga se utiliza el módulo **urllib**.

##### Cachear

Al ser los nodos trabajadores nodos pertenecientes a una DHT se salvan los HTML scrappeados en ella. Para la validez de la cache se tiene en cuenta un umbral de tiempo encontrado en *config.py*, si viene un pedido de una URL que se cumpla la condición de validez, el HTML no es descargado y es devuelto inmediatamente.

##### Persistencia

Para que los datos guardados sobrevivan el suceso de caída de un nodo se realizan copias del estado de la DHT en un nodo de almacenamiento. Esto permite la recuperación de información cada vez que se una un nuevo nodo a la tabla. El criterio por el cual se salva el estado de la tabla se cuenta por cantidad de escrituras por nodo, este es configurable en *config.py*.
