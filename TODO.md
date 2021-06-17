# TODO

- Conexion al mismo tiempo de varios nodos chord hace que no se vean entre ellos.
- Si no esta levantado el central lanza excepcion al crear RingNodes y se termina. Hacer que resistan ahi y que prueben de nuevo.
- El Time sync le falta mejorar el diseño para que trabaje con hilos de forma correcta. Por ejemplo los relojes se sincronizan luego de que se hayan recibido todos los llamados a los nodos. Me parece que no es necesario compartir el estado de client data, esto puede ocasionar problemas de sincronización, de ser posible, llamar a los métodos que lo usen añadiéndolo como parámetro. 

Errores en el name server

- No se borren las direcciones correctamente, por ejemplo se borra una direccion en un name server pero al actualizarse se vuelve a copiar la direccion de otro name server que no sabe que ya no esta activo el nodo
