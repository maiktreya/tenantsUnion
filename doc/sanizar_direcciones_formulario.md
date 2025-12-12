# 🛠️ Guía de Implementación: "Autocompletado Limpio"

---
---

Objetivo: Evitar que Google rellene el Distrito (ej: "Centro", "Chamberí") en el campo de dirección para prevenir duplicados en la base de datos. Resultado UX: Cuando la usuaria selecciona una dirección sugerida, el campo se reescribe instantáneamente mostrando solo Calle y Número.

## Paso 1: La Herramienta (Sin tocar archivos)
Dado que usáis Avada y WordPress, la forma más segura y ordenada de añadir este comportamiento sin romper la web es usar un plugin de gestión de scripts.

En el panel de WordPress, ve a Plugins > Añadir nuevo.

Busca e instala: WPCode (antes conocido como "Insert Headers and Footers").

Actívalo.

(Nota: Si ya tenéis una herramienta para insertar código en el "Header/Footer" o usáis las opciones de "Custom JS" de Avada, podéis saltar este paso, pero WPCode es más seguro para gestionar esto).

## Paso 2: El Código (Copiar y Pegar)
Este es el bloque de Javascript listo para usar. No necesita modificación. Detecta automáticamente cuando Google intenta rellenar el campo y "limpia" la dirección antes de que la usuaria se dé cuenta.

```{js}
<script type="text/javascript">
/**
 * Sindicato de Inquilinas - Sanitización de Direcciones en Frontend
 * Objetivo: Eliminar el 'Distrito' (ej: Centro) de la sugerencia de Google Maps.
 * Formulario ID: 5 | Campo ID: 36
 */

jQuery(document).on('gform_post_render', function(event, form_id, current_page){
    // 1. SEGURIDAD: Solo ejecutar en el formulario de afiliación (ID 5)
    if(form_id != 5) return;

    // 2. ESPERA: Damos un pequeño margen para que Google Maps cargue completamente
    setTimeout(function(){
        
        // Verificamos si el autocompletado del plugin está activo en el campo 36
        if(window.aac_input_5_36 && window.aac_input_5_36.autocomplete) {
            
            // 3. ESCUCHA: Ponemos una "oreja" digital al momento exacto en que la usuaria elige una dirección
            google.maps.event.addListener(window.aac_input_5_36.autocomplete, 'place_changed', function() {
                
                // Obtenemos los datos "crudos" de Google (sin formato de texto)
                var place = window.aac_input_5_36.autocomplete.getPlace();
                
                if (!place.address_components) return;

                var street = '';
                var number = '';

                // 4. FILTRADO: Buscamos solo la Calle (route) y el Número
                // Ignoramos deliberadamente "sublocality" o "administrative_area_level_2" (Distritos)
                for (var i = 0; i < place.address_components.length; i++) {
                    var component = place.address_components[i];
                    var addressType = component.types[0];

                    if (addressType === "route") {
                        street = component.long_name;
                    }
                    if (addressType === "street_number") {
                        number = component.long_name;
                    }
                }

                // 5. ACCIÓN: Si encontramos calle, reescribimos el campo visualmente
                if (street !== '') {
                    var cleanAddress = street;
                    if (number !== '') {
                        cleanAddress += ', ' + number;
                    }
                    
                    // Actualizamos el campo visible para la usuaria
                    jQuery('#input_5_36').val(cleanAddress);
                }
            });
        }
    }, 500); // Medio segundo de espera para asegurar carga
});
</script>
```


## Paso 3: Configuración Visual
Ve al menú Code Snippets (o WPCode) en la barra lateral izquierda del admin.

Haz clic en + Add New (Añadir nuevo).

Selecciona "Add Your Custom Code (New Snippet)".

Título: Ponle algo reconocible, ej: JS - Limpieza Direcciones Google Maps.

Code Type: Selecciona HTML Snippet a la derecha (porque el código incluye las etiquetas <script>).

Code Preview: Pega el código del Paso 2 en la caja negra.

Insertion (Importante):

Location: Site Wide Footer (Pie de página).

Razón UX/Perf: Esto asegura que el formulario ya existe antes de intentar modificarlo, evitando errores de carga.

Dale al interruptor de "Inactive" a Active y guarda.

## Paso 4: Test de Calidad (QA)
Para que la responsable de UX verifique que funciona, solo tiene que hacer esta prueba:

Abrir el formulario de afiliación en modo incógnito.

En el campo "Dirección", escribir: Calle del Pez 3.

Google sugerirá: "Calle del Pez, 3, Centro, 28004 Madrid".

Hacer clic en esa sugerencia.

Resultado esperado: En el campo de texto, la palabra "Centro" debe desaparecer mágicamente y quedar solo: "Calle del Pez, 3".

¿Por qué esto es mejor para UX?
Feedback Inmediato: La usuaria ve exactamente qué dirección se va a guardar.

Menos Confusión: Al quitar el distrito, la dirección se ve más corta y "limpia", reduciendo la carga cognitiva visual.

Consistencia: Todas las direcciones entrarán con el mismo formato estándar, facilitando la vida al equipo de datos después.
